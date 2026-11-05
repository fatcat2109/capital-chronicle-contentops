import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.outbox_preparation_gate_from_exact_jim_approval_v6 import *
from live_contentops.exact_jim_approval_declaration_intake_gate_v6 import (
    APPROVAL_MODE as INTAKE_APPROVAL_MODE,
    APPROVAL_SCOPE as INTAKE_APPROVAL_SCOPE,
    EXACT_APPROVAL_PHRASE,
    make_exact_jim_approval_declaration_intake_gate_bundle,
)

SAMPLE_VERIFIER = Path("docs/automation/V6_EXACT_OPERATOR_APPROVAL_SIGNATURE_VERIFIER_SCAFFOLD_HEAVY_BATCH_NO_APPROVAL_NO_SEND/sample_exact_operator_approval_signature_verifier_scaffold_bundle.json")
SAMPLE_INTAKE = Path("docs/automation/V6_EXACT_JIM_APPROVAL_DECLARATION_INTAKE_GATE_HEAVY_BATCH_NO_PROVIDER_NO_LIVE_SEND/sample_exact_jim_approval_declaration_intake_gate_bundle.json")


def _verifier_bundle():
    return json.loads(SAMPLE_VERIFIER.read_text(encoding="utf-8"))


def _default_intake():
    return json.loads(SAMPLE_INTAKE.read_text(encoding="utf-8"))


def _accepted_declaration():
    verifier = _verifier_bundle()
    template = verifier["future_exact_operator_approval_declaration_template"]
    return {
        "schema_version": SCHEMA_VERSION,
        "jim_approval_declaration_id": "synthetic_test_fixture_only_outbox_prep_jim_approval_001",
        "source_exact_operator_approval_signature_verifier_scaffold_bundle_id": verifier["exact_operator_approval_signature_verifier_scaffold_bundle_id"],
        "source_payload_hash_preview_approval_prep_bundle_id": template["source_payload_hash_preview_approval_prep_bundle_id"],
        "operator_id": "jim",
        "created_at_manual": "synthetic_test_fixture_only_manual_timestamp",
        "approval_mode": INTAKE_APPROVAL_MODE,
        "approval_scope": INTAKE_APPROVAL_SCOPE,
        "exact_approval_phrase_required": EXACT_APPROVAL_PHRASE,
        "exact_approval_phrase_provided": EXACT_APPROVAL_PHRASE,
        "approved_payload_preview_ids": ["synthetic_test_fixture_only_preview_001", "synthetic_test_fixture_only_preview_002"],
        "approved_payload_hashes": ["1" * 64, "2" * 64],
        "approved_platforms": ["discord", "telegram"],
        "approval_hash_binding_present": True,
        "payload_hashes_revalidated_now": True,
        "payload_hash_revalidation_report_id": "synthetic_test_fixture_only_revalidation_report_001",
        "destination_binding_present": False,
        "destination_binding_id": None,
        "credential_handle_present": False,
        "credential_handle_id": None,
        "approval_granted_now": True,
        "publication_approved_now": False,
        "outbox_approved_now": False,
        "dispatch_approved_now": False,
        "live_send_approved_now": False,
        "provider_call_requested": False,
        "env_read_requested": False,
        "credential_value_read_requested": False,
        "network_call_requested": False,
        "browser_session_requested": False,
        "executable_request_artifact_requested": False,
        "public_url_requested": False,
        "metrics_requested": False,
        "revocation_supported": True,
        "expires_at": "2099-01-01T00:00:00Z",
        "human_review_required": True,
        "notes": "synthetic_test_fixture_only",
    }


def _accepted_intake():
    return asdict(make_exact_jim_approval_declaration_intake_gate_bundle(_verifier_bundle(), _accepted_declaration()))


def _bundle(intake=None):
    return make_outbox_preparation_gate_bundle(intake or _accepted_intake())


def test_malformed_non_object_json_cli_fails_closed(tmp_path):
    inp = tmp_path / "bad.json"
    out = tmp_path / "out.json"
    inp.write_text("[]", encoding="utf-8")
    assert main(["--exact-jim-approval-intake-gate-bundle", str(inp), "--output", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["eligible_for_future_dispatch_gate_task"] is False
    assert data["eligible_for_live_send_now"] is False


def test_static_no_env_provider_network_browser_request_patterns():
    src = Path("live_contentops/outbox_preparation_gate_from_exact_jim_approval_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$", r"getenv", r"environ", r"dotenv", r"requests", r"urllib", r"httpx", r"webbrowser", r"selenium", r"playwright", r"discord(?:app)?\.com/api/webhooks", r"requests\.post", r"fetch\(", r"curl ", r"Authorization", r"Content-Type", r"\bPOST\b"]:
        assert re.search(pat, src, re.M | re.I) is None, pat


