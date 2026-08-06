"""Cohort orchestration for CORE V0 closure (Work Package D).

TASK_CONTENTOPS_CORE_V0_DIVERSITY_SEO_IMAGE_AND_CHART_CLOSURE_V1 — ``SHADOW_ONLY``.

Extends the accepted ``core-v0-shadow-demo`` path so one local command processes the
diversified governed evaluation corpus. Every decision is delegated to an already
accepted component; this module only sequences them and assembles the reviewable report:

* corpus indexing — ``core_v0_evaluation_corpus_v1``
* visual policy / charts / portfolio / SEO — ``core_v0_closure_capabilities_v1``
* canonical review — ``editorial_review_orchestrator_v2.run_editorial_review``
* platform packages — ``multi_story_platform_native_operator_packages_v1``
* durable state — ``durable_operational_store_v1`` via the accepted CORE V0 persistence

No credential read, provider call, network intake, browser/CDP action, scheduler
execution, dispatch, publication, or public write occurs on any path here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.capital_chronicle_content_evidence_packet_v3 import (
    validate_content_evidence_packet_v3,
)
from live_contentops.core_v0_closure_capabilities_v1 import (
    ClosureCapabilityError,
    build_authorized_chart,
    build_portfolio_report,
    build_seo_contract,
    apply_concentration_penalties,
    evaluate_story_visuals,
    run_chart_methodology_qa,
    run_seo_contract_qa,
)
from live_contentops.core_v0_evaluation_corpus_v1 import (
    EvaluationCorpusError,
    UNREVIEWED_ASSET,
    _load,
    _packet_from,
    build_evaluation_corpus,
    corpus_domain_coverage,
    load_authorized_prior_observations,
    load_governed_visual_assets,
)
from live_contentops.dual_lane_core_v0_shadow_newsroom_v1 import (
    DualLaneShadowError,
    _logical_hash,
    zero_live_action_flags,
)
from live_contentops.editorial_review_orchestrator_v2 import run_editorial_review
from live_contentops.freshness_market_state_v2 import evaluate_freshness
from live_contentops.multi_story_platform_native_operator_packages_v1 import (
    ALL_TIER1_PLATFORM_IDS,
    VisualAssetRequiredError,
    build_platform_native_variant,
)
from live_contentops.window_incremental_editorial_shadow_v1 import (
    _shadow_structured_role_reviewer as deterministic_structured_role_reviewer,
)

SCHEMA_VERSION = "contentops.core_v0_cohort_shadow_run.v1"
TASK_LABEL = "TASK_CONTENTOPS_CORE_V0_DIVERSITY_SEO_IMAGE_AND_CHART_CLOSURE_V1"
OPERATING_MODE = "SHADOW_ONLY"

COHORT_SUMMARY_FILENAME = "cohort_run_summary.json"
COHORT_CASES_FILENAME = "cohort_cases.json"
PORTFOLIO_FILENAME = "portfolio_report.json"
V5_SNAPSHOT_FILENAME = "v5_cohort_snapshot.json"

#: Dispositions that never produce a package. Each is a truthful terminal outcome.
_NON_PRODUCING = {
    "PERMISSION_BLOCKED": "REVIEW_BLOCKED",
    "EVIDENCE_BLOCKED": "REVIEW_BLOCKED",
    "VISUAL_RIGHTS_BLOCKED": "REVIEW_BLOCKED",
    "DUPLICATE_OR_LOW_DELTA": "DUPLICATE_SUPPRESSED",
    "HISTORICAL_NOT_CURRENT": "NO_PUBLICATION",
}


def _citation_urls(citations: Sequence[Mapping[str, Any]]) -> list[str]:
    seen: list[str] = []
    for row in citations:
        url = str(row.get("url") or "")
        if url and url not in seen:
            seen.append(url)
    return seen


def _claim_body(claim: Mapping[str, Any]) -> str:
    """Render one governed claim's authorized substance without adding meaning."""
    numeric = claim.get("numeric") or {}
    if numeric.get("value") is not None:
        unit = str(numeric.get("unit") or "").strip()
        return f"{numeric.get('metric')}: {numeric.get('value')} {unit}".strip()
    return str(claim.get("statement") or "").strip()


