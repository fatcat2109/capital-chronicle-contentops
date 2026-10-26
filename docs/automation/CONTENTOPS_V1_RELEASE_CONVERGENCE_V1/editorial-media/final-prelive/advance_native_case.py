"""Submit actual role returns and advance exact existing bindings once; never wait."""
import argparse
import json
import shutil
from pathlib import Path
from scripts.run_native_desktop_editorial import operation
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn

ROOT=Path(__file__).resolve().parent
AGENT='/root/v1_prelive_light'
parser=argparse.ArgumentParser()
parser.add_argument('slugs',nargs='+')
parser.add_argument('--stage',default='select')
args=parser.parse_args()
for slug in args.slugs:
 folder=ROOT/slug
 binding=json.loads((folder/'binding.json').read_bytes())
 store=ContentOpsDurableStore(binding['store_path'],auto_migrate=False)
 turn=NativeDesktopTurn(store,run_id=binding['run_id'],output_dir=binding['output_dir'],owner_manual_validation=True)
 request=turn.frozen_request(args.stage)
 response_path=folder/('native_'+args.stage.replace('-','_')+'_output.json')
 output=json.loads(response_path.read_bytes())
 envelope={'request_sha256':request['request_sha256'],'output':output,
    'invocation_observation':{'surface':'CODEX_NATIVE_SUBAGENT','invocation_id':AGENT,
      'model':'gpt-6.1-sol','reasoning_effort':'low','speed':'standard',
      'observation_source':'Actual collaboration.spawn_agent and returned native worker files; exact request and execution note retained'}}
 envpath=folder/('native_'+args.stage.replace('-','_')+'_return_envelope.json')
 envpath.write_text(json.dumps(envelope,indent=2)+'\n',encoding='utf-8')
 submitted=turn.submit(args.stage,envelope)
 (folder/('native-'+args.stage+'-submit.json')).write_text(json.dumps(submitted,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'slug':slug,'submitted':submitted}),flush=True)
 result=operation(binding)
 (folder/('native-after-'+args.stage+'.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 out=Path(binding['output_dir'])
 if result.get('stage')=='media-plan' and not slug.endswith('-r2'):
  result=operation(binding,command='media-plan')
  (folder/'native-media-plan-start.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 for name in ('desktop_request_media-plan.json','editorial_media_plan_required.json','desktop_request_write.json'):
  if (out/name).is_file():shutil.copyfile(out/name,folder/name)
 print(json.dumps({'slug':slug,'advanced':result}),flush=True)
