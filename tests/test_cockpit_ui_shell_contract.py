import importlib
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIRED_REGIONS = [
    "CommandHero",
    "SignalLockStrip",
    "OperationalTruthRail",
    "BlockerStack",
    "ContentLane",
    "EvidenceCard",
    "AuditTable",
    "NextActionPanel",
]


def _result():
    from live_contentops import cockpit_ui_shell_contract as contract

    return contract.write_artifacts(REPO_ROOT)


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.cockpit_ui_shell_contract")
    assert module.TASK_LABEL == "TASK_CONTENTOPS_0174YL_YM_YN_COCKPIT_UI_SHELL_CONTRACT_V0"


def test_shell_packet_status_counts_and_regions():
    result = _result()
    packet = result["shell"]
    assert packet["readiness_class"] == "NOT_READY_FOR_LIVE_DISPATCH"
    assert packet["live_dispatch_status"] == "BLOCKED"
    assert packet["can_dispatch"] is False
    assert packet["public_postable"] is False
    assert packet["rendered_shell_regions"] == REQUIRED_REGIONS
    assert [region["region_id"] for region in packet["shell_regions"]] == REQUIRED_REGIONS
    assert packet["reviewable_now_count"] == 14
    assert packet["manual_export_queue_count"] == 6
    assert packet["x_preview_queue_count"] == 6
    assert packet["telegram_preview_queue_count"] == 2
    assert packet["blocked_live_dispatch_count"] == 5
    assert packet["evidence_index_count"] == 5


def test_fixture_evidence_cards_are_hash_bound_and_non_dispatching():
    result = _result()
    fixture = result["fixture"]
    assert len(fixture["evidence_cards"]) == 14
    for card in fixture["evidence_cards"]:
        assert card["component"] == "EvidenceCard"
        assert len(card["payload_hash"]) == 64
        assert card["payload_hash_short"] == card["payload_hash"][:12]
        assert card["payload_class"]
        assert card["platform"] in {"substack", "x", "telegram"}
        assert card["source_payload_id"]
        assert card["source_notes"]
        assert isinstance(card["evidence_refs"], list)
        assert card["can_dispatch"] is False
        assert card["public_postable"] is False
        assert "non-executing" in card["shell_action_label"]


def test_html_contains_required_regions_and_no_external_dependency():
    result = _result()
    html = result["html"]
    lowered = html.lower()
    for region in REQUIRED_REGIONS:
        assert region in html
    assert "http://" not in lowered
    assert "https://" not in lowered
    assert "<iframe" not in lowered
    assert "<form" not in lowered
    assert "cdn." not in lowered
    assert "tailwind" not in lowered
    assert "react" not in lowered
    assert "approved for posting" not in lowered
    assert "production-ready" not in lowered
    assert "live-ready" not in lowered
    assert "dispatch-ready" not in lowered
    assert "ready to send" not in lowered
    assert "public-postable" not in lowered
    assert "live dispatch blocked" in lowered
    assert "non-executing" in lowered


def test_policy_proofs_and_no_live_behavior_carried():
    result = _result()
    packet = result["shell"]
    assert packet["no_external_dependency_proof"] == {
        "html_scripts_allowed": False,
        "html_forms_allowed": False,
        "external_assets_allowed": False,
        "iframe_allowed": False,
        "tracking_allowed": False,
        "runtime_network_allowed": False,
        "react_used": False,
        "tailwind_used": False,
        "cdn_used": False,
        "external_fonts_used": False,
    }
    assert packet["no_forbidden_readiness_claim_proof"] == "pass_no_forbidden_readiness_claims_in_cockpit_ui_shell"
    assert packet["no_live_action_affordance_proof"]["can_dispatch"] is False
    assert packet["no_live_action_affordance_proof"]["public_postable"] is False
    assert packet["no_live_action_affordance_proof"]["action_elements_review_only_or_non_executing"] is True
    assert packet["no_live_behavior_proof"]["env_read"] is False
    assert packet["no_live_behavior_proof"]["network_performed"] is False
    assert packet["no_live_behavior_proof"]["platform_api_called"] is False
    assert packet["no_live_behavior_proof"]["provider_api_called"] is False
    assert packet["no_live_behavior_proof"]["credential_hydration_performed"] is False


def test_checksums_next_browser_qa_and_generated_files():
    result = _result()
    shell = result["shell"]
    next_packet = result["next_packet"]
    assert len(shell["cockpit_ui_shell_checksum"]) == 64
    assert len(shell["cockpit_ui_shell_fixture_checksum"]) == 64
    assert len(shell["html_checksum"]) == 64
    assert len(result["policy"]["cockpit_ui_shell_policy_checksum"]) == 64
    assert len(next_packet["next_cockpit_browser_qa_packet_checksum"]) == 64
    assert next_packet["cockpit_ui_shell_checksum"] == shell["cockpit_ui_shell_checksum"]
    assert next_packet["rendered_shell_regions"] == REQUIRED_REGIONS
    out = REPO_ROOT / "docs" / "automation" / "0174YL_YM_YN"
    assert (out / "cockpit_ui_shell_packet.json").exists()
    assert (out / "cockpit_ui_shell.md").exists()
    assert (out / "cockpit_ui_shell_policy_packet.json").exists()
    assert (out / "cockpit_ui_shell_policy.md").exists()
    assert (out / "cockpit_ui_shell.html").exists()
    assert (out / "cockpit_ui_shell_fixture.json").exists()
    assert (out / "next_cockpit_browser_qa_packet.json").exists()
    assert (out / "next_cockpit_browser_qa.md").exists()


def test_generation_deterministic_and_unsafe_output_refused():
    first = _result()
    second = _result()
    assert first["shell"] == second["shell"]
    assert first["fixture"] == second["fixture"]
    assert first["html"] == second["html"]
    assert first["next_packet"] == second["next_packet"]
    from live_contentops import cockpit_ui_shell_contract as contract

    with pytest.raises(ValueError, match="unsafe_output_path_refused"):
        contract.write_artifacts(REPO_ROOT, REPO_ROOT / "docs" / "automation")
