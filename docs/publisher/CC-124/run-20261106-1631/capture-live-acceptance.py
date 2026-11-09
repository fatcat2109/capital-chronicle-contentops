"""Prove this article feeds saved outcomes and the installed CC-122 consumer."""
import hashlib
import json
import subprocess
import sys
import types
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parents[3]))
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_newsroom_volume_v1 import persist_native_day_measurement
from live_contentops.neo_destination_handoff_v1 import _text
from live_contentops.published_content_v1 import PRODUCTION_STORE, DEFAULT_FEED, read_records

WORK = 'cc124-oil-euro-followup-20261106-v2'
URL = 'https://capitalchronicle.substack.com/p/capital-chronicles-pre-payrolls-review'
binding = json.loads(Path(r'A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-oil-euro-followup-20261106-v2\binding.json').read_bytes())
store = ContentOpsDurableStore(PRODUCTION_STORE, auto_migrate=False)
publication = json.loads((BASE/'publication-resume-08-expanded.json').read_bytes())['publication']
assert publication['state'] == 'RECONCILED' and not publication['pending_requests']
assert publication['unknown_write_count'] == 0
rows = []
with store.get_read_only_connection() as conn:
    records = conn.execute('SELECT d.dispatch_id,d.platform,d.status,d.public_object_id,d.public_object_url,d.dispatched_at '
        'FROM platform_dispatches d JOIN outbox_messages m ON d.message_id=m.message_id '
        'WHERE m.work_item_id=? ORDER BY d.platform', (WORK,)).fetchall()
    for record in records:
        item = dict(record)
        readbacks = []
        for r in conn.execute('SELECT read_at,readback_data FROM readbacks WHERE dispatch_id=? ORDER BY read_at', (item['dispatch_id'],)):
            saved = json.loads(r['readback_data']); rb = saved.get('readback') or saved
            readbacks.append({'read_at_utc': r['read_at'], **{k: rb[k] for k in ['verified','source_status','identity_match',
                'meaningful_media_visible','observed_public_object_id','observed_public_object_url','content_binding_checks'] if k in rb}})
        assert item['status'] == 'DISPATCH_CONFIRMED' and readbacks[-1].get('verified') is True, item['platform']
        item['readbacks'] = readbacks; rows.append(item)
assert len(rows) == 10
payload = json.loads((BASE/'substack-native-payload.json').read_bytes())
observed = json.loads((BASE/'substack-readback-final-response.json').read_bytes())['result']['observed_text']
remaining = _text(observed)
paragraphs = payload['body_markdown'].split('\n\n')
for paragraph in paragraphs:
    wanted = _text(paragraph); assert wanted in remaining, wanted[:70]
    remaining = remaining.split(wanted,1)[1]
assert all(_text(payload[k]) in _text(observed) for k in ['title','subtitle'])
day_path = Path(persist_native_day_measurement(store,binding))
day = json.loads(day_path.read_bytes()); measurement = day['native_volume_measurement']
assert measurement['distinct_canonical_items_published'] >= 3
assert any(r.get('public_object_id') == '223749516' and r['channel']=='substack' for r in measurement['reader_counts'])
feed = [r for r in read_records(DEFAULT_FEED) if any(o['name']=='substack' and o['url']==URL for o in r['outlets'])]
assert len(feed)==1

# Read installed Main source through this lane's shared Git metadata only.
# No Main operating-root file is opened, changed or executed in place.
main_git = r'A:\Capital Chronicle\Worktrees\codex-main-exec'
metadata = subprocess.check_output(['git','-C',main_git,'worktree','list','--porcelain'],text=True)
block = next(b for b in metadata.strip().split('\n\n') if b.splitlines()[0].lower() ==
             'worktree a:/capital chronicle/main-jim-research-dashboard-20261025')
