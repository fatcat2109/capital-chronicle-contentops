import ast,json
from dataclasses import asdict
from pathlib import Path
from live_contentops.dispatch_execution_preparation_gate_from_redacted_audit_kill_switch_manual_fallback_v6 import *
from live_contentops.redacted_audit_kill_switch_manual_fallback_gate_from_exact_operator_go_v6 import make_redacted_audit_kill_switch_manual_fallback_gate_bundle
from tests.test_redacted_audit_kill_switch_manual_fallback_gate_from_exact_operator_go_v6 import _valid as _exact_valid
SAMPLE=Path('docs/automation/V6_REDACTED_AUDIT_KILL_SWITCH_MANUAL_FALLBACK_GATE_FROM_EXACT_OPERATOR_GO_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_redacted_audit_kill_switch_manual_fallback_gate_bundle.json')
def _default(): return json.loads(SAMPLE.read_text(encoding='utf-8'))
def _valid(): return asdict(make_redacted_audit_kill_switch_manual_fallback_gate_bundle(_exact_valid()))
def _gate(u=None): return make_dispatch_execution_preparation_gate_bundle(_valid() if u is None else u)
def test_default_committed_upstream_sample_blocked_no_dispatch_preparation():
    b=_gate(_default()); assert b.dispatch_execution_preparation_gate_status=='blocked_invalid_redacted_audit_kill_switch_manual_fallback_or_preparation'; assert b.dispatch_execution_preparation_records==[]; assert b.eligible_for_future_provider_scoped_dispatch_execution_task is False; assert b.eligible_for_future_dispatch_execution_task is False; assert b.dispatch_allowed is False and b.live_send_allowed is False and b.publication_ready is False
def test_valid_all_present_emits_non_executable_preparation_only():
    b=_gate(); s=json.dumps(asdict(b)); assert b.dispatch_execution_preparation_gate_status==GATE_STATUS; assert b.eligible_for_future_provider_scoped_dispatch_execution_task is True; assert b.eligible_for_future_dispatch_execution_task is False and b.eligible_for_live_send_now is False; assert len(b.dispatch_execution_preparation_records)==3
    assert b.all_required_dispatch_execution_preparation_records_available and b.provider_scope_required_later and b.payload_rehydration_required_later and b.credential_hydration_required_later and b.destination_binding_required_later and b.final_operator_go_required_later
    assert 'fake-secret-value' not in s and 'payload body content' not in s.lower(); assert b.kill_switch_state==KILL_STATE and b.manual_fallback_state==FALLBACK_STATE
    for r in b.dispatch_execution_preparation_records:
        assert r['dispatch_preparation_mode']==PREP_MODE and r['dispatch_preparation_status']==PREP_STATUS and r['non_executable_preparation_record'] is True
        assert r['dispatch_method_family_label']=='future_provider_scoped_dispatch_method_required_later'; assert r['future_provider_scope_required'] is True and r['human_review_required'] is True
        for f in FALSE_FLAGS: assert r[f] is False, f
def test_malformed_non_object_upstream_and_cli(tmp_path):
    assert 'redacted_audit_kill_switch_manual_fallback_gate_bundle_not_object' in _gate([]).blockers
    inp=tmp_path/'in.json'; out=tmp_path/'out.json'; inp.write_text('[]',encoding='utf-8'); assert main(['--redacted-audit-kill-switch-manual-fallback-gate-bundle',str(inp),'--output',str(out)])==1
    assert json.loads(out.read_text(encoding='utf-8'))['eligible_for_future_provider_scoped_dispatch_execution_task'] is False
def test_upstream_bundle_fail_closed_cases():
    cases=[('task_label','WRONG','redacted_audit_kill_switch_manual_fallback_gate_bundle_task_label_invalid'),('schema_version','5.0.0','redacted_audit_kill_switch_manual_fallback_gate_bundle_schema_version_invalid'),('redacted_audit_kill_switch_manual_fallback_gate_status','WRONG','redacted_audit_kill_switch_manual_fallback_gate_bundle_status_invalid'),('eligible_for_future_dispatch_execution_preparation_gate_task',False,'redacted_audit_kill_switch_manual_fallback_gate_bundle_preparation_eligibility_not_true')]
    for k,v,blk in cases:
        u=_valid(); u[k]=v; assert blk in _gate(u).blockers
    u=_valid(); u['redacted_audit_records']=[]; assert 'redacted_audit_records_missing' in _gate(u).blockers
    u=_valid(); u['kill_switch_records']=[]; assert 'kill_switch_records_missing' in _gate(u).blockers
    u=_valid(); u['manual_fallback_records']=[]; assert 'manual_fallback_records_missing' in _gate(u).blockers
