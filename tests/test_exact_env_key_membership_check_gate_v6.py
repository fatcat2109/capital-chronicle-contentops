import ast, json
from dataclasses import asdict
from pathlib import Path
from live_contentops.exact_env_key_membership_check_gate_v6 import *
from live_contentops.credential_presence_membership_scaffold_from_destination_binding_v6 import make_credential_presence_membership_scaffold_bundle, asdict as m_asdict
from live_contentops.destination_binding_review_scaffold_from_dispatch_gate_v6 import make_destination_binding_review_scaffold_bundle
from live_contentops.dispatch_gate_scaffold_from_prepared_outbox_v6 import make_dispatch_gate_scaffold_bundle
from tests.test_dispatch_gate_scaffold_from_prepared_outbox_v6 import _accepted_outbox
SAMPLE=Path('docs/automation/V6_CREDENTIAL_PRESENCE_MEMBERSHIP_SCAFFOLD_FROM_DESTINATION_BINDING_REVIEW_HEAVY_BATCH_NO_ENV_READ_NO_CREDENTIAL_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_credential_presence_membership_scaffold_bundle.json')
def _default(): return json.loads(SAMPLE.read_text(encoding='utf-8'))
def _accepted():
    d=asdict(make_destination_binding_review_scaffold_bundle(asdict(make_dispatch_gate_scaffold_bundle(_accepted_outbox()))))
    return m_asdict(make_credential_presence_membership_scaffold_bundle(d))
def _bundle(m=None, **kw): return make_exact_env_key_membership_check_gate_bundle(m or _accepted(), **kw)
def test_default_sample_blocked_no_check():
    b=_bundle(_default()); assert b.env_key_membership_check_status=='blocked_invalid_membership_scaffold'; assert b.env_key_membership_check_records==[]; assert b.eligible_for_future_destination_binding_proof_task is False; assert b.env_membership_checked is False; assert b.credential_presence_check_performed_now is False
    assert b.credential_value_read is False and b.credential_value_stored is False and b.credential_value_logged is False and b.env_read is False and b.dotenv_read is False and b.env_iterated is False
    assert b.eligible_for_future_dispatch_execution_task is False and b.eligible_for_live_send_now is False and b.publication_ready is False and b.dispatch_allowed is False and b.live_send_allowed is False
def test_valid_synthetic_without_flag_blocked_not_checked():
    b=_bundle(); assert b.env_key_membership_check_status=='blocked_not_checked'; assert b.env_membership_checked is False; assert b.eligible_for_future_destination_binding_proof_task is False; assert b.missing_required_env_key_names==[] and b.present_required_env_key_names==[]
    assert all(r['check_status']=='blocked_not_checked' and r['required_env_key_present'] is False and r['required_env_key_missing'] is True for r in b.env_key_membership_check_records)
def test_injected_env_all_present_key_names_only():
    env={k:'fake-secret-value-that-must-not-appear-or-be-read' for k in ['DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK','TELEGRAM_BOT_TOKEN','TELEGRAM_CHAT_ID']}
    b=_bundle(perform_check=True, env_mapping=env); assert b.env_key_membership_check_status=='all_required_env_keys_present_for_future_destination_binding_proof_only'; assert b.all_required_env_keys_present is True; assert b.eligible_for_future_destination_binding_proof_task is True
    assert sorted(b.present_required_env_key_names)==sorted(env); assert b.missing_required_env_key_names==[]; assert b.credential_presence_confirmed_now is True
    s=json.dumps(asdict(b)); assert 'fake-secret-value' not in s and 'must-not-appear' not in s
    for r in b.env_key_membership_check_records: assert r['required_env_key_present'] is True and r['required_env_key_missing'] is False and validate_env_key_membership_check_record(r)==[]
def test_injected_env_missing_lists_names_only():
    b=_bundle(perform_check=True, env_mapping={'DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK':'x'}); assert b.env_key_membership_check_status=='missing_required_env_keys'; assert b.all_required_env_keys_present is False; assert b.eligible_for_future_destination_binding_proof_task is False
    assert b.present_required_env_key_names==['DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK']; assert b.missing_required_env_key_names==['TELEGRAM_BOT_TOKEN','TELEGRAM_CHAT_ID']
def test_upstream_membership_fail_closed_cases():
    m=_accepted(); m['credential_presence_membership_status']='blocked'; assert 'credential_presence_membership_bundle_status_not_ready' in _bundle(m).blockers
    m=_accepted(); m['credential_presence_membership_records']=[]; assert 'credential_presence_membership_bundle_records_empty' in _bundle(m).blockers
    m=_accepted(); m['eligible_for_future_env_membership_check_task']=False; assert 'credential_presence_membership_bundle_future_env_membership_check_eligibility_not_true' in _bundle(m).blockers
    m=_accepted(); m['eligible_for_future_dispatch_execution_task']=True; assert 'credential_presence_membership_bundle_eligible_for_future_dispatch_execution_task_not_false' in _bundle(m).blockers
def test_hard_false_flags_fail_closed():
    for f in BUNDLE_FALSE_FLAGS:
        m=_accepted(); m[f]=True; assert f'credential_presence_membership_bundle_{f}_not_false' in _bundle(m).blockers
    for f in MEMBERSHIP_FALSE_FLAGS:
        m=_accepted(); m['credential_presence_membership_records'][0][f]=True; assert f'record_0_credential_presence_membership_record_{f}_not_false' in _bundle(m).blockers
