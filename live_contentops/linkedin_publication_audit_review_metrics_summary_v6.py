
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse
SCHEMA_VERSION='6.0.0'; SAMPLE_SCOPE='sample_fixture_only'; HASH_ALGORITHM='sha256_json_v6'
FORBIDDEN_SECRET_PATTERNS=(r'https://discord(?:app)?\\.com/api/webhooks/',r'sk-[A-Za-z0-9]',r'xox[baprs]-',r'ghp_[A-Za-z0-9]',r'bearer\\s+[A-Za-z0-9._-]{12,}',r'cookie\\s*[:=]',r'localstorage\\s*[:=]',r'sessionstorage\\s*[:=]',r'browser session data\\s*[:=]')
FORBIDDEN_ADVICE=('financial advice','trading signal','signal service','price target','target price','buy','sell','hold')
def _stable_hash(payload):
    body=payload if isinstance(payload,str) else json.dumps(payload, sort_keys=True, separators=(',',':'))
    return hashlib.sha256(body.encode('utf-8')).hexdigest()
def _walk_strings(value):
    if isinstance(value,str): return [value]
    if isinstance(value,Mapping): return [s for item in value.values() for s in _walk_strings(item)]
    if isinstance(value,list): return [s for item in value for s in _walk_strings(item)]
    return []
def _assert_safe(packet, exc):
    for text in _walk_strings(packet):
        low=text.lower()
        for pattern in FORBIDDEN_SECRET_PATTERNS:
            if re.search(pattern,text,flags=re.I): raise exc('forbidden_secret_or_session_material')
        for phrase in FORBIDDEN_ADVICE:
            if re.search(r'\\b'+re.escape(phrase)+r'\\b', low): raise exc('forbidden_financial_advice:'+phrase)
def _require_str(packet,key,exc):
    v=packet.get(key)
    if not isinstance(v,str) or not v.strip(): raise exc(f'missing_required_string:{key}')
    return v
def _require_mapping(packet,key,exc):
    v=packet.get(key)
    if not isinstance(v,Mapping): raise exc(f'missing_required_mapping:{key}')
    return v
def _require_false(packet,key,exc):
    if packet.get(key) is not False: raise exc(f'required_false:{key}')
def _require_true(packet,key,exc):
    if packet.get(key) is not True: raise exc(f'required_true:{key}')
def _eq(a,b,label,exc):
    if a!=b: raise exc(f'binding_mismatch:{label}')
def load_json(path: Path): return json.loads(path.read_text(encoding='utf-8-sig'))
def _write(path,packet):
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(packet,indent=2,sort_keys=True)+'\n',encoding='utf-8')

