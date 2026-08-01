"""Fail-closed point-in-time authority evaluation for governed story evidence."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence


TASK = "TASK_CONTENTOPS_FAST_SHIP_TEMPORAL_AUTHORITY_AND_POINT_IN_TIME_REPLAY_INTEGRITY_V1"
STARTING_REMOTE_HEAD = "1548196ebffd2bc7ce82a4ae290211b9c53a45df"
SOURCE_TIME_RESULT_KIND = "HISTORICAL_SOURCE_TIME_FRESHNESS_REPLAY"
AUTHORITY_RESULT_KIND = "POINT_IN_TIME_AUTHORITY_STATUS"
CURRENT_RESULT_KIND = "CURRENT_OPERATOR_READINESS"
SOURCE_EVIDENCE_RELATIVE = Path(
    "docs/automation/"
    "CONTENTOPS_FAST_SHIP_STORY_SCOPED_PERMISSION_AND_FIRST_TEXT_ONLY_OPERATOR_READY_PACKAGE_V1"
)
DECISION_TIME_EVIDENCE_RELATIVE = Path(
    "docs/automation/"
    "CONTENTOPS_FAST_SHIP_DECISION_TIME_FRESHNESS_AND_CURRENT_OPERATOR_READINESS_TRUTH_V1"
)
OUTPUT_RELATIVE = Path(
    "docs/automation/"
    "CONTENTOPS_FAST_SHIP_TEMPORAL_AUTHORITY_AND_POINT_IN_TIME_REPLAY_INTEGRITY_V1"
)
UNEVIDENCED_MARKERS = {
    "legacy_retrieval_timestamp_not_evidenced",
    "not_evidenced",
    "unknown",
    "unavailable",
}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def logical_hash(value: Any) -> str:
    return sha256(_canonical_bytes(value)).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


@dataclass(frozen=True)
class TemporalValue:
    raw: str | None
    state: str
    precision: str | None
    instant: datetime | None

    def evidence(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "state": self.state,
            "precision": self.precision,
            "normalized_utc": (
                self.instant.astimezone(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
                if self.instant is not None and self.precision == "INSTANT"
                else None
            ),
        }


def parse_temporal_value(value: Any) -> TemporalValue:
    """Parse only evidenced precision; never manufacture a time for a date."""
    if value is None or str(value).strip() == "":
        return TemporalValue(None, "UNEVIDENCED", None, None)
    raw = str(value).strip()
    if raw.casefold() in UNEVIDENCED_MARKERS or "not_evidenced" in raw.casefold():
        return TemporalValue(raw, "UNEVIDENCED", None, None)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError:
            return TemporalValue(raw, "INVALID", None, None)
        return TemporalValue(raw, "EVIDENCED", "DATE", parsed)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return TemporalValue(raw, "INVALID", None, None)
    if parsed.tzinfo is None:
        return TemporalValue(raw, "INVALID", None, None)
    return TemporalValue(raw, "EVIDENCED", "INSTANT", parsed)


def compare_temporal(left: TemporalValue, right: TemporalValue) -> str:
    """Return ordering only when the represented precision supports it."""
    if left.state != "EVIDENCED" or right.state != "EVIDENCED":
        return "UNPROVEN"
    assert left.instant is not None and right.instant is not None
    left_date = left.instant.date()
    right_date = right.instant.date()
    if left.precision == "DATE" or right.precision == "DATE":
        if left_date < right_date:
            return "BEFORE"
        if left_date > right_date:
            return "AFTER"
        return "INDETERMINATE_SAME_DATE"
    if left.instant < right.instant:
        return "BEFORE"
    if left.instant > right.instant:
        return "AFTER"
    return "EQUAL"


def evaluate_temporal_authority_item(
    *,
    evidence_kind: str,
    evidence_id: str,
    event_time_utc: Any,
    published_or_release_time_utc: Any,
    known_at_or_retrieved_at_utc: Any,
    revision_at_utc: Any,
    historical_replay_cutoff_utc: Any,
    operator_evaluation_cutoff_utc: Any,
    bound_historical_predecessor: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate whether this exact evidence version existed at the replay cutoff."""
    cutoff = parse_temporal_value(historical_replay_cutoff_utc)
    operator_cutoff = parse_temporal_value(operator_evaluation_cutoff_utc)
    values = {
        "event_time": parse_temporal_value(event_time_utc),
        "published_or_release_time": parse_temporal_value(
            published_or_release_time_utc
        ),
        "known_at_or_retrieved_at": parse_temporal_value(
            known_at_or_retrieved_at_utc
        ),
        "revision_at": parse_temporal_value(revision_at_utc),
    }
    blockers: list[str] = []
    unproven: list[str] = []
    if cutoff.state != "EVIDENCED":
        unproven.append("historical_replay_cutoff_unavailable_or_invalid")
    elif cutoff.precision != "INSTANT":
        unproven.append("historical_replay_cutoff_exact_time_unproven")

    source_comparisons: dict[str, str] = {}
    for field in ("event_time", "published_or_release_time"):
        value = values[field]
        comparison = compare_temporal(value, cutoff)
        source_comparisons[field] = comparison
        if value.state == "INVALID":
            unproven.append(f"{field}_invalid")
        elif value.state == "EVIDENCED" and comparison == "AFTER":
            blockers.append(f"{field}_after_historical_replay_cutoff")
        elif value.state == "EVIDENCED" and comparison == "INDETERMINATE_SAME_DATE":
            unproven.append(f"{field}_ordering_unproven_at_available_precision")

    known_value = values["known_at_or_retrieved_at"]
    known_comparison = compare_temporal(known_value, cutoff)
    if known_value.state == "UNEVIDENCED":
        unproven.append("known_at_or_retrieved_at_unavailable_or_unevidenced")
    elif known_value.state == "INVALID":
        unproven.append("known_at_or_retrieved_at_invalid")
    elif known_comparison == "AFTER":
        blockers.append("known_at_or_retrieved_at_after_historical_replay_cutoff")
    elif known_comparison == "INDETERMINATE_SAME_DATE":
        unproven.append("known_at_or_retrieved_at_ordering_unproven_at_available_precision")

    revision_value = values["revision_at"]
    revision_comparison = compare_temporal(revision_value, cutoff)
    predecessor_hash = str(
        (bound_historical_predecessor or {}).get("artifact_hash") or ""
    )
    predecessor_bound = bool(
        re.fullmatch(r"[a-f0-9]{64}", predecessor_hash)
    )
    if bound_historical_predecessor and not predecessor_bound:
        unproven.append("historical_predecessor_binding_invalid")
    if revision_value.state == "INVALID":
        unproven.append("revision_at_invalid")
    elif revision_comparison == "AFTER" and not predecessor_bound:
        blockers.append("FUTURE_REVISION_LEAKAGE_BLOCK")
    elif revision_comparison == "INDETERMINATE_SAME_DATE" and not predecessor_bound:
        unproven.append("revision_ordering_unproven_at_available_precision")

    operator_comparisons = {
        field: compare_temporal(value, operator_cutoff)
        for field, value in values.items()
    }
    if operator_cutoff.state != "EVIDENCED" or operator_cutoff.precision != "INSTANT":
        unproven.append("operator_evaluation_cutoff_exact_time_unproven")
    else:
        for field, comparison in operator_comparisons.items():
            if comparison == "AFTER":
                blockers.append(f"{field}_after_operator_evaluation_cutoff")

    blockers = list(dict.fromkeys(blockers))
    unproven = list(dict.fromkeys(unproven))
    authority_status = "BLOCK" if blockers else "UNPROVEN" if unproven else "PASS"
    core = {
        "schema_version": "contentops.temporal_authority_item.v1",
        "evidence_kind": evidence_kind,
        "evidence_id": evidence_id,
        "result_kind": AUTHORITY_RESULT_KIND,
        "historical_replay_cutoff": cutoff.evidence(),
        "operator_evaluation_cutoff": operator_cutoff.evidence(),
        "temporal_inputs": {
            field: value.evidence() for field, value in values.items()
        },
        "historical_cutoff_comparisons": {
            **source_comparisons,
            "known_at_or_retrieved_at": known_comparison,
            "revision_at": revision_comparison,
        },
        "operator_cutoff_comparisons": operator_comparisons,
        "bound_historical_predecessor": dict(bound_historical_predecessor or {}),
        "point_in_time_authority_status": authority_status,
        "point_in_time_authority_decision": (
            "PASS" if authority_status == "PASS" else "BLOCK"
        ),
        "blockers": blockers,
        "unproven_reasons": unproven,
        "timestamp_invention_or_coercion_performed": False,
    }
    return {**core, "temporal_authority_hash": logical_hash(core)}


