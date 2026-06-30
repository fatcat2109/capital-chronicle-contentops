"""V6 dispatch execution preparation gate, local-only non-executable no-provider no-live."""
from __future__ import annotations
import argparse, hashlib, json, re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
SCHEMA_VERSION="6.0.0"
TASK_LABEL="TASK_CONTENTOPS_V6_DISPATCH_EXECUTION_PREPARATION_GATE_FROM_REDACTED_AUDIT_KILL_SWITCH_MANUAL_FALLBACK_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
UPSTREAM_TASK_LABEL="TASK_CONTENTOPS_V6_REDACTED_AUDIT_KILL_SWITCH_MANUAL_FALLBACK_GATE_FROM_EXACT_OPERATOR_GO_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
UPSTREAM_STATUS="redacted_audit_kill_switch_manual_fallback_ready_for_future_dispatch_execution_preparation_only"
AUDIT_MODE="local_audit_safe_metadata_only"
KILL_MODE="symbolic_local_kill_switch_required_before_dispatch_execution"
KILL_STATE="armed_for_future_dispatch_preparation_only"
FALLBACK_MODE="symbolic_manual_fallback_required_before_dispatch_execution"
FALLBACK_STATE="available_redacted_for_future_dispatch_preparation_only"
PREP_MODE="redacted_symbolic_dispatch_execution_preparation_only"
PREP_STATUS="prepared_for_future_provider_scoped_dispatch_execution_task_only"
GATE_STATUS="dispatch_execution_preparation_ready_for_future_provider_scoped_dispatch_execution_task_only"
ALLOWED_REQUIRED_KEY_NAMES={"DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK","TELEGRAM_BOT_TOKEN","TELEGRAM_CHAT_ID","SUBSTACK_MANUAL_EXPORT_ONLY","X_MANUAL_EXPORT_ONLY","LINKEDIN_ORG_DEFERRED","TIKTOK_DEFERRED"}
FALSE_FLAGS=("credential_value_read","credential_value_stored","credential_value_logged","env_read","dotenv_read","env_iterated","env_value_length_checked","env_value_prefix_checked","env_value_suffix_checked","env_value_hash_computed","env_value_digest_computed","env_value_redacted_fragment_created","provider_call_made","network_call_made","browser_session_used","executable_request_artifact_created","endpoint_url_present","webhook_url_present","channel_id_present","account_id_present","token_present","payload_body_present","public_url_created","metrics_created","publication_ready","dispatch_allowed","live_send_allowed","runtime_truth")
BUNDLE_FALSE_FLAGS=("eligible_for_future_dispatch_execution_task","eligible_for_live_send_now") + FALSE_FLAGS
SECRET_OR_URL_RE=re.compile(r"https?://|[A-Za-z0-9_-]{3,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}",re.I)
SHA256_HEX_RE=re.compile(r"^[A-Fa-f0-9]{64}$")
@dataclass(frozen=True)
class DispatchExecutionPreparationGateBundle:
    schema_version:str; task_label:str; dispatch_execution_preparation_gate_bundle_id:str; source_redacted_audit_kill_switch_manual_fallback_gate_bundle_id:str; dispatch_execution_preparation_gate_status:str; dispatch_execution_preparation_records:list[dict[str,Any]]; all_required_dispatch_execution_preparation_records_available:bool; provider_scope_required_later:bool; payload_rehydration_required_later:bool; credential_hydration_required_later:bool; destination_binding_required_later:bool; final_operator_go_required_later:bool; approved_payload_hashes:list[str]; approved_payload_preview_ids:list[str]; symbolic_credential_handle_ids:list[str]; symbolic_destination_binding_ids:list[str]; proof_available_key_names:list[str]; proof_missing_key_names:list[str]; redacted_audit_envelope_id:str; redacted_audit_packet_hash:str; kill_switch_state:str; manual_fallback_state:str; eligible_for_future_provider_scoped_dispatch_execution_task:bool; eligible_for_future_dispatch_execution_task:bool; eligible_for_live_send_now:bool; credential_value_read:bool; credential_value_stored:bool; credential_value_logged:bool; env_read:bool; dotenv_read:bool; env_iterated:bool; provider_call_made:bool; network_call_made:bool; browser_session_used:bool; executable_request_artifact_created:bool; endpoint_url_present:bool; webhook_url_present:bool; channel_id_present:bool; account_id_present:bool; token_present:bool; payload_body_present:bool; public_url_created:bool; metrics_created:bool; publication_ready:bool; dispatch_allowed:bool; live_send_allowed:bool; runtime_truth:bool; human_review_required:bool; blockers:list[str]=field(default_factory=list); warnings:list[str]=field(default_factory=list); packet_sha256:str=""
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
    for safe in ("dispatch_execution_preparation","redacted_symbolic","provider_scoped","future_provider_lane","future_provider_scoped_dispatch_method_required_later","future_provider_scoped_dispatch_execution_task","redacted_audit","kill_switch","manual_fallback","approved_payload_hash","approved_payload_preview","symbolic_destination_binding_required_later","symbolic_credential_handle_required_later","credential_value_read","credential_value_stored","credential_value_logged","env_read","dotenv_read","env_iterated","env_value_length_checked","env_value_prefix_checked","env_value_suffix_checked","env_value_hash_computed","env_value_digest_computed","env_value_redacted_fragment_created","endpoint_url_present","webhook_url_present","channel_id_present","account_id_present","token_present","payload_body_present","public_url_created","metrics_created","provider_call_made","network_call_made","browser_session_used","executable_request_artifact_created","publication_ready","dispatch_allowed","live_send_allowed","runtime_truth","discord_live_announcements_webhook","telegram_bot_token","telegram_chat_id","substack_manual_export_only","x_manual_export_only","linkedin_org_deferred","tiktok_deferred","armed_for_future_dispatch_preparation_only","available_redacted_for_future_dispatch_preparation_only","local_audit_safe_metadata_only","prepared_for_future_provider_scoped_dispatch_execution_task_only","no_provider","no_dispatch","no_live"):
        low=low.replace(safe,"safe")
    for phrase in ("browser profile","provider config","secret file","env line","credential value","env value","public url","payload body","live send","live-send","executable request","http method","url path","retry"+" policy","live"+" button","background"+" worker"):
        if phrase in low: return False
    for word in ("endpoint","webhook","token","channel","account","metrics","secret","cookie","session","curl","fetch","re"+"quests","author"+"ization","scheduler"):
        if re.search(rf"\b{re.escape(word)}\b",low): return False
    return True
