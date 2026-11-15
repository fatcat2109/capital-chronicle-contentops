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
