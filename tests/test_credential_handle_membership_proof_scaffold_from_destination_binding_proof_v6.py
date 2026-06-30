import ast,json
from dataclasses import asdict
from pathlib import Path
from live_contentops.credential_handle_membership_proof_scaffold_from_destination_binding_proof_v6 import *
from live_contentops.destination_binding_proof_scaffold_from_env_membership_gate_v6 import make_destination_binding_proof_scaffold_bundle
from live_contentops.exact_env_key_membership_check_gate_v6 import make_exact_env_key_membership_check_gate_bundle
from live_contentops.credential_presence_membership_scaffold_from_destination_binding_v6 import make_credential_presence_membership_scaffold_bundle, asdict as m_asdict
from live_contentops.destination_binding_review_scaffold_from_dispatch_gate_v6 import make_destination_binding_review_scaffold_bundle
from live_contentops.dispatch_gate_scaffold_from_prepared_outbox_v6 import make_dispatch_gate_scaffold_bundle
from tests.test_dispatch_gate_scaffold_from_prepared_outbox_v6 import _accepted_outbox
SAMPLE=Path('docs/automation/V6_DESTINATION_BINDING_PROOF_SCAFFOLD_FROM_ENV_MEMBERSHIP_GATE_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_destination_binding_proof_scaffold_bundle.json')
def _default(): return json.loads(SAMPLE.read_text(encoding='utf-8'))
def _membership():
    d=asdict(make_destination_binding_review_scaffold_bundle(asdict(make_dispatch_gate_scaffold_bundle(_accepted_outbox()))))
    return m_asdict(make_credential_presence_membership_scaffold_bundle(d))
def _dest_present():
    g=asdict(make_exact_env_key_membership_check_gate_bundle(_membership(), perform_check=True, env_mapping={'DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK':'fake-secret-value','TELEGRAM_BOT_TOKEN':'fake-secret-value','TELEGRAM_CHAT_ID':'fake-secret-value'}))
    return asdict(make_destination_binding_proof_scaffold_bundle(g))
def _dest_missing():
    g=asdict(make_exact_env_key_membership_check_gate_bundle(_membership(), perform_check=True, env_mapping={'DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK':'fake-secret-value'}))
    return asdict(make_destination_binding_proof_scaffold_bundle(g))
def _bundle(x=None): return make_credential_handle_membership_proof_scaffold_bundle(x or _dest_present())
def test_default_committed_sample_blocked_no_proof():
    b=_bundle(_default()); assert b.credential_handle_membership_proof_status=='blocked_invalid_destination_binding_proof_scaffold'; assert b.credential_handle_membership_proof_records==[]; assert b.all_required_credential_handle_membership_proofs_available is False; assert b.eligible_for_future_payload_hash_revalidation_gate_task is False
    assert b.eligible_for_future_dispatch_execution_task is False and b.eligible_for_live_send_now is False and b.dispatch_allowed is False and b.live_send_allowed is False
def test_valid_all_present_symbolic_records_only_no_value_leak():
    b=_bundle(); s=json.dumps(asdict(b)); assert b.credential_handle_membership_proof_status=='all_required_credential_handle_membership_proofs_available_for_future_payload_hash_revalidation_only'; assert b.all_required_credential_handle_membership_proofs_available is True; assert b.eligible_for_future_payload_hash_revalidation_gate_task is True
    assert sorted(b.proof_available_key_names)==['DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK','TELEGRAM_BOT_TOKEN','TELEGRAM_CHAT_ID']; assert b.proof_missing_key_names==[]; assert 'fake-secret-value' not in s; assert len(b.symbolic_credential_handle_ids)==3 and len(b.symbolic_destination_binding_ids)==3
    for r in b.credential_handle_membership_proof_records:
        assert r['proof_status']==PROOF_AVAILABLE and r['credential_handle_membership_proof_available'] is True
        assert r['symbolic_destination_binding_id'].startswith('symbolic_destination_binding_required_later_') and r['symbolic_credential_handle_id'].startswith('symbolic_credential_handle_required_later_')
        assert validate_credential_handle_membership_proof_record(r)==[]
def test_missing_incomplete_input_fail_closed():
    b=_bundle(_dest_missing()); assert b.credential_handle_membership_proof_status=='blocked_invalid_destination_binding_proof_scaffold'; assert b.eligible_for_future_payload_hash_revalidation_gate_task is False
    x=_dest_present(); x['destination_binding_proof_records']=[]; assert 'destination_binding_proof_scaffold_bundle_records_empty' in _bundle(x).blockers
