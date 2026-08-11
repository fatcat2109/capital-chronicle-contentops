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
import xml.etree.ElementTree as ET

from live_contentops.official_primary_evidence_loader_v1 import (
    _default_http_get,
    _html_timestamp,
    _iso_utc,
    _parse_timestamp,
)


REPUTABLE_SECONDARY_HOSTS = frozenset(
    {
        "abcnews.go.com", "aljazeera.com", "apnews.com", "axios.com", "bbc.com",
        "bbc.co.uk", "bloomberg.com", "cbsnews.com", "cnbc.com", "cnn.com", "ft.com",
        "marketwatch.com", "nbcnews.com", "npr.org", "politico.com", "reuters.com",
        "theguardian.com", "thehill.com", "jpost.com", "wsj.com", "www.abcnews.go.com",
        "www.aljazeera.com", "www.apnews.com", "www.axios.com", "www.bbc.com",
        "www.bloomberg.com", "www.cbsnews.com", "www.cnbc.com", "www.cnn.com", "www.ft.com",
        "www.marketwatch.com", "www.nbcnews.com", "www.npr.org", "www.politico.com",
        "www.reuters.com", "www.theguardian.com", "www.thehill.com", "www.jpost.com", "www.wsj.com",
    }
)
REPUTABLE_SECONDARY_NAMES = frozenset(
    {
        "abc news", "al jazeera", "associated press", "the associated press", "ap", "axios", "bbc", "bloomberg",
        "cbs news", "cnbc", "cnn", "financial times", "marketwatch", "nbc news", "npr",
        "politico", "reuters", "the guardian", "the hill", "the jerusalem post",
        "jerusalem post", "the wall street journal", "wsj",
    }
)
NEWS_RSS_ENDPOINT = "https://news.google.com/rss/search"
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
    """Score a listing against the event-bearing query before applying the result cap."""
    query = {token.casefold() for token in query_terms}
    if not query:
        return 0.0
    title_terms = {token.casefold() for token in _rss_query_terms(title)}
    return len(query.intersection(title_terms)) / len(query)


