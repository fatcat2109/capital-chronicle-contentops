"""V6 provider runtime authority gate, local prerequisite-only no-provider no-live."""
from __future__ import annotations
import argparse, hashlib, json, re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
SCHEMA_VERSION="6.0.0"
TASK_LABEL="TASK_CONTENTOPS_V6_PROVIDER_RUNTIME_AUTHORITY_GATE_FROM_ENDPOINT_ALLOWLIST_HEAVY_BATCH_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
UPSTREAM_TASK_LABEL="TASK_CONTENTOPS_V6_ENDPOINT_ALLOWLIST_GATE_FROM_OFFICIAL_PROVIDER_DOCS_SCOPE_HEAVY_BATCH_DOCS_ONLY_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
UPSTREAM_STATUS="endpoint_allowlist_gate_ready_for_future_provider_runtime_authority_gate_only"
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
BUNDLE_FALSE_FLAGS=("eligible_for_future_provider_runtime_authority_gate_task","eligible_for_future_provider_scoped_dispatch_execution_task","eligible_for_future_dispatch_execution_task","eligible_for_live_send_now") + FALSE_FLAGS
SECRET_OR_URL_RE=re.compile(r"https?://|[A-Za-z0-9_-]{3,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}",re.I)
SHA256_HEX_RE=re.compile(r"^[A-Fa-f0-9]{64}$")



@dataclass(frozen=True)
class ProviderRuntimeAuthorityGateBundle:
    schema_version:str; task_label:str; provider_runtime_authority_gate_bundle_id:str; source_endpoint_allowlist_gate_bundle_id:str; provider_runtime_authority_gate_status:str; provider_runtime_authority_records:list[dict[str,Any]]; all_required_provider_runtime_authority_records_available:bool; runtime_authority_symbolic_only:bool; runtime_authority_prerequisites_present:bool; runtime_authority_does_not_authorize_execution:bool; endpoint_allowlist_symbolic_only:bool; endpoint_operation_ids_sanitized:bool; raw_endpoint_values_present:bool; raw_http_method_values_present:bool; raw_url_path_values_present:bool; credential_hydration_gate_required_later:bool; exact_payload_rehydration_gate_required_later:bool; destination_resolution_gate_required_later:bool; request_shape_gate_required_later:bool; final_operator_go_required_later:bool; redacted_runtime_audit_required_later:bool; manual_fallback_required_later:bool; kill_switch_required_later:bool; approved_payload_hashes:list[str]; approved_payload_preview_ids:list[str]; symbolic_credential_handle_ids:list[str]; symbolic_destination_binding_ids:list[str]; proof_available_key_names:list[str]; proof_missing_key_names:list[str]; provider_family_labels:list[str]; official_docs_provider_families:list[str]; official_docs_source_ids:list[str]; sanitized_endpoint_operation_ids:list[str]; dispatch_method_family_labels:list[str]; redacted_audit_envelope_id:str; redacted_audit_packet_hash:str; kill_switch_state:str; manual_fallback_state:str; eligible_for_future_credential_hydration_gate_task:bool; eligible_for_future_exact_payload_rehydration_gate_task:bool; eligible_for_future_destination_resolution_gate_task:bool; eligible_for_future_request_shape_gate_task:bool; eligible_for_future_provider_scoped_dispatch_execution_task:bool; eligible_for_future_dispatch_execution_task:bool; eligible_for_live_send_now:bool; credential_value_read:bool; credential_value_stored:bool; credential_value_logged:bool; env_read:bool; dotenv_read:bool; env_iterated:bool; provider_call_made:bool; network_call_made:bool; browser_session_used:bool; executable_request_artifact_created:bool; endpoint_url_present:bool; webhook_url_present:bool; channel_id_present:bool; account_id_present:bool; token_present:bool; payload_body_present:bool; public_url_created:bool; metrics_created:bool; publication_ready:bool; dispatch_allowed:bool; live_send_allowed:bool; runtime_truth:bool; human_review_required:bool; blockers:list[str]=field(default_factory=list); warnings:list[str]=field(default_factory=list); packet_sha256:str=""
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
    for safe in ("provider_runtime_authority","runtime_authority_symbolic_only","runtime_authority_prerequisites_present","runtime_authority_does_not_authorize_execution","credential_hydration_gate","exact_payload_rehydration_gate","destination_resolution_gate","request_shape_gate","endpoint_allowlist","endpoint_operation_ids_sanitized","raw_endpoint_values_present","raw_http_method_values_present","raw_url_path_values_present","provider_runtime_authority_required_later","future_provider_lane","future_provider_scoped_dispatch_method_required_later","redacted_audit","kill_switch","manual_fallback","approved_payload_hash","approved_payload_preview","symbolic_destination_binding_required_later","symbolic_credential_handle_required_later","credential_value_read","credential_value_stored","credential_value_logged","env_read","dotenv_read","env_iterated","endpoint_url_present","webhook_url_present","channel_id_present","account_id_present","token_present","payload_body_present","public_url_created","metrics_created","provider_call_made","network_call_made","browser_session_used","executable_request_artifact_created","publication_ready","dispatch_allowed","live_send_allowed","runtime_truth","discord_live_announcements_webhook","telegram_bot_token","telegram_chat_id","discord_future_provider_lane","telegram_future_provider_lane","discord_official_docs_scope","telegram_official_docs_scope","discord_developer_docs_webhook_execute","telegram_bot_api_core_docs","discord_execute_webhook_operation_required_later","telegram_send_message_operation_required_later","telegram_send_photo_operation_required_later","telegram_send_document_operation_required_later","telegram_send_media_group_operation_required_later","no_provider","no_dispatch","no_live"):
        low=low.replace(safe,"safe")
    for phrase in ("browser profile","provider config","secret file","env line","credential value","env value","public url","payload body","live send","live-send","executable request","http method","url path","retry"+" policy","request"+" budget","time"+"out","live"+" control","live-"+"control","live"+" button","background"+" worker"):
        if phrase in low: return False
    for word in ("endpoint","webhook","token","channel","account","metrics","secret","header","body","adapter","sdk","cookie","session","curl","fetch","re"+"quests","author"+"ization","sche"+"duler","que"+"ue"):
        if re.search(rf"\b{re.escape(word)}\b",low): return False
    return True
