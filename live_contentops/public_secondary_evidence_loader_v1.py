"""Bounded public first-party and reputable-secondary evidence acquisition.

The loader is a focused fallback inside the canonical rolling-X evidence adapter.  It performs
read-only public GETs, rejects social/paywall bypass behaviour, and never grants publication
authority.  Public news listings are useful only as corroborated, attributed secondary evidence.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
import ipaddress
import re
import socket
from typing import Any, Callable, Mapping
from urllib.parse import urlencode, urlsplit
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

from live_contentops.official_primary_evidence_loader_v1 import (
    USER_AGENT,
    _html_timestamp,
    _iso_utc,
    _parse_timestamp,
)
from live_contentops.claim_evidence_contract_v1 import summarize_evidence_substance
from live_contentops.source_route_health_v1 import (
    SourceRouteHealthState,
    normalized_host,
)


REPUTABLE_SECONDARY_HOSTS = frozenset(
    {
        "abcnews.go.com", "aljazeera.com", "apnews.com", "axios.com", "bbc.com",
        "bbc.co.uk", "bloomberg.com", "cbsnews.com", "cnbc.com", "cnn.com", "ft.com",
        "financialjuice.com", "marketwatch.com", "nbcnews.com", "npr.org", "politico.com", "reuters.com",
        "theguardian.com", "thehill.com", "jpost.com", "wsj.com", "www.abcnews.go.com",
        "www.aljazeera.com", "www.apnews.com", "www.axios.com", "www.bbc.com",
        "www.bloomberg.com", "www.cbsnews.com", "www.cnbc.com", "www.cnn.com", "www.financialjuice.com", "www.ft.com",
        "www.marketwatch.com", "www.nbcnews.com", "www.npr.org", "www.politico.com",
        "www.reuters.com", "www.theguardian.com", "www.thehill.com", "www.jpost.com", "www.wsj.com",
    }
)
REPUTABLE_SECONDARY_NAMES = frozenset(
    {
        "abc news", "al jazeera", "associated press", "the associated press", "ap", "ap news", "axios", "bbc", "bloomberg",
        "cbs news", "cnbc", "cnn", "financial times", "financialjuice", "marketwatch", "nbc news", "npr",
        "politico", "reuters", "the guardian", "the hill", "the jerusalem post",
        "jerusalem post", "the wall street journal", "wsj",
    }
)
# Exact, publisher-controlled short-link origins that may redirect only into the
# corresponding registered publisher family. They are locators, never evidence.
SAFE_PUBLISHER_SHORT_HOST_TARGETS = {
    "cnb.cx": "cnbc.com",
}
NEWS_RSS_ENDPOINT = "https://news.google.com/rss/search"
PUBLISHER_NEWS_SITEMAP_PATH = "/news-sitemap.xml"
PUBLISHER_ROBOTS_PATH = "/robots.txt"
PUBLISHER_GENERIC_SITEMAP_PATH = "/sitemap.xml"
MAX_PUBLISHER_RESOLUTION_ATTEMPTS = 2
MAX_PUBLISHER_SITEMAP_INDEX_CHILDREN = 1
MIN_PUBLISHER_SITEMAP_CANDIDATE_RELEVANCE = 0.5
MIN_RESOLVED_PUBLISHER_TITLE_RELEVANCE = 0.72
_TAG_RE = re.compile(r"<[^>]+>")
_SCRIPT_RE = re.compile(r"<(?:script|style|noscript)[^>]*>.*?</(?:script|style|noscript)>", re.I | re.S)
_RSS_QUERY_STOPWORDS = frozenset(
    {"a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "its", "of", "on", "or", "the", "to", "with"}
)
_RSS_DESK_LABEL_RE = re.compile(
    r"^(?:breaking|exclusive|analysis|opinion|live|update)\s*[|:\-]\s*", re.I
)
_RSS_TRAILING_PUBLISHER_RE = re.compile(
    r"\s+-\s+(?:AP|Associated Press|BBC|Bloomberg|CNBC|CNN|Financial Times|FT|Reuters|The Guardian|WSJ)\s*$",
    re.I,
)


def _public_host(url: str, *, resolve_dns: bool = True) -> str:
    parsed = urlsplit(url)
    host = str(parsed.hostname or "").casefold()
    if (
        parsed.scheme != "https"
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in {None, 443}
    ):
        raise ValueError("public_source_url_invalid")
    if resolve_dns:
        try:
            addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise ValueError("public_source_dns_unavailable") from exc
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if not ip.is_global:
                raise ValueError("public_source_nonpublic_address_forbidden")
    return host


def _default_public_http_get(url: str, timeout_seconds: float, max_bytes: int) -> dict[str, Any]:
    """GET a public source while allowing only a discovery-to-reputable redirect."""
    requested_host = _public_host(url)

    class _BoundedPublicRedirects(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            redirected_host = _public_host(newurl)
            allowed = (
                redirected_host == "news.google.com"
                or redirected_host in REPUTABLE_SECONDARY_HOSTS
            )
            if requested_host != "news.google.com":
                publisher_target = SAFE_PUBLISHER_SHORT_HOST_TARGETS.get(
                    normalized_host(requested_host), normalized_host(requested_host)
                )
                allowed = (
                    redirected_host in REPUTABLE_SECONDARY_HOSTS
                    and normalized_host(redirected_host) == publisher_target
                )
            if not allowed:
                raise ValueError("public_source_redirect_authority_invalid")
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Accept": "text/html, application/xhtml+xml, text/plain, application/xml",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.build_opener(_BoundedPublicRedirects).open(
        request, timeout=timeout_seconds
    ) as response:
        body = response.read(max_bytes + 1)
        truncated = len(body) > max_bytes
        if truncated:
            body = body[:max_bytes]
        return {
            "status": int(response.status),
            "final_url": str(response.geturl()),
            "headers": {
                str(key).casefold(): str(value)
                for key, value in response.headers.items()
            },
            "body": body,
            "content_truncated": truncated,
        }


def _title(text: str) -> str:
    patterns = (
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+name=["\']twitter:title["\'][^>]+content=["\']([^"\']+)',
        r"<title[^>]*>(.*?)</title>",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.I | re.S)
        if match:
            return " ".join(unescape(_TAG_RE.sub(" ", match.group(1))).split())[:500]
    return ""


def _public_text(body: bytes, content_type: str) -> str:
    if content_type not in {"text/html", "text/plain", "application/xhtml+xml"}:
        return ""
    text = body.decode("utf-8", errors="replace")
    if content_type == "text/plain":
        return " ".join(text.split())[:100_000]
    visible = _SCRIPT_RE.sub(" ", text)
    visible = unescape(_TAG_RE.sub(" ", visible))
    return " ".join(visible.split())[:100_000]


def _publisher_from_host(host: str) -> str:
    core = host.removeprefix("www.").split(".")[0]
    return core.replace("-", " ").title()


def _rss_query_terms(summary: str) -> list[str]:
    """Remove feed/desk metadata while retaining the event-bearing headline terms."""
    cleaned = " ".join(unescape(summary).split())
    cleaned = _RSS_DESK_LABEL_RE.sub("", cleaned)
    cleaned = _RSS_TRAILING_PUBLISHER_RE.sub("", cleaned)
    cleaned = re.sub(r"\bU\.S\.", "US", cleaned, flags=re.I)
    cleaned = re.sub(r"\bU\.K\.", "UK", cleaned, flags=re.I)
    return [
        token
        for token in re.findall(r"[A-Za-z][A-Za-z0-9'-]{1,}", cleaned)
        if token.casefold() not in _RSS_QUERY_STOPWORDS
    ][:12]


def _rss_relevance_score(query_terms: list[str], title: str) -> float:
    """Score a short publisher title against a longer event-bearing locator query.

    The previous query-denominator-only score rejected exact short headlines when a
    proposition contained attribution boilerplate. A symmetric denominator plus a
    conservative four-character morphology match retains precision while recognizing
    pairs such as ``Iranian``/``Iran`` and ``market``/``markets``.
    """
    query = {token.casefold().strip("'\"") for token in query_terms}
    title_terms = {
        token.casefold().strip("'\"") for token in _rss_query_terms(title)
    }
    if not query or not title_terms:
        return 0.0

    def same_family(left: str, right: str) -> bool:
        if left == right:
            return True
        common = min(len(left), len(right))
        return common >= 4 and (
            left.startswith(right)
            or right.startswith(left)
            or left[:4] == right[:4]
        )

    matched_title_terms = {
        title_term
        for title_term in title_terms
        if any(same_family(query_term, title_term) for query_term in query)
    }
    return len(matched_title_terms) / min(len(query), len(title_terms))


class BoundedPublicSecondaryEvidenceLoader:
    """Acquire a few public sources or corroborated reputable news-listing records."""

    def __init__(
        self,
        *,
        evaluation_as_of_utc: str,
        max_requests: int = 24,
        max_requests_per_candidate: int = 6,
        timeout_seconds: float = 12.0,
        max_response_bytes: int = 800_000,
        http_get: Callable[[str, float, int], Mapping[str, Any]] | None = None,
        clock: Callable[[], datetime] | None = None,
        source_route_health: SourceRouteHealthState | Mapping[str, Any] | None = None,
        shared_request_budget: dict[str, int] | None = None,
    ) -> None:
        cutoff = datetime.fromisoformat(evaluation_as_of_utc.replace("Z", "+00:00"))
        if cutoff.utcoffset() is None:
            raise ValueError("public_source_evaluation_time_timezone_required")
        self._evaluation_as_of_utc = _iso_utc(cutoff)
        self._max_requests = max_requests
        self._max_requests_per_candidate = max(1, min(max_requests_per_candidate, max_requests))
        self._timeout_seconds = timeout_seconds
        self._max_response_bytes = max_response_bytes
        self._http_get = http_get or _default_public_http_get
        self._validate_dns = http_get is None
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._source_route_health = (
            source_route_health
            if isinstance(source_route_health, SourceRouteHealthState)
            else SourceRouteHealthState(source_route_health, clock=self._clock)
        )
        self._request_count = 0
        self._shared_request_budget = shared_request_budget
        self._candidate_request_start = 0
        self._request_count_by_story_scope: dict[str, int] = {}
        self._active_story_scope_id: str | None = None
        self._response_cache_by_story_scope: dict[
            str, dict[str, dict[str, Any]]
        ] = {}
        self._reused_request_signatures_by_story_scope: dict[str, list[str]] = {}

    def _consume_request(self) -> None:
        if self._request_count >= self._max_requests:
            raise RuntimeError("public_source_request_budget_exhausted")
        if self._shared_request_budget is not None:
            used = int(self._shared_request_budget.get("used") or 0)
            limit = int(self._shared_request_budget.get("limit") or 0)
            if used >= limit:
                raise RuntimeError("public_source_request_budget_exhausted")
            self._shared_request_budget["used"] = used + 1
        self._request_count += 1

    def _get(self, url: str) -> dict[str, Any]:
        if self._active_story_scope_id:
            cached = self._response_cache_by_story_scope.get(
                self._active_story_scope_id, {}
            ).get(url)
            if cached is not None:
                self._reused_request_signatures_by_story_scope.setdefault(
                    self._active_story_scope_id, []
                ).append(sha256(url.encode("utf-8")).hexdigest())
                return dict(cached)
        suppressed = self._source_route_health.should_suppress(url)
        if suppressed is not None:
            if self._active_story_scope_id:
                self._reused_request_signatures_by_story_scope.setdefault(
                    self._active_story_scope_id, []
                ).append(str(suppressed["route_identity_sha256"]))
            raise RuntimeError("public_source_route_suppressed_by_recent_health")
        candidate_request_count = (
            self._request_count_by_story_scope.get(self._active_story_scope_id, 0)
            if self._active_story_scope_id
            else self._request_count - self._candidate_request_start
        )
        if candidate_request_count >= self._max_requests_per_candidate:
            raise RuntimeError("public_source_candidate_request_budget_exhausted")
        _public_host(url, resolve_dns=self._validate_dns)
        self._consume_request()
        if self._active_story_scope_id:
            self._request_count_by_story_scope[self._active_story_scope_id] = (
                candidate_request_count + 1
            )
        try:
            response = dict(
                self._http_get(url, self._timeout_seconds, self._max_response_bytes)
            )
        except urllib.error.HTTPError as exc:
            self._source_route_health.observe_failure(url, int(exc.code))
            raise
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            self._source_route_health.observe_failure(url, exc)
            raise
        status = int(response.get("status") or 0)
        if status == 200:
            self._source_route_health.observe_success(url)
        else:
            self._source_route_health.observe_failure(url, status)
        if self._active_story_scope_id:
            self._response_cache_by_story_scope.setdefault(
                self._active_story_scope_id, {}
            )[url] = dict(response)
        return response

    def _direct_document(
        self,
        url: str,
        headline_id: str,
        *,
        published_at_hint: str | None = None,
    ) -> dict[str, Any] | None:
        host = _public_host(url, resolve_dns=self._validate_dns)
        discovery_redirect = host == "news.google.com"
        publisher_short_link = normalized_host(host) in SAFE_PUBLISHER_SHORT_HOST_TARGETS
        if (
            host not in REPUTABLE_SECONDARY_HOSTS
            and not discovery_redirect
            and not publisher_short_link
        ):
            return None
        response = self._get(url)
        if int(response.get("status") or 0) != 200:
            raise ValueError("public_source_http_status_not_200")
        final_url = str(response.get("final_url") or url)
        final_host = _public_host(final_url, resolve_dns=self._validate_dns)
        if final_host not in REPUTABLE_SECONDARY_HOSTS:
            raise ValueError("public_source_redirect_authority_invalid")
        if publisher_short_link and normalized_host(final_host) != (
            SAFE_PUBLISHER_SHORT_HOST_TARGETS[normalized_host(host)]
        ):
            raise ValueError("public_source_redirect_authority_invalid")
        headers = {str(k).casefold(): str(v) for k, v in (response.get("headers") or {}).items()}
        content_type = headers.get("content-type", "").split(";", 1)[0].casefold()
        body = response.get("body")
        if not isinstance(body, bytes) or not body:
            raise ValueError("public_source_body_invalid")
        raw = body.decode("utf-8", errors="replace")
        title = _title(raw) or final_url.rsplit("/", 1)[-1].replace("-", " ")
        publisher_timestamp = _html_timestamp(raw) or _parse_timestamp(
            headers.get("last-modified")
        )
        published = publisher_timestamp or _parse_timestamp(published_at_hint)
        if not published:
            raise ValueError("public_source_published_timestamp_unavailable")
        if datetime.fromisoformat(published.replace("Z", "+00:00")) > datetime.fromisoformat(
            self._evaluation_as_of_utc.replace("Z", "+00:00")
        ):
            raise ValueError("public_source_published_after_evaluation_cutoff")
        text = _public_text(body, content_type)
        if len(text) < 80:
            raise ValueError("public_source_relevant_text_unavailable")
        return {
            "document_id": "public-secondary-" + sha256(body).hexdigest()[:20],
            "title": title,
            "publisher": _publisher_from_host(final_host),
            "source_identity": final_host,
            "source_authority_class": "reputable_secondary_source",
            "source_url": final_url,
            "reader_source_url": final_url,
            "requested_source_url": url,
            "discovery_path_url": url if discovery_redirect else None,
            "discovery_path_is_reader_authority": False,
            "source_headline_id": headline_id,
            "published_at_utc": published,
            "published_at_source": (
                "PUBLISHER_BYTES_OR_HEADERS"
                if publisher_timestamp
                else "EXACT_BOUND_DISCOVERY_TIMESTAMP"
            ),
            "event_time_utc": published,
            "raw_sha256": sha256(body).hexdigest(),
            "canonical_content_sha256": sha256(text.encode("utf-8")).hexdigest(),
            "canonical_content_text": text,
            "content_type": content_type,
            "byte_length": len(body),
            "content_truncated": bool(response.get("content_truncated")),
            "public_claim_allowed": True,
            "retrieval_method": "READ_ONLY_PUBLIC_HTTP_GET",
            "canonical_resolution_status": (
                "RESOLVED_FROM_DISCOVERY_REDIRECT"
                if discovery_redirect
                else "DIRECT_PUBLISHER_URL"
            ),
        }

    def _publisher_sitemap_candidate(
        self, listing: Mapping[str, Any]
    ) -> tuple[dict[str, Any] | None, list[str]]:
        """Resolve a listing through bounded same-publisher declared sitemap paths.

        The sitemap is locator evidence only. Its candidate must strongly match the
        discovery title and the exact publisher article is fetched separately before
        any public-claim authority is granted.
        """
        diagnostics: list[str] = []
        source_host = str(listing.get("source_identity") or "").casefold()
        if source_host not in REPUTABLE_SECONDARY_HOSTS:
            return None, diagnostics
        publisher_home_url = str(listing.get("publisher_home_url") or "")
        publisher_home_host = _public_host(
            publisher_home_url, resolve_dns=self._validate_dns
        )
        if publisher_home_host.removeprefix("www.") != source_host.removeprefix(
            "www."
        ):
            raise ValueError("publisher_news_sitemap_identity_mismatch")
        parsed_home = urlsplit(publisher_home_url)
        publisher_origin = f"{parsed_home.scheme}://{parsed_home.netloc}"
        locator_chain: list[dict[str, str]] = []

        def fetch_xml(url: str, *, failure_prefix: str) -> tuple[ET.Element, bytes] | None:
            try:
                if normalized_host(_public_host(url, resolve_dns=False)) != normalized_host(
                    source_host
                ):
                    raise ValueError("publisher_sitemap_cross_host_forbidden")
                response = self._get(url)
                if int(response.get("status") or 0) != 200:
                    raise ValueError(f"{failure_prefix}_http_status_not_200")
                final_url = str(response.get("final_url") or url)
                if normalized_host(
                    _public_host(final_url, resolve_dns=False)
                ) != normalized_host(source_host):
                    raise ValueError("publisher_sitemap_redirect_identity_mismatch")
                body = response.get("body")
                if not isinstance(body, bytes) or not body:
                    raise ValueError(f"{failure_prefix}_body_invalid")
                root = ET.fromstring(body)
                locator_chain.append(
                    {"url": final_url, "sha256": sha256(body).hexdigest()}
                )
                return root, body
            except (ET.ParseError, OSError, RuntimeError, TypeError, ValueError) as exc:
                diagnostics.append(str(exc) or f"{failure_prefix}_unavailable")
                return None

        locator_url = publisher_origin + PUBLISHER_NEWS_SITEMAP_PATH
        fetched = fetch_xml(
            locator_url, failure_prefix="publisher_news_sitemap"
        )
        resolution_method = "PUBLISHER_NEWS_SITEMAP"
        if fetched is None:
            robots_url = publisher_origin + PUBLISHER_ROBOTS_PATH
            declared_urls: list[str] = []
            try:
                robots = self._get(robots_url)
                robots_body = robots.get("body")
                if int(robots.get("status") or 0) != 200 or not isinstance(
                    robots_body, bytes
                ):
                    raise ValueError("publisher_robots_unavailable")
                robots_final_url = str(robots.get("final_url") or robots_url)
                if normalized_host(
                    _public_host(robots_final_url, resolve_dns=False)
                ) != normalized_host(source_host):
                    raise ValueError("publisher_robots_redirect_identity_mismatch")
                locator_chain.append(
                    {
                        "url": robots_final_url,
                        "sha256": sha256(robots_body).hexdigest(),
                    }
                )
                for match in re.findall(
                    r"(?im)^\s*Sitemap\s*:\s*(https://\S+)\s*$",
                    robots_body.decode("utf-8", errors="replace"),
                ):
                    try:
                        if normalized_host(
                            _public_host(match, resolve_dns=False)
                        ) == normalized_host(source_host):
                            declared_urls.append(match)
                    except ValueError:
                        continue
            except (OSError, RuntimeError, TypeError, ValueError) as exc:
                diagnostics.append(str(exc) or "publisher_robots_unavailable")
            declared_urls = sorted(
                dict.fromkeys(declared_urls),
                key=lambda value: (
                    0 if "news" in value.casefold() else 1 if "post" in value.casefold() else 2,
                    value,
                ),
            )
            if not declared_urls:
                declared_urls = [publisher_origin + PUBLISHER_GENERIC_SITEMAP_PATH]
            locator_url = declared_urls[0]
            fetched = fetch_xml(
                locator_url, failure_prefix="publisher_declared_sitemap"
            )
            resolution_method = "PUBLISHER_DECLARED_SITEMAP"
        if fetched is None:
            return None, diagnostics
        root, body = fetched
        if str(root.tag).rsplit("}", 1)[-1].casefold() == "sitemapindex":
            child_rows: list[tuple[int, float, str]] = []
            for sitemap_row in root:
                if str(sitemap_row.tag).rsplit("}", 1)[-1].casefold() != "sitemap":
                    continue
                child_url = next(
                    (
                        " ".join(str(child.text or "").split())
                        for child in sitemap_row
                        if str(child.tag).rsplit("}", 1)[-1].casefold() == "loc"
                        and str(child.text or "").strip()
                    ),
                    "",
                )
                if not child_url:
                    continue
                try:
                    child_host = _public_host(child_url, resolve_dns=False)
                except ValueError:
                    continue
                if child_host.removeprefix("www.") != source_host.removeprefix("www."):
                    continue
                lastmod = next(
                    (
                        _parse_timestamp(str(child.text or ""))
                        for child in sitemap_row
                        if str(child.tag).rsplit("}", 1)[-1].casefold()
                        == "lastmod"
                        and str(child.text or "").strip()
                    ),
                    None,
                )
                lastmod_epoch = (
                    datetime.fromisoformat(lastmod.replace("Z", "+00:00")).timestamp()
                    if lastmod
                    else 0.0
                )
                priority = (
                    0
                    if "news" in child_url.casefold()
                    else 1
                    if "post" in child_url.casefold()
                    else 2
                )
                child_rows.append((priority, -lastmod_epoch, child_url))
            for _priority, _lastmod, child_url in sorted(child_rows)[
                :MAX_PUBLISHER_SITEMAP_INDEX_CHILDREN
            ]:
                child = fetch_xml(
                    child_url,
                    failure_prefix="publisher_sitemap_child",
                )
                if child is not None:
                    root, body = child
                    locator_url = child_url
                    break

        listing_title = str(listing.get("title") or "")
        listing_terms = _rss_query_terms(listing_title)
        cutoff = datetime.fromisoformat(
            self._evaluation_as_of_utc.replace("Z", "+00:00")
        )
        candidates: list[tuple[float, float, str, str | None, str]] = []
        for url_row in root.iter():
            if not str(url_row.tag).casefold().endswith("url"):
                continue
            fields: dict[str, str] = {}
            for child in url_row.iter():
                local_name = str(child.tag).rsplit("}", 1)[-1].casefold()
                value = " ".join(str(child.text or "").split())
                if value and local_name in {"loc", "title", "publication_date"}:
                    fields[local_name] = value
            candidate_url = fields.get("loc", "")
            candidate_title = fields.get("title", "")
            if not candidate_url or not candidate_title:
                continue
            try:
                candidate_host = _public_host(candidate_url, resolve_dns=False)
            except ValueError:
                continue
            if candidate_host.removeprefix("www.") != source_host.removeprefix("www."):
                continue
            relevance = _rss_relevance_score(listing_terms, candidate_title)
            if relevance < MIN_PUBLISHER_SITEMAP_CANDIDATE_RELEVANCE:
                continue
            published = _parse_timestamp(fields.get("publication_date"))
            if published:
                observed = datetime.fromisoformat(published.replace("Z", "+00:00"))
                if observed > cutoff:
                    continue
                distance = abs(
                    observed.timestamp()
                    - datetime.fromisoformat(
                        str(listing.get("published_at_utc") or published).replace(
                            "Z", "+00:00"
                        )
                    ).timestamp()
                )
            else:
                distance = float("inf")
            candidates.append(
                (relevance, distance, candidate_url, published, candidate_title)
            )
        if not candidates:
            diagnostics.append("publisher_sitemap_relevant_candidate_unavailable")
            return None, diagnostics
        relevance, _distance, candidate_url, published, candidate_title = sorted(
            candidates,
            key=lambda row: (-row[0], row[1], row[2]),
        )[0]
        return {
            "source_url": candidate_url,
            "published_at_utc": published,
            "title": candidate_title,
            "title_relevance": round(relevance, 4),
            "locator_url": locator_url,
            "locator_sha256": sha256(body).hexdigest(),
            "locator_chain": locator_chain,
            "resolution_method": resolution_method,
        }, diagnostics

    def _resolve_listing_to_publisher_document(
        self, listing: Mapping[str, Any]
    ) -> tuple[dict[str, Any] | None, list[str]]:
        diagnostics: list[str] = []
        candidate: dict[str, Any] | None = None
        try:
            candidate, sitemap_diagnostics = self._publisher_sitemap_candidate(
                listing
            )
            diagnostics.extend(sitemap_diagnostics)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            diagnostics.append(str(exc) or type(exc).__name__)
        if candidate is not None:
            try:
                document = self._direct_document(
                    str(candidate["source_url"]),
                    str(listing.get("source_headline_id") or ""),
                    published_at_hint=str(candidate.get("published_at_utc") or "")
                    or str(listing.get("published_at_utc") or "")
                    or None,
                )
                if document is not None:
                    resolved_title_relevance = _rss_relevance_score(
                        _rss_query_terms(str(listing.get("title") or "")),
                        str(document.get("title") or ""),
                    )
                    if resolved_title_relevance < MIN_RESOLVED_PUBLISHER_TITLE_RELEVANCE:
                        diagnostics.append(
                            "publisher_document_title_relevance_insufficient"
                        )
                        document = None
                if document is not None:
                    document.update(
                        {
                            "discovery_path_url": listing.get("source_url"),
                            "discovery_path_is_reader_authority": False,
                            "publisher_locator_url": candidate["locator_url"],
                            "publisher_locator_sha256": candidate["locator_sha256"],
                            "publisher_locator_chain": list(
                                candidate.get("locator_chain") or []
                            ),
                            "publisher_locator_title_relevance": candidate[
                                "title_relevance"
                            ],
                            "publisher_document_title_relevance": round(
                                resolved_title_relevance, 4
                            ),
                            "canonical_resolution_status": (
                                "RESOLVED_FROM_PUBLISHER_DECLARED_SITEMAP"
                                if candidate.get("resolution_method")
                                == "PUBLISHER_DECLARED_SITEMAP"
                                else "RESOLVED_FROM_PUBLISHER_NEWS_SITEMAP"
                            ),
                        }
                    )
                    return document, diagnostics
            except (OSError, RuntimeError, TypeError, ValueError) as exc:
                diagnostics.append(str(exc) or type(exc).__name__)

        # Retain the bounded legacy redirect path for Google News link forms that do
        # issue a direct redirect to an allowlisted publisher.
        try:
            return (
                self._direct_document(
                    str(listing.get("source_url") or ""),
                    str(listing.get("source_headline_id") or ""),
                    published_at_hint=str(listing.get("published_at_utc") or "")
                    or None,
                ),
                diagnostics,
            )
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            diagnostics.append(str(exc) or type(exc).__name__)
            return None, diagnostics

    def _enough_with_existing(
        self, request: Mapping[str, Any], documents: list[dict[str, Any]]
    ) -> bool:
        own = summarize_evidence_substance(request, documents)
        enrichment = request.get("evidence_enrichment_context")
        enrichment = enrichment if isinstance(enrichment, Mapping) else {}
        existing = enrichment.get("existing_evidence_substance")
        existing = existing if isinstance(existing, Mapping) else {}
        target = int(own.get("target_usable_content_words") or 0)
        combined = int(existing.get("usable_content_words") or 0) + int(
            own.get("usable_content_words") or 0
        )
        return combined >= target

    def _rss_documents(
        self,
        request: Mapping[str, Any],
        *,
        existing_documents: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        context = request.get("story_context") or {}
        planned_queries = [
            " ".join(str(value).split())
            for value in context.get("grounded_research_queries") or []
            if str(value).strip()
        ][:3]
        summaries = planned_queries or [
            " ".join(str(value).split())
            for value in (context.get("leaf_summaries") or [])
            if str(value).strip()
        ]
        query_terms = [
            terms for terms in (_rss_query_terms(value) for value in summaries[:3]) if terms
        ]
        if not query_terms:
            return [], {
                "locator_candidate_count": 0,
                "publisher_resolution_attempt_count": 0,
                "publisher_resolution_diagnostics": [],
            }
        cutoff = datetime.fromisoformat(
            self._evaluation_as_of_utc.replace("Z", "+00:00")
        )
        resolved: list[dict[str, Any]] = []
        seen_publishers: set[str] = set()
        source_resolution_attempts = 0
        locator_candidate_count = 0
        resolution_diagnostics: list[str] = []
        for terms in query_terms:
            url = NEWS_RSS_ENDPOINT + "?" + urlencode(
                {"q": " ".join(terms), "hl": "en-US", "gl": "US", "ceid": "US:en"}
            )
            response = self._get(url)
            body = response.get("body")
            if int(response.get("status") or 0) != 200 or not isinstance(body, bytes) or not body:
                continue
            try:
                root = ET.fromstring(body)
            except ET.ParseError:
                continue
            candidates: dict[str, tuple[float, datetime, dict[str, Any]]] = {}
            for item in root.findall(".//item"):
                source = item.find("source")
                publisher = " ".join(str(source.text or "").split()) if source is not None else ""
                if publisher.casefold() not in REPUTABLE_SECONDARY_NAMES:
                    continue
                try:
                    source_host = _public_host(
                        str(source.get("url") or ""), resolve_dns=False
                    )
                except ValueError:
                    continue
                if source_host not in REPUTABLE_SECONDARY_HOSTS:
                    continue
                identity = source_host.removeprefix("www.")
                title = " ".join(str(item.findtext("title") or "").rsplit(" - ", 1)[0].split())
                link = str(item.findtext("link") or "")
                published = _parse_timestamp(item.findtext("pubDate"))
                if not title or not link or not published:
                    continue
                observed = datetime.fromisoformat(published.replace("Z", "+00:00"))
                relevance = _rss_relevance_score(terms, title)
                if observed > cutoff or relevance < 0.34:
                    continue
                item_bytes = ET.tostring(item, encoding="utf-8")
                document = {
                    "document_id": "public-news-listing-" + sha256(item_bytes).hexdigest()[:20],
                    "title": title,
                    "publisher": publisher,
                    "source_identity": identity,
                    "publisher_home_url": str(source.get("url") or ""),
                    "source_authority_class": "reputable_secondary_source",
                    "source_url": link,
                    "published_at_utc": published,
                    "event_time_utc": published,
                    "raw_sha256": sha256(item_bytes).hexdigest(),
                    "canonical_content_sha256": sha256(title.encode("utf-8")).hexdigest(),
                    "canonical_content_text": title,
                    "content_type": "application/rss+xml",
                    "byte_length": len(item_bytes),
                    "public_claim_allowed": True,
                    "retrieval_method": "READ_ONLY_PUBLIC_NEWS_RSS",
                    "secondary_listing_only": True,
                    "research_query_terms": terms,
                    "source_headline_id": str(
                        (request.get("headline_ids") or [""])[0]
                    ),
                }
                existing = candidates.get(identity)
                candidate = (relevance, observed, document)
                if existing is None or (relevance, observed) > (existing[0], existing[1]):
                    candidates[identity] = candidate
            ranked = sorted(
                candidates.values(),
                key=lambda row: (
                    -row[0],
                    -row[1].timestamp(),
                    str(row[2].get("publisher") or "").casefold(),
                    str(row[2].get("title") or "").casefold(),
                ),
            )
            locator_candidate_count += len(ranked)
            for _relevance, _observed, listing in ranked:
                identity = str(listing.get("source_identity") or "").casefold()
                if (
                    identity in seen_publishers
                    or source_resolution_attempts
                    >= MAX_PUBLISHER_RESOLUTION_ATTEMPTS
                ):
                    continue
                seen_publishers.add(identity)
                source_resolution_attempts += 1
                document, failures = self._resolve_listing_to_publisher_document(
                    listing
                )
                resolution_diagnostics.extend(failures)
                if document is None:
                    listing["reader_source_url"] = None
                    listing["reader_attribution_mode"] = "ATTRIBUTION_ONLY"
                    listing["discovery_path_is_reader_authority"] = False
                    listing["canonical_resolution_status"] = (
                        "PUBLISHER_URL_UNRESOLVED_ATTRIBUTION_ONLY"
                    )
                    listing["public_claim_allowed"] = False
                    listing["locator_or_attribution_only"] = True
                    document = listing
                resolved.append(document)
                if self._enough_with_existing(request, existing_documents + resolved):
                    return resolved, {
                        "locator_candidate_count": locator_candidate_count,
                        "publisher_resolution_attempt_count": source_resolution_attempts,
                        "publisher_resolution_diagnostics": sorted(
                            set(resolution_diagnostics)
                        ),
                    }
            if source_resolution_attempts >= MAX_PUBLISHER_RESOLUTION_ATTEMPTS:
                break
        return resolved, {
            "locator_candidate_count": locator_candidate_count,
            "publisher_resolution_attempt_count": source_resolution_attempts,
            "publisher_resolution_diagnostics": sorted(
                set(resolution_diagnostics)
            ),
        }

    def __call__(self, request: Mapping[str, Any]) -> dict[str, Any]:
        request_count_at_start = self._request_count
        story_scope_id = str(request.get("story_evidence_scope_id") or "")
        story_request_count_at_start = self._request_count_by_story_scope.get(
            story_scope_id, 0
        )
        reused_signature_count_at_start = len(
            self._reused_request_signatures_by_story_scope.get(story_scope_id, [])
        )
        if story_scope_id:
            self._candidate_request_start = request_count_at_start
            self._active_story_scope_id = story_scope_id
        else:
            self._candidate_request_start = request_count_at_start
            self._active_story_scope_id = None
        context = request.get("story_context") or {}
        headline_ids = {str(value) for value in (request.get("headline_ids") or [])}
        rows = [
            row
            for row in (
                context.get("public_source_url_bindings")
                or context.get("official_source_url_bindings")
                or []
            )
            if isinstance(row, Mapping)
            and str(row.get("headline_id") or "") in headline_ids
        ]
        documents: list[dict[str, Any]] = []
        diagnostics: list[str] = []
        rss_provenance: dict[str, Any] = {
            "locator_candidate_count": 0,
            "publisher_resolution_attempt_count": 0,
            "publisher_resolution_diagnostics": [],
        }
        for row in rows[:2]:
            try:
                document = self._direct_document(
                    str(row.get("url") or ""),
                    str(row.get("headline_id") or ""),
                    published_at_hint=str(
                        row.get("feed_published_at_utc")
                        or row.get("source_timestamp_utc")
                        or row.get("published_at_utc")
                        or ""
                    ) or None,
                )
                if document:
                    documents.append(document)
                    if self._enough_with_existing(request, documents):
                        break
            except (OSError, RuntimeError, TypeError, ValueError) as exc:
                diagnostics.append(str(exc) or type(exc).__name__)
                # A bound inaccessible path is candidate-local evidence friction. Reserve the
                # unchanged ledger for a reputable discovery path instead of burning the next
                # two bound URLs before trying accessible reporting.
                break
        if not self._enough_with_existing(request, documents):
            try:
                rss_documents, rss_provenance = self._rss_documents(
                    request, existing_documents=documents
                )
                documents.extend(rss_documents)
                diagnostics.extend(
                    rss_provenance.get("publisher_resolution_diagnostics") or []
                )
            except (OSError, RuntimeError, TypeError, ValueError) as exc:
                diagnostics.append(str(exc) or type(exc).__name__)
        unique: dict[tuple[str, str], dict[str, Any]] = {}
        for document in documents:
            unique[(str(document.get("publisher") or "").casefold(), str(document.get("title") or "").casefold())] = document
        documents = list(unique.values())[:4]
        locator_only_documents = [
            row for row in documents if row.get("public_claim_allowed") is not True
        ]
        documents = [
            row for row in documents if row.get("public_claim_allowed") is True
        ]
        retrieved = self._clock()
        if not isinstance(retrieved, datetime) or retrieved.utcoffset() is None:
            raise ValueError("public_source_retrieval_time_timezone_required")
        return {
            "status": "PASS" if documents else "BLOCKED",
            "rolling_x_story_binding": {
                "cluster_id": request.get("cluster_id"),
                "headline_ids": list(request.get("headline_ids") or []),
                "request_logical_hash": request.get("request_logical_hash"),
            },
            "evidence_documents": documents,
            "locator_only_records": locator_only_documents,
            "provided_evidence_capabilities": (
                ["credible_event_confirmation", "basic_attributed_facts"] if documents else []
            ),
            "provenance": {
                "retrieved_at_utc": _iso_utc(retrieved),
                "evaluation_as_of_utc": self._evaluation_as_of_utc,
                "request_count": self._request_count,
                "request_count_total": self._request_count,
                "request_count_for_candidate": (
                    self._request_count_by_story_scope.get(story_scope_id, 0)
                    if story_scope_id
                    else self._request_count - self._candidate_request_start
                ),
                "request_count_for_call": self._request_count - request_count_at_start,
                "story_evidence_scope_id": story_scope_id or None,
                "candidate_request_boundary_reused": bool(
                    story_scope_id and story_request_count_at_start > 0
                ),
                "network_reads_avoided_for_call": max(
                    0,
                    len(
                        self._reused_request_signatures_by_story_scope.get(
                            story_scope_id, []
                        )
                    )
                    - reused_signature_count_at_start,
                ),
                "reused_request_signatures": list(
                    self._reused_request_signatures_by_story_scope.get(
                        story_scope_id, []
                    )[reused_signature_count_at_start:]
                ),
                "request_limit": self._max_requests,
                "request_limit_per_candidate": self._max_requests_per_candidate,
                "read_only_public_gets": True,
                "paywall_or_access_control_bypass": False,
                "bounded_enrichment_requested": bool(
                    (request.get("evidence_enrichment_context") or {}).get("requested")
                ),
                "llm_directed_grounded_query_count": len(
                    (request.get("story_context") or {}).get(
                        "grounded_research_queries"
                    )
                    or []
                ),
                "acquisition_sequence": [
                    "EXACT_BOUND_PUBLIC_SOURCE_MAX_TWO_STOP_ON_INACCESSIBLE",
                    "RELEVANT_REPUTABLE_NEWS_LOCATOR",
                    "RELEVANCE_FIRST_ACCESSIBLE_SOURCE_NARROWING",
                    "RESOLVE_PUBLISHER_ARTICLE_OR_ATTRIBUTE_WITHOUT_LINK",
                ],
                "stopped_when_useful_depth_reached": self._enough_with_existing(
                    request, documents
                ),
                "additional_source_is_eligibility_requirement": False,
                "diagnostics": sorted(set(diagnostics)),
                "locator_only_record_count": len(locator_only_documents),
                "locator_candidate_count": int(
                    rss_provenance.get("locator_candidate_count") or 0
                ),
                "publisher_resolution_attempt_count": int(
                    rss_provenance.get("publisher_resolution_attempt_count") or 0
                ),
                "publisher_resolution_diagnostics": list(
                    rss_provenance.get("publisher_resolution_diagnostics") or []
                ),
            },
            "blockers": [] if documents else sorted(set(diagnostics or ["public_source_unavailable"])),
            "publication_authority": False,
        }

    def source_route_health_snapshot(self) -> dict[str, Any]:
        return self._source_route_health.snapshot()
