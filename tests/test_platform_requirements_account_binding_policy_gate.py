"""Network-free tests for the 0174CU platform requirements + account-binding policy gate.

These tests never touch the network and never read env/credentials. The module
under test imports ONLY hashlib, json, os.path, re (asserted below), so there is
no transport or dotenv surface at all.
"""

import ast

from live_contentops import platform_requirements_account_binding_policy_gate as gate


# --------------------------------------------------------------------------- #
# Write behavior
# --------------------------------------------------------------------------- #
def test_default_preview_does_not_write(tmp_path):
    out = gate.run_policy_gate(write=False, repo_root=str(tmp_path))
    assert out["status"] == "pass"
    assert out["write_requested"] is False
    assert out["packet_written"] is False
    assert out["readme_written"] is False
    assert not (tmp_path / gate.PACKET_REL_DIR).exists()


def test_explicit_write_creates_all_packets(tmp_path):
    out = gate.run_policy_gate(write=True, repo_root=str(tmp_path))
    assert out["status"] == "pass"
    assert out["packet_written"] is True
    assert out["readme_written"] is True
    out_dir = tmp_path / gate.PACKET_REL_DIR
    for name in (gate.TELEGRAM_FILENAME, gate.X_FILENAME,
                 gate.LINKEDIN_FILENAME, gate.INDEX_FILENAME,
                 gate.README_FILENAME):
        path = out_dir / name
        assert path.exists(), name
        assert path.read_text(encoding="utf-8").endswith("\n"), name


# --------------------------------------------------------------------------- #
# Platform packet content
# --------------------------------------------------------------------------- #
_REQUIRED_PACKET_FIELDS = (
    "platform", "objective", "docs_access_status", "official_docs_checked",
    "official_docs_sources", "endpoint_family_symbolic", "auth_model_symbolic",
    "permission_or_role_classes_redacted", "account_binding_model",
    "allowed_now", "forbidden_now", "required_before_dry_run",
    "required_before_live", "credential_policy", "account_binding_policy",
    "approval_policy", "redaction_policy", "test_policy", "blockers",
    "caveats", "recommended_next_task_for_platform", "status",
    "blocked_reasons",
)


def _all_packets():
    return {
        "telegram": gate.build_telegram_packet(),
        "x": gate.build_x_packet(),
        "linkedin": gate.build_linkedin_packet(),
    }


def test_each_platform_packet_has_required_fields():
    for name, packet in _all_packets().items():
        for field in _REQUIRED_PACKET_FIELDS:
            assert field in packet, f"{name} missing {field}"


def test_each_platform_packet_safety_booleans_true():
    flags = (
        "no_live_call_performed", "no_credentials_read", "no_env_read",
        "no_account_binding_performed", "no_oauth_flow_performed",
        "no_token_exchange_performed", "no_posting_performed",
        "dry_run_contract_required", "live_gate_required",
        "duplicate_send_prevention_required", "pre_attempt_marker_required",
        "post_send_redacted_ledger_required", "no_retry_required",
        "redaction_verified",
    )
    for name, packet in _all_packets().items():
        for flag in flags:
            assert packet[flag] is True, f"{name}:{flag}"
        assert packet["gate"] == gate.GATE
        assert packet["status"] == "pass"
        assert packet["blocked_reasons"] == []


def test_each_platform_packet_has_official_docs_sources():
    for name, packet in _all_packets().items():
        sources = packet["official_docs_sources"]
        assert isinstance(sources, list) and sources, name
        for src in sources:
            for key in ("source_family", "title", "url_or_symbolic_ref",
                        "accessed_date", "access_status"):
                assert key in src, f"{name} source missing {key}"


def test_x_packet_forbids_oauth_and_adjacent_families():
    packet = gate.build_x_packet()
    forbidden = " ".join(packet["forbidden_now"]).lower()
    for term in ("oauth", "token exchange", "post", "repost", "quote",
                 "bookmark"):
        assert term in forbidden, term
    assert packet["recommended_next_task_for_platform"] == gate.NEXT_TASK_X


def test_linkedin_packet_flags_version_deprecation():
    packet = gate.build_linkedin_packet()
    blob = (" ".join(packet["caveats"]) + " "
            + " ".join(packet["blockers"])).lower()
    assert "version" in blob
    assert "sunset" in blob or "deprecat" in blob
    assert packet["recommended_next_task_for_platform"] == \
        gate.NEXT_TASK_LINKEDIN


def test_telegram_packet_is_requirements_only_no_send():
    packet = gate.build_telegram_packet()
    forbidden = " ".join(packet["forbidden_now"]).lower()
    assert "sendmessage" in forbidden
    assert "credential read" in forbidden
    assert packet["recommended_next_task_for_platform"] == \
        gate.NEXT_TASK_TELEGRAM


# --------------------------------------------------------------------------- #
# Index packet
# --------------------------------------------------------------------------- #
def test_index_packet_references_three_platform_packets():
    out = gate.run_policy_gate(write=False)
    refs = out["platform_packets"]
    assert set(refs.keys()) == {"telegram_third_gate", "x", "linkedin"}


