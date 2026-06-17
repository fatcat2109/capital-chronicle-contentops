"""Tests for 0174UZ/VA/VB Telegram operator cockpit HTML render + handoff.

Pure, LOCAL, deterministic. NO network / API / Telegram / env / credential read
and NO ``sendMessage``. Asserts the render model, all seven cockpit sections in
the HTML, the absence of any dispatch/external affordance, the manual-gate
handoff contract, and deterministic scanner-clean packet/doc/html.
"""

import importlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

render = importlib.import_module(
    "live_contentops.telegram_operator_cockpit_html_render")
readmodel = importlib.import_module(
    "live_contentops.telegram_operator_cockpit_read_model")

READ_MODEL_PACKET_PATH = ROOT / render.READ_MODEL_PACKET_REL


def _read_model_packet():
    return json.loads(READ_MODEL_PACKET_PATH.read_text(encoding="utf-8"))


def _render_model():
    return render.build_cockpit_render_model(_read_model_packet())


def _html():
    return render.render_cockpit_html(_render_model())


# --------------------------------------------------------------------------- #
# Import / fixtures
# --------------------------------------------------------------------------- #
def test_import_has_no_side_effects():
    mod = importlib.reload(render)
    assert mod.TASK_LABEL.startswith("TASK_CONTENTOPS_0174UZ_VA_VB")


def test_committed_read_model_packet_exists():
    assert READ_MODEL_PACKET_PATH.is_file()


# --------------------------------------------------------------------------- #
# Render model
# --------------------------------------------------------------------------- #
def test_render_model_builds_from_committed_0174uw_packet():
    rm = _render_model()
    assert rm["render_model_schema"] == render.RENDER_MODEL_SCHEMA
    assert rm["provider"] == "telegram"
    assert rm["render_model_checksum"]
    assert (rm["source_read_model_checksum"]
            == _read_model_packet()["cockpit_read_model_checksum"])


def test_render_model_is_deterministic():
    assert (_render_model()["render_model_checksum"]
            == _render_model()["render_model_checksum"])


# --------------------------------------------------------------------------- #
# HTML structure / sections
# --------------------------------------------------------------------------- #
def test_html_contains_all_seven_sections():
    html = _html()
    for section in ("CommandHero", "OperationalTruthRail", "ReplayGuardPanel",
                    "NextSendPrecheckPanel", "EvidenceChainPanel",
                    "ForbiddenAffordancePanel", "ManualGateHandoffPanel"):
        assert section in html, section


def test_html_root_has_no_dispatch_attribute():
    html = _html()
    assert 'data-no-dispatch="true"' in html


def test_html_contains_truth_rail_values():
    html = _html()
    assert ">2<" in html  # ledger count 2
    assert ">3<" in html  # last sequence 3
    assert "RECONCILED" in html
    assert "ledger_reconciliation_ok_count_incremented" in html


def test_html_contains_no_candidate_selected_default_state():
    html = _html()
    assert "NO CANDIDATE SELECTED" in html
    assert "no_candidate_selected" in html
    assert "next_send_precheck_blocked_missing_candidate" in html


def test_html_contains_replay_states():
    html = _html()
    assert "blocked_exact_replay_do_not_send" in html
    assert "requires_fresh_operator_gate" in html
    assert "clear_for_manual_supervised_send_gate" in html


def test_html_live_ready_only_in_forbidden_context():
    html = _html()
    # The only mention of "live-ready" must be the forbidden affordance label.
    assert "no live ready claim" in html.lower() or "no_live_ready_claim" in html
    # Never a positive live-ready claim.
    assert "is live ready" not in html.lower()
    assert "live_ready=true" not in html.lower()


def test_html_has_no_secrets():
    html = _html()
    assert "api.telegram.org/bot" not in html
    assert not re.search(r"\b\d{6,}:[A-Za-z0-9_-]{30,}\b", html)  # bot token
    assert "set-cookie" not in html.lower()
    assert "authorization:" not in html.lower()


def test_html_has_no_external_resources():
    html = _html().lower()
    assert "http://" not in html
    assert "https://" not in html
    assert "//cdn" not in html
    assert "<link" not in html
    assert "src=" not in html
    assert "@import" not in html
    assert "googleapis" not in html


def test_html_has_no_network_or_form_affordance():
    html = _html().lower()
    assert "<form" not in html
    assert "action=" not in html
    assert "fetch(" not in html
    assert "xmlhttprequest" not in html
    assert "websocket" not in html
    assert "navigator.sendbeacon" not in html
    assert "method=\"post\"" not in html
    assert "http-equiv=\"refresh\"" not in html


def test_html_has_no_dispatch_control_labels():
    html = _html().lower()
    # No actionable send/publish/post/retry/schedule control labels.
    for bad in (">send<", ">publish<", ">post now<", ">retry<", ">schedule<",
                "send message", "post now"):
        assert bad not in html, bad


