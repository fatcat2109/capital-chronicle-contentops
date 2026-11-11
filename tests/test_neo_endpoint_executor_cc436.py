"""CC-436: copied-store consumer -> local MCP -> publish/readback, without a model."""
from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from threading import Thread

from PIL import Image, ImageDraw
import pytest
import requests

from live_contentops import neo_endpoint_executor_v1 as neo
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_neo_executor_v1 import bind_native_neo_coordinator
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator


@contextmanager
def endpoint(*, fault=None):
    state = {"calls":[],"posts":{},"composer":{},"fault":fault,"uploads":[]}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_GET(self):
            path=state['uploads'][0] if state['uploads'] else None
            if not path: self.send_response(404);self.end_headers();return
            data=Path(path).read_bytes()
            self.send_response(200);self.send_header('Content-Type','image/png');self.send_header('Content-Length',str(len(data)))
            self.end_headers();self.wfile.write(data)
        def do_POST(self):
            request=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            method=request['method']; params=request.get('params',{})
            if method == 'initialize': result={"protocolVersion":"2025-03-26","serverInfo":{"name":"fixture-neo"}}
            elif method == 'notifications/initialized':
                self.send_response(202); self.end_headers(); return
            else:
                name=params['name']; args=params['arguments']; state['calls'].append((name,args))
                value=None
                if name=='tabs': text='opened page '+('1' if 'x.com' in args.get('url','') else '2') if args['action']=='new' else ''
                elif name=='tab_groups': text='[task] "codex/cc436-automatic-posts" (pink) pages: '
                elif name=='act':
                    if args['kind']=='dialog_accept':state['beforeunload_dismissed']=True
                    if args['kind']=='fill': state['composer'].setdefault(args['page'],[]).append(args['value'])
                    text='ok'
                elif name=='navigate' and fault=='beforeunload' and not state.get('beforeunload_dismissed'):
                    text='[page 1 dialog open] beforeunload: "" - use act kind="dialog_accept"'
                elif name=='upload': state['uploads'].extend(args['files']); text='ok'
                elif name=='run':
                    code=args['code']; page=1 if 'browser.page(1)' in code else 2; dest='x' if page==1 else 'substack_notes'
                    if not code.startswith('const input='):
                        value={"refs":[{"role":"button","name":n,"ref":"e"+str(i)} for i,n in enumerate(
                            ['New post','Comment','Post','Add post','Choose Files','CC436 image upload'])]+
                            [{"role":"textbox","name":"Post text" if page==1 else "What's on your mind?","ref":"edit"}],
                            "url":"https://x.com/Capitalnicle" if page==1 else "https://substack.com/@capitalchronicle","text":"fixture"}
                    else:
                        args_in=json.loads(code.split('const input=',1)[1].split(';\n',1)[0]); phase=args_in['phase']
                        if phase=='identity': value={"authenticated":fault!='account',"observed_identity":args_in['expected_identity'] if fault!='account' else None,
                            "observed_at_utc":datetime.now(timezone.utc).isoformat()}
                        elif phase=='publish':
                            actual=state['composer'].get(page,[])
                            if actual!=args_in['posts'] or fault=='composer':
                                value={"status":"FAILED_BEFORE_WRITE","definite_no_write":True,"stage":"BEFORE_PUBLISH_CLICK",
                                    "reason_code":"NEO_COMPOSER_PAYLOAD_MISMATCH"}
                            else:
                                number='123' if page==1 else 'c-456'
                                url='https://x.com/Capitalnicle/status/123' if page==1 else 'https://substack.com/@capitalchronicle/note/c-456'
                                state['posts'][dest]={"public_object_id":number,"public_object_url":url,
                                    "observed_text":'\n\n'.join(actual),"links":[],"public_image_urls":
                                    (['https://pbs.twimg.com/media/card.png'] if dest=='x' else
                                     ['https://substack-post-media.s3.amazonaws.com/public/images/card.png']) if state['uploads'] else []}
                                if fault=='lost_return':
                                    self.send_response(503);self.end_headers();return
                                value={"status":"CLICKED","pre_click_posts":actual,"stage":"PUBLISH_CLICK_ATTEMPTED",
                                    "dispatched_at_utc":datetime.now(timezone.utc).isoformat()}
                        elif phase=='readback':
                            value={"tweets":[state['posts']['x']] if 'x' in state['posts'] else [],
                                "notes":[state['posts']['substack_notes']] if 'substack_notes' in state['posts'] else []}
                        else: value={"ready":True}
                    result={"content":[{"type":"text","text":"ok\nreturn: "+json.dumps({"ok":True,"logs":[],"value":value})}]}
                else: text='ok'
                if name!='run': result={"content":[{"type":"text","text":text}],
                    **({'isError':True} if 'beforeunload:' in text else {})}
            data=('data: \nid: 0\n\ndata: '+json.dumps({"jsonrpc":"2.0","id":request.get('id'),"result":result})+'\n\n').encode()
            self.send_response(200);self.send_header('Content-Type','text/event-stream');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    try: yield f'http://127.0.0.1:{server.server_port}/mcp',state
    finally: server.shutdown();server.server_close();thread.join()


