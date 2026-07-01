
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
class XManualOperatorHandoffError(ValueError): pass
def build_x_manual_operator_handoff_packet(export_packet,evidence_packet):
    _assert_safe(export_packet,XManualOperatorHandoffError); _assert_safe(evidence_packet,XManualOperatorHandoffError)
    eid=_require_str(export_packet,'export_packet_id',XManualOperatorHandoffError); exact=_require_str(export_packet,'exact_payload_hash',XManualOperatorHandoffError); evid=_require_str(evidence_packet,'approval_export_evidence_packet_id',XManualOperatorHandoffError); evh=_require_str(evidence_packet,'approval_export_evidence_hash',XManualOperatorHandoffError)
    sid=_require_str(export_packet,'source_article_packet_id',XManualOperatorHandoffError); sh=_require_str(export_packet,'source_canonical_hash',XManualOperatorHandoffError)
    _eq(evidence_packet.get('source_export_packet_id'),eid,'export_packet_id',XManualOperatorHandoffError); _eq(evidence_packet.get('exact_payload_hash'),exact,'exact_payload_hash',XManualOperatorHandoffError)
    for pkt in (export_packet,evidence_packet):
        for k in ('x_api_used','provider_call_made','network_call_made','credential_read_made','env_value_read_made','browser_session_used','enabled_publish_send_dispatch_approve_controls'):_require_false(pkt,k,XManualOperatorHandoffError)
    checklist=[{'check_id':'confirm_article_source','label':'Confirm canonical article source packet and hash','status':'pending_review','required':True},{'check_id':'confirm_export_payload','label':'Confirm X manual export payload hash before copy','status':'pending_review','required':True},{'check_id':'confirm_approval_evidence','label':'Confirm approval/export evidence packet remains pending','status':'pending_review','required':True},{'check_id':'confirm_manual_copy_only','label':'Confirm manual copy only; no X API, publish, send, dispatch, scheduler, DM, comment, like, or reaction','status':'pending_review','required':True}]
    instructions=['Open canonical V5 Manual Export, Approval Queue, and Evidence Vault views only.','Compare article, export, approval/export evidence, and handoff hashes before manual copy.','If separate human approval is granted outside this packet, manually copy the payload into X outside ContentOps.','Do not use X API, browser automation, live publish, dispatch, scheduler, provider calls, env values, credentials, browser sessions, cookies, localStorage, tokens, DMs, comments, likes, or reactions.']
    cards=[{'card_id':'canonical_article_source','card_type':'canonical_article_source','display_status':'bound','source_id':sid,'hash':sh},{'card_id':'manual_export_payload','card_type':'manual_export_payload','display_status':'bound','source_id':eid,'hash':exact},{'card_id':'approval_export_evidence_packet','card_type':'approval_export_evidence_packet','display_status':'bound','source_id':evid,'hash':evh},{'card_id':'manual_copy_checklist','card_type':'manual_copy_checklist','display_status':'pending_review','source_id':'operator_handoff_checklist','hash':_stable_hash({'manual_copy_checklist':checklist})}]
    core={'schema_version':SCHEMA_VERSION,'task_label':TASK_LABEL,'source_article_packet_id':sid,'source_article_hash':sh,'source_export_packet_id':eid,'source_export_payload_hash':exact,'approval_export_evidence_packet_id':evid,'approval_export_evidence_hash':evh,'manual_copy_payload':_require_mapping(export_packet,'manual_copy_payload',XManualOperatorHandoffError),'exact_payload_hash':_stable_hash({'manual_copy_payload':export_packet['manual_copy_payload'],'operator_instructions':instructions}),'hash_algorithm':HASH_ALGORITHM,'approval_status':'pending','operator_handoff_status':'ready_for_manual_review','manual_copy_only':True,'x_api_used':False,'provider_call_made':False,'network_call_made':False,'credential_read_made':False,'env_value_read_made':False,'browser_session_used':False,'live_publish_allowed':False,'live_publish_performed':False,'sample_scope':SAMPLE_SCOPE,'manual_copy_checklist':checklist,'operator_instructions':instructions,'evidence_cards':cards,'blockers':['operator_approval_pending','live_publish_disabled','manual_copy_only','x_api_disabled'],'blocked_controls':['approve','send','publish','dispatch','schedule'],'enabled_publish_send_dispatch_approve_controls':False,'warnings':['sample_fixture_only','manual_copy_only_no_x_api','live_publish_disabled','operator_handoff_pending_review'],'recommended_next_task':'TASK_CONTENTOPS_V6_X_MANUAL_PUBLICATION_URL_AUDIT_IMPORT_V0'}
    ph=_stable_hash(core); core['evidence_cards']=[*cards,{'card_id':'operator_handoff_packet','card_type':'operator_handoff_packet','display_status':'ready_for_manual_review','source_id':'operator_handoff','hash':ph}]; ph=_stable_hash(core); packet={'operator_handoff_packet_id':f'x_manual_operator_handoff_{ph[:16]}','operator_handoff_hash':ph,**core}; _assert_safe(packet,XManualOperatorHandoffError); return packet
def main():
    p=argparse.ArgumentParser(); p.add_argument('--export-input',required=True,type=Path); p.add_argument('--evidence-input',required=True,type=Path); p.add_argument('--output',required=True,type=Path); a=p.parse_args(); _write(a.output, build_x_manual_operator_handoff_packet(load_json(a.export_input),load_json(a.evidence_input)))
if __name__=='__main__': main()
