import ast,json
from dataclasses import asdict
from pathlib import Path
from live_contentops.endpoint_allowlist_gate_from_official_provider_docs_scope_v6 import *
from live_contentops.official_provider_docs_scope_gate_from_provider_scoped_prep_v6 import make_official_provider_docs_scope_gate_bundle, official_docs_fixture
from tests.test_official_provider_docs_scope_gate_from_provider_scoped_prep_v6 import _valid as _docs_valid
SAMPLE=Path('docs/automation/V6_OFFICIAL_PROVIDER_DOCS_SCOPE_GATE_FROM_PROVIDER_SCOPED_PREP_HEAVY_BATCH_DOCS_ONLY_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_official_provider_docs_scope_gate_bundle.json')
def _default(): return json.loads(SAMPLE.read_text(encoding='utf-8'))
def _valid(): return asdict(make_official_provider_docs_scope_gate_bundle(_docs_valid(), official_docs_fixture()))
def _gate(u=None): return make_endpoint_allowlist_gate_bundle(_valid() if u is None else u)
def test_static_no_forbidden_runtime_code():
 src=Path('live_contentops/endpoint_allowlist_gate_from_official_provider_docs_scope_v6.py').read_text(encoding='utf-8-sig'); ast.parse(src); low=src.lower()
 for bad in ['import os','from os','os.environ','os.getenv','getenv(','.env','import dotenv','from dotenv','keyring','discord.py','telebot','telegram.ext','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api','api/webhooks','requests.post','fetch(','curl ','authorization','content-type','post ','get ','/bots/','/webhooks/','payload_file','payload_path','read_bytes(','retry policy','request budget','timeout','background worker','live button','scheduler','queue']: assert bad not in low, bad
