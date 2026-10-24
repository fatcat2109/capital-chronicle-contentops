"""Validate a real native writer return, submit once and compile the same operation."""
import argparse
import json
import shutil
from pathlib import Path
from scripts.run_native_desktop_editorial import operation
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn,bind_editorial_media
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.v1_simple_gemini_newsroom_v1 import _validate_worker_text,_validate_article_against_source_pack

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('slugs',nargs='+');parser.add_argument('--submit-only',action='store_true');args=parser.parse_args()
agents={'policy':'/root/v1_prelive_max_policy','gold':'/root/v1_prelive_max_gold',
        'tesla-r2':'/root/v1_max_tesla','southwest-r2':'/root/v1_max_southwest'}
for slug in args.slugs:
    folder=ROOT/slug;binding=json.loads((folder/'binding.json').read_bytes())
    request=json.loads((folder/'desktop_request_write.json').read_bytes())
    worker=json.loads((folder/'native_write_output.json').read_bytes())
    schema=_validate_worker_text(json.dumps(worker))
    if not schema[0]:raise ValueError(str(schema))
    governed=request['governed_input']
    article,validation=_validate_article_against_source_pack(worker,governed['source_pack'],
        selected_candidate=governed['selected_candidate'],article_mode=governed['article_mode'],
        epistemic_state=governed.get('epistemic_state'))
    store=ContentOpsDurableStore(binding['store_path'],auto_migrate=False)
    turn=NativeDesktopTurn(store,run_id=binding['run_id'],output_dir=binding['output_dir'],owner_manual_validation=True)
    if request['request_sha256']!=turn.frozen_request('write')['request_sha256']:raise ValueError('EXACT_REQUEST_CHANGED')
    env={'request_sha256':request['request_sha256'],'output':worker,'invocation_observation':{
        'surface':'CODEX_NATIVE_SUBAGENT','invocation_id':agents[slug],'model':'gpt-6.1-sol',
        'reasoning_effort':'max','speed':'standard','observation_source':'Actual collaboration dispatch/resume and completed worker return with execution note; no model API'}}
    submitted=turn.submit('write',env)
    (folder/'native_write_return_envelope.json').write_text(json.dumps(env,indent=2)+'\n',encoding='utf-8')
    (folder/'parent-write-validation.json').write_text(json.dumps({'schema_valid':True,'source_validation':validation,'native_submit':submitted},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'slug':slug,'submitted':submitted,'supported':validation.get('supported_material_claim_count')}),flush=True)
    if args.submit_only:continue
    result=operation(binding)
    (folder/'native-after-write.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    row=store.get_outbox_message('cc-editorial-final-'+sha256_of(binding['run_id']))
    final=json.loads(row['payload']) if row else {}
    if not final.get('qualified_article_count'):raise ValueError('NATIVE_ARTICLE_NOT_QUALIFIED:'+str(result))
    media=json.loads((folder/'bound-media-assets.json').read_bytes())
    bound=bind_editorial_media(store,run_id=binding['run_id'],article_identity=final['article_identity'],assets=media)
    (folder/'media-binding.json').write_text(json.dumps(bound,indent=2)+'\n',encoding='utf-8')
    final=json.loads(store.get_outbox_message('cc-editorial-final-'+sha256_of(binding['run_id']))['payload'])
    (folder/'native-final-media-result.json').write_text(json.dumps(final,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'slug':slug,'article_identity':final['article_identity'],'media':bound}),flush=True)