def copied_store(tmp_path):
    seed=ContentOpsDurableStore(tmp_path/'seed.sqlite3')
    control=seed.get_operating_control()
    seed.update_operating_control(operating_mode='AUTONOMOUS_DEFAULT',expected_state_version=control['state_version'],control_source='CONTROLLED_TEST')
    path=tmp_path/'copied.sqlite3'
    with sqlite3.connect(seed.db_path) as source,sqlite3.connect(path) as target: source.backup(target)
    return ContentOpsDurableStore(path)


def message(store,destination):
    work='card-'+destination
    store.create_work_item(story_id=work,work_item_id=work,title='Bound source copy',target_surface='MULTI_PLATFORM')
    value={"work_item_id":work,"plan_hash":"plan","package_identity":"pkg",
        "canonical_url":"https://capitalchronicle.substack.com/p/original-call",
        "payload":"The original conditional call remains in force.",
        "native_payload":{"text":"The original conditional call remains in force."},
        "destination_plan":{"payload_hash":"hash","surface":"X_POST" if destination=='x' else 'SUBSTACK_NOTE'}}
    ids=Coordinator._ids(work,'plan',destination)
    store.register_outbox_message(message_id=ids['message_id'],work_item_id=work,destination=destination,payload=json.dumps(value),status='READY')
    return ids,value


def bound(store,tmp_path,work,url):
    return bind_native_neo_coordinator(store,operation_id=work,output_dir=tmp_path/work,
        native_invocation_id='fixture-parent',allow_publish=True,automatic=True,endpoint_client=neo.NeoMcpClient(url))


@pytest.fixture(autouse=True)
def isolated_control(monkeypatch):
    monkeypatch.setattr('live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled',lambda:None)


@pytest.mark.parametrize('destination',['x','substack_notes'])
def test_copied_store_posts_and_reconciles_through_endpoint_once(tmp_path,destination):
    store=copied_store(tmp_path);ids,value=message(store,destination)
    with endpoint() as (url,state):
        coordinator,executor=bound(store,tmp_path,value['work_item_id'],url)
        result=coordinator._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
        assert result['status']=='DISPATCH_CONFIRMED',json.dumps(result,indent=2)
        assert result['reconciliation_status']=='RECONCILED_CONFIRMED',result
        again=coordinator._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
        assert again['publish_called'] is False
        clicks=[args for name,args in state['calls'] if name=='run' and '"phase": "publish"' in args['code']]
        assert len(clicks)==1
        assert destination in state['posts']
        assert executor.pending()==[]
        response=next(json.loads(row['payload']) for row in store.list_outbox_messages(destination='internal:native-neo-tool')
            if 'native_tool_observation' in json.loads(row['payload']).get('result',{}))
        assert response['result']['native_tool_observation']['surface']=='NEO_ENDPOINT_EXECUTOR'


@pytest.mark.parametrize('fault',['account','composer'])
def test_wrong_account_or_changed_composer_makes_no_public_post(tmp_path,fault):
    store=copied_store(tmp_path);ids,value=message(store,'x')
    with endpoint(fault=fault) as (url,state):
        c,_=bound(store,tmp_path,value['work_item_id'],url)
        result=c._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
        assert result['status']=='DEFINITE_NO_WRITE',result
        assert not state['posts']


def test_lost_publish_return_recovers_by_readback_without_reposting(tmp_path):
    store=copied_store(tmp_path);ids,value=message(store,'x')
    with endpoint(fault='lost_return') as (url,state):
        c,e=bound(store,tmp_path,value['work_item_id'],url)
        first=c._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
        assert state['posts'].keys()=={'x'}
        # The lost click observation is never repeated; the coordinator's first
        # recovery read may already have confirmed it in this same invocation.
        c2,e2=bound(store,tmp_path,value['work_item_id'],url)
        recovered=c2.readback_existing_dispatch(ids['dispatch_id'])
        assert store.get_platform_dispatch(ids['dispatch_id'])['status']=='DISPATCH_CONFIRMED',recovered
        clicks=[a for n,a in state['calls'] if n=='run' and '"phase": "publish"' in a['code']]
        assert len(clicks)==1