def test_record_allowlist_platform_and_required_true_fail_closed():
    m=_accepted(); m['credential_presence_membership_records'][0]['required_env_key_name']='BAD_KEY'; assert 'record_0_credential_presence_membership_record_required_env_key_name_not_allowlisted' in _bundle(m).blockers
    m=_accepted(); m['credential_presence_membership_records'][0]['platform']='unknown'; assert 'record_0_credential_presence_membership_record_unsupported_platform' in _bundle(m).blockers
    for f in MEMBERSHIP_TRUE_FLAGS:
        m=_accepted(); m['credential_presence_membership_records'][0][f]=False; assert f'record_0_credential_presence_membership_record_{f}_not_true' in _bundle(m).blockers
def test_check_record_rejects_value_and_live_flags_and_complement():
    r=_bundle(perform_check=True, env_mapping={'DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK':'x','TELEGRAM_BOT_TOKEN':'x','TELEGRAM_CHAT_ID':'x'}).env_key_membership_check_records[0]
    for f in CHECK_FALSE_FLAGS:
        x=dict(r); x[f]=True; assert f'env_key_membership_check_record_{f}_not_false' in validate_env_key_membership_check_record(x)
    x=dict(r); x['required_env_key_missing']=True; assert 'env_key_membership_check_record_present_missing_not_complementary' in validate_env_key_membership_check_record(x)
def test_forbidden_text_no_echo():
    for term in ('endpoint','webhook','token','channel','account','cookie','session','localStorage','browser profile','env value','credential value','https://example.invalid/x','metrics','financial advice','signal service','fake metrics','fake citations','live-send','payload body','curl','fetch','requests'):
        m=_accepted(); m['credential_presence_membership_records'][0]['approved_payload_preview_id']=term; blockers=_bundle(m).blockers; assert any('forbidden_' in b for b in blockers); assert term not in ' '.join(blockers)
def test_malformed_non_object_cli(tmp_path):
    i=tmp_path/'bad.json'; o=tmp_path/'out.json'; i.write_text('[]', encoding='utf-8'); assert main(['--credential-presence-membership-scaffold-bundle',str(i),'--output',str(o)])==1
    data=json.loads(o.read_text(encoding='utf-8')); assert data['env_membership_checked'] is False and data['eligible_for_future_destination_binding_proof_task'] is False
def test_cli_deterministic_no_check(tmp_path):
    i=tmp_path/'in.json'; o1=tmp_path/'o1.json'; o2=tmp_path/'o2.json'; i.write_text(json.dumps(_accepted()), encoding='utf-8')
    assert main(['--credential-presence-membership-scaffold-bundle',str(i),'--output',str(o1)])==1; assert main(['--credential-presence-membership-scaffold-bundle',str(i),'--output',str(o2)])==1
    assert json.loads(o1.read_text(encoding='utf-8'))==json.loads(o2.read_text(encoding='utf-8'))
def test_static_process_env_membership_only():
    src=Path('live_contentops/exact_env_key_membership_check_gate_v6.py').read_text(encoding='utf-8-sig'); tree=ast.parse(src)
    forbidden_attrs={'getenv','get','keys','items','values'}
    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript) and ast.get_source_segment(src,n.value) in {'os.environ','PROCESS_ENV'}: raise AssertionError('env subscript forbidden')
        if isinstance(n, (ast.For, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            text=ast.get_source_segment(src,n) or ''; assert 'os.environ' not in text, text
        if isinstance(n, ast.Call):
            text=ast.get_source_segment(src,n) or ''; assert not any(x in text for x in ['os.getenv','getenv(','os.environ.get','dict(os.environ)','list(os.environ)','os.environ.keys','os.environ.items','os.environ.values']), text
    assert 'key_name in PROCESS_ENV' in src
    assert 'os.environ' not in src and 'os.getenv' not in src and 'getenv(' not in src
    for bad in ['keyring','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api/webhooks','discordapp.com/api/webhooks','requests.post','fetch(','curl ','Authorization','Content-Type','POST']:
        assert bad.lower() not in src.lower(), bad
    assert 'import dotenv' not in src.lower() and 'from dotenv' not in src.lower()
def test_docs_sample_hygiene():
    base=Path('docs/automation/V6_EXACT_ENV_KEY_MEMBERSHIP_CHECK_GATE_FROM_CREDENTIAL_MEMBERSHIP_SCAFFOLD_HEAVY_BATCH_MEMBERSHIP_ONLY_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE')
    paths=[base/'implementation_report.md', base/'exact_env_key_membership_check_gate_contract.md', base/'sample_exact_env_key_membership_check_gate_bundle.json', Path('docs/runbooks/V6_EXACT_ENV_KEY_MEMBERSHIP_CHECK_GATE_OPERATOR_RUNBOOK_MEMBERSHIP_ONLY_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE.md')]
    for p in paths:
        raw=p.read_bytes(); assert not raw.startswith(b'\xef\xbb\xbf'), p; assert '`n' not in raw.decode('utf-8'), p
    txt=paths[-1].read_text(encoding='utf-8').lower();
    for phrase in ['membership check only','exact key names only','no values','no .env','no credential values','no provider','no dispatch','no live send','future destination binding proof task separate']: assert phrase in txt
    sample=json.loads((base/'sample_exact_env_key_membership_check_gate_bundle.json').read_text(encoding='utf-8')); assert sample['env_membership_checked'] is False and sample['eligible_for_future_destination_binding_proof_task'] is False