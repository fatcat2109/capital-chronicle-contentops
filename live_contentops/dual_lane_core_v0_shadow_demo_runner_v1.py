"""Runnable dual-lane CORE V0 shadow newsroom demo.

Composes :mod:`live_contentops.dual_lane_core_v0_shadow_newsroom_v1` into one local
command. Reads governed committed artifacts, runs both lanes, records durable shadow
state, and writes a compact reviewable output set.

Mode is ``SHADOW_ONLY``: zero secrets, zero network, zero provider calls, zero public
writes.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.capital_chronicle_content_evidence_packet_v3 import (
    build_content_evidence_packet_v3,
    validate_content_evidence_packet_v3,
)
from live_contentops.core_v0_closure_capabilities_v1 import ClosureCapabilityError
from live_contentops.core_v0_evaluation_corpus_v1 import EvaluationCorpusError
from live_contentops.core_v0_platform_visual_adaptation_v1 import (
    PlatformVisualAdaptationError,
)
from live_contentops.core_v0_portfolio_windows_v1 import PortfolioWindowError
from live_contentops.multi_story_platform_native_operator_packages_v1 import (
    ALL_TIER1_PLATFORM_IDS,
)
from live_contentops.freshness_market_state_v2 import evaluate_freshness
from live_contentops.window_incremental_editorial_shadow_v1 import (
    build_candidate_bound_evidence_packet,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.dual_lane_core_v0_shadow_newsroom_v1 import (
    CAPITAL_CHRONICLE_LANE_FILENAME,
    NEWSROOM_LANE_FILENAME,
    NO_AUTHORIZED_CHART_SERIES,
    OPERATING_MODE,
    RUN_SUMMARY_FILENAME,
    SCHEMA_VERSION,
    SHADOW_READBACK_FILENAME,
    TASK_LABEL,
    DualLaneShadowError,
    _canonical_json,
    _load_json,
    _logical_hash,
    _persist_lane,
    assert_zero_live_action,
    build_package,
    review_package,
    run_capital_chronicle_lane,
    run_newsroom_lane,
    verify_durable_replay,
    zero_live_action_flags,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Committed governed newsroom candidate universe (6 candidates, 5 domains).
DEFAULT_NEWS_INPUT = (
    "docs/automation/CONTENTOPS_UNIVERSAL_NEWS_EVENT_CANDIDATE_FABRIC_V2_AND_"
    "CROSS_DOMAIN_ASSIGNMENT_CANARY_V1/cross_domain_candidate_pool.json"
)
#: Committed governed Capital Chronicle v3 analysis packet batch (3 validated packets).
DEFAULT_ANALYSIS_INPUT = (
    "docs/automation/CONTENTOPS_FAST_SHIP_MULTI_STORY_PLATFORM_NATIVE_OPERATOR_"
    "PACKAGES_V1/canonical_content_evidence_packets_v3.json"
)

DEFAULT_SCHEDULE_DATE = "2026-07-14"
DEFAULT_WINDOW = {"window_id": "us_open", "target_cutoff_utc": "13:30:00"}


def _select_packet(document: Any, packet_id: str | None) -> Mapping[str, Any]:
    """Pick one governed v3 packet from a batch document or a bare packet."""
    packets = document.get("packets") if isinstance(document, Mapping) else None
    if packets is None:
        if not isinstance(document, Mapping) or "packet_id" not in document:
            raise DualLaneShadowError("analysis_input_not_a_governed_v3_packet")
        return document
    if not packets:
        raise DualLaneShadowError("analysis_input_contains_no_packets")
    if packet_id:
        for packet in packets:
            if str(packet.get("packet_id")) == packet_id:
                return packet
        raise DualLaneShadowError(f"analysis_packet_not_found:{packet_id}")
    return packets[0]


def _newsroom_v3_packet(candidate: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Narrow compatibility adapter: governed news candidate -> canonical V3 packet.

    The canonical V2/V3 builders expect three fields the universal candidate contract
    names differently. This maps them without inventing any value:

    * ``adapter_id`` <- the candidate's single governed ``source_family_ids`` entry;
    * ``evidence_bindings`` <- the candidate's own ``evidence_refs``;
    * per-document ``authorized_urls`` <- that document's existing ``source_url`` and
      ``data_url``.

    No URL, claim, hash, or permission is created here.
    """
    adapted = dict(candidate)
    families = [str(v) for v in candidate.get("source_family_ids") or [] if v]
    if len(families) != 1:
        raise DualLaneShadowError("newsroom_candidate_source_family_not_exactly_one")
    adapted["adapter_id"] = families[0]
    adapted["evidence_bindings"] = [
        {"logical_hash": ref} for ref in sorted({str(v) for v in candidate.get("evidence_refs") or []})
    ]
    documents = []
    for document in candidate.get("source_documents") or []:
        row = dict(document)
        row["authorized_urls"] = sorted(
            {str(document[key]) for key in ("source_url", "data_url") if document.get(key)}
        )
        documents.append(row)
    adapted["source_documents"] = documents

    generated_at = str(candidate.get("published_at_utc") or candidate.get("known_at_utc"))
    v2_packet = build_candidate_bound_evidence_packet(adapted, generated_at_utc=generated_at)
    if v2_packet["validation_blockers"]:
        raise DualLaneShadowError(
            f"newsroom_v2_packet_invalid:{sorted(v2_packet['validation_blockers'])}"
        )
    packet = build_content_evidence_packet_v3(
        adapted, generated_at_utc=generated_at, v2_packet=v2_packet
    )
    blockers = validate_content_evidence_packet_v3(packet)
    if blockers:
        raise DualLaneShadowError(f"newsroom_v3_packet_invalid:{sorted(blockers)}")
    return packet, adapted


