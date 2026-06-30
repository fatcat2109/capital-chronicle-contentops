import json, re
from dataclasses import asdict
from pathlib import Path
from live_contentops.destination_binding_review_scaffold_from_dispatch_gate_v6 import make_destination_binding_review_scaffold_bundle
from live_contentops.dispatch_gate_scaffold_from_prepared_outbox_v6 import make_dispatch_gate_scaffold_bundle
from live_contentops.credential_presence_membership_scaffold_from_destination_binding_v6 import *
from tests.test_dispatch_gate_scaffold_from_prepared_outbox_v6 import _accepted_outbox
SAMPLE_DESTINATION=Path('docs/automation/V6_DESTINATION_BINDING_REVIEW_SCAFFOLD_FROM_DISPATCH_GATE_HEAVY_BATCH_NO_ENV_NO_CREDENTIAL_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_destination_binding_review_scaffold_bundle.json')
SAMPLE_MEMBERSHIP=Path('docs/automation/V6_CREDENTIAL_PRESENCE_MEMBERSHIP_SCAFFOLD_FROM_DESTINATION_BINDING_REVIEW_HEAVY_BATCH_NO_ENV_READ_NO_CREDENTIAL_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_credential_presence_membership_scaffold_bundle.json')
def _default_destination(): return json.loads(SAMPLE_DESTINATION.read_text(encoding='utf-8'))
def _accepted_destination():
    data=asdict(make_destination_binding_review_scaffold_bundle(asdict(make_dispatch_gate_scaffold_bundle(_accepted_outbox())))); data['warnings'].append('synthetic_test_fixture_only'); return data
def _bundle(d=None): return make_credential_presence_membership_scaffold_bundle(d or _accepted_destination())
def test_default_sample_blocked_no_membership_records():
    b=make_credential_presence_membership_scaffold_bundle(_default_destination())
    assert b.credential_presence_membership_status=='blocked_no_credential_presence_membership_records'; assert b.credential_presence_membership_records==[]; assert b.eligible_for_future_env_membership_check_task is False
    assert b.eligible_for_future_dispatch_execution_task is False and b.eligible_for_live_send_now is False
    assert b.credential_presence_check_performed_now is False and b.credential_presence_confirmed_now is False
    assert b.env_read is False and b.dotenv_read is False and b.credential_value_read is False and b.credential_value_stored is False and b.credential_value_logged is False
    assert 'destination_binding_review_bundle_status_not_ready' in b.blockers
def test_accepted_synthetic_destination_creates_membership_records():
    b=_bundle(); assert b.blockers==[]; assert b.credential_presence_membership_status=='ready_for_future_env_membership_check_only'; assert b.eligible_for_future_env_membership_check_task is True
    assert b.eligible_for_future_dispatch_execution_task is False and b.eligible_for_live_send_now is False
    assert b.credential_presence_check_performed_now is False and b.credential_presence_confirmed_now is False and b.env_read is False and b.dotenv_read is False
    assert b.credential_value_read is False and b.credential_value_stored is False and b.credential_value_logged is False
    assert b.provider_call_made is False and b.network_call_made is False and b.browser_session_used is False and b.executable_request_artifact_created is False
    assert b.endpoint_url_present is False and b.webhook_url_present is False and b.channel_id_present is False and b.account_id_present is False and b.token_present is False and b.payload_body_present is False
    assert b.publication_ready is False and b.dispatch_allowed is False and b.live_send_allowed is False
    keys={r['required_env_key_name'] for r in b.credential_presence_membership_records}; assert keys <= ALLOWED_REQUIRED_ENV_KEY_NAMES; assert {'DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK'} <= keys
    for r in b.credential_presence_membership_records: assert validate_credential_presence_membership_record(r)==[]
def test_bundle_status_records_eligibility_fail_closed():
    d=_accepted_destination(); d['destination_binding_review_status']='blocked'; assert 'destination_binding_review_bundle_status_not_ready' in _bundle(d).blockers
    d=_accepted_destination(); d['destination_binding_review_records']=[]; assert 'destination_binding_review_bundle_records_empty' in _bundle(d).blockers
    d=_accepted_destination(); d['eligible_for_future_credential_presence_membership_task']=False; assert 'destination_binding_review_bundle_future_credential_presence_membership_eligibility_not_true' in _bundle(d).blockers
    d=_accepted_destination(); d['eligible_for_future_dispatch_execution_task']=True; assert 'destination_binding_review_bundle_eligible_for_future_dispatch_execution_task_not_false' in _bundle(d).blockers
def test_bundle_hard_false_flags_fail_closed():
    for f in UPSTREAM_FALSE_FLAGS:
        d=_accepted_destination(); d[f]=True; assert f'destination_binding_review_bundle_{f}_not_false' in _bundle(d).blockers
def test_record_required_later_and_presence_flags_fail_closed():
    for f in RECORD_TRUE_FLAGS:
        d=_accepted_destination(); d['destination_binding_review_records'][0][f]=False; assert f'record_0_destination_binding_review_record_{f}_not_true' in _bundle(d).blockers
    for f in ('destination_binding_present','credential_handle_present','env_read','credential_value_read','endpoint_url_present','webhook_url_present','channel_id_present','account_id_present','token_present','payload_body_present','public_url_created','metrics_created'):
        d=_accepted_destination(); d['destination_binding_review_records'][0][f]=True; assert f'record_0_destination_binding_review_record_{f}_not_false' in _bundle(d).blockers