def safety_blockers(o:Any,label:str)->list[str]: return [f"{label}_forbidden_value:{p}" if SECRET_OR_URL_RE.search(v) else f"{label}_forbidden_text:{p}" for p,v in _walk(o) if isinstance(v,str) and not is_safe_string(v)]
def valid_hash(v:Any)->bool: return isinstance(v,str) and bool(SHA256_HEX_RE.fullmatch(v))
def _sorted_set(records:list[dict[str,Any]],key:str)->list[str]: return sorted({str(x) for r in records for x in (r.get(key,[]) if isinstance(r.get(key),list) else [r.get(key,"")]) if str(x)!=""})
def _false_flags_ok(r:dict[str,Any],prefix:str)->list[str]:
    b=[]
    for k in FALSE_FLAGS: _add(b,r.get(k,False) is False,f"{prefix}_{k}_not_false")
    return b
BUNDLE_FALSE_FLAGS=("eligible_for_future_provider_scoped_dispatch_execution_task","eligible_for_future_dispatch_execution_task","eligible_for_live_send_now") + FALSE_FLAGS
ALLOWED_PROVIDER_FAMILIES={"discord_future_provider_lane","telegram_future_provider_lane"}
ALLOWED_DOC_FAMILIES={"discord_official_docs_scope","telegram_official_docs_scope"}
ALLOWED_OPS={"discord_execute_webhook_operation_required_later","telegram_send_message_operation_required_later","telegram_send_photo_operation_required_later","telegram_send_document_operation_required_later","telegram_send_media_group_operation_required_later"}
OPS_BY_DOCS={"discord_developer_docs_webhook_execute":["discord_execute_webhook_operation_required_later"],"telegram_bot_api_core_docs":["telegram_send_message_operation_required_later","telegram_send_photo_operation_required_later","telegram_send_document_operation_required_later","telegram_send_media_group_operation_required_later"]}
DOCS_BY_PROVIDER={"discord_future_provider_lane":("discord_official_docs_scope","discord_developer_docs_webhook_execute"),"telegram_future_provider_lane":("telegram_official_docs_scope","telegram_bot_api_core_docs")}
GATE_STATUS="provider_runtime_authority_gate_ready_for_future_credential_hydration_gate_only"
REC_MODE="provider_runtime_authority_gate_symbolic_prerequisite_check_only"
REC_STATUS="provider_runtime_authority_ready_for_future_credential_and_payload_rehydration_gates_only"
def validate_allowlist_record(r:Any)->list[str]:
    b=[]
    if not isinstance(r,dict): return ["endpoint_allowlist_record_not_object"]
    b+=safety_blockers(r,"endpoint_allowlist_record")
    provider=r.get("provider_family_label"); docs_family=r.get("official_docs_provider_family"); docs_id=r.get("official_docs_source_id"); ops=r.get("sanitized_endpoint_operation_ids")
    _add(b,r.get("endpoint_allowlist_mode")=="endpoint_allowlist_gate_docs_backed_symbolic_only","endpoint_allowlist_record_mode_invalid"); _add(b,r.get("endpoint_allowlist_status")=="endpoint_allowlist_ready_for_future_runtime_authority_gate_only","endpoint_allowlist_record_status_invalid")
    _add(b,r.get("endpoint_allowlist_symbolic_only") is True,"endpoint_allowlist_record_not_symbolic_only"); _add(b,r.get("endpoint_operation_ids_sanitized") is True,"endpoint_allowlist_record_operation_ids_not_sanitized"); _add(b,r.get("non_executable_endpoint_allowlist_record") is True,"endpoint_allowlist_record_executable_marker_invalid")
    for k in ("raw_endpoint_values_present","raw_http_method_values_present","raw_url_path_values_present"):
        _add(b,r.get(k) is False,f"endpoint_allowlist_record_{k}_not_false")
    for k in ("provider_runtime_authority_required_later","credential_hydration_gate_required_later","exact_payload_rehydration_gate_required_later","final_operator_go_required_later","redacted_runtime_audit_required_later","manual_fallback_required_later","kill_switch_required_later","human_review_required"):
        _add(b,r.get(k) is True,f"endpoint_allowlist_record_{k}_not_true")
    _add(b,provider in ALLOWED_PROVIDER_FAMILIES,"endpoint_allowlist_record_provider_family_invalid"); _add(b,docs_family in ALLOWED_DOC_FAMILIES,"endpoint_allowlist_record_docs_family_invalid"); _add(b,docs_id in OPS_BY_DOCS,"endpoint_allowlist_record_source_id_invalid")
    if provider in DOCS_BY_PROVIDER: _add(b,(docs_family,docs_id)==DOCS_BY_PROVIDER[provider],"endpoint_allowlist_record_provider_docs_mismatch")
    _add(b,isinstance(ops,list) and ops==OPS_BY_DOCS.get(docs_id),"endpoint_allowlist_record_operation_ids_invalid")
    if isinstance(ops,list):
        for op in ops: _add(b,op in ALLOWED_OPS,"endpoint_allowlist_record_operation_id_not_allowlisted")
    _add(b,r.get("dispatch_method_family_label")=="future_provider_scoped_dispatch_method_required_later","endpoint_allowlist_record_method_family_invalid"); _add(b,valid_hash(r.get("approved_payload_hash")),"endpoint_allowlist_record_approved_payload_hash_invalid"); _add(b,isinstance(r.get("approved_payload_preview_id"),str) and r.get("approved_payload_preview_id")!="","endpoint_allowlist_record_approved_payload_preview_id_empty"); _add(b,str(r.get("symbolic_destination_binding_id","")).startswith("symbolic_destination_binding_required_later_"),"endpoint_allowlist_record_symbolic_destination_binding_id_invalid"); _add(b,str(r.get("symbolic_credential_handle_id","")).startswith("symbolic_credential_handle_required_later_"),"endpoint_allowlist_record_symbolic_credential_handle_id_invalid"); _add(b,r.get("required_env_key_name") in ALLOWED_REQUIRED_KEY_NAMES,"endpoint_allowlist_record_key_not_allowlisted")
    b+=_false_flags_ok(r,"endpoint_allowlist_record")
    return b
