"""Bounded deterministic lookup of candidate URLs on first-party official endpoints."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
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
    ]
    terms: list[str] = []
    for value in values:
        for term in re.findall(r"[A-Za-z][A-Za-z0-9'-]{2,}", str(value or "")):
            normalized = term.casefold()
            if normalized not in terms and normalized not in {"the", "and", "for", "with", "from", "that", "this"}:
                terms.append(normalized)
    return terms[:12]


def _query(request: Mapping[str, Any], family: str) -> dict[str, str]:
    terms = _terms(request)
    context = request.get("story_context") or {}
    if family == "official_regulatory_fiscal":
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
        endpoint = LOCATOR_ENDPOINTS[family]
        query = _query(request, family)
        locator_url = endpoint + ("?" + urlencode(query) if family == "official_regulatory_fiscal" else "")
        query_hash = _logical_hash({
            "family": family,
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
            if family == "official_regulatory_fiscal":
                candidate = _candidate_for_federal_register(body, request)
            elif family == "official_macro":
                candidate = _candidate_for_bls(body, request)
            elif family == "official_policy":
                candidate = _candidate_for_federal_reserve(body, request)
            else:
                candidate = _candidate_for_sec(body, request)
            if not candidate:
                raise ValueError("official_source_locator_candidate_unavailable")
            candidate_url, published_at = candidate
            _safe_url(candidate_url, set(OFFICIAL_HOSTS_BY_FAMILY[family]))
            return {
                "status": "PASS",
                "source_adapter_family": family,
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
                "locator_endpoint": locator_url,
                "locator_query_logical_hash": query_hash,
                "blockers": [str(exc) or type(exc).__name__],
            }
