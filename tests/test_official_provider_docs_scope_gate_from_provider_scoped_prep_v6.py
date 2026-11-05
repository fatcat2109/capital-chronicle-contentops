import ast,json
from dataclasses import asdict
from pathlib import Path
from live_contentops.official_provider_docs_scope_gate_from_provider_scoped_prep_v6 import *
from live_contentops.provider_scoped_dispatch_execution_gate_prep_from_dispatch_preparation_v6 import make_provider_scoped_dispatch_execution_gate_prep_bundle
from live_contentops.dispatch_execution_preparation_gate_from_redacted_audit_kill_switch_manual_fallback_v6 import make_dispatch_execution_preparation_gate_bundle
from tests.test_dispatch_execution_preparation_gate_from_redacted_audit_kill_switch_manual_fallback_v6 import _valid as _dispatch_valid
SAMPLE=Path('docs/automation/V6_PROVIDER_SCOPED_DISPATCH_EXECUTION_GATE_PREP_FROM_DISPATCH_PREPARATION_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_provider_scoped_dispatch_execution_gate_prep_bundle.json')
def _default(): return json.loads(SAMPLE.read_text(encoding='utf-8'))
def _valid(): return asdict(make_provider_scoped_dispatch_execution_gate_prep_bundle(asdict(make_dispatch_execution_preparation_gate_bundle(_dispatch_valid()))))
def _gate(u=None,d=None): return make_official_provider_docs_scope_gate_bundle(_valid() if u is None else u, official_docs_fixture() if d is None else d)
def test_static_no_forbidden_runtime_code():
 src=Path('live_contentops/official_provider_docs_scope_gate_from_provider_scoped_prep_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
 for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','discord.py','telebot','telegram.ext','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ','payload_file','payload_path','read_bytes(','retry policy','request budget','timeout','background worker','live button','scheduler','queue']: assert bad not in low, bad
