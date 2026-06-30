import json
import re
from dataclasses import asdict
from pathlib import Path

from live_contentops.discord_final_pre_live_release_readiness_v6 import *


def _prep():
    data = {
        "schema_version": "6.0.0",
        "task_label": UPSTREAM_TASK_LABEL,
        "discord_explicit_live_pilot_gate_prep_id": "prep_abc",
        "discord_live_capable_supervised_pilot_adapter_id": "adapter_abc",
        "discord_heavy_local_pre_live_batch_id": "heavy_abc",
        "eligible_for_future_operator_go_live_task": True,
        "max_request_count": 1,
        "max_retries": 0,
        "hidden_retry_allowed": False,
        "blockers": [],
    }
    for flag in FALSE_FLAGS:
        data[flag] = False
    for flag in TRUE_PREP_FLAGS:
        data[flag] = True
    return data


def _decl():
    prep = _prep()
    data = {
        "schema_version": "6.0.0",
        "discord_final_pre_live_release_readiness_declaration_id": "ready_decl_abc",
        "operator_id": "jim",
        "created_at_manual": "2026-06-30T08:00:00+07:00",
        "discord_explicit_live_pilot_gate_prep_id": prep["discord_explicit_live_pilot_gate_prep_id"],
        "discord_live_capable_supervised_pilot_adapter_id": prep["discord_live_capable_supervised_pilot_adapter_id"],
        "discord_heavy_local_pre_live_batch_id": prep["discord_heavy_local_pre_live_batch_id"],
        "platform": "discord",
        "readiness_mode": READINESS_MODE,
        "readiness_kind": READINESS_KIND,
        "operator_readiness_decision": "approve_final_pre_live_release_readiness_for_future_explicit_live_send_task_only",
        "declaration_decision": "mark_discord_final_pre_live_release_readiness_ready",
        "approval_phrase": APPROVAL_PHRASE,
        "approval_scope": APPROVAL_SCOPE,
        "notes": "",
    }
    for flag in FALSE_FLAGS:
        data[flag] = False
    for flag in TRUE_DECL_FLAGS:
        data[flag] = True
    return data


def test_valid_packet_future_task_only_and_deterministic():
    p = make_discord_final_pre_live_release_readiness_packet(_prep(), _decl())
    data = asdict(p)
    assert p.task_label == TASK_LABEL
    assert p.eligible_for_future_explicit_live_send_task is True
    assert p.eligible_for_live_send_now is False
    assert p.live_send_now is False
    assert p.dispatch_allowed is False
    assert p.publication_ready is False
    assert p.runtime_truth is False
    assert p.env_read_now is False and p.credential_value_read_now is False
    assert p.network_call_now is False and p.browser_session_now is False
    assert p.executable_request_created_now is False
    assert all(data["future_live_send_task_requirements"].values())
    assert p.packet_sha256 == make_discord_final_pre_live_release_readiness_packet(_prep(), _decl()).packet_sha256


def test_prep_packet_unavailable_or_false_live_safety_fields_fail_closed():
    prep = _prep(); prep["eligible_for_future_operator_go_live_task"] = False
    assert "prep_future_operator_go_not_true" in make_discord_final_pre_live_release_readiness_packet(prep, _decl()).blockers
    for flag in TRUE_PREP_FLAGS:
        prep = _prep(); prep[flag] = False
        assert f"prep_{flag}_not_true" in make_discord_final_pre_live_release_readiness_packet(prep, _decl()).blockers
    prep = _prep(); prep["blockers"] = ["x"]
    assert "prep_blockers_not_empty" in make_discord_final_pre_live_release_readiness_packet(prep, _decl()).blockers


def test_missing_docs_hygiene_booleans_fail_closed():
    for flag in ("docs_hygiene_reviewed", "docs_bom_removed", "docs_literal_backtick_n_removed", "evidence_chain_consolidated", "future_live_task_template_created"):
        decl = _decl(); decl[flag] = False
        assert f"declaration_{flag}_not_true" in make_discord_final_pre_live_release_readiness_packet(_prep(), decl).blockers


def test_no_env_network_browser_api_send_artifact_and_endpoint_flags_fail_closed():
    for flag in FALSE_FLAGS:
        prep = _prep(); prep[flag] = True
        assert f"prep_{flag}_not_false" in make_discord_final_pre_live_release_readiness_packet(prep, _decl()).blockers
        decl = _decl(); decl[flag] = True
        assert f"declaration_{flag}_not_false" in make_discord_final_pre_live_release_readiness_packet(_prep(), decl).blockers


def test_budget_publication_dispatch_runtime_and_future_requirements_fail_closed():
    for key, value, blocker in (("max_request_count", 2, "prep_max_request_count_not_one"), ("max_retries", 1, "prep_max_retries_not_zero"), ("hidden_retry_allowed", True, "prep_hidden_retry_allowed_not_false")):
        prep = _prep(); prep[key] = value
        assert blocker in make_discord_final_pre_live_release_readiness_packet(prep, _decl()).blockers
    for flag in TRUE_DECL_FLAGS:
        decl = _decl(); decl[flag] = False
        assert f"declaration_{flag}_not_true" in make_discord_final_pre_live_release_readiness_packet(_prep(), decl).blockers