def test_copied_store_runs_in_plain_python_child_with_no_codex_dispatch(tmp_path):
    store=copied_store(tmp_path)
    for destination in ('x','substack_notes'):message(store,destination)
    card=tmp_path/'media'/'card.png';card.parent.mkdir()
    Image.new('RGB',(256,256),'navy').save(card)
    for destination in ('x','substack_notes'):
        row=store.list_outbox_messages(destination=destination)[0]
        value=json.loads(row['payload'])
        value['media_assets']=[{'asset_id':'card','path':str(card),'sha256':sha256(card.read_bytes()).hexdigest()}]
        store.finalize_outbox_payload_before_dispatch(message_id=row['message_id'],payload=json.dumps(value),status='READY')
    with endpoint() as (url,state):
        code='''
import json,sys
import requests
from pathlib import Path
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_neo_executor_v1 import bind_native_neo_coordinator
from live_contentops.neo_endpoint_executor_v1 import NeoMcpClient
from live_contentops import llm_operator_control_v1
from live_contentops import neo_destination_handoff_v1
llm_operator_control_v1.assert_llm_operator_execution_enabled=lambda:None
neo_destination_handoff_v1.SUSPENDED_ROUTES_FILE=Path(sys.argv[1]).parent/'fixture-suspended-routes-absent.json'
s=ContentOpsDurableStore(Path(sys.argv[1]),auto_migrate=False)
class ImageHttp:
 def get(self,url,**kwargs):
  assert url.startswith(('https://pbs.twimg.com/media/','https://substack-post-media.s3.amazonaws.com/'))
  return requests.get(sys.argv[2].replace('/mcp','/card.png'),**kwargs)
for destination in ('x','substack_notes'):
 row=s.list_outbox_messages(destination=destination)[0]
 value=json.loads(row['payload'])
 client=NeoMcpClient(sys.argv[2]);client.image_http=ImageHttp()
 c,e=bind_native_neo_coordinator(s,operation_id=value['work_item_id'],output_dir=Path(sys.argv[1]).parent/destination,
  native_invocation_id='plain-python',allow_publish=True,automatic=True,endpoint_client=client)
 result=c._dispatch_message(row,canonical_url=value['canonical_url'])
 assert result['status']=='DISPATCH_CONFIRMED',result
 assert result['reconciliation_status']=='RECONCILED_CONFIRMED',result
print('X_AND_NOTE_CONFIRMED_WITHOUT_MODEL_OR_CODEX_CHILD')
'''
        result=subprocess.run([sys.executable,'-c',code,str(store.db_path),url],capture_output=True,text=True,timeout=35)
        assert result.returncode==0,result.stderr+result.stdout
        assert 'X_AND_NOTE_CONFIRMED_WITHOUT_MODEL_OR_CODEX_CHILD' in result.stdout
        assert state['posts'].keys()=={'x','substack_notes'}
        assert state['uploads']==[str(card),str(card)]


def test_local_endpoint_only():
    with pytest.raises(ValueError,match='NEO_LOCAL_ENDPOINT_REQUIRED'): neo.NeoMcpClient('https://example.com/mcp')


@pytest.mark.parametrize('font_size',[12,18,34])
def test_public_pixel_comparison_accepts_compression_and_rejects_changed_level(tmp_path,font_size):
    image=Image.new('RGB',(512,320),'white'); draw=ImageDraw.Draw(image)
    draw.rectangle((10,10,490,300),outline='black',width=3)
    draw.text((30,80),'CALL LEVEL 1234',fill='black',font_size=font_size)
    path=tmp_path/'card.png';image.save(path)
    source_hash=sha256(path.read_bytes()).hexdigest()
    request={'destination':'x','content_binding':{'media_manifest':[{'path':str(path),'sha256':source_hash}]}}
    observed={'public_object_url':'https://x.com/Capitalnicle/status/123','public_image_urls':['https://pbs.twimg.com/media/card.jpg']}
    class Http:
        def __init__(self,img): self.img=img
        def get(self,*args,**kwargs):
            buffer=BytesIO();self.img.save(buffer,format='JPEG',quality=95)
            class Response:
                status_code=200
                def raise_for_status(self):pass
                def iter_content(self,size):yield buffer.getvalue()
            return Response()
    good=neo.compare_public_images(request,observed,http=Http(image))
    assert good['media_comparisons'][0]['source_pixels_match'] is True
    altered=image.copy();d=ImageDraw.Draw(altered);d.rectangle((30,80,330,120),fill='white');d.text((30,80),'CALL LEVEL 1284',fill='black',font_size=font_size)
    bad=neo.compare_public_images(request,observed,http=Http(altered))
    assert bad['media_comparisons'][0]['source_pixels_match'] is False


def test_status_minute_consumer_selects_automatic_executor(tmp_path,monkeypatch):
    from live_contentops import plan_status_posts_v1 as posts,plan_call_cards_v1 as cards,plan_analysis_pages_v1 as pages
    # The consumer passes this factory to the actual card owner. Exercise that
    # factory, rather than duplicating the production binding in the assertion.
    store=copied_store(tmp_path);seen=[]
    def publish_cards(store,**kw):
        coordinator=kw['coordinator_for']('fresh-card',tmp_path/'fresh-card')
        executor=coordinator.transport_runtime._neo_transport.native_executor
        seen.append(executor)
        return {'posts':[]}
    monkeypatch.setattr(cards,'publish_ready',publish_cards)
    monkeypatch.setattr(pages,'distribute_links',lambda store,**kw:{'links':[]})
    posts.publish_ready(store,root=tmp_path,now=datetime.now(timezone.utc),automatic_neo=True)
    assert isinstance(seen[0],neo.EndpointNeoExecutor)
    assert seen[0].identity_at_action is True


