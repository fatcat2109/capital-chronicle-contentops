"""Verify this bounded CC-124 source comparison and retained operation."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json, math
from pathlib import Path
import sqlite3, subprocess, sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
LIVE=Path(r'A:\Capital Chronicle\ContentOps')
sys.path.insert(0,str(LIVE))
from live_contentops.native_publication_promotion_v1 import ReadOnlyStore
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
pre=json.loads((HERE/'preflight.json').read_bytes())
source=json.loads((HERE/'source-readiness.json').read_bytes())
compare=json.loads((HERE/'source-comparison.json').read_bytes())
status=json.loads((HERE/'publication-status.json').read_bytes())
operation=Path(source['binding_path']).parent
binding=json.loads((operation/'binding.json').read_bytes())
now=datetime.now(timezone.utc)
con=sqlite3.connect(Path(binding['store_path']).as_uri()+'?mode=ro',uri=True)
con.row_factory=sqlite3.Row
leases=[dict(r) for r in con.execute("SELECT lease_id,lease_key,status,expires_at FROM leases WHERE status='ACTIVE' AND expires_at>?",(now.isoformat().replace('+00:00','Z'),))]
con.close()
store=ReadOnlyStore(Path(binding['store_path']))
work='cc-opportunity-'+sha256_of(binding['run_id'])
dispatches=[{'platform':r['platform'],'status':r['status']} for identity in (work,binding['run_id']) for r in store.get_dispatches_for_work_item(identity)]
wip={name:{p:sha256(((ROOT if name=='exec' else LIVE)/p).read_bytes()).hexdigest() for p in data['dirty']} for name,data in pre['worktrees'].items()}
checks={
  'binding_bytes_unchanged':sha256((operation/'binding.json').read_bytes()).hexdigest()==source['binding_file_sha256'],
  'writer_request_bytes_unchanged':sha256((operation/'desktop_request_write.json').read_bytes()).hexdigest()==source['writer_request_file_sha256'],
  'writer_return_absent':not (operation/'desktop_response_write.json').exists(),
  'operation_dispatches_unchanged':dispatches==source['operation_dispatches']==[],
  'no_active_newsroom_lease':leases==[],
  'inherited_wip_bytes_unchanged':all(wip[name]==data['dirty'] for name,data in pre['worktrees'].items()),
  'all_retained_main_and_official_sources_verified':not source['source_adapter']['gaps'] and len(source['source_adapter']['records'])==3,
  'main_scenario_gap_observed_by_installed_consumer':compare['export_scenarios']==compare['export_missing_main_alternative_probability']==40,
  'latest_daily_main_report_unchanged':compare['latest_complete_daily_report_unchanged'],
  'no_prior_publication_tool_request_resumed':status['destinations']==[] and status['state']=='INVALIDATED',
}
assert all(checks.values()),checks
launch=pre['launch']; due=datetime.fromisoformat(launch['started_utc'].replace('Z','+00:00'))+timedelta(hours=12)
rounded=datetime.fromtimestamp(math.ceil(due.timestamp()/60)*60,timezone.utc)
verification={'observed_at_utc':now.isoformat(),'status':'PASS','checks':checks,'first_cause':compare['first_cause'],'classification':'SOURCE_BLOCKED','standing_item_end_status':'OPEN','occupied_article_slots':source['occupied_article_slots'],'production_date':source['production_date'],'article_cap':source['daily_article_limit'],'source_adapter_revision':source['source_adapter']['revision'],'configured_model':launch['model'],'configured_effort':launch['reasoning_effort'],'model_provenance':launch['provenance'],'next_due_utc':rounded.isoformat(),'next_due_gmt7':str(rounded.astimezone(timezone(timedelta(hours=7))).day)+' Nov 2026 '+rounded.astimezone(timezone(timedelta(hours=7))).strftime('%H:%M')+' GMT+7','next_due_rule':'Decision 94: twelve hours after actual start, rounded up to next minute.','next_action':compare['next_action'],'next_actor':compare['next_actor'],'new_publications':0,'new_editorial_model_calls':0,'new_source_requests':0,'new_media':0,'new_destination_drafts':0,'pytest_processes_started':0,'runtime_code_changed':False,'schedules_changed':False,'chat_messages_sent':False,'desktop_control_used':False,'inherited_wip_sha256':wip}
(HERE/'verification.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','checks':len(checks),'first_cause':verification['first_cause'],'next_due_gmt7':verification['next_due_gmt7']}))