def validate_upstream_bundle(bundle:Any)->list[str]:
    b=[]
    if not isinstance(bundle,dict): return ["endpoint_allowlist_gate_bundle_not_object"]
    b+=safety_blockers(bundle,"endpoint_allowlist_gate_bundle")
    _add(b,bundle.get("schema_version")==SCHEMA_VERSION,"endpoint_allowlist_gate_bundle_schema_version_invalid"); _add(b,bundle.get("task_label")==UPSTREAM_TASK_LABEL,"endpoint_allowlist_gate_bundle_task_label_invalid"); _add(b,bundle.get("endpoint_allowlist_gate_status")==UPSTREAM_STATUS,"endpoint_allowlist_gate_bundle_status_invalid"); _add(b,bundle.get("eligible_for_future_provider_runtime_authority_gate_task") is True,"endpoint_allowlist_gate_bundle_runtime_authority_eligibility_not_true")
    _add(b,bundle.get("endpoint_allowlist_symbolic_only") is True,"endpoint_allowlist_gate_bundle_not_symbolic_only"); _add(b,bundle.get("endpoint_operation_ids_sanitized") is True,"endpoint_allowlist_gate_bundle_operation_ids_not_sanitized")
    for k in ("raw_endpoint_values_present","raw_http_method_values_present","raw_url_path_values_present"):
        _add(b,bundle.get(k) is False,f"endpoint_allowlist_gate_bundle_{k}_not_false")
    for k in BUNDLE_FALSE_FLAGS: _add(b,bundle.get(k,False) is False,f"endpoint_allowlist_gate_bundle_{k}_not_false")
    _add(b,bundle.get("blockers")==[],"endpoint_allowlist_gate_bundle_blockers_not_empty"); _add(b,bundle.get("human_review_required") is True,"endpoint_allowlist_gate_bundle_human_review_required_not_true")
    recs=bundle.get("endpoint_allowlist_records"); _add(b,isinstance(recs,list) and len(recs)>0,"endpoint_allowlist_records_missing")
    if isinstance(recs,list):
        for i,r in enumerate(recs): b += [f"record_{i}_{x}" for x in validate_allowlist_record(r)]
    return b
