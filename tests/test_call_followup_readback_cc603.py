"""A published original/record link remains verifiable after platform rendering."""
import pytest

from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
from live_contentops.neo_endpoint_executor_v1 import NeoBrowserDriver


@pytest.mark.parametrize('case', ['correct', 'wrong_target', 'hidden_card', 'other_object'])
def test_note_original_link_card_reaches_the_coordinator_readback(case):
    target = 'https://capitalchronicle.substack.com/p/original-gold'
    public = 'https://substack.com/@capitalchronicle/note/c-603'
    text = 'Correction: the post was late.\nOriginal analysis: ' + target + '\nAnalysis only.'
    observed = 'Correction: the post was late.\nOriginal analysis:\nAnalysis only.'
    link = {'url':target if case != 'wrong_target' else target+'-wrong', 'text':'Original gold',
            'card_visible':case != 'hidden_card', 'public_object_url':public if case != 'other_object' else public+'0'}
    intent = {'work_item_id':'cc603-correction', 'plan_hash':'bound-plan', 'package_identity':'cc603-correction',
              'payload':text, 'native_payload':{'text':text,'full_text':text},
              'destination_plan':{'surface':'SUBSTACK_NOTE','payload_hash':'bound-text'}}
    def execute(request):
        return {'request_sha256':request['request_sha256'], 'status':'SUCCESS', 'content_verified':True,
                'public_object_id':'c-603','public_object_url':public,'observed_identity':'@capitalchronicle',
                'observed_text':observed,'observed_links':[link]}
    result = NeoDestinationHandoff(native_executor=execute).readback(destination='substack_notes', intent=intent,
                      public_object_id='c-603', public_object_url=public)
    assert result['content_binding_checks']['text_match'] is (case == 'correct')
    assert result['verified'] is (case == 'correct')


@pytest.mark.parametrize('case', ['correct', 'wrong_target', 'other_object'])
def test_x_original_and_record_short_links_keep_the_exact_bound_targets(case):
    target = 'https://t.me/CapitalChronicle/166'
    record = 'https://t.me/CapitalChronicle/134'
    public = 'https://x.com/Capitalnicle/status/123'
    text = 'Original: '+target+'\nPinned record: '+record
    request = {'destination':'x', 'content_binding':{'expected_text_segments':[text]}}
    post = {'public_object_url':public, 'observed_text':'Original: t.me/CapitalChronicle/166\nPinned record: t.me/CapitalChronicle/134',
            'links':[{'url':'https://t.co/abc','expanded_url':target if case != 'wrong_target' else target+'0',
                      'text':'t.me/CapitalChronicle/166'},
                     {'url':'https://t.co/def','expanded_url':record,'text':'t.me/CapitalChronicle/134'}]}
    assert NeoBrowserDriver._matches(request, text, post) is (case != 'wrong_target')
    from live_contentops.neo_destination_handoff_v1 import _x_reader_text, _bound_link_targets, _text
    links = NeoBrowserDriver._links(request, post)
    if case == 'other_object':
        for link in links:
            link['public_object_url'] = public+'0'
    normalized = _x_reader_text(post['observed_text'], links, public, '', bound_urls=_bound_link_targets(request['content_binding']))
    assert (_text(text) in normalized) is (case == 'correct')


