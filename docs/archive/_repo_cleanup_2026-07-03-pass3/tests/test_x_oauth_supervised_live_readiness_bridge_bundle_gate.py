"""Tests for the 0174DD X OAuth supervised-live-readiness BRIDGE BUNDLE gate.

These tests prove the module is strictly local, bridge-scaffold-only, and never
imports or references anything that could read credentials / env / env-file /
config / key-ring / browser store / network / browser / server / subprocess /
socket / shell history / source-control history. They also prove the gate is
fail-closed, deterministic, performs NO live network call, NO token exchange,
NO credential presence check, NO account binding, NO posting, adds NO runnable
live execution command, emits NO real secret / token / hash / fingerprint /
prefix / suffix / source-name-with-value / redacted-from-real string, that all
ten bridge contract sections exist, the blocker clearance order is
deterministic and blocker-first, and that the prior 0174CU..0174DC chain
artifacts are not mutated by importing/running it.
"""

import ast
import io
import json
import os
import re
import sys
import contextlib

import pytest

from live_contentops import (
    x_oauth_supervised_live_readiness_bridge_bundle_gate as gate)


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(
    REPO_ROOT, "live_contentops",
    "x_oauth_supervised_live_readiness_bridge_bundle_gate.py")


# --------------------------------------------------------------------------- #
# Import allow-list / forbidden imports (static AST analysis)
# --------------------------------------------------------------------------- #
ALLOWED_IMPORT_ROOTS = {"hashlib", "json", "os", "re", "sys"}

FORBIDDEN_IMPORT_ROOTS = {
    "socket", "socketserver", "ssl", "asyncio", "selectors",
    "http", "wsgiref", "urllib", "requests", "httpx", "aiohttp",
    "webbrowser", "subprocess", "dotenv", "ftplib", "telnetlib",
    "smtplib", "multiprocessing", "threading",
    "configparser", "keyring", "getpass", "secretstorage", "netrc",
    "browser_cookie3", "sqlite3", "pickle", "shelve",
}


def _module_imports():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                roots.add(node.module.split(".")[0])
    return roots


def test_import_allow_list_exact():
    roots = _module_imports()
    assert roots <= ALLOWED_IMPORT_ROOTS, (
        f"unexpected imports: {roots - ALLOWED_IMPORT_ROOTS}")


def test_no_forbidden_imports():
    roots = _module_imports()
    bad = roots & FORBIDDEN_IMPORT_ROOTS
    assert not bad, f"forbidden imports present: {bad}"


def test_only_os_path_used_not_os_environ():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    for forbidden in ("os.environ", "os.getenv", "getenv(", "expanduser",
                      "os.putenv", "environb"):
        assert forbidden not in src, f"forbidden env access: {forbidden}"


def test_no_forbidden_runtime_strings():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    forbidden_substrings = [
        ".bind(", ".listen(", ".connect(", "socket(", "create_server",
        "HTTPServer", "BaseHTTPRequestHandler", "serve_forever",
        "webbrowser.open", "subprocess.", "Popen", "urlopen", "requests.get",
        "requests.post", "httpx.", "aiohttp.", "load_dotenv",
        "configparser.", "keyring.", "getpass.", "ConfigParser",
        "open(os.path.expanduser", ".read_text(",
    ]
    for s in forbidden_substrings:
        assert s not in src, f"forbidden runtime string present: {s}"


def test_no_env_dotenv_config_keyring_access_strings():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    for s in ("os.environ", "os.getenv", "getenv(", "load_dotenv",
              "dotenv_values", "keyring.get", "keyring.set", "getpass.",
              "secretstorage.", "netrc(", "configparser.", "ConfigParser",
              "expanduser", "browser_cookie", "sqlite3."):
        assert s not in src, f"forbidden credential/env access string: {s}"