def safety_blockers(o:Any,label:str)->list[str]: return [f"{label}_forbidden_value:{p}" if SECRET_OR_URL_RE.search(v) else f"{label}_forbidden_text:{p}" for p,v in _walk(o) if isinstance(v,str) and not is_safe_string(v)]
def valid_hash(v:Any)->bool: return isinstance(v,str) and bool(SHA256_HEX_RE.fullmatch(v))
def _sorted_set(records:list[dict[str,Any]],key:str)->list[str]: return sorted({str(r.get(key,"")) for r in records if str(r.get(key,""))!=""})
def _false_flags_ok(r:dict[str,Any],prefix:str)->list[str]:
    b=[]
    for k in FALSE_FLAGS: _add(b,r.get(k,False) is False,f"{prefix}_{k}_not_false")
    return b
def validate_audit_record(r:Any)->list[str]:
    b=[]
    if not isinstance(r,dict): return ["redacted_audit_record_not_object"]
    b+=safety_blockers(r,"redacted_audit_record"); _add(b,r.get("redacted_audit_mode")==AUDIT_MODE,"redacted_audit_record_mode_invalid"); _add(b,r.get("redacted_audit_complete") is True,"redacted_audit_record_complete_not_true"); _add(b,valid_hash(r.get("approved_payload_hash")),"redacted_audit_record_approved_payload_hash_invalid"); _add(b,isinstance(r.get("approved_payload_preview_id"),str) and r.get("approved_payload_preview_id")!="","redacted_audit_record_approved_payload_preview_id_empty"); _add(b,str(r.get("symbolic_destination_binding_id","")).startswith("symbolic_destination_binding_required_later_"),"redacted_audit_record_symbolic_destination_binding_id_invalid"); _add(b,str(r.get("symbolic_credential_handle_id","")).startswith("symbolic_credential_handle_required_later_"),"redacted_audit_record_symbolic_credential_handle_id_invalid"); _add(b,r.get("required_env_key_name") in ALLOWED_REQUIRED_KEY_NAMES,"redacted_audit_record_key_not_allowlisted"); b+=_false_flags_ok(r,"redacted_audit_record")
    return b