def test_reject_defer_extra_and_forbidden_content_fail_closed():
    for key in ("operator_readiness_decision", "declaration_decision"):
        for val in ("reject", "defer"):
            decl = _decl(); decl[key] = val
            assert make_discord_final_pre_live_release_readiness_packet(_prep(), decl).eligible_for_future_explicit_live_send_task is False
    decl = _decl(); decl["extra"] = "x"
    assert "declaration_extra_fields" in make_discord_final_pre_live_release_readiness_packet(_prep(), decl).blockers
    for txt in ("send now", "financial advice", "signal service", "fake readiness", "public URL"):
        decl = _decl(); decl["notes"] = txt
        try:
            make_discord_final_pre_live_release_readiness_packet(_prep(), decl)
        except ValueError as exc:
            assert "forbidden_text" in str(exc)
        else:
            raise AssertionError("expected ValueError")
    decl = _decl(); decl["notes"] = "https://discord.com/api/webhooks/x/y"
    try:
        make_discord_final_pre_live_release_readiness_packet(_prep(), decl)
    except ValueError as exc:
        assert "forbidden_value" in str(exc) and "discord.com" not in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_static_no_env_network_request_imports_or_executable_patterns():
    src = Path("live_contentops/discord_final_pre_live_release_readiness_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$", r"getenv", r"environ", r"dotenv", r"requests", r"urllib", r"httpx", r"webbrowser", r"selenium", r"playwright", r"discord(?:app)?\.com/api/webhooks", r"requests\.post", r"fetch\(", r"curl ", r"Authorization", r"Content-Type"]:
        assert re.search(pat, src, re.M | re.I) is None, pat


def test_docs_hygiene_and_runbooks_no_send():
    paths = [
        "docs/automation/V6_DISCORD_EXPLICIT_LIVE_PILOT_GATE_PREP_HEAVY_BATCH_NO_SEND/discord_explicit_live_pilot_gate_prep_contract.md",
        "docs/automation/V6_DISCORD_EXPLICIT_LIVE_PILOT_GATE_PREP_HEAVY_BATCH_NO_SEND/implementation_report.md",
        "docs/runbooks/V6_DISCORD_EXPLICIT_LIVE_PILOT_OPERATOR_GO_TEMPLATE_NO_SEND.md",
        "docs/automation/V6_DISCORD_LIVE_CAPABLE_SUPERVISED_PILOT_ADAPTER_HEAVY_BATCH_NO_LIVE_SEND/discord_live_capable_supervised_pilot_adapter_contract.md",
        "docs/runbooks/V6_DISCORD_SUPERVISED_LIVE_PILOT_OPERATOR_RUNBOOK_NO_LIVE_SEND.md",
        "docs/runbooks/V6_DISCORD_FUTURE_LIVE_SEND_TASK_TEMPLATE_REQUIREMENTS_NO_SEND.md",
        "docs/automation/V6_DISCORD_FINAL_PRE_LIVE_RELEASE_AND_OPERATOR_GO_READINESS_HEAVY_BATCH_NO_SEND/implementation_report.md",
        "docs/automation/V6_DISCORD_FINAL_PRE_LIVE_RELEASE_AND_OPERATOR_GO_READINESS_HEAVY_BATCH_NO_SEND/discord_final_pre_live_release_readiness_contract.md",
    ]
    for path in paths:
        raw = Path(path).read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), path
        text = raw.decode("utf-8")
        assert "`n" not in text, path
    tpl = Path("docs/runbooks/V6_DISCORD_FUTURE_LIVE_SEND_TASK_TEMPLATE_REQUIREMENTS_NO_SEND.md").read_text(encoding="utf-8").lower()
    assert "no live send" in tpl and "separate explicit live task required" in tpl
    assert "curl " not in tpl and "fetch(" not in tpl and "http method" not in tpl


def test_cli_deterministic_output(tmp_path):
    prep = tmp_path / "prep.json"
    decl = tmp_path / "decl.json"
    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"
    prep.write_text(json.dumps(_prep()), encoding="utf-8")
    decl.write_text(json.dumps(_decl()), encoding="utf-8")
    assert main(["--input-prep-packet", str(prep), "--operator-readiness-declaration", str(decl), "--output", str(out1)]) == 0
    assert main(["--input-prep-packet", str(prep), "--operator-readiness-declaration", str(decl), "--output", str(out2)]) == 0
    a = json.loads(out1.read_text(encoding="utf-8")); b = json.loads(out2.read_text(encoding="utf-8"))
    assert a == b
    assert a["eligible_for_future_explicit_live_send_task"] is True
    assert a["eligible_for_live_send_now"] is False
