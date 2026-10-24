"""Bind actual completed Light plans to inspected assets in the sole outbox."""
import argparse
import json
import shutil
from pathlib import Path

from scripts.run_native_desktop_editorial import operation
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn,bind_editorial_media_plan
from live_contentops.rolling_x_grounded_article_media_builder_v1 import build_source_value_comparison_chart

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('slug');parser.add_argument('--reviewed',action='store_true');args=parser.parse_args()
folder=ROOT/args.slug
binding=json.loads((folder/'binding.json').read_bytes());store=ContentOpsDurableStore(binding['store_path'],auto_migrate=False)
out=Path(binding['output_dir']);pending=json.loads((out/'editorial_media_plan_required.json').read_bytes())
if args.slug.endswith('-r2'):
 prior=ROOT.parent/args.slug.removesuffix('-r2')
 old=json.loads((prior/'desktop_request_write.json').read_bytes())['governed_input']['editorial_media_plan']
 plan=old['plan'];assets=old['assets']
else:
 request=json.loads((folder/'desktop_request_media-plan.json').read_bytes())
 output=json.loads((folder/'native_media_plan_output.json').read_bytes())
 turn=NativeDesktopTurn(store,run_id=binding['run_id'],output_dir=out,owner_manual_validation=True)
 env={'request_sha256':request['request_sha256'],'output':output,'invocation_observation':{
   'surface':'CODEX_NATIVE_SUBAGENT','invocation_id':'/root/v1_prelive_light','model':'gpt-6.1-sol',
   'reasoning_effort':'low','speed':'standard','observation_source':'Actual collaboration role request and returned native worker files'}}
 turn.submit('media-plan',env)
 (folder/'native_media_plan_return_envelope.json').write_text(json.dumps(env,indent=2)+'\n',encoding='utf-8')
 story=output['story_plan'];chart_plan=story['chart_plan']
 doc=next(d for d in pending['source_pack'] if d['source_id']==chart_plan['source_id'])
 chart_path=folder/'chart-asset.json'
 if not args.reviewed:
  chart=build_source_value_comparison_chart(doc,rows=chart_plan['rows'],title=chart_plan['title'],unit=chart_plan['unit'],output_dir=folder)
  chart_path.write_text(json.dumps(chart,indent=2)+'\n',encoding='utf-8')
  (folder/'chart-data.json').write_text(json.dumps(chart_plan,indent=2)+'\n',encoding='utf-8')
  print(json.dumps({'chart_for_actual_inspection':chart['path'],'sha256':chart['sha256']}));raise SystemExit(0)
 chart=json.loads(chart_path.read_bytes())
 if not chart.get('visual_review',{}).get('pixels_inspected'):raise ValueError('ACTUAL_CHART_INSPECTION_REQUIRED')
 assets=[json.loads((folder/'release-photo-asset.json').read_bytes()),chart]
 plan={'native_plan_run_id':binding['run_id'],'native_plan_stage':'media-plan',
       'native_plan_request_sha256':request['request_sha256'],'story_plan':story}
receipt=bind_editorial_media_plan(store,run_id=binding['run_id'],output_dir=out,plan=plan,assets=assets)
(folder/'media-plan-binding.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
(folder/'bound-media-assets.json').write_text(json.dumps(assets,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'slug':args.slug,'media_bound':receipt}),flush=True)
result=operation(binding)
(folder/'native-writer-start.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
if (out/'desktop_request_write.json').is_file():shutil.copyfile(out/'desktop_request_write.json',folder/'desktop_request_write.json')
print(json.dumps({'slug':args.slug,'result':result}),flush=True)
