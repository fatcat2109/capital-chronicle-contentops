"""Controlled owner/lineage controls; no model, browser or production-store calls."""
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from live_contentops.contentops_editorial_desk_v1 import native_story_projection, record_story_source_review
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from tests.test_native_newsroom_owner_operation_v1 import entry


def native(store, run, identity, *, chain='original-chain'):
    value = {'qualified_article_count': 1, 'model_execution_state': 'NATIVE_DESKTOP_REQUEST_RETURN',
        'article_identity': identity, 'article': {'title': 'Controlled dated view', 'dek': 'Controlled only.',
            'substack_body_markdown': 'Prior dated fact.', 'story_identity': 'new-candidate', 'update_chain_identity': chain},
        'simple_result': {'run_id': run, 'cutoff_utc': '2026-10-21T00:00:00Z',
            'publication_lifecycle_plan': {'plan_hash': 'controlled-plan'}}, 'evidence': []}
    work = 'cc-opportunity-' + sha256_of(run)
    store.create_work_item(story_id=work, work_item_id=work, title='Controlled story', target_surface='CONTENTOPS_EDITORIAL_ONLY')
    store.register_outbox_message(message_id='cc-editorial-final-' + sha256_of(run), work_item_id=work,
        destination='internal:cc-report-simple-result', payload=canonical_bytes(value).decode(), status='EDITORIAL_INTERNAL')
    return value


def review_args(store):
    native(store, 'original', 'a' * 64)
    base = Path(__file__).resolve().parents[1] / 'docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018'
    research = RetainedSourceResearch(base / 'goal23/retained_research', editions_root=base / 'goal27/source_editions')
    return dict(run_id='original', article_identity='a' * 64, review_operation_id='controlled-check', research=research,
        source_ids=['goal27-gas-seasonal'], attempts=[dict(url='https://www.eia.gov/naturalgas/weekly/supplement/', status='PASS')],
        cutoff_utc='2026-10-23T00:00:00Z', reason='Controlled comparison of an exact retained seasonal proposition.')


def test_followup_review_keeps_original_chain_and_partial_gap_is_explicit(tmp_path):
    store = ContentOpsDurableStore(tmp_path / 'state.sqlite3'); args = review_args(store)
    args['attempts'].append(dict(url='https://www.eia.gov/controlled-missing', status='UNAVAILABLE'))
    result = record_story_source_review(store, **args)
    assert result['decision'] == 'MATERIAL_FOLLOW_UP'
    assert result['source_coverage_complete'] is False
    assert result['prior_story']['story_identity'] == 'original-chain'
    count = len(store.list_outbox_messages())
    assert record_story_source_review(store, **args) == result
    assert len(store.list_outbox_messages()) == count


def test_publisher_correction_is_not_silently_classified_as_an_ordinary_update(tmp_path):
    store = ContentOpsDurableStore(tmp_path / 'state.sqlite3'); args = review_args(store)
    records = copy.deepcopy(args['research'].records)
    records['goal27-gas-seasonal']['research_metadata']['period_relation'] = 'PUBLISHER_CORRECTION_OF_SAME_OBSERVATION'
    # Controlled classification input only; no admission or claim of a real correction.
    args['research'] = SimpleNamespace(records=records, revision='CONTROLLED_CORRECTION')
    result = record_story_source_review(store, **args)
    assert result['decision'] == 'CORRECTION_OR_WITHDRAWAL'
    assert result['writer_required'] and result['invalidates_prepared_review']


@pytest.mark.parametrize('decision', ['USE_UNCHANGED', 'STALE_OR_SOURCE_GAP'])
def test_owner_entry_reuses_or_holds_without_binding_source_or_model_work(tmp_path, monkeypatch, decision):
    module = entry(); store = ContentOpsDurableStore(tmp_path / 'state.sqlite3')
    args = review_args(store); args.update(source_ids=[], attempts=[dict(url='https://www.eia.gov/controlled',
        status='PASS' if decision == 'USE_UNCHANGED' else 'UNAVAILABLE')])
    review = record_story_source_review(store, **args)
    assert review['decision'] == decision
    profile = dict(store_path=str(tmp_path / 'state.sqlite3'), editorial_output_root=str(tmp_path / 'out'))
    monkeypatch.setattr(module, 'operation', lambda *_a, **_k: pytest.fail('No editorial/model work allowed'))
    before = store.list_outbox_messages()
    first = module.continue_owner_story(profile, source_review_id=review['review_id'])
    assert module.continue_owner_story(profile, source_review_id=review['review_id']) == first
    assert first['model_invocations'] == first['source_requests'] == 0
    assert store.list_outbox_messages() == before
    assert not (tmp_path / 'out').exists()


