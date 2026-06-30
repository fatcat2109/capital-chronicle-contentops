"""V6 redacted audit, kill switch, manual fallback gate, local-only no-value no-live."""
from __future__ import annotations
import argparse, hashlib, json, re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
SCHEMA_VERSION="6.0.0"
TASK_LABEL="TASK_CONTENTOPS_V6_REDACTED_AUDIT_KILL_SWITCH_MANUAL_FALLBACK_GATE_FROM_EXACT_OPERATOR_GO_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
UPSTREAM_TASK_LABEL="TASK_CONTENTOPS_V6_EXACT_OPERATOR_DISPATCH_GO_GATE_FROM_PAYLOAD_HASH_REVALIDATION_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
UPSTREAM_STATUS="exact_operator_go_declaration_matched_for_future_redacted_audit_kill_switch_manual_fallback_gate_only"
UPSTREAM_MODE="exact_operator_go_declaration_match_only"
KILL_MODE="symbolic_local_kill_switch_required_before_dispatch_execution"
KILL_STATE="armed_for_future_dispatch_preparation_only"
FALLBACK_MODE="symbolic_manual_fallback_required_before_dispatch_execution"
FALLBACK_STATE="available_redacted_for_future_dispatch_preparation_only"
GATE_STATUS="redacted_audit_kill_switch_manual_fallback_ready_for_future_dispatch_execution_preparation_only"
ALLOWED_REQUIRED_KEY_NAMES={"DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK","TELEGRAM_BOT_TOKEN","TELEGRAM_CHAT_ID","SUBSTACK_MANUAL_EXPORT_ONLY","X_MANUAL_EXPORT_ONLY","LINKEDIN_ORG_DEFERRED","TIKTOK_DEFERRED"}
FALSE_FLAGS=("credential_value_read","credential_value_stored","credential_value_logged","env_read","dotenv_read","env_iterated","env_value_length_checked","env_value_prefix_checked","env_value_suffix_checked","env_value_hash_computed","env_value_digest_computed","env_value_redacted_fragment_created","provider_call_made","network_call_made","browser_session_used","executable_request_artifact_created","endpoint_url_present","webhook_url_present","channel_id_present","account_id_present","token_present","payload_body_present","public_url_created","metrics_created","publication_ready","dispatch_allowed","live_send_allowed","runtime_truth")
BUNDLE_FALSE_FLAGS=("eligible_for_future_dispatch_execution_task","eligible_for_live_send_now") + FALSE_FLAGS
SECRET_OR_URL_RE=re.compile(r"https?://|[A-Za-z0-9_-]{3,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}",re.I)
SHA256_HEX_RE=re.compile(r"^[A-Fa-f0-9]{64}$")
@dataclass(frozen=True)
class RedactedAuditKillSwitchManualFallbackGateBundle:
    schema_version:str; task_label:str; redacted_audit_kill_switch_manual_fallback_gate_bundle_id:str; source_exact_operator_dispatch_go_gate_bundle_id:str; redacted_audit_kill_switch_manual_fallback_gate_status:str; redacted_audit_records:list[dict[str,Any]]; kill_switch_records:list[dict[str,Any]]; manual_fallback_records:list[dict[str,Any]]; redacted_audit_envelope_id:str; redacted_audit_packet_hash:str; kill_switch_state:str; manual_fallback_state:str; all_required_redacted_audit_records_available:bool; all_required_kill_switch_records_available:bool; all_required_manual_fallback_records_available:bool; approved_payload_hashes:list[str]; approved_payload_preview_ids:list[str]; symbolic_credential_handle_ids:list[str]; symbolic_destination_binding_ids:list[str]; proof_available_key_names:list[str]; proof_missing_key_names:list[str]; eligible_for_future_dispatch_execution_preparation_gate_task:bool; eligible_for_future_dispatch_execution_task:bool; eligible_for_live_send_now:bool; credential_value_read:bool; credential_value_stored:bool; credential_value_logged:bool; env_read:bool; dotenv_read:bool; env_iterated:bool; provider_call_made:bool; network_call_made:bool; browser_session_used:bool; executable_request_artifact_created:bool; endpoint_url_present:bool; webhook_url_present:bool; channel_id_present:bool; account_id_present:bool; token_present:bool; payload_body_present:bool; public_url_created:bool; metrics_created:bool; publication_ready:bool; dispatch_allowed:bool; live_send_allowed:bool; runtime_truth:bool; human_review_required:bool; blockers:list[str]=field(default_factory=list); warnings:list[str]=field(default_factory=list); packet_sha256:str=""
