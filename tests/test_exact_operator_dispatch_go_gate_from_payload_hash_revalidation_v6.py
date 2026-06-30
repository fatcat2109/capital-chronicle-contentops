import ast,json
from dataclasses import asdict
from pathlib import Path
from live_contentops.exact_operator_dispatch_go_gate_from_payload_hash_revalidation_v6 import *
from live_contentops.payload_hash_revalidation_gate_from_credential_handle_membership_proof_v6 import make_payload_hash_revalidation_gate_bundle
from tests.test_payload_hash_revalidation_gate_from_credential_handle_membership_proof_v6 import _proof_present, _proof_missing
SAMPLE=Path('docs/automation/V6_PAYLOAD_HASH_REVALIDATION_GATE_FROM_CREDENTIAL_HANDLE_MEMBERSHIP_PROOF_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_payload_hash_revalidation_gate_bundle.json')
def _default(): return json.loads(SAMPLE.read_text(encoding='utf-8'))
def _upstream_present(): return asdict(make_payload_hash_revalidation_gate_bundle(_proof_present()))
def _upstream_missing(): return asdict(make_payload_hash_revalidation_gate_bundle(_proof_missing()))
def _decl(u=None):
    u=u or _upstream_present(); exp=expected_sets(u)
    return dict(schema_version=SCHEMA_VERSION,operator_go_declaration_id='exact_operator_go_declaration_local_fixture_001',operator_go_phrase=GO_PHRASE,operator_name_or_role='Jim',approved_task_label=TASK_LABEL,source_payload_hash_revalidation_gate_bundle_id=u['payload_hash_revalidation_gate_bundle_id'],timestamp_or_fixture_id='local_fixture_exact_operator_go_001',human_review_required=True,**exp)
def _bundle(u=None,d=None):
    u=u or _upstream_present(); return make_exact_operator_dispatch_go_gate_bundle(u, _decl(u) if d is None else d)
def test_default_committed_sample_blocked_no_go():
    b=make_exact_operator_dispatch_go_gate_bundle(_default(),{}); assert b.exact_operator_dispatch_go_gate_status=='blocked_invalid_payload_hash_revalidation_or_operator_go_declaration'; assert b.exact_operator_dispatch_go_records==[]; assert b.operator_go_phrase_exact_match is False; assert b.eligible_for_future_redacted_audit_kill_switch_manual_fallback_gate_task is False; assert b.dispatch_allowed is False and b.live_send_allowed is False and b.publication_ready is False
def test_valid_all_present_exact_go_records_only_no_value_leak():
    b=_bundle(); s=json.dumps(asdict(b)); assert b.exact_operator_dispatch_go_gate_status==GO_STATUS; assert b.operator_go_phrase_exact_match is True; assert b.all_required_exact_operator_go_records_available is True; assert b.eligible_for_future_redacted_audit_kill_switch_manual_fallback_gate_task is True
    assert b.eligible_for_future_dispatch_execution_task is False and b.eligible_for_live_send_now is False and len(b.exact_operator_dispatch_go_records)==3
    assert sorted(b.proof_available_key_names)==['DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK','TELEGRAM_BOT_TOKEN','TELEGRAM_CHAT_ID']; assert 'fake-secret-value' not in s and 'payload body content' not in s.lower()
    for r in b.exact_operator_dispatch_go_records:
        assert r['operator_go_phrase_exact_match'] is True and r['operator_go_gate_status']==GO_STATUS and r['eligible_for_future_redacted_audit_kill_switch_manual_fallback_gate_task'] is True
        assert r['symbolic_destination_binding_id'].startswith('symbolic_destination_binding_required_later_') and r['symbolic_credential_handle_id'].startswith('symbolic_credential_handle_required_later_')
def test_go_phrase_exact_failures():
    u=_upstream_present()
    for phrase in ['jim_exact_go_for_future_dispatch_gate_only_no_provider_no_dispatch_no_live',GO_PHRASE+' ',GO_PHRASE[:-8],'WRONG','']:
        d=_decl(u); d['operator_go_phrase']=phrase; b=make_exact_operator_dispatch_go_gate_bundle(u,d); assert b.operator_go_phrase_exact_match is False; assert 'operator_go_declaration_phrase_not_exact' in b.blockers; assert b.eligible_for_future_redacted_audit_kill_switch_manual_fallback_gate_task is False
def test_declaration_list_mismatches_fail_closed():
    for key in ['approved_payload_hashes','approved_payload_preview_ids','symbolic_destination_binding_ids','symbolic_credential_handle_ids','required_env_key_names']:
        u=_upstream_present(); d=_decl(u); d[key]=d[key][1:]; assert f'operator_go_declaration_{key}_mismatch' in make_exact_operator_dispatch_go_gate_bundle(u,d).blockers
        d=_decl(u); d[key]=d[key]+['extra_symbolic_fixture_only']; assert f'operator_go_declaration_{key}_mismatch' in make_exact_operator_dispatch_go_gate_bundle(u,d).blockers
