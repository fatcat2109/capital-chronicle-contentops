import ast,json
from dataclasses import asdict
from pathlib import Path
from live_contentops.redacted_audit_kill_switch_manual_fallback_gate_from_exact_operator_go_v6 import *
from tests.test_exact_operator_dispatch_go_gate_from_payload_hash_revalidation_v6 import _bundle as _exact_go_bundle
SAMPLE=Path('docs/automation/V6_EXACT_OPERATOR_DISPATCH_GO_GATE_FROM_PAYLOAD_HASH_REVALIDATION_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_exact_operator_dispatch_go_gate_bundle.json')
def _default(): return json.loads(SAMPLE.read_text(encoding='utf-8'))
def _valid(): return asdict(_exact_go_bundle())
def _gate(u=None): return make_redacted_audit_kill_switch_manual_fallback_gate_bundle(_valid() if u is None else u)
def test_default_committed_exact_go_sample_blocked_no_audit_ready():
    b=_gate(_default()); assert b.redacted_audit_kill_switch_manual_fallback_gate_status=='blocked_invalid_exact_operator_go_or_safety_envelope'; assert b.redacted_audit_records==[] and b.kill_switch_records==[] and b.manual_fallback_records==[]; assert b.eligible_for_future_dispatch_execution_preparation_gate_task is False; assert b.dispatch_allowed is False and b.live_send_allowed is False and b.publication_ready is False
def test_valid_all_present_emits_redacted_symbolic_only():
    b=_gate(); s=json.dumps(asdict(b)); assert b.redacted_audit_kill_switch_manual_fallback_gate_status==GATE_STATUS; assert b.eligible_for_future_dispatch_execution_preparation_gate_task is True; assert b.eligible_for_future_dispatch_execution_task is False and b.eligible_for_live_send_now is False
    assert len(b.redacted_audit_records)==3 and len(b.kill_switch_records)==3 and len(b.manual_fallback_records)==3; assert b.all_required_redacted_audit_records_available and b.all_required_kill_switch_records_available and b.all_required_manual_fallback_records_available
    assert b.kill_switch_state==KILL_STATE and b.manual_fallback_state==FALLBACK_STATE; assert 'fake-secret-value' not in s and 'payload body content' not in s.lower()
    for r in b.redacted_audit_records: assert r['redacted_audit_complete'] is True and r['redacted_audit_mode']=='local_audit_safe_metadata_only'
    for r in b.kill_switch_records: assert r['kill_switch_required'] is True and r['kill_switch_state']==KILL_STATE and r['dispatch_execution_still_not_allowed'] is True
    for r in b.manual_fallback_records: assert r['manual_fallback_required'] is True and r['manual_fallback_available_for_operator'] is True and r['manual_fallback_instructions_redacted'] is True
def test_malformed_non_object_upstream_and_cli(tmp_path):
    assert 'exact_operator_dispatch_go_gate_bundle_not_object' in _gate([]).blockers
    inp=tmp_path/'in.json'; out=tmp_path/'out.json'; inp.write_text('[]',encoding='utf-8'); assert main(['--exact-operator-dispatch-go-gate-bundle',str(inp),'--output',str(out)])==1
    assert json.loads(out.read_text(encoding='utf-8'))['eligible_for_future_dispatch_execution_preparation_gate_task'] is False
def test_upstream_bundle_fail_closed_cases():
    cases=[('task_label','WRONG','exact_operator_dispatch_go_gate_bundle_task_label_invalid'),('schema_version','5.0.0','exact_operator_dispatch_go_gate_bundle_schema_version_invalid'),('exact_operator_dispatch_go_gate_status','WRONG','exact_operator_dispatch_go_gate_bundle_status_invalid'),('operator_go_phrase_exact_match',False,'exact_operator_dispatch_go_gate_bundle_phrase_match_not_true'),('eligible_for_future_redacted_audit_kill_switch_manual_fallback_gate_task',False,'exact_operator_dispatch_go_gate_bundle_redacted_audit_eligibility_not_true')]
    for k,v,blk in cases:
        u=_valid(); u[k]=v; assert blk in _gate(u).blockers
    u=_valid(); u['exact_operator_dispatch_go_records']=[]; assert 'exact_operator_dispatch_go_gate_bundle_records_empty' in _gate(u).blockers
