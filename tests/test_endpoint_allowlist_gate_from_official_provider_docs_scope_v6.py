import ast,json
from dataclasses import asdict
from pathlib import Path
from live_contentops.endpoint_allowlist_gate_from_official_provider_docs_scope_v6 import *
from live_contentops.official_provider_docs_scope_gate_from_provider_scoped_prep_v6 import make_official_provider_docs_scope_gate_bundle, official_docs_fixture
from tests.test_official_provider_docs_scope_gate_from_provider_scoped_prep_v6 import _valid as _docs_valid
SAMPLE=Path('docs/automation/V6_OFFICIAL_PROVIDER_DOCS_SCOPE_GATE_FROM_PROVIDER_SCOPED_PREP_HEAVY_BATCH_DOCS_ONLY_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_official_provider_docs_scope_gate_bundle.json')
def _default(): return json.loads(SAMPLE.read_text(encoding='utf-8'))
def _valid(): return asdict(make_official_provider_docs_scope_gate_bundle(_docs_valid(), official_docs_fixture()))
def _gate(u=None): return make_endpoint_allowlist_gate_bundle(_valid() if u is None else u)
def test_default_sample_blocked():
 b=_gate(_default()); assert b.endpoint_allowlist_gate_status=='blocked_invalid_official_docs_scope_or_endpoint_allowlist'; assert b.endpoint_allowlist_records==[]; assert b.eligible_for_future_provider_runtime_authority_gate_task is False
def test_valid_synthetic_allowlist_records_only_and_mapping():
 b=_gate(); s=json.dumps(asdict(b)); assert b.endpoint_allowlist_gate_status==GATE_STATUS; assert b.eligible_for_future_provider_runtime_authority_gate_task is True; assert b.eligible_for_future_provider_scoped_dispatch_execution_task is False; assert b.eligible_for_live_send_now is False; assert len(b.endpoint_allowlist_records)==3
 assert set(b.sanitized_endpoint_operation_ids)=={'discord_execute_webhook_operation_required_later','telegram_send_message_operation_required_later','telegram_send_photo_operation_required_later','telegram_send_document_operation_required_later','telegram_send_media_group_operation_required_later'}
 for r in b.endpoint_allowlist_records:
  assert r['non_executable_endpoint_allowlist_record'] is True and r['endpoint_allowlist_symbolic_only'] is True and r['endpoint_operation_ids_sanitized'] is True
  assert r['raw_endpoint_values_present'] is False and r['raw_http_method_values_present'] is False and r['raw_url_path_values_present'] is False
  if r['provider_family_label']=='discord_future_provider_lane': assert r['sanitized_endpoint_operation_ids']==['discord_execute_webhook_operation_required_later']
  if r['provider_family_label']=='telegram_future_provider_lane': assert r['sanitized_endpoint_operation_ids']==['telegram_send_message_operation_required_later','telegram_send_photo_operation_required_later','telegram_send_document_operation_required_later','telegram_send_media_group_operation_required_later']
  for f in FALSE_FLAGS: assert r[f] is False
 assert 'fake-secret-value' not in s and 'payload body content' not in s.lower()
def test_upstream_fail_closed_cases():
 cases=[('task_label','WRONG','task_label_invalid'),('schema_version','5','schema_version_invalid'),('official_provider_docs_scope_gate_status','WRONG','status_invalid'),('eligible_for_future_endpoint_allowlist_gate_task',False,'endpoint_allowlist_eligibility_not_true'),('official_provider_docs_authority_available',False,'authority_unavailable'),('official_provider_docs_authority_unofficial_sources_used',True,'unofficial_sources_used_not_false'),('eligible_for_future_provider_runtime_authority_gate_task',True,'provider_runtime_authority_gate_task_not_false'),('eligible_for_future_provider_scoped_dispatch_execution_task',True,'provider_scoped_dispatch_execution_task_not_false'),('eligible_for_future_dispatch_execution_task',True,'future_dispatch_execution_task_not_false'),('eligible_for_live_send_now',True,'live_send_now_not_false'),('dispatch_allowed',True,'dispatch_allowed_not_false'),('live_send_allowed',True,'live_send_allowed_not_false'),('publication_ready',True,'publication_ready_not_false'),('runtime_truth',True,'runtime_truth_not_false'),('provider_call_made',True,'provider_call_made_not_false'),('network_call_made',True,'network_call_made_not_false'),('browser_session_used',True,'browser_session_used_not_false'),('executable_request_artifact_created',True,'executable_request_artifact_created_not_false')]
 for k,v,frag in cases:
  u=_valid(); u[k]=v; assert any(frag in x for x in _gate(u).blockers), (k,_gate(u).blockers)
 u=_valid(); u['official_provider_docs_scope_records']=[]; assert 'official_docs_scope_records_missing' in _gate(u).blockers
