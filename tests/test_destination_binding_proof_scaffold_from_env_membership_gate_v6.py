import ast,json
from dataclasses import asdict
from pathlib import Path
from live_contentops.destination_binding_proof_scaffold_from_env_membership_gate_v6 import *
from live_contentops.exact_env_key_membership_check_gate_v6 import make_exact_env_key_membership_check_gate_bundle
from live_contentops.credential_presence_membership_scaffold_from_destination_binding_v6 import make_credential_presence_membership_scaffold_bundle, asdict as m_asdict
from live_contentops.destination_binding_review_scaffold_from_dispatch_gate_v6 import make_destination_binding_review_scaffold_bundle
from live_contentops.dispatch_gate_scaffold_from_prepared_outbox_v6 import make_dispatch_gate_scaffold_bundle
from tests.test_dispatch_gate_scaffold_from_prepared_outbox_v6 import _accepted_outbox
SAMPLE=Path('docs/automation/V6_EXACT_ENV_KEY_MEMBERSHIP_CHECK_GATE_FROM_CREDENTIAL_MEMBERSHIP_SCAFFOLD_HEAVY_BATCH_MEMBERSHIP_ONLY_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_exact_env_key_membership_check_gate_bundle.json')
def _default(): return json.loads(SAMPLE.read_text(encoding='utf-8'))
def _membership():
    d=asdict(make_destination_binding_review_scaffold_bundle(asdict(make_dispatch_gate_scaffold_bundle(_accepted_outbox()))))
    return m_asdict(make_credential_presence_membership_scaffold_bundle(d))
def _present(): return asdict(make_exact_env_key_membership_check_gate_bundle(_membership(), perform_check=True, env_mapping={'DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK':'fake-secret-value','TELEGRAM_BOT_TOKEN':'fake-secret-value','TELEGRAM_CHAT_ID':'fake-secret-value'}))
def _missing(): return asdict(make_exact_env_key_membership_check_gate_bundle(_membership(), perform_check=True, env_mapping={'DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK':'fake-secret-value'}))
def _bundle(x=None): return make_destination_binding_proof_scaffold_bundle(x or _present())
def test_default_committed_sample_blocked_no_proof():
    b=_bundle(_default()); assert b.destination_binding_proof_status=='blocked_invalid_env_membership_gate'; assert b.destination_binding_proof_records==[]; assert b.all_required_destination_binding_proofs_available is False; assert b.eligible_for_future_credential_handle_membership_proof_task is False
    assert b.eligible_for_future_dispatch_execution_task is False and b.eligible_for_live_send_now is False and b.dispatch_allowed is False and b.live_send_allowed is False
    assert b.credential_value_read is False and b.env_read is False and b.provider_call_made is False and b.network_call_made is False and b.browser_session_used is False
def test_valid_all_present_symbolic_proofs_only_no_value_leak():
    b=_bundle(); s=json.dumps(asdict(b)); assert b.destination_binding_proof_status=='all_required_destination_binding_proofs_available_for_future_credential_handle_membership_only'; assert b.all_required_destination_binding_proofs_available is True; assert b.eligible_for_future_credential_handle_membership_proof_task is True
    assert sorted(b.proof_available_key_names)==['DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK','TELEGRAM_BOT_TOKEN','TELEGRAM_CHAT_ID']; assert b.proof_missing_key_names==[]; assert 'fake-secret-value' not in s
    for r in b.destination_binding_proof_records:
        assert r['proof_status']==PROOF_AVAILABLE and r['destination_binding_proof_available'] is True
        assert r['symbolic_destination_binding_id'].startswith('symbolic_destination_binding_required_later_') and r['symbolic_credential_handle_id'].startswith('symbolic_credential_handle_required_later_')
        assert validate_proof_record(r)==[]
def test_missing_key_names_fail_closed():
    b=_bundle(_missing()); assert b.destination_binding_proof_status=='blocked_invalid_env_membership_gate' or b.destination_binding_proof_status=='missing_required_destination_binding_proofs'; assert b.eligible_for_future_credential_handle_membership_proof_task is False; assert b.eligible_for_future_dispatch_execution_task is False and b.eligible_for_live_send_now is False
