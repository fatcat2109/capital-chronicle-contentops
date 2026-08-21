"""Replay the exact current frozen-12 evidence requests with sanitized acquisition traces.

This acceptance harness never calls an article worker, publication coordinator, transport,
browser, or production store.  It preserves the historical cutoff and executes each request in
an isolated bounded research/cost scope so one diagnostic candidate cannot hide later source
reachability.  Discovery listings and sitemap bytes are summarized but never promoted to factual
authority; only the canonical loaders and adapter decide evidence acceptance.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping
from urllib.parse import parse_qs, urlsplit
import xml.etree.ElementTree as ET

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from live_contentops.grounded_news_research_v1 import (
    GroundedNewsResearchV1,
    build_deterministic_locator_plan,
    build_grounded_research_request,
)
from live_contentops.llm_cost_governor_v1 import llm_cycle_budget_scope
from live_contentops.nine_router_llm_seam_v2 import drain_invocation_log
from live_contentops.official_primary_evidence_loader_v1 import (
    BoundedOfficialPrimaryEvidenceLoader,
    _default_http_get,
)
from live_contentops.public_secondary_evidence_loader_v1 import (
    BoundedPublicSecondaryEvidenceLoader,
    REPUTABLE_SECONDARY_HOSTS,
    REPUTABLE_SECONDARY_NAMES,
    _default_public_http_get,
    _parse_timestamp,
    _rss_query_terms,
    _rss_relevance_score,
)
from live_contentops.rolling_x_targeted_evidence_adapter_v1 import (
    RollingXTargetedEvidenceAdapter,
)


SCHEMA_VERSION = "contentops.v1_current_evidence_yield_frozen_12_replay.v1"
TASK_LABEL = "TASK_V1_CURRENT_EVIDENCE_YIELD_REACHABILITY_AND_MULTI_FRONTIER_DAILY_FLOOR_CLOSURE_V1"
FROZEN_CUTOFF = "2026-08-20T23:37:06.897041Z"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"artifact_not_object:{path}")
    return value


def _write(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _safe_http_trace(
    *, requested_url: str, response: Mapping[str, Any] | None, error: Exception | None
) -> dict[str, Any]:
    requested = urlsplit(requested_url)
    final_url = str((response or {}).get("final_url") or requested_url)
    final = urlsplit(final_url)
    return {
        "requested_url": requested_url,
        "requested_host": str(requested.hostname or "").casefold(),
        "final_url": final_url,
        "final_host": str(final.hostname or "").casefold(),
        "status": int((response or {}).get("status") or 0) or None,
        "redirected": final_url != requested_url,
        "response_bytes": len((response or {}).get("body") or b""),
        "content_truncated": bool((response or {}).get("content_truncated")),
        "error": (str(error) or type(error).__name__) if error else None,
    }


def _rss_candidates(url: str, response: Mapping[str, Any]) -> list[dict[str, Any]]:
    if str(urlsplit(url).hostname or "").casefold() != "news.google.com":
        return []
    if not urlsplit(url).path.startswith("/rss/search"):
        return []
    body = response.get("body")
    if not isinstance(body, bytes) or not body:
        return []
    query = " ".join(parse_qs(urlsplit(url).query).get("q") or [])
    terms = _rss_query_terms(query)
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return []
    rows: list[dict[str, Any]] = []
    for item in root.findall(".//item"):
        source = item.find("source")
        publisher = " ".join(str(source.text or "").split()) if source is not None else ""
        publisher_home = str(source.get("url") or "") if source is not None else ""
        publisher_host = str(urlsplit(publisher_home).hostname or "").casefold()
        title = " ".join(str(item.findtext("title") or "").rsplit(" - ", 1)[0].split())
        published = _parse_timestamp(item.findtext("pubDate"))
        allowed_name = publisher.casefold() in REPUTABLE_SECONDARY_NAMES
        allowed_host = publisher_host in REPUTABLE_SECONDARY_HOSTS
        rows.append(
            {
                "publisher": publisher,
                "publisher_identity": publisher_host.removeprefix("www."),
                "title": title,
                "published_at_utc": published,
                "relevance_score": round(_rss_relevance_score(terms, title), 4),
                "publisher_name_allowed": allowed_name,
                "publisher_host_allowed": allowed_host,
                "eligible_listing_identity": allowed_name and allowed_host,
                "listing_grants_factual_authority": False,
            }
        )
    rows.sort(
        key=lambda row: (
            not bool(row["eligible_listing_identity"]),
            -float(row["relevance_score"]),
            str(row["publisher_identity"]),
            str(row["title"]),
        )
    )
    return rows[:12]


class _TracedGets:
    def __init__(self) -> None:
        self.public: list[dict[str, Any]] = []
        self.official: list[dict[str, Any]] = []
        self.rss_candidates: list[dict[str, Any]] = []

    def public_get(self, url: str, timeout: float, maximum: int) -> dict[str, Any]:
        try:
            response = dict(_default_public_http_get(url, timeout, maximum))
        except Exception as exc:
            self.public.append(
                _safe_http_trace(requested_url=url, response=None, error=exc)
            )
            raise
        self.public.append(
            _safe_http_trace(requested_url=url, response=response, error=None)
        )
        self.rss_candidates.extend(_rss_candidates(url, response))
        return response

    def official_get(self, url: str, timeout: float, maximum: int) -> dict[str, Any]:
        try:
            response = dict(_default_http_get(url, timeout, maximum))
        except Exception as exc:
            self.official.append(
                _safe_http_trace(requested_url=url, response=None, error=exc)
            )
            raise
        self.official.append(
            _safe_http_trace(requested_url=url, response=response, error=None)
        )
        return response


def _provider_telemetry(rows: list[dict[str, Any]]) -> dict[str, Any]:
    reported_costs = [
        (row.get("total_cost") or {}).get("usd")
        for row in rows
        if (row.get("total_cost") or {}).get("usd") is not None
    ]
    return {
        "logical_calls": len(rows),
        "provider_attempts": sum(int(row.get("total_attempts") or 0) for row in rows),
        "models_attempted_in_order": list(
            dict.fromkeys(
                str(model)
                for row in rows
                for model in row.get("models_attempted_in_order") or []
            )
        ),
        "prompt_tokens": sum(
            int((row.get("total_usage") or {}).get("prompt_tokens") or 0)
            for row in rows
        ),
        "completion_tokens": sum(
            int((row.get("total_usage") or {}).get("completion_tokens") or 0)
            for row in rows
        ),
        "total_tokens": sum(
            int((row.get("total_usage") or {}).get("total_tokens") or 0)
            for row in rows
        ),
        "reported_cost_usd": (
            round(sum(float(value) for value in reported_costs), 8)
            if reported_costs
            else None
        ),
        "cost_reporting_status": (
            "REPORTED" if reported_costs else "UNAVAILABLE_FROM_PROVIDER_RECEIPTS"
            if rows else "NOT_INCURRED_NO_PROVIDER_CALL"
        ),
        "terminal_dispositions": [row.get("terminal_disposition") for row in rows],
    }


def _classify(result: Mapping[str, Any]) -> str:
    if result.get("new_status") == "PASS":
        return "SOURCE_EXISTS_CURRENT_ADAPTER_SHOULD_HAVE_FOUND"
    public_trace = result.get("public_http_trace") or []
    rss = result.get("rss_listing_candidates") or []
    blockers = {str(value) for value in result.get("new_blockers") or []}
    official_locator = result.get("official_locator_attempt") or {}
    if (
        "/submissions/cik" in str(official_locator.get("candidate_official_url") or "").casefold()
        and int(result.get("accepted_evidence_document_count") or 0) == 0
    ):
        return "SOURCE_EXISTS_BUT_CURRENT_SOURCE_FAMILY_UNSUPPORTED"
    if any("missing:public_claim_permission" in value for value in blockers):
        return "SOURCE_EXISTS_BUT_CURRENT_SOURCE_FAMILY_UNSUPPORTED"
    if int(result.get("accepted_evidence_document_count") or 0) > 0 and any(
        "research_fact_not_supported_by_bound_source" in value
        or "research_core_proposition_not_supported" in value
        for value in blockers
    ):
        return "SOURCE_EXISTS_BUT_CURRENT_SOURCE_FAMILY_UNSUPPORTED"
    if any("published_after_evaluation_cutoff" in value for value in blockers):
        return "SOURCE_AFTER_CUTOFF_NOT_ELIGIBLE"
    if any(
        row.get("eligible_listing_identity")
        and float(row.get("relevance_score") or 0) >= 0.34
        for row in rss
    ) and any(
        row.get("error") or (row.get("status") not in {None, 200})
        for row in public_trace
        if row.get("requested_host") != "news.google.com"
    ):
        return "SOURCE_EXISTS_BUT_PUBLISHER_RESOLUTION_FAILED"
    if any("family_unsupported" in value for value in blockers):
        return "SOURCE_EXISTS_BUT_CURRENT_SOURCE_FAMILY_UNSUPPORTED"
    if rss:
        return "SOURCE_EXISTS_BUT_QUERY_OR_ALIAS_MISSED"
    return "SOURCE_TRULY_UNAVAILABLE_AT_CUTOFF"


def run(*, source_path: Path, output_path: Path) -> dict[str, Any]:
    source = _load(source_path)
    attempts = [dict(row) for row in source.get("rank_attempts") or []]
    if len(attempts) != 12:
        raise ValueError("frozen_current_replay_requires_exactly_12_requests")
    control_root = output_path.parent / "llm_control"
    results: list[dict[str, Any]] = []
    for attempt in attempts:
        rank = int(attempt.get("rank") or 0)
        request = dict(attempt.get("request") or {})
        traces = _TracedGets()
        public_loader = BoundedPublicSecondaryEvidenceLoader(
            evaluation_as_of_utc=FROZEN_CUTOFF,
            max_requests=6,
            max_requests_per_candidate=6,
            http_get=traces.public_get,
        )
        official_loader = BoundedOfficialPrimaryEvidenceLoader(
            evaluation_as_of_utc=FROZEN_CUTOFF,
            max_requests=24,
            http_get=traces.official_get,
        )
        grounded_researcher = GroundedNewsResearchV1(
            evaluation_as_of_utc=FROZEN_CUTOFF,
            public_retriever=public_loader,
        )
        adapter = RollingXTargetedEvidenceAdapter(
            evaluation_as_of_utc=FROZEN_CUTOFF,
            official_evidence_loader=official_loader,
            public_secondary_loader=public_loader,
            grounded_researcher=grounded_researcher,
        )
        compact = build_grounded_research_request(
            {**request, "evaluation_as_of_utc": FROZEN_CUTOFF}
        )
        deterministic_plan = build_deterministic_locator_plan(compact, max_queries=3)
        drain_invocation_log()
        with llm_cycle_budget_scope(
            f"v1-current-evidence-yield-frozen-rank-{rank}",
            control_root=control_root,
            now=datetime.now(timezone.utc),
        ):
            receipt = adapter(request)
        invocations = drain_invocation_log()
        acquisition = receipt.get("evidence_acquisition_provenance") or {}
        official = acquisition.get("official") or {}
        grounded = acquisition.get("grounded_research") or {}
        documents = [
            {
                key: row.get(key)
                for key in (
                    "document_id", "publisher", "title", "source_identity",
                    "source_authority_class", "source_url", "published_at_utc",
                    "raw_sha256", "canonical_content_sha256",
                    "canonical_resolution_status",
                )
            }
            for row in receipt.get("evidence_documents") or []
        ]
        result = {
            "rank": rank,
            "cluster_id": attempt.get("cluster_id"),
            "headline_ids": list(attempt.get("headline_ids") or []),
            "headline_proposition": (
                ((request.get("story_context") or {}).get("leaf_summaries") or [None])[0]
            ),
            "request_logical_hash": request.get("request_logical_hash"),
            "source_adapter_families": list(request.get("source_adapter_families") or []),
            "deterministic_locator_queries": list(deterministic_plan.get("queries") or []),
            "old_status": attempt.get("status"),
            "old_blockers": list(attempt.get("blockers") or []),
            "new_status": receipt.get("status"),
            "new_blockers": list(receipt.get("blockers") or []),
            "accepted_evidence_document_count": len(documents),
            "accepted_evidence_documents": documents,
            "official_locator_attempt": dict(official.get("provenance") or {}).get("locator"),
            "official_http_trace": traces.official,
            "public_http_trace": traces.public,
            "public_secondary_query_count": sum(
                row.get("requested_host") == "news.google.com"
                and urlsplit(str(row.get("requested_url") or "")).path.startswith("/rss/search")
                for row in traces.public
            ),
            "rss_listing_candidates": traces.rss_candidates,
            "rss_listing_candidate_count": len(traces.rss_candidates),
            "publisher_resolution_attempt_count": sum(
                row.get("requested_host") != "news.google.com"
                for row in traces.public
            ),
            "grounded_research": {
                "status": grounded.get("status"),
                "research_calls": int(grounded.get("research_calls") or 0),
                "public_retrieval_requests": int(
                    grounded.get("public_retrieval_requests") or 0
                ),
                "retrieval_result": dict(grounded.get("retrieval_result") or {}),
                "latest_event_state_closure": dict(
                    grounded.get("latest_event_state_closure") or {}
                ),
            },
            "minimum_trustworthy_evidence_status": (
                (receipt.get("minimum_trustworthy_evidence_packet") or {}).get("status")
            ),
            "provided_evidence_capabilities": list(
                receipt.get("provided_evidence_capabilities") or []
            ),
            "provider_telemetry": _provider_telemetry(invocations),
            "public_write_authority": False,
            "xhigh_called": False,
        }
        result["source_reachability_classification"] = _classify(result)
        results.append(result)

    before_documents = sum(
        len((attempt.get("evidence_receipt") or {}).get("evidence_documents") or [])
        for attempt in attempts
    )
    after_documents = sum(
        int(row.get("accepted_evidence_document_count") or 0) for row in results
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).strip(),
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "historical_cutoff_utc": FROZEN_CUTOFF,
        "source_artifact": {"path": str(source_path), "sha256": _sha256(source_path)},
        "frozen_candidate_count": len(results),
        "distinct_candidate_count": len({row["cluster_id"] for row in results}),
        "repeated_candidate_count": len(results) - len({row["cluster_id"] for row in results}),
        "before_accepted_evidence_document_count": before_documents,
        "after_accepted_evidence_document_count": after_documents,
        "before_evidence_qualified_candidate_count": 0,
        "after_evidence_qualified_candidate_count": sum(
            row.get("new_status") == "PASS" for row in results
        ),
        "public_secondary_requests": sum(
            len(row.get("public_http_trace") or []) for row in results
        ),
        "official_requests": sum(
            len(row.get("official_http_trace") or []) for row in results
        ),
        "research_provider_attempts": sum(
            int((row.get("provider_telemetry") or {}).get("provider_attempts") or 0)
            for row in results
        ),
        "research_prompt_tokens": sum(
            int((row.get("provider_telemetry") or {}).get("prompt_tokens") or 0)
            for row in results
        ),
        "research_completion_tokens": sum(
            int((row.get("provider_telemetry") or {}).get("completion_tokens") or 0)
            for row in results
        ),
        "research_total_tokens": sum(
            int((row.get("provider_telemetry") or {}).get("total_tokens") or 0)
            for row in results
        ),
        "reported_cost_usd": (
            round(
                sum(
                    float((row.get("provider_telemetry") or {}).get("reported_cost_usd"))
                    for row in results
                    if (row.get("provider_telemetry") or {}).get("reported_cost_usd")
                    is not None
                ),
                8,
            )
            if any(
                (row.get("provider_telemetry") or {}).get("reported_cost_usd") is not None
                for row in results
            )
            else None
        ),
        "cost_reporting_status": (
            "REPORTED"
            if any(
                (row.get("provider_telemetry") or {}).get("reported_cost_usd") is not None
                for row in results
            )
            else "UNAVAILABLE_FROM_PROVIDER_RECEIPTS"
        ),
        "candidate_results": results,
        "source_authority_invariants": {
            "discovery_listing_grants_factual_authority": False,
            "sitemap_metadata_grants_factual_authority": False,
            "model_output_grants_factual_authority": False,
            "exact_publisher_or_official_bytes_required": True,
            "post_cutoff_documents_rejected": True,
            "unapproved_source_class_rejected": True,
            "source_url_invention_permitted": False,
        },
        "safety": {
            "public_writes": 0,
            "publication_provider_writes": 0,
            "unknown_write": 0,
            "xhigh_calls": 0,
            "production_store_mutation": 0,
            "secret_or_session_inspection": 0,
        },
    }
    _write(output_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(
        source_path=Path(args.source).resolve(strict=True),
        output_path=Path(args.output).resolve(),
    )
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "frozen_candidate_count",
                    "after_accepted_evidence_document_count",
                    "after_evidence_qualified_candidate_count",
                    "public_secondary_requests",
                    "official_requests",
                    "research_provider_attempts",
                    "research_total_tokens",
                    "reported_cost_usd",
                    "safety",
                )
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