def test_html_contains_allowed_inert_ctas():
    html = _html()
    assert render.CTA_PREPARE in html
    assert render.CTA_OPEN_EVIDENCE in html
    assert render.CTA_COPY_SUMMARY in html


def test_html_embedded_js_is_inert():
    html = _html().lower()
    # Copy + density toggle only.
    assert "clipboard" in html
    assert "is-compact" in html


# --------------------------------------------------------------------------- #
# Manual gate handoff contract
# --------------------------------------------------------------------------- #
def test_handoff_contract_waiting_for_candidate_default():
    contract = render.build_manual_gate_handoff_contract(_render_model())
    assert contract["handoff_status"] == render.HANDOFF_WAITING
    assert contract["handoff_contract_checksum"]


def test_handoff_contract_requires_all_gates():
    contract = render.build_manual_gate_handoff_contract(_render_model())
    assert contract["candidate_required"] is True
    assert contract["fresh_operator_gate_required"] is True
    assert contract["credential_boundary_required"] is True
    assert contract["destination_binding_required"] is True
    assert contract["approved_payload_checksum_required"] is True
    assert contract["replay_guard_must_be_clear"] is True
    for req in render.HANDOFF_REQUIREMENTS:
        assert req in contract["requirements"]


def test_handoff_contract_is_not_dispatch():
    contract = render.build_manual_gate_handoff_contract(_render_model())
    assert contract["is_dispatch"] is False
    assert contract["requires_separate_operator_send_gate"] is True
    assert contract["live_ready"] is False
    assert contract["valid_for_live_execution"] is False
    blob = json.dumps(contract)
    assert "api.telegram.org/bot" not in blob


def test_handoff_status_clear_not_dispatch_when_precheck_clear():
    rm = _render_model()
    rm["next_send_precheck_panel"]["precheck_outcome_class"] = (
        readmodel.PRECHECK_CLEAR)
    contract = render.build_manual_gate_handoff_contract(rm)
    assert contract["handoff_status"] == render.HANDOFF_CLEAR_NOT_DISPATCH


def test_handoff_status_blocked_when_exact_replay():
    rm = _render_model()
    rm["next_send_precheck_panel"]["precheck_outcome_class"] = (
        readmodel.PRECHECK_BLOCKED_EXACT_REPLAY)
    contract = render.build_manual_gate_handoff_contract(rm)
    assert contract["handoff_status"] == render.HANDOFF_BLOCKED


# --------------------------------------------------------------------------- #
# Render packet + doc
# --------------------------------------------------------------------------- #
def _packet():
    rm = _render_model()
    handoff = render.build_manual_gate_handoff_contract(rm)
    return render.build_render_packet(_read_model_packet(), rm, handoff)


def test_render_packet_is_deterministic():
    assert _packet() == _packet()
    assert _packet()["render_packet_checksum"]


def test_render_packet_links_all_checksums():
    p = _packet()
    rm = _render_model()
    assert p["render_model_checksum"] == rm["render_model_checksum"]
    assert p["html_checksum"] == render.compute_checksum(
        render.render_cockpit_html(rm))
    assert (p["source_read_model_checksum"]
            == _read_model_packet()["cockpit_read_model_checksum"])
    assert p["handoff_contract_checksum"]
    assert len(p["cockpit_sections"]) == 7


def test_render_packet_and_doc_scanner_clean():
    p = _packet()
    doc = render.build_render_doc(p)
    html = render.render_cockpit_html(_render_model())
    assert render.scan_render(html, p, doc) == []


def test_render_packet_not_live_no_secrets():
    p = _packet()
    assert p["live_ready"] is False
    assert p["sendmessage_executed"] is False
    assert p["network_performed"] is False
    assert p["telegram_api_called"] is False
    assert p["credential_read"] is False
    assert p["env_read"] is False
    assert p["valid_for_live_execution"] is False
    assert p["no_external_dependency"] is True
    assert "api.telegram.org/bot" not in json.dumps(p)


def test_build_from_repo_matches_explicit():
    rm, handoff, packet, html, doc = render.build_all_from_repo(ROOT)
    assert rm["render_model_checksum"] == _render_model()["render_model_checksum"]
    assert packet["html_checksum"] == render.compute_checksum(html)
    assert handoff["handoff_status"] == render.HANDOFF_WAITING
    assert render.scan_render(html, packet, doc) == []


def test_write_artifacts_refuses_unsafe(tmp_path):
    import pytest
    rm = _render_model()
    handoff = render.build_manual_gate_handoff_contract(rm)
    packet = render.build_render_packet(_read_model_packet(), rm, handoff)
    doc = render.build_render_doc(packet)
    html = render.render_cockpit_html(rm)
    written = render.write_artifacts(tmp_path, html, packet, doc)
    assert len(written) == 3
    bad_html = html + "\n<!-- 123456789:AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQq00 -->"
    with pytest.raises(RuntimeError):
        render.write_artifacts(tmp_path, bad_html, packet, doc)
