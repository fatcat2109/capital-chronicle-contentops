import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from live_contentops import editorial_packet_export as export


def load_fixture(name):
    path = os.path.join(os.path.dirname(__file__), "fixtures", "editorial", name)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def export_req():
    return load_fixture("export_packet_input.json")


@pytest.fixture
def packet(export_req):
    return export.build_export_packet(export_req)


def test_packet_includes_all_required_components(packet):
    required = [
        "export_packet_id",
        "source_fixture_id",
        "content_type",
        "target_platforms",
        "audience_modes",
        "style_modes",
        "grounded_research_context",
        "seo_metadata_pack",
        "prompt_packet",
        "citation_guardrail_result",
        "editorial_qa_result",
        "preview_variants",
        "selection_packet",
        "no_public_post_status",
        "operator_review",
        "audit_flags",
        "advisory_only",
        "approval_granted",
        "publish_ready",
        "provider_call_allowed",
        "search_call_allowed",
        "platform_action_allowed",
    ]
    for key in required:
        assert key in packet, f"missing component: {key}"
    for component in export.COMPONENTS_INCLUDED:
        assert component in packet["components_included"]


def test_packet_safety_flags(packet):
    assert packet["advisory_only"] is True
    assert packet["approval_granted"] is False
    assert packet["publish_ready"] is False
    assert packet["provider_call_allowed"] is False
    assert packet["search_call_allowed"] is False
    assert packet["platform_action_allowed"] is False
    assert packet["human_review_required"] is True


def test_packet_is_deterministic(export_req):
    p1 = export.build_export_packet(export_req)
    p2 = export.build_export_packet(export_req)
    assert json.dumps(p1, sort_keys=True) == json.dumps(p2, sort_keys=True)
    assert p1["export_packet_id"] == p2["export_packet_id"]


def test_json_compatible_export(packet):
    as_json = export.to_json_dict(packet)
    dumped = json.dumps(as_json, sort_keys=True)
    assert json.loads(dumped) == as_json


def test_markdown_report_is_deterministic_and_has_banners(packet):
    md1 = export.render_markdown_report(packet)
    md2 = export.render_markdown_report(packet)
    assert md1 == md2
    for banner in ["LOCAL ONLY", "ADVISORY ONLY", "NOT PUBLIC POSTABLE", "HUMAN REVIEW REQUIRED"]:
        assert banner in md1
    assert "NO PROVIDER CALL" in md1
    assert "NO SEARCH CALL" in md1
    assert "NO PLATFORM ACTION" in md1


def test_manual_review_placeholders_grant_no_authority(packet):
    review = packet["operator_review"]
    assert review["operator_selected_preview_id"] is None
    assert review["selected_by_operator"] is False
    assert review["operator_notes"] == ""
    assert review["review_status"] == "PENDING_MANUAL_REVIEW"
    assert review["approval_status"] == "NOT_APPROVED"
    assert review["publish_status"] == "NOT_PUBLIC_POSTABLE"


def test_selection_packet_remains_manual_only(packet):
    sel = packet["selection_packet"]
    assert sel["manual_selection_required"] is True
    assert sel["auto_selected"] is False
    assert sel["approval_granted"] is False
    assert sel["publish_ready"] is False


def test_synthetic_outputs_carry_no_public_post_reason(packet):
    for variant in packet["preview_variants"]:
        assert variant["not_public_postable_reason"] is not None
    assert packet["grounded_research_context"]["not_public_postable_reason"] is not None
    assert packet["seo_metadata_pack"]["not_public_postable_reason"] is not None
    nps = packet["no_public_post_status"]
    assert nps["not_public_postable"] is True
    assert nps["all_fixture_outputs_not_public_postable"] is True


def test_limitations_and_sources_remain_visible(packet):
    sources = packet["grounded_research_context"]["source_items"]
    assert len(sources) >= 1
    assert all(s.get("limitations") for s in sources)


def test_validation_passes_on_clean_packet(packet):
    result = export.validate_export_packet(packet)
    assert result["status"] in ("PASS", "WARNING")
    assert result["blockers"] == []


def test_validation_blocks_authority_grant(packet):
    packet["approval_granted"] = True
    result = export.validate_export_packet(packet)
    assert result["status"] == "BLOCKED"
    assert any("approval/publish authority" in b for b in result["blockers"])


def test_validation_blocks_provider_search_platform(packet):
    packet["prompt_packet"]["provider_call_allowed"] = True
    result = export.validate_export_packet(packet)
    assert result["status"] == "BLOCKED"
    assert any("provider/search/platform" in b for b in result["blockers"])


def test_validation_blocks_auto_selection(packet):
    packet["selection_packet"]["auto_selected"] = True
    result = export.validate_export_packet(packet)
    assert result["status"] == "BLOCKED"
    assert any("auto-selects" in b for b in result["blockers"])



def test_blocked_citation_guardrail_cannot_be_published():
    req = {
        "source_fixture_id": "blocked_demo",
        "prompt": {
            "is_synthetic": True,
            "citation_requirements": "Required for all claims",
            "source_context": {"is_current_events": True, "source_items": []},
        },
    }
    packet = export.build_export_packet(req)
    assert packet["citation_guardrail_result"]["status"] == "BLOCKED"
    assert packet["publish_ready"] is False
    assert packet["approval_granted"] is False
    assert any("CITATION_GUARDRAIL_BLOCKED" in f for f in packet["audit_flags"])
    md = export.render_markdown_report(packet)
    assert "BLOCKED" in md
    packet["publish_ready"] = True
    result = export.validate_export_packet(packet)
    assert result["status"] == "BLOCKED"
    assert any("BLOCKED" in b for b in result["blockers"])


def test_no_forbidden_capability_imports():
    src_path = os.path.join(
        os.path.dirname(__file__), "..", "live_contentops", "editorial_packet_export.py"
    )
    with open(src_path, "r", encoding="utf-8") as f:
        src = f.read()
    forbidden = [
        "import requests", "import urllib", "import socket", "import http",
        "import aiohttp", "import websockets", "openai", "anthropic",
        "selenium", "playwright", "os.environ", "api_key", "bot_token",
    ]
    for token in forbidden:
        assert token not in src, f"forbidden capability token found: {token}"


def test_cli_grounded_editorial_packet_summary():
    result = subprocess.run(
        [sys.executable, "-m", "live_contentops.cli", "grounded-editorial-packet-summary"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["local_only"] is True
    assert data["advisory_only"] is True
    assert data["provider_call_allowed"] is False
    assert data["search_call_allowed"] is False
    assert data["platform_action_allowed"] is False
    assert data["human_review_required"] is True
    assert data["approval_granted"] is False
    assert data["publish_ready"] is False
    assert data["all_fixture_outputs_not_public_postable"] is True
    assert "json_dict" in data["export_formats_supported"]
    assert "markdown_report" in data["export_formats_supported"]