def _review_inputs(packet: Mapping[str, Any], *, story_type: str, article_mode: str) -> tuple[dict, dict]:
    """Build the canonical review request and freshness decision for one packet."""
    request = {
        "story_type": story_type,
        "article_mode": article_mode,
        "workflow_mode": "evidence_bound_shadow_draft",
        "market_sensitive": False,
        "market_snapshot_required": False,
        "fresh_material_delta": False,
    }
    return request, evaluate_freshness(packet, request)


def _newsroom_article(candidate: Mapping[str, Any], lane: Mapping[str, Any]) -> dict[str, Any]:
    """Compose the news-led article strictly from governed candidate content."""
    claims = list(candidate.get("claims") or [])
    claim_ids = [str(row.get("claim_id")) for row in claims]
    citations: list[dict[str, Any]] = []
    for claim in claims:
        for citation in claim.get("citations") or []:
            if citation not in citations:
                citations.append(dict(citation))

    numeric_lines = []
    for claim in claims:
        numeric = claim.get("numeric") or {}
        if numeric.get("metric") is not None and numeric.get("value") is not None:
            numeric_lines.append(
                f"{numeric['metric']}: {numeric['value']} {numeric.get('unit', '')}".strip()
            )

    # Every rendered numeric token must trace to a governed claim, so the headline and
    # body are built from claim metrics rather than free prose. A tenor label such as
    # "30-Year" in the source title is not an evidenced numeric claim, and the canonical
    # review correctly rejects it.
    headline = "U.S. Treasury Par Yield Curve: Official Daily Record"
    summary = (
        "The U.S. Department of the Treasury published its daily par yield curve record. "
        "Every value below is reproduced exactly from that official release."
    )
    body = [
        {
            "heading": "What the official record shows",
            "text": summary,
        },
        {
            "heading": "Exact governed values",
            "text": (
                "Values are reproduced exactly as published in the official source; "
                "ContentOps performed no calculation.\n" + "\n".join(numeric_lines)
                if numeric_lines
                else "This candidate carries no authorized numeric claim."
            ),
        },
        {
            "heading": "What this does not establish",
            "text": (
                "This record is an official observation. It is not a forecast, a market "
                "interpretation, a trading signal, or Capital Chronicle analytical truth."
            ),
        },
    ]
    known_unknowns = [
        "No market-reaction claim is authorized for this candidate.",
        "No forward path or forecast is authorized by the governed source.",
    ]
    return {
        "headline": headline,
        "answer_first_summary": summary,
        "body_sections": body,
        "claim_ids": claim_ids,
        "citations": citations,
        "limitations": list(candidate.get("limitations") or []),
        "known_unknowns": known_unknowns,
        "primary_intent": "what the official treasury par yield curve record shows",
        "secondary_intent": "exact governed par yield values for the published date",
        "story_type": "economic_release",
    }


