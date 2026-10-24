"""Curate observed public captures into the existing retained-research seam. No network."""
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from live_contentops.browser_rendered_source_recovery_v1 import _canonical_rendered_text
from live_contentops.contentops_source_research_v1 import RetainedSourceResearch

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
OBS = json.loads((ROOT / 'observed-public-sources.json').read_bytes())
ED = ROOT / 'source-editions'
ED.mkdir(exist_ok=True)
H = lambda raw: hashlib.sha256(raw).hexdigest()


def save(name, value):
    path = ED / name
    raw = (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()
    if path.exists() and path.read_bytes() != raw:
        raise ValueError('IMMUTABLE_CAPTURE_EXISTS:' + str(path))
    path.write_bytes(raw)
    return H(raw)


profile_path = REPO / 'config/native_desktop_operator_profile_v1.json'
profile = json.loads(profile_path.read_bytes())
pointer = json.loads(Path(profile['feed_pointer_path']).read_bytes())
prior_root = Path(pointer['research_root'])
prior_index = json.loads((prior_root / 'index.json').read_bytes())
fed_spec = next(s for s in prior_index['records'] if s['headline_id'] == 'goal21-fed-policy')
for source, target in ((prior_root / fed_spec['policy_capture_path'], ED / 'fed-permission.json'),
                       (REPO / 'docs/automation/CONTENTOPS_LATEST_REPORT_BRIDGE_V1_20261018/goal35/source_editions/facts-policy.json', ED / 'facts-policy.json')):
    if target.exists() and target.read_bytes() != source.read_bytes():
        raise ValueError('PERMISSION_HISTORY_CONFLICT')
    shutil.copyfile(source, target)

records = []
f = OBS['fed_implementation']
text = _canonical_rendered_text(f['text'])
capture = {'status':'PASS', 'final_url':f['url'], 'retrieval_method':'READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE',
    'content_truncated':False, 'rendered_markdown':f['text'], 'rendered_page_sha256':H(f['text'].encode()),
    'canonical_content_text':text, 'canonical_content_sha256':H(text.encode()),
    'retrieved_at_utc':f['observed'], 'credential_or_session_material_read':False, 'public_write_performed':False}
save('fed-implementation-capture.json', capture)
doc = {'document_id':'prelive-fed-implementation-20260916', 'title':f['title'], 'source_url':f['url'],
    'publisher':'www.federalreserve.gov', 'source_identity':'www.federalreserve.gov', 'raw_sha256':capture['rendered_page_sha256'],
    'canonical_content_text':text, 'canonical_content_sha256':capture['canonical_content_sha256'],
    'source_adapter_family':'official_policy', 'source_authority_class':'official_public_primary_source',
    'published_at_utc':'2026-09-16T00:00:00Z', 'published_at_precision':'DATE_ONLY',
    'published_at_source':'September 16, 2026', 'source_modified_at_utc':None, 'content_truncated':False,
    'retrieval_method':capture['retrieval_method']}
save('fed-implementation-admission.json', {'status':'PASS','official_source_documents':[doc],
    'provenance':{'retrieved_at_utc':f['observed'], 'loader':'EXACT_OBSERVED_NEO_RENDERED_TEXT'}})
prop = 'The Board of Governors of the Federal Reserve System voted unanimously to raise the interest rate paid on reserve balances to 3.90 percent, effective September 17, 2026.'
start = text.index(prop)
records.append({'headline_id':doc['document_id'], 'headline_text':prop,
    'capture_path':'fed-implementation-capture.json', 'capture_class':capture['retrieval_method'],
    'source_capture_sha256':doc['raw_sha256'], 'loader_result_path':'fed-implementation-admission.json',
    'policy_capture_path':'fed-permission.json', 'policy_capture_class':fed_spec['policy_capture_class'],
    'policy_url':fed_spec['policy_url'], 'policy_capture_sha256':H((ED/'fed-permission.json').read_bytes()),
    'policy_retrieved_at_utc':fed_spec['policy_retrieved_at_utc'], 'revision_at_utc':f['observed'],
    'proposition_span':[start,start+len(prop)], 'context_spans':[[text.index('"Effective September 17'),text.index('This information will be updated')]],
    'supporting_headline_ids':['goal21-fed-policy'], 'candidate_catalyst_tags':['rates','policy'],
    'research_metadata':{'family':'FX_RATES','assets':['US_RATES','BANK_RESERVES'],
        'context_kind':'DATED_OFFICIAL_POLICY_IMPLEMENTATION_EXPLAINER_NOT_CURRENT_DECISION',
        'period_relation':'MATERIAL_NEW_SOURCE_PROPOSITION','observation_date':'2026-09-17','release_date':'2026-09-16',
        'next_editorial_question':'How do the announced reserve, repo and reverse-repo rates implement the dated policy decision?',
        'authorship_scope':'AGENCY_AUTHORED_TEXT_ONLY_NO_LOGO_OR_PHOTO_PERMISSION'}})

g = OBS['gold_bounded_observation']
cap = {k:g[k] for k in ('url','title','observed_at_utc','full_text_sha256','full_text_characters','excerpts')}
cap.update(status='PASS',reporting_publisher='Reuters',attribution_text='By Reuters; syndicated by Kitco',
    retrieval_method='READ_ONLY_BROWSEROS_NEO_BOUNDED_EXTRACTS',credential_or_session_material_read=False,
    public_write_performed=False,capture_scope='EXACT_SELECTED_FACTUAL_PASSAGES_NOT_FULL_ARTICLE',
    publication_visible_clock={'text':'02:17, site display time zone unspecified'},
    publisher_machine_clock_metadata=[x for x in g['public_clock_metadata'] if x['name'] in ('article:published_time','article:modified_time')])
cap_sha = save('gold-report-capture.json', cap)
canonical = '\n\n'.join(e['text'] for e in cap['excerpts'])
doc = {'document_id':'prelive-gold-20261023','title':g['title'],'source_url':g['url'],'publisher':'Reuters',
    'source_identity':'reuters.com','raw_sha256':cap_sha,'canonical_content_text':canonical,
    'canonical_content_sha256':H(canonical.encode()), 'source_adapter_family':'reputable_secondary_report',
    'source_authority_class':'reputable_secondary_source','report_truth_only':True,
    'published_at_utc':'2026-10-23T19:17:01Z','published_at_source':'2026-10-23T15:17:01-04:00',
    'published_at_precision':'PUBLISHER_MACHINE_TIMESTAMP', 'source_modified_at_utc':'2026-10-23T19:18:51Z',
    'content_truncated':False,'retrieval_method':cap['retrieval_method']}
save('gold-report-admission.json', {'status':'PASS','official_source_documents':[doc],
    'provenance':{'retrieved_at_utc':g['observed_at_utc'],'loader':'EXACT_OBSERVED_NEO_BOUNDED_REPORT_FACTS'}})
records.append({'authorship_class':'REPUTABLE_REPORT_FACTS_ONLY','headline_id':doc['document_id'],
    'headline_text':g['title'],'capture_path':'gold-report-capture.json','source_capture_sha256':cap_sha,
    'loader_result_path':'gold-report-admission.json','policy_url':'https://www.copyright.gov/help/faq/faq-protect.html',
    'policy_capture_path':'facts-policy.json','policy_capture_sha256':H((ED/'facts-policy.json').read_bytes()),
    'policy_retrieved_at_utc':'2026-10-21T21:02:03.468Z','revision_at_utc':g['observed_at_utc'],
    'public_expression_reuse_allowed':False,'proposition_span':[0,len(g['title'])], 'candidate_catalyst_tags':['gold','metals','rates'],
    'research_metadata':{'family':'METALS','assets':['XAUUSD','XAGUSD','PLATINUM','PALLADIUM'],
        'context_kind':'CURRENT_ATTRIBUTED_REUTERS_REPORT_NOT_UNIVERSAL_EVENT_CONFIRMATION',
        'period_relation':'MATERIAL_NEW_SOURCE_PROPOSITION','observation_date':'2026-10-23','release_date':'2026-10-23',
        'observation_time_utc':'2026-10-23T15:20:00Z','source_modified_at_utc':'2026-10-23T19:18:51Z',
        'next_editorial_question':'Why does a reported gold selloff alongside other precious metals challenge a simple safe-haven narrative?',
        'origin_reporting_identity':'Reuters','syndication_is_not_independent_confirmation':True}})
save('index.json',{'schema_version':'contentops.retained_source_research.v1','records':records})
verified=RetainedSourceResearch(ED)
if verified.gaps or len(verified.records)!=2:
    raise ValueError(str(verified.gaps))
relative=ED.relative_to(REPO).as_posix()
if relative not in profile['research_editions_root']:
    profile['research_editions_root'].append(relative)
    profile_path.write_text(json.dumps(profile,indent=2)+'\n',encoding='utf-8')
(ROOT/'source-admission-result.json').write_text(json.dumps({'record_count':len(verified.records),'gaps':verified.gaps,
    'research_revision':verified.revision,'record_ids':list(verified.records),'production_store_write':False},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'admitted':list(verified.records),'gaps':verified.gaps,'profile_appended':relative}))
