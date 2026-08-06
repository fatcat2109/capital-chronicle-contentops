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

    headline = str(candidate.get("title") or "Governed news candidate")
    summary = str(candidate.get("summary") or "")
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
        "primary_intent": "what happened to the treasury yield curve",
        "secondary_intent": "current 2s10s spread and 30-year yield level",
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
    if selected_id:
        candidate = next(
            row for row in pool["candidates"] if str(row["candidate_id"]) == str(selected_id)
        )
        drafted = _newsroom_article(candidate, newsroom)
        news_package = build_package(
            package_id=f"pkg-newsroom-{_logical_hash(selected_id)[:16]}",
            lane="newsroom",
            story_id=str(candidate.get("story_id") or selected_id),
            internal_links=[
                {"anchor": "Capital Chronicle analysis", "target": "/capital-chronicle-analysis"}
            ],
            **drafted,
        )
        news_review = review_package(
            package=news_package,
            lane_result=newsroom,
            authorized_claim_ids=drafted["claim_ids"],
        )
    newsroom["package_produced"] = news_package is not None

    # --- Capital Chronicle lane -------------------------------------------
    capital = run_capital_chronicle_lane(packet=packet)
    cc_drafted = _capital_chronicle_article(packet, capital)
    cc_package = build_package(
        package_id=f"pkg-capital-chronicle-{_logical_hash(capital['packet_id'])[:16]}",
        lane="capital_chronicle",
        story_id=str(capital["packet_id"]),
        internal_links=[{"anchor": "Newsroom coverage", "target": "/newsroom"}],
        **cc_drafted,
    )
    cc_review = review_package(
        package=cc_package,
        lane_result=capital,
        authorized_claim_ids=capital["authorized_claim_ids"],
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
            "review_result": news_review["result"] if news_review else None,
            "review_logical_hash": news_review["review_logical_hash"] if news_review else None,
        },
        "capital_chronicle_lane": {
            "outcome": "TRANSFORMED_PRESENTATION_ONLY",
            "packet_id": capital["packet_id"],
            "authorized_claim_count": capital["authorized_claim_count"],
            "chart_series_status": capital["chart_series"]["status"],
            "analytical_fidelity_result": capital["analytical_fidelity"]["result"],
            "package_id": cc_package["package_id"],
            "package_logical_hash": cc_package["package_logical_hash"],
            "review_result": cc_review["result"],
            "review_logical_hash": cc_review["review_logical_hash"],
        },
        "platform_capability": {
            "tier1_destination_count": cc_package["platform"]["tier1_destination_count"],
            "supported_count": cc_package["platform"]["supported_count"],
            "unsupported_count": cc_package["platform"]["unsupported_count"],
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
    args = parser.parse_args(list(argv) if argv is not None else sys.argv[2:])

    try:
        summary = run_core_v0_shadow_demo(
            news_input=Path(args.news_input),
            analysis_input=Path(args.analysis_input),
            store_path=Path(args.store),
            output_dir=Path(args.output),
            schedule_date=args.schedule_date,
            window={"window_id": args.window_id, "target_cutoff_utc": args.window_cutoff_utc},
            analysis_packet_id=args.analysis_packet_id,
        )
    except DualLaneShadowError as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, sort_keys=True, indent=2))
        return 1

    print(json.dumps(summary, sort_keys=True, indent=2))
    return 0
