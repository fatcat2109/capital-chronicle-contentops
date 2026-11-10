from copy import deepcopy
from hashlib import sha256
import json

import pytest

from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator


@pytest.fixture
def source(tmp_path):
    root = tmp_path / 'runs'
    folder = root / 'requests' / 'request-test'
    folder.mkdir(parents=True)
    result = {'native_synthesis': {'candidates': [{'rationale': 'Base chance 55%; support 1.12; alternative 35%.'}]}}
    plan = {'plan_id': 'plan_test', 'registration_hash': 'f' * 64, 'run_id': 'request-test',
            'analysis_result_hash': sha256_of(result), 'asset_id': 'EURUSD'}
    freeze = {'frozen_at_utc': '2026-11-10T01:34:00Z', 'immutable_hash': 'e' * 64,
              'qualitative_result_hash': plan['analysis_result_hash']}
    documents = {name: {} for name in ['role-pack.json', 'critic-note.json', 'integrated-owner-record.json',
                  'plan-geometry.json', 'options-context.json', 'primary-native.json', 'critical-native.json']}
    documents.update({'role-evidence.json': [], 'owner-native.json': result,
                      'desktop-manual-result.json': result, 'final-decision-freeze.json': freeze})
    for name, value in documents.items():
        (folder / name).write_text(json.dumps(value), encoding='utf-8')
    paragraph = {'text': 'The base case has a 55% chance; support is 1.12. The alternative is 35%.',
                 'refs': [{'file': 'owner-native.json', 'pointer': '/native_synthesis/candidates/0/rationale'}],
                 'rights': 'CAPITAL_CHRONICLE_ORIGINAL_ANALYSIS', 'source_name': 'Capital Chronicle'}
    manuscript = {'plan_id': plan['plan_id'], 'registration_hash': plan['registration_hash'],
                  'title': 'EUR/USD: a conditional dollar view', 'subtitle': 'The case and its countercase.',
                  'introduction': 'A dated analysis with conditional levels.',
                  'sections': {k: {'paragraphs': [deepcopy(paragraph)], 'summary': 'Base case 55%; alternative 35%.'}
                               for k, _ in pages.SECTIONS}}
    return root, folder, plan, manuscript


def rendered(source, tmp_path):
    root, _, plan, manuscript = source
    return pages.render(plan, manuscript, run_root=root, output_dir=tmp_path / 'page')


@pytest.mark.parametrize('text,reason', [
    ('The desk is AI-run.', 'DESK_AI_LABEL'), ('Written by GPT-6.1.', 'DESK_AI_LABEL'),
    ('The position size is 0.5 lots.', 'PRIVATE_ACCOUNT_OR_SIZE'),
    ('Our account balance is $100000.', 'PRIVATE_ACCOUNT_OR_SIZE'),
    ('The source is https://x.com/list/status/123.', 'PRIVATE_X_LIST'),
])
def test_filter_refuses_owner_named_harms(text, reason):
    with pytest.raises(ValueError, match=reason):
        pages.public_filter(text)


def test_private_list_line_and_unlicensed_text_are_refused():
    text = 'A retained private sentence about the latest policy event.'
    with pytest.raises(ValueError, match='PRIVATE_X_LIST'):
        pages.public_filter(text, private_texts=[text])
    with pytest.raises(ValueError, match='PUBLIC_REDISTRIBUTION_NOT_LICENSED'):
        pages.public_filter('A licensed report.', rights='LICENSE_REQUIRED')
    assert pages.public_filter('AI investment is a market theme, with uncertain returns.')['status'] == 'PASS'


def test_all_sections_and_each_number_trace_to_exact_run_bytes(source, tmp_path):
    packet = rendered(source, tmp_path)
    assert len(packet['numeric_bindings']) == 7
    assert all(b['refs'] and b['numbers'] for b in packet['numeric_bindings'])
    assert all(title in packet['native_payload']['body_markdown'] for _, title in pages.SECTIONS)
    assert '20:34 ET on 9 November 2026' in packet['native_payload']['body_markdown']
    assert packet['freeze']['immutable_hash'] in packet['native_payload']['body_markdown']
    assert len(packet['source_manifest']) == 11
    assert (tmp_path / 'page/article.html').is_file()