def test_index_packet_inherits_blocked_posture():
    index = gate.build_index_packet(
        telegram_checksum="a", x_checksum="b", linkedin_checksum="c",
        status="pass", blocked_reasons=[])
    posture = index["inherited_operator_posture_from_0174CT"]
    assert posture["live_posting_state"] == \
        "blocked_until_new_explicit_task_and_operator_go"
    assert posture["pause_additional_live_sends"] is True
    assert posture["two_telegram_pilots_review_required"] is True


def test_index_packet_checksums_match_platform_packets():
    out = gate.run_policy_gate(write=False)
    checks = out["packet_checksums"]
    assert checks["telegram_third_gate_requirements_packet"] == \
        gate.compute_checksum(gate.build_telegram_packet())
    assert checks["x_account_binding_requirements_packet"] == \
        gate.compute_checksum(gate.build_x_packet())
    assert checks["linkedin_account_binding_requirements_packet"] == \
        gate.compute_checksum(gate.build_linkedin_packet())
    assert checks["index_packet"]


def test_summary_priority_recommends_x_then_linkedin_then_telegram():
    out = gate.run_policy_gate(write=False)
    assert out["platform_priority_recommendation"] == [
        "x_requirements_no_live",
        "linkedin_requirements_no_live",
        "telegram_third_gate_later",
    ]
    assert out["next_recommended_task"] == gate.NEXT_TASK_X


# --------------------------------------------------------------------------- #
# Redaction scanner
# --------------------------------------------------------------------------- #
def test_redaction_scanner_blocks_token_like_value():
    bad = {"x": "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ0123456789ab"}
    assert any(v.startswith("secret_like_value")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_scanner_blocks_raw_telegram_bot_url():
    bad = {"x": "https://api.telegram.org/botXXXX/sendMessage"}
    assert any(v.startswith("telegram_url")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_scanner_blocks_raw_handle():
    bad = {"x": "follow @capitalchronicle today"}
    assert any(v.startswith("raw_handle")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_scanner_blocks_long_numeric_id():
    bad = {"x": "chat is -1001234567890 here"}
    assert any(v.startswith("long_digits_possible_id")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_scanner_blocks_linkedin_urn():
    bad = {"x": "owner is urn:li:organization:12345"}
    assert any(v.startswith("linkedin_urn")
               for v in gate.scan_packet_for_leaks(bad))


def test_redaction_scanner_blocks_forbidden_raw_keys():
    for k in gate._FORBIDDEN_KEYS:
        bad = {k: "whatever"}
        assert any(v == f"forbidden_key:{k}"
                   for v in gate.scan_packet_for_leaks(bad)), k


def test_all_packets_pass_redaction_scan():
    for packet in _all_packets().values():
        assert gate.scan_packet_for_leaks(packet) == []
    index = gate.build_index_packet(
        telegram_checksum="a" * 64, x_checksum="b" * 64,
        linkedin_checksum="c" * 64, status="pass", blocked_reasons=[])
    assert gate.scan_packet_for_leaks(index) == []


def test_official_docs_urls_are_token_free():
    for packet in _all_packets().values():
        for src in packet["official_docs_sources"]:
            url = src["url_or_symbolic_ref"]
            assert gate.scan_packet_for_leaks({"url_or_symbolic_ref": url}) \
                == [], url


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #
def test_deterministic_serialization():
    packet = gate.build_x_packet()
    s1 = gate.serialize(packet)
    s2 = gate.serialize(packet)
    assert s1 == s2
    assert s1.endswith("\n")
    import json
    parsed = json.loads(s1)
    assert list(parsed.keys()) == sorted(parsed.keys())


# --------------------------------------------------------------------------- #
# No network / no env imports (static source analysis)
# --------------------------------------------------------------------------- #
def _module_source():
    with open(gate.__file__, "r", encoding="utf-8") as fh:
        return fh.read()


def test_module_has_no_network_imports():
    tree = ast.parse(_module_source())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imported.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.add(node.module.split(".")[0])
    for forbidden in ("urllib", "requests", "httpx", "socket", "http",
                      "dotenv"):
        assert forbidden not in imported, forbidden


def test_module_has_no_env_reads():
    src = _module_source()
    assert "os.environ" not in src
    assert "os.getenv" not in src
    assert "getenv" not in src


def test_module_imports_only_allowed_stdlib():
    tree = ast.parse(_module_source())
    top = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                top.add(n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                top.add(node.module.split(".")[0])
    allowed = {"hashlib", "json", "os", "re", "sys"}
    assert top <= allowed, top - allowed


# --------------------------------------------------------------------------- #
# CLI dispatch
# --------------------------------------------------------------------------- #
def test_cli_main_runs_and_is_local(capsys):
    rc = gate.main(argv=[])
    assert rc == 0
    out = capsys.readouterr().out
    assert gate.GATE in out
    assert "blocked_until_new_explicit_task_and_operator_go" in out
