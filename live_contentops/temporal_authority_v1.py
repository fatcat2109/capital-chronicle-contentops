"""Fail-closed point-in-time authority evaluation for governed story evidence."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping, Sequence

from live_contentops.governed_upstream_bridge_v1 import (
    GovernedArtifactBlocked,
    read_git_artifact,
)
from live_contentops.universal_evidence_receipt_verifier_v1 import (
    EvidenceReceiptVerificationError,
    verify_repository_origin,
)


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
HISTORICAL_PREDECESSOR_SCHEMA = (
    "contentops.verified_historical_predecessor_binding.v1"
)
PRIMARY_REPOSITORY = "fatcat2109/capital-chronicle-contentops"
PRIMARY_BRANCH = "master"
PREDECESSOR_REQUIRED_FIELDS = {
    "schema_version",
    "repository",
    "artifact_path",
    "producer_commit",
    "git_blob_sha1",
    "byte_sha256",
    "byte_length",
    "story_id",
    "evidence_kind",
    "source_document_id",
    "claim_id",
    "known_at_or_retrieved_at_utc",
    "represented_version_id",
    "represented_revision_at_utc",
    "historical_cutoff_utc",
    "logical_hash",
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


def _normalize_predecessor_bindings(
    value: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
) -> tuple[list[Mapping[str, Any]], list[str]]:
    if value is None:
        return [], []
    if isinstance(value, Mapping):
        return [value], []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return [], ["historical_predecessor_binding_malformed"]
    bindings = list(value)
    if not bindings or not all(isinstance(row, Mapping) for row in bindings):
        return [], ["historical_predecessor_binding_malformed"]
    logical_hashes = [str(row.get("logical_hash") or "") for row in bindings]
    if len(logical_hashes) != len(set(logical_hashes)):
        return bindings, ["historical_predecessor_binding_duplicate"]
    if len(bindings) != 1:
        return bindings, ["historical_predecessor_binding_not_exactly_one"]
    return bindings, []


def _predecessor_evidence_value(value: Any) -> Any:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes))
        and all(isinstance(row, Mapping) for row in value)
    ):
        return [dict(row) for row in value]
    return {"malformed_binding_type": type(value).__name__}


def _artifact_story(
    artifact: Mapping[str, Any], story_id: str
) -> tuple[Mapping[str, Any] | None, str | None]:
    stories = artifact.get("stories")
    if not isinstance(stories, list):
        return None, "historical_predecessor_artifact_story_collection_missing"
    matches = [
        row for row in stories
        if isinstance(row, Mapping) and str(row.get("story_id") or "") == story_id
    ]
    if len(matches) != 1:
        return None, "historical_predecessor_story_identity_not_exactly_one"
    return matches[0], None


def verify_historical_predecessor_binding(
    *,
    bindings: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
    repo_root: Path | None,
    observed_head: str | None,
    expected_story_id: str,
    expected_evidence_kind: str,
    expected_evidence_id: str,
    expected_historical_cutoff_utc: Any,
) -> dict[str, Any]:
    """Verify a temporal predecessor from exact reachable committed bytes."""
    normalized, failures = _normalize_predecessor_bindings(bindings)
    if not normalized:
        return {
            "verified": False,
            "failure_reasons": failures or ["historical_predecessor_binding_absent"],
        }
    if failures:
        return {"verified": False, "failure_reasons": failures}
    binding = dict(normalized[0])
    missing = sorted(PREDECESSOR_REQUIRED_FIELDS - set(binding))
    if missing:
        return {
            "verified": False,
            "failure_reasons": [
                "historical_predecessor_binding_missing_fields:" + ",".join(missing)
            ],
        }
    failures = []
    if set(binding) != PREDECESSOR_REQUIRED_FIELDS:
        failures.append("historical_predecessor_binding_unrecognized_fields")
    binding_core = {
        key: value for key, value in binding.items() if key != "logical_hash"
    }
    if binding.get("logical_hash") != logical_hash(binding_core):
        failures.append("historical_predecessor_binding_logical_hash_mismatch")
    if binding.get("schema_version") != HISTORICAL_PREDECESSOR_SCHEMA:
        failures.append("historical_predecessor_binding_schema_mismatch")
    if binding.get("repository") != PRIMARY_REPOSITORY:
        failures.append("historical_predecessor_repository_mismatch")
    artifact_path = str(binding.get("artifact_path") or "")
    path_parts = Path(artifact_path).parts
    if (
        not artifact_path
        or Path(artifact_path).is_absolute()
        or ".." in path_parts
        or "\\" in artifact_path
    ):
        failures.append("historical_predecessor_artifact_path_malformed")
    producer_commit = str(binding.get("producer_commit") or "")
    if not re.fullmatch(r"[a-f0-9]{40}", producer_commit):
        failures.append("historical_predecessor_producer_commit_malformed")
    if not re.fullmatch(r"[a-f0-9]{40}", str(binding.get("git_blob_sha1") or "")):
        failures.append("historical_predecessor_git_blob_malformed")
    if not re.fullmatch(r"[a-f0-9]{64}", str(binding.get("byte_sha256") or "")):
        failures.append("historical_predecessor_byte_sha256_malformed")
    if not isinstance(binding.get("byte_length"), int) or binding["byte_length"] < 0:
        failures.append("historical_predecessor_byte_length_malformed")
    if binding.get("story_id") != expected_story_id:
        failures.append("historical_predecessor_story_id_mismatch")
    if binding.get("evidence_kind") != expected_evidence_kind:
        failures.append("historical_predecessor_evidence_kind_mismatch")
    if expected_evidence_kind == "SOURCE_DOCUMENT":
        if binding.get("source_document_id") != expected_evidence_id:
            failures.append("historical_predecessor_source_document_id_mismatch")
        if binding.get("claim_id") is not None:
            failures.append("historical_predecessor_claim_id_must_be_null")
    elif expected_evidence_kind == "USED_CLAIM":
        if binding.get("claim_id") != expected_evidence_id:
            failures.append("historical_predecessor_claim_id_mismatch")
        if binding.get("source_document_id") is not None:
            failures.append("historical_predecessor_source_document_id_must_be_null")
    else:
        failures.append("historical_predecessor_evidence_kind_unsupported")
    expected_cutoff = parse_temporal_value(expected_historical_cutoff_utc)
    binding_cutoff = parse_temporal_value(binding.get("historical_cutoff_utc"))
    if (
        expected_cutoff.state != "EVIDENCED"
        or expected_cutoff.precision != "INSTANT"
        or binding_cutoff.state != "EVIDENCED"
        or binding_cutoff.precision != "INSTANT"
        or compare_temporal(binding_cutoff, expected_cutoff) != "EQUAL"
    ):
        failures.append("historical_predecessor_cutoff_mismatch_or_unproven")
    if repo_root is None or not observed_head:
        failures.append("historical_predecessor_verification_context_missing")
    if failures:
        return {"verified": False, "failure_reasons": list(dict.fromkeys(failures))}
    assert repo_root is not None and observed_head is not None
    try:
        verify_repository_origin(repo_root.resolve(), PRIMARY_REPOSITORY)
        content, receipt = read_git_artifact(
            root=repo_root.resolve(),
            observed_head=observed_head,
            artifact_path=artifact_path,
            producer_commit=producer_commit,
            repository=PRIMARY_REPOSITORY,
            branch=PRIMARY_BRANCH,
        )
    except (GovernedArtifactBlocked, EvidenceReceiptVerificationError, OSError) as error:
        return {
            "verified": False,
            "failure_reasons": [
                "historical_predecessor_committed_artifact_unverified:"
                + str(error)
            ],
        }
    receipt_fields = receipt.as_dict()
    try:
        artifact_version_commit = subprocess.check_output(
            [
                "git",
                "-C",
                str(repo_root.resolve()),
                "log",
                "-1",
                "--format=%H",
                observed_head,
                "--",
                artifact_path,
            ],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        artifact_version_commit = ""
    if producer_commit != artifact_version_commit:
        failures.append("historical_predecessor_producer_commit_not_artifact_version_commit")
    for field in (
        "repository",
        "artifact_path",
        "producer_commit",
        "git_blob_sha1",
        "byte_sha256",
        "byte_length",
    ):
        if binding.get(field) != receipt_fields.get(field):
            failures.append(f"historical_predecessor_git_receipt_{field}_mismatch")
    try:
        artifact = json.loads(content)
    except json.JSONDecodeError:
        failures.append("historical_predecessor_committed_json_malformed")
        artifact = {}
    if not isinstance(artifact, Mapping):
        failures.append("historical_predecessor_committed_json_root_invalid")
        artifact = {}
    story, story_failure = _artifact_story(artifact, expected_story_id)
    if story_failure:
        failures.append(story_failure)
    if story is not None:
        timestamps = story.get("timestamps") or {}
        artifact_known_at = timestamps.get("known_at")
        artifact_revision_at = timestamps.get("provider_updated_at")
        if binding.get("known_at_or_retrieved_at_utc") != artifact_known_at:
            failures.append("historical_predecessor_known_at_artifact_mismatch")
        if binding.get("represented_version_id") != story.get("version_id"):
            failures.append("historical_predecessor_version_id_artifact_mismatch")
        if binding.get("represented_revision_at_utc") != artifact_revision_at:
            failures.append("historical_predecessor_revision_artifact_mismatch")
        if expected_evidence_kind == "SOURCE_DOCUMENT":
            artifact_document_id = "document:" + str(story.get("provider_record_id") or "")
            if binding.get("source_document_id") != artifact_document_id:
                failures.append("historical_predecessor_source_document_artifact_mismatch")
        elif expected_evidence_kind == "USED_CLAIM":
            claims = story.get("claims") or []
            claim_matches = [
                row for row in claims
                if isinstance(row, Mapping)
                and row.get("claim_id") == binding.get("claim_id")
            ]
            if len(claim_matches) != 1:
                failures.append("historical_predecessor_claim_artifact_not_exactly_one")
    known_value = parse_temporal_value(binding.get("known_at_or_retrieved_at_utc"))
    revision_value = parse_temporal_value(binding.get("represented_revision_at_utc"))
    for label, value in (("known_at", known_value), ("revision", revision_value)):
        comparison = compare_temporal(value, binding_cutoff)
        if value.state != "EVIDENCED" or value.precision != "INSTANT":
            failures.append(f"historical_predecessor_{label}_unproven")
        elif comparison == "AFTER":
            failures.append(f"historical_predecessor_{label}_after_cutoff")
        elif comparison == "INDETERMINATE_SAME_DATE":
            failures.append(f"historical_predecessor_{label}_ordering_unproven")
    if failures:
        return {"verified": False, "failure_reasons": list(dict.fromkeys(failures))}
    verification_core = {
        "verified": True,
        "verification_method": "REPO_NATIVE_GIT_EXACT_BYTES_V1",
        "receipt": receipt_fields,
        "story_id": expected_story_id,
        "evidence_kind": expected_evidence_kind,
        "evidence_id": expected_evidence_id,
        "known_at_or_retrieved_at_utc": binding["known_at_or_retrieved_at_utc"],
        "represented_version_id": binding["represented_version_id"],
        "represented_revision_at_utc": binding["represented_revision_at_utc"],
        "historical_cutoff_utc": binding["historical_cutoff_utc"],
        "binding_logical_hash": binding["logical_hash"],
    }
    return {**verification_core, "verification_hash": logical_hash(verification_core)}


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
    bound_historical_predecessor: (
        Mapping[str, Any] | Sequence[Mapping[str, Any]] | None
    ) = None,
    historical_predecessor_repo_root: Path | None = None,
    historical_predecessor_observed_head: str | None = None,
    story_id: str | None = None,
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
    predecessor_verification: dict[str, Any] | None = None
    predecessor_bound = False
    if bound_historical_predecessor is not None:
        predecessor_verification = verify_historical_predecessor_binding(
            bindings=bound_historical_predecessor,
            repo_root=historical_predecessor_repo_root,
            observed_head=historical_predecessor_observed_head,
            expected_story_id=str(story_id or ""),
            expected_evidence_kind=evidence_kind,
            expected_evidence_id=evidence_id,
            expected_historical_cutoff_utc=historical_replay_cutoff_utc,
        )
        predecessor_bound = predecessor_verification["verified"] is True
        if not predecessor_bound:
            unproven.extend(predecessor_verification["failure_reasons"])
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
        "bound_historical_predecessor": _predecessor_evidence_value(
            bound_historical_predecessor
        ),
        "point_in_time_authority_status": authority_status,
        "point_in_time_authority_decision": (
            "PASS" if authority_status == "PASS" else "BLOCK"
        ),
        "blockers": blockers,
        "unproven_reasons": unproven,
        "timestamp_invention_or_coercion_performed": False,
    }
    if predecessor_verification is not None:
        core["historical_predecessor_verification"] = predecessor_verification
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
    historical_predecessor_repo_root: Path | None = None,
    historical_predecessor_observed_head: str | None = None,
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
                    historical_predecessor_repo_root=historical_predecessor_repo_root,
                    historical_predecessor_observed_head=historical_predecessor_observed_head,
                    story_id=story_id,
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
                    historical_predecessor_repo_root=historical_predecessor_repo_root,
                    historical_predecessor_observed_head=historical_predecessor_observed_head,
                    story_id=story_id,
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
    observed_head = subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        stderr=subprocess.DEVNULL,
        text=True,
    ).strip()
    temporal = build_temporal_authority_records(
        packets=packets["packets"],
        outcomes=outcomes["outcomes"],
        packages=packages["packages"],
        decision_time_records=decision_time["records"],
        operator_evaluation_as_of_utc=operator_evaluation_as_of_utc,
        historical_predecessor_repo_root=repo_root,
        historical_predecessor_observed_head=observed_head,
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