def _story_binding(
    packet: Mapping[str, Any],
    outcomes: Sequence[Mapping[str, Any]],
    packages: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
    outcome_matches = [
        row for row in outcomes if row.get("v3_packet_id") == packet.get("packet_id")
    ]
    if len(outcome_matches) != 1:
        raise ValueError("temporal_authority_story_binding_not_exactly_one")
    outcome = outcome_matches[0]
    package_matches = [
        row for row in packages if row.get("story_id") == outcome.get("story_id")
    ]
    if len(package_matches) != 1:
        raise ValueError("temporal_authority_package_binding_not_exactly_one")
    return outcome, package_matches[0]


def build_temporal_authority_records(
    *,
    packets: Sequence[Mapping[str, Any]],
    outcomes: Sequence[Mapping[str, Any]],
    packages: Sequence[Mapping[str, Any]],
    decision_time_records: Sequence[Mapping[str, Any]],
    operator_evaluation_as_of_utc: str,
) -> dict[str, Any]:
    decision_by_story = {str(row["story_id"]): row for row in decision_time_records}
    records: list[dict[str, Any]] = []
    for packet in packets:
        outcome, package = _story_binding(packet, outcomes, packages)
        story_id = str(outcome["story_id"])
        decision_record = decision_by_story[story_id]
        historical_cutoff = packet.get("as_of_utc")
        used_claim_ids = list(outcome.get("article_used_approved_claim_ids") or [])
        all_claims = list((packet.get("governed_claim_graph") or {}).get("claims") or [])
        used_claims = [row for row in all_claims if row.get("claim_id") in used_claim_ids]
        if {str(row.get("claim_id")) for row in used_claims} != set(used_claim_ids):
            raise ValueError("temporal_authority_used_claim_set_mismatch")
        source_documents = list(packet.get("official_source_documents") or [])
        items: list[dict[str, Any]] = []
        for document in source_documents:
            items.append(
                evaluate_temporal_authority_item(
                    evidence_kind="SOURCE_DOCUMENT",
                    evidence_id=str(document.get("document_id") or ""),
                    event_time_utc=document.get("event_time_utc"),
                    published_or_release_time_utc=(
                        document.get("published_at_utc")
                        or document.get("release_time_utc")
                    ),
                    known_at_or_retrieved_at_utc=(
                        document.get("known_at_utc")
                        or document.get("retrieved_at_utc")
                    ),
                    revision_at_utc=document.get("revision_at_utc"),
                    historical_replay_cutoff_utc=historical_cutoff,
                    operator_evaluation_cutoff_utc=operator_evaluation_as_of_utc,
                )
            )
        for claim in used_claims:
            items.append(
                evaluate_temporal_authority_item(
                    evidence_kind="USED_CLAIM",
                    evidence_id=str(claim.get("claim_id") or ""),
                    event_time_utc=claim.get("event_time_utc"),
                    published_or_release_time_utc=(
                        claim.get("published_at_utc") or claim.get("release_time_utc")
                    ),
                    known_at_or_retrieved_at_utc=(
                        claim.get("known_at_utc") or claim.get("retrieved_at_utc")
                    ),
                    revision_at_utc=claim.get("revision_at_utc"),
                    historical_replay_cutoff_utc=historical_cutoff,
                    operator_evaluation_cutoff_utc=operator_evaluation_as_of_utc,
                    bound_historical_predecessor=claim.get(
                        "bound_historical_predecessor"
                    ),
                )
            )
        statuses = [row["point_in_time_authority_status"] for row in items]
        status = "BLOCK" if "BLOCK" in statuses else "UNPROVEN" if "UNPROVEN" in statuses else "PASS"
        authority_blockers = list(
            dict.fromkeys(blocker for row in items for blocker in row["blockers"])
        )
        unproven_reasons = list(
            dict.fromkeys(reason for row in items for reason in row["unproven_reasons"])
        )
        source_replay = decision_record["historical_point_in_time_replay"]
        core = {
            "schema_version": "contentops.story_temporal_authority_record.v1",
            "record_id": f"temporal-authority:{story_id}",
            "story_id": story_id,
            "historical_replay_cutoff_utc": historical_cutoff,
            "operator_evaluation_cutoff_utc": operator_evaluation_as_of_utc,
            "historical_source_time_freshness_replay": {
                "result_kind": SOURCE_TIME_RESULT_KIND,
                "decision": source_replay["decision"],
                "source_age_hours": source_replay["primary_source_age_hours"],
                "blockers": source_replay["blockers"],
                "source_decision_hash": logical_hash(source_replay),
                "does_not_imply_point_in_time_authority": True,
            },
            "point_in_time_authority": {
                "result_kind": AUTHORITY_RESULT_KIND,
                "status": status,
                "decision": "PASS" if status == "PASS" else "BLOCK",
                "blockers": authority_blockers,
                "unproven_reasons": unproven_reasons,
                "used_claim_ids": used_claim_ids,
                "item_records": items,
            },
            "current_operator_readiness": {
                "result_kind": CURRENT_RESULT_KIND,
                "operator_evaluation_as_of_utc": operator_evaluation_as_of_utc,
                "freshness_decision": decision_record["current_operator_readiness"]["decision"],
                "calculated_source_age_hours": decision_record["current_operator_readiness"]["primary_source_age_hours"],
                "CURRENT_OPERATOR_READY": False,
            },
            "hashes": {
                "package_hash": package["package_hash"],
                "article_hash": outcome["canonical_article_hash"],
                "v3_packet_hash": outcome["v3_packet_logical_hash"],
            },
            "canonical_package_evidence_unchanged": True,
            "publication_authority": False,
            "dispatch_authority": False,
            "approval_authority": False,
            "public_write_authority": False,
        }
        authority_hash = logical_hash(core["point_in_time_authority"])
        core["hashes"]["temporal_authority_hash"] = authority_hash
        records.append({**core, "record_hash": logical_hash(core)})
    document_core = {
        "schema_version": "contentops.temporal_authority_records.v1",
        "task": TASK,
        "starting_remote_head": STARTING_REMOTE_HEAD,
        "result_kinds": [SOURCE_TIME_RESULT_KIND, AUTHORITY_RESULT_KIND, CURRENT_RESULT_KIND],
        "operator_evaluation_as_of_utc": operator_evaluation_as_of_utc,
        "record_count": len(records),
        "point_in_time_authority_pass_count": sum(
            row["point_in_time_authority"]["status"] == "PASS" for row in records
        ),
        "records": records,
        "canonical_package_evidence_unchanged": True,
        "publication_authority": False,
        "dispatch_authority": False,
        "approval_authority": False,
        "public_write_authority": False,
        "network_call_performed": False,
        "browser_platform_action_performed": False,
    }
    return {**document_core, "logical_hash": logical_hash(document_core)}


def build_historical_replay_integrity_matrix(
    temporal_records: Mapping[str, Any],
) -> dict[str, Any]:
    rows = []
    for record in temporal_records["records"]:
        authority = record["point_in_time_authority"]
        rows.append(
            {
                "story_id": record["story_id"],
                "historical_source_time_freshness_replay_decision": record[
                    "historical_source_time_freshness_replay"
                ]["decision"],
                "point_in_time_authority_status": authority["status"],
                "point_in_time_authority_decision": authority["decision"],
                "authority_blockers": authority["blockers"],
                "authority_unproven_reasons": authority["unproven_reasons"],
                "current_operator_ready": False,
                "temporal_authority_hash": record["hashes"]["temporal_authority_hash"],
            }
        )
    core = {
        "schema_version": "contentops.historical_replay_integrity_matrix.v1",
        "task": TASK,
        "separation_contract": {
            SOURCE_TIME_RESULT_KIND: "source publication age only",
            AUTHORITY_RESULT_KIND: "exact-version availability and known-at proof",
            CURRENT_RESULT_KIND: "decision-time freshness plus all applicable gates",
        },
        "row_count": len(rows),
        "rows": rows,
        "historical_authority_pass_count": sum(
            row["point_in_time_authority_status"] == "PASS" for row in rows
        ),
        "source_time_pass_does_not_grant_authority": True,
    }
    return {**core, "logical_hash": logical_hash(core)}


def build_current_readiness_parity(
    current_readiness: Mapping[str, Any], temporal_records: Mapping[str, Any]
) -> dict[str, Any]:
    temporal_by_story = {
        row["story_id"]: row for row in temporal_records["records"]
    }
    rows = []
    for record in current_readiness["records"]:
        story_id = record["story_id"]
        hashes = record["hashes"]
        rows.append(
            {
                "story_id": story_id,
                "platform_id": record["current_operator_readiness"]["platform_id"],
                "CURRENT_OPERATOR_READY": record["current_operator_readiness"]["CURRENT_OPERATOR_READY"],
                "canonical_package_state": record["canonical_package_state"],
                "canonical_editorial_state": record["canonical_editorial_state"],
                "market_sensitive": record["current_operator_readiness"]["freshness_decision"]["market_sensitive"],
                "market_snapshot_required": record["current_operator_readiness"]["freshness_decision"]["market_snapshot_required"],
                "supersedes_prior_text_only_operator_ready_receipt": record["supersedes_prior_text_only_operator_ready_receipt"],
                "superseded_prior_receipt_hash": record["superseded_prior_receipt_hash"],
                "package_hash": hashes["package_hash"],
                "article_hash": hashes["article_hash"],
                "v3_packet_hash": hashes["v3_packet_hash"],
                "variant_hash": hashes["variant_hash"],
                "prior_readiness_hash": hashes["readiness_hash"],
                "prior_receipt_hash": record["receipt_hash"],
                "temporal_authority_hash": temporal_by_story[story_id]["hashes"]["temporal_authority_hash"],
                "publication_authority": False,
                "dispatch_authority": False,
                "approval_authority": False,
                "public_write_authority": False,
            }
        )
    core = {
        "schema_version": "contentops.current_readiness_temporal_parity.v1",
        "task": TASK,
        "source_current_readiness_logical_hash": current_readiness["logical_hash"],
        "record_count": len(rows),
        "current_operator_ready_count": sum(row["CURRENT_OPERATOR_READY"] for row in rows),
        "superseded_prior_text_only_receipt_count": sum(
            row["supersedes_prior_text_only_operator_ready_receipt"] for row in rows
        ),
        "records": rows,
        "canonical_package_article_v3_variant_evidence_unchanged": True,
        "publication_authority": False,
        "dispatch_authority": False,
        "approval_authority": False,
        "public_write_authority": False,
    }
    return {**core, "logical_hash": logical_hash(core)}


def generate_temporal_authority_evidence(
    *, repo_root: Path, operator_evaluation_as_of_utc: str
) -> dict[str, dict[str, Any]]:
    source_dir = repo_root / SOURCE_EVIDENCE_RELATIVE
    decision_dir = repo_root / DECISION_TIME_EVIDENCE_RELATIVE
    packets = _read_json(source_dir / "canonical_content_evidence_packets_v3.json")
    outcomes = _read_json(source_dir / "canonical_editorial_outcomes.json")
    packages = _read_json(source_dir / "superseding_unsigned_operator_packages.json")
    decision_time = _read_json(decision_dir / "decision_time_freshness_records.json")
    current_readiness = _read_json(decision_dir / "current_operator_readiness_records.json")
    temporal = build_temporal_authority_records(
        packets=packets["packets"],
        outcomes=outcomes["outcomes"],
        packages=packages["packages"],
        decision_time_records=decision_time["records"],
        operator_evaluation_as_of_utc=operator_evaluation_as_of_utc,
    )
    matrix = build_historical_replay_integrity_matrix(temporal)
    parity = build_current_readiness_parity(current_readiness, temporal)
    output_dir = repo_root / OUTPUT_RELATIVE
    _write_json(output_dir / "temporal_authority_records.json", temporal)
    _write_json(output_dir / "historical_replay_integrity_matrix.json", matrix)
    _write_json(output_dir / "current_readiness_parity.json", parity)
    return {"temporal": temporal, "matrix": matrix, "parity": parity}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--operator-evaluation-as-of-utc", required=True)
    args = parser.parse_args(argv)
    evidence = generate_temporal_authority_evidence(
        repo_root=args.repo_root.resolve(),
        operator_evaluation_as_of_utc=args.operator_evaluation_as_of_utc,
    )
    print(
        json.dumps(
            {
                "record_count": evidence["temporal"]["record_count"],
                "parity_count": evidence["parity"]["record_count"],
                "logical_hash": evidence["temporal"]["logical_hash"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
