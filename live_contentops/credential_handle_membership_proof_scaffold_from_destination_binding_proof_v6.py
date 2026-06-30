"""V6 credential handle membership proof scaffold, local-only no-value no-live."""
from __future__ import annotations

import argparse, hashlib, json, re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION="6.0.0"
TASK_LABEL="TASK_CONTENTOPS_V6_CREDENTIAL_HANDLE_MEMBERSHIP_PROOF_SCAFFOLD_FROM_DESTINATION_BINDING_PROOF_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
UPSTREAM_TASK_LABEL="TASK_CONTENTOPS_V6_DESTINATION_BINDING_PROOF_SCAFFOLD_FROM_ENV_MEMBERSHIP_GATE_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
CHECK_MODE="symbolic_destination_binding_proof_scaffold_only"
PROOF_MODE="symbolic_credential_handle_membership_proof_scaffold_only"
PROOF_AVAILABLE="credential_handle_membership_proof_available_for_future_payload_hash_revalidation_only"
PROOF_MISSING="credential_handle_membership_proof_missing_required_key"
PROOF_BLOCKED="credential_handle_membership_proof_blocked_not_available"
ALLOWED_REQUIRED_KEY_NAMES={"DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK","TELEGRAM_BOT_TOKEN","TELEGRAM_CHAT_ID","SUBSTACK_MANUAL_EXPORT_ONLY","X_MANUAL_EXPORT_ONLY","LINKEDIN_ORG_DEFERRED","TIKTOK_DEFERRED"}
CHECK_FALSE_FLAGS=("credential_value_read","credential_value_stored","credential_value_logged","env_read","dotenv_read","env_iterated","env_value_length_checked","env_value_prefix_checked","env_value_suffix_checked","env_value_hash_computed","env_value_digest_computed","env_value_redacted_fragment_created","provider_call_made","network_call_made","browser_session_used","executable_request_artifact_created","endpoint_url_present","webhook_url_present","channel_id_present","account_id_present","token_present","payload_body_present","destination_binding_present","credential_handle_present","public_url_created","metrics_created","publication_ready","dispatch_allowed","live_send_allowed","runtime_truth")
BUNDLE_FALSE_FLAGS=("eligible_for_future_dispatch_execution_task","eligible_for_live_send_now","credential_value_read","credential_value_stored","credential_value_logged","env_read","dotenv_read","env_iterated","env_value_length_checked","env_value_prefix_checked","env_value_suffix_checked","env_value_hash_computed","env_value_digest_computed","env_value_redacted_fragment_created","provider_call_made","network_call_made","browser_session_used","executable_request_artifact_created","endpoint_url_present","webhook_url_present","channel_id_present","account_id_present","token_present","payload_body_present","destination_binding_present","credential_handle_present","public_url_created","metrics_created","publication_ready","dispatch_allowed","live_send_allowed","runtime_truth")
PROOF_FALSE_FLAGS=("credential_value_read","credential_value_stored","credential_value_logged","env_read","dotenv_read","env_iterated","env_value_length_checked","env_value_prefix_checked","env_value_suffix_checked","env_value_hash_computed","env_value_digest_computed","env_value_redacted_fragment_created","provider_call_made","network_call_made","browser_session_used","executable_request_artifact_created","endpoint_url_present","webhook_url_present","channel_id_present","account_id_present","token_present","payload_body_present","public_url_created","metrics_created","publication_ready","dispatch_allowed","live_send_allowed","runtime_truth")
PROOF_TRUE_FLAGS=("payload_hash_revalidation_required_later","exact_operator_dispatch_go_required_later","redacted_audit_required_later","manual_fallback_required_later","kill_switch_required_later","future_dispatch_execution_task_required_later","human_review_required")
SECRET_OR_URL_RE=re.compile(r"https?://|[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}",re.I)
@dataclass(frozen=True)
class CredentialHandleMembershipProofScaffoldBundle:
    schema_version:str; task_label:str; credential_handle_membership_proof_scaffold_bundle_id:str; source_destination_binding_proof_scaffold_bundle_id:str; credential_handle_membership_proof_status:str; credential_handle_membership_proof_records:list[dict[str,Any]]; all_required_credential_handle_membership_proofs_available:bool; proof_available_key_names:list[str]; proof_missing_key_names:list[str]; symbolic_credential_handle_ids:list[str]; symbolic_destination_binding_ids:list[str]; eligible_for_future_payload_hash_revalidation_gate_task:bool; eligible_for_future_dispatch_execution_task:bool; eligible_for_live_send_now:bool; credential_value_read:bool; credential_value_stored:bool; credential_value_logged:bool; env_read:bool; dotenv_read:bool; env_iterated:bool; provider_call_made:bool; network_call_made:bool; browser_session_used:bool; executable_request_artifact_created:bool; endpoint_url_present:bool; webhook_url_present:bool; channel_id_present:bool; account_id_present:bool; token_present:bool; payload_body_present:bool; public_url_created:bool; metrics_created:bool; publication_ready:bool; dispatch_allowed:bool; live_send_allowed:bool; runtime_truth:bool; human_review_required:bool; blockers:list[str]=field(default_factory=list); warnings:list[str]=field(default_factory=list); packet_sha256:str=""
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
    low=v.lower()
    for safe in ("credential_handle_membership_proof","symbolic_destination_binding_required_later","symbolic_credential_handle_required_later","destination_binding_proof","present_for_future_destination_binding_review_only","missing_required_key","blocked_not_checked","credential_value_read","credential_value_stored","credential_value_logged","env_read","dotenv_read","env_iterated","env_value_length_checked","env_value_prefix_checked","env_value_suffix_checked","env_value_hash_computed","env_value_digest_computed","env_value_redacted_fragment_created","endpoint_url_present","webhook_url_present","channel_id_present","account_id_present","token_present","payload_body_present","public_url_created","metrics_created","provider_call_made","network_call_made","browser_session_used","executable_request_artifact_created","publication_ready","dispatch_allowed","live_send_allowed","runtime_truth","approved_payload_preview","approved_payload_hash","dispatch_review_record","outbox_record","credential_presence_membership_record","destination_binding_review_record","payload_hash_revalidation","exact_operator_dispatch_go","redacted_audit","manual_fallback","kill_switch","future_payload_hash_revalidation","future_dispatch_execution","no_value","no_provider","no_dispatch","no_live","discord_live_announcements_webhook","telegram_bot_token","telegram_chat_id","substack_manual_export_only","x_manual_export_only","linkedin_org_deferred","tiktok_deferred"): low=low.replace(safe,"safe")
    for phrase in ("browser profile","provider config","secret file","env line","credential value","env value","public url","payload body","live send","live-send","executable request"):
        if phrase in low: return False
    for word in ("endpoint","webhook","token","channel","account","metrics","secret","cookie","session","curl","fetch","re"+"quests","author"+"ization"):
        if re.search(rf"\b{re.escape(word)}\b",low): return False
    return True
