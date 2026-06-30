import ast,json
from dataclasses import asdict
from pathlib import Path
from live_contentops.credential_hydration_gate_from_provider_runtime_authority_v6 import *
from live_contentops.provider_runtime_authority_gate_from_endpoint_allowlist_v6 import make_provider_runtime_authority_gate_bundle
from live_contentops.endpoint_allowlist_gate_from_official_provider_docs_scope_v6 import make_endpoint_allowlist_gate_bundle
from live_contentops.official_provider_docs_scope_gate_from_provider_scoped_prep_v6 import make_official_provider_docs_scope_gate_bundle, official_docs_fixture
from tests.test_official_provider_docs_scope_gate_from_provider_scoped_prep_v6 import _valid as docs_valid
SAMPLE=Path('docs/automation/V6_PROVIDER_RUNTIME_AUTHORITY_GATE_FROM_ENDPOINT_ALLOWLIST_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_provider_runtime_authority_gate_bundle.json')
def _default(): return json.loads(SAMPLE.read_text(encoding='utf-8'))
def _valid(): return asdict(make_provider_runtime_authority_gate_bundle(asdict(make_endpoint_allowlist_gate_bundle(asdict(make_official_provider_docs_scope_gate_bundle(docs_valid(), official_docs_fixture()))))))
def _gate(u=None): return make_credential_hydration_gate_bundle(_valid() if u is None else u)
def test_default_sample_blocked():
 b=_gate(_default()); assert b.credential_hydration_gate_status=='blocked_invalid_provider_runtime_authority_or_credential_hydration'; assert b.credential_hydration_records==[]; assert b.eligible_for_future_exact_payload_rehydration_gate_task is False
def test_valid_synthetic_no_value_records():
 b=_gate(); s=json.dumps(asdict(b)); assert b.credential_hydration_gate_status==GATE_STATUS; assert b.eligible_for_future_exact_payload_rehydration_gate_task is True; assert b.eligible_for_future_destination_resolution_gate_task is False; assert b.eligible_for_future_request_shape_gate_task is False; assert b.eligible_for_live_send_now is False; assert len(b.credential_hydration_records)==3
 assert set(b.proof_available_key_names) <= ALLOWED_REQUIRED_KEY_NAMES and b.symbolic_credential_handle_ids and b.symbolic_destination_binding_ids
 for r in b.credential_hydration_records:
  assert r['credential_hydration_symbolic_only'] is True and r['credential_hydration_no_value'] is True and r['non_executable_credential_hydration_record'] is True
  assert r['credential_key_name_allowlisted'] is True and r['symbolic_credential_handle_present'] is True and r['symbolic_destination_binding_present'] is True
  assert r['symbolic_credential_handle_id'].startswith('symbolic_credential_handle_required_later_') and r['symbolic_destination_binding_id'].startswith('symbolic_destination_binding_required_later_')
  for f in VALUE_FALSE_FLAGS+OTHER_FALSE_FLAGS: assert r[f] is False
 assert 'fake-secret-value' not in s and 'payload body content' not in s.lower()
def test_upstream_fail_closed_cases():
 cases=[('task_label','WRONG','task_label_invalid'),('schema_version','5','schema_version_invalid'),('provider_runtime_authority_gate_status','WRONG','status_invalid'),('eligible_for_future_credential_hydration_gate_task',False,'credential_hydration_eligibility_not_true'),('runtime_authority_symbolic_only',False,'runtime_authority_symbolic_only_not_true'),('runtime_authority_prerequisites_present',False,'runtime_authority_prerequisites_present_not_true'),('runtime_authority_does_not_authorize_execution',False,'does_not_authorize_execution_not_true'),('endpoint_allowlist_symbolic_only',False,'endpoint_allowlist_symbolic_only_not_true'),('endpoint_operation_ids_sanitized',False,'endpoint_operation_ids_sanitized_not_true'),('raw_endpoint_values_present',True,'raw_endpoint_values_present_not_false'),('raw_http_method_values_present',True,'raw_http_method_values_present_not_false'),('raw_url_path_values_present',True,'raw_url_path_values_present_not_false'),('eligible_for_future_provider_scoped_dispatch_execution_task',True,'provider_scoped_dispatch_execution_task_not_false'),('eligible_for_future_dispatch_execution_task',True,'future_dispatch_execution_task_not_false'),('eligible_for_live_send_now',True,'live_send_now_not_false'),('dispatch_allowed',True,'dispatch_allowed_not_false'),('live_send_allowed',True,'live_send_allowed_not_false'),('publication_ready',True,'publication_ready_not_false'),('runtime_truth',True,'runtime_truth_not_false'),('provider_call_made',True,'provider_call_made_not_false'),('network_call_made',True,'network_call_made_not_false'),('browser_session_used',True,'browser_session_used_not_false'),('executable_request_artifact_created',True,'executable_request_artifact_created_not_false'),('credential_value_read',True,'credential_value_read_not_false'),('credential_value_hydrated',True,'credential_value_hydrated_not_false'),('env_read',True,'env_read_not_false')]
 for k,v,frag in cases:
  u=_valid(); u[k]=v; assert any(frag in x for x in _gate(u).blockers), (k,_gate(u).blockers)
