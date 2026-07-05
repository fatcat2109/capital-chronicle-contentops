import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
TASK = "TASK_CONTENTOPS_V6_OPERATOR_MAINTENANCE_AND_POST_RELEASE_GOVERNANCE_V0"
BASELINE_SHA = "ee2cd700675138de290090dc8968e2e60325dcd3"
MODULES = {
    "live_contentops/jim_daily_content_run_packet_v6.py",
    "live_contentops/jim_content_intent_to_variant_preview_bundle_v6.py",
    "live_contentops/jim_manual_export_approval_workbench_v6.py",
    "live_contentops/jim_redacted_audit_metrics_import_loop_v6.py",
}
FORBIDDEN_STATUS_WORDING = (
    "dispatch-ready",
    "dispatch ready",
    "publish-ready",
    "publish ready",
    "ready for dispatch",
    "ready for publish",
)


def test_status_promotes_jim_content_cockpit_baseline():
    status = json.loads((ROOT / "docs/status/current_project_status.json").read_text(encoding="utf-8"))

    assert status["latest_accepted_task"] == TASK
    assert status["accepted_product_baseline_sha"] == BASELINE_SHA
    assert "Jim" in status["current_product_lane"] or "Post-release" in status["current_product_lane"] or "rehearsal" in status["current_product_lane"].lower()
    assert "ui/contentops_v5/" == status["canonical_dashboard_surface"]
    assert MODULES.issubset(set(status["backend_status_modules"]))


def test_release_manifest_matches_status_baseline():
    status = json.loads((ROOT / "docs/status/current_project_status.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "docs/automation/V6_JIM_CONTENT_COCKPIT_BASELINE/jim_content_cockpit_release_manifest_v0.json").read_text(encoding="utf-8"))

    assert manifest["task_label"] == status["latest_accepted_task"]
    assert manifest["baseline_sha"] == status["accepted_product_baseline_sha"]
    assert manifest["canonical_dashboard_surface"] == status["canonical_dashboard_surface"]
    assert len(manifest["packet_chain"]) == 4
    assert manifest["safety_flags"]["public_url_verified"] is False
    assert manifest["safety_flags"]["dispatch_allowed"] is False
    assert manifest["safety_flags"]["live_write_allowed"] is False
    assert manifest["safety_flags"]["network_called"] is False
    assert manifest["safety_flags"]["provider_api_called"] is False
    assert manifest["safety_flags"]["platform_api_called"] is False
    assert manifest["safety_flags"]["browser_or_cdp_used"] is False
    assert manifest["safety_flags"]["credential_or_env_read"] is False


def test_status_docs_do_not_claim_forbidden_readiness_or_public_url_verification():
    targets = [
        ROOT / "docs/status/current_project_status.json",
        ROOT / "docs/automation/V6_JIM_CONTENT_COCKPIT_BASELINE/jim_content_cockpit_release_manifest_v0.json",
        ROOT / "docs/automation/V6_JIM_CONTENT_COCKPIT_BASELINE/jim_content_cockpit_release_handoff_v0.md",
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8").lower()
        assert not any(term in text for term in FORBIDDEN_STATUS_WORDING), path
        assert "public_url_verified\": true" not in text
        if "public_url" in text or "public url" in text:
            assert "public url verification is not claimed" in text or "public_url_verified\": false" in text or "public url verification remains false" in text or "substack_public_url_verified\": false" in text or "public url not verified" in text
