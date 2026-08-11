"""Bounded read-only acquisition of launch-critical official primary evidence."""
from __future__ import annotations

from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
import json
import re
from typing import Any, Callable, Mapping
from urllib.parse import urlsplit
import urllib.request


OFFICIAL_HOSTS_BY_FAMILY = {
    "official_regulatory_fiscal": frozenset({
        "api.federalregister.gov",
        "www.federalregister.gov",
        "www.govinfo.gov",
        "www.congress.gov",
        "home.treasury.gov",
        "fiscaldata.treasury.gov",
        "www.whitehouse.gov",
    }),
    "company_primary": frozenset({"data.sec.gov", "www.sec.gov"}),
    "sec_regulatory": frozenset({"data.sec.gov", "www.sec.gov"}),
    "official_policy": frozenset({"www.federalreserve.gov"}),
    "official_macro": frozenset({
        "api.bls.gov",
        "www.bls.gov",
        "apps.bea.gov",
        "www.bea.gov",
        "api.census.gov",
        "www.census.gov",
        "www.federalreserve.gov",
        "www.newyorkfed.org",
        "fiscaldata.treasury.gov",
        "home.treasury.gov",
        "www.eia.gov",
        "data-api.ecb.europa.eu",
        "www.ecb.europa.eu",
    }),
}
SUPPORTED_FAMILIES = frozenset(OFFICIAL_HOSTS_BY_FAMILY)
ALLOWED_CONTENT_TYPES = frozenset({
    "application/json",
    "application/pdf",
    "application/xml",
    "application/xhtml+xml",
    "text/csv",
    "text/html",
    "text/plain",
    "text/xml",
})
USER_AGENT = (
    "CapitalChronicleContentOps/1.0 "
    "(bounded public-primary evidence acquisition; contact: repository maintainer)"
)


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            return _iso_utc(datetime.combine(date.fromisoformat(text), datetime.min.time(), timezone.utc))
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return _iso_utc(parsed)
    except ValueError:
        try:
            parsed = parsedate_to_datetime(text)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return _iso_utc(parsed)
        except (TypeError, ValueError):
            return None


def _walk_json(value: Any):
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield str(key), child
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _json_keys(value: Any) -> set[str]:
    return {key.casefold() for key, _ in _walk_json(value)}


def _first_json_timestamp(value: Any) -> str | None:
    preferred = {
        "publication_date",
        "published_at",
        "published_at_utc",
        "filingdate",
        "accepted",
        "release_date",
        "releasedate",
        "effective_on",
        "date",
    }
    for key, child in _walk_json(value):
        if key.casefold() in preferred:
            candidates = child if isinstance(child, list) else [child]
            for candidate in candidates:
                parsed = _parse_timestamp(candidate)
                if parsed:
                    return parsed
    return None


