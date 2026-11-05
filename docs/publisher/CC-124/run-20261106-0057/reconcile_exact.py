"""Consume exact existing readbacks through the sole coordinator; never publish."""
from pathlib import Path
import json
import sys
from uuid import uuid4

root = Path(__file__).resolve().parent
sys.path.insert(0, r"A:\Capital Chronicle\ContentOps")
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_publication_v1 import NativeReviewedPublication
from live_contentops.native_finished_publication_v1 import newsroom_lease
from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired

label, *destinations = sys.argv[1:]
assert label.replace('-', '').isalnum()
assert destinations and set(destinations) <= {'substack', 'linkedin', 'linkedin_company', 'x', 'youtube'}
binding = json.loads(Path(r'A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-bitcoin-rates-20261106-h\binding.json').read_bytes())
rollout = json.loads(Path(r"A:\Capital Chronicle\ContentOps\config\native_desktop_rollout_v1.json").read_bytes())
store = ContentOpsDurableStore(binding['store_path'], auto_migrate=False)
publication = NativeReviewedPublication(store, binding, native_invocation_id='/root', rollout=rollout)
owner = 'native-desktop-' + uuid4().hex
outcomes = []
with newsroom_lease(store):
    lease = store.acquire_lease('internal:native-editorial:' + binding['run_id'], owner, ttl_seconds=900)
    try:
        plan, _ = publication.validate()
        publication._authorize_and_bind()
        for destination in destinations:
            dispatch = publication.coordinator._ids(binding['run_id'], plan['plan_hash'], destination)['dispatch_id']
            try:
                result = publication.coordinator.readback_existing_dispatch(dispatch)
                if destination == 'substack' and result.get('reconciliation_status') == 'RECONCILED_CONFIRMED':
                    result['published_content_record'] = publication.coordinator.sync_published_content(binding['run_id'])
            except NativeNeoInputRequired as pending:
                result = {'destination': destination, 'status': 'NATIVE_NEO_TOOL_PENDING',
                          'native_tool_request': pending.request}
            outcomes.append(result)
    finally:
        store.release_lease(lease['lease_id'], owner, lease['fencing_token'])
projection = publication.projection()
(root / (label + '.json')).write_text(json.dumps({'outcomes': outcomes, 'publication': projection,
    'public_write_performed': False}), encoding='utf-8')
print(json.dumps({'outcomes': [{k: r.get(k) for k in ('destination', 'status', 'reconciliation_status')} for r in outcomes],
    'unknown_write_count': projection['unknown_write_count'],
    'pending': [{'destination': p['request']['destination'], 'action': p['request']['action'],
                'request_sha256': p['request']['request_sha256'], 'tool_request_sha256': p.get('tool_request_sha256')}
               for p in projection['pending_requests']]}))