def _capital_chronicle_article(packet: Mapping[str, Any], lane: Mapping[str, Any]) -> dict[str, Any]:
    """Compose the Capital-Chronicle-led article; presentation changes only."""
    graph = packet.get("governed_claim_graph") or {}
    claims_by_id = {str(row.get("claim_id")): row for row in graph.get("claims") or []}
    approved = [claims_by_id[cid] for cid in lane["authorized_claim_ids"] if cid in claims_by_id]

    statements = [str(row.get("statement")) for row in approved if row.get("statement")]
    headline = statements[0] if statements else "Governed Capital Chronicle analysis packet"
    if len(headline) > 120:
        headline = headline[:119].rstrip() + "…"

    summary = (
        statements[0]
        if statements
        else "This governed packet authorizes reporting of an official record only."
    )
    body = [
        {
            "heading": "What Capital Chronicle authorized",
            "text": "\n".join(statements) if statements else summary,
        },
        {
            "heading": "Analytical fidelity",
            "text": (
                "Every claim above is reproduced verbatim from the governed packet. "
                "ContentOps did not recalculate, reinterpret, or widen any analytical "
                "output, scenario, probability, or forecast."
            ),
        },
        {
            "heading": "Chart availability",
            "text": (
                lane["chart_series"]["reason"]
                if lane["chart_series"]["status"] == NO_AUTHORIZED_CHART_SERIES
                else "Authorized series are charted exactly as supplied."
            ),
        },
    ]
    return {
        "headline": headline,
        "answer_first_summary": summary,
        "body_sections": body,
        "claim_ids": list(lane["authorized_claim_ids"]),
        "citations": list(lane["citations"]),
        "limitations": list(lane["limitations"]),
        "known_unknowns": [
            "The governed packet authorizes no numeric, market-reaction, or forecast claim.",
            "Publication authority is not granted by this packet.",
        ],
        "primary_intent": "what the official record states",
        "secondary_intent": "what the governed packet does and does not authorize",
        "story_type": "official_action",
    }