head = next(l[5:] for l in block.splitlines() if l.startswith('HEAD '))
source = subprocess.check_output(['git','-C',main_git,'show',head+':tools/product/contentops_digest_v1.py'])
main_source = subprocess.check_output(['git','-C',main_git,'show',head+':tools/product/main_daily_digest_v1.py'])
module = types.ModuleType('cc124_installed_contentops_digest')
exec(compile(source,'installed-contentops-digest@'+head,'exec'), module.__dict__)
class Reader:
    def __init__(self): self.evidence = {}
    def read(self,path,label):
        raw = Path(path).read_bytes()
        self.evidence[str(path)] = {'label':label,'state':'READ','sha256':hashlib.sha256(raw).hexdigest()}
        return json.loads(raw)
reader = Reader(); now = datetime.now(timezone.utc)
consumer = module.collect_contentops(reader,record=day_path,store=Path(PRODUCTION_STORE),now=now)
assert consumer['state']=='SAVED_RECORD' and consumer['distinct_articles_published']==measurement['distinct_canonical_items_published']
assert consumer['confirmed_copies_by_channel']['substack']>=3
assert consumer['last_public_post']['state']=='SAVED_CONFIRMED_DISPATCH'
wiring = []
for number,line in enumerate(main_source.decode('utf-8').splitlines(),1):
    if 'contentops_digest_v1 import' in line or 'contentops = collect_contentops(' in line or "newsroom['distinct_articles_published']" in line:
        wiring.append({'line':number,'source':line.strip()})
assert len(wiring)==3
next_local_date = now.astimezone(module.LOCAL).date()+timedelta(days=1)
next_digest = datetime.combine(next_local_date,time(7),module.LOCAL)
# Pure path selection only uses the next scheduled instant. The consumer above
# reads current data with actual time; no future clock reaches a write owner.
assert module.default_production_record(next_digest)==day_path
digest = {'observed_at_utc':now.isoformat(),'installed_main_commit':head,
    'source_sha256':hashlib.sha256(source).hexdigest(),'main_daily_digest_source_sha256':hashlib.sha256(main_source).hexdigest(),
    'installed_wiring':wiring,'consumer':consumer,'reader_evidence':reader.evidence,
    'next_0700_GMT7':next_digest.isoformat(),'default_next_record':str(day_path),
    'path_selection_is_pure_forecast':True,'actual_consumer_clock_utc':now.isoformat(),
    'email_sent':False,'schedule_changed':False,'published_feed_rows':len(feed)}
(BASE/'cc122-digest-live-consumer.json').write_text(json.dumps(digest,indent=2)+'\n',encoding='utf-8')
approval = json.loads((BASE/'editor-check-result-repaired.json').read_bytes())['first_text_approval_utc']
result = {'observed_at_utc':now.isoformat(),'operation_id':WORK,'state':publication['state'],
    'canonical_url':URL,'unknown_write_count':0,'pending_requests':[], 'confirmed_destinations':rows,
    'substack_exact_prose':{'approved_paragraphs':len(paragraphs),'all_present_in_order':True,'title_match':True,'subtitle_match':True},
    'production_day':{'path':str(day_path),'record_sha256':day['record_sha256'],'day':day['newsroom_production_day_id'],
        'distinct_canonicals':measurement['distinct_canonical_items_published'],'new_canonical_in_consumer':True},
    'digest_consumer':{'evidence':'cc122-digest-live-consumer.json','email_sent':False,'installed_consumer_count':consumer['distinct_articles_published']},
    'publication_timing':{'first_text_approval_utc':approval,'canonical_publish_utc':'2026-11-06T10:37:42.739Z',
        'latest_browser_send_click_utc':'2026-11-06T11:02:10.319Z','all_channels_within_15_minutes':False,
        'cause':'Quota interrupted the saved KEEP handoff; native upload work and serialized browser distribution then exceeded 15 minutes. Original approval clock retained.'},
    'telegram_readback':'telegram-public-readback.json','schedule_changed':False,'source_trace':'source-claim-trace.json'}
(BASE/'live-acceptance.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(BASE/'production-day-refresh.json').write_text(json.dumps(result['production_day'],indent=2)+'\n',encoding='utf-8')
print(json.dumps({'state':result['state'],'verified_destinations':len(rows),'production_day_distinct':measurement['distinct_canonical_items_published'],
                  'cc122_installed_main_commit':head,'digest_consumer_count':consumer['distinct_articles_published'],'published_feed_rows':len(feed)}))