def test_transient_endpoint_outage_keeps_exact_unclaimed_request_pending(tmp_path,monkeypatch):
    from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired
    store=copied_store(tmp_path);ids,value=message(store,'x')
    with endpoint() as (url,state):
        c,e=bound(store,tmp_path,value['work_item_id'],url)
        original=e.client.initialize
        monkeypatch.setattr(e.client,'initialize',lambda: (_ for _ in ()).throw(neo.NeoEndpointError('OFFLINE')))
        first=c._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
        assert first['status']=='NATIVE_NEO_TOOL_PENDING',first
        request=first['native_tool_request']['request']
        assert e._get(request['request_sha256'],'started') is None
        monkeypatch.setattr(e.client,'initialize',original)
        second=c._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
        assert second['status']=='DISPATCH_CONFIRMED',second
        assert e._get(request['request_sha256'],'response') is not None


def test_default_manual_binding_never_calls_browser_endpoint(tmp_path,monkeypatch):
    from live_contentops.native_neo_executor_v1 import NativeNeoExecutor
    store=copied_store(tmp_path);ids,value=message(store,'x')
    monkeypatch.setattr(neo.NeoMcpClient,'initialize',lambda: pytest.fail('manual binding touched real browser'))
    c,e=bind_native_neo_coordinator(store,operation_id=value['work_item_id'],output_dir=tmp_path/'manual',
        native_invocation_id='manual',allow_publish=True)
    assert type(e) is NativeNeoExecutor
    result=c._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
    assert result['status']=='NATIVE_NEO_TOOL_PENDING'


def test_shortened_link_readback_requires_its_exact_bound_destination():
    request={'destination':'x','canonical_url':'https://capitalchronicle.substack.com/p/right-plan'}
    text='Read https://capitalchronicle.substack.com/p/right-plan'
    observed={'observed_text':'Read capitalchronicle.substack.com/p/right-plan',
        'public_object_url':'https://x.com/Capitalnicle/status/123','links':[{
            'text':'capitalchronicle.substack.com/p/right-plan','url':'https://t.co/a',
            'expanded_url':'https://capitalchronicle.substack.com/p/right-plan'}]}
    assert neo.NeoBrowserDriver._matches(request,text,observed)
    observed['links'][0]['expanded_url']='https://capitalchronicle.substack.com/p/wrong-plan'
    assert not neo.NeoBrowserDriver._matches(request,text,observed)


def test_cli_publish_passes_automatic_transport_to_the_real_consumer(tmp_path,monkeypatch,capsys):
    from scripts import plan_status_posts as cli
    from live_contentops import plan_status_posts_v1 as posts,plan_analysis_pages_v1 as pages
    from live_contentops import pinned_result_scorecard_v1,event_timestamp_v1,event_pack_v1
    store=copied_store(tmp_path);seen=[]
    monkeypatch.setattr(cli,'queue_posts',lambda *a,**kw:{'status':'OK','latest_states':{},'active_recoveries':{}})
    monkeypatch.setattr(pinned_result_scorecard_v1,'refresh_scorecard',lambda *a,**kw:{'status':'CONFIRMED'})
    monkeypatch.setattr(pages,'resume_discord_links',lambda *a,**kw:[])
    monkeypatch.setattr(event_timestamp_v1,'maintain_timestamps',lambda:{'status':'OK'})
    monkeypatch.setattr(event_pack_v1,'run_due_packs',lambda *a,**kw:{'status':'OK'})
    monkeypatch.setattr(posts,'publish_ready',lambda s,**kw:seen.append((s.db_path,kw)) or {'posts':[]})
    assert cli.main(['--store',str(store.db_path),'--publish'])==0
    assert seen[0][0]==store.db_path
    assert seen[0][1]['automatic_neo'] is True


def test_larger_neo_dom_result_reads_only_documented_local_output(tmp_path,monkeypatch):
    folder=tmp_path/'.browseros'/'tool-output';folder.mkdir(parents=True)
    path=folder/'evaluate_in_page-test.txt'
    data={'tweets':[{'observed_text':'Bound public copy'}],'notes':[]}
    path.write_text('[UNTRUSTED_PAGE_CONTENT nonce=test]\n'+json.dumps(data)+'\n[END_UNTRUSTED_PAGE_CONTENT nonce=test]',encoding='utf-8')
    c=neo.NeoMcpClient()
    monkeypatch.setattr(c,'call',lambda *a,**kw:{'structuredContent':{'ok':True,'value':{'neo_output_file':str(path)}}})
    assert c.run(1,'readback')==data
    monkeypatch.setattr(c,'call',lambda *a,**kw:{'structuredContent':{'ok':True,'value':{'neo_output_file':str(tmp_path/'outside.txt')}}})
    with pytest.raises(neo.NeoEndpointError,match='NEO_DOM_OUTPUT_PATH_INVALID'):c.run(1,'readback')