def test_changed_owner_entry_resumes_one_frozen_operation_after_interruption(tmp_path, monkeypatch):
    module = entry(); store = ContentOpsDurableStore(tmp_path / 'state.sqlite3');args = review_args(store)
    review = record_story_source_review(store, **args)
    profile = dict(schema_version='contentops.native_desktop_operator_profile.v1',
        store_path=str(tmp_path / 'state.sqlite3'), editorial_output_root=str(tmp_path / 'out'),
        **{k: str(tmp_path / k) for k in ('feed_pointer_path','published_memory_store','published_memory_output_root')})
    calls = []
    def interrupted(binding):
        calls.append(binding)
        return dict(classification='CONTROLLED_PENDING_NATIVE_SELECT',run_id=binding['run_id'])
    monkeypatch.setattr(module, 'operation', interrupted)
    one = module.continue_owner_story(profile, source_review_id=review['review_id'],
        request='A custom owner question that must survive interruption unchanged.')
    path = Path(calls[0]['output_dir']) / 'binding.json'; raw = path.read_bytes()
    assert module.continue_owner_story(profile, source_review_id=review['review_id']) == one
    assert path.read_bytes() == raw and calls[0] == calls[1]
    assert calls[0]['source_review_ids'] == [review['review_id']]
    assert calls[0]['editorial_request']=='A custom owner question that must survive interruption unchanged.'
    assert len(list((tmp_path / 'out').glob('*/binding.json'))) == 1


def test_completed_followup_cannot_allocate_a_duplicate_operation(tmp_path, monkeypatch):
    module = entry(); store = ContentOpsDurableStore(tmp_path / 'state.sqlite3');args = review_args(store)
    review = record_story_source_review(store, **args)
    child = native(store, 'accepted-child', 'b' * 64)
    child['article']['source_review_id'] = review['review_id']
    store.finalize_outbox_payload_before_dispatch(message_id='cc-editorial-final-'+sha256_of('accepted-child'),
        payload=canonical_bytes(child).decode(), status='EDITORIAL_INTERNAL')
    profile = dict(store_path=str(tmp_path / 'state.sqlite3'))
    with pytest.raises(ValueError, match='ALREADY_ACCEPTED'):
        module.continue_owner_story(profile, source_review_id=review['review_id'], operation_id='duplicate')


def test_source_gap_invalidates_only_the_exact_affected_review(tmp_path):
    from live_contentops.contentops_editorial_desk_v1 import record_native_article_review
    from live_contentops.native_desktop_editorial_v1 import validated_native_review
    store = ContentOpsDurableStore(tmp_path / 'state.sqlite3'); args = review_args(store)
    native(store, 'unaffected', 'b' * 64, chain='unaffected-chain')
    for run, identity in [('original','a'*64),('unaffected','b'*64)]:
        record_native_article_review(store,run_id=run,article_identity=identity,decision='KEEP',
            rationale='Controlled exact revision review, no publication grant.')
    args.update(source_ids=[],attempts=[dict(url='https://www.eia.gov/controlled',status='UNAVAILABLE')])
    review = record_story_source_review(store, **args)
    assert review['decision']=='STALE_OR_SOURCE_GAP'
    with pytest.raises(ValueError,match='SOURCE_CHANGED_PREPARED_REVIEW_INVALIDATED'):
        validated_native_review(store,run_id='original')
    assert validated_native_review(store,run_id='unaffected')[0]['article_identity']=='b'*64


def test_followup_pool_cannot_route_an_unrelated_story(tmp_path, monkeypatch):
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker
    import live_contentops.capital_chronicle_report_editorial_workspace_v1 as workspace
    import live_contentops.v1_simple_gemini_newsroom_v1 as deterministic
    from live_contentops.native_desktop_editorial_v1 import NativeDesktopTurn
    store = ContentOpsDurableStore(tmp_path / 'state.sqlite3'); args = review_args(store)
    review = record_story_source_review(store, **args)
    class ObservedBoundPool(Exception):
        pass
    filtered_population = []
    def observe(**kwargs):
        assert [h['headline_id'] for h in kwargs['rolling_input']['headlines']]==['goal27-gas-seasonal']
        context=kwargs['rolling_input']['headlines'][0]['external_content']['evolving_story_context'][0]
        assert context['source_review_id']==review['review_id']
        assert context['update_chain_identity']=='original-chain'
        raise ObservedBoundPool()
    monkeypatch.setattr(deterministic,'run_v1_simple_gemini_newsroom',observe)
    caller=NativeDesktopTurn(store,run_id='controlled-followup',output_dir=tmp_path/'out',owner_manual_validation=True)
    (tmp_path/'out').mkdir()
    def full_population(rolling):
        filtered_population.extend(h['headline_id'] for h in rolling['headlines'])
        return rolling, {'scope':'CONTROLLED_FILTER_OBSERVATION_NOT_MODEL_EXECUTION'}
    monkeypatch.setattr(caller,'filter_headlines',full_population)
    with pytest.raises(ObservedBoundPool):
        workspace.run_report_editorial_cycle(LatestReportDeliveryTracker(store),receipt_id='independent-control',
            admission=None,output_dir=tmp_path/'out',cutoff_utc=args['cutoff_utc'],llm_invoke=caller,
            run_id='controlled-followup',opportunity_id='controlled-followup',source_reviews=[review],
            rolling_input={'headlines':[dict(headline_id='goal27-gas-seasonal',headline_text='Bound retained proposition'),
                                       dict(headline_id='unrelated',headline_text='Unrelated current story')]})
    assert set(filtered_population)=={'goal27-gas-seasonal','unrelated'}


