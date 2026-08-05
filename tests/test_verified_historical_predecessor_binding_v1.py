from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import subprocess

import pytest

from live_contentops.temporal_authority_v1 import (
    HISTORICAL_PREDECESSOR_SCHEMA,
    evaluate_temporal_authority_item,
    logical_hash,
    verify_historical_predecessor_binding,
)
from live_contentops.verified_historical_predecessor_evidence_v1 import (
    OUTPUT_RELATIVE,
    STALE_NEXT_ACTION,
    STATUS_PATHS,
    STATUS_RECONCILIATION_COMMIT,
    TASK,
    build_current_parity,
    build_status_reconciliation,
    build_truth_table,
    build_validation_truth,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
OBSERVED_HEAD = "5453b8fa29c5be3cc165efe86fea9e3ee27e7c8b"
PRODUCER_COMMIT = "1548196ebffd2bc7ce82a4ae290211b9c53a45df"
UNREACHABLE_COMMIT = "631ea29c5388d52d4353810b6d8b2a50d677bb44"
ARTIFACT_PATH = "tests/fixtures/multi_story_scoped_reporting_authority_batch_v1.json"
STORY_ID = "fomc-minutes-2026-04-28-29"
CLAIM_ID = "claim-95f6638ac5460d82"
DOCUMENT_ID = "document:fomc-rss-monetary20260520a"
CUTOFF = "2026-07-10T00:00:00Z"


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), *args], text=True
    ).strip()


def _binding(kind: str = "USED_CLAIM") -> dict:
    content = subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "show", f"{PRODUCER_COMMIT}:{ARTIFACT_PATH}"]
    )
    core = {
        "schema_version": HISTORICAL_PREDECESSOR_SCHEMA,
        "repository": "fatcat2109/capital-chronicle-contentops",
        "artifact_path": ARTIFACT_PATH,
        "producer_commit": PRODUCER_COMMIT,
        "git_blob_sha1": _git("rev-parse", f"{PRODUCER_COMMIT}:{ARTIFACT_PATH}"),
        "byte_sha256": __import__("hashlib").sha256(content).hexdigest(),
        "byte_length": len(content),
        "story_id": STORY_ID,
        "evidence_kind": kind,
        "source_document_id": DOCUMENT_ID if kind == "SOURCE_DOCUMENT" else None,
        "claim_id": CLAIM_ID if kind == "USED_CLAIM" else None,
        "known_at_or_retrieved_at_utc": "2026-07-09T18:12:22.866521Z",
        "represented_version_id": "1eec98f094ca3981b7550cdae87cc409e6352e7347f38d689d273aa0bd180d8e",
        "represented_revision_at_utc": "2026-05-20T18:00:00Z",
        "historical_cutoff_utc": CUTOFF,
    }
    return {**core, "logical_hash": logical_hash(core)}


def _rehash(binding: dict) -> dict:
    binding["logical_hash"] = logical_hash(
        {key: value for key, value in binding.items() if key != "logical_hash"}
    )
    return binding


def _verify(binding, *, kind="USED_CLAIM", evidence_id=CLAIM_ID):
    return verify_historical_predecessor_binding(
        bindings=binding,
        repo_root=REPO_ROOT,
        observed_head=OBSERVED_HEAD,
        expected_story_id=STORY_ID,
        expected_evidence_kind=kind,
        expected_evidence_id=evidence_id,
        expected_historical_cutoff_utc=CUTOFF,
    )


def test_exact_committed_claim_and_source_document_bindings_verify_from_bytes():
    for kind, evidence_id in (
        ("USED_CLAIM", CLAIM_ID),
        ("SOURCE_DOCUMENT", DOCUMENT_ID),
    ):
        result = _verify(_binding(kind), kind=kind, evidence_id=evidence_id)
        assert result["verified"] is True
        assert result["verification_method"] == "REPO_NATIVE_GIT_EXACT_BYTES_V1"
        assert result["receipt"]["producer_commit"] == PRODUCER_COMMIT
        assert result["receipt"]["git_blob_sha1"] == "fbb25216d08b5a4c5ca30386cf8f47ed468c1eac"
        assert result["receipt"]["byte_sha256"] == "5bc4ca67c4c149c0f68eeacdcb3899fbd29e3647945723c9ceb955a69ddb5d05"
        assert result["receipt"]["byte_length"] == 16646