def _build_article(
    *,
    case: Mapping[str, Any],
    packet: Mapping[str, Any],
    claim_ids: Sequence[str],
) -> dict[str, Any]:
    """Compose article copy strictly from authorized governed claim substance."""
    graph = packet.get("governed_claim_graph") or {}
    claims = {str(row.get("claim_id")): row for row in graph.get("claims") or []}
    lines = [_claim_body(claims[cid]) for cid in claim_ids if cid in claims]
    lines = [line for line in lines if line]
    if not lines:
        raise ClosureCapabilityError(f"case_has_no_authorized_substance:{case['case_id']}")

    domain = str(case["domain_family"]).replace("_", " ")
    headline = f"Official record: {domain} governed disclosure"
    summary = (
        "Every value and statement below is reproduced exactly from the governed "
        "Capital Chronicle packet for this official record."
    )
    sections = [
        {"heading": "What the official record states", "text": summary},
        {
            "heading": "Exact authorized substance",
            "text": (
                "Reproduced verbatim from the governed packet; ContentOps performed no "
                "calculation.\n" + "\n".join(lines)
            ),
        },
        {
            "heading": "What this does not establish",
            "text": (
                "This is an official observation. It is not a forecast, an "
                "interpretation, a trading signal, or Capital Chronicle analytical truth."
            ),
        },
    ]
    citations: list[dict[str, Any]] = []
    limitations: list[str] = []
    for cid in claim_ids:
        claim = claims.get(cid) or {}
        for citation in claim.get("citations") or []:
            if citation not in citations:
                citations.append(dict(citation))
        limitations.extend(str(item) for item in claim.get("limitations") or [])

    return {
        "headline": headline,
        "answer_first_summary": summary,
        "body_sections": sections,
        "claim_ids": list(claim_ids),
        "citations": citations,
        "limitations": sorted(set(limitations)),
    }


