import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.operator_approval_ledger_gate_scaffold_v6 import *
import live_contentops.operator_approval_ledger_gate_scaffold_v6 as scaffold

SAMPLE_PREP = Path("docs/automation/V6_PAYLOAD_HASH_PREVIEW_AND_APPROVAL_LEDGER_PREP_FROM_DRAFT_INSPECTION_HEAVY_BATCH_NO_PROVIDER_NO_SEND/sample_payload_hash_preview_approval_prep_bundle.json")


def _prep_bundle():
    return json.loads(SAMPLE_PREP.read_text(encoding="utf-8"))


def _bundle(prep_bundle=None):
    return make_operator_approval_ledger_gate_scaffold_bundle(prep_bundle or _prep_bundle())


def test_malformed_non_object_json_cli_fails_closed(tmp_path):
    inp = tmp_path / "bad.json"
    out = tmp_path / "out.json"
    inp.write_text("[]", encoding="utf-8")
    
    assert main(["--payload-hash-prep-bundle", str(inp), "--output", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["eligible_for_future_exact_operator_approval_task"] is False
    assert data["eligible_for_live_send_now"] is False


def test_static_no_env_provider_network_browser_request_patterns():
    src = Path("live_contentops/operator_approval_ledger_gate_scaffold_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$", r"getenv", r"environ", r"dotenv", r"requests", r"urllib", r"httpx", r"webbrowser", r"selenium", r"playwright", r"discord(?:app)?\.com/api/webhooks", r"requests\.post", r"fetch\(", r"curl ", r"Authorization", r"Content-Type", r"\bPOST\b"]:
        assert re.search(pat, src, re.M | re.I) is None, pat