TASK_LABEL='TASK_CONTENTOPS_V6_LINKEDIN_MANUAL_PUBLICATION_EVIDENCE_LOOP_V0'; METRICS_SOURCE='operator_supplied_manual_entry'
class LinkedInPublicationAuditReviewMetricsSummaryError(ValueError): pass
def build_linkedin_publication_audit_review_metrics_summary_packet(url_audit_packet,*,operator_supplied_impressions=None,operator_supplied_reactions=None,operator_supplied_comments=None,operator_supplied_reposts=None,operator_supplied_clicks=None,operator_supplied_profile_views=None,operator_supplied_followers_delta=None,operator_supplied_notes=None):
    _assert_safe(url_audit_packet,LinkedInPublicationAuditReviewMetricsSummaryError); _require_true(url_audit_packet,'manual_publication_claim_operator_supplied',LinkedInPublicationAuditReviewMetricsSummaryError)
    for k in ('url_network_verified','linkedin_api_used','provider_call_made','network_call_made','credential_read_made','env_value_read_made','browser_session_used','enabled_publish_send_dispatch_approve_controls'):_require_false(url_audit_packet,k,LinkedInPublicationAuditReviewMetricsSummaryError)
    aid=_require_str(url_audit_packet,'publication_url_audit_packet_id',LinkedInPublicationAuditReviewMetricsSummaryError); ah=_require_str(url_audit_packet,'publication_url_audit_hash',LinkedInPublicationAuditReviewMetricsSummaryError); hid=_require_str(url_audit_packet,'operator_handoff_packet_id',LinkedInPublicationAuditReviewMetricsSummaryError); hh=_require_str(url_audit_packet,'operator_handoff_hash',LinkedInPublicationAuditReviewMetricsSummaryError); eid=_require_str(url_audit_packet,'source_export_packet_id',LinkedInPublicationAuditReviewMetricsSummaryError); exact=_require_str(url_audit_packet,'source_export_payload_hash',LinkedInPublicationAuditReviewMetricsSummaryError); evid=_require_str(url_audit_packet,'approval_export_evidence_packet_id',LinkedInPublicationAuditReviewMetricsSummaryError); evh=_require_str(url_audit_packet,'approval_export_evidence_hash',LinkedInPublicationAuditReviewMetricsSummaryError); sid=_require_str(url_audit_packet,'source_article_packet_id',LinkedInPublicationAuditReviewMetricsSummaryError); sh=_require_str(url_audit_packet,'source_article_hash',LinkedInPublicationAuditReviewMetricsSummaryError); url=_require_str(url_audit_packet,'operator_supplied_publication_url',LinkedInPublicationAuditReviewMetricsSummaryError); uh=_require_str(url_audit_packet,'operator_supplied_publication_url_hash',LinkedInPublicationAuditReviewMetricsSummaryError)
    metrics={'impressions':operator_supplied_impressions,'reactions':operator_supplied_reactions,'comments':operator_supplied_comments,'reposts':operator_supplied_reposts,'clicks':operator_supplied_clicks,'profile_views':operator_supplied_profile_views,'followers_delta':operator_supplied_followers_delta,'notes':operator_supplied_notes.strip() if operator_supplied_notes else None}
    cards=[{'card_id':'publication_url_audit_packet','card_type':'publication_url_audit_packet','display_status':'bound','source_id':aid,'hash':ah},{'card_id':'operator_handoff_packet','card_type':'operator_handoff_packet','display_status':'bound','source_id':hid,'hash':hh},{'card_id':'manual_export_payload','card_type':'manual_export_payload','display_status':'bound','source_id':eid,'hash':exact},{'card_id':'approval_export_evidence_packet','card_type':'approval_export_evidence_packet','display_status':'bound','source_id':evid,'hash':evh},{'card_id':'canonical_article_source','card_type':'canonical_article_source','display_status':'bound','source_id':sid,'hash':sh},{'card_id':'operator_supplied_publication_url','card_type':'operator_supplied_publication_url','display_status':'operator_supplied_not_network_verified','source_id':'operator_supplied_publication_url','hash':uh}]
    core={'schema_version':SCHEMA_VERSION,'task_label':TASK_LABEL,'sample_scope':SAMPLE_SCOPE,'hash_algorithm':HASH_ALGORITHM,'publication_audit_status':'manual_url_import_reviewed_pending_metrics_confirmation','metrics_summary_status':'manual_metrics_fixture_only_pending_operator_confirmation','publication_url_audit_packet_id':aid,'publication_url_audit_hash':ah,'operator_handoff_packet_id':hid,'operator_handoff_hash':hh,'source_export_packet_id':eid,'source_export_payload_hash':exact,'approval_export_evidence_packet_id':evid,'approval_export_evidence_hash':evh,'source_article_packet_id':sid,'source_article_hash':sh,'exact_payload_hash':_require_str(url_audit_packet,'exact_payload_hash',LinkedInPublicationAuditReviewMetricsSummaryError),'operator_supplied_publication_url':url,'operator_supplied_publication_url_hash':uh,'operator_supplied_publication_timestamp':_require_str(url_audit_packet,'operator_supplied_publication_timestamp',LinkedInPublicationAuditReviewMetricsSummaryError),'metrics_source':METRICS_SOURCE,'metrics_network_verified':False,'metrics_provider_api_used':False,'url_network_verified':False,'linkedin_api_used':False,'provider_call_made':False,'network_call_made':False,'credential_read_made':False,'env_value_read_made':False,'browser_session_used':False,'live_publish_performed_by_contentops':False,'manual_publication_claim_operator_supplied':True,'manual_metrics_claim_operator_supplied':True,'enabled_publish_send_dispatch_approve_controls':False,'blocked_controls':['approve','send','publish','dispatch','schedule'],'evidence_cards':cards,'manual_metrics':metrics,'operator_review_status':'pending_review','warnings':['sample_fixture_only','operator_supplied_metrics_not_network_verified','no_metrics_api_used','manual_metrics_claim_not_contentops_metrics'],'recommended_next_task':'TASK_CONTENTOPS_V6_LINKEDIN_PUBLICATION_EVIDENCE_LOOP_ACCEPTANCE_OR_NEXT_LANE_V0'}
    rh=_stable_hash(core); packet={'publication_audit_review_packet_id':f'linkedin_publication_audit_review_{rh[:16]}','publication_audit_review_hash':rh,**core}; _assert_safe(packet,LinkedInPublicationAuditReviewMetricsSummaryError); return packet
def main():
    p=argparse.ArgumentParser(); p.add_argument('--url-audit-input',required=True,type=Path); p.add_argument('--impressions',type=int,default=2310); p.add_argument('--reactions',type=int,default=67); p.add_argument('--comments',type=int,default=9); p.add_argument('--reposts',type=int,default=4); p.add_argument('--clicks',type=int,default=33); p.add_argument('--profile-views',type=int,default=21); p.add_argument('--followers-delta',type=int,default=6); p.add_argument('--notes',default='Fixture LinkedIn metrics for evaluation purposes only.'); p.add_argument('--output',required=True,type=Path); a=p.parse_args(); _write(a.output, build_linkedin_publication_audit_review_metrics_summary_packet(load_json(a.url_audit_input),operator_supplied_impressions=a.impressions,operator_supplied_reactions=a.reactions,operator_supplied_comments=a.comments,operator_supplied_reposts=a.reposts,operator_supplied_clicks=a.clicks,operator_supplied_profile_views=a.profile_views,operator_supplied_followers_delta=a.followers_delta,operator_supplied_notes=a.notes))
if __name__=='__main__': main()