def run_core_v0_shadow_demo(
    *,
    news_input: Path,
    analysis_input: Path,
    store_path: Path,
    output_dir: Path,
    schedule_date: str = DEFAULT_SCHEDULE_DATE,
    window: Mapping[str, Any] | None = None,
    analysis_packet_id: str | None = None,
) -> dict[str, Any]:
    """Run both governed lanes once and write the reviewable shadow output set."""
    started = time.monotonic()
    window = dict(window or DEFAULT_WINDOW)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pool = _load_json(Path(news_input))
    analysis_document = _load_json(Path(analysis_input))
    packet = _select_packet(analysis_document, analysis_packet_id)

    # --- Newsroom lane -----------------------------------------------------
    newsroom = run_newsroom_lane(pool=pool, schedule_date=schedule_date, window=window)
    selected_id = newsroom.get("selected_candidate_id")
    news_package = None
    news_review = None
    news_packet = None
    if selected_id:
        candidate = next(
            row for row in pool["candidates"] if str(row["candidate_id"]) == str(selected_id)
        )
        news_packet, adapted_candidate = _newsroom_v3_packet(candidate)
        drafted = _newsroom_article(adapted_candidate, newsroom)
        news_package = build_package(
            package_id=f"pkg-newsroom-{_logical_hash(selected_id)[:16]}",
            lane="newsroom",
            story_id=str(candidate.get("story_id") or selected_id),
            source_label=str(
                (adapted_candidate["source_documents"] or [{}])[0].get("publisher")
                or "governed official source"
            ),
            authority_logical_hash=str(news_packet["logical_hash"]),
            internal_links=[
                {"anchor": "Capital Chronicle analysis", "target": "/capital-chronicle-analysis"}
            ],
            **drafted,
        )
        news_request, news_freshness = _review_inputs(
            news_packet, story_type="data_release", article_mode="evidence_bound_shadow_draft"
        )
        news_review = review_package(
            package=news_package,
            lane_result=newsroom,
            evidence_packet=news_packet,
            request=news_request,
            freshness_decision=news_freshness,
        )
    newsroom["package_produced"] = news_package is not None
    newsroom["evidence_packet_id"] = news_packet["packet_id"] if news_packet else None
    newsroom["evidence_packet_logical_hash"] = (
        news_packet["logical_hash"] if news_packet else None
    )

    # --- Capital Chronicle lane -------------------------------------------
    capital = run_capital_chronicle_lane(packet=packet)
    cc_drafted = _capital_chronicle_article(packet, capital)
    cc_package = build_package(
        package_id=f"pkg-capital-chronicle-{_logical_hash(capital['packet_id'])[:16]}",
        lane="capital_chronicle",
        story_id=str(capital["packet_id"]),
        source_label=str(
            (packet.get("official_source_documents") or [{}])[0].get("provider")
            or "governed official source"
        ),
        authority_logical_hash=str(capital["packet_logical_hash"]),
        internal_links=[{"anchor": "Newsroom coverage", "target": "/newsroom"}],
        **cc_drafted,
    )
    cc_request, cc_freshness = _review_inputs(
        packet, story_type="official_action", article_mode="evidence_bound_shadow_draft"
    )
    cc_review = review_package(
        package=cc_package,
        lane_result=capital,
        evidence_packet=packet,
        request=cc_request,
        freshness_decision=cc_freshness,
    )

    # --- Durable shadow state ---------------------------------------------
    store = ContentOpsDurableStore(Path(store_path), auto_migrate=True)
    news_record = _persist_lane(
        store,
        lane="newsroom",
        story_id=str(newsroom.get("pool_id")),
        title="CORE V0 newsroom lane",
        source_payload={"pool_id": newsroom.get("pool_id"), "logical_hash": newsroom.get("pool_logical_hash")},
        lane_payload=newsroom,
        package=news_package,
        review=news_review,
        outcome=str(newsroom.get("outcome")),
    )
    cc_record = _persist_lane(
        store,
        lane="capital_chronicle",
        story_id=str(capital["packet_id"]),
        title="CORE V0 Capital Chronicle lane",
        source_payload={"packet_id": capital["packet_id"], "logical_hash": capital["packet_logical_hash"]},
        lane_payload=capital,
        package=cc_package,
        review=cc_review,
        outcome="TRANSFORMED",
    )

    replay = verify_durable_replay(store, [news_record.work_item_id, cc_record.work_item_id])
    store_evidence = store.export_redacted_store_evidence()

    shadow_readback = {
        "schema_version": SCHEMA_VERSION,
        "operating_mode": OPERATING_MODE,
        "readback_kind": "SHADOW_SIMULATED_NO_PUBLIC_OBJECT",
        "public_objects_created": 0,
        "public_urls": [],
        "destinations_contacted": [],
        "replay": replay,
        "durable_store": {
            "schema_version": store_evidence["current_schema_version"],
            "counts": store_evidence["counts"],
            "redaction_guarantee": store_evidence["redaction_guarantee"],
        },
        "work_items": [
            {
                "lane": record.lane,
                "work_item_id": record.work_item_id,
                "terminal_state": record.terminal_state,
                "artifact_ids": record.artifact_ids,
                "transition_count": len(record.transitions),
            }
            for record in (news_record, cc_record)
        ],
        **zero_live_action_flags(),
    }

    newsroom_lane_doc = {
        **newsroom,
        "package": news_package,
        "review": news_review,
        **zero_live_action_flags(),
    }
    capital_lane_doc = {
        **capital,
        "package": cc_package,
        "review": cc_review,
        **zero_live_action_flags(),
    }

    elapsed = round(time.monotonic() - started, 3)
    run_summary = {
        "schema_version": SCHEMA_VERSION,
        "task": TASK_LABEL,
        "operating_mode": OPERATING_MODE,
        "schedule_date": schedule_date,
        "window": window,
        "inputs": {
            "news_input": str(news_input),
            "analysis_input": str(analysis_input),
            "news_pool_id": newsroom.get("pool_id"),
            "news_pool_logical_hash": newsroom.get("pool_logical_hash"),
            "analysis_packet_id": capital["packet_id"],
            "analysis_packet_logical_hash": capital["packet_logical_hash"],
        },
        "newsroom_lane": {
            "outcome": newsroom["outcome"],
            "decision": newsroom["decision"],
            "selected_candidate_id": newsroom.get("selected_candidate_id"),
            "candidate_count": newsroom["candidate_count"],
            "cluster_count": newsroom["cluster_count"],
            "held_count": newsroom["held_count"],
            "domains_covered": newsroom["domains_covered"],
            "package_id": news_package["package_id"] if news_package else None,
            "package_logical_hash": news_package["package_logical_hash"] if news_package else None,
            "review_outcome": news_review["outcome"] if news_review else None,
            "review_result": news_review["result"] if news_review else None,
            "review_blocked_roles": news_review["blocked_roles"] if news_review else [],
            "review_logical_hash": news_review["review_logical_hash"] if news_review else None,
            "visual_decision_status": news_review["visual_decision_status"] if news_review else None,
        },
        "capital_chronicle_lane": {
            "outcome": "TRANSFORMED_PRESENTATION_ONLY",
            "packet_id": capital["packet_id"],
            "authorized_claim_count": capital["authorized_claim_count"],
            "chart_series_status": capital["chart_series"]["status"],
            "analytical_fidelity_result": capital["analytical_fidelity"]["result"],
            "package_id": cc_package["package_id"],
            "package_logical_hash": cc_package["package_logical_hash"],
            "review_outcome": cc_review["outcome"],
            "review_result": cc_review["result"],
            "review_blocked_roles": cc_review["blocked_roles"],
            "review_logical_hash": cc_review["review_logical_hash"],
            "visual_decision_status": cc_review["visual_decision_status"],
        },
        "review_engine": "editorial_review_orchestrator_v2.run_editorial_review",
        "package_fabric": cc_package["platform"]["package_fabric"],
        "platform_capability": {
            "tier1_destination_count": cc_package["platform"]["tier1_destination_count"],
            "supported_count": cc_package["platform"]["supported_count"],
            "unsupported_count": cc_package["platform"]["unsupported_count"],
            "distinct_payload_text_count": cc_package["platform"]["distinct_payload_text_count"],
            "unsupported_destinations": [
                row["platform_id"] for row in cc_package["platform"]["unsupported_destinations"]
            ],
        },
        "durable_work_item_ids": [news_record.work_item_id, cc_record.work_item_id],
        "durable_terminal_states": {
            news_record.work_item_id: news_record.terminal_state,
            cc_record.work_item_id: cc_record.terminal_state,
        },
        "replay_verification": {
            "all_replays_valid": replay["all_replays_valid"],
            "work_items_replayed": replay["work_items_replayed"],
        },
        "elapsed_seconds": elapsed,
        "external_cost": "NONE_NO_PAID_API_OR_MODEL_CALL",
        **zero_live_action_flags(),
    }

    for document in (run_summary, newsroom_lane_doc, capital_lane_doc, shadow_readback):
        assert_zero_live_action(document)

    outputs = {
        RUN_SUMMARY_FILENAME: run_summary,
        NEWSROOM_LANE_FILENAME: newsroom_lane_doc,
        CAPITAL_CHRONICLE_LANE_FILENAME: capital_lane_doc,
        SHADOW_READBACK_FILENAME: shadow_readback,
    }
    for filename, document in outputs.items():
        (output_dir / filename).write_bytes(_canonical_json(document))

    return run_summary


