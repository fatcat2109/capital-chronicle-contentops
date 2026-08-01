"""Decision-time freshness records for canonical local editorial packages."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from live_contentops.freshness_market_state_v2 import evaluate_freshness
from live_contentops.source_capability_registry_v2 import (
    load_source_capability_registry,
    resolve_story_capabilities,
)


TASK = "TASK_CONTENTOPS_FAST_SHIP_DECISION_TIME_FRESHNESS_AND_CURRENT_OPERATOR_READINESS_TRUTH_V1"
STARTING_REMOTE_HEAD = "fa829e72fb9fa873d41058d48a2da50270135407"
DEFAULT_OPERATOR_EVALUATION_AS_OF_UTC = "2026-08-01T00:00:00Z"
SOURCE_EVIDENCE_RELATIVE = Path(
    "docs/automation/"
    "CONTENTOPS_FAST_SHIP_STORY_SCOPED_PERMISSION_AND_FIRST_TEXT_ONLY_OPERATOR_READY_PACKAGE_V1"
)
OUTPUT_RELATIVE = Path(
    "docs/automation/"
    "CONTENTOPS_FAST_SHIP_DECISION_TIME_FRESHNESS_AND_CURRENT_OPERATOR_READINESS_TRUTH_V1"
)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def _logical_hash(value: Any) -> str:
    return sha256(_canonical_bytes(value)).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _first_timestamp(rows: list[Mapping[str, Any]], field: str) -> str | None:
    return next((str(row[field]) for row in rows if row.get(field)), None)


def build_decision_time_freshness_records(
    *,
    packets: Sequence[Mapping[str, Any]],
    outcomes: Sequence[Mapping[str, Any]],
    packages: Sequence[Mapping[str, Any]],
    operator_evaluation_as_of_utc: str,
    capability_registry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    registry = dict(capability_registry or load_source_capability_registry())
    outcomes_by_story = {str(row["story_id"]): row for row in outcomes}
    packages_by_story = {str(row["story_id"]): row for row in packages}
    records: list[dict[str, Any]] = []
    for packet in packets:
        source_documents = list(packet.get("official_source_documents") or [])
        claims = list((packet.get("governed_claim_graph") or {}).get("claims") or [])
        if len(source_documents) != 1:
            raise ValueError("decision_time_source_document_not_exactly_one")
        source_family = str(source_documents[0].get("source_family_id") or "")
        capability = resolve_story_capabilities(
            {"source_family_id": source_family}, registry
        )
        if capability.get("status") != "PASS":
            raise ValueError(
                "decision_time_capability_unresolved:"
                + ",".join(capability.get("blockers") or [])
            )
        story_matches = [
            story_id
            for story_id, outcome in outcomes_by_story.items()
            if outcome.get("v3_packet_id") == packet.get("packet_id")
        ]
        if len(story_matches) != 1:
            raise ValueError("decision_time_story_binding_not_exactly_one")
        story_id = story_matches[0]
        outcome = outcomes_by_story[story_id]
        package = packages_by_story[story_id]
        request = {
            "story_type": capability["story_type"],
            "article_mode": capability["article_mode"],
            "market_sensitive": capability["market_sensitive"],
            "market_snapshot_required": capability["market_snapshot_required"],
            "fresh_material_delta": False,
            "expected_source_cadence": capability.get("freshness_policy"),
        }
        historical = evaluate_freshness(
            packet,
            {
                **request,
                "readiness_evaluation_basis": "HISTORICAL_POINT_IN_TIME_REPLAY",
            },
        )
        current = evaluate_freshness(
            packet,
            {
                **request,
                "readiness_evaluation_basis": "CURRENT_OPERATOR_READINESS",
                "operator_evaluation_as_of_utc": operator_evaluation_as_of_utc,
            },
        )
        if current["operator_evaluation_as_of_utc"] is None:
            raise ValueError("operator_evaluation_as_of_utc_unresolved")
        core = {
            "schema_version": "contentops.decision_time_freshness_record.v1",
            "record_id": f"decision-time-freshness:{story_id}",
            "story_id": story_id,
            "source_family": source_family,
            "story_type": capability["story_type"],
            "article_mode": capability["article_mode"],
            "market_sensitive": capability["market_sensitive"],
            "market_snapshot_required": capability["market_snapshot_required"],
            "source_timestamps": {
                "event_at_utc": _first_timestamp(claims, "event_time_utc"),
                "published_at_utc": str(source_documents[0].get("published_at_utc") or "") or None,
                "known_at_utc": str(source_documents[0].get("known_at_utc") or "") or None,
                "revision_at_utc": _first_timestamp(claims, "revision_at_utc"),
            },
            "historical_point_in_time_replay": historical,
            "current_operator_readiness": current,
            "hashes": {
                "package_hash": package["package_hash"],
                "article_hash": outcome["canonical_article_hash"],
                "v3_packet_hash": outcome["v3_packet_logical_hash"],
                "historical_freshness_hash": _logical_hash(historical),
                "current_freshness_hash": _logical_hash(current),
            },
            "canonical_package_evidence_unchanged": True,
            "publication_authority": False,
            "dispatch_authority": False,
            "public_write_authority": False,
        }
        records.append({**core, "record_hash": _logical_hash(core)})
    document_core = {
        "schema_version": "contentops.decision_time_freshness_records.v1",
        "task": TASK,
        "starting_remote_head": STARTING_REMOTE_HEAD,
        "operator_evaluation_as_of_utc": operator_evaluation_as_of_utc,
        "historical_result_kind": "HISTORICAL_POINT_IN_TIME_REPLAY",
        "current_result_kind": "CURRENT_OPERATOR_READINESS",
        "record_count": len(records),
        "records": records,
        "canonical_package_evidence_unchanged": True,
        "publication_authority": False,
        "dispatch_authority": False,
        "public_write_authority": False,
        "network_call_performed": False,
        "browser_platform_action_performed": False,
    }
    return {**document_core, "logical_hash": _logical_hash(document_core)}


def generate_decision_time_freshness_records(
    *, repo_root: Path, operator_evaluation_as_of_utc: str
) -> dict[str, Any]:
    source_dir = repo_root / SOURCE_EVIDENCE_RELATIVE
    packets = _read_json(source_dir / "canonical_content_evidence_packets_v3.json")
    outcomes = _read_json(source_dir / "canonical_editorial_outcomes.json")
    packages = _read_json(source_dir / "superseding_unsigned_operator_packages.json")
    document = build_decision_time_freshness_records(
        packets=packets["packets"],
        outcomes=outcomes["outcomes"],
        packages=packages["packages"],
        operator_evaluation_as_of_utc=operator_evaluation_as_of_utc,
    )
    _write_json(repo_root / OUTPUT_RELATIVE / "decision_time_freshness_records.json", document)
    return document


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--operator-evaluation-as-of-utc",
        required=True,
        help="Explicit fixed decision-time cutoff; never inferred from packet time.",
    )
    args = parser.parse_args(argv)
    result = generate_decision_time_freshness_records(
        repo_root=args.repo_root.resolve(),
        operator_evaluation_as_of_utc=args.operator_evaluation_as_of_utc,
    )
    print(json.dumps({"record_count": result["record_count"], "logical_hash": result["logical_hash"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