def test_record_fail_closed_cases():
    audit_cases=[('approved_payload_hash','abc','redacted_audit_record_approved_payload_hash_invalid'),('symbolic_destination_binding_id','realish','redacted_audit_record_symbolic_destination_binding_id_invalid'),('symbolic_credential_handle_id','realish','redacted_audit_record_symbolic_credential_handle_id_invalid'),('approved_payload_preview_id','','redacted_audit_record_approved_payload_preview_id_empty'),('required_env_key_name','BAD_KEY','redacted_audit_record_key_not_allowlisted')]
    for k,v,blk in audit_cases:
        u=_valid(); u['redacted_audit_records'][0][k]=v; assert any(blk in x for x in _gate(u).blockers), (k,_gate(u).blockers)
    u=_valid(); u['kill_switch_records'][0]['kill_switch_state']='not_armed'; assert any('kill_switch_record_not_armed' in x for x in _gate(u).blockers)
    u=_valid(); u['manual_fallback_records'][0]['manual_fallback_available_for_operator']=False; assert any('manual_fallback_record_unavailable' in x for x in _gate(u).blockers)
def test_unsafe_flags_fail_closed():
    for section in ['redacted_audit_records','kill_switch_records','manual_fallback_records']:
        for k in ['provider_call_made','network_call_made','browser_session_used','dispatch_allowed','live_send_allowed','executable_request_artifact_created','endpoint_url_present','webhook_url_present','channel_id_present','account_id_present','token_present','payload_body_present','public_url_created','metrics_created']:
            u=_valid(); u[section][0][k]=True; b=_gate(u); assert b.eligible_for_future_provider_scoped_dispatch_execution_task is False; assert b.dispatch_execution_preparation_records==[]; assert any(k in x for x in b.blockers)
def test_forbidden_text_no_echo_and_injected_values_not_serialized():
    for term in ('endpoint','webhook','token','channel','account','https://example.invalid/x','metrics','browser profile','provider config','secret file','env line','credential value','env value','public url','payload body','live-send','executable request','curl','fetch','requests','http method','url path','retry policy','scheduler'):
        u=_valid(); u['redacted_audit_records'][0]['platform']=term; b=_gate(u); assert any('forbidden_' in x for x in b.blockers); assert term not in ' '.join(b.blockers)
    u=_valid(); u['redacted_audit_records'][0]['warnings']=['fake-secret-value','payload body content']; s=json.dumps(asdict(_gate(u))).lower(); assert 'fake-secret-value' not in s and 'payload body content' not in s
def test_flags_false_every_case():
    for b in [_gate(), _gate(_default())]:
        for f in ['credential_value_read','credential_value_stored','credential_value_logged','env_read','dotenv_read','env_iterated','provider_call_made','network_call_made','browser_session_used','executable_request_artifact_created','endpoint_url_present','webhook_url_present','channel_id_present','account_id_present','token_present','payload_body_present','public_url_created','metrics_created','publication_ready','dispatch_allowed','live_send_allowed','runtime_truth','eligible_for_future_dispatch_execution_task','eligible_for_live_send_now']:
            assert getattr(b,f) is False, f
def test_static_no_env_provider_network_browser_payload_body_reads():
    src=Path('live_contentops/dispatch_execution_preparation_gate_from_redacted_audit_kill_switch_manual_fallback_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
    for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ','payload_file','payload_path','read_bytes(','retry policy','background worker','live button']: assert bad not in low, bad
def test_docs_sample_hygiene():
    base=Path('docs/automation/V6_DISPATCH_EXECUTION_PREPARATION_GATE_FROM_REDACTED_AUDIT_KILL_SWITCH_MANUAL_FALLBACK_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE')
    paths=[base/'implementation_report.md',base/'dispatch_execution_preparation_gate_contract.md',base/'sample_dispatch_execution_preparation_gate_bundle.json',Path('docs/runbooks/V6_DISPATCH_EXECUTION_PREPARATION_GATE_OPERATOR_RUNBOOK_NO_PROVIDER_NO_DISPATCH_NO_LIVE.md')]
    for p in paths:
        raw=p.read_bytes(); assert not raw.startswith(b'\xef\xbb\xbf'), p; txt=raw.decode('utf-8'); assert '`n' not in txt
        for bad in ['https://','discord.com/api','api/webhooks','Bearer ','fake-secret-value','payload body content','public url','metrics endpoint','webhook url','endpoint url','channel id','account id','token value']: assert bad.lower() not in txt.lower(), (p,bad)
    d=json.loads(paths[2].read_text(encoding='utf-8')); assert d['dispatch_execution_preparation_gate_status']=='blocked_invalid_redacted_audit_kill_switch_manual_fallback_or_preparation'; assert d['eligible_for_future_provider_scoped_dispatch_execution_task'] is False
