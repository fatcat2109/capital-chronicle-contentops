from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_v5_remains_canonical_dashboard() -> None:
    status = json.loads((ROOT / "docs/status/current_project_status.json").read_text(encoding="utf-8"))
    assert status["canonical_dashboard_surface"] == "ui/contentops_v5/"
    assert status["canonical_dashboard_entrypoint"] == "ui/contentops_v5/src/App.tsx"
    assert "ui/institutional_operator_cockpit_v4/" in status["legacy_reference_surfaces"]


def test_current_backend_chain_is_registered() -> None:
    status = json.loads((ROOT / "docs/status/current_project_status.json").read_text(encoding="utf-8"))
    modules = set(status["backend_status_modules"])
    assert "live_contentops/eight_platform_substack_first_pipeline_v1.py" in modules
    assert "live_contentops/edge_cdp_publishing_adapter_v1.py" in modules
    assert "live_contentops/media_manifest_authority_v1.py" in modules


def test_historical_release_manifest_remains_historical() -> None:
    manifest = json.loads((ROOT / "docs/automation/V6_JIM_CONTENT_COCKPIT_BASELINE/jim_content_cockpit_release_manifest_v0.json").read_text(encoding="utf-8"))
    status = json.loads((ROOT / "docs/status/current_project_status.json").read_text(encoding="utf-8"))
    assert manifest["baseline_sha"] != status["accepted_product_baseline_sha"]
    assert manifest["canonical_dashboard_surface"] == status["canonical_dashboard_surface"]


def test_status_does_not_claim_tiktok_completion() -> None:
    status = json.loads((ROOT / "docs/status/current_project_status.json").read_text(encoding="utf-8"))
    assert status["platform_matrix"]["tiktok_native"]["quality_status"] == "BLOCKED_TIKTOK_OAUTH_ADAPTER_AND_APP_AUDIT_INCOMPLETE"
