import ast,json
from dataclasses import asdict
from pathlib import Path
from live_contentops.dispatch_execution_preparation_gate_from_redacted_audit_kill_switch_manual_fallback_v6 import *
from live_contentops.redacted_audit_kill_switch_manual_fallback_gate_from_exact_operator_go_v6 import make_redacted_audit_kill_switch_manual_fallback_gate_bundle
from tests.test_redacted_audit_kill_switch_manual_fallback_gate_from_exact_operator_go_v6 import _valid as _exact_valid
SAMPLE=Path('docs/automation/V6_REDACTED_AUDIT_KILL_SWITCH_MANUAL_FALLBACK_GATE_FROM_EXACT_OPERATOR_GO_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_redacted_audit_kill_switch_manual_fallback_gate_bundle.json')
def _default(): return json.loads(SAMPLE.read_text(encoding='utf-8'))
def _valid(): return asdict(make_redacted_audit_kill_switch_manual_fallback_gate_bundle(_exact_valid()))
def _gate(u=None): return make_dispatch_execution_preparation_gate_bundle(_valid() if u is None else u)
def test_malformed_non_object_upstream_and_cli(tmp_path):
    assert 'redacted_audit_kill_switch_manual_fallback_gate_bundle_not_object' in _gate([]).blockers
    inp=tmp_path/'in.json'; out=tmp_path/'out.json'; inp.write_text('[]',encoding='utf-8'); assert main(['--redacted-audit-kill-switch-manual-fallback-gate-bundle',str(inp),'--output',str(out)])==1
    assert json.loads(out.read_text(encoding='utf-8'))['eligible_for_future_provider_scoped_dispatch_execution_task'] is False
def test_static_no_env_provider_network_browser_payload_body_reads():
    src=Path('live_contentops/dispatch_execution_preparation_gate_from_redacted_audit_kill_switch_manual_fallback_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
    for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ','payload_file','payload_path','read_bytes(','retry policy','background worker','live button']: assert bad not in low, bad
