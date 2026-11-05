import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.payload_hash_preview_approval_prep_v6 import *
import live_contentops.payload_hash_preview_approval_prep_v6 as prep

SAMPLE_DRAFT_INSPECT = Path("docs/automation/V6_DRAFT_INSPECTOR_FOR_CONTENT_PRODUCTION_REVIEW_BUNDLE_HEAVY_BATCH_NO_PROVIDER_NO_SEND/sample_draft_inspection_bundle.json")
SAMPLE_REVIEW_CORE = Path("docs/automation/V6_CONTENT_PRODUCTION_CORE_REVIEW_PACKETS_HEAVY_BATCH_NO_PROVIDER_NO_SEND/sample_content_production_core_review_bundle.json")


def _draft_inspect():
    return json.loads(SAMPLE_DRAFT_INSPECT.read_text(encoding="utf-8"))


def _review_core():
    return json.loads(SAMPLE_REVIEW_CORE.read_text(encoding="utf-8"))


def _bundle(d_inspect=None, r_core=None):
    return make_payload_hash_preview_approval_prep_bundle(d_inspect or _draft_inspect(), r_core or _review_core())


def test_static_no_env_provider_network_browser_request_patterns():
    src = Path("live_contentops/payload_hash_preview_approval_prep_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$", r"getenv", r"environ", r"dotenv", r"requests", r"urllib", r"httpx", r"webbrowser", r"selenium", r"playwright", r"discord(?:app)?\.com/api/webhooks", r"requests\.post", r"fetch\(", r"curl ", r"Authorization", r"Content-Type", r"\bPOST\b"]:
        assert re.search(pat, src, re.M | re.I) is None, pat