def test_malformed_non_object_cli(tmp_path):
    i=tmp_path/'bad.json'; o=tmp_path/'out.json'; i.write_text('[]', encoding='utf-8'); assert main(['--exact-env-key-membership-check-gate-bundle',str(i),'--output',str(o)])==1
    d=json.loads(o.read_text(encoding='utf-8')); assert d['destination_binding_proof_status']=='blocked_invalid_env_membership_gate'; assert d['eligible_for_future_credential_handle_membership_proof_task'] is False
def test_wrong_label_and_unchecked_fail_closed():
    x=_present(); x['task_label']='WRONG'; assert 'exact_env_key_membership_check_gate_bundle_task_label_invalid' in _bundle(x).blockers
    x=_present(); x['env_membership_checked']=False; assert 'exact_env_key_membership_check_gate_bundle_membership_not_checked' in _bundle(x).blockers
    x=_present(); x['env_key_membership_check_records'][0]['env_membership_checked']=False; assert 'record_0_env_key_membership_check_record_unchecked' in _bundle(x).blockers
def test_forbidden_text_no_echo():
    for term in ('endpoint','webhook','token','channel','account','https://example.invalid/x','metrics','browser profile','provider config','secret file','env line','credential value','env value','public url','payload body','live-send','executable request','curl','fetch','requests'):
        x=_present(); x['env_key_membership_check_records'][0]['approved_payload_preview_id']=term; blockers=_bundle(x).blockers; assert any('forbidden_' in b for b in blockers); assert term not in ' '.join(blockers)
def test_flags_false_every_case():
    for source in (_present(), _missing(), _default()):
        b=_bundle(source)
        for f in ['credential_value_read','credential_value_stored','credential_value_logged','env_read','dotenv_read','env_iterated','provider_call_made','network_call_made','browser_session_used','executable_request_artifact_created','endpoint_url_present','webhook_url_present','channel_id_present','account_id_present','token_present','payload_body_present','public_url_created','metrics_created','publication_ready','dispatch_allowed','live_send_allowed','runtime_truth','eligible_for_future_dispatch_execution_task','eligible_for_live_send_now']:
            assert getattr(b,f) is False, f
def test_future_credential_handle_eligibility_only_all_safe_present():
    assert _bundle(_present()).eligible_for_future_credential_handle_membership_proof_task is True
    assert _bundle(_missing()).eligible_for_future_credential_handle_membership_proof_task is False
    x=_present(); x['env_key_membership_check_records'][0]['credential_value_read']=True; assert _bundle(x).eligible_for_future_credential_handle_membership_proof_task is False
def test_static_no_env_provider_network_browser():
    src=Path('live_contentops/destination_binding_proof_scaffold_from_env_membership_gate_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
    for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ']: assert bad not in low, bad
def test_docs_sample_hygiene():
    base=Path('docs/automation/V6_DESTINATION_BINDING_PROOF_SCAFFOLD_FROM_ENV_MEMBERSHIP_GATE_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE')
    paths=[base/'implementation_report.md',base/'destination_binding_proof_scaffold_contract.md',base/'sample_destination_binding_proof_scaffold_bundle.json',Path('docs/runbooks/V6_DESTINATION_BINDING_PROOF_SCAFFOLD_OPERATOR_RUNBOOK_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE.md')]
    for p in paths:
        raw=p.read_bytes(); assert not raw.startswith(b'\xef\xbb\xbf'), p; txt=raw.decode('utf-8'); assert '`n' not in txt
        for bad in ['https://','discord.com/api','api/webhooks','Bearer ','fake-secret-value']: assert bad.lower() not in txt.lower(), (p,bad)
    d=json.loads(paths[2].read_text(encoding='utf-8')); assert d['destination_binding_proof_status']=='blocked_invalid_env_membership_gate'; assert d['eligible_for_future_credential_handle_membership_proof_task'] is False