def test_record_blockers_missing_sources_unsupported_platform_fail_closed():
    d=_accepted_destination(); d['destination_binding_review_records'][0]['blockers']=['x']; assert 'record_0_destination_binding_review_record_blockers_not_empty' in _bundle(d).blockers
    for k in ('source_dispatch_review_record_id','source_outbox_record_id','platform','approved_payload_preview_id','approved_payload_hash'):
        d=_accepted_destination(); d['destination_binding_review_records'][0][k]=''; assert any(k in b for b in _bundle(d).blockers)
    d=_accepted_destination(); d['destination_binding_review_records'][0]['platform']='unknown'; assert 'record_0_unsupported_platform_for_membership_scaffold' in _bundle(d).blockers
def test_membership_record_rejects_hard_flags_and_key_allowlist():
    r=_bundle().credential_presence_membership_records[0]
    for f in MEMBERSHIP_FALSE_FLAGS:
        x=dict(r); x[f]=True; assert f'credential_presence_membership_record_{f}_not_false' in validate_credential_presence_membership_record(x)
    x=dict(r); x['required_env_key_name']='BAD_KEY'; assert 'credential_presence_membership_record_required_env_key_name_not_allowlisted' in validate_credential_presence_membership_record(x)
def test_forbidden_text_fails_closed_without_echoing_raw_value():
    forbidden=('endpoint','webhook','token','channel','account','cookie','session','localStorage','browser profile','env value','credential value','https://example.invalid/x','metrics','financial advice','signal service','fake metrics','fake citations','live-send','payload body','curl','fetch','requests')
    for term in forbidden:
        d=_accepted_destination(); d['destination_binding_review_records'][0]['approved_payload_preview_id']=term; blockers=_bundle(d).blockers; assert any('forbidden_' in b for b in blockers); assert term not in ' '.join(blockers)
def test_malformed_non_object_json_cli_fails_closed(tmp_path):
    inp=tmp_path/'bad.json'; out=tmp_path/'out.json'; inp.write_text('[]', encoding='utf-8')
    assert main(['--destination-binding-review-scaffold-bundle', str(inp), '--output', str(out)])==1
    data=json.loads(out.read_text(encoding='utf-8')); assert data['eligible_for_future_env_membership_check_task'] is False and data['eligible_for_future_dispatch_execution_task'] is False and data['eligible_for_live_send_now'] is False
def test_cli_deterministic_output(tmp_path):
    inp=tmp_path/'in.json'; o1=tmp_path/'o1.json'; o2=tmp_path/'o2.json'; inp.write_text(json.dumps(_accepted_destination()), encoding='utf-8')
    assert main(['--destination-binding-review-scaffold-bundle', str(inp), '--output', str(o1)])==0; assert main(['--destination-binding-review-scaffold-bundle', str(inp), '--output', str(o2)])==0
    assert json.loads(o1.read_text(encoding='utf-8'))==json.loads(o2.read_text(encoding='utf-8'))
def test_static_no_env_provider_network_browser_request_patterns():
    src=Path('live_contentops/credential_presence_membership_scaffold_from_destination_binding_v6.py').read_text(encoding='utf-8')
    for pat in [r'^import os$', r'getenv', r'environ', r'dotenv', r'keyring', r'requests', r'urllib', r'httpx', r'webbrowser', r'selenium', r'playwright', r'discord(?:app)?\.com/api/webhooks', r'requests\.post', r'fetch\(', r'curl ', r'Authorization', r'Content-Type', r'\bPOST\b']:
        assert re.search(pat, src, re.M|re.I) is None, pat
def test_static_no_hardcoded_endpoint_or_executable_pattern():
    src=Path('live_contentops/credential_presence_membership_scaffold_from_destination_binding_v6.py').read_text(encoding='utf-8')
    for pat in [r'discord(?:app)?\.com/api/webhooks', r'https?://', r'\bPOST\b', r'headers\s*=', r'body\s*=', r'curl\s', r'fetch\(', r'requests\.']:
        assert re.search(pat, src, re.I) is None, pat
def test_docs_runbook_sample_hygiene():
    paths=['docs/runbooks/V6_CREDENTIAL_PRESENCE_MEMBERSHIP_SCAFFOLD_OPERATOR_RUNBOOK_NO_ENV_READ_NO_CREDENTIAL_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE.md','docs/automation/V6_CREDENTIAL_PRESENCE_MEMBERSHIP_SCAFFOLD_FROM_DESTINATION_BINDING_REVIEW_HEAVY_BATCH_NO_ENV_READ_NO_CREDENTIAL_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE/implementation_report.md','docs/automation/V6_CREDENTIAL_PRESENCE_MEMBERSHIP_SCAFFOLD_FROM_DESTINATION_BINDING_REVIEW_HEAVY_BATCH_NO_ENV_READ_NO_CREDENTIAL_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE/credential_presence_membership_scaffold_contract.md','docs/automation/V6_CREDENTIAL_PRESENCE_MEMBERSHIP_SCAFFOLD_FROM_DESTINATION_BINDING_REVIEW_HEAVY_BATCH_NO_ENV_READ_NO_CREDENTIAL_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_credential_presence_membership_scaffold_bundle.json']
    for p in paths:
        raw=Path(p).read_bytes(); assert not raw.startswith(b'\xef\xbb\xbf'), p; assert '`n' not in raw.decode('utf-8'), p
    txt=Path(paths[0]).read_text(encoding='utf-8').lower(); assert 'credential presence membership scaffold only' in txt and 'no env read' in txt and 'no .env read' in txt and 'no credential value read' in txt and 'no credential presence check now' in txt and 'no provider' in txt and 'no dispatch' in txt and 'no live send' in txt and 'future env membership check task separate' in txt
    sample=json.loads(SAMPLE_MEMBERSHIP.read_text(encoding='utf-8')); assert sample['credential_presence_membership_records']==[] and sample['eligible_for_future_env_membership_check_task'] is False