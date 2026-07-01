
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

TASK_LABEL='TASK_CONTENTOPS_V6_ROADMAP_AUDIT_AND_X_MANUAL_PUBLICATION_EVIDENCE_LOOP_HEAVY_BATCH_V0'; PUBLICATION_PLATFORM='x'; PUBLICATION_STATUS='manually_published_outside_contentops'; URL_VERIFICATION_STATUS='operator_supplied_not_network_verified'
class XManualPublicationUrlAuditImportError(ValueError): pass
def _norm(url):
    u=url.strip(); parsed=urlparse(u)
    if any(c in u for c in '\n\r\t') or parsed.scheme!='https' or not parsed.netloc: raise XManualPublicationUrlAuditImportError('operator_url_must_be_https')
    return u
def build_x_manual_publication_url_audit_import_packet(handoff_packet,*,operator_supplied_publication_url,operator_supplied_publication_timestamp,operator_supplied_publication_platform=PUBLICATION_PLATFORM,operator_supplied_publication_status=PUBLICATION_STATUS,operator_supplied_url_verification_status=URL_VERIFICATION_STATUS):
    _assert_safe(handoff_packet,XManualPublicationUrlAuditImportError); _require_true(handoff_packet,'manual_copy_only',XManualPublicationUrlAuditImportError)
    for k in ('x_api_used','provider_call_made','network_call_made','credential_read_made','env_value_read_made','browser_session_used','enabled_publish_send_dispatch_approve_controls'):_require_false(handoff_packet,k,XManualPublicationUrlAuditImportError)
    if operator_supplied_publication_platform!=PUBLICATION_PLATFORM: raise XManualPublicationUrlAuditImportError('publication_platform_must_be_x')
    url=_norm(operator_supplied_publication_url); uh=_stable_hash(url)
    hid=_require_str(handoff_packet,'operator_handoff_packet_id',XManualPublicationUrlAuditImportError); hh=_require_str(handoff_packet,'operator_handoff_hash',XManualPublicationUrlAuditImportError)
    eid=_require_str(handoff_packet,'source_export_packet_id',XManualPublicationUrlAuditImportError); exact=_require_str(handoff_packet,'source_export_payload_hash',XManualPublicationUrlAuditImportError); evid=_require_str(handoff_packet,'approval_export_evidence_packet_id',XManualPublicationUrlAuditImportError); evh=_require_str(handoff_packet,'approval_export_evidence_hash',XManualPublicationUrlAuditImportError); sid=_require_str(handoff_packet,'source_article_packet_id',XManualPublicationUrlAuditImportError); sh=_require_str(handoff_packet,'source_article_hash',XManualPublicationUrlAuditImportError)
    cards=[{'card_id':'operator_handoff_packet','card_type':'operator_handoff_packet','display_status':'bound','source_id':hid,'hash':hh},{'card_id':'manual_export_payload','card_type':'manual_export_payload','display_status':'bound','source_id':eid,'hash':exact},{'card_id':'approval_export_evidence_packet','card_type':'approval_export_evidence_packet','display_status':'bound','source_id':evid,'hash':evh},{'card_id':'canonical_article_source','card_type':'canonical_article_source','display_status':'bound','source_id':sid,'hash':sh},{'card_id':'operator_supplied_publication_url','card_type':'operator_supplied_publication_url','display_status':URL_VERIFICATION_STATUS,'source_id':'operator_supplied_publication_url','hash':uh}]
    core={'schema_version':SCHEMA_VERSION,'task_label':TASK_LABEL,'sample_scope':SAMPLE_SCOPE,'hash_algorithm':HASH_ALGORITHM,'publication_audit_status':'manual_url_imported_pending_operator_review','operator_handoff_packet_id':hid,'operator_handoff_hash':hh,'source_export_packet_id':eid,'source_export_payload_hash':exact,'approval_export_evidence_packet_id':evid,'approval_export_evidence_hash':evh,'source_article_packet_id':sid,'source_article_hash':sh,'exact_payload_hash':_require_str(handoff_packet,'exact_payload_hash',XManualPublicationUrlAuditImportError),'operator_supplied_publication_url':url,'operator_supplied_publication_url_hash':uh,'operator_supplied_publication_timestamp':operator_supplied_publication_timestamp.strip(),'operator_supplied_publication_platform':operator_supplied_publication_platform,'operator_supplied_publication_status':operator_supplied_publication_status,'operator_supplied_url_verification_status':operator_supplied_url_verification_status,'url_network_verified':False,'x_api_used':False,'provider_call_made':False,'network_call_made':False,'credential_read_made':False,'env_value_read_made':False,'browser_session_used':False,'live_publish_performed_by_contentops':False,'manual_publication_claim_operator_supplied':True,'enabled_publish_send_dispatch_approve_controls':False,'blocked_controls':['approve','send','publish','dispatch','schedule'],'evidence_cards':cards,'operator_review_status':'pending_review','warnings':['sample_fixture_only','operator_supplied_url_not_network_verified','no_url_fetch_no_scrape','manual_publication_claim_not_contentops_publish'],'recommended_next_task':'TASK_CONTENTOPS_V6_X_PUBLICATION_AUDIT_REVIEW_METRICS_SUMMARY_V0'}
    ah=_stable_hash(core); packet={'publication_url_audit_packet_id':f'x_manual_publication_url_audit_{ah[:16]}','publication_url_audit_hash':ah,**core}; _assert_safe(packet,XManualPublicationUrlAuditImportError); return packet
def main():
    p=argparse.ArgumentParser(); p.add_argument('--handoff-input',required=True,type=Path); p.add_argument('--publication-url',required=True); p.add_argument('--publication-timestamp',required=True); p.add_argument('--output',required=True,type=Path); a=p.parse_args(); _write(a.output, build_x_manual_publication_url_audit_import_packet(load_json(a.handoff_input),operator_supplied_publication_url=a.publication_url,operator_supplied_publication_timestamp=a.publication_timestamp))
if __name__=='__main__': main()