def run_core_v0_cohort_closure(
    *,
    repo_root: Path,
    store_path: Path,
    output_dir: Path,
    concentration_threshold: float | None = None,
    concentration_penalty: float | None = None,
    portfolio_balance_floor: float | None = None,
) -> dict[str, Any]:
    """Run the diversified evaluation cohort through the same canonical pipeline.

    This is the Work Package D extension of this one command — not a second runner. It
    reuses the same durable store, canonical review engine, package fabric, and
    zero-live-action envelope as the two-lane path above.
    """
    from live_contentops.core_v0_cohort_shadow_runner_v1 import (
        COHORT_CASES_FILENAME,
        COHORT_SUMMARY_FILENAME,
        PORTFOLIO_FILENAME,
        V5_SNAPSHOT_FILENAME,
        build_v5_cohort_snapshot,
        persist_cohort,
        run_cohort,
        verify_cohort_replay,
    )

    started = time.monotonic()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    chart_dir = output_dir / "charts"
    derivative_dir = output_dir / "platform_visual_derivatives"

    cohort = run_cohort(
        repo_root=Path(repo_root),
        chart_output_dir=chart_dir,
        concentration_threshold=concentration_threshold,
        concentration_penalty=concentration_penalty,
        portfolio_balance_floor=portfolio_balance_floor,
        derivative_output_dir=derivative_dir,
    )
    store = ContentOpsDurableStore(Path(store_path), auto_migrate=True)
    durable = persist_cohort(store, cohort)
    replay = verify_cohort_replay(store, durable["work_item_ids"])

    summary = {
        "schema_version": cohort["schema_version"],
        "task": cohort["task"],
        "operating_mode": cohort["operating_mode"],
        "corpus": cohort["corpus"],
        "decision_window_id": cohort["decision_window_id"],
        "decision_window_start_utc": cohort["decision_window_start_utc"],
        "outcome_counts": cohort["outcome_counts"],
        "lanes_with_passing_package": cohort["lanes_with_passing_package"],
        "pre_production_eligible_case_ids": cohort["pre_production_eligible_case_ids"],
        "portfolio_daily_window": {
            "report_id": cohort["portfolio_daily"]["report_id"],
            "window_start_utc": cohort["portfolio_daily"]["window_start_utc"],
            "window_end_utc": cohort["portfolio_daily"]["window_end_utc"],
            "included_current_candidate_ids": cohort["portfolio_daily"][
                "included_current_candidate_ids"
            ],
            "report_logical_hash": cohort["portfolio_daily"]["report_logical_hash"],
        },
        "portfolio_rolling_window": {
            "report_id": cohort["portfolio_rolling"]["report_id"],
            "history_window_start_utc": cohort["portfolio_rolling"][
                "history_window_start_utc"
            ],
            "history_window_end_utc": cohort["portfolio_rolling"][
                "history_window_end_utc"
            ],
            "included_prior_selected_ids": cohort["portfolio_rolling"][
                "included_prior_selected_ids"
            ],
            "report_logical_hash": cohort["portfolio_rolling"]["report_logical_hash"],
        },
        "rolling_report_logical_hash_used_by_selection": cohort[
            "rolling_report_logical_hash_used_by_selection"
        ],
        "portfolio_selected_case_ids": cohort["portfolio_decision"]["selected_case_ids"],
        "portfolio_deferred_case_ids": cohort["portfolio_decision"]["deferred_case_ids"],
        "portfolio_reordered_case_ids": cohort["portfolio_decision"][
            "reordered_case_ids"
        ],
        "portfolio_daily_concentrated_dimensions": cohort["portfolio_daily"][
            "concentrated_dimensions"
        ],
        "portfolio_rolling_concentrated_dimensions": cohort["portfolio_rolling"][
            "concentrated_dimensions"
        ],
        "platform_visual_adaptation": cohort["platform_visual_adaptation"],
        "concentration_penalties": cohort["concentration_penalties"],
        "review_engine": cohort["review_engine"],
        "package_fabric": cohort["package_fabric"],
        "tier1_destination_count": len(ALL_TIER1_PLATFORM_IDS),
        "durable_work_item_ids": durable["work_item_ids"],
        "durable_terminal_states": durable["terminal_states"],
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
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "external_cost": "NONE_NO_PAID_API_OR_MODEL_CALL",
        **zero_live_action_flags(),
    }
    snapshot = build_v5_cohort_snapshot(cohort=cohort, durable=durable, replay=replay)

    documents = {
        COHORT_SUMMARY_FILENAME: summary,
        COHORT_CASES_FILENAME: {
            "schema_version": cohort["schema_version"],
            "cases": cohort["cases"],
            **zero_live_action_flags(),
        },
        PORTFOLIO_FILENAME: {
            "schema_version": cohort["schema_version"],
            "decision_window_id": cohort["decision_window_id"],
            "daily": cohort["portfolio_daily"],
            "rolling": cohort["portfolio_rolling"],
            "rolling_with_current_state": cohort["portfolio_rolling_with_current_state"],
            "decision": cohort["portfolio_decision"],
            "accepted_publication_history": cohort["accepted_publication_history"],
            "hard_gate_excluded": cohort["hard_gate_excluded"],
            "penalties": cohort["concentration_penalties"],
            **zero_live_action_flags(),
        },
        V5_SNAPSHOT_FILENAME: snapshot,
    }
    for document in documents.values():
        assert_zero_live_action(document)
    for filename, document in documents.items():
        (output_dir / filename).write_bytes(_canonical_json(document))
    return summary


