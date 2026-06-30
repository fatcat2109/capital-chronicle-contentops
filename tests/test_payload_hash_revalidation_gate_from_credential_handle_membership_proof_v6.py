import ast,json
from dataclasses import asdict
from pathlib import Path
from live_contentops.payload_hash_revalidation_gate_from_credential_handle_membership_proof_v6 import *
from live_contentops.credential_handle_membership_proof_scaffold_from_destination_binding_proof_v6 import make_credential_handle_membership_proof_scaffold_bundle
from tests.test_credential_handle_membership_proof_scaffold_from_destination_binding_proof_v6 import _dest_present, _dest_missing
SAMPLE=Path('docs/automation/V6_CREDENTIAL_HANDLE_MEMBERSHIP_PROOF_SCAFFOLD_FROM_DESTINATION_BINDING_PROOF_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_credential_handle_membership_proof_scaffold_bundle.json')
def _default(): return json.loads(SAMPLE.read_text(encoding='utf-8'))
def _proof_present(): return asdict(make_credential_handle_membership_proof_scaffold_bundle(_dest_present()))
def _proof_missing(): return asdict(make_credential_handle_membership_proof_scaffold_bundle(_dest_missing()))
def _bundle(x=None): return make_payload_hash_revalidation_gate_bundle(x or _proof_present())
def test_default_committed_sample_blocked_no_revalidation():
    b=_bundle(_default()); assert b.payload_hash_revalidation_status=='blocked_invalid_credential_handle_membership_proof_scaffold'; assert b.payload_hash_revalidation_records==[]; assert b.all_required_payload_hash_revalidations_available is False; assert b.eligible_for_future_exact_operator_dispatch_go_gate_task is False
    assert b.eligible_for_future_dispatch_execution_task is False and b.eligible_for_live_send_now is False and b.dispatch_allowed is False and b.live_send_allowed is False
def test_valid_all_present_emits_hash_revalidation_only_no_value_leak():
    b=_bundle(); s=json.dumps(asdict(b)); assert b.payload_hash_revalidation_status=='all_required_payload_hash_revalidations_available_for_future_exact_operator_dispatch_go_only'; assert b.all_required_payload_hash_revalidations_available is True; assert b.eligible_for_future_exact_operator_dispatch_go_gate_task is True
    assert sorted(b.proof_available_key_names)==['DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK','TELEGRAM_BOT_TOKEN','TELEGRAM_CHAT_ID']; assert b.proof_missing_key_names==[]; assert len(b.payload_hash_revalidation_records)==3; assert 'fake-secret-value' not in s; assert 'payload_body' in s and 'payload_body_present' in s
    assert all(SHA256_HEX_RE.fullmatch(h) for h in b.revalidated_payload_hashes)
    for r in b.payload_hash_revalidation_records:
        assert r['payload_hash_revalidation_status']==REVALIDATION_AVAILABLE and r['payload_hash_format_valid'] is True and r['payload_hash_revalidated_for_future_exact_operator_dispatch_go_only'] is True
        assert r['symbolic_destination_binding_id'].startswith('symbolic_destination_binding_required_later_') and r['symbolic_credential_handle_id'].startswith('symbolic_credential_handle_required_later_')
        assert validate_revalidation_record(r)==[]
def test_hash_format_missing_malformed_token_url_fail_closed_no_echo():
    cases=[('', 'credential_handle_membership_proof_record_approved_payload_hash_invalid'),('abc','credential_handle_membership_proof_record_approved_payload_hash_invalid'),('g'*64,'credential_handle_membership_proof_record_approved_payload_hash_invalid'),('https://example.invalid/x','forbidden_value'),('abc.defghijklmnopqrstuvwxyz.abcdefghijklmnopqrstuvwxyz','forbidden_value')]
    for value, expected in cases:
        x=_proof_present(); x['credential_handle_membership_proof_records'][0]['approved_payload_hash']=value; blockers=_bundle(x).blockers; assert any(expected in b for b in blockers), (value, blockers); assert value=='' or value not in ' '.join(blockers)
def test_missing_preview_and_incomplete_input_fail_closed():
    x=_proof_present(); x['credential_handle_membership_proof_records'][0]['approved_payload_preview_id']=''; assert 'record_0_credential_handle_membership_proof_record_approved_payload_preview_id_empty' in _bundle(x).blockers
    x=_proof_present(); x['credential_handle_membership_proof_records']=[]; assert 'credential_handle_membership_proof_scaffold_bundle_records_empty' in _bundle(x).blockers
    assert _bundle(_proof_missing()).eligible_for_future_exact_operator_dispatch_go_gate_task is False