def test_record_fail_closed_cases():
 cases=[('non_executable_docs_scope_record',False,'executable_marker_invalid'),('provider_family_label','unknown_future_provider_lane','provider_family_invalid'),('official_docs_source_id','unknown_docs','source_id_invalid'),('official_docs_provider_family','bad_docs','docs_family_invalid'),('approved_payload_hash','abc','approved_payload_hash_invalid'),('symbolic_destination_binding_id','real','symbolic_destination_binding_id_invalid'),('symbolic_credential_handle_id','real','symbolic_credential_handle_id_invalid'),('approved_payload_preview_id','','preview_id_empty'),('required_env_key_name','BAD','key_not_allowlisted'),('dispatch_method_family_label','bad','method_family_invalid')]
 for k,v,frag in cases:
  u=_valid(); u['official_provider_docs_scope_records'][0][k]=v; assert any(frag in x for x in _gate(u).blockers), (k,_gate(u).blockers)
def test_raw_and_unsafe_flags_fail_closed():
 for k in ['provider_call_made','network_call_made','browser_session_used','dispatch_allowed','live_send_allowed','executable_request_artifact_created','endpoint_url_present','webhook_url_present','channel_id_present','account_id_present','token_present','payload_body_present','public_url_created','metrics_created']:
  u=_valid(); u['official_provider_docs_scope_records'][0][k]=True; b=_gate(u); assert b.eligible_for_future_provider_runtime_authority_gate_task is False; assert any(k in x for x in b.blockers)
def test_forbidden_text_no_echo_and_injected_values_not_serialized():
 terms=('endpoint','webhook','token','channel','account','https://example.invalid/x','metrics','browser profile','provider config','secret file','env line','credential value','env value','public url','payload body','live-control','executable request','curl','fetch','requests','http method','url path','header','body','sdk','adapter','retry policy','request budget','timeout','scheduler','queue','background worker','live button')
 for term in terms:
  u=_valid(); u['official_provider_docs_scope_records'][0]['platform']=term; b=_gate(u); assert any('forbidden_' in x for x in b.blockers); assert term not in ' '.join(b.blockers)
 u=_valid(); u['official_provider_docs_scope_records'][0]['warnings']=['fake-secret-value','payload body content']; s=json.dumps(asdict(_gate(u))).lower(); assert 'fake-secret-value' not in s and 'payload body content' not in s
def test_flags_false_every_case():
 for b in [_gate(),_gate(_default())]:
  for f in ['credential_value_read','credential_value_stored','credential_value_logged','env_read','dotenv_read','env_iterated','provider_call_made','network_call_made','browser_session_used','executable_request_artifact_created','endpoint_url_present','webhook_url_present','channel_id_present','account_id_present','token_present','payload_body_present','public_url_created','metrics_created','publication_ready','dispatch_allowed','live_send_allowed','runtime_truth','eligible_for_future_provider_scoped_dispatch_execution_task','eligible_for_future_dispatch_execution_task','eligible_for_live_send_now']:
   assert getattr(b,f) is False, f
def test_static_no_forbidden_runtime_code():
 src=Path('live_contentops/endpoint_allowlist_gate_from_official_provider_docs_scope_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
 for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','discord.py','telebot','telegram.ext','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ','get ','/bots/','/webhooks/','payload_file','payload_path','read_bytes(','retry policy','request budget','timeout','background worker','live button','scheduler','queue']: assert bad not in low, bad
def test_docs_sample_hygiene():
 base=Path('docs/automation/V6_ENDPOINT_ALLOWLIST_GATE_FROM_OFFICIAL_PROVIDER_DOCS_SCOPE_HEAVY_BATCH_DOCS_ONLY_NO_PROVIDER_NO_DISPATCH_NO_LIVE')
 paths=[base/'implementation_report.md',base/'endpoint_allowlist_gate_contract.md',base/'sample_endpoint_allowlist_gate_bundle.json',Path('docs/runbooks/V6_ENDPOINT_ALLOWLIST_GATE_OPERATOR_RUNBOOK_DOCS_ONLY_NO_PROVIDER_NO_DISPATCH_NO_LIVE.md')]
 for p in paths:
  raw=p.read_bytes(); assert not raw.startswith(b'\xef\xbb\xbf'); txt=raw.decode('utf-8'); assert '`n' not in txt
  for bad in ['https://','discord.com/api','api/webhooks','Bearer ','fake-secret-value','payload body content','public url','metrics endpoint','webhook url','endpoint url','channel id','account id','token value','retry policy','request budget','timeout','http method','url path','sdk adapter']: assert bad.lower() not in txt.lower(), (p,bad)
 d=json.loads(paths[2].read_text(encoding='utf-8')); assert d['endpoint_allowlist_gate_status']=='blocked_invalid_official_docs_scope_or_endpoint_allowlist'; assert d['eligible_for_future_provider_runtime_authority_gate_task'] is False