@pytest.mark.parametrize('changed', [False, True])
def test_note_chart_compares_its_observed_public_original_without_looser_pixels(tmp_path, changed):
    from hashlib import sha256
    from io import BytesIO
    from PIL import Image, ImageDraw
    from live_contentops.neo_endpoint_executor_v1 import compare_public_images
    source = Image.new('RGB', (512,320), 'white')
    ImageDraw.Draw(source).text((30,80), 'CALL LEVEL 1234', fill='black', font_size=24)
    path=tmp_path/'chart.png'; source.save(path)
    original='https://substack-post-media.s3.amazonaws.com/public/images/exact_512x320.png'
    small='https://substackcdn.com/image/fetch/w_800,f_webp/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fexact_512x320.png'
    delivered=source.copy()
    if changed:
        draw=ImageDraw.Draw(delivered);draw.rectangle((30,80,400,120), fill='white')
        draw.text((30,80), 'CALL LEVEL 1284', fill='black', font_size=24)
    buffer=BytesIO();delivered.save(buffer,format='PNG')
    class Http:
        def get(self,url,**kwargs):
            assert url == original
            assert kwargs['allow_redirects'] is False
            class Response:
                status_code=200
                def raise_for_status(self):pass
                def iter_content(self,size):yield buffer.getvalue()
            return Response()
    result=compare_public_images({'destination':'substack_notes','content_binding':{
        'media_manifest':[{'path':str(path),'sha256':sha256(path.read_bytes()).hexdigest()}]}},
        {'public_object_url':'https://substack.com/@capitalchronicle/note/c-603','public_image_urls':[small]},http=Http())
    compared=result['media_comparisons'][0]
    assert compared['source_pixels_match'] is (not changed)
    assert compared['observed_image_url'] == small and compared['public_image_url'] == original


def test_repaired_reader_refreshes_exact_object_without_changing_a_publish_claim(tmp_path):
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.neo_endpoint_executor_v1 import EndpointNeoExecutor
    store=ContentOpsDurableStore(tmp_path/'state.sqlite3')
    executor=EndpointNeoExecutor(store,operation_id='cc603-readback',output_dir=tmp_path/'native',
                                 native_invocation_id='test',allow_publish=False)
    request={'action':'READBACK','work_item_id':'cc603-readback','destination':'substack_notes',
             'content_binding':{},'public_object_id':'c-603','public_object_url':'https://substack.com/@capitalchronicle/note/c-603'}
    revised=executor.fresh_readback_request(request)
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    assert revised['request_sha256']==sha256_of({k:v for k,v in revised.items() if k!='request_sha256'})
    assert revised['readback_transport_revision']==executor.executor_revision
    assert revised['action']=='READBACK' and revised['public_object_id']=='c-603'
    assert store.list_platform_dispatches()==[]


def test_same_note_restore_uses_edit_and_save_and_cannot_create_another_post():
    public='https://substack.com/@capitalchronicle/note/c-603'
    text='Original: https://t.me/CapitalChronicle/166\nRecord: https://t.me/CapitalChronicle/134'
    class Client:
        def __init__(self):self.actions=[];self.copy=text
        def open(self,destination,url):assert url==public;return 1
        def wait(self,*args):pass
        def snapshot(self,page):return {'refs':[{'role':'button','name':'More options','ref':'more'},
            {'role':'menuitem','name':'Edit','ref':'edit'},{'role':'textbox','name':"What's on your mind?",'ref':'editor'}]}
        def act(self,page,kind,**kwargs):self.actions.append((kind,kwargs))
        def call(self,name,args):assert name=='navigate' and args['url']==public
        def run(self,page,phase,**kw):
            if phase=='readback':return {'notes':[{'public_object_id':'c-603','public_object_url':public,
                'observed_text':self.copy,'links':[]}]}
            if phase=='note_inline_copy':assert kw['text']==text;return {'pasted':True}
            assert phase=='publish' and kw['edit_existing'] is True
            return {'status':'CLICKED','pre_click_posts':[text]}
    client=Client()
    request={'action':'EDIT_EXISTING','destination':'substack_notes','public_object_url':public,
        'public_object_id':'c-603','expected_identity':'@capitalchronicle','request_sha256':'bound',
        'approved_presentation_restore':{'original_intent_sha256':'frozen'},'native_payload':{'text':text},
        'content_binding':{'expected_text_segments':[text]}}
    result=NeoBrowserDriver(client).perform({'request':request})
    assert result['readback']['public_object_url']==public
    assert [a[1].get('ref') for a in client.actions if a[0]=='click']==['more','edit']
    assert result['pre_click_posts']==[text]