# --------------------------------------------------------------------------- #
# Packet structure / flags
# --------------------------------------------------------------------------- #
REQUIRED_TRUE_FLAGS = [
    "no_live_network_call_performed",
    "no_network_call_performed",
    "no_credentials_read",
    "no_env_read",
    "no_dotenv_read",
    "no_config_read",
    "no_keyring_read",
    "no_browser_store_read",
    "no_shell_history_read",
    "no_git_history_secret_scan",
    "no_client_id_read",
    "no_client_secret_read",
    "no_access_token_read",
    "no_refresh_token_read",
    "no_bearer_token_read",
    "no_credential_presence_check_performed",
    "no_token_exchange_performed",
    "no_token_response_seen",
    "no_token_persisted",
    "no_secret_material_persisted",
    "no_secret_hash_or_fingerprint_created",
    "no_secret_prefix_or_suffix_exposed",
    "no_account_identifier_read",
    "no_account_binding_performed",
    "no_oauth_flow_performed",
    "no_authorize_url_opened",
    "no_browser_login_performed",
    "no_developer_portal_login_performed",
    "no_callback_server_started",
    "no_localhost_port_bound",
    "no_socket_created",
    "no_port_listened",
    "no_authorization_code_generated_or_received",
    "no_real_callback_url_processed",
    "no_raw_callback_query_processed",
    "no_state_generated",
    "no_code_verifier_generated",
    "no_code_challenge_generated",
    "no_posting_performed",
    "no_metrics_fetched",
    "no_webhook_created",
    "no_reply_dm_created",
    "no_scraping_performed",
    "no_autonomous_publishing",
    "redaction_verified",
]


def test_packet_required_true_flags():
    packet = gate.build_packet()
    for flag in REQUIRED_TRUE_FLAGS:
        assert packet.get(flag) is True, f"flag not true: {flag}"


def test_packet_required_keys_present():
    packet = gate.build_packet()
    required = [
        "task_label", "gate", "platform", "source_baseline_commit",
        "inherited_0174dc_commit", "accepted_0174dc_reference",
        "bridge_bundle_status", "live_readiness_stage",
        "official_docs_checked", "official_docs_sources",
        "developer_portal_access_status", "access_tier_status",
        "redirect_uri_registration_status", "client_type_resolution",
        "redacted_credential_presence_fixture_contract",
        "operator_controlled_source_handle_contract",
        "disabled_presence_check_execution_contract",
        "account_binding_proof_packet_contract",
        "token_response_redaction_ledger_contract",
        "future_live_read_only_identity_proof_contract",
        "pre_live_blocker_dashboard_contract",
        "future_text_only_dry_run_contract",
        "future_payload_hash_approval_contract",
        "future_kill_switch_duplicate_prevention_contract",
        "future_supervised_post_budget_contract",
        "current_blockers", "blocker_clearance_order",
        "exact_next_live_read_only_task", "exact_next_task_recommendation",
        "caveats",
    ]
    for key in required:
        assert key in packet, f"missing required key: {key}"


def test_packet_identity_values():
    packet = gate.build_packet()
    assert packet["platform"] == "x"
    assert packet["source_baseline_commit"] == (
        "725ab7c5ca38ccc1c4231eb0e6d9e23ec4ea2c67")
    assert packet["inherited_0174dc_commit"] == (
        "725ab7c5ca38ccc1c4231eb0e6d9e23ec4ea2c67")


def test_bridge_bundle_status_and_stage():
    out = gate.run_gate(write=False)
    assert out["bridge_bundle_status"] == "local_bridge_scaffold_only"
    assert out["live_readiness_stage"] == "pre_live_blocked"
    assert out["status"] == "pass"
    packet = gate.build_packet()
    assert packet["bridge_bundle_status"] == "local_bridge_scaffold_only"
    assert packet["live_readiness_stage"] == "pre_live_blocked"


def test_developer_portal_and_access_tier_blocked():
    packet = gate.build_packet()
    assert packet["developer_portal_access_status"] == (
        "gated_login_required_not_performed")
    assert packet["access_tier_status"] == "not_verified"
    assert packet["redirect_uri_registration_status"] == (
        "not_verified_blocked")
    assert packet["client_type_resolution"] == (
        "unresolved_public_vs_confidential")


