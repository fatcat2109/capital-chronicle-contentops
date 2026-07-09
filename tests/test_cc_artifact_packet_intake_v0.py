from __future__ import annotations

import copy
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from live_contentops.cc_artifact_packet_approval_v0 import build_approval_hash
from live_contentops.cc_artifact_packet_intake_v0 import (
    PacketValidationError,
    intake_packet,
    load_packet,
    load_schema,
    validate_contentops_guards,
    validate_schema,
)
from live_contentops.cc_artifact_packet_render_v0 import render_internal_draft

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "cc_artifact_packet_v0"
SAMPLE_PATH = FIXTURE_DIR / "sample_internal_draft_packet_v0.json"
SCHEMA_PATH = ROOT / "schemas" / "cc_content_artifact_packet_v0.schema.json"


def _sample() -> dict:
    return load_packet(SAMPLE_PATH)


def _schema() -> dict:
    return load_schema(SCHEMA_PATH)


def test_valid_pinned_sample_passes_schema_validation() -> None:
    validate_schema(_sample(), _schema())


def test_valid_pinned_sample_passes_contentops_guards() -> None:
    validate_contentops_guards(_sample())


def test_valid_sample_renders_internal_draft_with_required_caveats() -> None:
    draft = render_internal_draft(_sample())

    assert draft["dqr_warning"].startswith("DQR status is BLOCKED")
    assert "candidate_only=true" in draft["candidate_only_warning"]
    assert "degraded" in draft["source_quality_warning"]
    assert "internal_draft_only" in draft["publish_eligibility_warning"]
    assert draft["source_trail"]
    assert draft["claim_ledger"]
    assert draft["numeric_anchors"][0]["authority_status"] == "candidate"
    assert draft["numeric_anchors"][0]["caveat"]
    assert draft["limitations"]
    assert draft["forbidden_use_notes"]
    assert draft["public_publishable_by_intake_alone"] is False
    assert "NOT PUBLIC-PUBLISHABLE" in draft["explicit_publication_statement"]


@pytest.mark.parametrize(
    ("fixture_name", "expected"),
    [
        ("invalid_hidden_dqr.json", "dqr_status"),
        ("invalid_public_auto.json", "public_auto"),
        ("invalid_candidate_only_false.json", "candidate_only"),
        ("invalid_silent_exact_promotion.json", "silently promotes"),
        ("invalid_missing_forbidden_use_notes.json", "forbidden_use_notes"),
        ("invalid_missing_source_trail.json", "source_trail"),
        ("invalid_missing_claim_ledger.json", "claim_ledger"),
        ("invalid_numeric_anchor_missing_caveat.json", "caveat"),
        ("invalid_numeric_anchor_missing_authority_status.json", "authority_status"),
        ("invalid_mutate_main_repo_instruction.json", "mutate main repo"),
        ("invalid_publish_instruction.json", "publish externally"),
    ],
)
def test_invalid_fixtures_fail_contentops_guards(fixture_name: str, expected: str) -> None:
    packet = load_packet(FIXTURE_DIR / fixture_name)
    with pytest.raises(PacketValidationError, match=expected):
        validate_contentops_guards(packet)


def test_hidden_dqr_fails_schema_validation() -> None:
    packet = load_packet(FIXTURE_DIR / "invalid_hidden_dqr.json")
    with pytest.raises(PacketValidationError, match="schema validation failed"):
        validate_schema(packet, _schema())


def test_public_auto_fails_schema_validation() -> None:
    packet = load_packet(FIXTURE_DIR / "invalid_public_auto.json")
    with pytest.raises(PacketValidationError, match="schema validation failed"):
        validate_schema(packet, _schema())


def test_unsupported_claim_without_forbidden_wording_fails() -> None:
    packet = _sample()
    packet["claim_ledger"][0]["support_status"] = "unsupported"
    packet["claim_ledger"][0]["forbidden_wording"] = []
    with pytest.raises(PacketValidationError, match="forbidden wording"):
        validate_contentops_guards(packet)


def test_approval_hash_changes_when_source_trail_changes() -> None:
    packet = _sample()
    changed = copy.deepcopy(packet)
    changed["source_trail"].append("data/audit/new_source.json")
    assert build_approval_hash(packet) != build_approval_hash(changed)


def test_approval_hash_changes_when_claim_ledger_changes() -> None:
    packet = _sample()
    changed = copy.deepcopy(packet)
    changed["claim_ledger"][0]["allowed_wording"].append("new caveated wording")
    assert build_approval_hash(packet) != build_approval_hash(changed)


