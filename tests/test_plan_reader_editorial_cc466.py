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