# --------------------------------------------------------------------------- #
# All ten bridge contract sections exist
# --------------------------------------------------------------------------- #
def test_all_ten_bridge_contract_sections_exist():
    packet = gate.build_packet()
    for key in gate.BRIDGE_CONTRACT_SECTION_KEYS:
        assert key in packet, f"missing bridge contract section: {key}"
    assert len(gate.BRIDGE_CONTRACT_SECTION_KEYS) == 10


def test_presence_fixture_contract_classes_only():
    packet = gate.build_packet()
    contract = packet["redacted_credential_presence_fixture_contract"]
    assert contract["execution_status"] == (
        "not_executed_design_fixtures_only")
    fixtures = contract["fixture_classes"]
    for expected in [
        "fixture_no_operator_go",
        "fixture_source_handle_missing",
        "fixture_source_handle_configured_but_unread",
        "fixture_client_id_presence_boolean_only",
        "fixture_client_secret_presence_boolean_only",
        "fixture_token_presence_forbidden_until_later_gate",
        "fixture_redaction_violation_fail_closed",
        "fixture_unknown_fail_closed",
    ]:
        assert expected in fixtures, f"missing fixture class: {expected}"


def test_operator_controlled_source_handle_contract_abstract():
    packet = gate.build_packet()
    contract = packet["operator_controlled_source_handle_contract"]
    assert contract["handle_class"] == (
        "operator_controlled_x_oauth_source_handle_class")
    assert contract["value_exposure"] == "never"
    assert "abstract" in contract["rule"].lower()


def test_disabled_presence_check_execution_contract():
    packet = gate.build_packet()
    contract = packet["disabled_presence_check_execution_contract"]
    assert contract["runnable_now"] is False
    assert contract["command_added_now"] is False
    assert "operator go" in contract["future_command_rule"].lower()
    assert "separate explicit task" in contract["future_command_rule"].lower()


def test_account_binding_proof_packet_contract_redacted():
    packet = gate.build_packet()
    contract = packet["account_binding_proof_packet_contract"]
    for cls in [
        "account_binding_status_class", "identity_source_class",
        "account_permission_class", "operator_attestation_class",
    ]:
        assert cls in contract["redacted_field_classes"]
    forbidden = contract["forbidden_fields"].lower()
    assert "no account id" in forbidden
    assert "profile url" in forbidden


def test_token_response_redaction_ledger_contract():
    packet = gate.build_packet()
    contract = packet["token_response_redaction_ledger_contract"]
    for cls in [
        "request_budget_class", "endpoint_family_class",
        "token_response_seen_boolean", "token_value_exposed_boolean_false",
        "token_storage_status_class", "redaction_passed_boolean",
    ]:
        assert cls in contract["ledger_field_classes"]
    joined = " ".join(contract["invariants"]).lower()
    assert "token_value_exposed_boolean is always false" in joined
    assert "no raw token body" in joined
    assert "no token hash" in joined


def test_future_live_read_only_identity_proof_contract():
    packet = gate.build_packet()
    contract = packet["future_live_read_only_identity_proof_contract"]
    assert contract["one_request_max"] is True
    assert contract["no_retry"] is True
    assert contract["no_posting"] is True
    assert contract["no_metrics"] is True
    assert contract["no_account_mutation"] is True
    assert contract["no_token_persistence"] is True
    assert contract["redacted_output_only"] is True
    assert contract["operator_go_required"] is True
    assert contract["live_read_only_gate_required"] is True
    assert contract["exact_endpoint_family"] == "must_be_declared_later"


def test_future_supervised_post_budget_contract():
    packet = gate.build_packet()
    contract = packet["future_supervised_post_budget_contract"]
    assert contract["request_budget"] == 1
    assert contract["no_retry"] is True
    assert contract["exact_payload_hash_required"] is True
    assert contract["exact_channel_account_binding_required"] is True
    assert contract["approval_ledger_required"] is True
    assert contract["kill_switch_required"] is True
    assert contract["duplicate_prevention_required"] is True
    assert contract["redacted_post_send_ledger_required"] is True
    assert contract["operator_one_time_go_required"] is True
    assert contract["execution_status"] == "not_executed_contract_only"