def validate_kill_record(r:Any)->list[str]:
    b=[]
    if not isinstance(r,dict): return ["kill_switch_record_not_object"]
    b+=safety_blockers(r,"kill_switch_record"); _add(b,r.get("kill_switch_required") is True,"kill_switch_record_required_not_true"); _add(b,r.get("kill_switch_mode")==KILL_MODE,"kill_switch_record_mode_invalid"); _add(b,r.get("kill_switch_state")==KILL_STATE,"kill_switch_record_not_armed"); _add(b,r.get("kill_switch_can_prevent_future_dispatch_execution") is True,"kill_switch_record_can_prevent_not_true"); _add(b,r.get("dispatch_execution_still_not_allowed") is True,"kill_switch_record_dispatch_still_allowed"); b+=_false_flags_ok(r,"kill_switch_record")
    return b
def validate_fallback_record(r:Any)->list[str]:
    b=[]
    if not isinstance(r,dict): return ["manual_fallback_record_not_object"]
    b+=safety_blockers(r,"manual_fallback_record"); _add(b,r.get("manual_fallback_required") is True,"manual_fallback_record_required_not_true"); _add(b,r.get("manual_fallback_mode")==FALLBACK_MODE,"manual_fallback_record_mode_invalid"); _add(b,r.get("manual_fallback_state")==FALLBACK_STATE,"manual_fallback_record_state_invalid"); _add(b,r.get("manual_fallback_available_for_operator") is True,"manual_fallback_record_unavailable"); _add(b,r.get("manual_fallback_instructions_redacted") is True,"manual_fallback_record_instructions_not_redacted"); b+=_false_flags_ok(r,"manual_fallback_record")
    return b
def validate_upstream_bundle(bundle:Any)->list[str]:
    b=[]
    if not isinstance(bundle,dict): return ["redacted_audit_kill_switch_manual_fallback_gate_bundle_not_object"]
    b+=safety_blockers(bundle,"redacted_audit_kill_switch_manual_fallback_gate_bundle"); _add(b,bundle.get("schema_version")==SCHEMA_VERSION,"redacted_audit_kill_switch_manual_fallback_gate_bundle_schema_version_invalid"); _add(b,bundle.get("task_label")==UPSTREAM_TASK_LABEL,"redacted_audit_kill_switch_manual_fallback_gate_bundle_task_label_invalid"); _add(b,bundle.get("redacted_audit_kill_switch_manual_fallback_gate_status")==UPSTREAM_STATUS,"redacted_audit_kill_switch_manual_fallback_gate_bundle_status_invalid"); _add(b,bundle.get("eligible_for_future_dispatch_execution_preparation_gate_task") is True,"redacted_audit_kill_switch_manual_fallback_gate_bundle_preparation_eligibility_not_true")
    for k in BUNDLE_FALSE_FLAGS: _add(b,bundle.get(k,False) is False,f"redacted_audit_kill_switch_manual_fallback_gate_bundle_{k}_not_false")
    _add(b,bundle.get("blockers")==[],"redacted_audit_kill_switch_manual_fallback_gate_bundle_blockers_not_empty"); _add(b,bundle.get("human_review_required") is True,"redacted_audit_kill_switch_manual_fallback_gate_bundle_human_review_required_not_true")
    audits=bundle.get("redacted_audit_records"); kills=bundle.get("kill_switch_records"); falls=bundle.get("manual_fallback_records")
    _add(b,isinstance(audits,list) and len(audits)>0,"redacted_audit_records_missing"); _add(b,isinstance(kills,list) and len(kills)>0,"kill_switch_records_missing"); _add(b,isinstance(falls,list) and len(falls)>0,"manual_fallback_records_missing")
    if isinstance(audits,list):
        for i,r in enumerate(audits): b += [f"audit_{i}_{x}" for x in validate_audit_record(r)]
    if isinstance(kills,list):
        for i,r in enumerate(kills): b += [f"kill_{i}_{x}" for x in validate_kill_record(r)]
    if isinstance(falls,list):
        for i,r in enumerate(falls): b += [f"fallback_{i}_{x}" for x in validate_fallback_record(r)]
    return b
def provider_family(platform:str)->str:
    p=(platform or "future").lower()
    if "telegram" in p: return "telegram_future_provider_lane"
    if "discord" in p: return "discord_future_provider_lane"
    return "generic_future_provider_lane"