def _sha(o:Any)->str: return hashlib.sha256(json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
def _packet_sha(p:dict[str,Any])->str: c=dict(p); c.pop("packet_sha256",None); return _sha(c)
def _add(b:list[str],ok:bool,msg:str)->None:
    if not ok: b.append(msg)
def _walk(o:Any,path:str=""):
    if isinstance(o,dict):
        out=[]
        for k,v in o.items(): out.extend(_walk(v,f"{path}.{k}" if path else str(k)))
        return out
    if isinstance(o,list):
        out=[]
        for i,v in enumerate(o): out.extend(_walk(v,f"{path}[{i}]"))
        return out
    return [(path,o)]
def is_safe_string(v:str)->bool:
    if SECRET_OR_URL_RE.search(v): return False
    if SHA256_HEX_RE.fullmatch(v): return True
    low=v.lower()
    for safe in ("redacted_audit","kill_switch","manual_fallback","exact_operator_dispatch_go","payload_hash_revalidation","approved_payload_hash","approved_payload_preview","symbolic_destination_binding_required_later","symbolic_credential_handle_required_later","future_dispatch_execution","preparation","no_value","no_provider","no_dispatch","no_live","credential_value_read","credential_value_stored","credential_value_logged","env_read","dotenv_read","env_iterated","env_value_length_checked","env_value_prefix_checked","env_value_suffix_checked","env_value_hash_computed","env_value_digest_computed","env_value_redacted_fragment_created","endpoint_url_present","webhook_url_present","channel_id_present","account_id_present","token_present","payload_body_present","public_url_created","metrics_created","provider_call_made","network_call_made","browser_session_used","executable_request_artifact_created","publication_ready","dispatch_allowed","live_send_allowed","runtime_truth","discord_live_announcements_webhook","telegram_bot_token","telegram_chat_id","substack_manual_export_only","x_manual_export_only","linkedin_org_deferred","tiktok_deferred","armed_for_future_dispatch_preparation_only","available_redacted_for_future_dispatch_preparation_only","symbolic_local","local_audit"):
        low=low.replace(safe,"safe")
    for phrase in ("browser profile","provider config","secret file","env line","credential value","env value","public url","payload body","live send","live-send","executable request"):
        if phrase in low: return False
    for word in ("endpoint","webhook","token","channel","account","metrics","secret","cookie","session","curl","fetch","re"+"quests","author"+"ization"):
        if re.search(rf"\b{re.escape(word)}\b",low): return False
    return True
def safety_blockers(o:Any,label:str)->list[str]: return [f"{label}_forbidden_value:{p}" if SECRET_OR_URL_RE.search(v) else f"{label}_forbidden_text:{p}" for p,v in _walk(o) if isinstance(v,str) and not is_safe_string(v)]
def valid_hash(v:Any)->bool: return isinstance(v,str) and bool(SHA256_HEX_RE.fullmatch(v))
def _sorted_set(records:list[dict[str,Any]],key:str)->list[str]: return sorted({str(r.get(key,"")) for r in records if str(r.get(key,""))!=""})
def validate_upstream_record(r:dict[str,Any])->list[str]:
    b=[]
    if not isinstance(r,dict): return ["exact_operator_go_record_not_object"]
    b+=safety_blockers(r,"exact_operator_go_record")
    _add(b,r.get("schema_version")==SCHEMA_VERSION,"exact_operator_go_record_schema_version_invalid"); _add(b,r.get("operator_go_gate_mode")==UPSTREAM_MODE,"exact_operator_go_record_mode_invalid"); _add(b,r.get("operator_go_gate_status")==UPSTREAM_STATUS,"exact_operator_go_record_status_invalid")
    _add(b,r.get("operator_go_phrase_exact_match") is True,"exact_operator_go_record_phrase_match_not_true"); _add(b,r.get("eligible_for_future_redacted_audit_kill_switch_manual_fallback_gate_task") is True,"exact_operator_go_record_redacted_audit_eligibility_not_true"); _add(b,valid_hash(r.get("approved_payload_hash")),"exact_operator_go_record_approved_payload_hash_invalid")
    _add(b,isinstance(r.get("approved_payload_preview_id"),str) and r.get("approved_payload_preview_id")!="","exact_operator_go_record_approved_payload_preview_id_empty"); _add(b,str(r.get("symbolic_destination_binding_id","")).startswith("symbolic_destination_binding_required_later_"),"exact_operator_go_record_symbolic_destination_binding_id_invalid"); _add(b,str(r.get("symbolic_credential_handle_id","")).startswith("symbolic_credential_handle_required_later_"),"exact_operator_go_record_symbolic_credential_handle_id_invalid"); _add(b,r.get("required_env_key_name") in ALLOWED_REQUIRED_KEY_NAMES,"exact_operator_go_record_key_not_allowlisted")
    for k in FALSE_FLAGS: _add(b,r.get(k,False) is False,f"exact_operator_go_record_{k}_not_false")
    _add(b,r.get("human_review_required") is True,"exact_operator_go_record_human_review_required_not_true")
    return b
def validate_upstream_bundle(bundle:Any)->list[str]:
    b=[]
    if not isinstance(bundle,dict): return ["exact_operator_dispatch_go_gate_bundle_not_object"]
    b+=safety_blockers(bundle,"exact_operator_dispatch_go_gate_bundle")
    _add(b,bundle.get("schema_version")==SCHEMA_VERSION,"exact_operator_dispatch_go_gate_bundle_schema_version_invalid"); _add(b,bundle.get("task_label")==UPSTREAM_TASK_LABEL,"exact_operator_dispatch_go_gate_bundle_task_label_invalid"); _add(b,bundle.get("exact_operator_dispatch_go_gate_status")==UPSTREAM_STATUS,"exact_operator_dispatch_go_gate_bundle_status_invalid")
    recs=bundle.get("exact_operator_dispatch_go_records"); _add(b,isinstance(recs,list) and len(recs)>0,"exact_operator_dispatch_go_gate_bundle_records_empty"); _add(b,bundle.get("operator_go_phrase_exact_match") is True,"exact_operator_dispatch_go_gate_bundle_phrase_match_not_true"); _add(b,bundle.get("all_required_exact_operator_go_records_available") is True,"exact_operator_dispatch_go_gate_bundle_records_not_available"); _add(b,bundle.get("eligible_for_future_redacted_audit_kill_switch_manual_fallback_gate_task") is True,"exact_operator_dispatch_go_gate_bundle_redacted_audit_eligibility_not_true")
    for k in BUNDLE_FALSE_FLAGS: _add(b,bundle.get(k,False) is False,f"exact_operator_dispatch_go_gate_bundle_{k}_not_false")
    _add(b,bundle.get("human_review_required") is True,"exact_operator_dispatch_go_gate_bundle_human_review_required_not_true"); _add(b,bundle.get("blockers") == [],"exact_operator_dispatch_go_gate_bundle_blockers_not_empty")
    if isinstance(recs,list):
        for i,r in enumerate(recs): b += [f"record_{i}_{x}" for x in validate_upstream_record(r)]
    return b
def make_records(bundle:dict[str,Any]):
    sid=bundle.get("exact_operator_dispatch_go_gate_bundle_id",""); recs=bundle.get("exact_operator_dispatch_go_records",[])
    audit=[]; kills=[]; fallbacks=[]
    for r in recs:
        base={"schema_version":SCHEMA_VERSION,"source_exact_operator_dispatch_go_record_id":r.get("exact_operator_dispatch_go_record_id",""),"platform":r.get("platform",""),"required_env_key_name":r.get("required_env_key_name",""),"approved_payload_preview_id":r.get("approved_payload_preview_id",""),"approved_payload_hash":r.get("approved_payload_hash",""),"symbolic_destination_binding_id":r.get("symbolic_destination_binding_id",""),"symbolic_credential_handle_id":r.get("symbolic_credential_handle_id",""),"human_review_required":True,"blockers":[],"warnings":["redacted_metadata_only"]}
        aid=_sha({"audit":sid,"record":base})[:16]
        audit.append({**base,"redacted_audit_record_id":f"redacted_audit_record_{aid}","redacted_audit_mode":"local_audit_safe_metadata_only","redacted_audit_complete":True})
        kills.append({**base,"kill_switch_record_id":f"symbolic_kill_switch_record_{aid}","kill_switch_required":True,"kill_switch_mode":KILL_MODE,"kill_switch_state":KILL_STATE,"kill_switch_can_prevent_future_dispatch_execution":True,"dispatch_execution_still_not_allowed":True})
        fallbacks.append({**base,"manual_fallback_record_id":f"symbolic_manual_fallback_record_{aid}","manual_fallback_required":True,"manual_fallback_mode":FALLBACK_MODE,"manual_fallback_state":FALLBACK_STATE,"manual_fallback_available_for_operator":True,"manual_fallback_instructions_redacted":True})
    for coll in (audit,kills,fallbacks):
        for d in coll:
            for k in FALSE_FLAGS: d[k]=False
    return audit,kills,fallbacks
def validate_output_records(audit,kills,fallbacks)->list[str]:
    b=[]
    if not audit: b.append("redacted_audit_records_missing")
    if not kills: b.append("kill_switch_records_missing")
    if not fallbacks: b.append("manual_fallback_records_missing")
    for i,r in enumerate(kills):
        _add(b,r.get("kill_switch_required") is True,f"kill_switch_{i}_required_not_true"); _add(b,r.get("kill_switch_mode")==KILL_MODE,f"kill_switch_{i}_mode_invalid"); _add(b,r.get("kill_switch_state")==KILL_STATE,f"kill_switch_{i}_not_armed"); _add(b,r.get("dispatch_execution_still_not_allowed") is True,f"kill_switch_{i}_dispatch_still_allowed")
    for i,r in enumerate(fallbacks):
        _add(b,r.get("manual_fallback_required") is True,f"manual_fallback_{i}_required_not_true"); _add(b,r.get("manual_fallback_mode")==FALLBACK_MODE,f"manual_fallback_{i}_mode_invalid"); _add(b,r.get("manual_fallback_available_for_operator") is True,f"manual_fallback_{i}_unavailable"); _add(b,r.get("manual_fallback_instructions_redacted") is True,f"manual_fallback_{i}_instructions_not_redacted")
    for label,coll in (("redacted_audit",audit),("kill_switch",kills),("manual_fallback",fallbacks)):
        for i,r in enumerate(coll):
            b += [f"{label}_{i}_{x}" for x in safety_blockers(r,label)]
            for k in FALSE_FLAGS: _add(b,r.get(k,False) is False,f"{label}_{i}_{k}_not_false")
    return b
def make_redacted_audit_kill_switch_manual_fallback_gate_bundle(bundle:Any)->RedactedAuditKillSwitchManualFallbackGateBundle:
    blockers=validate_upstream_bundle(bundle); source_id=str(bundle.get("exact_operator_dispatch_go_gate_bundle_id") if isinstance(bundle,dict) else _sha({})[:16]); audit=[]; kills=[]; fallbacks=[]
    if not blockers: audit,kills,fallbacks=make_records(bundle)
    blockers += validate_output_records(audit,kills,fallbacks) if not blockers else []
    all_ok=bool(audit and kills and fallbacks and not blockers)
    status=GATE_STATUS if all_ok else "blocked_invalid_exact_operator_go_or_safety_envelope"
    exp={"approved_payload_hashes":_sorted_set(audit,"approved_payload_hash"),"approved_payload_preview_ids":_sorted_set(audit,"approved_payload_preview_id"),"symbolic_credential_handle_ids":_sorted_set(audit,"symbolic_credential_handle_id"),"symbolic_destination_binding_ids":_sorted_set(audit,"symbolic_destination_binding_id"),"proof_available_key_names":_sorted_set(audit,"required_env_key_name")}
    envelope={"source_exact_operator_dispatch_go_gate_bundle_id":source_id,"source_exact_operator_go_record_ids":_sorted_set(audit,"source_exact_operator_dispatch_go_record_id"),"upstream_task_label":UPSTREAM_TASK_LABEL,**exp,"safety_flags_all_false":True,"blockers":[],"warnings":["redacted_audit_metadata_only"]} if all_ok else {}
    audit_hash=_sha(envelope) if all_ok else ""
    data=dict(schema_version=SCHEMA_VERSION,task_label=TASK_LABEL,redacted_audit_kill_switch_manual_fallback_gate_bundle_id=f"redacted_audit_kill_switch_manual_fallback_gate_bundle_{_sha({'source':source_id,'status':status,'audit':audit_hash})[:16]}",source_exact_operator_dispatch_go_gate_bundle_id=source_id,redacted_audit_kill_switch_manual_fallback_gate_status=status,redacted_audit_records=audit if all_ok else [],kill_switch_records=kills if all_ok else [],manual_fallback_records=fallbacks if all_ok else [],redacted_audit_envelope_id=f"redacted_audit_envelope_{audit_hash[:16]}" if all_ok else "",redacted_audit_packet_hash=audit_hash,kill_switch_state=KILL_STATE if all_ok else "",manual_fallback_state=FALLBACK_STATE if all_ok else "",all_required_redacted_audit_records_available=all_ok,all_required_kill_switch_records_available=all_ok,all_required_manual_fallback_records_available=all_ok,approved_payload_hashes=exp["approved_payload_hashes"] if all_ok else [],approved_payload_preview_ids=exp["approved_payload_preview_ids"] if all_ok else [],symbolic_credential_handle_ids=exp["symbolic_credential_handle_ids"] if all_ok else [],symbolic_destination_binding_ids=exp["symbolic_destination_binding_ids"] if all_ok else [],proof_available_key_names=exp["proof_available_key_names"] if all_ok else [],proof_missing_key_names=[],eligible_for_future_dispatch_execution_preparation_gate_task=all_ok,eligible_for_future_dispatch_execution_task=False,eligible_for_live_send_now=False,credential_value_read=False,credential_value_stored=False,credential_value_logged=False,env_read=False,dotenv_read=False,env_iterated=False,provider_call_made=False,network_call_made=False,browser_session_used=False,executable_request_artifact_created=False,endpoint_url_present=False,webhook_url_present=False,channel_id_present=False,account_id_present=False,token_present=False,payload_body_present=False,public_url_created=False,metrics_created=False,publication_ready=False,dispatch_allowed=False,live_send_allowed=False,runtime_truth=False,human_review_required=True,blockers=blockers,warnings=["local_redacted_audit_symbolic_kill_switch_manual_fallback_only","no_dispatch_execution_artifact_created"])
    return RedactedAuditKillSwitchManualFallbackGateBundle(**{**data,"packet_sha256":_packet_sha(data)})
def blocked_bundle(reason:str)->RedactedAuditKillSwitchManualFallbackGateBundle:
    b=make_redacted_audit_kill_switch_manual_fallback_gate_bundle({}); d=asdict(b); d["blockers"]=[reason]; d["redacted_audit_kill_switch_manual_fallback_gate_status"]="blocked_invalid_exact_operator_go_or_safety_envelope"; d["packet_sha256"]=_packet_sha(d); return RedactedAuditKillSwitchManualFallbackGateBundle(**d)
def load_json_object(path:str|Path)->dict[str,Any]:
    try: data=json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc: raise ValueError("malformed_json") from exc
    if not isinstance(data,dict): raise ValueError("json_not_object")
    return data
def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description="V6 redacted audit kill switch manual fallback gate CLI"); parser.add_argument("--exact-operator-dispatch-go-gate-bundle",required=True); parser.add_argument("--output",required=True); args=parser.parse_args(argv)
    try: packet=make_redacted_audit_kill_switch_manual_fallback_gate_bundle(load_json_object(args.exact_operator_dispatch_go_gate_bundle))
    except ValueError as exc: packet=blocked_bundle(str(exc))
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(asdict(packet),indent=2,sort_keys=True),encoding="utf-8")
    return 0 if packet.eligible_for_future_dispatch_execution_preparation_gate_task else 1
if __name__=="__main__":
    import sys; sys.exit(main())