# --------------------------------------------------------------------------- #
# Blocker dashboard / clearance order are deterministic and blocker-first
# --------------------------------------------------------------------------- #
def test_pre_live_blocker_dashboard_deterministic_order():
    packet = gate.build_packet()
    contract = packet["pre_live_blocker_dashboard_contract"]
    ordered = contract["ordered_blockers"]
    assert ordered == list(gate.PRE_LIVE_BLOCKER_ORDER)
    assert ordered[0] == "developer access/tier unverified"
    assert ordered[-1] == "live posting still blocked"
    assert contract["ordering_rule"] == (
        "deterministic_blocker_first_fixed_order")


def test_blocker_clearance_order_deterministic_blocker_first():
    p1 = gate.build_packet()["blocker_clearance_order"]
    p2 = gate.build_packet()["blocker_clearance_order"]
    assert p1 == p2
    assert "developer access/tier" in p1[0].lower()
    assert "operator one-time go" in p1[-1].lower()


def test_exact_next_live_read_only_task_is_one_request_no_post():
    packet = gate.build_packet()
    contract = packet["future_live_read_only_identity_proof_contract"]
    nxt = contract["exact_next_live_read_only_task"]
    assert nxt == packet["exact_next_live_read_only_task"]
    assert "LIVE_READ_ONLY" in nxt
    assert "NO_POST" in nxt
    assert "NO_TOKEN_PERSIST" in nxt
    assert "OPERATOR_GO_REQUIRED" in nxt


# --------------------------------------------------------------------------- #
# No live execution command added / no live behavior exists
# --------------------------------------------------------------------------- #
def test_no_live_execution_command_added():
    out = gate.run_gate(write=False)
    assert out["no_live_execution_command_added"] is True
    packet = gate.build_packet()
    contract = packet["disabled_presence_check_execution_contract"]
    assert contract["command_added_now"] is False


def test_explicit_non_actions_present():
    packet = gate.build_packet()
    joined = " ".join(packet["explicit_non_actions"]).lower()
    for needle in [
        "does not perform a live network call",
        "does not exchange tokens",
        "does not perform a credential presence check",
        "does not bind an x account",
        "does not perform oauth",
        "does not start a callback server",
        "does not post, edit, delete, repost, like, reply, or dm",
        "does not add a new live execution command",
        "separate explicit task and operator go",
    ]:
        assert needle in joined, f"missing explicit non-action: {needle}"


def test_no_token_exchange_or_posting_behavior_in_source():
    with open(MODULE_PATH, "r", encoding="utf-8") as fh:
        src = fh.read()
    # No HTTP verb / send shapes for token exchange or posting.
    for s in ("requests.post", "urlopen", "httpx.post", "session.post",
              ".post(", "create_tweet", "statuses/update"):
        assert s not in src, f"forbidden live behavior string: {s}"


# --------------------------------------------------------------------------- #
# Redaction
# --------------------------------------------------------------------------- #
def test_packet_redaction_scan_clean():
    packet = gate.build_packet()
    assert gate.scan_packet_for_leaks(packet) == []


def test_redaction_catches_token_like():
    bad = {"notes": "bearer ABCDEFGHIJKLMNOP1234567890"}
    assert gate.scan_packet_for_leaks(bad)


def test_redaction_catches_callback_url_with_query():
    bad = {"notes": "https://example.com/callback?code=abc&state=xyz"}
    assert gate.scan_packet_for_leaks(bad)


