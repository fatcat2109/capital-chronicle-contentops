"""Controlled permission fixtures prove mechanics, never real rights or live cadence."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from live_contentops.contentops_main_headline_projection_v1 import MainHeadlineExporter, project_headline
from live_contentops.contentops_main_intake_export_v1 import configured_intake_export, export_after_intake
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

NOW = '2026-10-29T06:00:00Z'


def controlled_records(count):
    research = RetainedSourceResearch.__new__(RetainedSourceResearch)
    research.records, research.gaps, research.revision = {}, [], 'CONTROLLED_NOT_REAL_RIGHTS_PROOF'
    rows = []
    for index in range(count):
        text = f'Controlled attributed context {index}'
        digest = hashlib.sha256(text.encode()).hexdigest()
        capture = hashlib.sha256(f'controlled capture {index}'.encode()).hexdigest()
        row = {'headline_id':f'row-{index}', 'headline_text':text, 'text_sha256':digest,
            'source_platform':'x_cdp_list_latest_tweets_timeline', 'author_handle':'FixtureAccount',
            'tweet_id':str(index+100000), 'tweet_url':f'https://x.com/FixtureAccount/status/{index+100000}',
            'raw_payload_sha256':capture, 'headline_timestamp':'2026-10-29T05:00:00Z',
            'captured_at_utc':'2026-10-29T05:01:00Z'}
        research.records[f'permission-{index}'] = {'headline_id':f'permission-{index}',
            'headline_text':text, 'source_identity':'FixtureAccount', 'source_url':row['tweet_url'],
            'source_capture_sha256':capture, 'rights_evidence_sha256':'a'*64,
            'revision_at_utc':'2026-10-29T05:01:00Z', 'source_permissions':{'content_sha256':digest,
                'INTERNAL_ANALYSIS_ALLOWED':True, 'MODEL_INPUT_ALLOWED':True, 'LLM_INPUT_ALLOWED':True,
                'provider_safe':True, 'permitted_consumers':['narrative_context'],
                'public_expression_reuse_allowed':False}}
        rows.append(row)
    return research, rows


def test_exact_x_inheritance_preserves_internal_scope_and_rejects_lookalikes(tmp_path):
    research, rows = controlled_records(1)
    exporter = MainHeadlineExporter(ContentOpsDurableStore(tmp_path/'state.sqlite3'), research=research)
    projected, reason = project_headline(rows[0], cutoff_utc=NOW, locator={}, permission_resolver=exporter.permission_for)
    assert reason is None and projected['allowed_consumers'] == ['narrative_context']
    assert projected['source_identity'] == 'FixtureAccount'
    assert projected['source_capture_sha256'] == rows[0]['raw_payload_sha256']
    assert not projected['public_republication_authority'] and not projected['numeric_authority_granted']
    local = {**rows[0], 'headline_timestamp':'2026-10-29 12:00:00 GMT+7'}
    converted, reason = project_headline(local, cutoff_utc=NOW, locator={}, permission_resolver=exporter.permission_for)
    assert reason is None and converted['headline_timestamp'] == '2026-10-29T05:00:00Z'
    assert converted['published_at_source'] == local['headline_timestamp']
    for mutation in ({'headline_text':'Unbound text'}, {'raw_payload_sha256':'b'*64},
                     {'author_handle':'DifferentAccount'}, {'tweet_id':'987654'},
                     {'tweet_url':'https://x.com/DifferentAccount/status/100000'}):
        altered = {**rows[0], **mutation}
        assert project_headline(altered, cutoff_utc=NOW, locator={}, permission_resolver=exporter.permission_for)[0] is None
    research.records['permission-0']['source_permissions']['permitted_consumers'] = ['catalyst_detection']
    assert exporter.permission_for(rows[0], NOW) is None
    fake = {**rows[0], 'source_permissions':{'provider_safe':True,'permitted_consumers':['internal_research']}}
    assert MainHeadlineExporter(exporter.store).permission_for(fake, NOW) is None


def test_continuation_past_500_survives_restart_and_appends_without_duplicates(tmp_path):
    research, rows = controlled_records(620)
    path = tmp_path/'sidecar.jsonl'
    path.write_text(''.join(json.dumps(row)+'\n' for row in rows[:610]), encoding='utf-8')
    store = ContentOpsDurableStore(tmp_path/'state.sqlite3')
    target = tmp_path/'governed'
    first = export_after_intake(store, cutoff_utc=NOW, intake_identity='capture-1',
        paths=[path], research=research, output_root=target, max_pages=1)
    assert first['source_rows_scanned'] == first['eligible_rows'] == 500 and first['continuation_required']
    # An ordinary editorial export cannot reset the intake cursor to its oldest page.
    MainHeadlineExporter(store, research=research).export(batch_id='editorial-interleaved', paths=[path],
        cutoff_utc=NOW, max_rows=1)
    second = export_after_intake(ContentOpsDurableStore(tmp_path/'state.sqlite3'), cutoff_utc=NOW,
        intake_identity='capture-2', paths=[path], research=research, output_root=target)
    assert second['source_rows_scanned'] == second['new_eligible_rows'] == 110
    assert second['eligible_rows'] == 610 and not second['continuation_required']
    snapshot = json.loads((target/'main_headline_projection.json').read_bytes())
    assert len({row['headline_id'] for row in snapshot['rows']}) == 610
    assert all(row['known_at_utc'] == '2026-10-29T05:01:00Z' for row in snapshot['rows'])
    with path.open('a', encoding='utf-8') as stream:
        stream.write(''.join(json.dumps(row)+'\n' for row in rows[610:]))
    third = export_after_intake(store, cutoff_utc=NOW, intake_identity='capture-3',
        paths=[path], research=research, output_root=target)
    assert third['source_rows_scanned'] == third['new_eligible_rows'] == 10 and third['eligible_rows'] == 620
    duplicate = export_after_intake(store, cutoff_utc=NOW, intake_identity='capture-3',
        paths=[path], research=research, output_root=target)
    assert duplicate == third
    idle = export_after_intake(store, cutoff_utc=NOW, intake_identity='capture-4',
        paths=[path], research=research, output_root=target)
    assert idle['source_rows_scanned'] == idle['new_eligible_rows'] == 0 and idle['eligible_rows'] == 620


def test_normal_full_continuation_and_unknown_rights_keep_hash_only_gaps(tmp_path):
    research, rows = controlled_records(610)
    unknown = {**rows[0], 'headline_id':'unknown', 'headline_text':'RESTRICTED_NEVER_EXPORTED',
        'author_handle':'Unknown', 'tweet_url':'https://x.com/Unknown/status/100000'}
    path = tmp_path/'sidecar.jsonl'
    path.write_text(''.join(json.dumps(row)+'\n' for row in [unknown, *rows]), encoding='utf-8')
    store = ContentOpsDurableStore(tmp_path/'state.sqlite3')
    result = export_after_intake(store, cutoff_utc=NOW, intake_identity='capture', paths=[path],
        research=research, output_root=tmp_path/'governed')
    assert result['pages'] == 2 and result['source_rows_scanned'] == 611 and result['eligible_rows'] == 610
    value = json.loads(Path(result['projection_path']).read_bytes())
    assert 'RESTRICTED_NEVER_EXPORTED' not in json.dumps(value)
    assert value['gaps'][0]['state'] == 'SOURCE_RIGHTS_MISSING_NO_GOVERNED_INHERITANCE'
    assert value['source_requests'] == value['model_calls'] == 0 and not value['public_write_performed']


def test_controlled_store_cannot_write_the_production_projection(tmp_path):
    result = configured_intake_export(ContentOpsDurableStore(tmp_path/'state.sqlite3'),
        cutoff_utc=NOW, intake_identity='controlled-not-production')
    assert result['state'] == 'NOT_CONFIGURED_PRODUCTION_STORE'


def test_changed_permission_index_revalidates_rows_and_drops_revoked_permissions(tmp_path):
    research, rows = controlled_records(2)
    source = tmp_path/'rows.jsonl'
    source.write_text(''.join(json.dumps(row)+'\n' for row in rows), encoding='utf-8')
    store = ContentOpsDurableStore(tmp_path/'state.sqlite3')
    options = {'paths':[source], 'research':research, 'output_root':tmp_path/'governed'}
    first = export_after_intake(store, cutoff_utc=NOW, intake_identity='original', **options)
    assert first['eligible_rows'] == 2
    research.records.pop('permission-1')
    research.revision = 'CONTROLLED_PERMISSION_REVOCATION_NOT_REAL_RIGHTS_PROOF'
    revised = export_after_intake(store, cutoff_utc=NOW, intake_identity='revised', **options)
    assert revised['eligible_rows'] == 1
    view = json.loads(Path(revised['projection_path']).read_bytes())
    assert [row['headline_id'] for row in view['rows']] == ['row-0']
    assert sum(gap['state'] == 'SOURCE_RIGHTS_MISSING_NO_GOVERNED_INHERITANCE' for gap in view['gaps']) == 1


def test_successful_capture_exports_once_after_capture_and_not_on_not_due(tmp_path, monkeypatch):
    from live_contentops.continuous_headline_ingest_v1 import run_ingestion_housekeeping_iteration
    store = ContentOpsDurableStore(tmp_path/'state.sqlite3')
    control = store.get_operating_control()
    store.update_operating_control(operating_mode='AUTONOMOUS_DEFAULT', expected_state_version=control['state_version'],
        control_source='CONTROLLED_TEST')
    order = []
    def capture(**_kwargs):
        order.append('capture')
        return {'capture_state':'CAPTURED_NO_NEW_HEADLINES','new_headlines':0}
    def exported(*_args, **_kwargs):
        order.append('export')
        return {'state':'CONTROLLED_EXPORTED'}
    kwargs = {'state_fn':lambda:{'state':'READY'}, 'ensure_fn':lambda:{'chrome_9222_ingestion':'READY'},
        'session_fn':lambda:{'session_state':'AUTHENTICATED'}, 'capture_fn':capture, 'export_fn':exported}
    result = run_ingestion_housekeeping_iteration(store, now=datetime(2026,10,29,6,tzinfo=timezone.utc), **kwargs)
    assert order == ['capture','export'] and result['main_headline_projection']['state'] == 'CONTROLLED_EXPORTED'
    run_ingestion_housekeeping_iteration(store, now=datetime(2026,10,29,6,1,tzinfo=timezone.utc), **kwargs)
    assert order == ['capture','export']


def test_due_failed_capture_can_export_existing_local_evidence_with_failure_visible(tmp_path):
    from live_contentops.continuous_headline_ingest_v1 import run_ingestion_housekeeping_iteration
    store = ContentOpsDurableStore(tmp_path/'state.sqlite3')
    control = store.get_operating_control()
    store.update_operating_control(operating_mode='AUTONOMOUS_DEFAULT', expected_state_version=control['state_version'],
        control_source='CONTROLLED_TEST')
    observations = []
    def exported(*_args, **kwargs):
        observations.append(kwargs['intake_observation'])
        return {'state':'CONTROLLED_EXISTING_LOCAL_ROWS_ONLY'}
    value = run_ingestion_housekeeping_iteration(store, now=datetime(2026,10,29,6,tzinfo=timezone.utc),
        state_fn=lambda:{'state':'READY'}, ensure_fn=lambda:{'chrome_9222_ingestion':'READY'},
        session_fn=lambda:{'session_state':'READY'}, export_fn=exported,
        capture_fn=lambda **_kwargs:{'capture_state':'CAPTURE_FAILED','new_headlines':0,
            'failure_class':'MALFORMED_EMPTY_CAPTURE_RESPONSE'})
    assert len(observations) == 1 and observations[0]['new_rows_captured'] == 0
    assert observations[0]['capture_state'] == 'CAPTURE_FAILED'
    assert observations[0]['failure_class'] == 'MALFORMED_EMPTY_CAPTURE_RESPONSE'
    assert value['lane_state'] == 'DEGRADED'
