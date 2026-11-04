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
def test_malformed_non_object_json_cli_fails_closed(tmp_path):
    inp=tmp_path/'bad.json'; out=tmp_path/'out.json'; inp.write_text('[]', encoding='utf-8')
    assert main(['--destination-binding-review-scaffold-bundle', str(inp), '--output', str(out)])==1
    data=json.loads(out.read_text(encoding='utf-8')); assert data['eligible_for_future_env_membership_check_task'] is False and data['eligible_for_future_dispatch_execution_task'] is False and data['eligible_for_live_send_now'] is False
def test_static_no_env_provider_network_browser_request_patterns():
    src=Path('live_contentops/credential_presence_membership_scaffold_from_destination_binding_v6.py').read_text(encoding='utf-8')
    for pat in [r'^import os$', r'getenv', r'environ', r'dotenv', r'keyring', r'requests', r'urllib', r'httpx', r'webbrowser', r'selenium', r'playwright', r'discord(?:app)?\.com/api/webhooks', r'requests\.post', r'fetch\(', r'curl ', r'Authorization', r'Content-Type', r'\bPOST\b']:
        assert re.search(pat, src, re.M|re.I) is None, pat
def test_static_no_hardcoded_endpoint_or_executable_pattern():
    src=Path('live_contentops/credential_presence_membership_scaffold_from_destination_binding_v6.py').read_text(encoding='utf-8')
    for pat in [r'discord(?:app)?\.com/api/webhooks', r'https?://', r'\bPOST\b', r'headers\s*=', r'body\s*=', r'curl\s', r'fetch\(', r'requests\.']:
        assert re.search(pat, src, re.I) is None, pat
