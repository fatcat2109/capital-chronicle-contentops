
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
class XManualExportError(ValueError): pass
def build_x_manual_export_packet(source_packet: Mapping[str,Any]) -> dict[str,Any]:
    _assert_safe(source_packet, XManualExportError)
    article=_require_mapping(source_packet,'canonical_article_draft',XManualExportError)
    source_id=_require_str(source_packet,'packet_id',XManualExportError)
    source_hash=_require_str(article,'canonical_payload_hash',XManualExportError)
    title=_require_str(article,'title',XManualExportError)
    post_body=(f"Capital Chronicle educational briefing: {title}\n\n"
        "Process note: This manual X post is fixture-only evidence for operator review. "
        "It summarizes methodology, source review, and educational context without recommendations.\n\n"
        "Operators must verify primary sources independently before any manual external publication.\n\n"
        "Manual copy only. X API not used. Live publish disabled. No runtime proof.")
    manual_copy_payload={'platform':'x','target':'x_manual_copy','copy_mode':'manual copy only','post_body':post_body,'operator_instructions':'Review in canonical V5, then manually copy into X only if separately approved outside ContentOps.','safety_labels':[SAMPLE_SCOPE,'manual copy only','X API not used','live publish disabled','no runtime proof']}
    exact=_stable_hash(manual_copy_payload)
    packet={'schema_version':SCHEMA_VERSION,'task_label':TASK_LABEL,'export_packet_id':f'x_manual_export_{exact[:16]}','platform':'x','source_article_packet_id':source_id,'source_canonical_hash':source_hash,'post_body_fixture':post_body,'manual_copy_payload':manual_copy_payload,'exact_payload_hash':exact,'hash_algorithm':HASH_ALGORITHM,'export_status':'ready_for_manual_review','approval_status':'pending','sample_scope':SAMPLE_SCOPE,'manual_copy_only':True,'x_api_used':False,'provider_call_made':False,'network_call_made':False,'credential_read_made':False,'env_value_read_made':False,'browser_session_used':False,'live_publish_allowed':False,'live_publish_performed':False,'blocked_controls':['approve','send','publish','dispatch','schedule'],'enabled_publish_send_dispatch_approve_controls':False,'warnings':['sample_fixture_only','manual_copy_only_no_x_api','no_runtime_proof'],'recommended_next_task':'TASK_CONTENTOPS_V6_X_MANUAL_APPROVAL_EXPORT_EVIDENCE_V0'}
    _assert_safe(packet, XManualExportError); return packet
def main():
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True,type=Path); p.add_argument('--output',required=True,type=Path); a=p.parse_args(); _write(a.output, build_x_manual_export_packet(load_json(a.input)))
if __name__=='__main__': main()