def test_verified_predecessor_not_hash_shape_suppresses_future_revision_leakage():
    result = evaluate_temporal_authority_item(
        evidence_kind="USED_CLAIM",
        evidence_id=CLAIM_ID,
        story_id=STORY_ID,
        event_time_utc="2026-05-20T18:00:00Z",
        published_or_release_time_utc="2026-05-20T18:00:00Z",
        known_at_or_retrieved_at_utc="2026-07-09T18:12:22.866521Z",
        revision_at_utc="2026-07-11T00:00:00Z",
        historical_replay_cutoff_utc=CUTOFF,
        operator_evaluation_cutoff_utc="2026-08-01T00:00:00Z",
        bound_historical_predecessor=_binding(),
        historical_predecessor_repo_root=REPO_ROOT,
        historical_predecessor_observed_head=OBSERVED_HEAD,
    )
    assert result["point_in_time_authority_status"] == "PASS"
    assert "FUTURE_REVISION_LEAKAGE_BLOCK" not in result["blockers"]
    assert result["historical_predecessor_verification"]["verified"] is True


@pytest.mark.parametrize("value", [{"artifact_hash": "abc"}, {"artifact_hash": "a" * 64}])
def test_bare_and_random_hashes_never_verify_or_suppress_leakage(value):
    result = evaluate_temporal_authority_item(
        evidence_kind="USED_CLAIM",
        evidence_id=CLAIM_ID,
        story_id=STORY_ID,
        event_time_utc="2026-05-20T18:00:00Z",
        published_or_release_time_utc="2026-05-20T18:00:00Z",
        known_at_or_retrieved_at_utc="2026-07-09T18:12:22.866521Z",
        revision_at_utc="2026-07-11T00:00:00Z",
        historical_replay_cutoff_utc=CUTOFF,
        operator_evaluation_cutoff_utc="2026-08-01T00:00:00Z",
        bound_historical_predecessor=value,
        historical_predecessor_repo_root=REPO_ROOT,
        historical_predecessor_observed_head=OBSERVED_HEAD,
    )
    assert result["point_in_time_authority_status"] == "BLOCK"
    assert "FUTURE_REVISION_LEAKAGE_BLOCK" in result["blockers"]
    assert result["historical_predecessor_verification"]["verified"] is False


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("repository", "someone/example", "repository_mismatch"),
        ("artifact_path", "tests/fixtures/missing-predecessor.json", "committed_artifact_unverified"),
        ("producer_commit", OBSERVED_HEAD, "producer_commit_not_artifact_version_commit"),
        ("producer_commit", UNREACHABLE_COMMIT, "committed_artifact_unverified"),
        ("git_blob_sha1", "0" * 40, "git_receipt_git_blob_sha1_mismatch"),
        ("byte_sha256", "0" * 64, "git_receipt_byte_sha256_mismatch"),
        ("byte_length", 1, "git_receipt_byte_length_mismatch"),
        ("story_id", "wrong-story", "story_id_mismatch"),
        ("evidence_kind", "SOURCE_DOCUMENT", "evidence_kind_mismatch"),
        ("claim_id", "claim-wrong", "claim_id_mismatch"),
        ("known_at_or_retrieved_at_utc", "2026-07-11T00:00:00Z", "known_at_after_cutoff"),
        ("represented_revision_at_utc", "2026-07-11T00:00:00Z", "revision_after_cutoff"),
    ],
)
def test_claim_binding_mismatches_fail_closed(field, value, reason):
    binding = deepcopy(_binding())
    binding[field] = value
    _rehash(binding)
    result = _verify(binding)
    assert result["verified"] is False
    assert any(reason in item for item in result["failure_reasons"])


def test_wrong_source_document_id_fails_closed():
    binding = _binding("SOURCE_DOCUMENT")
    binding["source_document_id"] = "document:wrong"
    _rehash(binding)
    result = _verify(binding, kind="SOURCE_DOCUMENT", evidence_id=DOCUMENT_ID)
    assert result["verified"] is False
    assert "historical_predecessor_source_document_id_mismatch" in result["failure_reasons"]


def test_malformed_logical_hash_duplicate_and_unverified_bytes_fail_closed():
    malformed = _binding()
    malformed["logical_hash"] = "f" * 64
    assert "historical_predecessor_binding_logical_hash_mismatch" in _verify(malformed)["failure_reasons"]

    duplicate = _binding()
    duplicate_result = _verify([duplicate, deepcopy(duplicate)])
    assert duplicate_result["verified"] is False
    assert duplicate_result["failure_reasons"] == ["historical_predecessor_binding_duplicate"]

    unverified = _binding()
    unverified["artifact_path"] = "tests/fixtures/never-committed-predecessor.json"
    _rehash(unverified)
    unverified_result = _verify(unverified)
    assert unverified_result["verified"] is False
    assert any("committed_artifact_unverified" in item for item in unverified_result["failure_reasons"])

    malformed_type = evaluate_temporal_authority_item(
        evidence_kind="USED_CLAIM",
        evidence_id=CLAIM_ID,
        story_id=STORY_ID,
        event_time_utc="2026-05-20T18:00:00Z",
        published_or_release_time_utc="2026-05-20T18:00:00Z",
        known_at_or_retrieved_at_utc="2026-07-09T18:12:22.866521Z",
        revision_at_utc="2026-07-11T00:00:00Z",
        historical_replay_cutoff_utc=CUTOFF,
        operator_evaluation_cutoff_utc="2026-08-01T00:00:00Z",
        bound_historical_predecessor="not-a-binding",  # type: ignore[arg-type]
        historical_predecessor_repo_root=REPO_ROOT,
        historical_predecessor_observed_head=OBSERVED_HEAD,
    )
    assert malformed_type["point_in_time_authority_status"] == "BLOCK"
    assert "FUTURE_REVISION_LEAKAGE_BLOCK" in malformed_type["blockers"]
    assert "historical_predecessor_binding_malformed" in malformed_type["unproven_reasons"]