def make_preparation_records(bundle:dict[str,Any])->list[dict[str,Any]]:
    audits=bundle.get("redacted_audit_records",[]); kills={r.get("source_exact_operator_dispatch_go_record_id",""):r for r in bundle.get("kill_switch_records",[]) if isinstance(r,dict)}; falls={r.get("source_exact_operator_dispatch_go_record_id",""):r for r in bundle.get("manual_fallback_records",[]) if isinstance(r,dict)}; out=[]
    for a in audits:
        sid=a.get("source_exact_operator_dispatch_go_record_id",""); k=kills.get(sid,{}); f=falls.get(sid,{})
        rec={"schema_version":SCHEMA_VERSION,"dispatch_execution_preparation_record_id":f"dispatch_execution_preparation_record_{_sha({'source':sid,'hash':a.get('approved_payload_hash')})[:16]}","source_redacted_audit_record_id":a.get("redacted_audit_record_id",""),"source_kill_switch_record_id":k.get("kill_switch_record_id",""),"source_manual_fallback_record_id":f.get("manual_fallback_record_id",""),"platform":a.get("platform",""),"required_env_key_name":a.get("required_env_key_name",""),"approved_payload_hash":a.get("approved_payload_hash",""),"approved_payload_preview_id":a.get("approved_payload_preview_id",""),"symbolic_destination_binding_id":a.get("symbolic_destination_binding_id",""),"symbolic_credential_handle_id":a.get("symbolic_credential_handle_id",""),"redacted_audit_envelope_id":bundle.get("redacted_audit_envelope_id",""),"redacted_audit_packet_hash":bundle.get("redacted_audit_packet_hash",""),"kill_switch_state":k.get("kill_switch_state",""),"manual_fallback_state":f.get("manual_fallback_state",""),"provider_family_label":provider_family(a.get("platform","")),"dispatch_method_family_label":"future_provider_scoped_dispatch_method_required_later","dispatch_preparation_mode":PREP_MODE,"dispatch_preparation_status":PREP_STATUS,"future_provider_scope_required":True,"future_exact_payload_rehydration_required":True,"future_credential_value_hydration_required":True,"future_destination_binding_required":True,"future_final_operator_go_required":True,"non_executable_preparation_record":True,"human_review_required":True,"blockers":[],"warnings":["non_executable_redacted_symbolic_preparation_only"]}
        for flag in FALSE_FLAGS: rec[flag]=False
        out.append(rec)
    return out
def validate_preparation_records(records:list[dict[str,Any]])->list[str]:
    b=[]
    if not records: b.append("dispatch_execution_preparation_records_missing")
    for i,r in enumerate(records):
        b += [f"preparation_{i}_{x}" for x in safety_blockers(r,"dispatch_execution_preparation_record")]
        _add(b,r.get("dispatch_preparation_mode")==PREP_MODE,f"preparation_{i}_mode_invalid"); _add(b,r.get("dispatch_preparation_status")==PREP_STATUS,f"preparation_{i}_status_invalid"); _add(b,r.get("non_executable_preparation_record") is True,f"preparation_{i}_not_marked_non_executable")
        for key in ("future_provider_scope_required","future_exact_payload_rehydration_required","future_credential_value_hydration_required","future_destination_binding_required","future_final_operator_go_required","human_review_required"): _add(b,r.get(key) is True,f"preparation_{i}_{key}_not_true")
        _add(b,r.get("dispatch_method_family_label")=="future_provider_scoped_dispatch_method_required_later",f"preparation_{i}_method_family_invalid"); _add(b,valid_hash(r.get("approved_payload_hash")),f"preparation_{i}_approved_payload_hash_invalid"); b += _false_flags_ok(r,f"preparation_{i}")
    return b
