import ast,json
from dataclasses import asdict
from pathlib import Path
from live_contentops.official_provider_docs_scope_gate_from_provider_scoped_prep_v6 import *
from live_contentops.provider_scoped_dispatch_execution_gate_prep_from_dispatch_preparation_v6 import make_provider_scoped_dispatch_execution_gate_prep_bundle
from live_contentops.dispatch_execution_preparation_gate_from_redacted_audit_kill_switch_manual_fallback_v6 import make_dispatch_execution_preparation_gate_bundle
from tests.test_dispatch_execution_preparation_gate_from_redacted_audit_kill_switch_manual_fallback_v6 import _valid as _dispatch_valid
SAMPLE=Path('docs/automation/V6_PROVIDER_SCOPED_DISPATCH_EXECUTION_GATE_PREP_FROM_DISPATCH_PREPARATION_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_provider_scoped_dispatch_execution_gate_prep_bundle.json')
def _default(): return json.loads(SAMPLE.read_text(encoding='utf-8'))
def _valid(): return asdict(make_provider_scoped_dispatch_execution_gate_prep_bundle(asdict(make_dispatch_execution_preparation_gate_bundle(_dispatch_valid()))))
def _gate(u=None,d=None): return make_official_provider_docs_scope_gate_bundle(_valid() if u is None else u, official_docs_fixture() if d is None else d)
def test_default_sample_blocked():
 b=_gate(_default()); assert b.official_provider_docs_scope_gate_status=='blocked_invalid_provider_scope_prep_or_official_docs_scope'; assert b.official_provider_docs_scope_records==[]; assert b.eligible_for_future_endpoint_allowlist_gate_task is False; assert b.eligible_for_future_provider_runtime_authority_gate_task is False
def test_valid_synthetic_docs_scope_records_only():
 b=_gate(); s=json.dumps(asdict(b)); assert b.official_provider_docs_scope_gate_status==GATE_STATUS; assert b.eligible_for_future_endpoint_allowlist_gate_task is True; assert b.eligible_for_future_provider_runtime_authority_gate_task is False; assert b.eligible_for_future_provider_scoped_dispatch_execution_task is False; assert b.eligible_for_live_send_now is False; assert len(b.official_provider_docs_scope_records)==3
 assert b.official_provider_docs_authority_available is True and b.official_provider_docs_authority_unofficial_sources_used is False
 assert set(b.official_docs_provider_families)=={'discord_official_docs_scope','telegram_official_docs_scope'}; assert set(b.official_docs_source_ids)=={'discord_developer_docs_webhook_execute','telegram_bot_api_core_docs'}
 assert 'fake-secret-value' not in s and 'payload body content' not in s.lower()
 for r in b.official_provider_docs_scope_records:
  assert r['non_executable_docs_scope_record'] is True and r['provider_docs_scope_symbolic_only'] is True and r['official_docs_access_status']=='available'
  for f in FALSE_FLAGS: assert r[f] is False
def test_upstream_fail_closed_cases():
 cases=[('task_label','WRONG','task_label_invalid'),('schema_version','5','schema_version_invalid'),('provider_scoped_dispatch_execution_gate_prep_status','WRONG','status_invalid'),('eligible_for_future_official_provider_docs_scope_gate_task',False,'docs_eligibility_not_true'),('eligible_for_future_provider_runtime_authority_gate_task',True,'provider_runtime_authority_gate_task_not_false'),('eligible_for_future_provider_scoped_dispatch_execution_task',True,'provider_scoped_dispatch_execution_task_not_false'),('eligible_for_future_dispatch_execution_task',True,'future_dispatch_execution_task_not_false'),('eligible_for_live_send_now',True,'live_send_now_not_false'),('dispatch_allowed',True,'dispatch_allowed_not_false'),('live_send_allowed',True,'live_send_allowed_not_false'),('publication_ready',True,'publication_ready_not_false'),('runtime_truth',True,'runtime_truth_not_false'),('provider_call_made',True,'provider_call_made_not_false'),('network_call_made',True,'network_call_made_not_false'),('browser_session_used',True,'browser_session_used_not_false'),('executable_request_artifact_created',True,'executable_request_artifact_created_not_false')]
 for k,v,frag in cases:
  u=_valid(); u[k]=v; assert any(frag in x for x in _gate(u).blockers), (k,_gate(u).blockers)
 u=_valid(); u['provider_scoped_dispatch_execution_gate_prep_records']=[]; assert 'provider_scope_prep_records_missing' in _gate(u).blockers
def test_docs_fixture_fail_closed_cases():
 d=official_docs_fixture(False); assert any('unavailable' in x for x in _gate(d=d).blockers)
 d=official_docs_fixture(True, True); assert any('unofficial_source_used' in x for x in _gate(d=d).blockers)
 u=_valid(); u['provider_scoped_dispatch_execution_gate_prep_records'][0]['provider_family_label']='unknown_future_provider_lane'; assert any('provider_family_invalid' in x or 'unknown_provider' in x for x in _gate(u).blockers)
 d=official_docs_fixture(); d['discord_future_provider_lane']['official_docs_page_label']='bad endpoint'; assert any('forbidden_' in x or 'page_label_unsafe' in x for x in _gate(d=d).blockers)