def test_committed_evidence_replays_and_all_logical_and_artifact_hashes_verify():
    expected = {
        "predecessor_binding_truth_table.json": build_truth_table(REPO_ROOT),
        "current_temporal_parity.json": build_current_parity(REPO_ROOT),
        "status_authority_reconciliation.json": build_status_reconciliation(REPO_ROOT),
        "validation_truth.json": build_validation_truth(),
    }
    for filename, rebuilt in expected.items():
        committed = __import__("json").loads(
            (REPO_ROOT / OUTPUT_RELATIVE / filename).read_text(encoding="utf-8")
        )
        assert committed == rebuilt
        assert committed["logical_hash"] == logical_hash(
            {key: value for key, value in committed.items() if key != "logical_hash"}
        )
    manifest = __import__("json").loads(
        (REPO_ROOT / OUTPUT_RELATIVE / "final_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["logical_hash"] == logical_hash(
        {key: value for key, value in manifest.items() if key != "logical_hash"}
    )
    for artifact in manifest["generated_artifacts"]:
        content = (REPO_ROOT / artifact["path"]).read_bytes()
        assert artifact["byte_sha256"] == __import__("hashlib").sha256(content).hexdigest()
        assert artifact["byte_length"] == len(content)


def test_status_authority_has_one_current_pointer_and_no_stale_decision_time_pointer():
    # This record is a closeout snapshot: it describes status authority as of the commit that
    # produced it, not as of today. Current status docs have legitimately moved on since.
    reconciliation = build_status_reconciliation(REPO_ROOT)
    assert reconciliation["all_status_files_consistent"] is True
    assert all(not row["stale_pointer_present"] for row in reconciliation["rows"])
    assert reconciliation["json_sha_roles"]["task_starting_sha"] == OBSERVED_HEAD
    assert reconciliation["json_sha_roles"]["final_sha_reported_after_commit"] is None


def test_status_reconciliation_is_pinned_to_producer_commit_not_current_worktree():
    # The pin must stay reachable or the historical record becomes unreplayable.
    subprocess.check_call(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "merge-base",
            "--is-ancestor",
            STATUS_RECONCILIATION_COMMIT,
            "HEAD",
        ]
    )

    built = build_status_reconciliation(REPO_ROOT)
    pinned_rows = {}
    worktree_rows = {}
    for relative in STATUS_PATHS:
        pinned = subprocess.check_output(
            ["git", "-C", str(REPO_ROOT), "show", f"{STATUS_RECONCILIATION_COMMIT}:{relative}"]
        ).decode("utf-8")
        current = (REPO_ROOT / relative).read_text(encoding="utf-8")
        pinned_rows[relative] = (TASK in pinned, STALE_NEXT_ACTION in pinned)
        worktree_rows[relative] = (TASK in current, STALE_NEXT_ACTION in current)

    for row in built["rows"]:
        expected_task_present, expected_stale = pinned_rows[row["path"]]
        assert row["completed_task_present"] is expected_task_present
        assert row["stale_pointer_present"] is expected_stale

    # Guard against a vacuous pass: if the worktree ever agreed with the pin, this test could
    # not distinguish a pinned read from a worktree read.
    assert pinned_rows != worktree_rows, (
        "worktree matches the pinned commit, so this regression test cannot prove pinning"
    )


def test_status_reconciliation_refuses_to_fall_back_when_pin_is_unreachable(monkeypatch):
    module = __import__(
        "live_contentops.verified_historical_predecessor_evidence_v1",
        fromlist=["STATUS_RECONCILIATION_COMMIT"],
    )
    monkeypatch.setattr(module, "STATUS_RECONCILIATION_COMMIT", UNREACHABLE_COMMIT)
    with pytest.raises(RuntimeError, match="unreachable"):
        build_status_reconciliation(REPO_ROOT)