def test_malformed_non_object_cli(tmp_path):
    i=tmp_path/'bad.json'; o=tmp_path/'out.json'; i.write_text('[]', encoding='utf-8'); assert main(['--credential-handle-membership-proof-scaffold-bundle',str(i),'--output',str(o)])==1
    d=json.loads(o.read_text(encoding='utf-8')); assert d['payload_hash_revalidation_status']=='blocked_invalid_credential_handle_membership_proof_scaffold'; assert d['eligible_for_future_exact_operator_dispatch_go_gate_task'] is False
def test_wrong_label_schema_symbolic_and_availability_fail_closed():
    x=_proof_present(); x['task_label']='WRONG'; assert 'credential_handle_membership_proof_scaffold_bundle_task_label_invalid' in _bundle(x).blockers
    x=_proof_present(); x['schema_version']='5.0.0'; assert 'credential_handle_membership_proof_scaffold_bundle_schema_version_invalid' in _bundle(x).blockers
    x=_proof_present(); x['credential_handle_membership_proof_records'][0]['symbolic_destination_binding_id']='realish'; assert 'record_0_credential_handle_membership_proof_record_symbolic_destination_binding_id_invalid' in _bundle(x).blockers
    x=_proof_present(); x['credential_handle_membership_proof_records'][0]['symbolic_credential_handle_id']='realish'; assert 'record_0_credential_handle_membership_proof_record_symbolic_credential_handle_id_invalid' in _bundle(x).blockers
    x=_proof_present(); x['credential_handle_membership_proof_records'][0]['credential_handle_membership_proof_available']=False; assert 'record_0_credential_handle_membership_proof_record_availability_not_true' in _bundle(x).blockers
def test_forbidden_text_no_echo():
    for term in ('endpoint','webhook','token','channel','account','https://example.invalid/x','metrics','browser profile','provider config','secret file','env line','credential value','env value','public url','payload body','live-send','executable request','curl','fetch','requests'):
        x=_proof_present(); x['credential_handle_membership_proof_records'][0]['approved_payload_preview_id']=term; blockers=_bundle(x).blockers; assert any('forbidden_' in b for b in blockers); assert term not in ' '.join(blockers)
def test_flags_false_every_case():
    for source in (_proof_present(), _proof_missing(), _default()):
        b=_bundle(source)
        for f in ['credential_value_read','credential_value_stored','credential_value_logged','env_read','dotenv_read','env_iterated','provider_call_made','network_call_made','browser_session_used','executable_request_artifact_created','endpoint_url_present','webhook_url_present','channel_id_present','account_id_present','token_present','payload_body_present','public_url_created','metrics_created','publication_ready','dispatch_allowed','live_send_allowed','runtime_truth','eligible_for_future_dispatch_execution_task','eligible_for_live_send_now']:
            assert getattr(b,f) is False, f
def test_exact_go_eligibility_only_all_safe_present():
    assert _bundle(_proof_present()).eligible_for_future_exact_operator_dispatch_go_gate_task is True
    assert _bundle(_proof_missing()).eligible_for_future_exact_operator_dispatch_go_gate_task is False
    x=_proof_present(); x['credential_handle_membership_proof_records'][0]['approved_payload_hash']='abc'; assert _bundle(x).eligible_for_future_exact_operator_dispatch_go_gate_task is False
    x=_proof_present(); x['credential_handle_membership_proof_records'][0]['payload_body_present']=True; assert _bundle(x).eligible_for_future_exact_operator_dispatch_go_gate_task is False
def test_static_no_env_provider_network_browser_payload_body_reads():
    src=Path('live_contentops/payload_hash_revalidation_gate_from_credential_handle_membership_proof_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
    for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ','payload_file','payload_path','read_bytes(']: assert bad not in low, bad
def test_docs_sample_hygiene():
    base=Path('docs/automation/V6_PAYLOAD_HASH_REVALIDATION_GATE_FROM_CREDENTIAL_HANDLE_MEMBERSHIP_PROOF_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE')
    paths=[base/'implementation_report.md',base/'payload_hash_revalidation_gate_contract.md',base/'sample_payload_hash_revalidation_gate_bundle.json',Path('docs/runbooks/V6_PAYLOAD_HASH_REVALIDATION_GATE_OPERATOR_RUNBOOK_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE.md')]
    for p in paths:
        raw=p.read_bytes(); assert not raw.startswith(b'\xef\xbb\xbf'), p; txt=raw.decode('utf-8'); assert '`n' not in txt
        for bad in ['https://','discord.com/api','api/webhooks','Bearer ','fake-secret-value','payload body content','public url','metrics endpoint']: assert bad.lower() not in txt.lower(), (p,bad)
    d=json.loads(paths[2].read_text(encoding='utf-8')); assert d['payload_hash_revalidation_status']=='blocked_invalid_credential_handle_membership_proof_scaffold'; assert d['eligible_for_future_exact_operator_dispatch_go_gate_task'] is False
