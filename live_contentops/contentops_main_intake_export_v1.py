"""Deterministic export owned by the existing intake tick, never a service/timer."""
from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from live_contentops.capital_chronicle_latest_report_consumer_v1 import LatestReportDeliveryTracker, canonical_bytes, sha256_of
from live_contentops.contentops_main_headline_projection_v1 import DESTINATION, MainHeadlineExporter, permitted_report_headlines
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch, XListPrivateMainPermission
from live_contentops.headline_data_root_v1 import canonical_headline_sidecar_dir

REPO_ROOT = Path(__file__).resolve().parents[1]
STABLE_EXPORT_ROOT = Path('A:/Capital Chronicle/Runtime/ContentOps/daily_app_outputs/main-headline-projection')


def _atomic(path, raw):
    temporary = path.with_name(path.name + '.' + uuid4().hex + '.tmp')
    temporary.write_bytes(raw)
    os.replace(temporary, path)


def export_after_intake(store, *, cutoff_utc, intake_identity, paths=None, research=None,
                        output_root=None, max_pages=32, page_rows=500, additional_gaps=(), intake_observation=None,
                        private_profile=None):
    """Advance durable cursors beyond one page and publish one governed read model.

    Repeated calls for the same completed intake reuse the existing pages. A
    bounded backlog remains explicit and continues on the next intake; no oldest
    page reset, extra acquisition, model execution or public write occurs.
    """
    if not 1 <= max_pages <= 32 or not 1 <= page_rows <= 1000:
        raise ValueError('INTAKE_EXPORT_BOUND_INVALID')
    source_paths = sorted(canonical_headline_sidecar_dir().glob('step1_headline_sidecar_*.jsonl'))[-4:] if paths is None else paths
    inventory = None
    if private_profile:
        prior_pages = [json.loads(row['payload']) for row in store.list_outbox_messages()
            if row['destination'] == DESTINATION]
        last_profile = max((p for p in prior_pages if p.get('cursor_namespace') == 'continuous-intake'
            and p.get('private_source_profile_revision') == private_profile.revision),
            key=lambda p:p['sequence'], default={})
        family_paths = list(canonical_headline_sidecar_dir().glob('step1_headline_sidecar_*.jsonl')) if paths is None else paths
        source_paths = private_profile.covered_paths(family_paths,
            previous_inventory=last_profile.get('source_profile_inventory'))
        inventory = private_profile.inventory
    root = Path(output_root or STABLE_EXPORT_ROOT)
    exporter = MainHeadlineExporter(store, research=research, private_profile=private_profile)
    permitted = permitted_report_headlines(LatestReportDeliveryTracker(store))
    pages, previous_progress = [], None
    for ordinal in range(max_pages):
        page = exporter.export(batch_id='intake-' + sha256_of([intake_identity, ordinal]),
            paths=source_paths, cutoff_utc=cutoff_utc, max_rows=page_rows, max_files=16,
            permitted_rows=permitted, authority_revision='intake-record-permissions-v1', additional_gaps=additional_gaps,
            cursor_namespace='continuous-intake', source_profile_inventory=inventory)
        pages.append(page)
        progress = {k:v.get('offset') for k,v in page['cursors'].items()}
        if not page.get('continuation_required') or progress == previous_progress:
            break
        previous_progress = progress
    # Existing durable export pages retain lineage. This is their cumulative
    # read model, not another ledger or a new observation of old source facts.
    latest = {}
    saved_pages = [json.loads(row['payload']) for row in store.list_outbox_messages() if row['destination'] == DESTINATION]
    for saved in sorted(saved_pages, key=lambda value:value['sequence']):
        if saved.get('authority_revision') != pages[-1]['authority_revision']:
            continue
        for item in saved['rows']:
            prior = latest.get(item['headline_id'])
            if prior is None or item['revision_at_utc'] >= prior['revision_at_utc']:
                latest[item['headline_id']] = item
        for headline_id in saved.get('excluded_headline_ids', []):
            latest.pop(headline_id, None)
    gaps = {sha256_of(g):g for page in pages for g in page['gaps']}
    view = {**pages[-1], 'projection_kind':'GOVERNED_CUMULATIVE_READ_MODEL',
        'source_page_sha256':pages[-1]['page_sha256'], 'observed_at_utc':cutoff_utc,
        'rows':list(latest.values()), 'eligible_rows':len(latest),
        'new_eligible_rows':sum(p['eligible_rows'] for p in pages),
        'independent_items':sum(r['originality']=='INDEPENDENT_CONTENTOPS_ACQUISITION' for r in latest.values()),
        'main_origin_recirculated_items':sum(r['originality']=='MAIN_ORIGIN_RECIRCULATION' for r in latest.values()),
        'change_dispositions':[d for p in pages for d in p['change_dispositions']],
        'new_independent_observations':sum(p['new_independent_observations'] for p in pages),
        'representation_supersessions':sum(p['representation_supersessions'] for p in pages),
        'source_rows_scanned':sum(p['source_rows_scanned'] for p in pages),
        'gaps':list(gaps.values()), 'missing_rows':len(gaps),
        'continuation_pages':[{'sequence':p['sequence'],'page_sha256':p['page_sha256']} for p in pages],
        'intake_identity':intake_identity, 'public_write_performed':False, 'model_calls':0,
        'intake_observation':intake_observation,
        'private_source_profile_revision':private_profile.revision if private_profile else None,
        'private_source_profile_grant':private_profile.GRANT_ID if private_profile else None,
        'source_requests':0, 'existing_source_clocks_preserved':True}
    view.pop('page_sha256', None)
    view['page_sha256'] = sha256_of(view)
    root.mkdir(parents=True, exist_ok=True)
    _atomic(root/'main_headline_rows.jsonl', b''.join(canonical_bytes(row)+b'\n' for row in view['rows']))
    _atomic(root/'main_headline_projection.json', canonical_bytes(view))
    x_count = sum(r['source_platform'] == 'x_cdp_list_latest_tweets_timeline' for r in view['rows'])
    return {'state':'EXPORTED_WITH_BACKLOG' if view['continuation_required'] else 'EXPORTED',
        'projection_path':str(root/'main_headline_projection.json'),
        'rows_path':str(root/'main_headline_rows.jsonl'), 'eligible_rows':view['eligible_rows'],
        'new_eligible_rows':view['new_eligible_rows'], 'source_rows_scanned':view['source_rows_scanned'],
        'missing_rows':view['missing_rows'], 'pages':len(pages), 'continuation_required':view['continuation_required'],
        'private_grant_id':private_profile.GRANT_ID if private_profile else None,
        'x_rows':x_count, 'retained_context_rows':len(view['rows'])-x_count,
        'gap_causes':{state:sum(g['state']==state for g in view['gaps']) for state in {g['state'] for g in view['gaps']}},
        'page_sha256':view['page_sha256'], 'public_write_performed':False, 'source_requests':0, 'model_calls':0}