def test_large_preclick_posts_load_the_actual_bounded_observation(tmp_path,monkeypatch):
    folder=tmp_path/'.browseros'/'tool-output';folder.mkdir(parents=True)
    path=folder/'preclick.txt';actual=['Bound public copy. '*500]
    path.write_text(json.dumps(actual),encoding='utf-8')
    c=neo.NeoMcpClient()
    monkeypatch.setattr(c,'call',lambda *a,**kw:{'structuredContent':{'ok':True,'value':
        {'status':'CLICKED','pre_click_posts':{'neo_output_file':str(path)}}}})
    assert c.run(1,'publish')['pre_click_posts']==actual
    path=tmp_path/'outside.txt'
    with pytest.raises(neo.NeoEndpointError,match='NEO_DOM_OUTPUT_PATH_INVALID'):c.run(1,'publish')


def test_repaired_transport_supersedes_only_a_proven_preclick_refusal(tmp_path,monkeypatch):
    store=copied_store(tmp_path);ids,value=message(store,'substack_notes')
    with endpoint(fault='composer') as (url,state):
        c,e=bound(store,tmp_path,value['work_item_id'],url)
        e.executor_revision='old-source'
        failed=c._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
        assert failed['status']=='DEFINITE_NO_WRITE',failed
        packets=[json.loads(r['payload']) for r in store.list_outbox_messages(destination='internal:native-neo-tool')]
        request=next(p['request'] for p in packets if p.get('request',{}).get('action')=='PUBLISH')
        original=e._get(request['request_sha256'],'response')
        base={k:v for k,v in request.items() if k!='request_sha256'}
        assert e.fresh_publish_request(base) is None  # unchanged code never repeats its failed attempt
        e.executor_revision='repaired-source'
        refreshed=e.fresh_publish_request(base)
        assert refreshed['supersedes_prewrite_no_write_sha256']
        assert all(refreshed[k]==v for k,v in base.items())
        assert e._get(request['request_sha256'],'response')==original
        ambiguous={**original['result'],'status':'UNKNOWN_WRITE','definite_no_write':False,
                   'stage':'PUBLISH_CLICK_ATTEMPTED'}
        monkeypatch.setattr(e,'_get',lambda *a:{'result':ambiguous})
        assert e.fresh_publish_request(base) is None


def test_reopened_note_runs_the_repaired_transport_through_its_original_coordinator(tmp_path,monkeypatch):
    from live_contentops import neo_destination_handoff_v1 as handoff
    control=tmp_path/'suspended_routes.json';control.write_text('{}',encoding='utf-8')
    monkeypatch.setattr(handoff,'SUSPENDED_ROUTES_FILE',control)
    store=copied_store(tmp_path);ids,value=message(store,'substack_notes')
    with endpoint(fault='composer') as (url,state):
        c,e=bound(store,tmp_path,value['work_item_id'],url);e.executor_revision='old-source'
        failed=c._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
        assert failed['status']=='DEFINITE_NO_WRITE',failed
    control.write_text(json.dumps({'substack_notes':'SUBSTACK_ACCOUNT_SUSPENDED'}),encoding='utf-8')
    c._settle_barred_browser_no_write(store.get_outbox_message(ids['message_id']))
    control.write_text('{}',encoding='utf-8')
    with endpoint() as (url,state):
        c,e=bound(store,tmp_path,value['work_item_id'],url)
        original=c.transport_runtime.publish
        def publish(**kwargs):
            try:
                return original(**kwargs)
            except ValueError as exc:
                pytest.fail('REPAIRED_NOTE_LOCAL_ERROR: '+str(exc))
        monkeypatch.setattr(c.transport_runtime,'publish',publish)
        result=c._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
        assert result['status']=='DISPATCH_CONFIRMED',json.dumps(result)
        assert result['public_object_url']=='https://substack.com/@capitalchronicle/note/c-456'


def test_endpoint_names_a_preclaim_validation_failure_without_a_browser_action(tmp_path,monkeypatch):
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
    store=copied_store(tmp_path);ids,value=message(store,'substack_notes')
    with endpoint() as (url,state):
        c,e=bound(store,tmp_path,value['work_item_id'],url)
        def refused(request_hash):raise ValueError('NATIVE_NEO_EXACT_COORDINATOR_PENDING_DISPATCH_REQUIRED')
        monkeypatch.setattr(e,'begin',refused)
        result=c._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
        assert result['status']=='DEFINITE_NO_WRITE',json.dumps(result)
        assert result['safe_error_classification']=='NATIVE_NEO_EXACT_COORDINATOR_PENDING_DISPATCH_REQUIRED'
        assert not any(name=='run' for name,args in state['calls'])


