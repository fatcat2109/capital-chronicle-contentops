"""Retained written articles remain readable after recovery-key installation."""
import json

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_manual_candidate_v1 import native_artifact_key


def retained_recovery(tmp_path, result):
    store = ContentOpsDurableStore(tmp_path / 'store.sqlite3')
    run_id = 'retained-written-before-recovery-key'
    work = 'cc-opportunity-' + sha256_of(run_id)
    store.create_work_item(story_id=work, title='Retained article', target_surface='CONTENTOPS_EDITORIAL_ONLY', work_item_id=work)
    legacy = 'cc-editorial-final-' + sha256_of(run_id)
    store.register_outbox_message(message_id=legacy, work_item_id=work,
        destination='internal:cc-report-simple-result', payload=json.dumps(result), status='EDITORIAL_INTERNAL')
    store.register_outbox_message(message_id='retained-source-recovery', work_item_id=work,
        destination='internal:native-desktop-source-recovery', status='EDITORIAL_INTERNAL',
        payload=json.dumps({'pre_writer_source_recovery': True, 'request_sha256': 'accepted-recovery'}))
    return store, run_id, legacy


@pytest.mark.parametrize('result', [
    {'writer_invoked': True}, {'qualified_article_count': 1},
    {'article': {'article_identity': 'retained-approved-copy'}}, {'public_write_performed': True},
])
def test_existing_written_article_stays_available_to_retained_review_consumer(tmp_path, result):
    store, run_id, legacy = retained_recovery(tmp_path, result)
    selected = native_artifact_key(store, run_id, 'cc-editorial-final-')
    assert selected == legacy
    assert json.loads(store.get_outbox_message(selected)['payload']) == result


def test_zero_writer_failure_keeps_immutable_bytes_and_selects_recovered_result(tmp_path):
    failed = {'writer_invoked': False, 'qualified_article_count': 0, 'article': None, 'public_write_performed': False}
    store, run_id, legacy = retained_recovery(tmp_path, failed)
    recovered_key = native_artifact_key(store, run_id, 'cc-editorial-final-')
    assert recovered_key != legacy
    recovered = {'qualified_article_count': 1, 'article': {'article_identity': 'recovered-article'}}
    row = store.get_outbox_message(legacy)
    store.register_outbox_message(message_id=recovered_key, work_item_id=row['work_item_id'],
        destination='internal:cc-report-simple-result', payload=json.dumps(recovered), status='EDITORIAL_INTERNAL')
    selected = native_artifact_key(store, run_id, 'cc-editorial-final-')
    assert json.loads(store.get_outbox_message(selected)['payload']) == recovered
    assert json.loads(store.get_outbox_message(legacy)['payload']) == failed
