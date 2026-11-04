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
def test_static_no_env_provider_network_browser_payload_body_reads():
    src=Path('live_contentops/exact_operator_dispatch_go_gate_from_payload_hash_revalidation_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
    for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ','payload_file','payload_path','read_bytes(']: assert bad not in low, bad
