
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

TASK_LABEL='TASK_CONTENTOPS_V6_ROADMAP_AUDIT_AND_X_MANUAL_PUBLICATION_EVIDENCE_LOOP_HEAVY_BATCH_V0'
class XManualApprovalExportEvidenceError(ValueError): pass
def build_x_manual_approval_export_evidence_packet(export_packet):
    _assert_safe(export_packet, XManualApprovalExportEvidenceError)
    for k in ('x_api_used','provider_call_made','network_call_made','credential_read_made','env_value_read_made','browser_session_used','live_publish_allowed','live_publish_performed','enabled_publish_send_dispatch_approve_controls'):_require_false(export_packet,k,XManualApprovalExportEvidenceError)
    _require_true(export_packet,'manual_copy_only',XManualApprovalExportEvidenceError)
    eid=_require_str(export_packet,'export_packet_id',XManualApprovalExportEvidenceError); exact=_require_str(export_packet,'exact_payload_hash',XManualApprovalExportEvidenceError); sid=_require_str(export_packet,'source_article_packet_id',XManualApprovalExportEvidenceError); sh=_require_str(export_packet,'source_canonical_hash',XManualApprovalExportEvidenceError)
    checklist=[{'check_id':'manual_copy_payload_present','label':'X manual copy payload reviewed in V5','status':'pending_review','required':True},{'check_id':'operator_confirms_no_live_publish','label':'Operator confirms no publish/send/dispatch/schedule action is enabled','status':'pending_review','required':True},{'check_id':'operator_confirms_x_api_absent','label':'Operator confirms X API was not used','status':'pending_review','required':True},{'check_id':'operator_confirms_hash_match','label':'Operator confirms exact payload hash before manual copy','status':'pending_review','required':True}]
    cards=[{'card_id':'article_source_packet','card_type':'article_source_packet','display_status':'bound','source_id':sid,'hash':sh},{'card_id':'x_export_packet','card_type':'x_export_packet','display_status':'bound','source_id':eid,'hash':exact},{'card_id':'approval_checkpoint','card_type':'approval_checkpoint','display_status':'pending_review','source_id':'operator_review_status','hash':exact},{'card_id':'blocked_live_publish_state','card_type':'blocked_live_publish_state','display_status':'blocked','source_id':'live_publish_allowed=false','hash':_stable_hash({'live_publish_allowed':False,'x_api_used':False})}]
    core={'schema_version':SCHEMA_VERSION,'task_label':TASK_LABEL,'source_export_packet_id':eid,'source_article_packet_id':sid,'source_canonical_hash':sh,'exact_payload_hash':exact,'operator_review_status':'pending_review','approval_status':'pending','manual_export_status':'ready_for_manual_copy','x_api_used':False,'provider_call_made':False,'network_call_made':False,'credential_read_made':False,'env_value_read_made':False,'browser_session_used':False,'live_publish_allowed':False,'live_publish_performed':False,'sample_scope':SAMPLE_SCOPE,'hash_algorithm':HASH_ALGORITHM,'manual_copy_checklist':checklist,'evidence_cards':cards,'blocked_controls':['approve','send','publish','dispatch','schedule'],'enabled_publish_send_dispatch_approve_controls':False,'operator_review_proof':'pending operator review; deterministic fixture only; no runtime proof','warnings':['sample_fixture_only','manual_copy_only_no_x_api','live_publish_disabled','operator_review_pending']}
    eh=_stable_hash(core); packet={'approval_export_evidence_packet_id':f'x_manual_approval_export_evidence_{eh[:16]}','approval_export_evidence_hash':eh,**core}; _assert_safe(packet,XManualApprovalExportEvidenceError); return packet
def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True,type=Path); p.add_argument('--output',required=True,type=Path); a=p.parse_args(); _write(a.output, build_x_manual_approval_export_evidence_packet(load_json(a.input)))
if __name__=='__main__': main()