def test_numeric_invention_and_unsupported_probability_complement_fail(source, tmp_path):
    root, _, plan, manuscript = source
    manuscript['sections']['scenarios']['paragraphs'][0]['text'] = 'The remaining chance is 10%.'
    with pytest.raises(ValueError, match='UNBOUND_NUMBER:scenarios'):
        pages.render(plan, manuscript, run_root=root, output_dir=tmp_path / 'page')


def test_plan_and_freeze_join_fail_closed(source, tmp_path):
    root, folder, plan, manuscript = source
    altered = deepcopy(plan)
    altered['registration_hash'] = 'wrong'
    with pytest.raises(ValueError, match='EXACT_PLAN'):
        pages.render(altered, manuscript, run_root=root, output_dir=tmp_path / 'page')
    freeze = json.loads((folder / 'final-decision-freeze.json').read_bytes())
    freeze['qualitative_result_hash'] = 'wrong'
    (folder / 'final-decision-freeze.json').write_text(json.dumps(freeze))
    with pytest.raises(ValueError, match='FREEZE_RESULT_MISMATCH'):
        pages.render(plan, manuscript, run_root=root, output_dir=tmp_path / 'page')


def test_page_is_wired_to_real_coordinator_and_confirmed_summary_consumer(source, tmp_path):
    from live_contentops.plan_call_cards_v1 import analysis_publication
    store = ContentOpsDurableStore(tmp_path / 'store.sqlite3')
    packet = pages.register_page(store, rendered(source, tmp_path))
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None, published_content_path=tmp_path/'published.jsonl')
    coordinator.register_plan(packet['page_id'], packet['plan'])
    messages = store.list_outbox_messages(destination='substack')
    assert len(messages) == 1
    intent = json.loads(messages[0]['payload'])
    assert intent['native_payload'] == packet['native_payload']
    assert intent['destination_plan']['substack_delivery_mode'] == 'WEB_ONLY'
    assert 'published_content_export' not in intent
    pages.validate_intent(store, intent)
    assert pages.confirmed_publication(store, packet['source_plan']) is None
    ids = coordinator._ids(packet['page_id'], packet['plan']['plan_hash'], 'substack')
    store.register_platform_dispatch(dispatch_id=ids['dispatch_id'], message_id=ids['message_id'], platform='substack',
        status='DISPATCH_CONFIRMED', public_object_id='123', public_object_url='https://capitalchronicle.substack.com/p/eur-analysis')
    store.register_reconciliation(reconciliation_id=ids['reconciliation_id'], work_item_id=packet['page_id'], status='RECONCILED_CONFIRMED')
    publication = pages.confirmed_publication(store, packet['source_plan'])
    accepted, cause = analysis_publication({**packet['source_plan'], 'analysis_publication': publication})
    assert cause is None and accepted['summary'] == packet['summary']
    coordinator.register_plan(packet['page_id'], packet['plan'])
    assert len(store.list_outbox_messages(destination='substack')) == 1


def test_mutated_source_and_mutated_intent_cannot_reach_write(source, tmp_path):
    _, folder, _, _ = source
    store = ContentOpsDurableStore(tmp_path / 'store.sqlite3')
    packet = pages.register_page(store, rendered(source, tmp_path))
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None)
    coordinator.register_plan(packet['page_id'], packet['plan'])
    intent = json.loads(store.list_outbox_messages(destination='substack')[0]['payload'])
    intent['native_payload']['body_markdown'] += ' Changed.'
    with pytest.raises(ValueError, match='EXACT_WEB_ONLY_INTENT'):
        pages.validate_intent(store, intent)
    (folder / 'options-context.json').write_text('{"changed":true}')
    with pytest.raises(ValueError, match='SOURCE_BYTES_CHANGED'):
        coordinator.register_plan(packet['page_id'], packet['plan'])


