"""Bounded deterministic lookup of candidate URLs on first-party official endpoints."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import html
import json
import re
from typing import Any, Callable, Mapping
from urllib.parse import urlencode, urljoin

from live_contentops.official_primary_evidence_loader_v1 import (
    OFFICIAL_HOSTS_BY_FAMILY,
    _default_http_get,
    _iso_utc,
    _parse_timestamp,
    _safe_url,
)


LOCATOR_ENDPOINTS = {
    "official_regulatory_fiscal": "https://www.federalregister.gov/api/v1/documents.json",
    "official_macro": "https://www.bls.gov/bls/newsrels.htm",
    "company_primary": "https://www.sec.gov/files/company_tickers.json",
    "sec_regulatory": "https://www.sec.gov/files/company_tickers.json",
    # Stable first-party Federal Reserve FOMC calendar/listing page. This replaces the earlier
    # press-release index path that returned HTTP 404. The calendar links out to individual
    # FOMC statement / implementation-note documents on the same official host.
    "official_policy": "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
}
LOCATOR_FAMILIES = frozenset(LOCATOR_ENDPOINTS)

# A source family is an authority class, not a single publisher.  These narrowly scoped
# surfaces extend the existing locator without creating another registry or acquisition path.
# Order is deterministic and an exact story may select no more than one surface.
LOCATOR_SURFACES = (
    {
        "surface_id": "eia_weekly_natural_gas_storage_v1",
        "family": "official_macro",
        "endpoint": "https://www.eia.gov/dnav/ng/ng_stor_wkly_s1_w.htm",
    },
    {
        "surface_id": "philadelphia_fed_mbos_v1",
        "family": "official_macro",
        "endpoint": (
            "https://www.philadelphiafed.org/surveys-and-data/"
            "regional-economic-analysis/manufacturing-business-outlook-survey"
        ),
    },
    {
        "surface_id": "state_current_fms_press_releases_v1",
        "family": "official_regulatory_fiscal",
        "endpoint": "https://www.state.gov/wp-json/wp/v2/state_press_release",
    },
    {
        "surface_id": "uscc_research_v1",
        "family": "official_regulatory_fiscal",
        "endpoint": "https://www.uscc.gov/research",
    },
    {
        "surface_id": "waymo_company_blog_rss_v1",
        "family": "company_primary",
        "endpoint": "https://waymo.com/blog/rss.xml",
    },
)

LEGACY_SURFACE_BY_FAMILY = {
    family: {
        "surface_id": {
            "official_regulatory_fiscal": "federal_register_documents_v1",
            "official_macro": "bls_news_releases_v1",
            "company_primary": "sec_company_ticker_index_v1",
            "sec_regulatory": "sec_company_ticker_index_v1",
            "official_policy": "federal_reserve_fomc_calendar_v1",
        }[family],
        "family": family,
        "endpoint": endpoint,
    }
    for family, endpoint in LOCATOR_ENDPOINTS.items()
}

BASE_ORIGIN_BY_FAMILY = {
    "official_policy": "https://www.federalreserve.gov/",
}


def _logical_hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _retrieval_timestamp(clock: Callable[[], datetime]) -> str:
    value = clock()
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError("official_source_locator_retrieval_time_timezone_required")
    return _iso_utc(value)


def _terms(request: Mapping[str, Any]) -> list[str]:
    context = request.get("story_context") or {}
    values = [
        *(context.get("entities_topics") or []),
        *(context.get("leaf_summaries") or []),
        context.get("why_now"),
        context.get("headline_text"),
        context.get("event_topic_summary"),
        *(context.get("follow_up_data_need_candidates") or []),
        *(context.get("needed_evidence") or []),
        *(request.get("needed_evidence") or []),
        context.get("seo_intent"),
    ]
    terms: list[str] = []
    for value in values:
        for term in re.findall(r"[A-Za-z][A-Za-z0-9'-]{2,}", str(value or "")):
            normalized = term.casefold()
            if normalized not in terms and normalized not in {"the", "and", "for", "with", "from", "that", "this"}:
                terms.append(normalized)
    return terms[:12]


def _story_text(request: Mapping[str, Any]) -> str:
    context = request.get("story_context") or {}
    values = [
        *(context.get("entities_topics") or []),
        *(context.get("leaf_summaries") or []),
        context.get("why_now"),
        context.get("headline_text"),
        context.get("event_topic_summary"),
        *(context.get("follow_up_data_need_candidates") or []),
        *(context.get("needed_evidence") or []),
        *(request.get("needed_evidence") or []),
        context.get("seo_intent"),
    ]
    return " ".join(str(value or "") for value in values).casefold()


def _surface_matches(surface_id: str, request: Mapping[str, Any]) -> bool:
    text = _story_text(request)
    if surface_id == "eia_weekly_natural_gas_storage_v1":
        return bool(
            re.search(r"\b(eia|energy information administration)\b", text)
            and re.search(r"\b(natural gas storage|working gas|underground storage)\b", text)
        )
    if surface_id == "philadelphia_fed_mbos_v1":
        return bool(
            re.search(
                r"\b(philadelphia fed|philly fed|federal reserve bank of philadelphia)\b",
                text,
            )
            and re.search(
                r"\b(manufacturing (?:business )?outlook|manufacturing index|mbos)\b",
                text,
            )
        )
    if surface_id == "state_current_fms_press_releases_v1":
        return bool(
            re.search(r"\b(state department|department of state)\b", text)
            and re.search(
                r"\b(foreign military sale|military sale|arms sale|major arms sale|kc-46a?)\b",
                text,
            )
        )
    if surface_id == "uscc_research_v1":
        return bool(
            re.search(
                r"\b(uscc|u\.?s\.?-china economic and security review commission)\b",
                text,
            )
            and re.search(r"\b(research|fact sheet|issue brief|china-russia)\b", text)
        )
    if surface_id == "waymo_company_blog_rss_v1":
        return bool(
            re.search(r"\bwaymo\b", text)
            and re.search(r"\b(asic|custom silicon|compute|robotaxi|purpose-built)\b", text)
        )
    return False


def _matching_surfaces(request: Mapping[str, Any]) -> list[Mapping[str, str]]:
    return [
        surface
        for surface in LOCATOR_SURFACES
        if _surface_matches(str(surface["surface_id"]), request)
    ]


def routed_official_locator_families(request: Mapping[str, Any]) -> frozenset[str]:
    """Return one exact context-routed family, or none when routing is absent/ambiguous.

    This is discovery routing only.  It grants no evidence, factual, numeric, Capital Chronicle,
    permission, publication, or public-write authority.
    """
    matches = _matching_surfaces(request)
    return frozenset({str(matches[0]["family"])}) if len(matches) == 1 else frozenset()


def routed_official_locator_surface_ids(request: Mapping[str, Any]) -> tuple[str, ...]:
    """Return one exact surface identity, or none when routing is absent/ambiguous."""
    matches = _matching_surfaces(request)
    return (str(matches[0]["surface_id"]),) if len(matches) == 1 else ()


def _query(request: Mapping[str, Any], family: str, surface_id: str) -> dict[str, str]:
    terms = _terms(request)
    context = request.get("story_context") or {}
    if surface_id == "federal_register_documents_v1":
        query = " ".join(terms[:8]) or str(request.get("story_type") or "")
        cutoff = datetime.fromisoformat(
            str(request.get("evaluation_as_of_utc") or "").replace("Z", "+00:00")
        )
        return {
            "per_page": "10",
            "order": "newest",
            "conditions[term]": query,
            "conditions[publication_date][gte]": (cutoff - timedelta(days=1)).date().isoformat(),
            "conditions[publication_date][lte]": cutoff.date().isoformat(),
        }
    if surface_id == "state_current_fms_press_releases_v1":
        cutoff = datetime.fromisoformat(
            str(request.get("evaluation_as_of_utc") or "").replace("Z", "+00:00")
        )
        return {
            "per_page": "20",
            "orderby": "date",
            "order": "desc",
            "after": _iso_utc(cutoff - timedelta(days=1)),
            "before": _iso_utc(cutoff),
        }
    return {"query": " ".join(terms) or str(request.get("story_type") or "")}


def _candidate_for_federal_register(
    body: bytes, request: Mapping[str, Any]
) -> tuple[str, str | None] | None:
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    terms = set(_terms(request))
    matches: list[tuple[int, str, str | None]] = []
    for row in parsed.get("results") or [] if isinstance(parsed, Mapping) else []:
        if not isinstance(row, Mapping):
            continue
        candidate = str(row.get("json_url") or row.get("html_url") or "")
        if candidate:
            haystack = " ".join([
                str(row.get("title") or ""),
                str(row.get("abstract") or ""),
                " ".join(
                    str(agency.get("name") or "")
                    for agency in (row.get("agencies") or [])
                    if isinstance(agency, Mapping)
                ),
            ]).casefold()
            score = sum(term in haystack for term in terms)
            if score >= 3:
                matches.append((score, candidate, _parse_timestamp(row.get("publication_date"))))
    if not matches:
        return None
    _, candidate, published_at = sorted(matches, key=lambda row: (-row[0], row[1]))[0]
    return candidate, published_at


def _candidate_for_bls(body: bytes, request: Mapping[str, Any]) -> tuple[str, str | None] | None:
    text = body.decode("utf-8", errors="replace")
    terms = _terms(request)
    story_text = " ".join([
        *[str(value) for value in ((request.get("story_context") or {}).get("leaf_summaries") or [])],
        str((request.get("story_context") or {}).get("why_now") or ""),
    ]).casefold()
    links = re.findall(r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', text, re.IGNORECASE | re.DOTALL)
    scored: list[tuple[int, str]] = []
    for href, label in links:
        candidate = urljoin("https://www.bls.gov/bls/news-release/", href)
        if "/news.release/" not in candidate:
            continue
        haystack = f"{href} {label}".casefold()
        score = sum(term in haystack for term in terms)
        normalized_label = re.sub(r"<[^>]+>", " ", label).casefold()
        if "employment situation" in normalized_label and re.search(
            r"\b(non-?farm|payrolls?|workforce|labor market|employment situation)\b",
            story_text,
        ):
            score += 20
        if "job openings and labor turnover" in normalized_label and re.search(
            r"\b(job openings|turnover|jolts)\b", story_text
        ):
            score += 20
        if "consumer price index" in normalized_label and re.search(
            r"\b(consumer price|cpi|inflation)\b", story_text
        ):
            score += 20
        if "producer price index" in normalized_label and re.search(
            r"\b(producer price|ppi)\b", story_text
        ):
            score += 20
        if score:
            if candidate.endswith(".toc.htm"):
                candidate = candidate[:-8] + ".nr0.htm"
            scored.append((score, candidate))
    if not scored:
        return None
    return sorted(scored, key=lambda row: (-row[0], row[1]))[0][1], None


def _candidate_for_sec(body: bytes, request: Mapping[str, Any]) -> tuple[str, str | None] | None:
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    ordered_terms = _terms(request)
    terms = set(ordered_terms)
    rows = parsed.values() if isinstance(parsed, Mapping) else []
    matches: list[tuple[int, str]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        name_terms = set(re.findall(r"[A-Za-z][A-Za-z0-9'-]{2,}", str(row.get("title") or "").casefold()))
        matching_terms = terms.intersection(name_terms)
        # Prefer the earliest governed request terms (normally the named entity) over
        # later generic feed words such as ``income`` or ``results``.  The old count-only
        # tie-break could select an unrelated lower-CIK company when both matched once.
        score = sum(
            max(1, 20 - ordered_terms.index(term)) for term in matching_terms
        )
        cik = str(row.get("cik_str") or "")
        if cik and score:
            matches.append((score, f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"))
    if not matches:
        return None
    return sorted(matches, key=lambda row: (-row[0], row[1]))[0][1], None


def _candidate_for_federal_reserve(
    body: bytes, request: Mapping[str, Any]
) -> tuple[str, str | None] | None:
    """Deterministically locate a relevant first-party FOMC/Federal Reserve policy document.

    Discovery only: parses the official Federal Reserve FOMC calendar/listing page for links to
    individual monetary-policy documents (FOMC statements and implementation notes) on the same
    official host. Selects the most recent candidate whose embedded date does not exceed the
    evaluation cutoff, preferring candidates whose link/label matches the story terms. No search
    engine, no snippet evidence, no authority granted, no URL invented.
    """
    text = body.decode("utf-8", errors="replace")
    base_origin = BASE_ORIGIN_BY_FAMILY["official_policy"]
    # First-party FOMC monetary-policy document link shapes on federalreserve.gov.
    pattern = re.compile(
        r'href=["\']([^"\']*(?:newsevents/pressreleases/monetary|monetarypolicy/fomc)[\w.-]*\.htm)["\']',
        re.IGNORECASE,
    )
    terms = set(_terms(request))
    # Calendar page itself is not a usable statement candidate.
    raw_links = [
        href
        for href in pattern.findall(text)
        if "fomccalendars" not in href.casefold()
    ]
    if not raw_links:
        return None
    cutoff_text = str(request.get("evaluation_as_of_utc") or "")
    try:
        cutoff_date = datetime.fromisoformat(cutoff_text.replace("Z", "+00:00")).date()
    except ValueError:
        cutoff_date = None
    dated: list[tuple[date | None, int, str]] = []
    for href in raw_links:
        candidate = urljoin(base_origin, href)
        match = re.search(r"monetary[\w.-]*?(20\d{6})[\w.-]*\.htm", candidate, re.IGNORECASE) or re.search(
            r"monetary[\w.-]*?(20\d{2})[\w.-]*\.htm", candidate, re.IGNORECASE
        )
        candidate_date: date | None = None
        if match:
            token = match.group(1)
            if len(token) >= 8:
                try:
                    candidate_date = datetime.strptime(token[:8], "%Y%m%d").date()
                except ValueError:
                    candidate_date = None
            elif len(token) == 4:
                try:
                    candidate_date = datetime(int(token), 1, 1).date()
                except ValueError:
                    candidate_date = None
        if cutoff_date is not None and candidate_date is not None and candidate_date > cutoff_date:
            continue
        score = sum(term in candidate.casefold() for term in terms)
        dated.append((candidate_date, score, candidate))
    if not dated:
        return None
    # Most recent date first (None sorts last), then higher term score, then URL for stability.
    dated.sort(
        key=lambda row: (
            row[0] is None,
            -(row[0].toordinal() if row[0] else 0),
            -row[1],
            row[2],
        )
    )
    candidate_date, _score, candidate = dated[0]
    published_at = candidate_date.isoformat() if candidate_date else None
    return candidate, (_parse_timestamp(published_at) if published_at else None)


def _cutoff(request: Mapping[str, Any]) -> datetime:
    value = datetime.fromisoformat(
        str(request.get("evaluation_as_of_utc") or "").replace("Z", "+00:00")
    )
    if value.utcoffset() is None:
        raise ValueError("official_source_locator_evaluation_time_timezone_required")
    return value.astimezone(timezone.utc)


def _not_after_cutoff(timestamp: str | None, request: Mapping[str, Any]) -> bool:
    if timestamp is None:
        return True
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    return parsed <= _cutoff(request)


def _within_locator_window(
    timestamp: str | None, request: Mapping[str, Any], *, days: int
) -> bool:
    if timestamp is None:
        return False
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    cutoff = _cutoff(request)
    return cutoff - timedelta(days=days) <= parsed <= cutoff


def _candidate_for_eia_storage(
    body: bytes, request: Mapping[str, Any]
) -> tuple[str, str | None] | None:
    text = body.decode("utf-8", errors="replace")
    if not re.search(r"weekly working gas in underground storage", text, re.IGNORECASE):
        return None
    match = re.search(
        r"\brelease date\s*:\s*(\d{1,2}/\d{1,2}/\d{4})",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None
    try:
        published_at = _iso_utc(
            datetime.strptime(match.group(1), "%m/%d/%Y").replace(tzinfo=timezone.utc)
        )
    except ValueError:
        return None
    if not _not_after_cutoff(published_at, request):
        return None
    return "https://www.eia.gov/dnav/ng/ng_stor_wkly_s1_w.htm", published_at


def _candidate_for_philadelphia_fed_mbos(
    body: bytes, request: Mapping[str, Any]
) -> tuple[str, str | None] | None:
    text = body.decode("utf-8", errors="replace")
    link_match = re.search(
        r"sidebarData\.reportLink\s*=\s*['\"]"
        r"(/surveys-and-data/regional-economic-analysis/mbos-20\d{2}-\d{2})['\"]",
        text,
        re.IGNORECASE,
    )
    date_match = re.search(
        r"sidebarData\.publishedDate\s*=\s*['\"]([^'\"]+)['\"]",
        text,
        re.IGNORECASE,
    )
    if not link_match or not date_match:
        return None
    published_at = _parse_timestamp(date_match.group(1))
    if not published_at or not _not_after_cutoff(published_at, request):
        return None
    return urljoin("https://www.philadelphiafed.org/", link_match.group(1)), published_at


def _candidate_for_state_fms(
    body: bytes, request: Mapping[str, Any]
) -> tuple[str, str | None] | None:
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    terms = set(_terms(request))
    matches: list[tuple[int, str, str | None]] = []
    for row in parsed if isinstance(parsed, list) else []:
        if not isinstance(row, Mapping):
            continue
        candidate = str(row.get("link") or "")
        if not re.fullmatch(
            r"https://www\.state\.gov/releases/bureau-of-political-military-affairs/"
            r"20\d{2}/\d{2}/[a-z0-9-]+/",
            candidate,
        ):
            continue
        title_value = row.get("title") or {}
        title = str(
            title_value.get("rendered") if isinstance(title_value, Mapping) else title_value
        )
        score = sum(term in f"{title} {candidate}".casefold() for term in terms)
        published_at = _parse_timestamp(row.get("date_gmt") or row.get("date"))
        if score >= 2 and published_at and _not_after_cutoff(published_at, request):
            matches.append((score, candidate, published_at))
    if not matches:
        return None
    _score, candidate, published_at = sorted(
        matches, key=lambda row: (-row[0], row[1])
    )[0]
    return candidate, published_at


def _candidate_for_uscc_research(
    body: bytes, request: Mapping[str, Any]
) -> tuple[str, str | None] | None:
    text = body.decode("utf-8", errors="replace")
    terms = set(_terms(request))
    matches: list[tuple[int, str, str | None]] = []
    for row in re.finditer(
        r'<time\b[^>]*datetime=["\']([^"\']+)["\'][^>]*>.*?'
        r'<a\b[^>]*href=["\'](/research/[a-z0-9-]+)["\'][^>]*>(.*?)</a>',
        text,
        re.IGNORECASE | re.DOTALL,
    ):
        candidate = urljoin("https://www.uscc.gov/", row.group(2))
        label = html.unescape(re.sub(r"<[^>]+>", " ", row.group(3)))
        score = sum(term in f"{candidate} {label}".casefold() for term in terms)
        published_at = _parse_timestamp(row.group(1))
        if score >= 2 and published_at and _not_after_cutoff(published_at, request):
            matches.append((score, candidate, published_at))
    if not matches:
        return None
    _score, candidate, published_at = sorted(
        matches, key=lambda row: (-row[0], row[1])
    )[0]
    return candidate, published_at


def _candidate_for_waymo_blog(
    body: bytes, request: Mapping[str, Any]
) -> tuple[str, str | None] | None:
    text = body.decode("utf-8", errors="replace")
    terms = set(_terms(request))
    matches: list[tuple[int, str, str | None]] = []
    for item in re.findall(r"<item>(.*?)</item>", text, re.IGNORECASE | re.DOTALL):
        title_match = re.search(
            r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>",
            item,
            re.IGNORECASE | re.DOTALL,
        )
        link_match = re.search(r"<link>\s*([^<]+)\s*</link>", item, re.IGNORECASE)
        date_match = re.search(r"<pubDate>\s*([^<]+)\s*</pubDate>", item, re.IGNORECASE)
        description_match = re.search(
            r"<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>",
            item,
            re.IGNORECASE | re.DOTALL,
        )
        if not title_match or not link_match or not date_match:
            continue
        candidate = html.unescape(link_match.group(1)).rstrip("/")
        if not re.fullmatch(r"https://waymo\.com/blog/20\d{2}/\d{2}/[a-z0-9-]+", candidate):
            continue
        title = html.unescape(title_match.group(1))
        description = html.unescape(description_match.group(1)) if description_match else ""
        score = sum(
            term in f"{candidate} {title} {description}".casefold() for term in terms
        )
        published_at = _parse_timestamp(date_match.group(1))
        if score >= 2 and _within_locator_window(published_at, request, days=2):
            matches.append((score, candidate + "/", published_at))
    if not matches:
        return None
    _score, candidate, published_at = sorted(
        matches, key=lambda row: (-row[0], row[1])
    )[0]
    return candidate, published_at


def _candidate_for_surface(
    surface_id: str, body: bytes, request: Mapping[str, Any]
) -> tuple[str, str | None] | None:
    parsers = {
        "federal_register_documents_v1": _candidate_for_federal_register,
        "bls_news_releases_v1": _candidate_for_bls,
        "sec_company_ticker_index_v1": _candidate_for_sec,
        "federal_reserve_fomc_calendar_v1": _candidate_for_federal_reserve,
        "eia_weekly_natural_gas_storage_v1": _candidate_for_eia_storage,
        "philadelphia_fed_mbos_v1": _candidate_for_philadelphia_fed_mbos,
        "state_current_fms_press_releases_v1": _candidate_for_state_fms,
        "uscc_research_v1": _candidate_for_uscc_research,
        "waymo_company_blog_rss_v1": _candidate_for_waymo_blog,
    }
    return parsers[surface_id](body, request)


class BoundedOfficialPrimarySourceLocator:
    """Perform at most one deterministic first-party lookup for a request."""

    def __init__(
        self,
        *,
        http_get: Callable[[str, float, int], Mapping[str, Any]] | None = None,
        clock: Callable[[], datetime] | None = None,
        timeout_seconds: float = 12.0,
        max_response_bytes: int = 1_000_000,
    ) -> None:
        self._http_get = http_get or _default_http_get
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._timeout_seconds = timeout_seconds
        self._max_response_bytes = max_response_bytes

    def __call__(self, request: Mapping[str, Any]) -> dict[str, Any]:
        requested = [
            str(value)
            for value in (request.get("source_adapter_families") or [])
            if str(value) in LOCATOR_FAMILIES
        ]
        family = requested[0] if requested else ""
        if not family:
            return {"status": "BLOCKED", "blockers": ["official_source_locator_family_unsupported"]}
        exact_matches = _matching_surfaces(request)
        family_matches = [
            surface for surface in exact_matches if str(surface["family"]) == family
        ]
        if exact_matches and not family_matches:
            return {
                "status": "BLOCKED",
                "blockers": ["official_source_locator_surface_family_mismatch"],
            }
        if len(family_matches) > 1:
            return {
                "status": "BLOCKED",
                "blockers": ["official_source_locator_surface_ambiguous"],
            }
        surface = family_matches[0] if family_matches else LEGACY_SURFACE_BY_FAMILY[family]
        surface_id = str(surface["surface_id"])
        endpoint = str(surface["endpoint"])
        query = _query(request, family, surface_id)
        locator_url = endpoint
        if surface_id in {
            "federal_register_documents_v1",
            "state_current_fms_press_releases_v1",
        }:
            locator_url += "?" + urlencode(query)
        query_hash = _logical_hash({
            "family": family,
            "surface_id": surface_id,
            "endpoint": endpoint,
            "query": query,
            "cluster_id": request.get("cluster_id"),
            "headline_ids": list(request.get("headline_ids") or []),
        })
        try:
            _safe_url(locator_url, set(OFFICIAL_HOSTS_BY_FAMILY[family]))
            response = dict(self._http_get(locator_url, self._timeout_seconds, self._max_response_bytes))
            _safe_url(
                str(response.get("final_url") or locator_url),
                set(OFFICIAL_HOSTS_BY_FAMILY[family]),
            )
            body = response.get("body")
            if int(response.get("status") or 0) != 200:
                raise ValueError("official_source_locator_http_status_not_200")
            if response.get("content_truncated") is True:
                raise ValueError("official_source_locator_response_truncated")
            if not isinstance(body, bytes) or not body or len(body) > self._max_response_bytes:
                raise ValueError("official_source_locator_response_invalid")
            retrieved_at = _retrieval_timestamp(self._clock)
            candidate = _candidate_for_surface(surface_id, body, request)
            if not candidate:
                raise ValueError("official_source_locator_candidate_unavailable")
            candidate_url, published_at = candidate
            _safe_url(candidate_url, set(OFFICIAL_HOSTS_BY_FAMILY[family]))
            return {
                "status": "PASS",
                "source_adapter_family": family,
                "locator_surface_id": surface_id,
                "locator_endpoint": locator_url,
                "locator_query_logical_hash": query_hash,
                "retrieved_at_utc": retrieved_at,
                "evaluation_as_of_utc": request.get("evaluation_as_of_utc"),
                "candidate_official_url": candidate_url,
                "source_published_at_utc": published_at,
                "locator_response_sha256": sha256(body).hexdigest(),
                "discovery_only": True,
                "factual_authority": False,
                "evidence_capabilities": [],
                "publication_authority": False,
            }
        except (OSError, TypeError, ValueError) as exc:
            return {
                "status": "BLOCKED",
                "locator_surface_id": surface_id,
                "locator_endpoint": locator_url,
                "locator_query_logical_hash": query_hash,
                "blockers": [str(exc) or type(exc).__name__],
            }
