import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.dispatch_gate_scaffold_from_prepared_outbox_v6 import *
from live_contentops.outbox_preparation_gate_from_exact_jim_approval_v6 import make_outbox_preparation_gate_bundle
from tests.test_outbox_preparation_gate_from_exact_jim_approval_v6 import _accepted_intake

SAMPLE_OUTBOX = Path("docs/automation/V6_OUTBOX_PREPARATION_GATE_FROM_EXACT_JIM_APPROVAL_INTAKE_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_outbox_preparation_gate_bundle.json")


def _default_outbox():
    return json.loads(SAMPLE_OUTBOX.read_text(encoding="utf-8"))


def _accepted_outbox():
    data = asdict(make_outbox_preparation_gate_bundle(_accepted_intake()))
    data["warnings"].append("synthetic_test_fixture_only")
    return data


def _bundle(outbox=None):
    return make_dispatch_gate_scaffold_bundle(outbox or _accepted_outbox())


def test_malformed_non_object_json_cli_fails_closed(tmp_path):
    inp = tmp_path / "bad.json"
    out = tmp_path / "out.json"
    inp.write_text("[]", encoding="utf-8")
    assert main(["--outbox-preparation-gate-bundle", str(inp), "--output", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["eligible_for_future_destination_binding_task"] is False
    assert data["eligible_for_future_dispatch_execution_task"] is False
    assert data["eligible_for_live_send_now"] is False


def test_static_no_env_provider_network_browser_request_patterns():
    src = Path("live_contentops/dispatch_gate_scaffold_from_prepared_outbox_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$", r"getenv", r"environ", r"dotenv", r"requests", r"urllib", r"httpx", r"webbrowser", r"selenium", r"playwright", r"discord(?:app)?\.com/api/webhooks", r"requests\.post", r"fetch\(", r"curl ", r"Authorization", r"Content-Type", r"\bPOST\b"]:
        assert re.search(pat, src, re.M | re.I) is None, pat


