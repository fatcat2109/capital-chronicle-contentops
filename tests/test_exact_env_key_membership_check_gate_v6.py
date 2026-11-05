import ast, json
from dataclasses import asdict
from pathlib import Path
from live_contentops.exact_env_key_membership_check_gate_v6 import *
from live_contentops.credential_presence_membership_scaffold_from_destination_binding_v6 import make_credential_presence_membership_scaffold_bundle, asdict as m_asdict
from live_contentops.destination_binding_review_scaffold_from_dispatch_gate_v6 import make_destination_binding_review_scaffold_bundle
from live_contentops.dispatch_gate_scaffold_from_prepared_outbox_v6 import make_dispatch_gate_scaffold_bundle
from tests.test_dispatch_gate_scaffold_from_prepared_outbox_v6 import _accepted_outbox
SAMPLE=Path('docs/automation/V6_CREDENTIAL_PRESENCE_MEMBERSHIP_SCAFFOLD_FROM_DESTINATION_BINDING_REVIEW_HEAVY_BATCH_NO_ENV_READ_NO_CREDENTIAL_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE/sample_credential_presence_membership_scaffold_bundle.json')
def _default(): return json.loads(SAMPLE.read_text(encoding='utf-8'))
def _accepted():
    d=asdict(make_destination_binding_review_scaffold_bundle(asdict(make_dispatch_gate_scaffold_bundle(_accepted_outbox()))))
    return m_asdict(make_credential_presence_membership_scaffold_bundle(d))
def _bundle(m=None, **kw): return make_exact_env_key_membership_check_gate_bundle(m or _accepted(), **kw)
def test_malformed_non_object_cli(tmp_path):
    i=tmp_path/'bad.json'; o=tmp_path/'out.json'; i.write_text('[]', encoding='utf-8'); assert main(['--credential-presence-membership-scaffold-bundle',str(i),'--output',str(o)])==1
    data=json.loads(o.read_text(encoding='utf-8')); assert data['env_membership_checked'] is False and data['eligible_for_future_destination_binding_proof_task'] is False
def test_static_process_env_membership_only():
    src=Path('live_contentops/exact_env_key_membership_check_gate_v6.py').read_text(encoding='utf-8-sig'); tree=ast.parse(src)
    forbidden_attrs={'getenv','get','keys','items','values'}
    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript) and ast.get_source_segment(src,n.value) in {'os.environ','PROCESS_ENV'}: raise AssertionError('env subscript forbidden')
        if isinstance(n, (ast.For, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            text=ast.get_source_segment(src,n) or ''; assert 'os.environ' not in text, text
        if isinstance(n, ast.Call):
            text=ast.get_source_segment(src,n) or ''; assert not any(x in text for x in ['os.getenv','getenv(','os.environ.get','dict(os.environ)','list(os.environ)','os.environ.keys','os.environ.items','os.environ.values']), text
    assert 'key_name in PROCESS_ENV' in src
    assert 'os.environ' not in src and 'os.getenv' not in src and 'getenv(' not in src
    for bad in ['keyring','requests','urllib','httpx','webbrowser','selenium','playwright','discord.com/api/webhooks','discordapp.com/api/webhooks','requests.post','fetch(','curl ','Authorization','Content-Type','POST']:
        assert bad.lower() not in src.lower(), bad
    assert 'import dotenv' not in src.lower() and 'from dotenv' not in src.lower()
