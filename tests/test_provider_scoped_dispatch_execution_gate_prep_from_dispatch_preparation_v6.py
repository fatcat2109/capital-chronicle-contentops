import ast,json
from dataclasses import asdict
from pathlib import Path
from live_contentops.provider_scoped_dispatch_execution_gate_prep_from_dispatch_preparation_v6 import *
from live_contentops.dispatch_execution_preparation_gate_from_redacted_audit_kill_switch_manual_fallback_v6 import make_dispatch_execution_preparation_gate_bundle
from tests.test_dispatch_execution_preparation_gate_from_redacted_audit_kill_switch_manual_fallback_v6 import _valid as _prep_valid
SAMPLE=Path('docs/automation/V6_DISPATCH_EXECUTION_PREPARATION_GATE_FROM_REDACTED_AUDIT_KILL_SWITCH_MANUAL_FALLBACK_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_dispatch_execution_preparation_gate_bundle.json')
def _default(): return json.loads(SAMPLE.read_text(encoding='utf-8'))
def _valid(): return asdict(make_dispatch_execution_preparation_gate_bundle(_prep_valid()))
def _gate(u=None): return make_provider_scoped_dispatch_execution_gate_prep_bundle(_valid() if u is None else u)
def test_default_committed_upstream_sample_blocked_no_provider_scope_prep():
    b=_gate(_default()); assert b.provider_scoped_dispatch_execution_gate_prep_status=='blocked_invalid_dispatch_execution_preparation_or_provider_scope_prep'; assert b.provider_scoped_dispatch_execution_gate_prep_records==[]; assert b.eligible_for_future_official_provider_docs_scope_gate_task is False; assert b.eligible_for_future_provider_scoped_dispatch_execution_task is False; assert b.dispatch_allowed is False and b.live_send_allowed is False
def test_valid_all_present_emits_non_executable_provider_scope_prep_only():
    b=_gate(); s=json.dumps(asdict(b)); assert b.provider_scoped_dispatch_execution_gate_prep_status==GATE_STATUS; assert b.eligible_for_future_official_provider_docs_scope_gate_task is True; assert b.eligible_for_future_provider_scoped_dispatch_execution_task is False and b.eligible_for_future_dispatch_execution_task is False and b.eligible_for_live_send_now is False; assert len(b.provider_scoped_dispatch_execution_gate_prep_records)==3
    assert b.all_required_provider_scope_prep_records_available and b.official_provider_docs_gate_required_later and b.endpoint_allowlist_gate_required_later and b.credential_hydration_gate_required_later and b.exact_payload_rehydration_gate_required_later and b.final_operator_go_required_later and b.redacted_runtime_audit_required_later and b.manual_fallback_required_later and b.kill_switch_required_later
    assert 'fake-secret-value' not in s and 'payload body content' not in s.lower()
    for r in b.provider_scoped_dispatch_execution_gate_prep_records:
        assert r['provider_scoped_gate_prep_mode']==GATE_PREP_MODE and r['provider_scoped_gate_prep_status']==GATE_PREP_STATUS; assert r['provider_scope_symbolic_only'] is True and r['non_executable_provider_scope_prep'] is True
        for f in FALSE_FLAGS: assert r[f] is False, f
def test_malformed_non_object_upstream_and_cli(tmp_path):
    assert 'dispatch_execution_preparation_gate_bundle_not_object' in _gate([]).blockers
    inp=tmp_path/'in.json'; out=tmp_path/'out.json'; inp.write_text('[]',encoding='utf-8'); assert main(['--dispatch-execution-preparation-gate-bundle',str(inp),'--output',str(out)])==1
    assert json.loads(out.read_text(encoding='utf-8'))['eligible_for_future_official_provider_docs_scope_gate_task'] is False
def test_upstream_bundle_fail_closed_cases():
    cases=[('task_label','WRONG','dispatch_execution_preparation_gate_bundle_task_label_invalid'),('schema_version','5.0.0','dispatch_execution_preparation_gate_bundle_schema_version_invalid'),('dispatch_execution_preparation_gate_status','WRONG','dispatch_execution_preparation_gate_bundle_status_invalid'),('eligible_for_future_provider_scoped_dispatch_execution_task',False,'dispatch_execution_preparation_gate_bundle_provider_scoped_eligibility_not_true'),('eligible_for_future_dispatch_execution_task',True,'dispatch_execution_preparation_gate_bundle_eligible_for_future_dispatch_execution_task_not_false'),('eligible_for_live_send_now',True,'dispatch_execution_preparation_gate_bundle_eligible_for_live_send_now_not_false'),('dispatch_allowed',True,'dispatch_execution_preparation_gate_bundle_dispatch_allowed_not_false'),('live_send_allowed',True,'dispatch_execution_preparation_gate_bundle_live_send_allowed_not_false'),('publication_ready',True,'dispatch_execution_preparation_gate_bundle_publication_ready_not_false'),('runtime_truth',True,'dispatch_execution_preparation_gate_bundle_runtime_truth_not_false'),('provider_call_made',True,'dispatch_execution_preparation_gate_bundle_provider_call_made_not_false'),('network_call_made',True,'dispatch_execution_preparation_gate_bundle_network_call_made_not_false'),('browser_session_used',True,'dispatch_execution_preparation_gate_bundle_browser_session_used_not_false'),('executable_request_artifact_created',True,'dispatch_execution_preparation_gate_bundle_executable_request_artifact_created_not_false')]
    for k,v,blk in cases:
        u=_valid(); u[k]=v; assert blk in _gate(u).blockers
    u=_valid(); u['dispatch_execution_preparation_records']=[]; assert 'dispatch_execution_preparation_records_missing' in _gate(u).blockers
