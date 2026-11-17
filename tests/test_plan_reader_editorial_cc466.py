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


def test_explicit_page_resume_reuses_exact_source_and_retains_failed_writer(source,tmp_path,monkeypatch):
    from functools import partial
    from pathlib import Path
    import subprocess
    root,_,plan,_=source
    plan['scenario_analysis']={'mechanism':'Base chance 55%; support 1.12; alternative 35%.'}
    basis=reader.source_packet(plan,pages.load_run(plan,run_root=root))
    ref=next(s['id'] for s in basis['sources'] if '55' in s['text'] and '1.12' in s['text'])
    prose=('We assign the base case a 55% chance. We place support at 1.12. '
           'We give the alternative a 35% chance. ')*4
    value={'title':'EUR/USD: a conditional dollar view','subtitle':'We weigh the case and its countercase.',
           'introduction':'We weigh a dated conditional view.',
           'sections':{key:{'paragraphs':[{'text':prose.strip(),'source_ids':[ref]}],
                             'summary':'We assign the base case a 55% chance.'}
                       for key,_ in pages.READER_SECTIONS}}
    calls=[]
    def runner(args,**kw):
        calls.append(kw['input'])
        if len(calls)==1:
            return subprocess.CompletedProcess(args,1,b'',b'Usage limit.')
        return subprocess.CompletedProcess(args,0,json.dumps(value).encode(),b'')
    monkeypatch.setattr(editorial.shutil,'which',lambda _: 'codex.exe')
    call=partial(editorial.text_call,runner=runner)
    folder=tmp_path/'page'
    first=editorial.prepare_page(plan,output_dir=folder,run_root=root,call=call)
    assert first['status']=='PAGE_TEXT_UNAVAILABLE'
    failure=Path(first['calls'][0]['artifact_path'])
    original_bytes=failure.read_bytes()
    assert editorial.prepare_page(plan,output_dir=folder,run_root=root,call=call)==first
    assert len(calls)==1
    resumed=editorial.prepare_page(plan,output_dir=folder,run_root=root,call=call,retry_failed=True)
    assert resumed['status']=='PREPARED',resumed
    assert failure.read_bytes()==original_bytes
    assert calls[0]==calls[1]
    assert resumed['packet']['registration_hash']==plan['registration_hash']
    assert resumed['packet']['numeric_bindings']
    store=ContentOpsDurableStore(tmp_path/'resumed.sqlite3')
    packet=pages.register_page(store,resumed['packet'])
    assert json.loads(store.get_outbox_message(packet['page_id'])['payload'])['native_payload']==packet['native_payload']
    editorial.prepare_page(plan,output_dir=folder,run_root=root,call=call)
    assert len(calls)==2


def test_page_resume_cli_registers_return_for_live_consumer_without_reauthoring(source,tmp_path,monkeypatch):
    from scripts import plan_analysis_pages as cli
    root,_,plan,manuscript=source
    packet=pages.render(plan,manuscript,run_root=root,output_dir=tmp_path/'page')
    store=ContentOpsDurableStore(tmp_path/'cli.sqlite3')
    calls=[]
    def prepare(selected,**kwargs):
        calls.append((selected,kwargs))
        return {'status':'PREPARED','packet':packet}
    monkeypatch.setattr(cli,'read_export',lambda:{'status':{'plans':[plan]}})
    monkeypatch.setattr(editorial,'prepare_page',prepare)
    args=['prepare-page','--plan-id',plan['plan_id'],'--store',str(store.db_path),
          '--output-dir',str(tmp_path/'page'),'--retry-failed-text','--result',str(tmp_path/'result.json')]
    assert cli.main(args)==0
    assert calls==[(plan,{'output_dir':tmp_path/'page','retry_failed':True})]
    held=store.get_outbox_message('plan-analysis-'+plan['plan_id'])
    assert json.loads(held['payload'])['native_payload']==packet['native_payload']
    assert cli.main(args)==0
    assert len(calls)==1
    assert store.list_outbox_messages(destination='substack')==[]


