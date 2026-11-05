"""Run the existing exact operation once, retaining an actionable exception trace."""
import json
from pathlib import Path
import sys
import traceback

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root.parents[3]))
from scripts.run_native_desktop_editorial import operation

binding = json.loads(Path(r'A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-next-article-20261105-d\binding.json').read_bytes())
rollout = json.loads(Path('config/native_desktop_rollout_v1.json').read_bytes())
try:
    result = operation(binding, command='publication-resume', rollout=rollout, native_invocation_id='/root')
except Exception:
    trace = traceback.format_exc()
    (root / 'publication-resume-trace.txt').write_text(trace, encoding='utf-8')
    print(trace)
    raise SystemExit(1)
(root / 'publication-resume-traced.json').write_text(json.dumps(result), encoding='utf-8')
publication = result.get('publication') or result
print(json.dumps({'classification': result.get('classification'), 'state': publication.get('state'),
    'pending': [{'destination': p['request']['destination'], 'action': p['request']['action'],
                 'request_sha256': p['request']['request_sha256'], 'tool_request_sha256': p.get('tool_request_sha256')}
                for p in publication.get('pending_requests', [])]}))
