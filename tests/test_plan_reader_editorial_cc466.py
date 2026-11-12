from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest

from live_contentops import plan_reader_editorial_v1 as editorial
from live_contentops import plan_reader_copy_v1 as reader
from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_status_posts_v1 as posts
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from test_plan_reader_copy_cc466 import source_and_fields
from test_plan_analysis_pages_cc432 import source


def test_nine_section_manuscript_reads_original_run_and_keeps_private_hash_out(source,tmp_path):
    root,_,plan,old=source
    manuscript={**old,'reader_contract':reader.CONTRACT,
        'sections':{k:deepcopy(old['sections']['macro']) for k,_ in pages.READER_SECTIONS}}
    packet=pages.render(plan,manuscript,run_root=root,output_dir=tmp_path/'page')
    body=packet['native_payload']['body_markdown']
    assert [body.index('## '+title) for _,title in pages.READER_SECTIONS] == sorted(
        body.index('## '+title) for _,title in pages.READER_SECTIONS)
    assert packet['freeze']['immutable_hash'] not in body
    assert 'before this page was published.' in body
    assert '8:34 PM ET' in body


def test_missing_optional_critic_note_uses_held_critical_output(source):
    root,folder,plan,_=source
    (folder/'critic-note.json').unlink()
    run=pages.load_run(plan,run_root=root)
    assert 'critical-native.json' in run['documents']
    assert 'critic-note.json' not in run['documents']


def test_page_pending_remains_unsettled_and_never_calls_variant_writer(tmp_path):
    store=ContentOpsDurableStore(tmp_path/'store.sqlite3')
    row={'source_plan':{'plan_id':'not-published'}}
    def forbidden(*a,**kw):
        pytest.fail('No variants or public writes before the canonical exists')
    result=editorial.prepare_social_row(store,row,root=tmp_path,call=forbidden)
    assert result['status']=='CANONICAL_PENDING'
    assert result['cause']=='SUBSTACK_PLAN_PAGE_NOT_CONFIRMED'


def test_whole_native_source_and_et_transforms_are_bound_to_own_plan(source):
    root,_,plan,_=source
    plan.update(registered_at_utc='2026-11-11T16:20:00Z',
        scenario_analysis={'mechanism':'Hot inflation supports the dollar.',
            'base_case':{'probability_pct':55,'market_move':'The dollar strengthens.'},
            'main_alternative':{'probability_pct':35,'market_move':'The dollar weakens.'}})
    run=pages.load_run(plan,run_root=root)
    packet=reader.source_packet(plan,run)
    transformed=next(s for s in packet['sources'] if s['ref'].get('transform')=='ET12')
    assert pages._source_text(run,transformed['ref'])==transformed['text']
    assert '11:20 AM ET' in transformed['text']


def test_new_composer_uses_force_fields_and_old_composer_bytes_stay_available():
    source_,fields=source_and_fields()
    fields['points'][0]['text']='Hot inflation supports the dollar.'
    fields['points'][1]['text']='The rate path weighs on the euro.'
    fields['points'][2]['text']='Euro shorts are crowded.'
    row={'reader_contract':reader.CONTRACT,'reader_source':source_,'reader_fields':fields,
        'analysis_publication':{'canonical_url':'https://capitalchronicle.substack.com/p/euro-view'}}
    result=cards.compose(row)
    assert result['lead']==fields['hook']['text']
    assert 'Macro:' in result['text'] and 'calls judged' not in result['text']
    old=cards.compose({'kind':'run','at_utc':'2026-11-10T08:00:00Z','card_keys':['one']})
    assert 'run: 1.' in old['text']


def test_acronym_only_rewrite_happens_once_then_logs_without_gate(source,tmp_path):
    root,_,plan,_=source
    run=pages.load_run(plan,run_root=root)
    basis=reader.source_packet(plan,run)
    assert basis['plan_id']==plan['plan_id']
    check=reader.check_text('HICP matters.',source='HICP matters.')
    assert check['automatic_acronyms']==['HICP']