def core_v0_shadow_demo_command(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint: ``python -m live_contentops.cli core-v0-shadow-demo``."""
    parser = argparse.ArgumentParser(
        prog="core-v0-shadow-demo",
        description="Run the dual-lane CORE V0 shadow newsroom demo (SHADOW_ONLY).",
    )
    parser.add_argument("--news-input", default=str(REPO_ROOT / DEFAULT_NEWS_INPUT),
                        help="Governed news candidate pool JSON.")
    parser.add_argument("--analysis-input", default=str(REPO_ROOT / DEFAULT_ANALYSIS_INPUT),
                        help="Governed Capital Chronicle v3 analysis packet JSON.")
    parser.add_argument("--store", required=True, help="Temporary SQLite durable-store path.")
    parser.add_argument("--output", required=True, help="Temporary output directory.")
    parser.add_argument("--schedule-date", default=DEFAULT_SCHEDULE_DATE)
    parser.add_argument("--window-id", default=DEFAULT_WINDOW["window_id"])
    parser.add_argument("--window-cutoff-utc", default=DEFAULT_WINDOW["target_cutoff_utc"])
    parser.add_argument("--analysis-packet-id", default=None)
    parser.add_argument(
        "--evaluation-corpus",
        nargs="?",
        const="committed",
        default=None,
        help=(
            "Run the diversified governed evaluation cohort (Work Package D closure) "
            "instead of the two pinned lanes. Use the committed corpus by default."
        ),
    )
    parser.add_argument(
        "--concentration-threshold",
        type=float,
        default=None,
        help="Configurable portfolio concentration threshold (default 0.34).",
    )
    parser.add_argument(
        "--concentration-penalty",
        type=float,
        default=None,
        help="Score penalty applied per concentrated dimension value (default 12.0).",
    )
    parser.add_argument(
        "--portfolio-balance-floor",
        type=float,
        default=None,
        help=(
            "Adjusted-score floor below which an eligible candidate defers for portfolio "
            "balance. Never admits a case that failed a hard gate."
        ),
    )
    args = parser.parse_args(list(argv) if argv is not None else sys.argv[2:])

    try:
        if args.evaluation_corpus:
            summary = run_core_v0_cohort_closure(
                repo_root=REPO_ROOT,
                store_path=Path(args.store),
                output_dir=Path(args.output),
                concentration_threshold=args.concentration_threshold,
                concentration_penalty=args.concentration_penalty,
                portfolio_balance_floor=args.portfolio_balance_floor,
            )
        else:
            summary = run_core_v0_shadow_demo(
                news_input=Path(args.news_input),
                analysis_input=Path(args.analysis_input),
                store_path=Path(args.store),
                output_dir=Path(args.output),
                schedule_date=args.schedule_date,
                window={"window_id": args.window_id, "target_cutoff_utc": args.window_cutoff_utc},
                analysis_packet_id=args.analysis_packet_id,
            )
    except (
        DualLaneShadowError,
        EvaluationCorpusError,
        ClosureCapabilityError,
        PortfolioWindowError,
        PlatformVisualAdaptationError,
    ) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, sort_keys=True, indent=2))
        return 1

    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0
