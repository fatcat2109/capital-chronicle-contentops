from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from live_contentops.cc_artifact_packet_intake_v0 import load_packet
from live_contentops.cc_artifact_packet_operator_decision_v1 import (
    build_operator_decision_packet,
    evaluate_packet_public_candidate_eligibility,
    load_existing_intake_artifacts,
    write_operator_decision_outputs,
)
from live_contentops.cc_artifact_packet_public_candidate_gate_v1 import (
    PUBLIC_CANDIDATE_ALLOWED_WITH_CAVEATS,
    PUBLIC_CANDIDATE_BLOCKED_BY_PACKET,
    evaluate_public_candidate_gate,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "cc_artifact_packet_v0"
SAMPLE_PATH = FIXTURE_DIR / "sample_internal_draft_packet_v0.json"
OVERRIDE_PATH = FIXTURE_DIR / "invalid_public_override_packet_v0.json"
INTAKE_DIR = ROOT / "docs" / "automation" / "CC_ARTIFACT_PACKET_INTAKE_ADAPTER_V0"


def _packet() -> dict:
    return load_packet(SAMPLE_PATH)


def _artifacts() -> dict:
    return load_existing_intake_artifacts(INTAKE_DIR)


def _decision(operator_go: bool = True) -> dict:
    artifacts = _artifacts()
    return build_operator_decision_packet(
        _packet(),
        artifacts["internal_draft"],
        artifacts["intake_summary"],
        artifacts["rehearsal_intent"],
        approval_hash_file=artifacts["approval_hash_file"],
        operator_go=operator_go,
    )


def test_current_sample_packet_produces_public_ready_false() -> None:
    decision = _decision()
    assert decision["public_ready"] is False
    assert decision["classification"] == "PASS_OPERATOR_DECISION_GATE_BLOCKED_BY_PACKET_ELIGIBILITY"


def test_current_sample_blocks_because_dqr_blocked_candidate_and_internal_only() -> None:
    decision = _decision()
    assert "dqr_status_not_clear:BLOCKED" in decision["blockers"]
    assert "candidate_only_true" in decision["blockers"]
    assert "publish_eligibility_internal_draft_only" in decision["blockers"]


def test_decision_preserves_packet_caveats_and_source_quality() -> None:
    decision = _decision()
    assert "INTERNAL DRAFT USE ONLY. Do not use for live trading or execution." in decision["forbidden_use_notes"]
    assert "DQR status is BLOCKED." in decision["limitations"]
    assert decision["source_quality_status"] == "degraded (success_files=92, active_failures=6)"
    assert decision["claim_ledger"]
    assert decision["numeric_anchors"][0]["caveat"]


def test_approval_hash_continuity_is_checked() -> None:
    decision = _decision()
    assert decision["approval_hash_continuity_status"] == "PASS"
    assert not [b for b in decision["blockers"] if b.startswith("approval_hash_mismatch")]


def test_approval_hash_mismatch_blocks() -> None:
    artifacts = _artifacts()
    internal = copy.deepcopy(artifacts["internal_draft"])
    internal["approval_hash"] = "bad"
    decision = build_operator_decision_packet(
        _packet(),
        internal,
        artifacts["intake_summary"],
        artifacts["rehearsal_intent"],
        approval_hash_file=artifacts["approval_hash_file"],
        operator_go=True,
    )
    assert decision["approval_hash_continuity_status"] == "FAIL"
    assert "approval_hash_mismatch_internal_draft" in decision["blockers"]


def test_missing_intake_summary_blocks() -> None:
    artifacts = _artifacts()
    result = evaluate_packet_public_candidate_eligibility(
        _packet(),
        artifacts["internal_draft"],
        None,
        artifacts["rehearsal_intent"],
        approval_hash_file=artifacts["approval_hash_file"],
        operator_go=True,
    )
    assert "missing_intake_summary" in result["blockers"]


def test_missing_internal_draft_blocks() -> None:
    artifacts = _artifacts()
    result = evaluate_packet_public_candidate_eligibility(
        _packet(),
        None,
        artifacts["intake_summary"],
        artifacts["rehearsal_intent"],
        approval_hash_file=artifacts["approval_hash_file"],
        operator_go=True,
    )
    assert "missing_internal_draft" in result["blockers"]


def test_public_override_attempt_with_dqr_blocked_fails() -> None:
    packet = load_packet(OVERRIDE_PATH)
    artifacts = _artifacts()
    decision = build_operator_decision_packet(
        packet,
        artifacts["internal_draft"],
        artifacts["intake_summary"],
        artifacts["rehearsal_intent"],
        approval_hash_file=artifacts["approval_hash_file"],
        operator_go=True,
    )
    assert decision["public_ready"] is False
    assert "dqr_status_not_clear:BLOCKED" in decision["blockers"]
    assert "candidate_only_true" in decision["blockers"]
    assert "publish_eligibility_manual_review_only_without_public_upgrade_packet" in decision["blockers"]


def test_operator_go_does_not_override_dqr_candidate_or_publish_eligibility() -> None:
    decision = _decision(operator_go=True)
    assert decision["operator_go_received"] is True
    assert decision["operator_go_scope"] == "decision_gate_only_not_dqr_override"
    assert "operator_go_received_for_decision_gate_only_not_dqr_override" in decision["warnings"]
    assert decision["public_ready"] is False


def test_operator_public_override_allows_candidate_commentary_with_caveats() -> None:
    artifacts = _artifacts()
    decision = build_operator_decision_packet(
        _packet(),
        artifacts["internal_draft"],
        artifacts["intake_summary"],
        artifacts["rehearsal_intent"],
        approval_hash_file=artifacts["approval_hash_file"],
        operator_public_override=True,
        public_mode="candidate_commentary",
    )
    assert decision["classification"] == PUBLIC_CANDIDATE_ALLOWED_WITH_CAVEATS
    assert decision["public_ready"] is True
    assert decision["dispatch_allowed_now"] is False
    assert decision["operator_public_override_received"] is True
    assert "dqr_status_not_clear:BLOCKED" in decision["converted_blockers_to_warnings"]
    assert not decision["blockers"]
    assert "Internal candidate analysis / non-authoritative / not financial advice / source caveats apply." in decision["mandatory_disclaimer"]


def test_gate_emits_blocked_by_packet_for_current_sample() -> None:
    gate = evaluate_public_candidate_gate(_decision())
    assert gate["gate_status"] == PUBLIC_CANDIDATE_BLOCKED_BY_PACKET
    assert gate["dispatch_allowed_now"] is False


def test_gate_emits_allowed_with_caveats_for_operator_public_override() -> None:
    artifacts = _artifacts()
    decision = build_operator_decision_packet(
        _packet(),
        artifacts["internal_draft"],
        artifacts["intake_summary"],
        artifacts["rehearsal_intent"],
        approval_hash_file=artifacts["approval_hash_file"],
        operator_public_override=True,
        public_mode="candidate_commentary",
    )
    gate = evaluate_public_candidate_gate(decision)
    assert gate["gate_status"] == PUBLIC_CANDIDATE_ALLOWED_WITH_CAVEATS
    assert gate["public_ready"] is True
    assert gate["dispatch_allowed_now"] is False
    assert gate["requires_separate_live_task"] is True


def test_operator_review_preview_and_outputs_are_generated(tmp_path: Path) -> None:
    result = write_operator_decision_outputs(
        packet=_packet(),
        artifacts=_artifacts(),
        output_dir=tmp_path,
        operator_go=True,
        packet_path=SAMPLE_PATH,
        intake_dir=INTAKE_DIR,
    )
    assert result["gate_packet"]["gate_status"] == PUBLIC_CANDIDATE_BLOCKED_BY_PACKET
    assert (tmp_path / "operator_decision_packet_v1.json").exists()
    assert (tmp_path / "public_candidate_gate_v1.json").exists()
    assert (tmp_path / "operator_review_preview_v1.md").exists()
    assert (tmp_path / "controlled_candidate_rehearsal_envelope_v1.json").exists()
    assert (tmp_path / "decision_evidence_v1.json").exists()
    preview = (tmp_path / "operator_review_preview_v1.md").read_text(encoding="utf-8")
    assert "Jim GO was received" in preview
    assert "DQR status: `BLOCKED`" in preview


def test_operator_public_override_writes_public_preview_artifacts(tmp_path: Path) -> None:
    result = write_operator_decision_outputs(
        packet=_packet(),
        artifacts=_artifacts(),
        output_dir=tmp_path / "decision",
        operator_public_override=True,
        public_mode="candidate_commentary",
        public_preview_output_dir=tmp_path / "public_preview",
        packet_path=SAMPLE_PATH,
        intake_dir=INTAKE_DIR,
    )
    assert result["gate_packet"]["gate_status"] == PUBLIC_CANDIDATE_ALLOWED_WITH_CAVEATS
    assert (tmp_path / "public_preview" / "public_override_decision_v0.json").exists()
    assert (tmp_path / "public_preview" / "candidate_public_preview_v0.md").exists()
    assert (tmp_path / "public_preview" / "candidate_platform_payloads_v0.json").exists()
    assert (tmp_path / "public_preview" / "caveat_disclaimer_block_v0.md").exists()
    assert (tmp_path / "public_preview" / "public_permissive_evidence_v0.json").exists()


def test_cli_writes_outputs_and_exits_zero_for_blocked_packet(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/decide_cc_artifact_public_candidate_v1.py",
            "--intake-dir",
            str(INTAKE_DIR),
            "--packet",
            str(SAMPLE_PATH),
            "--output-dir",
            str(tmp_path),
            "--operator-go",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "gate_status=PUBLIC_CANDIDATE_BLOCKED_BY_PACKET" in result.stdout
    assert "public_dispatch_performed=false" in result.stdout
    assert (tmp_path / "decision_evidence_v1.json").exists()


def test_cli_public_override_writes_preview_artifacts_and_exits_zero(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/decide_cc_artifact_public_candidate_v1.py",
            "--intake-dir",
            str(INTAKE_DIR),
            "--packet",
            str(SAMPLE_PATH),
            "--output-dir",
            str(tmp_path / "decision"),
            "--operator-public-override",
            "--public-mode",
            "candidate_commentary",
            "--public-preview-output-dir",
            str(tmp_path / "public_preview"),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "gate_status=PUBLIC_CANDIDATE_ALLOWED_WITH_CAVEATS" in result.stdout
    assert "public_ready=true" in result.stdout
    assert "public_dispatch_performed=false" in result.stdout
    assert (tmp_path / "public_preview" / "public_permissive_evidence_v0.json").exists()


def test_no_platform_network_env_main_repo_or_source_brain_paths_added() -> None:
    source_paths = [
        ROOT / "live_contentops" / "cc_artifact_packet_operator_decision_v1.py",
        ROOT / "live_contentops" / "cc_artifact_packet_public_candidate_gate_v1.py",
        ROOT / "live_contentops" / "public_permissive_supervised_mode_v0.py",
        ROOT / "scripts" / "decide_cc_artifact_public_candidate_v1.py",
    ]
    forbidden_snippets = [
        "os.environ",
        "load_dotenv",
        "requests",
        "urlopen",
        "socket",
        "playwright",
        "selenium",
        "telegram_live_adapter",
        "substack_browser_adapter",
        "linkedin_browser_adapter",
        "facebook_page_adapter",
        "instagram_adapter",
        "threads_adapter",
        "live_production_pipeline_runner",
        "fetch_fred",
        "fetch_treasury",
        "parse_macro_source",
        "git -C",
    ]
    for path in source_paths:
        text = path.read_text(encoding="utf-8")
        for snippet in forbidden_snippets:
            assert snippet not in text


def test_no_public_dispatch_path_invoked_in_outputs(tmp_path: Path) -> None:
    result = write_operator_decision_outputs(
        packet=_packet(),
        artifacts=_artifacts(),
        output_dir=tmp_path,
        operator_go=True,
        packet_path=SAMPLE_PATH,
        intake_dir=INTAKE_DIR,
    )
    decision = result["decision_packet"]
    assert decision["safety_flags"]["public_dispatch_performed"] is False
    assert decision["safety_flags"]["platform_api_call_performed"] is False
    assert decision["safety_flags"]["network_or_source_fetch_performed"] is False
    assert decision["safety_flags"]["env_credential_session_read_performed"] is False
    assert decision["safety_flags"]["main_repo_write_performed"] is False
    assert decision["contentops_source_brain_added"] is False