def _html_timestamp(text: str) -> str | None:
    patterns = (
        r'<meta[^>]+(?:property|name)=["\'](?:article:published_time|date|dc\.date)["\'][^>]+content=["\']([^"\']+)',
        r'<time[^>]+datetime=["\']([^"\']+)',
        r'(?:release date|last modified date)\s*:?</[^>]+>\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})',
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            parsed = _parse_timestamp(match.group(1))
            if parsed:
                return parsed
    return None


def _safe_url(url: str, allowed_hosts: set[str]) -> tuple[str, str]:
    parsed = urlsplit(url)
    host = str(parsed.hostname or "").casefold()
    if (
        parsed.scheme != "https"
        or not host
        or host not in allowed_hosts
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in {None, 443}
    ):
        raise ValueError("official_source_url_not_allowlisted")
    return url, host


def _default_http_get(url: str, timeout_seconds: float, max_bytes: int) -> dict[str, Any]:
    requested_host = str(urlsplit(url).hostname or "").casefold()

    class _SameAuthorityRedirects(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            parsed = urlsplit(newurl)
            if (
                parsed.scheme != "https"
                or str(parsed.hostname or "").casefold() != requested_host
                or parsed.username is not None
                or parsed.password is not None
                or parsed.port not in {None, 443}
            ):
                raise ValueError("official_source_cross_authority_redirect_forbidden")
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    request = urllib.request.Request(
        url,
        method="GET",
        headers={"Accept": "application/json, text/html, application/xml, text/plain, application/pdf", "User-Agent": USER_AGENT},
    )
    with urllib.request.build_opener(_SameAuthorityRedirects).open(
        request, timeout=timeout_seconds
    ) as response:
        body = response.read(max_bytes + 1)
        truncated = len(body) > max_bytes
        if truncated:
            body = body[:max_bytes]
        return {
            "status": int(response.status),
            "final_url": str(response.geturl()),
            "headers": {str(key).casefold(): str(value) for key, value in response.headers.items()},
            "body": body,
            "content_truncated": truncated,
        }


def _verified_capabilities(
    *, family: str, url: str, content_type: str, body: bytes
) -> tuple[set[str], Any, str]:
    text = body.decode("utf-8", errors="replace") if content_type != "application/pdf" else ""
    parsed: Any = None
    if content_type == "application/json" or text.lstrip().startswith(("{", "[")):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
    keys = _json_keys(parsed) if parsed is not None else set()
    lowered = text.casefold()
    capabilities: set[str] = set()
    if family == "official_regulatory_fiscal":
        capabilities.add("official_document")
        if keys.intersection({"effective_on", "publication_date", "dates", "implementation_date"}) or re.search(
            r"\b(effective|implementation|takes effect|compliance date)\b", lowered
        ):
            capabilities.add("implementation_timeline")
        if keys.intersection({"agencies", "agency_names", "affected_entities", "entities"}) or re.search(
            r"\b(agency|agencies|companies|entities|persons subject to)\b", lowered
        ):
            capabilities.add("affected_entities")
    elif family in {"company_primary", "sec_regulatory"}:
        filing_keys = {"accessionnumber", "filingdate", "form", "primarydocument", "filings"}
        if keys.intersection(filing_keys) or "/archives/edgar/data/" in url.casefold():
            capabilities.add("company_filing_or_release")
        if keys.intersection({"filingdate", "accepted", "reportdate", "periodofreport"}):
            capabilities.add("filing_or_release_timeline")
        if keys.intersection({"cik", "name", "entitytype", "issuer", "companyname"}):
            capabilities.add("affected_entities")
    elif family == "official_macro":
        macro_keys = {
            "data", "results", "series", "seriesid", "value", "observations",
            "period", "periodname", "unit", "linedescription", "releasedate",
        }
        official_release = bool(
            keys.intersection(macro_keys)
            or re.search(r"\b(data release|news release|economic release|employment situation)\b", lowered)
        )
        if official_release:
            capabilities.add("official_release")
        if (keys.intersection({"value", "data", "observations", "series"}) or official_release) and re.search(
            r"(?:^|[^a-z])[-+]?\d+(?:\.\d+)?(?:[^a-z]|$)", text
        ):
            capabilities.add("authorized_release_values")
        if keys.intersection({"releasedate", "release_date", "date", "period", "year"}) or _html_timestamp(text):
            capabilities.add("release_timestamps")
        if keys.intersection({"seriesid", "periodname", "unit", "linedescription", "metric", "definitions"}) or (
            official_release
            and re.search(r"\b(definitions?|technical note|seasonally adjusted|establishment survey|household survey)\b", lowered)
        ):
            capabilities.add("release_definitions")
    elif family == "official_policy":
        policy_published = (
            (_first_json_timestamp(parsed) if parsed is not None else None)
            or _html_timestamp(text)
        )
        if re.search(
            r"\b(statement|press release|implementation note|minutes|policy decision|target range)\b",
            lowered,
        ):
            capabilities.add("official_statement")
        if re.search(
            r"\b(federal reserve|board of governors|federal open market committee|fomc)\b",
            lowered,
        ):
            capabilities.add("issuing_authority")
        if policy_published:
            capabilities.add("decision_timeline")
    return capabilities, parsed, text


class BoundedOfficialPrimaryEvidenceLoader:
    """Fetch at most a few exact, explicitly allowlisted official URLs."""

    def __init__(
        self,
        *,
        evaluation_as_of_utc: str,
        max_requests: int = 24,
        timeout_seconds: float = 12.0,
        max_response_bytes: int = 2_000_000,
        http_get: Callable[[str, float, int], Mapping[str, Any]] | None = None,
        clock: Callable[[], datetime] | None = None,
        source_locator: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None = None,
    ) -> None:
        evaluation_as_of = datetime.fromisoformat(
            evaluation_as_of_utc.replace("Z", "+00:00")
        )
        if evaluation_as_of.utcoffset() is None:
            raise ValueError("official_source_evaluation_time_timezone_required")
        self._evaluation_as_of_utc = _iso_utc(evaluation_as_of)
        self._max_requests = max_requests
        self._timeout_seconds = timeout_seconds
        self._max_response_bytes = max_response_bytes
        self._http_get = http_get or _default_http_get
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        if source_locator is None:
            from live_contentops.official_primary_source_locator_v1 import (
                BoundedOfficialPrimarySourceLocator,
            )

            source_locator = BoundedOfficialPrimarySourceLocator(
                http_get=self._http_get,
                clock=self._clock,
            )
        self._source_locator = source_locator
        self._request_count = 0

    def __call__(self, request: Mapping[str, Any]) -> dict[str, Any]:
        requested_families = [
            str(value) for value in (request.get("source_adapter_families") or [])
            if str(value) in SUPPORTED_FAMILIES
        ]
        context = request.get("story_context") or {}
        binding_rows = [
            row for row in (context.get("official_source_url_bindings") or [])
            if isinstance(row, Mapping)
        ]
        headline_ids = {str(value) for value in (request.get("headline_ids") or [])}
        requested_hosts = {
            host
            for family in requested_families
            for host in OFFICIAL_HOSTS_BY_FAMILY[family]
        }
        bindings = [
            {"url": str(row.get("url") or ""), "headline_id": str(row.get("headline_id") or "")}
            for row in (context.get("official_source_url_bindings") or [])
            if isinstance(row, Mapping)
            and row.get("url")
            and str(row.get("headline_id") or "") in headline_ids
            and str(urlsplit(str(row.get("url") or "")).hostname or "").casefold()
            in requested_hosts
        ]
        urls = [row["url"] for row in bindings]
        public_binding_rows_present = bool(context.get("public_source_url_bindings"))
        blockers: list[str] = []
        document: dict[str, Any] | None = None
        retrieved_at_utc: str | None = None
        locator: dict[str, Any] | None = None
        locator_request_count = 0
        official_evidence_get_count = 0
        supplied: set[str] = set()
        if not requested_families:
            blockers.append("official_source_family_not_launch_supported")
        if not urls:
            if requested_families and (not binding_rows or public_binding_rows_present):
                if self._request_count >= self._max_requests:
                    blockers.append("official_source_request_budget_exhausted")
                else:
                    self._request_count += 1
                    locator_request_count = 1
                    located = self._source_locator({
                        **dict(request),
                        "evaluation_as_of_utc": self._evaluation_as_of_utc,
                    })
                    locator = dict(located) if isinstance(located, Mapping) else None
                    candidate_url = (
                        str((locator or {}).get("candidate_official_url") or "")
                        if (locator or {}).get("status") == "PASS"
                        else ""
                    )
                    if candidate_url:
                        headline_id = str((request.get("headline_ids") or [""])[0])
                        bindings = [{"url": candidate_url, "headline_id": headline_id}]
                        urls = [candidate_url]
                    else:
                        blockers.extend(
                            str(value) for value in ((locator or {}).get("blockers") or [])
                        )
                        blockers.append("exact_official_source_url_unavailable")
            else:
                blockers.append("exact_official_source_url_unavailable")
                if binding_rows and not public_binding_rows_present:
                    blockers.append("official_source_url_family_binding_invalid")
        candidates = []
        for url in urls:
            matching = [
                family
                for family in requested_families
                if (urlsplit(url).hostname or "").casefold()
                in OFFICIAL_HOSTS_BY_FAMILY[family]
            ]
            if matching:
                candidates.append((url, matching))
        if urls and requested_families and not candidates:
            blockers.append("official_source_url_family_binding_invalid")
        for url, matching in candidates[:1] if not blockers else []:
            family = (
                "sec_regulatory"
                if "sec_regulatory" in matching
                else matching[0]
            )
            allowed_hosts = set(OFFICIAL_HOSTS_BY_FAMILY[family])
            try:
                requested_url, host = _safe_url(url, allowed_hosts)
                if self._request_count >= self._max_requests:
                    raise RuntimeError("official_source_request_budget_exhausted")
                self._request_count += 1
                official_evidence_get_count = 1
                response = dict(
                    self._http_get(
                        requested_url, self._timeout_seconds, self._max_response_bytes
                    )
                )
                final_url, final_host = _safe_url(
                    str(response.get("final_url") or requested_url), allowed_hosts
                )
                if int(response.get("status") or 0) != 200:
                    raise RuntimeError("official_source_http_status_not_200")
                headers = {
                    str(key).casefold(): str(value)
                    for key, value in (response.get("headers") or {}).items()
                }
                content_type = headers.get("content-type", "").split(";", 1)[0].strip().casefold()
                if content_type not in ALLOWED_CONTENT_TYPES:
                    raise ValueError("official_source_content_type_not_allowlisted")
                body = response.get("body")
                if not isinstance(body, bytes) or not body or len(body) > self._max_response_bytes:
                    raise ValueError("official_source_body_invalid")
                retrieved_at = self._clock()
                if not isinstance(retrieved_at, datetime) or retrieved_at.utcoffset() is None:
                    raise ValueError("official_source_retrieval_time_timezone_required")
                retrieved_at_utc = _iso_utc(retrieved_at)
                content_truncated = bool(response.get("content_truncated"))
                verified, parsed, text = _verified_capabilities(
                    family=family, url=final_url, content_type=content_type, body=body
                )
                published_at = (
                    (_first_json_timestamp(parsed) if parsed is not None else None)
                    or _html_timestamp(text)
                    or _parse_timestamp(headers.get("last-modified"))
                    or _parse_timestamp((locator or {}).get("source_published_at_utc"))
                )
                if not published_at:
                    raise ValueError("official_source_published_timestamp_unavailable")
                if datetime.fromisoformat(published_at.replace("Z", "+00:00")) > datetime.fromisoformat(
                    self._evaluation_as_of_utc.replace("Z", "+00:00")
                ):
                    raise ValueError("official_source_published_after_evaluation_cutoff")
                supplied.update(verified)
                document = {
                    "document_id": "official-primary-" + sha256(body).hexdigest()[:20],
                    "title": headers.get("x-document-title") or final_url.rsplit("/", 1)[-1] or host,
                    "publisher": final_host,
                    "source_authority_class": "official_public_primary_source",
                    "source_adapter_family": family,
                    "source_url": final_url,
                    "requested_source_url": requested_url,
                    "source_headline_id": next(
                        row["headline_id"] for row in bindings if row["url"] == requested_url
                    ),
                    "published_at_utc": published_at,
                    "event_time_utc": published_at,
                    "raw_sha256": sha256(body).hexdigest(),
                    "canonical_content_sha256": sha256(body).hexdigest(),
                    "content_type": content_type,
                    "byte_length": len(body),
                    "canonical_content_text": text[:100_000] if text else None,
                    "public_claim_allowed": True,
                    "retrieval_method": (
                        "READ_ONLY_HTTP_GET_BOUNDED_PREFIX"
                        if content_truncated
                        else "READ_ONLY_HTTP_GET"
                    ),
                    "content_truncated": content_truncated,
                    "bounded_section_byte_length": len(body),
                }
            except (OSError, RuntimeError, TypeError, ValueError) as exc:
                blockers.append(str(exc) or type(exc).__name__)
            break

        required = {str(value) for value in (request.get("required_evidence_capabilities") or [])}
        missing = required - supplied
        blockers.extend(f"required_evidence_capability_missing:{value}" for value in sorted(missing))
        return {
            "status": "PASS" if not blockers else "BLOCKED",
            "rolling_x_story_binding": {
                "cluster_id": request.get("cluster_id"),
                "headline_ids": list(request.get("headline_ids") or []),
                "request_logical_hash": request.get("request_logical_hash"),
            },
            # Report every capability actually verified from acquired bytes.  The caller decides
            # which are required for the effective article mode and which merely enrich claims.
            "provided_evidence_capabilities": sorted(supplied),
            "official_source_documents": [document] if document else [],
            "provenance": {
                "retrieved_at_utc": retrieved_at_utc,
                "evaluation_as_of_utc": self._evaluation_as_of_utc,
                "locator": locator,
                "locator_request_count": locator_request_count,
                "official_evidence_get_count": official_evidence_get_count,
                "request_count": self._request_count,
                "request_limit": self._max_requests,
                "timeout_seconds": self._timeout_seconds,
                "read_only_http_get_only": True,
                "bounded_truncation_allowed": True,
            },
            "blockers": sorted(set(blockers)),
            "publication_authority": False,
        }
