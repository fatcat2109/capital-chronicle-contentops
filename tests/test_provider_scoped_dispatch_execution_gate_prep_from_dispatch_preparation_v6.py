import ast,json
from dataclasses import asdict
from pathlib import Path
from live_contentops.provider_scoped_dispatch_execution_gate_prep_from_dispatch_preparation_v6 import *
from live_contentops.dispatch_execution_preparation_gate_from_redacted_audit_kill_switch_manual_fallback_v6 import make_dispatch_execution_preparation_gate_bundle
from tests.test_dispatch_execution_preparation_gate_from_redacted_audit_kill_switch_manual_fallback_v6 import _valid as _prep_valid
SAMPLE=Path('docs/automation/V6_DISPATCH_EXECUTION_PREPARATION_GATE_FROM_REDACTED_AUDIT_KILL_SWITCH_MANUAL_FALLBACK_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_dispatch_execution_preparation_gate_bundle.json')
def _default(): return json.loads(SAMPLE.read_text(encoding='utf-8'))
def _valid(): return asdict(make_dispatch_execution_preparation_gate_bundle(_prep_valid()))
def _gate(u=None): return make_provider_scoped_dispatch_execution_gate_prep_bundle(_valid() if u is None else u)
def test_malformed_non_object_upstream_and_cli(tmp_path):
    assert 'dispatch_execution_preparation_gate_bundle_not_object' in _gate([]).blockers
    inp=tmp_path/'in.json'; out=tmp_path/'out.json'; inp.write_text('[]',encoding='utf-8'); assert main(['--dispatch-execution-preparation-gate-bundle',str(inp),'--output',str(out)])==1
    assert json.loads(out.read_text(encoding='utf-8'))['eligible_for_future_official_provider_docs_scope_gate_task'] is False
def test_static_no_env_provider_network_browser_payload_body_or_runtime_strings():
    src=Path('live_contentops/provider_scoped_dispatch_execution_gate_prep_from_dispatch_preparation_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
    for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ','payload_file','payload_path','read_bytes(','retry policy','request budget','timeout','background worker','live button','scheduler','queue']: assert bad not in low, bad