def make_dispatch_execution_preparation_gate_bundle(bundle:Any)->DispatchExecutionPreparationGateBundle:
    blockers=validate_upstream_bundle(bundle); source_id=str(bundle.get("redacted_audit_kill_switch_manual_fallback_gate_bundle_id") if isinstance(bundle,dict) else _sha({})[:16]); records=[]
    if not blockers: records=make_preparation_records(bundle); blockers += validate_preparation_records(records)
    all_ok=bool(records and not blockers); status=GATE_STATUS if all_ok else "blocked_invalid_redacted_audit_kill_switch_manual_fallback_or_preparation"
    exp={"approved_payload_hashes":_sorted_set(records,"approved_payload_hash"),"approved_payload_preview_ids":_sorted_set(records,"approved_payload_preview_id"),"symbolic_credential_handle_ids":_sorted_set(records,"symbolic_credential_handle_id"),"symbolic_destination_binding_ids":_sorted_set(records,"symbolic_destination_binding_id"),"proof_available_key_names":_sorted_set(records,"required_env_key_name")}
    data=dict(schema_version=SCHEMA_VERSION,task_label=TASK_LABEL,dispatch_execution_preparation_gate_bundle_id=f"dispatch_execution_preparation_gate_bundle_{_sha({'source':source_id,'status':status,'records':records})[:16]}",source_redacted_audit_kill_switch_manual_fallback_gate_bundle_id=source_id,dispatch_execution_preparation_gate_status=status,dispatch_execution_preparation_records=records if all_ok else [],all_required_dispatch_execution_preparation_records_available=all_ok,provider_scope_required_later=all_ok,payload_rehydration_required_later=all_ok,credential_hydration_required_later=all_ok,destination_binding_required_later=all_ok,final_operator_go_required_later=all_ok,approved_payload_hashes=exp["approved_payload_hashes"] if all_ok else [],approved_payload_preview_ids=exp["approved_payload_preview_ids"] if all_ok else [],symbolic_credential_handle_ids=exp["symbolic_credential_handle_ids"] if all_ok else [],symbolic_destination_binding_ids=exp["symbolic_destination_binding_ids"] if all_ok else [],proof_available_key_names=exp["proof_available_key_names"] if all_ok else [],proof_missing_key_names=[],redacted_audit_envelope_id=bundle.get("redacted_audit_envelope_id","") if isinstance(bundle,dict) and all_ok else "",redacted_audit_packet_hash=bundle.get("redacted_audit_packet_hash","") if isinstance(bundle,dict) and all_ok else "",kill_switch_state=bundle.get("kill_switch_state","") if isinstance(bundle,dict) and all_ok else "",manual_fallback_state=bundle.get("manual_fallback_state","") if isinstance(bundle,dict) and all_ok else "",eligible_for_future_provider_scoped_dispatch_execution_task=all_ok,eligible_for_future_dispatch_execution_task=False,eligible_for_live_send_now=False,credential_value_read=False,credential_value_stored=False,credential_value_logged=False,env_read=False,dotenv_read=False,env_iterated=False,provider_call_made=False,network_call_made=False,browser_session_used=False,executable_request_artifact_created=False,endpoint_url_present=False,webhook_url_present=False,channel_id_present=False,account_id_present=False,token_present=False,payload_body_present=False,public_url_created=False,metrics_created=False,publication_ready=False,dispatch_allowed=False,live_send_allowed=False,runtime_truth=False,human_review_required=True,blockers=blockers,warnings=["non_executable_dispatch_preparation_only","provider_scoped_lane_required_later_no_provider_call"])
    return DispatchExecutionPreparationGateBundle(**{**data,"packet_sha256":_packet_sha(data)})
def blocked_bundle(reason:str)->DispatchExecutionPreparationGateBundle:
    b=make_dispatch_execution_preparation_gate_bundle({}); d=asdict(b); d["blockers"]=[reason]; d["dispatch_execution_preparation_gate_status"]="blocked_invalid_redacted_audit_kill_switch_manual_fallback_or_preparation"; d["packet_sha256"]=_packet_sha(d); return DispatchExecutionPreparationGateBundle(**d)
def load_json_object(path:str|Path)->dict[str,Any]:
    try: data=json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc: raise ValueError("malformed_json") from exc
    if not isinstance(data,dict): raise ValueError("json_not_object")
    return data
def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description="V6 dispatch execution preparation gate CLI"); parser.add_argument("--redacted-audit-kill-switch-manual-fallback-gate-bundle",required=True); parser.add_argument("--output",required=True); args=parser.parse_args(argv)
    try: packet=make_dispatch_execution_preparation_gate_bundle(load_json_object(args.redacted_audit_kill_switch_manual_fallback_gate_bundle))
    except ValueError as exc: packet=blocked_bundle(str(exc))
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(asdict(packet),indent=2,sort_keys=True),encoding="utf-8")
    return 0 if packet.eligible_for_future_provider_scoped_dispatch_execution_task else 1
if __name__=="__main__":
    import sys; sys.exit(main())
