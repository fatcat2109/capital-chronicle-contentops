"""Bounded CC-384 acceptance readback; no public/store writes."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BUILDER = HERE.parents[3]
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
sys.path.insert(0, str(LIVE))
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.discord_live_adapter_v6 import readback_discord_post
from live_contentops.threads_adapter_v6 import readback_threads_post
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.published_content_v1 import PRODUCTION_STORE

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

assert Path(posts.__file__).resolve().is_relative_to(LIVE)
prior = json.loads((HERE.parent / 'resume-20261115/readbacks.json').read_text(encoding='utf-8-sig'))
telegram = json.loads((HERE / 'telegram-public-readback.json').read_text(encoding='utf-8'))
results = []
class ReadOnlyStore(ContentOpsDurableStore):
    get_connection = ContentOpsDurableStore.get_read_only_connection

store = ReadOnlyStore(PRODUCTION_STORE, auto_migrate=False)
for row in prior['destinations']:
    current = store.get_outbox_message(row['outbox_message_id'])
    assert current, row['destination']
    if row['destination'] == 'discord':
        result = readback_discord_post(message_id=row['public_object_id'], expected_text=row['expected_text'], canonical_url='')
        assert result['verified'] and result['body_text_visible'], result
    elif row['destination'] == 'threads':
        result = readback_threads_post(post_id=row['public_object_id'], expected_text=row['expected_text'])
        assert result['status'] == 'SUCCESS' and result['content_binding_checks']['text_match'], result
    else:
        assert row['expected_text'] in telegram['text']
        assert 'https://t.me/CapitalChronicle/114' in telegram['text']
        result = {'status': 'SUCCESS', 'text_match': True, 'object_url_match': True,
                  'public_surface': telegram['url'], 'evidence': 'telegram-public-readback.json'}
    results.append({'destination': row['destination'], 'object_id': row['public_object_id'],
                    'object_url': row['public_object_url'], 'outbox_message_id': row['outbox_message_id'],
                    'dispatch_id': row['dispatch_id'], 'expected_text_sha256': row['expected_text_sha256'],
                    'readback': result})
save('readbacks.json', {'observed_at_utc': datetime.now(timezone.utc).isoformat(),
                       'plan_id': prior['plan_id'], 'work_item_id': prior['work_item_id'],
                       'entries': prior['entries'], 'public_writes': 0, 'destinations': results})
export = posts.read_export()
plans = export['status']['plans']
with store.get_connection() as connection:
    retained = [json.loads(r['payload']) for r in connection.execute(
        'SELECT payload FROM outbox_messages WHERE destination=?', (posts.DESTINATION,))]
counts = Counter(len(p.get('entries') or []) for p in retained)
save('installed-export-read.json', {'observed_at_utc': datetime.now(timezone.utc).isoformat(),
    'reader': str(Path(posts.__file__).resolve()), 'generated_at_utc': export['status'].get('generated_at_utc'),
    'plans': len(plans), 'with_public_instrument': sum(bool(p.get('public_instrument')) for p in plans),
    'with_entries': sum(bool(p.get('entries')) for p in plans),
    'dual_entry_plans': sum(len(p.get('entries') or []) > 1 for p in plans),
    'retained_post_entry_counts': dict(counts), 'store_read_only': True})
files = list(json.loads((HERE.parent / 'resume-20261115/installed-consumer.json').read_text())['files'])
checks = {f: {'sha256': sha(LIVE/f), 'builder_bytes_match': sha(BUILDER/f) == sha(LIVE/f),
              'builder_text_matches_installed': (BUILDER/f).read_text(encoding='utf-8') == (LIVE/f).read_text(encoding='utf-8'),
              'installed_matches_committed': git(LIVE, 'hash-object', '--path', f, f) == git(LIVE, 'rev-parse', 'HEAD:'+f)} for f in files}
assert all(v['builder_text_matches_installed'] and v['installed_matches_committed'] for v in checks.values())
preserved = {}
for root, label in [(BUILDER, 'builder'), (LIVE, 'operating')]:
    paths = git(root, 'diff', '--name-only').splitlines()
    preserved[label] = {p: sha(root/p) for p in paths}
save('installed-consumer.json', {'observed_at_utc': datetime.now(timezone.utc).isoformat(),
    'operating_head': git(LIVE, 'rev-parse', 'HEAD'), 'branch_base': git(BUILDER, 'rev-parse', 'HEAD'),
    'branch_base_reason': 'Continue the integrated operating HEAD; remote master predates installed consumer changes.',
    'delivery_00eebb_ancestor': subprocess.run(['git', '-C', str(LIVE), 'merge-base', '--is-ancestor',
        '00eebb5571a2f5a441092f10a33d431112e71e99', 'HEAD']).returncode == 0,
    'files': checks, 'preserved_dirty': preserved})
print(json.dumps({'readbacks': {r['destination']: r['readback']['status'] for r in results},
                  'plans': len(plans), 'dual_entry_plans': sum(len(p.get('entries') or []) > 1 for p in plans),
                  'retained_post_entry_counts': dict(counts), 'installed_files_match': True}))