@pytest.mark.parametrize('rationale,expected',[
    ('Dollar strength supports the view. Probability: 55% lower at the exit.',55),
    ('Dollar strength supports the view. Touch probability 55%; probability up 45%.',None),
    ('Dollar strength supports the view. Probability: 55% higher at the exit.',None),
])
def test_new_variants_use_explicit_original_odds_without_inventing_a_complement(source,tmp_path,rationale,expected):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    from test_plan_analysis_distribution_cc435 import confirm
    root,folder,plan,manuscript=source
    result={'native_synthesis':{'candidates':[{'candidate_id':'cand_macro_eurusd','rationale':rationale}]}}
    plan.update(direction='BEARISH',analysis_result_hash=sha256_of(result),
        scenario_analysis={'base_case':{'probability_pct':None},'main_alternative':{'probability_pct':None}})
    for name in ('owner-native.json','desktop-manual-result.json'):
        (folder/name).write_text(json.dumps(result),encoding='utf-8')
    freeze=json.loads((folder/'final-decision-freeze.json').read_bytes())
    freeze['qualitative_result_hash']=plan['analysis_result_hash']
    (folder/'final-decision-freeze.json').write_text(json.dumps(freeze),encoding='utf-8')
    run=pages.load_run(plan,run_root=root)
    old=reader.source_packet(plan,run)
    current=reader.source_packet(plan,run,original_probabilities=True)
    assert old['scenario_analysis']['base_case']['probability_pct'] is None
    assert plan['scenario_analysis']['base_case']['probability_pct'] is None
    assert current['scenario_analysis']['base_case']['probability_pct']==expected
    assert current['scenario_analysis']['main_alternative']['probability_pct'] is None
    if expected is None:
        assert current==old
        return
    # The new social consumer receives the held original reasoning and odds.
    # Old projections remain byte-equivalent for their exact issued packets.
    manuscript['sections']={key:{'paragraphs':[{'text':rationale,
        'refs':[{'file':'owner-native.json','pointer':'/native_synthesis/candidates/0/rationale'}],
        'rights':'CAPITAL_CHRONICLE_ORIGINAL_ANALYSIS','source_name':'Capital Chronicle'}],
        'summary':'Dollar strength supports the view.'} for key,_ in pages.SECTIONS}
    store=ContentOpsDurableStore(tmp_path/'original-odds.sqlite3')
    packet=pages.register_page(store,pages.render(plan,manuscript,run_root=root,output_dir=tmp_path/'page'))
    confirm(store,packet['page_id'],packet['plan']['plan_hash'],'substack','123',
        'https://capitalchronicle.substack.com/p/original-odds')
    row={'kind':'setup','symbol':'EURUSD','instrument_title':'EUR/USD','source_plan':plan,
        'source_plan_registration':plan['registration_hash'],'levels':{'zone_low':1.12,'zone_high':1.13,
        'invalidation_level':1.15,'direction':'bearish','valid_until_utc':'2026-11-13T13:15:00Z'}}
    sid=current['original_probability_binding']['source_id']
    def field(text):return {'text':text,'source_ids':[sid]}
    fields={'hook':field('Dollar strength supports the view.'),
        'points':[{'layer':'macro',**field('The dollar supports the view.')}],
        'scenario_main':field('Main (55%): the euro is lower at the exit.'),'scenario_alt':None,
        'alt_text':field('The chart shows the original plan.')}
    def call(prompt,**kwargs):
        assert '55% lower at the exit' in prompt
        assert '"probability_pct": 55' in prompt
        return {'status':'RETURNED','output':fields}
    prepared=editorial.prepare_variants(packet,row,output_dir=tmp_path/'variants',call=call)
    assert prepared['status']=='PREPARED',prepared
    updated={**row,**{k:v for k,v in prepared.items() if k!='status'},
             'analysis_publication':{'canonical_url':'https://capitalchronicle.substack.com/p/original-odds'}}
    editorial.validate_reader_row(store,updated)
    assert updated['reader_source']['original_probability_binding']['statement']=='55% lower at the exit'
