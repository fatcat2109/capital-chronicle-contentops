from __future__ import annotations

import copy
import json
from pathlib import Path

from live_contentops.cc_artifact_packet_intake_v0 import load_packet
from live_contentops.cc_artifact_packet_operator_decision_v1 import (
    evaluate_packet_public_candidate_eligibility,
    load_existing_intake_artifacts,
)
from live_contentops.public_permissive_supervised_mode_v0 import (
    MANDATORY_DISCLAIMER,
    PUBLIC_CANDIDATE_ALLOWED_WITH_CAVEATS,
    PUBLIC_CANDIDATE_OVERRIDE_BLOCKED,
    build_candidate_platform_payloads,
    build_candidate_public_preview,
    build_caveat_disclaimer_block,
    build_public_override_decision,
    candidate_topic_hash,
    evaluate_duplicate_guard,
    validate_public_candidate_materials,
    write_public_permissive_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "cc_artifact_packet_v0"
SAMPLE_PATH = FIXTURE_DIR / "sample_internal_draft_packet_v0.json"
INTAKE_DIR = ROOT / "docs" / "automation" / "CC_ARTIFACT_PACKET_INTAKE_ADAPTER_V0"


def _packet() -> dict:
    return load_packet(SAMPLE_PATH)


def _base_eligibility(packet: dict | None = None) -> dict:
    artifacts = load_existing_intake_artifacts(INTAKE_DIR)
    return evaluate_packet_public_candidate_eligibility(
        packet or _packet(),
        artifacts["internal_draft"],
        artifacts["intake_summary"],
        artifacts["rehearsal_intent"],
        approval_hash_file=artifacts["approval_hash_file"],
        operator_go=True,
    )


def _override(packet: dict | None = None, **kwargs) -> dict:
    pkt = packet or _packet()
    return build_public_override_decision(
        packet=pkt,
        base_eligibility=_base_eligibility(pkt),
        operator_public_override=kwargs.pop("operator_public_override", True),
        public_mode=kwargs.pop("public_mode", "candidate_commentary"),
        **kwargs,
    )


def test_override_allows_sample_as_candidate_commentary() -> None:
    decision = _override()
    assert decision["classification"] == PUBLIC_CANDIDATE_ALLOWED_WITH_CAVEATS
    assert decision["public_ready"] is True
    assert decision["dispatch_allowed_now"] is False
    assert decision["operator_public_override_received"] is True
    assert decision["duplicate_guard"]["status"] == "PASS_DETERMINISTIC_NO_DUPLICATE"


def test_missing_operator_override_blocks() -> None:
    decision = _override(operator_public_override=False)
    assert decision["classification"] == PUBLIC_CANDIDATE_OVERRIDE_BLOCKED
    assert "operator_public_override_missing" in decision["hard_blockers"]
    assert decision["public_ready"] is False


def test_mandatory_disclaimer_and_candidate_labels_are_visible() -> None:
    decision = _override()
    preview = decision["candidate_public_preview_markdown"]
    payload_blob = json.dumps(decision["candidate_platform_payloads"], sort_keys=True)
    assert MANDATORY_DISCLAIMER in preview
    assert MANDATORY_DISCLAIMER in payload_blob
    assert "Candidate/proxy non-authoritative value" in preview
    assert "DQR status: BLOCKED" in preview
    assert "Internal candidate analysis" in preview


def test_internal_only_caveat_is_transformed_not_hidden() -> None:
    disclaimer = build_caveat_disclaimer_block(_packet())
    assert MANDATORY_DISCLAIMER in disclaimer
    assert "Preserved source caveat: INTERNAL DRAFT USE ONLY" in disclaimer
    assert "DQR status remains BLOCKED" in disclaimer


def test_no_exact_authority_promotion_or_trading_advice() -> None:
    decision = _override()
    validation = decision["material_validation"]
    assert validation["status"] == "PASS"
    assert validation["exact_authority_promotion_detected"] is False
    assert validation["trading_advice_detected"] is False


def test_approval_hash_continuity_is_required() -> None:
    base = copy.deepcopy(_base_eligibility())
    base["approval_hash_continuity_status"] = "FAIL"
    base["blockers"].append("approval_hash_mismatch_file")
    decision = build_public_override_decision(
        packet=_packet(),
        base_eligibility=base,
        operator_public_override=True,
        public_mode="candidate_commentary",
    )
    assert decision["classification"] == PUBLIC_CANDIDATE_OVERRIDE_BLOCKED
    assert "approval_hash_continuity_not_pass" in decision["hard_blockers"]
    assert "approval_hash_mismatch_file" in decision["hard_blockers"]


def test_duplicate_failure_still_blocks() -> None:
    packet = _packet()
    payloads = build_candidate_platform_payloads(packet, approval_hash=_base_eligibility(packet)["approval_hash"])
    duplicate_rows = [
        {
            "record_type": "public_candidate",
            "topic_hash": candidate_topic_hash(packet),
            "payload_hash": payloads["payload_hash"],
        }
    ]
    guard = evaluate_duplicate_guard(packet, payloads, duplicate_ledger_rows=duplicate_rows)
    assert guard["status"] == "BLOCKED_DUPLICATE_DETECTED"
    decision = _override(duplicate_ledger_rows=duplicate_rows)
    assert decision["classification"] == PUBLIC_CANDIDATE_OVERRIDE_BLOCKED
    assert "duplicate_topic_hash" in decision["hard_blockers"]


def test_public_material_validation_blocks_exact_authority_claim() -> None:
    packet = _packet()
    disclaimer = build_caveat_disclaimer_block(packet)
    payloads = build_candidate_platform_payloads(packet, approval_hash=_base_eligibility(packet)["approval_hash"])
    validation = validate_public_candidate_materials(
        packet=packet,
        preview_markdown=build_candidate_public_preview(packet) + "\nDQR cleared for production active use.",
        payload_bundle=payloads,
        disclaimer_block=disclaimer,
    )
    assert validation["status"] == "BLOCKED"
    assert "exact_authority_promotion_detected" in validation["hard_blockers"]


def test_write_public_permissive_artifacts(tmp_path: Path) -> None:
    paths = write_public_permissive_artifacts(_override(), output_dir=tmp_path)
    for path in paths.values():
        assert path.exists()
    evidence = json.loads((tmp_path / "public_permissive_evidence_v0.json").read_text(encoding="utf-8"))
    assert evidence["classification"] == PUBLIC_CANDIDATE_ALLOWED_WITH_CAVEATS
    assert evidence["safety"]["public_dispatch_performed"] is False
    assert evidence["safety"]["platform_api_call_performed"] is False
    assert evidence["safety"]["env_credential_session_read_performed"] is False
    assert evidence["safety"]["main_repo_write_performed"] is False


def test_no_forbidden_runtime_paths_in_module() -> None:
    text = (ROOT / "live_contentops" / "public_permissive_supervised_mode_v0.py").read_text(encoding="utf-8")
    forbidden = [
        "os.environ",
        "os.getenv",
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
    ]
    for snippet in forbidden:
        assert snippet not in text