class BoundedPublicSecondaryEvidenceLoader:
    """Acquire a few public sources or corroborated reputable news-listing records."""

    def __init__(
        self,
        *,
        evaluation_as_of_utc: str,
        max_requests: int = 24,
        timeout_seconds: float = 12.0,
        max_response_bytes: int = 800_000,
        http_get: Callable[[str, float, int], Mapping[str, Any]] | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        cutoff = datetime.fromisoformat(evaluation_as_of_utc.replace("Z", "+00:00"))
        if cutoff.utcoffset() is None:
            raise ValueError("public_source_evaluation_time_timezone_required")
        self._evaluation_as_of_utc = _iso_utc(cutoff)
        self._max_requests = max_requests
        self._timeout_seconds = timeout_seconds
        self._max_response_bytes = max_response_bytes
        self._http_get = http_get or _default_http_get
        self._validate_dns = http_get is None
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._request_count = 0

    def _get(self, url: str) -> dict[str, Any]:
        if self._request_count >= self._max_requests:
            raise RuntimeError("public_source_request_budget_exhausted")
        _public_host(url, resolve_dns=self._validate_dns)
        self._request_count += 1
        return dict(self._http_get(url, self._timeout_seconds, self._max_response_bytes))

    def _direct_document(self, url: str, headline_id: str) -> dict[str, Any] | None:
        host = _public_host(url, resolve_dns=self._validate_dns)
        if host not in REPUTABLE_SECONDARY_HOSTS:
            return None
        response = self._get(url)
        if int(response.get("status") or 0) != 200:
            raise ValueError("public_source_http_status_not_200")
        final_url = str(response.get("final_url") or url)
        final_host = _public_host(final_url, resolve_dns=self._validate_dns)
        if final_host not in REPUTABLE_SECONDARY_HOSTS:
            raise ValueError("public_source_redirect_authority_invalid")
        headers = {str(k).casefold(): str(v) for k, v in (response.get("headers") or {}).items()}
        content_type = headers.get("content-type", "").split(";", 1)[0].casefold()
        body = response.get("body")
        if not isinstance(body, bytes) or not body:
            raise ValueError("public_source_body_invalid")
        raw = body.decode("utf-8", errors="replace")
        title = _title(raw) or final_url.rsplit("/", 1)[-1].replace("-", " ")
        published = _html_timestamp(raw) or _parse_timestamp(headers.get("last-modified"))
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
            "requested_source_url": url,
            "source_headline_id": headline_id,
            "published_at_utc": published,
            "event_time_utc": published,
            "raw_sha256": sha256(body).hexdigest(),
            "canonical_content_sha256": sha256(text.encode("utf-8")).hexdigest(),
            "canonical_content_text": text,
            "content_type": content_type,
            "byte_length": len(body),
            "content_truncated": bool(response.get("content_truncated")),
            "public_claim_allowed": True,
            "retrieval_method": "READ_ONLY_PUBLIC_HTTP_GET",
        }

    def _rss_documents(self, request: Mapping[str, Any]) -> list[dict[str, Any]]:
        summaries = [
            " ".join(str(value).split())
            for value in ((request.get("story_context") or {}).get("leaf_summaries") or [])
            if str(value).strip()
        ]
        terms = _rss_query_terms(summaries[0] if summaries else "")
        if not terms:
            return []
        url = NEWS_RSS_ENDPOINT + "?" + urlencode(
            {"q": " ".join(terms), "hl": "en-US", "gl": "US", "ceid": "US:en"}
        )
        response = self._get(url)
        body = response.get("body")
        if int(response.get("status") or 0) != 200 or not isinstance(body, bytes) or not body:
            return []
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            return []
        cutoff = datetime.fromisoformat(
            self._evaluation_as_of_utc.replace("Z", "+00:00")
        )
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
            }
            existing = candidates.get(identity)
            candidate = (relevance, observed, document)
            if existing is None or (observed, relevance) > (existing[1], existing[0]):
                candidates[identity] = candidate
        ranked = sorted(
            candidates.values(),
            key=lambda row: (
                -row[1].timestamp(),
                -row[0],
                str(row[2].get("publisher") or "").casefold(),
                str(row[2].get("title") or "").casefold(),
            ),
        )
        return [row[2] for row in ranked[:3]]

    def __call__(self, request: Mapping[str, Any]) -> dict[str, Any]:
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
        for row in rows[:3]:
            try:
                document = self._direct_document(
                    str(row.get("url") or ""), str(row.get("headline_id") or "")
                )
                if document:
                    documents.append(document)
            except (OSError, RuntimeError, TypeError, ValueError) as exc:
                diagnostics.append(str(exc) or type(exc).__name__)
        if len({str(row.get("publisher") or "").casefold() for row in documents}) < 2:
            try:
                documents.extend(self._rss_documents(request))
            except (OSError, RuntimeError, TypeError, ValueError) as exc:
                diagnostics.append(str(exc) or type(exc).__name__)
        unique: dict[tuple[str, str], dict[str, Any]] = {}
        for document in documents:
            unique[(str(document.get("publisher") or "").casefold(), str(document.get("title") or "").casefold())] = document
        documents = list(unique.values())[:4]
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
            "provided_evidence_capabilities": (
                ["credible_event_confirmation", "basic_attributed_facts"] if documents else []
            ),
            "provenance": {
                "retrieved_at_utc": _iso_utc(retrieved),
                "evaluation_as_of_utc": self._evaluation_as_of_utc,
                "request_count": self._request_count,
                "request_limit": self._max_requests,
                "read_only_public_gets": True,
                "paywall_or_access_control_bypass": False,
                "diagnostics": sorted(set(diagnostics)),
            },
            "blockers": [] if documents else sorted(set(diagnostics or ["public_source_unavailable"])),
            "publication_authority": False,
        }