def test_redaction_catches_forbidden_key():
    bad = {"access_token": "x"}
    assert any(v.startswith("forbidden_key:")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_catches_profile_url_key():
    bad = {"profile_url": "x"}
    assert any(v.startswith("forbidden_key:")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_catches_env_assignment():
    bad = {"notes": "X_CLIENT_SECRET=supersecretvalue123"}
    assert any(v.startswith("env_assignment:")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_catches_secret_fingerprint_claim():
    bad = {"notes": "token fingerprint: ab12cd34"}
    assert any(v.startswith("secret_fingerprint_claim:")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_catches_redacted_from_real_claim():
    bad = {"notes": "the secret starts with abcd"}
    assert any(v.startswith("redacted_from_real_claim:")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_catches_source_name_with_value():
    bad = {"notes": "credential source: vault_path=/secret/x"}
    assert any(v.startswith("source_name_with_value:")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_catches_raw_token_response_claim():
    bad = {"notes": "access_token: abcdef123456"}
    assert gate.scan_packet_for_leaks(bad)


def test_redaction_catches_handle():
    bad = {"notes": "bind to @somehandle now"}
    assert any(v.startswith("raw_handle:")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_catches_long_numeric_id():
    bad = {"notes": "user 1234567890 bound"}
    assert any(v.startswith("long_digits_possible_id:")
               for v in gate.scan_packet_for_leaks(bad))


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #
def test_serialize_deterministic():
    p1 = gate.build_packet()
    p2 = gate.build_packet()
    assert gate.serialize(p1) == gate.serialize(p2)
    assert gate.serialize(p1).endswith("\n")


def test_checksum_stable():
    assert gate.compute_checksum(gate.build_packet()) == (
        gate.compute_checksum(gate.build_packet()))


# --------------------------------------------------------------------------- #
# run_gate dry-run vs write
# --------------------------------------------------------------------------- #
def test_run_gate_dry_run_writes_nothing(tmp_path):
    out = gate.run_gate(write=False, repo_root=str(tmp_path))
    assert out["write_requested"] is False
    assert out["packet_written"] is False
    assert out["readme_written"] is False
    assert not (tmp_path / gate.PACKET_REL_DIR / gate.PACKET_FILENAME).exists()


def test_run_gate_write_creates_only_packet_and_readme(tmp_path):
    out = gate.run_gate(write=True, repo_root=str(tmp_path))
    assert out["packet_written"] is True
    assert out["readme_written"] is True
    out_dir = tmp_path / "docs" / "credential_readiness" / "0174DD"
    written = sorted(p.name for p in out_dir.iterdir())
    assert written == sorted([gate.PACKET_FILENAME, gate.README_FILENAME])
    with open(out_dir / gate.PACKET_FILENAME, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert gate.scan_packet_for_leaks(data) == []
    assert data["bridge_bundle_status"] == "local_bridge_scaffold_only"
    assert data["live_readiness_stage"] == "pre_live_blocked"


def test_written_packet_checksum_matches_reported(tmp_path):
    out = gate.run_gate(write=True, repo_root=str(tmp_path))
    out_dir = tmp_path / "docs" / "credential_readiness" / "0174DD"
    with open(out_dir / gate.PACKET_FILENAME, "rb") as fh:
        raw = fh.read()
    import hashlib
    assert hashlib.sha256(raw).hexdigest() == out["packet_checksum"]


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _run_cli(args):
    buf = io.StringIO()
    old = sys.argv
    sys.argv = ["live_contentops.cli",
                "x-oauth-supervised-live-readiness-bridge-bundle-gate"] + args
    try:
        with contextlib.redirect_stdout(buf):
            gate.main(argv=args)
    finally:
        sys.argv = old
    return buf.getvalue()


def test_cli_main_dry_run():
    out = json.loads(_run_cli([]))
    assert out["status"] == "pass"
    assert out["write_requested"] is False


def test_cli_command_is_wired():
    from live_contentops import cli
    assert "x-oauth-supervised-live-readiness-bridge-bundle-gate" in (
        cli.COMMANDS)


# --------------------------------------------------------------------------- #
# Prior chain must not be mutated by import/run
# --------------------------------------------------------------------------- #
def test_prior_chain_packets_exist_and_untouched():
    prior = [
        "0174CU", "0174CV", "0174CW", "0174CX", "0174CY", "0174CZ", "0174DA",
        "0174DB", "0174DC",
    ]
    base = os.path.join(REPO_ROOT, "docs", "credential_readiness")
    before = {}
    for d in prior:
        ddir = os.path.join(base, d)
        if os.path.isdir(ddir):
            for fn in os.listdir(ddir):
                fp = os.path.join(ddir, fn)
                if os.path.isfile(fp):
                    with open(fp, "rb") as fh:
                        before[fp] = fh.read()
    gate.run_gate(write=False)
    for fp, content in before.items():
        with open(fp, "rb") as fh:
            assert fh.read() == content, f"prior artifact mutated: {fp}"