def test_api_complete_parent_drains_its_exact_stored_request_without_rebuilding(tmp_path):
    store=copied_store(tmp_path);ids,value=message(store,'x')
    c,e=bind_native_neo_coordinator(store,operation_id=value['work_item_id'],output_dir=tmp_path/'issued',
        native_invocation_id='earlier-agent',allow_publish=True)
    first=c._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
    packet=first['native_tool_request'];request_hash=packet['request']['request_sha256']
    original=e._get(request_hash,'request')
    store.register_outbox_message(message_id=value['work_item_id'],work_item_id=value['work_item_id'],
        destination='internal:plan-status-post',payload=json.dumps({'kind':'result','at_utc':datetime.now(timezone.utc).isoformat()}),
        status='PUBLISHED')
    with endpoint() as (url,state):
        result=neo.resume_stored_requests(store,client=neo.NeoMcpClient(url),output_root=tmp_path/'resumed')
        assert result['requests'][0]['status']=='RECONCILED_CONFIRMED',result
        assert result['requests'][0]['request_sha256']==request_hash
        assert e._get(request_hash,'request')==original
        assert store.get_outbox_message(value['work_item_id'])['status']=='PUBLISHED'
        count=len(state['calls'])
        again=neo.resume_stored_requests(store,client=neo.NeoMcpClient(url),output_root=tmp_path/'resumed')
        assert again['requests']==[]
        assert len(state['calls'])==count
        assert state['posts'].keys()=={'x'}


def test_expired_claimed_step_still_reads_back_without_another_click(tmp_path):
    store=copied_store(tmp_path);ids,value=message(store,'x')
    c,e=bind_native_neo_coordinator(store,operation_id=value['work_item_id'],output_dir=tmp_path/'issued',
        native_invocation_id='lost-agent',allow_publish=True)
    first=c._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
    request_hash=first['native_tool_request']['request']['request_sha256']
    e.begin(request_hash)
    store.register_outbox_message(message_id=value['work_item_id'],work_item_id=value['work_item_id'],
        destination='internal:plan-status-post',payload=json.dumps({'kind':'setup','at_utc':'2026-01-01T00:00:00Z'}),status='PUBLISHED')
    with endpoint() as (url,state):
        result=neo.resume_stored_requests(store,client=neo.NeoMcpClient(url),output_root=tmp_path/'resumed')
        assert result['requests']
        assert result['requests'][0]['status']!='PLAN_STATUS_X_STALE_NOT_POSTED'
        assert not state['posts']
        assert any(name=='run' and '"phase": "readback"' in args['code'] for name,args in state['calls'])


@pytest.mark.parametrize('historical_without_cause',[False,True])
def test_live_route_suspension_prevents_endpoint_calls_and_leaves_x_available(tmp_path,monkeypatch,historical_without_cause):
    from live_contentops import neo_destination_handoff_v1 as handoff
    control=tmp_path/'suspended_routes.json'
    control.write_text(json.dumps({'substack_notes':'SUBSTACK_ACCOUNT_SUSPENDED'}),encoding='utf-8')
    monkeypatch.setattr(handoff,'SUSPENDED_ROUTES_FILE',control)
    store=copied_store(tmp_path);ids,value=message(store,'substack_notes')
    with endpoint() as (url,state):
        c,_=bound(store,tmp_path,value['work_item_id'],url)
        if historical_without_cause:
            store.register_platform_dispatch(dispatch_id=ids['dispatch_id'],message_id=ids['message_id'],
                platform='substack_notes',status='DEFINITE_NO_WRITE')
            result=c._settle_barred_browser_no_write(store.get_outbox_message(ids['message_id']))
        else:
            result=c._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
        assert result['status']=='DEFINITE_NO_WRITE',result
        assert result['reason_code']=='SUBSTACK_ACCOUNT_SUSPENDED'
        assert not state['calls']
        assert handoff._prohibited_write('x') is None
        control.write_text('{}', encoding='utf-8')
        result=c._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
        assert result['status']=='DISPATCH_CONFIRMED',json.dumps({
            'outcome':result,'reconciliation':[r['status'] for r in store.get_reconciliations_for_work_item(value['work_item_id'])]},indent=2)
        assert result['public_object_url']=='https://substack.com/@capitalchronicle/note/c-456'
        c._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
        clicks=[args for name,args in state['calls'] if name=='run' and '"phase": "publish"' in args.get('code','')]
        assert len(clicks)==1


def test_reopening_suspended_route_never_retries_an_uncertain_note(tmp_path,monkeypatch):
    from live_contentops import neo_destination_handoff_v1 as handoff
    control=tmp_path/'suspended_routes.json'
    control.write_text('{}',encoding='utf-8')
    monkeypatch.setattr(handoff,'SUSPENDED_ROUTES_FILE',control)
    store=copied_store(tmp_path);ids,value=message(store,'substack_notes')
    store.register_platform_dispatch(dispatch_id=ids['dispatch_id'],message_id=ids['message_id'],
        platform='substack_notes',status='UNKNOWN_WRITE')
    store.set_outbox_status(ids['message_id'],'UNKNOWN_WRITE')
    with endpoint() as (url,state):
        c,_=bound(store,tmp_path,value['work_item_id'],url)
        result=c._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
        assert result['status']=='UNKNOWN_WRITE',result
        assert not any(name=='run' and '"phase": "publish"' in args.get('code','') for name,args in state['calls'])