def test_approval_hash_changes_when_numeric_anchors_changes() -> None:
    packet = _sample()
    changed = copy.deepcopy(packet)
    changed["numeric_anchors"][0]["value"] = 208425.0
    assert build_approval_hash(packet) != build_approval_hash(changed)


def test_approval_hash_changes_when_forbidden_use_notes_changes() -> None:
    packet = _sample()
    changed = copy.deepcopy(packet)
    changed["forbidden_use_notes"].append("Do not treat candidate values as exact facts.")
    assert build_approval_hash(packet) != build_approval_hash(changed)


def test_intake_packet_writes_deterministic_dry_run_outputs(tmp_path: Path) -> None:
    summary = intake_packet(SAMPLE_PATH, SCHEMA_PATH, tmp_path, dry_run=True)

    assert summary["classification"] == "PASS_WITH_CAVEAT_CONTENTOPS_CC_PACKET_INTAKE_V0"
    assert summary["approval_queue_integration_status"].startswith("caveated")
    assert summary["dry_run_bridge_status"] == "LOCAL_REHEARSAL_INTENT_READY_INTERNAL_REVIEW_ONLY"
    assert summary["public_dispatch_performed"] is False
    assert (tmp_path / "internal_draft_v0.json").exists()
    assert (tmp_path / "intake_dry_run_summary_v0.json").exists()
    assert (tmp_path / "approval_hash_v0.txt").exists()
    assert (tmp_path / "rehearsal_intent_v0.json").exists()

    rehearsal = json.loads((tmp_path / "rehearsal_intent_v0.json").read_text(encoding="utf-8"))
    assert rehearsal["public_ready"] is False
    assert rehearsal["runner_invocation_performed"] is False
    assert "public_dispatch" in rehearsal["blocked_actions"]


def test_cli_dry_run_writes_required_output_files(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/intake_cc_artifact_packet_v0.py",
            "--packet",
            str(SAMPLE_PATH),
            "--schema",
            str(SCHEMA_PATH),
            "--dry-run",
            "--output-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "public_dispatch_performed=false" in result.stdout
    assert (tmp_path / "internal_draft_v0.json").exists()
    assert (tmp_path / "intake_dry_run_summary_v0.json").exists()
    assert (tmp_path / "approval_hash_v0.txt").exists()


def test_cli_invalid_packet_exits_nonzero(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/intake_cc_artifact_packet_v0.py",
            "--packet",
            str(FIXTURE_DIR / "invalid_publish_instruction.json"),
            "--schema",
            str(SCHEMA_PATH),
            "--dry-run",
            "--output-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "publish externally" in result.stderr


def test_new_modules_do_not_import_network_platform_or_env_paths() -> None:
    forbidden_imports = {
        "os",
        "requests",
        "urllib",
        "httpx",
        "socket",
        "subprocess",
        "selenium",
        "playwright",
    }
    module_names = [
        "live_contentops.cc_artifact_packet_intake_v0",
        "live_contentops.cc_artifact_packet_render_v0",
        "live_contentops.cc_artifact_packet_approval_v0",
        "live_contentops.cc_artifact_packet_rehearsal_bridge_v0",
    ]
    for module_name in module_names:
        module = importlib.import_module(module_name)
        imported = set(getattr(module, "__dict__", {}).keys())
        assert forbidden_imports.isdisjoint(imported)


def test_new_modules_do_not_read_secret_or_session_material() -> None:
    source_paths = [
        ROOT / "live_contentops" / "cc_artifact_packet_intake_v0.py",
        ROOT / "live_contentops" / "cc_artifact_packet_render_v0.py",
        ROOT / "live_contentops" / "cc_artifact_packet_approval_v0.py",
        ROOT / "live_contentops" / "cc_artifact_packet_rehearsal_bridge_v0.py",
        ROOT / "scripts" / "intake_cc_artifact_packet_v0.py",
    ]
    forbidden_snippets = [
        "os.environ",
        "load_dotenv",
        ".env",
        "cookie",
        "localStorage",
        "sessionStorage",
        "webhook",
        "provider key",
        "platform_api_client",
        "live_production_pipeline_runner",
    ]
    for path in source_paths:
        text = path.read_text(encoding="utf-8")
        for snippet in forbidden_snippets:
            assert snippet not in text


def test_no_contentops_macro_source_brain_extension_added() -> None:
    source = (ROOT / "live_contentops" / "cc_artifact_packet_intake_v0.py").read_text(encoding="utf-8")
    forbidden_runtime_terms = [
        "fetch_fred",
        "fetch_treasury",
        "fetch_ny_fed",
        "parse_macro_source",
        "requests.get",
        "urlopen",
        "database_write",
    ]
    for term in forbidden_runtime_terms:
        assert term not in source
