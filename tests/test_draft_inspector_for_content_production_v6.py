import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.draft_inspector_for_content_production_v6 import *
import live_contentops.draft_inspector_for_content_production_v6 as inspector

SAMPLE = Path("docs/automation/V6_CONTENT_PRODUCTION_CORE_REVIEW_PACKETS_HEAVY_BATCH_NO_PROVIDER_NO_SEND/sample_content_production_core_review_bundle.json")


def _bundle():
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


def _inspection(bundle=None):
    return make_draft_inspection_bundle(bundle or _bundle())


def test_malformed_non_object_json_cli_fails_closed(tmp_path):
    inp = tmp_path / "bad.json"; out = tmp_path / "out.json"
    inp.write_text("[]", encoding="utf-8")
    assert main(["--content-production-review-bundle", str(inp), "--output", str(out)]) == 1
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["eligible_for_payload_hash_preview_task"] is False
    assert data["eligible_for_live_send_now"] is False


def test_static_no_env_provider_network_browser_request_patterns():
    src = Path("live_contentops/draft_inspector_for_content_production_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$", r"getenv", r"environ", r"dotenv", r"requests", r"urllib", r"httpx", r"webbrowser", r"selenium", r"playwright", r"discord(?:app)?\.com/api/webhooks", r"requests\.post", r"fetch\(", r"curl ", r"Authorization", r"Content-Type", r"\bPOST\b"]:
        assert re.search(pat, src, re.M | re.I) is None, pat


