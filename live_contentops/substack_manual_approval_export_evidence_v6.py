from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION='6.0.0'
TASK_LABEL='TASK_CONTENTOPS_V6_SUBSTACK_MANUAL_APPROVAL_AND_EXPORT_EVIDENCE_HARDENING_V0'
SAMPLE_SCOPE='sample_fixture_only'
HASH_ALGORITHM='sha256_json_v6'

FORBIDDEN_SECRET_PATTERNS=(r'https://discord(?:app)?\\.com/api/webhooks/',r'sk-[A-Za-z0-9]',r'xox[baprs]-',r'ghp_[A-Za-z0-9]',r'bearer\\s+[A-Za-z0-9._-]{12,}',r'cookie\\s*[:=]',r'localstorage\\s*[:=]',r'sessionstorage\\s*[:=]')

class SubstackApprovalExportEvidenceError(ValueError):
    pass

def _stable_hash(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()

def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str): return [value]
    if isinstance(value, Mapping): return [s for item in value.values() for s in _walk_strings(item)]
    if isinstance(value, list): return [s for item in value for s in _walk_strings(item)]
    return []

def _assert_safe(packet: Mapping[str, Any]) -> None:
    for text in _walk_strings(packet):
        for pattern in FORBIDDEN_SECRET_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                raise SubstackApprovalExportEvidenceError('forbidden_secret_or_session_material')

def _require_str(packet: Mapping[str, Any], key: str) -> str:
    value=packet.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SubstackApprovalExportEvidenceError(f'missing_required_string:{key}')
    return value

def _require_mapping(packet: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value=packet.get(key)
    if not isinstance(value, Mapping):
        raise SubstackApprovalExportEvidenceError(f'missing_required_mapping:{key}')
    return value

def _require_false(packet: Mapping[str, Any], key: str) -> None:
    if packet.get(key) is not False:
        raise SubstackApprovalExportEvidenceError(f'required_false:{key}')

def build_substack_manual_approval_export_evidence_packet(export_packet: Mapping[str, Any]) -> dict[str, Any]:
    _assert_safe(export_packet)
    manual_copy_payload=_require_mapping(export_packet, 'manual_copy_payload')
    source_export_packet_id=_require_str(export_packet, 'export_packet_id')
    exact_payload_hash=_require_str(export_packet, 'exact_payload_hash')
    source_article_packet_id=_require_str(export_packet, 'source_article_packet_id')
    source_canonical_hash=_require_str(export_packet, 'source_canonical_hash')
    for key in ('live_publish_allowed','live_publish_performed','provider_call_made','network_call_made','browser_session_used'):
        _require_false(export_packet, key)
    if export_packet.get('sample_scope') != SAMPLE_SCOPE:
        raise SubstackApprovalExportEvidenceError('sample_scope_must_be_fixture_only')
    checklist=[
        {'check_id':'manual_copy_payload_present','label':'Manual copy payload reviewed in V5','status':'pending_review','required':True},
        {'check_id':'operator_confirms_no_live_publish','label':'Operator confirms no publish/send/dispatch action is enabled','status':'pending_review','required':True},
        {'check_id':'operator_confirms_substack_api_absent','label':'Operator confirms Substack API was not used','status':'pending_review','required':True},
        {'check_id':'operator_confirms_hash_match','label':'Operator confirms exact payload hash before manual copy','status':'pending_review','required':True},
    ]
    evidence_cards=[
        {'card_id':'article_source_packet','card_type':'article_source_packet','display_status':'bound','source_id':source_article_packet_id,'hash':source_canonical_hash},
        {'card_id':'substack_export_packet','card_type':'substack_export_packet','display_status':'bound','source_id':source_export_packet_id,'hash':exact_payload_hash},
        {'card_id':'approval_checkpoint','card_type':'approval_checkpoint','display_status':'pending_review','source_id':'operator_review_status','hash':exact_payload_hash},
        {'card_id':'manual_copy_checklist','card_type':'manual_copy_checklist','display_status':'ready_for_manual_copy','source_id':'manual_copy_payload','hash':_stable_hash({'checklist':checklist,'payload':manual_copy_payload})},
        {'card_id':'blocked_live_publish_state','card_type':'blocked_live_publish_state','display_status':'blocked','source_id':'live_publish_allowed=false','hash':_stable_hash({'live_publish_allowed':False,'live_publish_performed':False,'substack_api_used':False})},
    ]
    core={
        'schema_version':SCHEMA_VERSION,'task_label':TASK_LABEL,'source_export_packet_id':source_export_packet_id,
        'source_article_packet_id':source_article_packet_id,'source_canonical_hash':source_canonical_hash,
        'exact_payload_hash':exact_payload_hash,'operator_review_status':'pending_review','approval_status':'pending',
        'manual_export_status':'ready_for_manual_copy','live_publish_allowed':False,'live_publish_performed':False,
        'substack_api_used':False,'provider_call_made':False,'network_call_made':False,'credential_read_made':False,
        'env_value_read_made':False,'browser_session_used':False,'sample_scope':SAMPLE_SCOPE,
        'hash_algorithm':HASH_ALGORITHM,'manual_copy_checklist':checklist,'evidence_cards':evidence_cards,
        'blocked_controls':['approve','send','publish','dispatch'],'enabled_publish_send_dispatch_approve_controls':False,
        'operator_review_proof':'pending operator review; deterministic fixture only; no runtime proof',
        'warnings':['sample_fixture_only','manual_copy_only_no_substack_api','live_publish_disabled','operator_review_pending'],
    }
    evidence_hash=_stable_hash(core)
    packet={'approval_export_evidence_packet_id':f'substack_manual_approval_export_evidence_{evidence_hash[:16]}', 'approval_export_evidence_hash':evidence_hash, **core}
    _assert_safe(packet)
    return packet

def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8-sig'))

def main() -> None:
    import argparse
    parser=argparse.ArgumentParser(description='Build V6 Substack manual approval/export evidence packet.')
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args=parser.parse_args()
    packet=build_substack_manual_approval_export_evidence_packet(load_json(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True)+'\n', encoding='utf-8')
if __name__=='__main__': main()
