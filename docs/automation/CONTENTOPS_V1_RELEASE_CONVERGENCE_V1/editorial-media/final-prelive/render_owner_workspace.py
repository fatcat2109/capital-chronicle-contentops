"""Render the existing owner's exact selected edition; no synthetic reader records."""
import gzip
import json
import subprocess
from pathlib import Path
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.contentops_editorial_desk_v1 import read_reviews,record_owner_edition
from live_contentops.capital_chronicle_report_editorial_workspace_v1 import report_workspace_projection

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[4]
profile=json.loads((REPO/'config/native_desktop_operator_profile_v1.json').read_bytes())
store=ContentOpsDurableStore(profile['store_path'],auto_migrate=False)
ids=['v1-media-oil-r1','v1-media-ibm-r1','v1-prelive-tesla-r2','v1-media-meta-r1',
     'v1-prelive-southwest-r2','v1-prelive-fed-policy','v1-prelive-gold-oct23']
with store.get_read_only_connection() as conn:
    rows=[dict(r) for r in conn.execute("SELECT * FROM outbox_messages WHERE destination != 'internal:cc-report-editorial-stage' OR message_id LIKE 'native-operation-binding-%' ORDER BY created_at,message_id")]
present={json.loads(r['payload']).get('simple_result',{}).get('run_id') for r in rows if r['destination']=='internal:cc-report-simple-result'}
if not set(ids)<=present:raise ValueError('REQUIRED_REAL_ARTICLES_NOT_READY:'+str(set(ids)-present))
edition=record_owner_edition(store,edition_id='v1-final-prelive-seven',
    title='V1 final pre-live editorial acceptance — seven useful articles',operation_ids=ids,
    held_candidates=[{'operation_id':'goal35-fx','title':'October21 FX candidate','reason':'Preserved prior held source gap; not silently substituted or counted ready.'}],
    opportunity_outcomes=[{'operation_id':op,'outcome':'UPDATE' if op.endswith('-r2') else 'NEW' if op.startswith('v1-prelive') else 'KEEP',
        'source_blocked':False,'reason':'Material source-note editorial revision with unchanged facts' if op.endswith('-r2') else 'Dated policy implementation case' if op.endswith('fed-policy') else 'Genuinely October23 attributed report' if op.endswith('gold-oct23') else 'Valid C9 copy/media/render retained'} for op in ids])
with store.get_read_only_connection() as conn:
    rows=[dict(r) for r in conn.execute("SELECT * FROM outbox_messages WHERE destination != 'internal:cc-report-editorial-stage' OR message_id LIKE 'native-operation-binding-%' ORDER BY created_at,message_id")]
data=report_workspace_projection(rows,review_records=read_reviews(store),dispatches=store.list_platform_dispatches())
# A bounded view of this exact edition. No body/media/preview/status is fabricated.
data['native_edition']=[e for e in data['native_edition'] if e['run_id'] in ids]
if len(data['native_edition'])!=7:raise ValueError('EXACT_SEVEN_OWNER_PROJECTION_REQUIRED')
out=ROOT/'renders';out.mkdir(exist_ok=True)
raw=(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n').encode()
(out/'workspace.json').write_bytes(raw);(out/'workspace.json.gz').write_bytes(gzip.compress(raw,mtime=0))
proc=subprocess.run(['node',str(REPO/'ui/contentops_v5/scripts/render-report-workspace.mjs'),str(out/'workspace.json'),str(out/'index.html')],cwd=REPO,text=True,capture_output=True)
if proc.returncode:raise RuntimeError(proc.stderr)
(out/'index.html.gz').write_bytes(gzip.compress((out/'index.html').read_bytes(),mtime=0))
(out/'render-receipt.json').write_text(json.dumps({'renderer':json.loads(proc.stdout),'edition':edition,
    'source_projection':'report_workspace_projection actual owner outbox/reviews, filtered only to seven existing operation IDs',
    'required_new_changed_inspections':['v1-prelive-tesla-r2','v1-prelive-southwest-r2','v1-prelive-fed-policy','v1-prelive-gold-oct23'],
    'prior_unchanged_views':'C9 oil/IBM/Meta final actual desktop/mobile inspection reused','public_write_performed':False},indent=2)+'\n',encoding='utf-8')
print(proc.stdout)