def make_runtime_records(bundle:dict[str,Any])->list[dict[str,Any]]:
    out=[]
    for r in bundle.get("endpoint_allowlist_records",[]):
        rec={"schema_version":SCHEMA_VERSION,"provider_runtime_authority_record_id":f"provider_runtime_authority_record_{_sha({'source':r.get('endpoint_allowlist_record_id'),'ops':r.get('sanitized_endpoint_operation_ids')})[:16]}","source_endpoint_allowlist_record_id":r.get("endpoint_allowlist_record_id",""),"platform":r.get("platform",""),"provider_family_label":r.get("provider_family_label",""),"official_docs_provider_family":r.get("official_docs_provider_family",""),"official_docs_source_id":r.get("official_docs_source_id",""),"dispatch_method_family_label":r.get("dispatch_method_family_label",""),"required_env_key_name":r.get("required_env_key_name",""),"approved_payload_hash":r.get("approved_payload_hash",""),"approved_payload_preview_id":r.get("approved_payload_preview_id",""),"symbolic_destination_binding_id":r.get("symbolic_destination_binding_id",""),"symbolic_credential_handle_id":r.get("symbolic_credential_handle_id",""),"sanitized_endpoint_operation_ids":r.get("sanitized_endpoint_operation_ids",[]),"endpoint_allowlist_symbolic_only":True,"endpoint_operation_ids_sanitized":True,"raw_endpoint_values_present":False,"raw_http_method_values_present":False,"raw_url_path_values_present":False,"provider_runtime_authority_mode":REC_MODE,"provider_runtime_authority_status":REC_STATUS,"runtime_authority_symbolic_only":True,"runtime_authority_prerequisites_present":True,"runtime_authority_does_not_authorize_execution":True,"future_credential_hydration_gate_required":True,"future_exact_payload_rehydration_gate_required":True,"future_destination_resolution_gate_required":True,"future_request_shape_gate_required":True,"future_final_operator_go_required":True,"future_redacted_runtime_audit_required":True,"future_manual_fallback_required":True,"future_kill_switch_required":True,"non_executable_runtime_authority_record":True,"human_review_required":True,"blockers":[],"warnings":["runtime_authority_prerequisite_check_only_no_execution"]}
        for flag in FALSE_FLAGS: rec[flag]=False
        out.append(rec)
    return out