def test_record_fail_closed_cases():
 cases=[('required_env_key_name','BAD','key_not_allowlisted'),('symbolic_credential_handle_id','','symbolic_credential_handle_id_invalid'),('symbolic_credential_handle_id','real','symbolic_credential_handle_id_invalid'),('symbolic_destination_binding_id','','symbolic_destination_binding_id_invalid'),('symbolic_destination_binding_id','real','symbolic_destination_binding_id_invalid'),('sanitized_endpoint_operation_ids',['unknown_operation_required_later'],'operation_ids_invalid'),('official_docs_source_id','unknown_docs','source_id_invalid'),('provider_family_label','unknown_future_provider_lane','provider_family_invalid'),('runtime_authority_symbolic_only',False,'runtime_authority_symbolic_only_not_true'),('runtime_authority_prerequisites_present',False,'runtime_authority_prerequisites_present_not_true'),('runtime_authority_does_not_authorize_execution',False,'does_not_authorize_execution_not_true'),('non_executable_runtime_authority_record',False,'non_executable_runtime_authority_record_not_true'),('approved_payload_hash','abc','approved_payload_hash_invalid'),('approved_payload_preview_id','','preview_id_empty')]
 for k,v,frag in cases:
  u=_valid(); u['provider_runtime_authority_records'][0][k]=v; assert any(frag in x for x in _gate(u).blockers), (k,_gate(u).blockers)
def test_value_and_env_flags_fail_closed():
 for k in VALUE_FALSE_FLAGS+OTHER_FALSE_FLAGS+('raw_endpoint_values_present','raw_http_method_values_present','raw_url_path_values_present'):
  u=_valid(); u['provider_runtime_authority_records'][0][k]=True; b=_gate(u); assert b.eligible_for_future_exact_payload_rehydration_gate_task is False; assert any(k in x for x in b.blockers)
def test_forbidden_text_and_injected_values_not_serialized():
 terms=('credential value','env value','token','secret','https://example.invalid/x','endpoint','webhook','channel','account','payload body','public url','metrics','browser profile','provider config','retry policy','request budget','timeout','http method','url path','header','body','sdk','adapter','scheduler','queue','live-control')
 for term in terms:
  u=_valid(); u['provider_runtime_authority_records'][0]['platform']=term; b=_gate(u); assert any('forbidden_' in x for x in b.blockers)
  if term not in {'endpoint','webhook','token','channel','account','metrics','body'}: assert term not in json.dumps(asdict(b))
 u=_valid(); u['provider_runtime_authority_records'][0]['warnings']=['fake-secret-value','payload body content']; s=json.dumps(asdict(_gate(u))).lower(); assert 'fake-secret-value' not in s and 'payload body content' not in s
def test_output_flags_false_every_case():
 for b in [_gate(),_gate(_default())]:
  for f in ['credential_value_hydrated','credential_value_read','credential_value_stored','credential_value_logged','credential_value_length_checked','credential_value_prefix_checked','credential_value_suffix_checked','credential_value_hash_computed','credential_value_digest_computed','credential_value_redacted_fragment_created','env_read','dotenv_read','env_iterated','provider_call_made','network_call_made','browser_session_used','executable_request_artifact_created','endpoint_url_present','webhook_url_present','channel_id_present','account_id_present','token_present','payload_body_present','public_url_created','metrics_created','publication_ready','dispatch_allowed','live_send_allowed','runtime_truth','eligible_for_future_destination_resolution_gate_task','eligible_for_future_request_shape_gate_task','eligible_for_future_provider_scoped_dispatch_execution_task','eligible_for_future_dispatch_execution_task','eligible_for_live_send_now']:
   assert getattr(b,f) is False, f
def test_static_no_forbidden_runtime_code():
 src=Path('live_contentops/credential_hydration_gate_from_provider_runtime_authority_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
 for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','discord.py','telebot','telegram.ext','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ','get ','/bots/','/webhooks/','payload_file','payload_path','read_bytes(','retry policy','request budget','timeout','background worker','live button','scheduler','queue','len(','hexdigest(','digest(','startswith(secret','endswith(secret']:
  assert bad not in low, bad
def test_credential_output_marker_tamper_fails_closed():
 d=asdict(_gate()); d['credential_hydration_records'][0]['credential_hydration_no_value']=False; assert any('credential_hydration_no_value_not_true' in x for x in validate_credential_records(d['credential_hydration_records']))
 d['credential_hydration_records'][0]['non_executable_credential_hydration_record']=False; assert any('non_executable_credential_hydration_record_not_true' in x for x in validate_credential_records(d['credential_hydration_records']))
def test_docs_sample_hygiene():
 base=Path('docs/automation/V6_CREDENTIAL_HYDRATION_GATE_FROM_PROVIDER_RUNTIME_AUTHORITY_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE')
 paths=[base/'implementation_report.md',base/'credential_hydration_gate_contract.md',base/'sample_credential_hydration_gate_bundle.json',Path('docs/runbooks/V6_CREDENTIAL_HYDRATION_GATE_OPERATOR_RUNBOOK_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE.md')]
 for p in paths:
  raw=p.read_bytes(); assert not raw.startswith(b'\xef\xbb\xbf'); txt=raw.decode('utf-8')
  for bad in ['https://','discord.com/api','api/webhooks','Bearer ','fake-secret-value','payload body content','credential value','env value','token value','public url','metrics endpoint','webhook url','endpoint url','channel id','account id','retry policy','request budget','timeout','http method','url path','sdk adapter']: assert bad.lower() not in txt.lower(), (p,bad)
 d=json.loads(paths[2].read_text(encoding='utf-8')); assert d['credential_hydration_gate_status']=='blocked_invalid_provider_runtime_authority_or_credential_hydration'; assert d['eligible_for_future_exact_payload_rehydration_gate_task'] is False