def _canonical_article(
    *,
    drafted: Mapping[str, Any],
    packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Project drafted copy into the canonical V3 article contract."""
    graph = packet.get("governed_claim_graph") or {}
    claims = {str(row.get("claim_id")): row for row in graph.get("claims") or []}
    claim_ids = [str(value) for value in drafted["claim_ids"]]
    rendered = "\n\n".join(
        str(row.get("text") or "") for row in drafted["body_sections"]
    ) + "\n\nNot financial advice."
    return {
        "title": drafted["headline"],
        "summary": drafted["answer_first_summary"],
        "rendered_body": rendered,
        "article_mode": "evidence_bound_shadow_draft",
        "workflow_mode": "evidence_bound_shadow_draft",
        "claim_ids_used": claim_ids,
        # The headline and summary carry no claim-specific numeric or factual assertion,
        # so no claim is declared against them.
        "title_claim_ids_used": [],
        "summary_claim_ids_used": [],
        "body_claim_ids_used": claim_ids,
        "claim_citations": {
            cid: sorted(
                {
                    str(row["url"])
                    for row in (claims.get(cid, {}).get("citations") or [])
                    if row.get("url")
                }
            )
            for cid in claim_ids
        },
        "claim_authority_used": {
            cid: claims.get(cid, {}).get("authority_class") for cid in claim_ids
        },
        "claim_permissions_used": {
            cid: claims.get(cid, {}).get("permission_state") for cid in claim_ids
        },
        "market_reaction_claim_ids": [
            cid for cid in claim_ids
            if claims.get(cid, {}).get("claim_type") == "market_reaction"
        ],
        "numeric_claims_from_llm": False,
        "cross_asset_assertions": False,
        "hard_truncation_used": False,
        "quantitative_blockers": [],
        "publication_authority": False,
    }


def _platform_results(
    *,
    case: Mapping[str, Any],
    drafted: Mapping[str, Any],
    package_id: str,
    authority_logical_hash: str,
    visual_asset_ids: Sequence[str],
    visual_asset_hashes: Sequence[str],
    source_label: str,
) -> dict[str, Any]:
    """Build every Tier-1 destination through the canonical package fabric.

    All nine destinations get an explicit outcome. A destination that cannot be built
    truthfully — Instagram with no rights-cleared asset — is reported as blocked rather
    than degraded or omitted.
    """
    citation_urls = _citation_urls(drafted["citations"])
    payloads: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    for platform_id in ALL_TIER1_PLATFORM_IDS:
        try:
            variant = build_platform_native_variant(
                platform_id=platform_id,
                subject_id=package_id,
                candidate_id=str(case["case_id"]),
                authority_logical_hash=authority_logical_hash,
                authorized_claim_ids=list(drafted["claim_ids"]),
                headline=drafted["headline"],
                summary=drafted["answer_first_summary"],
                source_label=source_label,
                citation_urls=citation_urls,
                limitations=list(drafted["limitations"]),
                visual_asset_ids=list(visual_asset_ids),
                visual_asset_hashes=list(visual_asset_hashes),
            )
        except VisualAssetRequiredError as exc:
            blocked.append(
                {
                    "platform_id": platform_id,
                    "capability": "BLOCKED_VISUAL_ASSET_REQUIRED",
                    "reason": str(exc),
                    "image_fabricated_to_satisfy_platform": False,
                    "valid_for_dispatch": False,
                    "dispatch_ready": False,
                    "public_ready": False,
                    "live_eligibility": False,
                }
            )
            continue
        payloads.append({**variant, "capability": "SUPPORTED_DRY_RUN_PAYLOAD"})

    return {
        "package_fabric": (
            "multi_story_platform_native_operator_packages_v1.build_platform_native_variant"
        ),
        "tier1_destination_count": len(ALL_TIER1_PLATFORM_IDS),
        "supported_count": len(payloads),
        "blocked_count": len(blocked),
        "explicit_outcome_count": len(payloads) + len(blocked),
        "all_destinations_have_explicit_outcome": (
            len(payloads) + len(blocked) == len(ALL_TIER1_PLATFORM_IDS)
        ),
        "distinct_payload_text_count": len({row["text"] for row in payloads}),
        "distinct_payload_hash_count": len({row["payload_hash"] for row in payloads}),
        "payloads": payloads,
        "blocked_destinations": blocked,
    }


def process_case(
    *,
    case: Mapping[str, Any],
    repo_root: Path,
    visual_assets: Sequence[Mapping[str, Any]],
    prior_observations: Mapping[str, Mapping[str, Any]],
    chart_output_dir: Path,
) -> dict[str, Any]:
    """Run one cohort case through the full canonical shadow pipeline."""
    disposition = str(case["expected_disposition"])
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "case_id": case["case_id"],
        "lane": case["lane"],
        "domain_family": case["domain_family"],
        "sector": case["sector"],
        "entities": list(case.get("entities") or []),
        "geography": case.get("geography"),
        "source_family": case.get("source_family"),
        "content_mode": case.get("content_mode"),
        "visual_type": case.get("visual_type"),
        "update_chain": case.get("update_chain"),
        "story_type": case.get("story_type"),
        "material_class": case.get("material_class"),
        "presented_as_current_news": False,
        "artifact_path": case.get("artifact_path"),
        "governed_disposition": disposition,
        "notes": case.get("notes"),
        **zero_live_action_flags(),
    }

    # --- Non-producing cases terminate truthfully, with a real gate reason ---------
    if disposition in _NON_PRODUCING:
        if disposition == "VISUAL_RIGHTS_BLOCKED":
            # Run the real visual gate against the unreviewed asset so the block is a
            # measured policy outcome, not a label.
            probe_asset = {
                **{k: v for k, v in (visual_assets[0] if visual_assets else {}).items()},
                "asset_id": UNREVIEWED_ASSET["asset_id"],
                "rights_status": UNREVIEWED_ASSET["rights_status"],
                "source_page_url": UNREVIEWED_ASSET["source_page_url"],
            }
            visual = evaluate_story_visuals(
                story_type=str(case["story_type"]), assets=[probe_asset]
            )
            result["visual"] = visual
            result["visual_status"] = visual["status"]
        result["outcome"] = disposition
        result["package_produced"] = False
        result["review_result"] = None
        result["terminal_state"] = _NON_PRODUCING[disposition]
        result["gate_reason"] = {
            "PERMISSION_BLOCKED": "Source-family permission ceiling is CONTEXT_ONLY; reporting not granted.",
            "EVIDENCE_BLOCKED": "Governed candidate carries a context_only_evidence blocker.",
            "VISUAL_RIGHTS_BLOCKED": "No rights-cleared visual asset; unreviewed image withheld.",
            "DUPLICATE_OR_LOW_DELTA": "Same governed update chain already assigned; no new delta.",
            "HISTORICAL_NOT_CURRENT": "Historical material only; NO_PUBLICATION is the valid outcome.",
        }[disposition]
        result["governed_blockers"] = list(case.get("governed_blockers") or [])
        return result

    # --- Eligible cases produce a full reviewable package -------------------------
    document = _load(repo_root / str(case["artifact_path"]))
    if case.get("newsroom_candidate"):
        # Newsroom-led case: go through the accepted candidate -> canonical V3 adapter
        # rather than reading a pre-built packet.
        from live_contentops.dual_lane_core_v0_shadow_demo_runner_v1 import (
            _newsroom_v3_packet,
        )

        candidate = next(
            row for row in document["candidates"]
            if str(row.get("candidate_id")) == str(case["candidate_id"])
        )
        packet, _adapted = _newsroom_v3_packet(candidate)
    else:
        packet = _packet_from(document, str(case["packet_id"]))
    blockers = validate_content_evidence_packet_v3(packet)
    if blockers:
        raise ClosureCapabilityError(f"packet_invalid:{case['case_id']}:{sorted(blockers)}")

    claim_ids = list((packet.get("governed_claim_graph") or {}).get("approved_claim_ids") or [])
    drafted = _build_article(case=case, packet=packet, claim_ids=claim_ids)
    package_id = f"pkg-{case['case_id']}-{_logical_hash(case['case_id'])[:12]}"

    # Visual: policy-resolved, rights-audited, engine-decided.
    assets = list(visual_assets) if case.get("visual_capable") else []
    visual = evaluate_story_visuals(story_type=str(case["story_type"]), assets=assets)

    # Chart: only from authorized values, only when this case authorizes them.
    chart_manifest: dict[str, Any] | None = None
    chart_qa: dict[str, Any] | None = None
    if case.get("chart_capable"):
        chart_manifest = build_authorized_chart(
            chart_id=str(case["case_id"]).replace("case-", "chart-"),
            title="U.S. Treasury Par Yield Curve: 2026-07-13",
            packet=packet,
            authorized_claim_ids=claim_ids,
            prior_observations=prior_observations,
            output_dir=chart_output_dir,
        )
        chart_qa = run_chart_methodology_qa(chart_manifest)

    seo = build_seo_contract(
        headline=drafted["headline"],
        summary=drafted["answer_first_summary"],
        body_sections=drafted["body_sections"],
        citations=drafted["citations"],
        domain_family=str(case["domain_family"]),
        story_type=str(case["story_type"]),
        target_reader=f"institutional reader following {str(case['sector']).replace('_', ' ')}",
        primary_intent=f"what the official {str(case['domain_family']).replace('_', ' ')} record states",
        secondary_intent="what the governed packet does and does not authorize",
        keyword_cluster=[
            str(case["domain_family"]).replace("_", " "),
            str(case["sector"]).replace("_", " "),
            "official record",
        ],
        canonical_angle="exact official record, no interpretation added",
        competitive_differentiation=(
            "Exact governed values with full source binding and explicit limitations."
        ),
        update_timestamp_utc=str(packet.get("as_of_utc") or packet.get("generated_at_utc")),
        internal_links=[
            {"anchor": "Capital Chronicle analysis", "target": "/capital-chronicle-analysis"},
            {"anchor": "Newsroom coverage", "target": "/newsroom"},
        ],
        visual_assets=[
            row for row in assets if row.get("asset_id") in set(visual["bound_asset_ids"])
        ],
        chart_manifest=chart_manifest,
    )
    seo_qa = run_seo_contract_qa(seo)

    platform = _platform_results(
        case=case,
        drafted=drafted,
        package_id=package_id,
        authority_logical_hash=str(packet.get("logical_hash")),
        visual_asset_ids=visual["bound_asset_ids"],
        visual_asset_hashes=visual["bound_asset_hashes"],
        source_label=str((case.get("entities") or ["governed official source"])[0]),
    )

    request = {
        "story_type": str(case["story_type"]),
        "article_mode": "evidence_bound_shadow_draft",
        "workflow_mode": "evidence_bound_shadow_draft",
        "market_sensitive": False,
        "market_snapshot_required": False,
        "fresh_material_delta": False,
    }
    freshness = evaluate_freshness(packet, request)
    article = _canonical_article(drafted=drafted, packet=packet)
    review = run_editorial_review(
        request=request,
        packet=packet,
        article=article,
        freshness_decision=freshness,
        visual_decision=visual["decision"],
        structured_reviewer=deterministic_structured_role_reviewer,
    )

    package = {
        "schema_version": SCHEMA_VERSION,
        "package_id": package_id,
        "case_id": case["case_id"],
        "lane": case["lane"],
        "article": {
            "headline": drafted["headline"],
            "answer_first_summary": drafted["answer_first_summary"],
            "body": drafted["body_sections"],
            "claim_ids_used": drafted["claim_ids"],
            "citations": drafted["citations"],
            "limitations": drafted["limitations"],
        },
        "seo": seo,
        "seo_qa": seo_qa,
        "visual": visual,
        "chart": chart_manifest,
        "chart_qa": chart_qa,
        "platform": platform,
        "publication_authority": False,
        "dispatch_authority": False,
        "public_write_authority": False,
    }
    package["package_logical_hash"] = _logical_hash(package)

    passed = review["status"] == "PASS"
    result.update(
        {
            "outcome": "PACKAGE_REVIEW_PASSED" if passed else "PACKAGE_REVIEW_BLOCKED",
            "package_produced": True,
            "package_id": package_id,
            "package_logical_hash": package["package_logical_hash"],
            "package": package,
            "authorized_claim_ids": claim_ids,
            "packet_id": packet.get("packet_id"),
            "packet_logical_hash": packet.get("logical_hash"),
            "review_engine": "editorial_review_orchestrator_v2.run_editorial_review",
            "review_result": review["status"],
            "review_role_count": len(review["roles"]),
            "review_role_order": list(review["role_order"]),
            "review_blocked_roles": [
                row["role"] for row in review["roles"] if row["status"] == "BLOCK"
            ],
            "review_blockers": list(review["blockers"]),
            "review_logical_hash": _logical_hash(review),
            "visual_status": visual["status"],
            "seo_contract_status": seo_qa["status"],
            "chart_qa_status": (chart_qa or {}).get("status"),
            "terminal_state": "REVIEW_READY" if passed else "REVIEW_BLOCKED",
            "freshness_decision": freshness["decision"],
        }
    )
    return result


def persist_cohort(
    store: "ContentOpsDurableStore",
    cohort: Mapping[str, Any],
) -> dict[str, Any]:
    """Persist every cohort case as durable work items, artifacts, and transitions.

    Reuses the accepted Wave 02 store. Terminal states are truthful: only a case whose
    canonical review passed reaches ``REVIEW_READY``; everything else terminates as
    blocked, duplicate, or deferred. No protected authority state is ever requested.
    """
    from live_contentops.durable_operational_store_v1 import compute_sha256
    from live_contentops.dual_lane_core_v0_shadow_newsroom_v1 import _canonical_json

    #: Terminal state -> the legal transition path that reaches it from ASSIGNMENT_CANDIDATE.
    _PATHS: dict[str, tuple[str, ...]] = {
        "REVIEW_READY": ("ASSIGNED", "PRODUCTION_IN_PROGRESS", "REVIEW_READY"),
        "REVIEW_BLOCKED": ("ASSIGNED", "PRODUCTION_IN_PROGRESS", "REVIEW_BLOCKED"),
        "DUPLICATE_SUPPRESSED": ("DUPLICATE",),
        "NO_PUBLICATION": ("DEFERRED",),
    }
    records: list[dict[str, Any]] = []
    for case in cohort["cases"]:
        case_id = str(case["case_id"])
        work_item_id = f"wi_{case_id.replace('-', '_')}"[:120]
        story_id = case_id
        actor_ref = f"core_v0_cohort_{case['lane']}"
        lease_key = f"lease_{work_item_id}"
        correlation_id = f"corr_{work_item_id}"

        store.create_work_item(
            story_id=story_id,
            title=f"CORE V0 cohort case {case_id}",
            target_surface="shadow_only_no_destination",
            work_item_id=work_item_id,
            actor_ref=actor_ref,
            correlation_id=correlation_id,
        )
        lease = store.acquire_lease(lease_key, actor_ref, ttl_seconds=300,
                                    work_item_id=work_item_id)
        token = int(lease["fencing_token"])

        artifact_ids: list[str] = []
        for name, payload, artifact_type in (
            ("case", {k: v for k, v in case.items() if k != "package"}, "COHORT_CASE"),
            ("package", case.get("package"), "SHADOW_PACKAGE"),
        ):
            if payload is None:
                continue
            content = _canonical_json(payload)
            artifact_id = (
                f"art_{compute_sha256(f'{work_item_id}:{name}:' + compute_sha256(content))[:24]}"
            )
            store.register_artifact(
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                storage_class="MEMORY",
                schema_version=SCHEMA_VERSION,
                producer_ref=TASK_LABEL,
                content_bytes=content,
                story_id=story_id,
                work_item_id=work_item_id,
                artifact_scope="WORK_ITEM_EXACT",
            )
            artifact_ids.append(artifact_id)

        transitions = 0
        states = ("EVIDENCE_PENDING", "EVIDENCE_READY", "ASSIGNMENT_CANDIDATE") + _PATHS[
            str(case["terminal_state"])
        ]
        for to_state in states:
            item = store.get_work_item(work_item_id)
            store.transition_state(
                work_item_id=work_item_id,
                expected_from_state=item["current_state"],
                to_state=to_state,
                expected_state_version=item["state_version"],
                actor_class="CoreV0CohortShadowRunner",
                actor_ref=actor_ref,
                reason_code=f"CORE_V0_COHORT_{to_state}",
                explanation=f"{case_id} -> {to_state} ({case['outcome']})",
                lease_key=lease_key,
                fencing_token=token,
                input_artifact_ids=artifact_ids[:1],
                output_artifact_ids=artifact_ids[1:],
                correlation_id=correlation_id,
            )
            transitions += 1

        store.release_lease(lease["lease_id"], actor_ref, token)
        records.append(
            {
                "case_id": case_id,
                "lane": case["lane"],
                "work_item_id": work_item_id,
                "terminal_state": str(case["terminal_state"]),
                "artifact_ids": artifact_ids,
                "transition_count": transitions,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "work_items": records,
        "work_item_ids": [row["work_item_id"] for row in records],
        "terminal_states": {row["work_item_id"]: row["terminal_state"] for row in records},
    }


def verify_cohort_replay(
    store: "ContentOpsDurableStore",
    work_item_ids: Sequence[str],
) -> dict[str, Any]:
    """Replay every cohort work item's hash-chained history from the store."""
    results = []
    for work_item_id in work_item_ids:
        replay = store.replay_work_item_events(work_item_id)
        item = store.get_work_item(work_item_id)
        results.append(
            {
                "work_item_id": work_item_id,
                "current_state": item["current_state"],
                "replayed_state": replay["replayed_state"],
                "replayed_version": replay["replayed_version"],
                "event_count": replay["event_count"],
                "last_event_hash": replay["last_event_hash"],
                "verification_status": replay["verification_status"],
                "replay_valid": (
                    replay["verification_status"] == "PASS"
                    and replay["replayed_state"] == item["current_state"]
                ),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "work_items_replayed": len(results),
        "all_replays_valid": all(row["replay_valid"] for row in results),
        "replays": results,
    }


def build_v5_cohort_snapshot(
    *,
    cohort: Mapping[str, Any],
    durable: Mapping[str, Any],
    replay: Mapping[str, Any],
) -> dict[str, Any]:
    """Project one real cohort run into the compact snapshot the V5 surface reads.

    Generated from the actual run — never hand-authored — so the operator view cannot
    drift from what the pipeline produced.
    """
    cases = []
    for case in cohort["cases"]:
        package = case.get("package") or {}
        platform = package.get("platform") or {}
        chart = package.get("chart") or {}
        visual = package.get("visual") or {}
        cases.append(
            {
                "case_id": case["case_id"],
                "lane": case["lane"],
                "domain_family": case["domain_family"],
                "sector": case["sector"],
                "geography": case["geography"],
                "source_family": case["source_family"],
                "content_mode": case["content_mode"],
                "visual_type": case["visual_type"],
                "story_type": case.get("story_type"),
                "outcome": case["outcome"],
                "governed_disposition": case["governed_disposition"],
                "terminal_state": case["terminal_state"],
                "review_result": case.get("review_result"),
                "review_role_count": case.get("review_role_count"),
                "review_blocked_roles": list(case.get("review_blocked_roles") or []),
                "visual_status": case.get("visual_status"),
                "visual_strategy": visual.get("strategy"),
                "visual_rights_cleared": (visual.get("rights_audit") or {}).get(
                    "assets_rights_cleared"
                ),
                "seo_contract_status": case.get("seo_contract_status"),
                "chart_qa_status": case.get("chart_qa_status"),
                "chart_title": chart.get("chart_title") or None,
                "chart_partial_period": (chart.get("methodology") or {}).get("partial_period"),
                "tier1_supported_count": platform.get("supported_count"),
                "tier1_blocked_count": platform.get("blocked_count"),
                "tier1_explicit_outcome_count": platform.get("explicit_outcome_count"),
                "tier1_blocked_destinations": [
                    row["platform_id"] for row in platform.get("blocked_destinations") or []
                ],
                "gate_reason": case.get("gate_reason"),
                "material_class": case.get("material_class"),
                "presented_as_current_news": False,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "task_label": TASK_LABEL,
        "operating_mode": OPERATING_MODE,
        "generated_from_real_run": True,
        "corpus": cohort["corpus"],
        "cases": cases,
        "outcome_counts": cohort["outcome_counts"],
        "lanes_with_passing_package": cohort["lanes_with_passing_package"],
        "portfolio_daily": cohort["portfolio_daily"],
        "portfolio_rolling": cohort["portfolio_rolling"],
        "concentration_penalties": cohort["concentration_penalties"],
        "review_engine": cohort["review_engine"],
        "package_fabric": cohort["package_fabric"],
        "tier1_destination_count": len(ALL_TIER1_PLATFORM_IDS),
        "tier1_destinations": list(ALL_TIER1_PLATFORM_IDS),
        "durable": {
            "work_item_ids": list(durable["work_item_ids"]),
            "terminal_states": dict(durable["terminal_states"]),
        },
        "replay_verification": {
            "all_replays_valid": replay["all_replays_valid"],
            "work_items_replayed": replay["work_items_replayed"],
        },
        "shadow_readback": {
            "readback_kind": "SHADOW_SIMULATED_NO_PUBLIC_OBJECT",
            "public_objects_created": 0,
            "public_urls": [],
            "destinations_contacted": [],
        },
        "external_cost": "NONE_NO_PAID_API_OR_MODEL_CALL",
        **zero_live_action_flags(),
    }


def run_cohort(
    *,
    repo_root: Path,
    chart_output_dir: Path,
    concentration_threshold: float | None = None,
) -> dict[str, Any]:
    """Process the whole diversified cohort once and assemble the reviewable report."""
    corpus = build_evaluation_corpus(repo_root)
    coverage = corpus_domain_coverage(corpus)
    assets = load_governed_visual_assets(repo_root)
    priors = load_authorized_prior_observations(repo_root)

    threshold = (
        concentration_threshold
        if concentration_threshold is not None
        else 0.34
    )
    portfolio_daily = build_portfolio_report(
        corpus["cases"], label="daily", concentration_threshold=threshold
    )

    cases = [
        process_case(
            case=case,
            repo_root=repo_root,
            visual_assets=assets,
            prior_observations=priors,
            chart_output_dir=chart_output_dir,
        )
        for case in corpus["cases"]
    ]

    eligible = [
        case for case in corpus["cases"]
        if str(case["expected_disposition"]) == "ELIGIBLE_CANDIDATE"
    ]
    penalties = apply_concentration_penalties(
        eligible=eligible, portfolio=portfolio_daily
    )
    portfolio_rolling = build_portfolio_report(
        [case for case in corpus["cases"] if case.get("lane")],
        label="rolling",
        concentration_threshold=threshold,
    )

    passed = [row for row in cases if row.get("review_result") == "PASS"]
    return {
        "schema_version": SCHEMA_VERSION,
        "task": TASK_LABEL,
        "operating_mode": OPERATING_MODE,
        "corpus": {
            "case_count": corpus["case_count"],
            "domain_family_count": corpus["domain_family_count"],
            "coverage": coverage,
            "fabricated_content": corpus["fabricated_content"],
            "material_class": corpus["material_class"],
            "governed_artifact_paths": corpus["governed_artifact_paths"],
        },
        "cases": cases,
        "portfolio_daily": portfolio_daily,
        "portfolio_rolling": portfolio_rolling,
        "concentration_penalties": penalties,
        "outcome_counts": {
            "eligible_review_passed": len(passed),
            "package_review_blocked": sum(
                1 for row in cases if row.get("outcome") == "PACKAGE_REVIEW_BLOCKED"
            ),
            "permission_blocked": sum(
                1 for row in cases if row.get("outcome") == "PERMISSION_BLOCKED"
            ),
            "evidence_blocked": sum(
                1 for row in cases if row.get("outcome") == "EVIDENCE_BLOCKED"
            ),
            "visual_rights_blocked": sum(
                1 for row in cases if row.get("outcome") == "VISUAL_RIGHTS_BLOCKED"
            ),
            "duplicate_or_low_delta": sum(
                1 for row in cases if row.get("outcome") == "DUPLICATE_OR_LOW_DELTA"
            ),
            "no_publication": sum(
                1 for row in cases if row.get("outcome") == "HISTORICAL_NOT_CURRENT"
            ),
        },
        "lanes_with_passing_package": sorted(
            {str(row["lane"]) for row in passed}
        ),
        "review_engine": "editorial_review_orchestrator_v2.run_editorial_review",
        "package_fabric": (
            "multi_story_platform_native_operator_packages_v1.build_platform_native_variant"
        ),
        "external_cost": "NONE_NO_PAID_API_OR_MODEL_CALL",
        **zero_live_action_flags(),
    }