def test_record_fail_closed_cases():
 cases=[('non_executable_provider_scope_prep',False,'executable_marker_invalid'),('approved_payload_hash','abc','approved_payload_hash_invalid'),('symbolic_destination_binding_id','real','symbolic_destination_binding_id_invalid'),('symbolic_credential_handle_id','real','symbolic_credential_handle_id_invalid'),('approved_payload_preview_id','','preview_id_empty'),('required_env_key_name','BAD','key_not_allowlisted'),('provider_family_label','bad endpoint','provider_family_invalid'),('dispatch_method_family_label','bad','method_family_invalid')]
 for k,v,frag in cases:
  u=_valid(); u['provider_scoped_dispatch_execution_gate_prep_records'][0][k]=v; assert any(frag in x for x in _gate(u).blockers), (k,_gate(u).blockers)
def test_unsafe_flags_and_endpoint_artifact_fail_closed():
 for k in ['provider_call_made','network_call_made','browser_session_used','dispatch_allowed','live_send_allowed','executable_request_artifact_created','endpoint_url_present','webhook_url_present','channel_id_present','account_id_present','token_present','payload_body_present','public_url_created','metrics_created']:
  u=_valid(); u['provider_scoped_dispatch_execution_gate_prep_records'][0][k]=True; b=_gate(u); assert b.eligible_for_future_endpoint_allowlist_gate_task is False; assert any(k in x for x in b.blockers)
def test_forbidden_text_no_echo_and_injected_values_not_serialized():
 terms=('endpoint','webhook','token','channel','account','https://example.invalid/x','metrics','browser profile','provider config','secret file','env line','credential value','env value','public url','payload body','live-send','executable request','curl','fetch','requests','http method','url path','retry policy','request budget','timeout','scheduler','queue','background worker','live button')
 for term in terms:
  u=_valid(); u['provider_scoped_dispatch_execution_gate_prep_records'][0]['platform']=term; b=_gate(u); assert any('forbidden_' in x for x in b.blockers); assert term not in ' '.join(b.blockers)
 u=_valid(); u['provider_scoped_dispatch_execution_gate_prep_records'][0]['warnings']=['fake-secret-value','payload body content']; s=json.dumps(asdict(_gate(u))).lower(); assert 'fake-secret-value' not in s and 'payload body content' not in s
def test_flags_false_every_case():
 for b in [_gate(),_gate(_default())]:
  for f in ['credential_value_read','credential_value_stored','credential_value_logged','env_read','dotenv_read','env_iterated','provider_call_made','network_call_made','browser_session_used','executable_request_artifact_created','endpoint_url_present','webhook_url_present','channel_id_present','account_id_present','token_present','payload_body_present','public_url_created','metrics_created','publication_ready','dispatch_allowed','live_send_allowed','runtime_truth','eligible_for_future_provider_runtime_authority_gate_task','eligible_for_future_provider_scoped_dispatch_execution_task','eligible_for_future_dispatch_execution_task','eligible_for_live_send_now']:
   assert getattr(b,f) is False, f
def test_static_no_forbidden_runtime_code():
 src=Path('live_contentops/official_provider_docs_scope_gate_from_provider_scoped_prep_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
 for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','discord.py','telebot','telegram.ext','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ','payload_file','payload_path','read_bytes(','retry policy','request budget','timeout','background worker','live button','scheduler','queue']: assert bad not in low, bad
def test_docs_sample_hygiene():
 base=Path('docs/automation/V6_OFFICIAL_PROVIDER_DOCS_SCOPE_GATE_FROM_PROVIDER_SCOPED_PREP_HEAVY_BATCH_DOCS_ONLY_NO_PROVIDER_NO_DISPATCH_NO_LIVE')
 paths=[base/'implementation_report.md',base/'official_provider_docs_scope_gate_contract.md',base/'sample_official_provider_docs_scope_gate_bundle.json',Path('docs/runbooks/V6_OFFICIAL_PROVIDER_DOCS_SCOPE_GATE_OPERATOR_RUNBOOK_DOCS_ONLY_NO_PROVIDER_NO_DISPATCH_NO_LIVE.md')]
 for p in paths:
  raw=p.read_bytes(); assert not raw.startswith(b'\xef\xbb\xbf'); txt=raw.decode('utf-8'); assert '`n' not in txt
  for bad in ['https://','discord.com/api','api/webhooks','Bearer ','fake-secret-value','payload body content','public url','metrics endpoint','webhook url','endpoint url','channel id','account id','token value','retry policy','request budget','timeout']: assert bad.lower() not in txt.lower(), (p,bad)
 d=json.loads(paths[2].read_text(encoding='utf-8')); assert d['official_provider_docs_scope_gate_status']=='blocked_invalid_provider_scope_prep_or_official_docs_scope'; assert d['eligible_for_future_endpoint_allowlist_gate_task'] is False