@pytest.mark.parametrize('condition', ['exact','wrong_dispatch','uncertain','public_object'])
def test_daily_failure_is_released_only_for_bound_preclick_and_reconciled_absence(tmp_path,condition):
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
    store=ContentOpsDurableStore(tmp_path/'store.sqlite3')
    store.create_work_item(story_id='page',work_item_id='page',title='Page',target_surface='SUBSTACK_ARTICLE')
    store.register_outbox_message(message_id='outbox_test',work_item_id='page',destination='substack',payload='{}')
    store.register_platform_dispatch(dispatch_id='dispatch_test',message_id='outbox_test',platform='substack',
        status='RECONCILED_ABSENT_SAFE_TO_RETRY',
        public_object_id='123' if condition=='public_object' else None)
    c=Coordinator(store=store,transport_runtime=None)
    c._record_destination_day_failure({'work_item_id':'page'},'substack',
        {'dispatch_id':'dispatch_test','safe_error_classification':'NEO_RETURN_BINDING_OR_IDENTITY_MISMATCH'})
    result={'request_sha256':'request','native_tool_return_sha256':'a'*64,
        'status':'FAILED_BEFORE_WRITE','stage':'BEFORE_PUBLISH_CLICK',
        'definite_no_write':condition!='uncertain','public_write_performed':False}
    request={'action':'PUBLISH','destination':'substack','work_item_id':'page',
        'dispatch_attempt_identity':'wrong' if condition=='wrong_dispatch' else 'dispatch_test'}
    class Returned:
        def _get(self,key,kind):
            return {'request':request} if kind=='request' else {'result':result}
    if condition=='exact':
        c.resolve_reconciled_native_preclick_failure('substack',native_executor=Returned(),request_hash='request')
        assert c._destination_day_failure('substack') is None
        assert store.get_platform_dispatch('dispatch_test')['status']=='RECONCILED_ABSENT_SAFE_TO_RETRY'
    else:
        with pytest.raises(ValueError,match='EXACT_NATIVE_PRECLICK_AND_ABSENCE'):
            c.resolve_reconciled_native_preclick_failure('substack',native_executor=Returned(),request_hash='request')
        assert c._destination_day_failure('substack') is not None


def test_a_missing_identity_before_an_observed_no_click_is_not_unknown_write():
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
    def no_click(request):
        return {'request_sha256':request['request_sha256'],'native_tool_return_sha256':'a'*64,
            'status':'FAILED_BEFORE_WRITE','definite_no_write':True,'public_write_performed':False,
            'stage':'BEFORE_PUBLISH_CLICK','reason_code':'CC466_SOURCE_STATUS_COPY_REPAIR'}
    h=NeoDestinationHandoff(native_executor=no_click)
    result=h.publish(destination='substack',intent={'work_item_id':'page','native_payload':{'title':'A page','body_markdown':'A sourced page.'}},
        authorization_context={})
    assert result['status']=='FAILED_BEFORE_WRITE' and result['definite_no_write']


def test_source_validation_uses_the_confirmed_page_not_only_writer_fields(source,tmp_path,monkeypatch):
    root,_,plan,manuscript=source
    packet=pages.render(plan,manuscript,run_root=root,output_dir=tmp_path/'page')
    store=ContentOpsDurableStore(tmp_path/'store.sqlite3')
    packet=pages.register_page(store,packet)
    supplied=reader.source_packet(plan,pages.load_run(plan,run_root=root))
    row={'source_plan':plan,'source_plan_registration':plan['registration_hash'],
        'reader_source':supplied,'analysis_publication':{'canonical_url':'https://capitalchronicle.substack.com/p/view'},
        'reader_fields':{}}
    with pytest.raises(ValueError,match='CANONICAL_PAGE_NOT_CONFIRMED'):
        editorial.validate_reader_row(store,row)
    monkeypatch.setattr(pages,'confirmed_publication',lambda *a:{'canonical_url':row['analysis_publication']['canonical_url']})
    row['reader_source']={**supplied,'sources':[{'id':'fake','text':'Invented 99%.','layer':'macro'}]}
    with pytest.raises(ValueError,match='ANALYSIS_SOURCE_CHANGED'):
        editorial.validate_reader_row(store,row)


def test_explicit_native_retry_preserves_the_failure_and_caches_its_return(tmp_path):
    import subprocess
    calls=[]
    def runner(args,**kw):
        calls.append(args)
        if len(calls)<=2:
            raise subprocess.TimeoutExpired(args,120,output=b'')
        return subprocess.CompletedProcess(args,0,b'{"answer":"Returned text."}',b'')
    first=editorial.text_call('Exact input.',root=tmp_path,runner=runner)
    assert first['cause']=='AGY_VARIANTS_TIMEOUT_120S'
    assert editorial.text_call('Exact input.',root=tmp_path,runner=runner)==first
    assert len(calls)==2
    second=editorial.text_call('Exact input.',root=tmp_path,runner=runner,retry_failed=True)
    assert second['status']=='RETURNED'
    assert json.loads(__import__('pathlib').Path(first['artifact_path']).read_bytes())==first
    assert second['artifact_path']!=first['artifact_path']
    assert editorial.text_call('Exact input.',root=tmp_path,runner=runner)==second
    assert len(calls)==3
