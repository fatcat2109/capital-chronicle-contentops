"""Record actual parent acceptance after rendered inspection, then prepare without dispatch."""
import json
import shutil
from pathlib import Path
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.contentops_editorial_desk_v1 import read_reviews,record_native_article_review
from live_contentops.native_desktop_editorial_v1 import validate_release_media,prepare_reviewed_handoff
from live_contentops.native_desktop_publication_v1 import prepare_native_publication,NativeReviewedPublication
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of

ROOT=Path(__file__).resolve().parent
visual=json.loads((ROOT/'renders/final/visual-review.json').read_bytes())
if not visual['all_final_sheets_actually_inspected'] or visual['total_views']!=72:raise ValueError('ACTUAL_FINAL_VISUAL_ACCEPTANCE_REQUIRED')
rationales={
 'policy':'KEEP: useful dated September16/17 policy/document explanation with3announced settings, distinct source documents and operational roles, conditional transmission/countercase/watchpoint. Exact authentic KevinWarsh May22person/archive/PD-USGov photo and3.90/4.0/3.75percent chart inspected. Canonical and8packages desktop/mobile inspected; date-onlysource, links, captions, uncertainty, legibility and enlargement checked. Settings do not establish realized rates or asset moves; same Fed origin not independent confirmations. No publication authority.',
 'gold':'KEEP: genuinely October23 single-Reuters-origin report via Kitco, gold15:20observation/publication/update/capture distinct. Mechanism and alternatives remain attributed/conditional, no causal proof or synchronized4metalclock. Exact archive2022CCBY4gold photo and reported signed -0.6/-1/-0.5/-0.9percent chart inspected. Canonical/eight appropriate previews at desktop/mobile retain source date, uncertainty, pending link and owned chart; exact public citations and captions visible. No new confirmation, probability or publication authority.',
 'tesla-r2':'KEEP: bounded source-note readability revision removes internal capture/cutoff microseconds and audit vocabulary while preserving October21facts, same prior article/story/updatechain, reported cash/capex distinction, serious operatingcash countercase and missing bridge. Exact C9photo/chart bytes reused. Canonical/eight packages desktop/mobile inspected; source links, sign/estimate/period, source date and uncertainty retained. No new factual observation, independent confirmation or publication authority.',
 'southwest-r2':'KEEP: bounded public source-note repair retains October21report, quarterly actual/estimate versus annualforecast distinction, fare/fuel/margin mechanism/countercase, missing earningsbridge and no current hedge-status assertion. Same prior article/story/updatechain; C9bytes/history intact and exact lawful photo/range chart reused. Canonical/eightpackages desktop/mobile inspected with source dates/links/captions/forecast bounds and retained report certainty. No new facts, independent confirmation or publication authority.'}
for slug,rationale in rationales.items():
    folder=ROOT/slug;b=json.loads((folder/'binding.json').read_bytes());store=ContentOpsDurableStore(b['store_path'],auto_migrate=False)
    row=store.get_outbox_message('cc-editorial-final-'+sha256_of(b['run_id']));result=json.loads(row['payload'])
    validate_release_media(result)
    if result!=json.loads((folder/'native-final-media-result.json').read_bytes()):raise ValueError('INSPECTED_PACKAGE_CHANGED')
    prior=[r for r in read_reviews(store) if r['work_item_id']==row['work_item_id'] and r['reviewer_ref']=='NATIVE_DESKTOP_ARTICLE_REVIEW']
    if prior:
        latest=prior[-1];notes=json.loads(latest['notes'])
        if latest['decision']!='KEEP' or notes['rationale']!=rationale:raise ValueError('EXACT_EXISTING_REVIEW_REQUIRED')
        review={'review_id':latest['review_id'],'decision':latest['decision'],**notes}
    else:review=record_native_article_review(store,run_id=b['run_id'],article_identity=result['article_identity'],decision='KEEP',rationale=rationale,expected_review_id=None)
    (folder/'review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
    handoff=prepare_reviewed_handoff(store,run_id=b['run_id'],output_dir=b['output_dir'])
    (folder/'reviewed-handoff.json').write_text(json.dumps(handoff,indent=2)+'\n',encoding='utf-8')
    prepared=prepare_native_publication(store,b)
    status=NativeReviewedPublication(store,b,native_invocation_id=None).projection()
    (folder/'publication-prepared.json').write_text(json.dumps(prepared,indent=2)+'\n',encoding='utf-8')
    (folder/'publication-status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    target=folder/'reviewed-handoff';target.mkdir(exist_ok=True)
    for name in ('article_manifest_v1.json','qualified_article_record_v1.json','native_derivative_previews_v1.json','publication_lifecycle_plan_v1.json','run_context_v1.json'):
        shutil.copyfile(Path(b['output_dir'])/'reviewed-handoff'/name,target/name)
    print(json.dumps({'slug':slug,'article_identity':result['article_identity'],'review':review['review_id'],'prepared':prepared.get('classification'),'state':status.get('state')}),flush=True)