def test_existing_minute_record_keeps_exact_safe_drain_result(tmp_path):
    from live_contentops import plan_status_posts_v1 as posts
    request={'operation_id':'same-post','destination':'x','request_sha256':'a'*64,
        'status':'RECONCILED_CONFIRMED','native_payload':'never in the run record'}
    path=posts.record_run({'status':'OK','publication':{'status':'OK',
        'neo_stored_requests':{'status':'OK','requests':[request]}}},tmp_path)
    row=json.loads(path.read_text(encoding='utf-8'))
    assert row['neo_stored_requests']['requests']==[{k:v for k,v in request.items() if k!='native_payload'}]
    assert 'never in the run record' not in path.read_text(encoding='utf-8')


def test_own_task_beforeunload_finishes_navigation_without_duplicate_publish(tmp_path):
    store=copied_store(tmp_path);ids,value=message(store,'x')
    with endpoint(fault='beforeunload') as (url,state):
        c,_=bound(store,tmp_path,value['work_item_id'],url)
        result=c._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
        assert result['status']=='DISPATCH_CONFIRMED',result
        assert state['beforeunload_dismissed'] is True
        clicks=[a for n,a in state['calls'] if n=='run' and '"phase": "publish"' in a['code']]
        assert len(clicks)==1


def test_sse_transport_stops_at_matching_reply_without_waiting_for_stream_close():
    class Response:
        headers={'Content-Type':'text/event-stream'}
        closed=False
        def raise_for_status(self):pass
        def close(self):self.closed=True
        def iter_lines(self,**kw):
            yield 'data: '
            yield 'data: '+json.dumps({'jsonrpc':'2.0','id':1,'result':{'accepted':True}})
            pytest.fail('read beyond the matching SSE reply')
    response=Response()
    class Session:
        headers={}
        def post(self,*args,**kw):
            assert kw['stream'] is True
            return response
    client=neo.NeoMcpClient(session=Session())
    assert client.rpc('fixture')=={'accepted':True}
    assert response.closed is True


def test_covered_thread_editor_uses_neo_focus_and_types_only_bound_copy():
    class Client:
        def __init__(self):self.actions=[];self.actual=[];self.last_error={}
        def call(self,*args,**kwargs):return {}
        def wait(self,*args):pass
        def snapshot(self,page):return {'refs':[{'role':'textbox','name':'Post text','ref':'editor'}]}
        def run(self,page,phase):
            assert phase=='composer'
            return self.actual
        def act(self,page,kind,**values):
            self.actions.append((kind,values))
            if kind=='fill':
                self.last_error={'classification':'CONTROL_COVERED'}
                raise neo.NeoEndpointError('NEO_CONTROL_COVERED_ACT')
            if kind=='type':self.actual=[values['text']]
    client=Client()
    request={'destination':'x','native_payload':{'text':'The bound original call.'},'content_binding':{}}
    assert neo.NeoBrowserDriver(client).prepare(request,1)==['The bound original call.']
    assert client.actual==['The bound original call.']
    assert [kind for kind,_ in client.actions]==['fill','focus','press','type']
    assert all(kind!='click' for kind,_ in client.actions)


def test_notes_reply_uses_the_observed_editor_without_posting():
    class Client:
        def __init__(self): self.actions=[]
        def call(self,name,args):
            assert name=='navigate'
            assert args['url']=='https://substack.com/@capitalchronicle/note/c-123'
        def wait(self,*args): pass
        def snapshot(self,page):
            return {'refs':[{'role':'button','name':'Comment','ref':'comment'},
                {'role':'textbox','name':'Leave a reply...','ref':'reply'}]}
        def act(self,page,kind,**values): self.actions.append((kind,values))
    client=Client()
    request={'destination':'substack_notes','native_payload':{'text':'The original conditional call.'},
        'reply_parent':{'public_object_url':'https://substack.com/@capitalchronicle/note/c-123'}}
    assert neo.NeoBrowserDriver(client).prepare(request,1)==['The original conditional call.']
    assert client.actions==[('click',{'ref':'comment'}),('fill',{'ref':'reply','value':'The original conditional call.'})]