def safety_blockers(o:Any,label:str)->list[str]: return [f"{label}_forbidden_value:{p}" if SECRET_OR_URL_RE.search(v) else f"{label}_forbidden_text:{p}" for p,v in _walk(o) if isinstance(v,str) and not is_safe_string(v)]
def validate_check_record(r:dict[str,Any])->list[str]:
    b=[]
    if not isinstance(r,dict): return ["destination_binding_proof_record_not_object"]
    b+=safety_blockers(r,"destination_binding_proof_record")
    _add(b,r.get("schema_version")==SCHEMA_VERSION,"destination_binding_proof_record_schema_version_invalid"); _add(b,r.get("proof_mode")==CHECK_MODE,"destination_binding_proof_record_mode_invalid"); _add(b,r.get("required_env_key_name") in ALLOWED_REQUIRED_KEY_NAMES,"destination_binding_proof_record_required_env_key_name_not_allowlisted")
    _add(b,r.get("destination_binding_proof_available") is True,"destination_binding_proof_record_availability_not_true")
    _add(b,r.get("proof_status")=="destination_binding_proof_available_for_future_credential_handle_membership_only","destination_binding_proof_record_status_not_available")
    _add(b,r.get("destination_binding_proof_available") is True,"destination_binding_proof_record_availability_not_true")
    _add(b,str(r.get("symbolic_destination_binding_id","")).startswith("symbolic_destination_binding_required_later_"),"destination_binding_proof_record_symbolic_destination_binding_id_invalid"); _add(b,str(r.get("symbolic_credential_handle_id","")).startswith("symbolic_credential_handle_required_later_"),"destination_binding_proof_record_symbolic_credential_handle_id_invalid")
    for k in CHECK_FALSE_FLAGS: _add(b,r.get(k, False) is False,f"destination_binding_proof_record_{k}_not_false")
    for k in ("destination_binding_proof_record_id","source_credential_presence_membership_record_id","source_destination_binding_review_record_id","source_dispatch_review_record_id","source_outbox_record_id","platform","approved_payload_preview_id","approved_payload_hash"):
        _add(b,isinstance(r.get(k),str) and r.get(k)!="",f"destination_binding_proof_record_{k}_empty")
    return b