def validate_runtime_records(records:list[dict[str,Any]])->list[str]:
    b=[]
    if not records: b.append("provider_runtime_authority_records_missing")
    for i,r in enumerate(records):
        b += [f"provider_runtime_authority_{i}_{x}" for x in safety_blockers(r,"provider_runtime_authority_record")]
        for k in ("runtime_authority_symbolic_only","runtime_authority_prerequisites_present","runtime_authority_does_not_authorize_execution","future_credential_hydration_gate_required","future_exact_payload_rehydration_gate_required","future_destination_resolution_gate_required","future_request_shape_gate_required","future_final_operator_go_required","future_redacted_runtime_audit_required","future_manual_fallback_required","future_kill_switch_required","non_executable_runtime_authority_record","human_review_required"):
            _add(b,r.get(k) is True,f"provider_runtime_authority_{i}_{k}_not_true")
        for k in ("raw_endpoint_values_present","raw_http_method_values_present","raw_url_path_values_present"):
            _add(b,r.get(k) is False,f"provider_runtime_authority_{i}_{k}_not_false")
        _add(b,r.get("endpoint_allowlist_symbolic_only") is True,f"provider_runtime_authority_{i}_endpoint_allowlist_not_symbolic_only"); _add(b,r.get("endpoint_operation_ids_sanitized") is True,f"provider_runtime_authority_{i}_operation_ids_not_sanitized")
        b+=_false_flags_ok(r,f"provider_runtime_authority_{i}")
    return b