def configured_intake_export(store, *, cutoff_utc, intake_identity, intake_observation=None):
    """Use the existing retained research roots without Main/DB reads or execution."""
    rollout = json.loads((REPO_ROOT/'config/native_desktop_rollout_v1.json').read_bytes())
    if Path(store.db_path).resolve() != Path(rollout['store_path']).resolve():
        return {'state':'NOT_CONFIGURED_PRODUCTION_STORE','public_write_performed':False}
    gaps = []
    try:
        profile = json.loads((REPO_ROOT/'config/native_desktop_operator_profile_v1.json').read_bytes())
        pointer = json.loads(Path(profile['feed_pointer_path']).read_bytes())
        editions = [Path(p) if Path(p).is_absolute() else REPO_ROOT/p for p in profile.get('research_editions_root', [])]
        research = RetainedSourceResearch(pointer['research_root'], editions_root=editions)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        research = None
        gaps.append({'state':'RESEARCH_PERMISSION_INDEX_UNAVAILABLE','error_type':type(exc).__name__})
    try:
        private_profile = XListPrivateMainPermission()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        private_profile = None
        gaps.append({'state':'PRIVATE_MAIN_GRANT_UNAVAILABLE','error_type':type(exc).__name__})
    return export_after_intake(store, cutoff_utc=cutoff_utc, intake_identity=intake_identity, research=research,
        additional_gaps=gaps, intake_observation=intake_observation, private_profile=private_profile)