def validate_destination_binding_proof_bundle(bundle:dict[str,Any])->list[str]:
    b=[]
    if not isinstance(bundle,dict): return ["destination_binding_proof_scaffold_bundle_not_object"]
    b+=safety_blockers(bundle,"destination_binding_proof_scaffold_bundle")
    _add(b,bundle.get("schema_version")==SCHEMA_VERSION,"destination_binding_proof_scaffold_bundle_schema_version_invalid"); _add(b,bundle.get("task_label")==UPSTREAM_TASK_LABEL,"destination_binding_proof_scaffold_bundle_task_label_invalid")
    recs=bundle.get("destination_binding_proof_records"); _add(b,isinstance(recs,list) and len(recs)>0,"destination_binding_proof_scaffold_bundle_records_empty")
    _add(b,bundle.get("all_required_destination_binding_proofs_available") is True,"destination_binding_proof_scaffold_bundle_proofs_not_available")
    _add(b,bundle.get("eligible_for_future_credential_handle_membership_proof_task") is True,"destination_binding_proof_scaffold_bundle_credential_handle_membership_eligibility_not_true")
    for k in BUNDLE_FALSE_FLAGS: _add(b,bundle.get(k, False) is False,f"destination_binding_proof_scaffold_bundle_{k}_not_false")
    _add(b,bundle.get("human_review_required") is True,"destination_binding_proof_scaffold_bundle_human_review_required_not_true")
    _add(b,bundle.get("blockers") == [],"destination_binding_proof_scaffold_bundle_blockers_not_empty")
    if isinstance(recs,list):
        for i,r in enumerate(recs): b += [f"record_{i}_{x}" for x in validate_check_record(r)]
    return b
def _symbolic_destination_binding_id(r:dict[str,Any])->str: return f"symbolic_destination_binding_required_later_{r.get('platform','unknown')}_{r.get('required_env_key_name','unknown').lower()}"
def _symbolic_credential_handle_id(r:dict[str,Any])->str: return f"symbolic_credential_handle_required_later_{r.get('platform','unknown')}_{r.get('required_env_key_name','unknown').lower()}"
def make_credential_handle_membership_proof_record(r:dict[str,Any],source_id:str)->dict[str,Any]:
    present=bool(r.get("destination_binding_proof_available") is True)
    status=PROOF_AVAILABLE if present else (PROOF_MISSING if r.get("required_env_key_missing") is True else PROOF_BLOCKED)
    key=str(r.get("required_env_key_name","")); short=_sha({"source":source_id,"record":r.get("destination_binding_proof_record_id"),"key":key,"present":present})[:16]
    d={"schema_version":SCHEMA_VERSION,"credential_handle_membership_proof_record_id":f"credential_handle_membership_proof_record_{short}","source_destination_binding_proof_record_id":r.get("destination_binding_proof_record_id",""),"source_credential_presence_membership_record_id":r.get("source_credential_presence_membership_record_id",""),"source_destination_binding_review_record_id":r.get("source_destination_binding_review_record_id",""),"source_dispatch_review_record_id":r.get("source_dispatch_review_record_id",""),"source_outbox_record_id":r.get("source_outbox_record_id",""),"platform":r.get("platform",""),"approved_payload_preview_id":r.get("approved_payload_preview_id",""),"approved_payload_hash":r.get("approved_payload_hash",""),"proof_mode":PROOF_MODE,"proof_status":status,"required_env_key_name":key,"credential_handle_membership_proof_available":present,"destination_binding_proof_available":True,"symbolic_destination_binding_id":r.get("symbolic_destination_binding_id",""),"symbolic_credential_handle_id":r.get("symbolic_credential_handle_id",""),"future_payload_hash_revalidation_required_later":True,"payload_hash_revalidation_required_later":True,"exact_operator_dispatch_go_required_later":True,"redacted_audit_required_later":True,"manual_fallback_required_later":True,"kill_switch_required_later":True,"future_dispatch_execution_task_required_later":True,"human_review_required":True,"blockers":[] if present else ["required_key_membership_not_present_for_symbolic_credential_handle_membership_proof"],"warnings":["symbolic_credential_handle_membership_only","no_credential_values","future_payload_hash_revalidation_gate_task_separate"]}
    for k in PROOF_FALSE_FLAGS: d[k]=False
    return d
def validate_credential_handle_membership_proof_record(r:dict[str,Any])->list[str]:
    b=[]
    if not isinstance(r,dict): return ["credential_handle_membership_proof_record_not_object"]
    b+=safety_blockers(r,"credential_handle_membership_proof_record"); _add(b,r.get("schema_version")==SCHEMA_VERSION,"credential_handle_membership_proof_record_schema_version_invalid"); _add(b,r.get("proof_mode")==PROOF_MODE,"credential_handle_membership_proof_record_mode_invalid"); _add(b,r.get("required_env_key_name") in ALLOWED_REQUIRED_KEY_NAMES,"credential_handle_membership_proof_record_key_not_allowlisted")
    _add(b,str(r.get("symbolic_destination_binding_id","")).startswith("symbolic_destination_binding_required_later_"),"credential_handle_membership_proof_record_symbolic_destination_binding_id_invalid"); _add(b,str(r.get("symbolic_credential_handle_id","")).startswith("symbolic_credential_handle_required_later_"),"credential_handle_membership_proof_record_symbolic_credential_handle_id_invalid")
    for k in PROOF_FALSE_FLAGS: _add(b,r.get(k, False) is False,f"credential_handle_membership_proof_record_{k}_not_false")
    for k in PROOF_TRUE_FLAGS: _add(b,r.get(k) is True,f"credential_handle_membership_proof_record_{k}_not_true")
    return b