def test_missing_malformed_non_object_operator_declaration_and_cli(tmp_path):
    u=_upstream_present(); assert 'operator_go_declaration_not_object' in make_exact_operator_dispatch_go_gate_bundle(u,[]).blockers
    d=_decl(u); del d['operator_go_phrase']; assert 'operator_go_declaration_phrase_not_exact' in make_exact_operator_dispatch_go_gate_bundle(u,d).blockers
    inp=tmp_path/'u.json'; dec=tmp_path/'d.json'; out=tmp_path/'out.json'; inp.write_text(json.dumps(u),encoding='utf-8'); dec.write_text('[]',encoding='utf-8'); assert main(['--payload-hash-revalidation-gate-bundle',str(inp),'--operator-go-declaration',str(dec),'--output',str(out)])==1
    assert json.loads(out.read_text(encoding='utf-8'))['eligible_for_future_redacted_audit_kill_switch_manual_fallback_gate_task'] is False
def test_upstream_fail_closed_cases():
    assert _bundle(_upstream_missing()).eligible_for_future_redacted_audit_kill_switch_manual_fallback_gate_task is False
    for mutate, blocker in [(lambda u:u.update(task_label='WRONG'),'payload_hash_revalidation_gate_bundle_task_label_invalid'),(lambda u:u.update(schema_version='5.0.0'),'payload_hash_revalidation_gate_bundle_schema_version_invalid'),(lambda u:u.update(all_required_payload_hash_revalidations_available=False),'payload_hash_revalidation_gate_bundle_revalidations_not_available'),(lambda u:u.update(payload_hash_revalidation_records=[]),'payload_hash_revalidation_gate_bundle_records_empty')]:
        u=_upstream_present(); mutate(u); assert blocker in make_exact_operator_dispatch_go_gate_bundle(u,_decl(_upstream_present())).blockers
    assert 'payload_hash_revalidation_gate_bundle_not_object' in make_exact_operator_dispatch_go_gate_bundle([],_decl(_upstream_present())).blockers
def test_record_symbolic_availability_flags_fail_closed():
    cases=[('symbolic_destination_binding_id','realish','payload_hash_revalidation_record_symbolic_destination_binding_id_invalid'),('symbolic_credential_handle_id','realish','payload_hash_revalidation_record_symbolic_credential_handle_id_invalid'),('payload_hash_revalidated_for_future_exact_operator_dispatch_go_only',False,'payload_hash_revalidation_record_revalidated_not_true'),('payload_hash_format_valid',False,'payload_hash_revalidation_record_hash_format_not_true'),('approved_payload_hash','abc','payload_hash_revalidation_record_approved_payload_hash_invalid')]
    for k,v,blk in cases:
        u=_upstream_present(); u['payload_hash_revalidation_records'][0][k]=v; assert any(blk in b for b in make_exact_operator_dispatch_go_gate_bundle(u,_decl(_upstream_present())).blockers)
def test_forbidden_text_no_echo():
    for term in ('endpoint','webhook','token','channel','account','https://example.invalid/x','metrics','browser profile','provider config','secret file','env line','credential value','env value','public url','payload body','live-send','executable request','curl','fetch','requests'):
        u=_upstream_present(); d=_decl(u); d['timestamp_or_fixture_id']=term; blockers=make_exact_operator_dispatch_go_gate_bundle(u,d).blockers; assert any('forbidden_' in b for b in blockers); assert term not in ' '.join(blockers)
def test_flags_false_every_case():
    for b in [_bundle(), _bundle(_upstream_missing()), make_exact_operator_dispatch_go_gate_bundle(_default(),{})]:
        for f in ['credential_value_read','credential_value_stored','credential_value_logged','env_read','dotenv_read','env_iterated','provider_call_made','network_call_made','browser_session_used','executable_request_artifact_created','endpoint_url_present','webhook_url_present','channel_id_present','account_id_present','token_present','payload_body_present','public_url_created','metrics_created','publication_ready','dispatch_allowed','live_send_allowed','runtime_truth','eligible_for_future_dispatch_execution_task','eligible_for_live_send_now']:
            assert getattr(b,f) is False, f
def test_static_no_env_provider_network_browser_payload_body_reads():
    src=Path('live_contentops/exact_operator_dispatch_go_gate_from_payload_hash_revalidation_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
    for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ','payload_file','payload_path','read_bytes(']: assert bad not in low, bad
def test_docs_sample_hygiene():
    base=Path('docs/automation/V6_EXACT_OPERATOR_DISPATCH_GO_GATE_FROM_PAYLOAD_HASH_REVALIDATION_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE')
    paths=[base/'implementation_report.md',base/'exact_operator_dispatch_go_gate_contract.md',base/'sample_exact_operator_dispatch_go_gate_bundle.json',Path('docs/runbooks/V6_EXACT_OPERATOR_DISPATCH_GO_GATE_OPERATOR_RUNBOOK_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE.md')]
    for p in paths:
        raw=p.read_bytes(); assert not raw.startswith(b'\xef\xbb\xbf'), p; txt=raw.decode('utf-8'); assert '`n' not in txt
        for bad in ['https://','discord.com/api','api/webhooks','Bearer ','fake-secret-value','payload body content','public url','metrics endpoint']: assert bad.lower() not in txt.lower(), (p,bad)
    d=json.loads(paths[2].read_text(encoding='utf-8')); assert d['exact_operator_dispatch_go_gate_status']=='blocked_invalid_payload_hash_revalidation_or_operator_go_declaration'; assert d['eligible_for_future_redacted_audit_kill_switch_manual_fallback_gate_task'] is False
