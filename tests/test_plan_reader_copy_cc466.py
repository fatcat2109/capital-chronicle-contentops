"""The new reader contract protects actual copy and bound consumer payloads."""
from copy import deepcopy

import pytest

from live_contentops import plan_reader_copy_v1 as reader
from live_contentops import plan_status_posts_v1 as posts


def source_and_fields():
    texts = [
        ('macro', 'Hot inflation supports the dollar. CPI rose 0.3% in October.'),
        ('priced_in', 'The expected rate path puts pressure on the euro.'),
        ('positioning', 'CFTC data for 3 Nov show crowded euro shorts.'),
        ('scenarios', 'Main 50%: the euro weakens. Alternative 35%: short covering lifts the euro.'),
    ]
    source = {'sources': [{'id':str(i),'layer':layer,'text':text} for i,(layer,text) in enumerate(texts)],
              'scenario_analysis': {'base_case':{'probability_pct':50}, 'main_alternative':{'probability_pct':35}}}
    def f(text, *ids):
        return {'text':text,'source_ids':list(ids)}
    fields = {'hook':f('Hot inflation keeps the dollar supported.', '0'),
        'points':[{'layer':layer, **f(text,str(i))} for i,(layer,text) in enumerate(texts[:3])],
        'scenario_main':f('Main (50%): the euro weakens.', '3'),
        'scenario_alt':f('Alternative (35%): short covering lifts the euro.', '3'),
        'alt_text':f('Inflation supports the dollar.', '0')}
    return source, fields


@pytest.mark.parametrize('text', [
    'A vol-normalised move.', 'There are 5 calls judged.', 'The outcome is STOPPED_OUT.',
    'Post-CPI yields not…', 'The dollar rises...', 'Our account balance is 500 dollars.',
    'The 1-day reading uses SMA50.', 'The move is z +1.2.',
])
def test_real_bad_public_text_is_refused(text):
    with pytest.raises(ValueError):
        reader.check_text(text, source=text)


def test_meaningful_macro_words_and_sourced_acronym_are_kept():
    for text in ('The current account matters.', 'The balance sheet contracts.', 'Armed forces leave the region.'):
        assert reader.check_text(text, source=text)['status'] == 'PASS'
    report=reader.check_text('HICP rose 0.3%.', source='HICP rose 0.3%.')
    assert report['automatic_acronyms']==['HICP']
    report=reader.check_text('NEWWORD matters.', source='The rate path matters.')
    assert report['status']=='PASS' and report['unknown_acronyms']==['NEWWORD']


def test_every_field_number_is_bound_to_its_own_source():
    source, fields = source_and_fields()
    assert reader.validate_fields(fields, source)
    fields['points'][0]['text']='CPI rose 0.4% in October.'
    with pytest.raises(ValueError, match='NUMBER_NOT_IN_BOUND_SOURCE'):
        reader.validate_fields(fields, source)


def test_alternative_is_not_computed_or_suppressed():
    source, fields=source_and_fields()
    fields['scenario_alt']['text']='Alternative (50%): short covering lifts the euro.'
    with pytest.raises(ValueError, match='SCENARIO_ODDS_CHANGED'):
        reader.validate_fields(fields,source)
    fields['scenario_alt']=None
    with pytest.raises(ValueError, match='HELD_ALTERNATIVE_ODDS_OMITTED'):
        reader.validate_fields(fields,source)
    source['scenario_analysis']['main_alternative']['probability_pct']=None
    assert reader.validate_fields(fields,source)


def test_real_consumer_has_link_only_in_first_x_reply_and_full_forces():
    source, fields=source_and_fields()
    # Keep each complete line short enough for X's three-point reply.
    fields['points'][0]['text']='Hot inflation supports the dollar.'
    fields['points'][1]['text']='The rate path weighs on the euro.'
    fields['points'][2]['text']='Euro shorts are crowded.'
    row={'reader_fields':fields,'reader_source':source,'discord_delivery':'channel',
         'analysis_publication':{'canonical_url':'https://capitalchronicle.substack.com/p/euro-view'}}
    payloads=reader.payloads(row,'chart')
    x=payloads['x']
    assert 'http' not in x['text']
    assert row['analysis_publication']['canonical_url'] in x['reply_texts'][0]
    assert reader.PUBLIC_NOTICE in x['reply_texts'][0]
    assert x['posts'][0]['media_asset_ids']==['chart']
    assert all(posts._x_length(p['text'])<=280 for p in x['posts'])
    assert x['reply_texts'][1].index('Macro:') < x['reply_texts'][1].index('Priced in:') < x['reply_texts'][1].index('Positioning:')
    assert all(label in payloads['telegram']['text'] for label in ('Macro:', 'Priced in:', 'Positioning:'))
    assert 'calls judged' not in payloads['telegram']['text']


def test_source_force_cannot_be_replaced_by_technical_only():
    source, fields=source_and_fields()
    fields['points']=[{'layer':'technical','text':'The euro weakens.','source_ids':['3']}]
    with pytest.raises(ValueError,match='HELD_MARKET_FORCES_OMITTED'):
        reader.validate_fields(fields,source)


def test_et_twelve_hour_conversion_uses_date_correct_zone():
    assert reader.et('2026-11-11T16:20:00Z')=='Wed 11 Nov, 11:20 AM ET'
    assert reader.et('2026-07-11T16:20:00Z')=='Sat 11 Jul, 12:20 PM ET'


def test_r_result_is_exported_not_inferred_from_stopped():
    assert reader.result_r({'outcome':{'result':'STOPPED'}}) is None
    assert str(reader.result_r({'outcome':{'score':{'result_r':-1.0}}}))=='-1.0'
    source,fields=source_and_fields()
    fields.pop('scenario_main');fields.pop('scenario_alt')
    fields['result_line']={'text':'Gold, short from 3 Nov: stopped out. Result: −1.0R.','source_ids':['3']}
    fields['points']=[]
    source['sources'][3]['text']='Gold short 3 Nov stopped out. -1.0'
    source['result_r']='-1.0'
    assert reader.validate_fields(fields,source)
    source['result_r']='-0.8'
    with pytest.raises(ValueError,match='R_RESULT_NOT_IN_EXPORT'):
        reader.validate_fields(fields,source)


def test_signed_r_result_exception_keeps_money_volume_and_account_private():
    from live_contentops.event_article_guard_v1 import public_execution_copy_forbidden
    assert not public_execution_copy_forbidden('Result: −1.0R.')
    assert public_execution_copy_forbidden('Result: −1.0R. The size is 2 lots.')
    assert public_execution_copy_forbidden('The account balance is 100000.')
    assert public_execution_copy_forbidden('We made 2R.')


def test_unavailable_status_never_becomes_closed_in_new_page_footer():
    plan={'status':None,'registered_at_utc':'2026-11-11T16:20:00Z'}
    freeze={'frozen_at_utc':'2026-11-11T16:19:00Z'}
    assert 'unavailable' in reader.page_footer(plan,freeze)[1]
    assert 'closed' not in reader.page_footer(plan,freeze)[1]
    assert 'Status: closed' in reader.page_footer({**plan,'status':'EXPIRED'},freeze)[1]