def make_credential_handle_membership_proof_scaffold_bundle(membership_gate_bundle:dict[str,Any])->CredentialHandleMembershipProofScaffoldBundle:
    blockers=validate_destination_binding_proof_bundle(membership_gate_bundle); source_id=str(membership_gate_bundle.get("destination_binding_proof_scaffold_bundle_id") or _sha(membership_gate_bundle if isinstance(membership_gate_bundle,dict) else {})[:16]); recs=[]
    if not blockers:
        recs=[make_credential_handle_membership_proof_record(r,source_id) for r in membership_gate_bundle.get("destination_binding_proof_records",[])]
    for i,r in enumerate(recs): blockers += [f"proof_{i}_{x}" for x in validate_credential_handle_membership_proof_record(r)]
    available=sorted({r["required_env_key_name"] for r in recs if r["credential_handle_membership_proof_available"]}) if not blockers else []
    missing=sorted({r["required_env_key_name"] for r in recs if not r["credential_handle_membership_proof_available"]}) if recs and not blockers else []
    all_available=bool(recs and not blockers and not missing and len(available)==len(recs))
    status="blocked_invalid_destination_binding_proof_scaffold" if blockers else ("all_required_credential_handle_membership_proofs_available_for_future_payload_hash_revalidation_only" if all_available else "missing_required_credential_handle_membership_proofs")
    short=_sha({"source":source_id,"records":recs,"status":status})[:16]
    data=dict(schema_version=SCHEMA_VERSION,task_label=TASK_LABEL,credential_handle_membership_proof_scaffold_bundle_id=f"credential_handle_membership_proof_scaffold_bundle_{short}",source_destination_binding_proof_scaffold_bundle_id=source_id,credential_handle_membership_proof_status=status,credential_handle_membership_proof_records=recs if recs else [],all_required_credential_handle_membership_proofs_available=all_available,proof_available_key_names=available,proof_missing_key_names=missing,symbolic_credential_handle_ids=sorted({r["symbolic_credential_handle_id"] for r in recs}) if all_available else [],symbolic_destination_binding_ids=sorted({r["symbolic_destination_binding_id"] for r in recs}) if all_available else [],eligible_for_future_payload_hash_revalidation_gate_task=all_available,eligible_for_future_dispatch_execution_task=False,eligible_for_live_send_now=False,credential_value_read=False,credential_value_stored=False,credential_value_logged=False,env_read=False,dotenv_read=False,env_iterated=False,provider_call_made=False,network_call_made=False,browser_session_used=False,executable_request_artifact_created=False,endpoint_url_present=False,webhook_url_present=False,channel_id_present=False,account_id_present=False,token_present=False,payload_body_present=False,public_url_created=False,metrics_created=False,publication_ready=False,dispatch_allowed=False,live_send_allowed=False,runtime_truth=False,human_review_required=True,blockers=blockers,warnings=["local_deterministic_symbolic_credential_handle_membership_only","no_credential_values","no_provider_network_browser_dispatch_live"])
    return CredentialHandleMembershipProofScaffoldBundle(**{**data,"packet_sha256":_packet_sha(data)})
def blocked_bundle(reason:str)->CredentialHandleMembershipProofScaffoldBundle:
    b=make_credential_handle_membership_proof_scaffold_bundle({}); d=asdict(b); d["blockers"]=[reason]; d["credential_handle_membership_proof_status"]="blocked_invalid_destination_binding_proof_scaffold"; d["packet_sha256"]=_packet_sha(d); return CredentialHandleMembershipProofScaffoldBundle(**d)
def load_json_object(path:str|Path)->dict[str,Any]:
    try: data=json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc: raise ValueError("malformed_json") from exc
    if not isinstance(data,dict): raise ValueError("json_not_object")
    return data
def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description="V6 credential handle membership proof scaffold CLI"); parser.add_argument("--destination-binding-proof-scaffold-bundle",required=True); parser.add_argument("--output",required=True); args=parser.parse_args(argv)
    try: packet=make_credential_handle_membership_proof_scaffold_bundle(load_json_object(args.destination_binding_proof_scaffold_bundle))
    except ValueError as exc: packet=blocked_bundle(str(exc))
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(asdict(packet),indent=2,sort_keys=True),encoding="utf-8")
    return 0 if packet.eligible_for_future_payload_hash_revalidation_gate_task else 1
if __name__=="__main__":
    import sys; sys.exit(main())