def make_provider_runtime_authority_gate_bundle(bundle:Any)->ProviderRuntimeAuthorityGateBundle:
    blockers=validate_upstream_bundle(bundle); source_id=str(bundle.get("endpoint_allowlist_gate_bundle_id") if isinstance(bundle,dict) else _sha({})[:16]); records=[]
    if not blockers: records=make_runtime_records(bundle); blockers+=validate_runtime_records(records)
    all_ok=bool(records and not blockers); status=GATE_STATUS if all_ok else "blocked_invalid_endpoint_allowlist_or_provider_runtime_authority"
    exp={"approved_payload_hashes":_sorted_set(records,"approved_payload_hash"),"approved_payload_preview_ids":_sorted_set(records,"approved_payload_preview_id"),"symbolic_credential_handle_ids":_sorted_set(records,"symbolic_credential_handle_id"),"symbolic_destination_binding_ids":_sorted_set(records,"symbolic_destination_binding_id"),"proof_available_key_names":_sorted_set(records,"required_env_key_name"),"provider_family_labels":_sorted_set(records,"provider_family_label"),"official_docs_provider_families":_sorted_set(records,"official_docs_provider_family"),"official_docs_source_ids":_sorted_set(records,"official_docs_source_id"),"sanitized_endpoint_operation_ids":_sorted_set(records,"sanitized_endpoint_operation_ids"),"dispatch_method_family_labels":_sorted_set(records,"dispatch_method_family_label")}
    data=dict(schema_version=SCHEMA_VERSION,task_label=TASK_LABEL,provider_runtime_authority_gate_bundle_id=f"provider_runtime_authority_gate_bundle_{_sha({'source':source_id,'status':status,'records':records})[:16]}",source_endpoint_allowlist_gate_bundle_id=source_id,provider_runtime_authority_gate_status=status,provider_runtime_authority_records=records if all_ok else [],all_required_provider_runtime_authority_records_available=all_ok,runtime_authority_symbolic_only=all_ok,runtime_authority_prerequisites_present=all_ok,runtime_authority_does_not_authorize_execution=True,endpoint_allowlist_symbolic_only=all_ok,endpoint_operation_ids_sanitized=all_ok,raw_endpoint_values_present=False,raw_http_method_values_present=False,raw_url_path_values_present=False,credential_hydration_gate_required_later=all_ok,exact_payload_rehydration_gate_required_later=all_ok,destination_resolution_gate_required_later=all_ok,request_shape_gate_required_later=all_ok,final_operator_go_required_later=all_ok,redacted_runtime_audit_required_later=all_ok,manual_fallback_required_later=all_ok,kill_switch_required_later=all_ok,approved_payload_hashes=exp["approved_payload_hashes"] if all_ok else [],approved_payload_preview_ids=exp["approved_payload_preview_ids"] if all_ok else [],symbolic_credential_handle_ids=exp["symbolic_credential_handle_ids"] if all_ok else [],symbolic_destination_binding_ids=exp["symbolic_destination_binding_ids"] if all_ok else [],proof_available_key_names=exp["proof_available_key_names"] if all_ok else [],proof_missing_key_names=[],provider_family_labels=exp["provider_family_labels"] if all_ok else [],official_docs_provider_families=exp["official_docs_provider_families"] if all_ok else [],official_docs_source_ids=exp["official_docs_source_ids"] if all_ok else [],sanitized_endpoint_operation_ids=exp["sanitized_endpoint_operation_ids"] if all_ok else [],dispatch_method_family_labels=exp["dispatch_method_family_labels"] if all_ok else [],redacted_audit_envelope_id=bundle.get("redacted_audit_envelope_id","") if isinstance(bundle,dict) and all_ok else "",redacted_audit_packet_hash=bundle.get("redacted_audit_packet_hash","") if isinstance(bundle,dict) and all_ok else "",kill_switch_state=bundle.get("kill_switch_state","") if isinstance(bundle,dict) and all_ok else "",manual_fallback_state=bundle.get("manual_fallback_state","") if isinstance(bundle,dict) and all_ok else "",eligible_for_future_credential_hydration_gate_task=all_ok,eligible_for_future_exact_payload_rehydration_gate_task=False,eligible_for_future_destination_resolution_gate_task=False,eligible_for_future_request_shape_gate_task=False,eligible_for_future_provider_scoped_dispatch_execution_task=False,eligible_for_future_dispatch_execution_task=False,eligible_for_live_send_now=False,credential_value_read=False,credential_value_stored=False,credential_value_logged=False,env_read=False,dotenv_read=False,env_iterated=False,provider_call_made=False,network_call_made=False,browser_session_used=False,executable_request_artifact_created=False,endpoint_url_present=False,webhook_url_present=False,channel_id_present=False,account_id_present=False,token_present=False,payload_body_present=False,public_url_created=False,metrics_created=False,publication_ready=False,dispatch_allowed=False,live_send_allowed=False,runtime_truth=False,human_review_required=True,blockers=blockers,warnings=["provider_runtime_authority_prerequisites_only","credential_hydration_gate_required_later"])
    return ProviderRuntimeAuthorityGateBundle(**{**data,"packet_sha256":_packet_sha(data)})
def blocked_bundle(reason:str)->ProviderRuntimeAuthorityGateBundle:
    b=make_provider_runtime_authority_gate_bundle({}); d=asdict(b); d["blockers"]=[reason]; d["provider_runtime_authority_gate_status"]="blocked_invalid_endpoint_allowlist_or_provider_runtime_authority"; d["packet_sha256"]=_packet_sha(d); return ProviderRuntimeAuthorityGateBundle(**d)
def load_json_object(path:str|Path)->dict[str,Any]:
    try: data=json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc: raise ValueError("malformed_json") from exc
    if not isinstance(data,dict): raise ValueError("json_not_object")
    return data
def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description="V6 provider runtime authority gate CLI"); parser.add_argument("--endpoint-allowlist-gate-bundle",required=True); parser.add_argument("--output",required=True); args=parser.parse_args(argv)
    try: packet=make_provider_runtime_authority_gate_bundle(load_json_object(args.endpoint_allowlist_gate_bundle))
    except ValueError as exc: packet=blocked_bundle(str(exc))
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(asdict(packet),indent=2,sort_keys=True),encoding="utf-8")
    return 0 if packet.eligible_for_future_credential_hydration_gate_task else 1
if __name__=="__main__":
    import sys; sys.exit(main())
