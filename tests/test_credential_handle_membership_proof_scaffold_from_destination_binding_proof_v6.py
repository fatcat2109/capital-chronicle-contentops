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
def test_malformed_non_object_cli(tmp_path):
    i=tmp_path/'bad.json'; o=tmp_path/'out.json'; i.write_text('[]', encoding='utf-8'); assert main(['--destination-binding-proof-scaffold-bundle',str(i),'--output',str(o)])==1
    d=json.loads(o.read_text(encoding='utf-8')); assert d['credential_handle_membership_proof_status']=='blocked_invalid_destination_binding_proof_scaffold'; assert d['eligible_for_future_payload_hash_revalidation_gate_task'] is False
def test_static_no_env_provider_network_browser():
    src=Path('live_contentops/credential_handle_membership_proof_scaffold_from_destination_binding_proof_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
    for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ']: assert bad not in low, bad
