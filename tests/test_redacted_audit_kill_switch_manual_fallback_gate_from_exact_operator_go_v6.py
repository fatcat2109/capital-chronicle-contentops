import ast,json
from dataclasses import asdict
from pathlib import Path
from live_contentops.redacted_audit_kill_switch_manual_fallback_gate_from_exact_operator_go_v6 import *
from tests.test_exact_operator_dispatch_go_gate_from_payload_hash_revalidation_v6 import _bundle as _exact_go_bundle
SAMPLE=Path('docs/automation/V6_EXACT_OPERATOR_DISPATCH_GO_GATE_FROM_PAYLOAD_HASH_REVALIDATION_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_exact_operator_dispatch_go_gate_bundle.json')
def _default(): return json.loads(SAMPLE.read_text(encoding='utf-8'))
def _valid(): return asdict(_exact_go_bundle())
def _gate(u=None): return make_redacted_audit_kill_switch_manual_fallback_gate_bundle(_valid() if u is None else u)
def test_malformed_non_object_upstream_and_cli(tmp_path):
    assert 'exact_operator_dispatch_go_gate_bundle_not_object' in _gate([]).blockers
    inp=tmp_path/'in.json'; out=tmp_path/'out.json'; inp.write_text('[]',encoding='utf-8'); assert main(['--exact-operator-dispatch-go-gate-bundle',str(inp),'--output',str(out)])==1
    assert json.loads(out.read_text(encoding='utf-8'))['eligible_for_future_dispatch_execution_preparation_gate_task'] is False
def test_static_no_env_provider_network_browser_payload_body_reads():
    src=Path('live_contentops/redacted_audit_kill_switch_manual_fallback_gate_from_exact_operator_go_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
    for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ','payload_file','payload_path','read_bytes(']: assert bad not in low, bad