def test_pure_completed_story_contract_orders_exact_parents_and_does_not_merge_issuer(tmp_path):
    store = ContentOpsDurableStore(tmp_path / 'state.sqlite3')
    first = native(store, 'prior', 'a' * 64)
    second = native(store, 'current', 'b' * 64);second['article']['prior_article_identity'] = 'a' * 64
    second['article']['social_mechanism_summary'] = 'A changed authored interpretation.'
    unrelated = native(store, 'same-issuer-other-question', 'c' * 64, chain='different-chain')
    # A completed projection can be delivered in reverse order without changing ancestry.
    edition = {v['article_identity']: dict(article=v['article'], article_identity=v['article_identity'],
        run_id=v['simple_result']['run_id'], review=dict(decision='KEEP'), publication=dict(state='PREPARED'),
        evidence=[dict(source_id='SOURCE_1', publisher='Controlled issuer',url='https://example.com/source',
            published_at_utc='2026-10-20T00:00:00Z')], media_assets=[],
        previews=[dict(destination='telegram',payload=dict(text='What to watch: Does the next dated release retain this change?\n\nSource date: 2026-10-20.'))])
        for v in (second, first, unrelated)}
    rows = store.list_outbox_messages(); before = copy.deepcopy((edition,rows))
    view = native_story_projection(edition,rows,observed_at_utc='2026-10-23T00:00:00Z')
    assert (edition,rows) == before
    assert len(view) == 2
    story = next(v for v in view if v['story_identity']=='original-chain')
    assert [v['run_id'] for v in story['versions']] == ['prior','current']
    assert story['current_article_identity'] == 'b'*64
    assert story['change']['interpretation_changed'] is True
    assert story['current_version']['analysis_age_seconds'] == 2*86400
    assert story['current_version']['source_dates'][0]['age_seconds'] == 3*86400
    assert story['next_observation'] == 'Does the next dated release retain this change?'
    assert all(v['publication']['state']=='PREPARED' for v in story['versions'])
    del edition['a'*64]
    missing = next(v for v in native_story_projection(edition,rows) if v['story_identity']=='original-chain')
    assert missing['lineage_gap'] is True and missing['prior_article_identity'] is None


def test_later_keep_keeps_the_original_version_fact_delta_visible(tmp_path):
    store=ContentOpsDurableStore(tmp_path/'state.sqlite3');args=review_args(store)
    original=record_story_source_review(store,**args)
    child=native(store,'child','b'*64)
    child['article'].update(prior_article_identity='a'*64,source_review_id=original['review_id'])
    work='cc-opportunity-'+sha256_of('child')
    later={**original,'review_id':'later-keep','article_identity':'b'*64,'run_id':'child',
        'decision':'USE_UNCHANGED','reader_change_summary':'Keep the dated revised view; next observation is still missing.',
        'source_changes':[],'invalidates_prepared_review':False,'writer_required':False}
    store.register_outbox_message(message_id='later-keep',work_item_id=work,destination='internal:native-story-source-review',
        payload=canonical_bytes(later).decode(),status='EDITORIAL_INTERNAL')
    edition={v['article_identity']:dict(article=v['article'],article_identity=v['article_identity'],
        run_id=v['simple_result']['run_id'],previews=[],evidence=[]) for v in (child,)}
    story=native_story_projection(edition,store.list_outbox_messages())[0]
    assert story['state']=='KEEP'
    assert story['change']['decision']=='MATERIAL_FOLLOW_UP'
    assert story['change']['source_changes']==original['source_changes']
    assert story['latest_assessment']['decision']=='USE_UNCHANGED'


def test_partial_legacy_record_is_not_a_completed_story_or_a_reader_crash():
    entry={'article_identity':'media-only','article':{},'media_assets':[{'asset_id':'controlled'}]}
    assert native_story_projection({'media-only':entry},[])==[]
    assert entry['media_assets']==[{'asset_id':'controlled'}]
