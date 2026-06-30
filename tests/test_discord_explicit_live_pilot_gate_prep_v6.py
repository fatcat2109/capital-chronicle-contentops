import json
import re
from dataclasses import asdict
from pathlib import Path
from live_contentops.discord_explicit_live_pilot_gate_prep_v6 import *

def _adapter():
    return {"schema_version":"6.0.0","task_label":UPSTREAM_TASK_LABEL,"discord_live_capable_supervised_pilot_adapter_id":"adapter_abc","discord_heavy_local_pre_live_batch_id":"heavy_abc","platform":"discord","adapter_available":True,"adapter_declared_ready":True,"live_execution_enabled_now":False,"live_dispatch_approval_granted":False,"executable_request_artifact_created":False,"executable_request_artifact_creation_allowed":False,"webhook_value_read_allowed":False,"discord_api_call_allowed":False,"webhook_send_test_allowed":False,"browser_session_allowed":False,"env_read_allowed":False,"dot_env_read_allowed":False,"public_url_created":False,"metrics_created":False,"publication_ready":False,"dispatch_allowed":False,"requires_future_explicit_live_execution_task":True,"requires_exact_operator_confirmation_later":True,"future_live_execution_blockers":["future_explicit_live_execution_task_required","exact_operator_confirmation_required_later","credential_presence_membership_only_required_later","destination_binding_required_later","payload_hash_revalidation_required_later","kill_switch_required_later","redacted_audit_required_later","manual_fallback_required_later","live_dispatch_disabled_in_this_packet"],"blockers":[]}

def _decl():
    return {"schema_version":"6.0.0","discord_explicit_live_pilot_gate_prep_declaration_id":"prep_decl_abc","operator_id":"jim","created_at_manual":"2026-06-30T07:45:00+07:00","discord_live_capable_supervised_pilot_adapter_id":"adapter_abc","discord_heavy_local_pre_live_batch_id":"heavy_abc","platform":"discord","prep_mode":PREP_MODE,"prep_kind":PREP_KIND,"payload_preview_kind":PAYLOAD_PREVIEW_KIND,"payload_preview_contains_real_content":False,"payload_preview_hash":"a4d3b5b6307374eeaa27f6cfb08c903823790e668b5a1532822a16d8cfb08cb0","destination_binding_kind":DESTINATION_BINDING_KIND,"destination_binding_contains_channel_id":False,"destination_binding_contains_account_id":False,"destination_binding_contains_webhook_url":False,"credential_key_name":CREDENTIAL_KEY_NAME,"credential_presence_membership_only_planned":True,"credential_value_read_now":False,"env_read_now":False,"dot_env_read_now":False,"network_call_now":False,"browser_session_now":False,"executable_request_created_now":False,"live_send_now":False,"discord_api_call_now":False,"webhook_send_test_now":False,"endpoint_url_included":False,"webhook_url_included":False,"webhook_token_included":False,"channel_identity_included":False,"account_identity_included":False,"http_method_included":False,"http_path_included":False,"http_headers_included":False,"http_body_included":False,"curl_command_included":False,"fetch_or_http_client_code_included":False,"browser_instruction_included":False,"public_url_included":False,"metrics_included":False,"max_request_count":1,"timeout_seconds":15,"max_retries":0,"hidden_retry_allowed":False,"idempotency_required":True,"kill_switch_required":True,"redacted_audit_required":True,"manual_fallback_required":True,"exact_operator_go_phrase_required_later":True,"future_live_execution_task_required":True,"operator_prep_decision":"approve_explicit_live_pilot_gate_prep_for_future_operator_go_only","declaration_decision":"mark_discord_explicit_live_pilot_gate_prep_ready","approval_phrase":APPROVAL_PHRASE,"approval_scope":APPROVAL_SCOPE,"notes":""}

def test_valid_packet_future_go_only():
    p=make_discord_explicit_live_pilot_gate_prep_packet(_adapter(),_decl()); data=asdict(p)
    assert p.task_label==TASK_LABEL and p.eligible_for_future_operator_go_live_task is True
    assert p.eligible_for_live_send_now is False and p.live_send_now is False and p.dispatch_allowed is False and p.publication_ready is False and p.runtime_truth is False
    assert p.env_read_now is False and p.credential_value_read_now is False and p.network_call_now is False and p.browser_session_now is False and p.executable_request_created_now is False
    assert data["final_operator_go_packet_template"]["future_task_required"] is True
    assert p.packet_sha256 == make_discord_explicit_live_pilot_gate_prep_packet(_adapter(),_decl()).packet_sha256

def test_adapter_flags_and_missing_blockers_fail_closed():
    for flag in ("adapter_available","adapter_declared_ready"):
        a=_adapter(); a[flag]=False; assert make_discord_explicit_live_pilot_gate_prep_packet(a,_decl()).eligible_for_future_operator_go_live_task is False
    for flag in ("live_execution_enabled_now","discord_api_call_allowed","webhook_send_test_allowed","env_read_allowed","executable_request_artifact_created","public_url_created"):
        a=_adapter(); a[flag]=True; assert make_discord_explicit_live_pilot_gate_prep_packet(a,_decl()).eligible_for_future_operator_go_live_task is False
    a=_adapter(); a["future_live_execution_blockers"]=[]; assert "adapter_missing_future_live_execution_blockers" in make_discord_explicit_live_pilot_gate_prep_packet(a,_decl()).blockers