def test_record_fail_closed_cases():
    cases=[('non_executable_preparation_record',False,'dispatch_preparation_record_executable_marker_invalid'),('approved_payload_hash','abc','dispatch_preparation_record_approved_payload_hash_invalid'),('symbolic_destination_binding_id','realish','dispatch_preparation_record_symbolic_destination_binding_id_invalid'),('symbolic_credential_handle_id','realish','dispatch_preparation_record_symbolic_credential_handle_id_invalid'),('approved_payload_preview_id','','dispatch_preparation_record_approved_payload_preview_id_empty'),('required_env_key_name','BAD_KEY','dispatch_preparation_record_key_not_allowlisted'),('provider_family_label','bad endpoint','dispatch_preparation_record_provider_family_label_invalid'),('dispatch_method_family_label','bad method','dispatch_preparation_record_method_family_label_invalid')]
    for k,v,blk in cases:
        u=_valid(); u['dispatch_execution_preparation_records'][0][k]=v; assert any(blk in x for x in _gate(u).blockers), (k,_gate(u).blockers)
def test_unsafe_flags_fail_closed():
    for k in ['provider_call_made','network_call_made','browser_session_used','dispatch_allowed','live_send_allowed','executable_request_artifact_created','endpoint_url_present','webhook_url_present','channel_id_present','account_id_present','token_present','payload_body_present','public_url_created','metrics_created']:
        u=_valid(); u['dispatch_execution_preparation_records'][0][k]=True; b=_gate(u); assert b.eligible_for_future_official_provider_docs_scope_gate_task is False; assert b.provider_scoped_dispatch_execution_gate_prep_records==[]; assert any(k in x for x in b.blockers)
def test_forbidden_text_no_echo_and_injected_values_not_serialized():
    terms=('endpoint','webhook','token','channel','account','https://example.invalid/x','metrics','browser profile','provider config','secret file','env line','credential value','env value','public url','payload body','live-send','executable request','curl','fetch','requests','http method','url path','retry policy','request budget','timeout','scheduler','queue','background worker','live button')
    for term in terms:
        u=_valid(); u['dispatch_execution_preparation_records'][0]['platform']=term; b=_gate(u); assert any('forbidden_' in x for x in b.blockers); assert term not in ' '.join(b.blockers)
    u=_valid(); u['dispatch_execution_preparation_records'][0]['warnings']=['fake-secret-value','payload body content']; s=json.dumps(asdict(_gate(u))).lower(); assert 'fake-secret-value' not in s and 'payload body content' not in s
def test_flags_false_every_case():
    for b in [_gate(), _gate(_default())]:
        for f in ['credential_value_read','credential_value_stored','credential_value_logged','env_read','dotenv_read','env_iterated','provider_call_made','network_call_made','browser_session_used','executable_request_artifact_created','endpoint_url_present','webhook_url_present','channel_id_present','account_id_present','token_present','payload_body_present','public_url_created','metrics_created','publication_ready','dispatch_allowed','live_send_allowed','runtime_truth','eligible_for_future_provider_scoped_dispatch_execution_task','eligible_for_future_dispatch_execution_task','eligible_for_live_send_now']:
            assert getattr(b,f) is False, f
def test_static_no_env_provider_network_browser_payload_body_or_runtime_strings():
    src=Path('live_contentops/provider_scoped_dispatch_execution_gate_prep_from_dispatch_preparation_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
    for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ','payload_file','payload_path','read_bytes(','retry policy','request budget','timeout','background worker','live button','scheduler','queue']: assert bad not in low, bad
def test_docs_sample_hygiene():
    base=Path('docs/automation/V6_PROVIDER_SCOPED_DISPATCH_EXECUTION_GATE_PREP_FROM_DISPATCH_PREPARATION_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE')
    paths=[base/'implementation_report.md',base/'provider_scoped_dispatch_execution_gate_prep_contract.md',base/'sample_provider_scoped_dispatch_execution_gate_prep_bundle.json',Path('docs/runbooks/V6_PROVIDER_SCOPED_DISPATCH_EXECUTION_GATE_PREP_OPERATOR_RUNBOOK_NO_PROVIDER_NO_DISPATCH_NO_LIVE.md')]
    for p in paths:
        raw=p.read_bytes(); assert not raw.startswith(b'\xef\xbb\xbf'), p; txt=raw.decode('utf-8'); assert '`n' not in txt
        for bad in ['https://','discord.com/api','api/webhooks','Bearer ','fake-secret-value','payload body content','public url','metrics endpoint','webhook url','endpoint url','channel id','account id','token value','retry policy','request budget','timeout']: assert bad.lower() not in txt.lower(), (p,bad)
    d=json.loads(paths[2].read_text(encoding='utf-8')); assert d['provider_scoped_dispatch_execution_gate_prep_status']=='blocked_invalid_dispatch_execution_preparation_or_provider_scope_prep'; assert d['eligible_for_future_official_provider_docs_scope_gate_task'] is False