def test_upstream_record_fail_closed_cases():
    cases=[('operator_go_phrase_exact_match',False,'exact_operator_go_record_phrase_match_not_true'),('eligible_for_future_redacted_audit_kill_switch_manual_fallback_gate_task',False,'exact_operator_go_record_redacted_audit_eligibility_not_true'),('approved_payload_hash','abc','exact_operator_go_record_approved_payload_hash_invalid'),('symbolic_destination_binding_id','realish','exact_operator_go_record_symbolic_destination_binding_id_invalid'),('symbolic_credential_handle_id','realish','exact_operator_go_record_symbolic_credential_handle_id_invalid'),('approved_payload_preview_id','','exact_operator_go_record_approved_payload_preview_id_empty'),('required_env_key_name','BAD_KEY','exact_operator_go_record_key_not_allowlisted'),('provider_call_made',True,'exact_operator_go_record_provider_call_made_not_false'),('network_call_made',True,'exact_operator_go_record_network_call_made_not_false'),('browser_session_used',True,'exact_operator_go_record_browser_session_used_not_false'),('dispatch_allowed',True,'exact_operator_go_record_dispatch_allowed_not_false'),('live_send_allowed',True,'exact_operator_go_record_live_send_allowed_not_false')]
    for k,v,blk in cases:
        u=_valid(); u['exact_operator_dispatch_go_records'][0][k]=v; assert any(blk in x for x in _gate(u).blockers), (k, _gate(u).blockers)
def test_missing_kill_switch_and_manual_fallback_validation_helpers():
    u=_valid(); audit,kills,fallbacks=make_records(u); assert 'kill_switch_records_missing' in validate_output_records(audit,[],fallbacks); assert 'manual_fallback_records_missing' in validate_output_records(audit,kills,[])
    kills[0]['kill_switch_state']='not_armed'; assert any('kill_switch_0_not_armed'==x for x in validate_output_records(audit,kills,fallbacks))
    audit,kills,fallbacks=make_records(u); fallbacks[0]['manual_fallback_available_for_operator']=False; assert 'manual_fallback_0_unavailable' in validate_output_records(audit,kills,fallbacks)
def test_forbidden_text_no_echo_and_injected_values_not_serialized():
    for term in ('endpoint','webhook','token','channel','account','https://example.invalid/x','metrics','browser profile','provider config','secret file','env line','credential value','env value','public url','payload body','live-send','executable request','curl','fetch','requests'):
        u=_valid(); u['exact_operator_dispatch_go_records'][0]['platform']=term; b=_gate(u); assert any('forbidden_' in x for x in b.blockers); assert term not in ' '.join(b.blockers)
    u=_valid(); u['exact_operator_dispatch_go_records'][0]['warnings']=['fake-secret-value','payload body content']; s=json.dumps(asdict(_gate(u))).lower(); assert 'fake-secret-value' not in s and 'payload body content' not in s
def test_flags_false_every_case():
    for b in [_gate(), _gate(_default())]:
        for f in ['credential_value_read','credential_value_stored','credential_value_logged','env_read','dotenv_read','env_iterated','provider_call_made','network_call_made','browser_session_used','executable_request_artifact_created','endpoint_url_present','webhook_url_present','channel_id_present','account_id_present','token_present','payload_body_present','public_url_created','metrics_created','publication_ready','dispatch_allowed','live_send_allowed','runtime_truth','eligible_for_future_dispatch_execution_task','eligible_for_live_send_now']:
            assert getattr(b,f) is False, f
def test_static_no_env_provider_network_browser_payload_body_reads():
    src=Path('live_contentops/redacted_audit_kill_switch_manual_fallback_gate_from_exact_operator_go_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
    for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ','payload_file','payload_path','read_bytes(']: assert bad not in low, bad
def test_docs_sample_hygiene():
    base=Path('docs/automation/V6_REDACTED_AUDIT_KILL_SWITCH_MANUAL_FALLBACK_GATE_FROM_EXACT_OPERATOR_GO_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE')
    paths=[base/'implementation_report.md',base/'redacted_audit_kill_switch_manual_fallback_gate_contract.md',base/'sample_redacted_audit_kill_switch_manual_fallback_gate_bundle.json',Path('docs/runbooks/V6_REDACTED_AUDIT_KILL_SWITCH_MANUAL_FALLBACK_GATE_OPERATOR_RUNBOOK_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE.md')]
    for p in paths:
        raw=p.read_bytes(); assert not raw.startswith(b'\xef\xbb\xbf'), p; txt=raw.decode('utf-8'); assert '`n' not in txt
        for bad in ['https://','discord.com/api','api/webhooks','Bearer ','fake-secret-value','payload body content','public url','metrics endpoint']: assert bad.lower() not in txt.lower(), (p,bad)
    d=json.loads(paths[2].read_text(encoding='utf-8')); assert d['redacted_audit_kill_switch_manual_fallback_gate_status']=='blocked_invalid_exact_operator_go_or_safety_envelope'; assert d['eligible_for_future_dispatch_execution_preparation_gate_task'] is False