def test_credential_hash_decisions_extra_and_forbidden_text():
    d=_decl(); d["credential_key_name"]="OTHER"; assert "declaration_credential_key_name_invalid" in make_discord_explicit_live_pilot_gate_prep_packet(_adapter(),d).blockers
    d=_decl(); d["payload_preview_hash"]=""; assert "payload_preview_hash_missing" in make_discord_explicit_live_pilot_gate_prep_packet(_adapter(),d).blockers
    d=_decl(); d["payload_preview_hash"]="https://discord.com/api/webhooks/x/y"
    try: make_discord_explicit_live_pilot_gate_prep_packet(_adapter(),d)
    except ValueError as e: assert "forbidden_value" in str(e) and "discord.com" not in str(e)
    else: raise AssertionError("expected ValueError")
    for k,v in (("operator_prep_decision","reject"),("operator_prep_decision","defer"),("declaration_decision","reject"),("declaration_decision","defer")):
        d=_decl(); d[k]=v; assert make_discord_explicit_live_pilot_gate_prep_packet(_adapter(),d).eligible_for_future_operator_go_live_task is False
    d=_decl(); d["extra"]="x"; assert "declaration_extra_fields" in make_discord_explicit_live_pilot_gate_prep_packet(_adapter(),d).blockers
    for txt in ("send now","financial advice","signal service","fake readiness"):
        d=_decl(); d["notes"]=txt
        try: make_discord_explicit_live_pilot_gate_prep_packet(_adapter(),d)
        except ValueError as e: assert "forbidden_text" in str(e)
        else: raise AssertionError("expected ValueError")

def test_no_send_artifact_flags_budget_retry_timeout_and_required_booleans_fail_closed():
    flags=["destination_binding_contains_channel_id","destination_binding_contains_account_id","destination_binding_contains_webhook_url","credential_value_read_now","env_read_now","dot_env_read_now","network_call_now","browser_session_now","executable_request_created_now","live_send_now","discord_api_call_now","webhook_send_test_now","endpoint_url_included","webhook_url_included","webhook_token_included","channel_identity_included","account_identity_included","http_method_included","http_path_included","http_headers_included","http_body_included","curl_command_included","fetch_or_http_client_code_included","browser_instruction_included","public_url_included","metrics_included"]
    for f in flags:
        d=_decl(); d[f]=True; p=make_discord_explicit_live_pilot_gate_prep_packet(_adapter(),d); assert p.eligible_for_future_operator_go_live_task is False and f"declaration_{f}_not_false" in p.blockers
    for k,v,b in (("max_request_count",2,"max_request_count_not_one"),("max_retries",1,"max_retries_not_zero"),("hidden_retry_allowed",True,"declaration_hidden_retry_allowed_not_false"),("timeout_seconds",31,"timeout_seconds_out_of_range")):
        d=_decl(); d[k]=v; assert b in make_discord_explicit_live_pilot_gate_prep_packet(_adapter(),d).blockers
    for f in ("idempotency_required","kill_switch_required","redacted_audit_required","manual_fallback_required","exact_operator_go_phrase_required_later","future_live_execution_task_required"):
        d=_decl(); d[f]=False; assert f"declaration_{f}_not_true" in make_discord_explicit_live_pilot_gate_prep_packet(_adapter(),d).blockers

def test_static_guards_cli_runbook_and_utf8(tmp_path):
    src=Path("live_contentops/discord_explicit_live_pilot_gate_prep_v6.py").read_text(encoding="utf-8")
    for pat in [r"^import os$",r"getenv",r"environ",r"dotenv",r"requests",r"urllib",r"httpx",r"webbrowser",r"selenium",r"playwright",r"discord(?:app)?\.com/api/webhooks",r"requests\.post",r"fetch\(",r"curl "]:
        assert re.search(pat,src,re.M|re.I) is None, pat
    ap=tmp_path/"a.json"; dp=tmp_path/"d.json"; op=tmp_path/"o.json"; ap.write_text(json.dumps(_adapter()),encoding="utf-8"); dp.write_text(json.dumps(_decl()),encoding="utf-8")
    assert main(["--input-adapter-packet",str(ap),"--operator-prep-declaration",str(dp),"--output",str(op)])==0
    out=json.loads(op.read_text(encoding="utf-8")); assert out["eligible_for_future_operator_go_live_task"] is True and out["eligible_for_live_send_now"] is False
    text=Path("docs/runbooks/V6_DISCORD_EXPLICIT_LIVE_PILOT_OPERATOR_GO_TEMPLATE_NO_SEND.md").read_text(encoding="utf-8").lower(); assert "no live send" in text and "future operator go task required" in text
    for path in ["live_contentops/discord_explicit_live_pilot_gate_prep_v6.py","tests/test_discord_explicit_live_pilot_gate_prep_v6.py","docs/runbooks/V6_DISCORD_EXPLICIT_LIVE_PILOT_OPERATOR_GO_TEMPLATE_NO_SEND.md"]:
        raw=Path(path).read_bytes(); assert not raw.startswith(b"\xef\xbb\xbf"); raw.decode("utf-8")
