from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sqlite3,subprocess,sys
LIVE=Path(r'A:\Capital Chronicle\ContentOps')
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(LIVE))
from live_contentops import published_images_v1 as images
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.plan_status_posts_v1 import read_export
from live_contentops.published_content_v1 import read_records
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
now=datetime.now(timezone.utc)
runtime=Path(r'A:\Capital Chronicle\Runtime\ContentOps')
operation=runtime/'daily_app_outputs/owner-manual/cc124-nfp-arrival-review-20261106-v1'
binding_path=operation/'binding.json'
request_path=operation/'desktop_request_write.json'
binding=json.loads(binding_path.read_bytes()); request=json.loads(request_path.read_bytes())
assert request['request_sha256']==sha256_of({k:v for k,v in request.items() if k!='request_sha256'})
feed_path=runtime/'published_content_v1.jsonl'; feed=read_records(feed_path)
register=images.PublishedImages(runtime/'published_images_v1.jsonl',published_feed=feed_path)
daily=register._daily_pieces(register.records(),now)
con=sqlite3.connect(Path(binding['store_path']).as_uri()+'?mode=ro',uri=True); con.row_factory=sqlite3.Row
leases=[dict(r) for r in con.execute("SELECT lease_id,lease_key,status,expires_at FROM leases WHERE status='ACTIVE' AND expires_at>?",(now.isoformat().replace('+00:00','Z'),))]
work='cc-opportunity-'+sha256_of(binding['run_id'])
dispatches=[dict(r) for identity in (work,binding['run_id']) for r in con.execute('SELECT d.platform,d.status FROM platform_dispatches d JOIN outbox_messages m ON m.message_id=d.message_id WHERE m.work_item_id=? ORDER BY d.dispatch_id',(identity,))]; con.close()
research=RetainedSourceResearch(LIVE/'docs/publisher/CC-124/run-20261106-2050/source')
print('Verifying held Main/BLS records and the installed Main export reader.',flush=True)
export=read_export()
def find(value,key,pointer=''):
    if isinstance(value,dict):
        for name,child in value.items():
            at=pointer+'/'+name
            if name==key: yield {'pointer':at,'value':child}
            else: yield from find(child,key,at)
    elif isinstance(value,list):
        for index,child in enumerate(value): yield from find(child,key,pointer+'/'+str(index))
scenarios=list(find(export,'scenario_analysis'))
(HERE/'main-export-scenarios.json').write_text(json.dumps({'observed_at_utc':now.isoformat(),'consumer':'live_contentops.plan_status_posts_v1.read_export','scenarios':scenarios},indent=2)+'\n',encoding='utf-8')
root=Path(r'A:\Capital Chronicle\ResearchRuns\claude-main-research\daily-research-portfolio-279805139\requests')
paths=sorted(root.glob('*/owner-native.json'),key=lambda p:p.stat().st_mtime,reverse=True)
latest=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'modified_utc':datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat()} for p in paths[:6]]
mainroot=Path(r'A:\Capital Chronicle\Runtime\MainPublicReports-v1')
link=json.loads((mainroot/'latest-manifest.json').read_bytes()); manifestpath=mainroot/link['path']; manifest=json.loads(manifestpath.read_bytes())
source_summary=[{'id':k,'known_at_utc':v['known_at_utc'],'revision_at_utc':v['revision_at_utc'],'sha256':v['document']['canonical_content_sha256'],'public_claim_allowed':v['document']['public_claim_allowed']} for k,v in research.records.items()]
result={'observed_at_utc':now.isoformat(),'item':'CC-124','operating_head':subprocess.check_output(['git','-C',str(LIVE),'rev-parse','HEAD'],text=True).strip(),'production_date':images.day_of(now),'daily_article_limit':images.daily_limit(now),'occupied_article_slots':len(daily),'active_leases':leases,'operation_id':binding['run_id'],'binding_path':str(binding_path),'binding_file_sha256':hashlib.sha256(binding_path.read_bytes()).hexdigest(),'cutoff_utc':binding['cutoff_utc'],'writer_request_sha256':request['request_sha256'],'writer_request_file_sha256':hashlib.sha256(request_path.read_bytes()).hexdigest(),'writer_return_present':(operation/'desktop_response_write.json').exists(),'operation_dispatches':dispatches,'source_adapter':{'root':str(research.root),'revision':research.revision,'gaps':research.gaps,'records':source_summary},'main_export_scenario_count':len(scenarios),'latest_daily_main_reports':latest,'daily_report_count':len(paths),'main_public_manifest':{'path':str(manifestpath),'sha256':hashlib.sha256(manifestpath.read_bytes()).hexdigest(),'emitted_at_utc':manifest['emitted_at_utc'],'entry_count':len(manifest['entries'])},'latest_publications':[{k:r.get(k) for k in ('content_id','title','published_at_utc')} for r in feed[-3:]],'reads_only':True}
(HERE/'source-readiness.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ('production_date','daily_article_limit','occupied_article_slots','active_leases','operation_id','writer_return_present','operation_dispatches','main_export_scenario_count','latest_daily_main_reports','daily_report_count','main_public_manifest')}))
print(json.dumps({'retained_source_gaps':research.gaps,'verified_source_records':len(source_summary)}))