def test_native_request_carries_every_paragraph_and_bound_card_without_article_compiler(source, tmp_path):
    from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
    store = ContentOpsDurableStore(tmp_path / 'store.sqlite3')
    packet = pages.register_page(store, rendered(source, tmp_path))
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None)
    coordinator.register_plan(packet['page_id'], packet['plan'])
    intent = json.loads(store.list_outbox_messages(destination='substack')[0]['payload'])
    request = NeoDestinationHandoff().request(destination='substack', action='READBACK', intent=intent)
    assert request['native_payload'] == packet['native_payload']
    assert request['content_binding']['expected_text_segments'] == list(packet['native_payload'].values())


def test_local_prewrite_resolution_preserves_real_failure_circuit_and_exact_unknown(source, tmp_path):
    store = ContentOpsDurableStore(tmp_path / 'store.sqlite3')
    packet = pages.register_page(store, rendered(source, tmp_path))
    coordinator = DurablePublicationCoordinator(store=store, transport_runtime=None)
    coordinator.register_plan(packet['page_id'], packet['plan'])
    intent = json.loads(store.list_outbox_messages(destination='substack')[0]['payload'])
    ids = coordinator._ids(packet['page_id'],packet['plan']['plan_hash'],'substack')
    store.register_platform_dispatch(dispatch_id=ids['dispatch_id'],message_id=ids['message_id'],platform='substack',status='UNKNOWN_WRITE')
    coordinator._record_destination_day_failure(intent,'substack',{'dispatch_id':ids['dispatch_id'],'safe_error_classification':'KeyError'})
    coordinator.resolve_local_neo_prewrite_failure('substack')
    assert coordinator._destination_day_failure('substack') is None
    assert store.get_platform_dispatch(ids['dispatch_id'])['status'] == 'UNKNOWN_WRITE'
    coordinator._record_destination_day_failure(intent,'substack',{'dispatch_id':ids['dispatch_id'],'safe_error_classification':'TimeoutError'})
    assert coordinator._destination_day_failure('substack')['safe_error_classification'] == 'TimeoutError'


def test_local_resolution_refuses_any_issued_native_write_request(source, tmp_path):
    store=ContentOpsDurableStore(tmp_path/'store.sqlite3')
    packet=pages.register_page(store,rendered(source,tmp_path))
    c=DurablePublicationCoordinator(store=store,transport_runtime=None)
    c.register_plan(packet['page_id'],packet['plan'])
    intent=json.loads(store.list_outbox_messages(destination='substack')[0]['payload'])
    ids=c._ids(packet['page_id'],packet['plan']['plan_hash'],'substack')
    store.register_platform_dispatch(dispatch_id=ids['dispatch_id'],message_id=ids['message_id'],platform='substack',status='UNKNOWN_WRITE')
    c._record_destination_day_failure(intent,'substack',{'dispatch_id':ids['dispatch_id'],'safe_error_classification':'KeyError'})
    store.register_outbox_message(message_id='issued',work_item_id=packet['page_id'],destination='internal:native-neo-tool',
        payload=json.dumps({'request':{'action':'PUBLISH'}}),status='NATIVE_NEO_TOOL_PENDING')
    with pytest.raises(ValueError,match='NATIVE_WRITE_REQUEST_EXISTS'):
        c.resolve_local_neo_prewrite_failure('substack')


def test_structured_summaries_respect_limits_keep_link_and_filter(source,tmp_path):
    packet=rendered(source,tmp_path)
    url='https://capitalchronicle.substack.com/p/full-original-plan-analysis'
    for destination,limit in [('telegram',4096),('discord',2000),('threads',500),('facebook_page',60000),('instagram_business',2200)]:
        text=pages.structured_summary(packet,destination,url)
        assert len(text)<=limit and url in text
        assert 'Macro' in text and 'Scenarios' in text and 'Desk review' in text
