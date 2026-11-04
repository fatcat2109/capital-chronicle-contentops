import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.exact_operator_approval_signature_verifier_scaffold_v6 import *
import live_contentops.exact_operator_approval_signature_verifier_scaffold_v6 as verifier

SAMPLE_LEDGER = Path("docs/automation/V6_OPERATOR_APPROVAL_LEDGER_GATE_SCAFFOLD_FROM_PAYLOAD_HASH_PREP_HEAVY_BATCH_NO_APPROVAL_NO_SEND/sample_operator_approval_ledger_gate_scaffold_bundle.json")


def _ledger_bundle():
    return json.loads(SAMPLE_LEDGER.read_text(encoding="utf-8"))


def _bundle(source=None):
    return make_exact_operator_approval_signature_verifier_scaffold_bundle(source or _ledger_bundle())


def test_malformed_non_object_json_cli_fails_closed(tmp_path):
    inp = tmp_path / "bad.json"
    out = tmp_path / "out.json"
    inp.write_text("[]", encoding="utf-8")
    assert main(["--operator-approval-ledger-gate-scaffold-bundle", str(inp), "--output", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["eligible_for_future_exact_operator_approval_task"] is False
    assert data["approval_granted_now"] is False
    assert data["eligible_for_live_send_now"] is False


def test_static_no_env_provider_network_browser_request_patterns():
    src = Path("live_contentops/exact_operator_approval_signature_verifier_scaffold_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$", r"getenv", r"environ", r"dotenv", r"requests", r"urllib", r"httpx", r"webbrowser", r"selenium", r"playwright", r"discord(?:app)?\.com/api/webhooks", r"requests\.post", r"fetch\(", r"curl ", r"Authorization", r"Content-Type", r"\bPOST\b"]:
        assert re.search(pat, src, re.M | re.I) is None, pat