def test_malformed_non_object_cli(tmp_path):
    i=tmp_path/'bad.json'; o=tmp_path/'out.json'; i.write_text('[]', encoding='utf-8'); assert main(['--destination-binding-proof-scaffold-bundle',str(i),'--output',str(o)])==1
    d=json.loads(o.read_text(encoding='utf-8')); assert d['credential_handle_membership_proof_status']=='blocked_invalid_destination_binding_proof_scaffold'; assert d['eligible_for_future_payload_hash_revalidation_gate_task'] is False
def test_wrong_label_schema_non_symbolic_and_availability_fail_closed():
    x=_dest_present(); x['task_label']='WRONG'; assert 'destination_binding_proof_scaffold_bundle_task_label_invalid' in _bundle(x).blockers
    x=_dest_present(); x['schema_version']='5.0.0'; assert 'destination_binding_proof_scaffold_bundle_schema_version_invalid' in _bundle(x).blockers
    x=_dest_present(); x['destination_binding_proof_records'][0]['symbolic_destination_binding_id']='realish'; assert 'record_0_destination_binding_proof_record_symbolic_destination_binding_id_invalid' in _bundle(x).blockers
    x=_dest_present(); x['destination_binding_proof_records'][0]['symbolic_credential_handle_id']='realish'; assert 'record_0_destination_binding_proof_record_symbolic_credential_handle_id_invalid' in _bundle(x).blockers
    x=_dest_present(); x['destination_binding_proof_records'][0]['destination_binding_proof_available']=False; assert 'record_0_destination_binding_proof_record_availability_not_true' in _bundle(x).blockers
def test_forbidden_text_no_echo():
    for term in ('endpoint','webhook','token','channel','account','https://example.invalid/x','metrics','browser profile','provider config','secret file','env line','credential value','env value','public url','payload body','live-send','executable request','curl','fetch','requests'):
        x=_dest_present(); x['destination_binding_proof_records'][0]['approved_payload_preview_id']=term; blockers=_bundle(x).blockers; assert any('forbidden_' in b for b in blockers); assert term not in ' '.join(blockers)
def test_flags_false_every_case():
    for source in (_dest_present(), _dest_missing(), _default()):
        b=_bundle(source)
        for f in ['credential_value_read','credential_value_stored','credential_value_logged','env_read','dotenv_read','env_iterated','provider_call_made','network_call_made','browser_session_used','executable_request_artifact_created','endpoint_url_present','webhook_url_present','channel_id_present','account_id_present','token_present','payload_body_present','public_url_created','metrics_created','publication_ready','dispatch_allowed','live_send_allowed','runtime_truth','eligible_for_future_dispatch_execution_task','eligible_for_live_send_now']:
            assert getattr(b,f) is False, f
def test_future_payload_hash_revalidation_eligibility_only_all_safe_present():
    assert _bundle(_dest_present()).eligible_for_future_payload_hash_revalidation_gate_task is True
    assert _bundle(_dest_missing()).eligible_for_future_payload_hash_revalidation_gate_task is False
    x=_dest_present(); x['destination_binding_proof_records'][0]['credential_value_read']=True; assert _bundle(x).eligible_for_future_payload_hash_revalidation_gate_task is False
def test_static_no_env_provider_network_browser():
    src=Path('live_contentops/credential_handle_membership_proof_scaffold_from_destination_binding_proof_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
    for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ']: assert bad not in low, bad
def test_docs_sample_hygiene():
    base=Path('docs/automation/V6_CREDENTIAL_HANDLE_MEMBERSHIP_PROOF_SCAFFOLD_FROM_DESTINATION_BINDING_PROOF_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE')
    paths=[base/'implementation_report.md',base/'credential_handle_membership_proof_scaffold_contract.md',base/'sample_credential_handle_membership_proof_scaffold_bundle.json',Path('docs/runbooks/V6_CREDENTIAL_HANDLE_MEMBERSHIP_PROOF_SCAFFOLD_OPERATOR_RUNBOOK_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE.md')]
    for p in paths:
        raw=p.read_bytes(); assert not raw.startswith(b'\xef\xbb\xbf'), p; txt=raw.decode('utf-8'); assert '`n' not in txt
        for bad in ['https://','discord.com/api','api/webhooks','Bearer ','fake-secret-value']: assert bad.lower() not in txt.lower(), (p,bad)
    d=json.loads(paths[2].read_text(encoding='utf-8')); assert d['credential_handle_membership_proof_status']=='blocked_invalid_destination_binding_proof_scaffold'; assert d['eligible_for_future_payload_hash_revalidation_gate_task'] is False