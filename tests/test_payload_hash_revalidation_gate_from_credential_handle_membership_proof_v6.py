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
def test_malformed_non_object_cli(tmp_path):
    i=tmp_path/'bad.json'; o=tmp_path/'out.json'; i.write_text('[]', encoding='utf-8'); assert main(['--credential-handle-membership-proof-scaffold-bundle',str(i),'--output',str(o)])==1
    d=json.loads(o.read_text(encoding='utf-8')); assert d['payload_hash_revalidation_status']=='blocked_invalid_credential_handle_membership_proof_scaffold'; assert d['eligible_for_future_exact_operator_dispatch_go_gate_task'] is False
def test_static_no_env_provider_network_browser_payload_body_reads():
    src=Path('live_contentops/payload_hash_revalidation_gate_from_credential_handle_membership_proof_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
    for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ','payload_file','payload_path','read_bytes(']: assert bad not in low, bad