@pytest.mark.parametrize('destination,button',[('substack_notes','Post'),('x','Reply')])
def test_reply_validates_the_platforms_actual_submit_button(destination,button):
    # Run the production JS with the SDK/DOM observations from the live Notes
    # reply. Validation must find Post on Notes and Reply on X, without a click.
    code='''
const fs=require('node:fs');
const input={phase:'validate',destination:process.argv[1],reply_parent:{public_object_id:'parent'},posts:['Bound copy']};
const page={snapshot:async()=>({refs:[{role:'button',name:process.argv[2],ref:'submit'}]}),
 evaluateInPage:async()=>({value:{count:1,matches:true}}),click:async()=>{throw Error('unexpected publish')}};
const run=new Function('input','page','return (async()=>{'+fs.readFileSync(process.argv[3],'utf8')+'})()');
run(input,page).then(x=>process.stdout.write(JSON.stringify(x))).catch(e=>{console.error(e);process.exit(1)});
'''
    result=subprocess.run(['node','-e',code,destination,button,str(neo.STEPS)],capture_output=True,text=True,timeout=10,check=True)
    assert json.loads(result.stdout)=={'status':'PREPARED','post_count':1}


@pytest.mark.parametrize('destination',['x','substack_notes'])
@pytest.mark.parametrize('status',['DEFINITE_NO_WRITE','UNKNOWN_WRITE'])
def test_composer_preparation_does_not_mute_unrelated_posts_when_definitely_unsent(tmp_path,destination,status):
    store=copied_store(tmp_path);_,value=message(store,destination)
    c=Coordinator(store=store,transport_runtime=None)
    detail={'status':status,'safe_error_classification':'NEO_COMPOSER_PREPARATION_FAILED'}
    c._record_destination_day_failure(value,destination,detail)
    assert (c._destination_day_failure(destination) is None) is (status=='DEFINITE_NO_WRITE')
    if status=='UNKNOWN_WRITE': return
    # Preserve and interpret incidents made by the previously installed code.
    incident_id,_=c._destination_failure_key(destination)
    original=json.dumps(detail,sort_keys=True)
    store.register_incident(incident_id=incident_id,work_item_id=value['work_item_id'],
        severity='DISPATCH_FAILURE',description=original)
    with endpoint() as (url,state):
        c,e=bound(store,tmp_path,value['work_item_id'],url)
        result=c._dispatch_message(store.list_outbox_messages(destination=destination)[0],canonical_url=value['canonical_url'])
        assert result['status']=='DISPATCH_CONFIRMED',result
        assert destination in state['posts']
    with store.get_read_only_connection() as conn:
        assert conn.execute('SELECT description FROM incidents WHERE incident_id=?',(incident_id,)).fetchone()[0]==original


def test_existing_beforeunload_is_cleared_before_running_a_page_script():
    class Client(neo.NeoMcpClient):
        def __init__(self):self.actions=[]
        def call(self,name,args):
            assert name=='snapshot'
            self.last_error={'classification':'BEFOREUNLOAD'}
            raise neo.NeoEndpointError('NEO_BEFOREUNLOAD_SNAPSHOT')
        def act(self,page,kind,**kw):self.actions.append((page,kind))
        def snapshot(self,page):pytest.fail('SDK script attempted in a page with a blocking browser dialog')
    client=Client();client.clear_task_draft(1)
    assert client.actions==[(1,'dialog_accept')]


@pytest.mark.parametrize('settled',['DEFINITE_NO_WRITE','DISPATCH_CONFIRMED'])
def test_settled_no_write_readback_does_not_consume_the_next_minute_slot(tmp_path,settled):
    store=copied_store(tmp_path);ids,value=message(store,'substack_notes')
    c,e=bind_native_neo_coordinator(store,operation_id=value['work_item_id'],output_dir=tmp_path/'old-note',
        native_invocation_id='old-note',allow_publish=True)
    first=c._dispatch_message(store.get_outbox_message(ids['message_id']),canonical_url=value['canonical_url'])
    # An earlier read request can survive after its account route settles as a
    # definite no-write. It is retained, but is not an observable public object.
    c.readback_existing_dispatch(ids['dispatch_id'])
    store.set_dispatch_status(ids['dispatch_id'],settled)
    if settled=='DISPATCH_CONFIRMED':
        store.register_platform_dispatch(dispatch_id=ids['dispatch_id'],message_id=ids['message_id'],platform='substack_notes',
            status=settled,public_object_id='c-123',public_object_url='https://substack.com/@capitalchronicle/note/c-123')
        prior=store.get_reconciliations_for_work_item(value['work_item_id'])
        if prior:
            store.set_reconciliation_status(ids['reconciliation_id'],'RECONCILED_CONFIRMED')
        else:
            store.register_reconciliation(reconciliation_id=ids['reconciliation_id'],work_item_id=value['work_item_id'],status='RECONCILED_CONFIRMED')
    store.register_outbox_message(message_id=value['work_item_id'],work_item_id=value['work_item_id'],
        destination='internal:plan-status-post',payload=json.dumps({'kind':'result','at_utc':datetime.now(timezone.utc).isoformat()}),status='PUBLISHED')
    with endpoint() as (url,state):
        result=neo.resume_stored_requests(store,client=neo.NeoMcpClient(url),output_root=tmp_path/'resumed')
        assert result['requests']==[]
        assert not state['calls']
