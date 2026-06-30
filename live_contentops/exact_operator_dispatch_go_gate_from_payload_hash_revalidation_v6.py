"""V6 exact operator dispatch GO gate, local-only no-value no-live."""
from __future__ import annotations

import argparse, hashlib, json, re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION="6.0.0"
TASK_LABEL="TASK_CONTENTOPS_V6_EXACT_OPERATOR_DISPATCH_GO_GATE_FROM_PAYLOAD_HASH_REVALIDATION_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
UPSTREAM_TASK_LABEL="TASK_CONTENTOPS_V6_PAYLOAD_HASH_REVALIDATION_GATE_FROM_CREDENTIAL_HANDLE_MEMBERSHIP_PROOF_HEAVY_BATCH_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
UPSTREAM_STATUS="all_required_payload_hash_revalidations_available_for_future_exact_operator_dispatch_go_only"
UPSTREAM_MODE="approved_payload_hash_identifier_revalidation_only"
UPSTREAM_RECORD_STATUS="approved_payload_hash_identifier_revalidated_for_future_exact_operator_dispatch_go_only"
GO_PHRASE="JIM_EXACT_GO_FOR_FUTURE_DISPATCH_GATE_ONLY_NO_PROVIDER_NO_DISPATCH_NO_LIVE"
GO_MODE="exact_operator_go_declaration_match_only"
GO_STATUS="exact_operator_go_declaration_matched_for_future_redacted_audit_kill_switch_manual_fallback_gate_only"
ALLOWED_REQUIRED_KEY_NAMES={"DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK","TELEGRAM_BOT_TOKEN","TELEGRAM_CHAT_ID","SUBSTACK_MANUAL_EXPORT_ONLY","X_MANUAL_EXPORT_ONLY","LINKEDIN_ORG_DEFERRED","TIKTOK_DEFERRED"}
FALSE_FLAGS=("credential_value_read","credential_value_stored","credential_value_logged","env_read","dotenv_read","env_iterated","env_value_length_checked","env_value_prefix_checked","env_value_suffix_checked","env_value_hash_computed","env_value_digest_computed","env_value_redacted_fragment_created","provider_call_made","network_call_made","browser_session_used","executable_request_artifact_created","endpoint_url_present","webhook_url_present","channel_id_present","account_id_present","token_present","payload_body_present","public_url_created","metrics_created","publication_ready","dispatch_allowed","live_send_allowed","runtime_truth")
BUNDLE_FALSE_FLAGS=("eligible_for_future_dispatch_execution_task","eligible_for_live_send_now") + FALSE_FLAGS
TRUE_RECORD_FLAGS=("payload_hash_format_valid","payload_hash_revalidated_for_future_exact_operator_dispatch_go_only","future_exact_operator_dispatch_go_required_later","redacted_audit_required_later","manual_fallback_required_later","kill_switch_required_later","future_dispatch_execution_task_required_later","human_review_required")
SECRET_OR_URL_RE=re.compile(r"https?://|[A-Za-z0-9_-]{3,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}",re.I)
SHA256_HEX_RE=re.compile(r"^[A-Fa-f0-9]{64}$")

@dataclass(frozen=True)
class ExactOperatorDispatchGoGateBundle:
    schema_version:str; task_label:str; exact_operator_dispatch_go_gate_bundle_id:str; source_payload_hash_revalidation_gate_bundle_id:str; exact_operator_dispatch_go_gate_status:str; exact_operator_dispatch_go_records:list[dict[str,Any]]; operator_go_declaration_id:str; operator_go_phrase_exact_match:bool; all_required_exact_operator_go_records_available:bool; approved_payload_hashes:list[str]; approved_payload_preview_ids:list[str]; symbolic_credential_handle_ids:list[str]; symbolic_destination_binding_ids:list[str]; proof_available_key_names:list[str]; proof_missing_key_names:list[str]; eligible_for_future_redacted_audit_kill_switch_manual_fallback_gate_task:bool; eligible_for_future_dispatch_execution_task:bool; eligible_for_live_send_now:bool; credential_value_read:bool; credential_value_stored:bool; credential_value_logged:bool; env_read:bool; dotenv_read:bool; env_iterated:bool; provider_call_made:bool; network_call_made:bool; browser_session_used:bool; executable_request_artifact_created:bool; endpoint_url_present:bool; webhook_url_present:bool; channel_id_present:bool; account_id_present:bool; token_present:bool; payload_body_present:bool; public_url_created:bool; metrics_created:bool; publication_ready:bool; dispatch_allowed:bool; live_send_allowed:bool; runtime_truth:bool; human_review_required:bool; blockers:list[str]=field(default_factory=list); warnings:list[str]=field(default_factory=list); packet_sha256:str=""

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
    for safe in ("jim_exact_go_for_future_dispatch_gate_only_no_provider_no_dispatch_no_live","jim","exact_operator_go_declaration","exact_operator_dispatch_go","payload_hash_revalidation","approved_payload_hash","approved_payload_preview","symbolic_destination_binding_required_later","symbolic_credential_handle_required_later","credential_handle_membership_proof","destination_binding_proof","dispatch_review_record","outbox_record","redacted_audit","manual_fallback","kill_switch","future_dispatch_execution","no_value","no_provider","no_dispatch","no_live","credential_value_read","credential_value_stored","credential_value_logged","env_read","dotenv_read","env_iterated","env_value_length_checked","env_value_prefix_checked","env_value_suffix_checked","env_value_hash_computed","env_value_digest_computed","env_value_redacted_fragment_created","endpoint_url_present","webhook_url_present","channel_id_present","account_id_present","token_present","payload_body_present","public_url_created","metrics_created","provider_call_made","network_call_made","browser_session_used","executable_request_artifact_created","publication_ready","dispatch_allowed","live_send_allowed","runtime_truth","discord_live_announcements_webhook","telegram_bot_token","telegram_chat_id","substack_manual_export_only","x_manual_export_only","linkedin_org_deferred","tiktok_deferred","local_fixture","fixture"):
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
    if not isinstance(r,dict): return ["payload_hash_revalidation_record_not_object"]
    b+=safety_blockers(r,"payload_hash_revalidation_record")
    _add(b,r.get("schema_version")==SCHEMA_VERSION,"payload_hash_revalidation_record_schema_version_invalid"); _add(b,r.get("payload_hash_revalidation_mode")==UPSTREAM_MODE,"payload_hash_revalidation_record_mode_invalid"); _add(b,r.get("payload_hash_revalidation_status")==UPSTREAM_RECORD_STATUS,"payload_hash_revalidation_record_status_invalid")
    _add(b,r.get("payload_hash_format_valid") is True,"payload_hash_revalidation_record_hash_format_not_true"); _add(b,r.get("payload_hash_revalidated_for_future_exact_operator_dispatch_go_only") is True,"payload_hash_revalidation_record_revalidated_not_true"); _add(b,valid_hash(r.get("approved_payload_hash")),"payload_hash_revalidation_record_approved_payload_hash_invalid")
    _add(b,isinstance(r.get("approved_payload_preview_id"),str) and r.get("approved_payload_preview_id")!="","payload_hash_revalidation_record_approved_payload_preview_id_empty"); _add(b,str(r.get("symbolic_destination_binding_id","")).startswith("symbolic_destination_binding_required_later_"),"payload_hash_revalidation_record_symbolic_destination_binding_id_invalid"); _add(b,str(r.get("symbolic_credential_handle_id","")).startswith("symbolic_credential_handle_required_later_"),"payload_hash_revalidation_record_symbolic_credential_handle_id_invalid"); _add(b,r.get("required_env_key_name") in ALLOWED_REQUIRED_KEY_NAMES,"payload_hash_revalidation_record_key_not_allowlisted")
    for k in FALSE_FLAGS: _add(b,r.get(k,False) is False,f"payload_hash_revalidation_record_{k}_not_false")
    for k in TRUE_RECORD_FLAGS: _add(b,r.get(k) is True,f"payload_hash_revalidation_record_{k}_not_true")
    return b

def validate_upstream_bundle(bundle:Any)->list[str]:
    b=[]
    if not isinstance(bundle,dict): return ["payload_hash_revalidation_gate_bundle_not_object"]
    b+=safety_blockers(bundle,"payload_hash_revalidation_gate_bundle")
    _add(b,bundle.get("schema_version")==SCHEMA_VERSION,"payload_hash_revalidation_gate_bundle_schema_version_invalid"); _add(b,bundle.get("task_label")==UPSTREAM_TASK_LABEL,"payload_hash_revalidation_gate_bundle_task_label_invalid"); _add(b,bundle.get("payload_hash_revalidation_status")==UPSTREAM_STATUS,"payload_hash_revalidation_gate_bundle_status_invalid")
    recs=bundle.get("payload_hash_revalidation_records"); _add(b,isinstance(recs,list) and len(recs)>0,"payload_hash_revalidation_gate_bundle_records_empty"); _add(b,bundle.get("all_required_payload_hash_revalidations_available") is True,"payload_hash_revalidation_gate_bundle_revalidations_not_available"); _add(b,bundle.get("eligible_for_future_exact_operator_dispatch_go_gate_task") is True,"payload_hash_revalidation_gate_bundle_exact_go_eligibility_not_true")
    for k in BUNDLE_FALSE_FLAGS: _add(b,bundle.get(k,False) is False,f"payload_hash_revalidation_gate_bundle_{k}_not_false")
    _add(b,bundle.get("human_review_required") is True,"payload_hash_revalidation_gate_bundle_human_review_required_not_true"); _add(b,bundle.get("blockers") == [],"payload_hash_revalidation_gate_bundle_blockers_not_empty")
    if isinstance(recs,list):
        for i,r in enumerate(recs): b += [f"record_{i}_{x}" for x in validate_upstream_record(r)]
    return b

def expected_sets(bundle:dict[str,Any])->dict[str,list[str]]:
    recs=bundle.get("payload_hash_revalidation_records",[]) if isinstance(bundle,dict) else []
    return {"approved_payload_hashes":_sorted_set(recs,"approved_payload_hash"),"approved_payload_preview_ids":_sorted_set(recs,"approved_payload_preview_id"),"symbolic_destination_binding_ids":_sorted_set(recs,"symbolic_destination_binding_id"),"symbolic_credential_handle_ids":_sorted_set(recs,"symbolic_credential_handle_id"),"required_env_key_names":_sorted_set(recs,"required_env_key_name")}

def validate_operator_declaration(decl:Any,bundle:dict[str,Any])->list[str]:
    b=[]
    if not isinstance(decl,dict): return ["operator_go_declaration_not_object"]
    b+=safety_blockers(decl,"operator_go_declaration")
    _add(b,decl.get("schema_version")==SCHEMA_VERSION,"operator_go_declaration_schema_version_invalid"); _add(b,decl.get("operator_go_phrase")==GO_PHRASE,"operator_go_declaration_phrase_not_exact"); _add(b,isinstance(decl.get("operator_name_or_role"),str) and decl.get("operator_name_or_role")!="","operator_go_declaration_operator_empty"); _add(b,decl.get("approved_task_label")==TASK_LABEL,"operator_go_declaration_approved_task_label_invalid")
    source_id=str(bundle.get("payload_hash_revalidation_gate_bundle_id","") if isinstance(bundle,dict) else ""); _add(b,decl.get("source_payload_hash_revalidation_gate_bundle_id")==source_id,"operator_go_declaration_source_bundle_id_mismatch")
    _add(b,isinstance(decl.get("timestamp_or_fixture_id"),str) and decl.get("timestamp_or_fixture_id")!="","operator_go_declaration_fixture_id_empty"); _add(b,decl.get("human_review_required") is True,"operator_go_declaration_human_review_required_not_true")
    exp=expected_sets(bundle)
    for k,v in exp.items(): _add(b,sorted(decl.get(k,[]) if isinstance(decl.get(k),list) else [])==v,f"operator_go_declaration_{k}_mismatch")
    return b

def make_exact_go_record(r:dict[str,Any],decl_id:str)->dict[str,Any]:
    short=_sha({"decl":decl_id,"record":r.get("payload_hash_revalidation_record_id"),"hash":r.get("approved_payload_hash")})[:16]
    d={"schema_version":SCHEMA_VERSION,"exact_operator_dispatch_go_record_id":f"exact_operator_dispatch_go_record_{short}","source_payload_hash_revalidation_record_id":r.get("payload_hash_revalidation_record_id",""),"platform":r.get("platform",""),"required_env_key_name":r.get("required_env_key_name",""),"approved_payload_preview_id":r.get("approved_payload_preview_id",""),"approved_payload_hash":r.get("approved_payload_hash",""),"symbolic_destination_binding_id":r.get("symbolic_destination_binding_id",""),"symbolic_credential_handle_id":r.get("symbolic_credential_handle_id",""),"operator_go_declaration_id":decl_id,"operator_go_phrase_exact_match":True,"operator_go_gate_mode":GO_MODE,"operator_go_gate_status":GO_STATUS,"eligible_for_future_redacted_audit_kill_switch_manual_fallback_gate_task":True,"human_review_required":True,"blockers":[],"warnings":["exact_operator_go_intent_only","no_provider_network_browser_dispatch_live"]}
    for k in FALSE_FLAGS: d[k]=False
    return d

def make_exact_operator_dispatch_go_gate_bundle(bundle:Any,decl:Any)->ExactOperatorDispatchGoGateBundle:
    blockers=validate_upstream_bundle(bundle); blockers += validate_operator_declaration(decl,bundle if isinstance(bundle,dict) else {})
    source_id=str(bundle.get("payload_hash_revalidation_gate_bundle_id") if isinstance(bundle,dict) else _sha({})[:16]); decl_id=str(decl.get("operator_go_declaration_id") or f"operator_go_declaration_{_sha(decl if isinstance(decl,dict) else {})[:16]}" if isinstance(decl,dict) else "")
    recs=[]
    if not blockers: recs=[make_exact_go_record(r,decl_id) for r in bundle.get("payload_hash_revalidation_records",[])]
    all_ok=bool(recs and not blockers and isinstance(decl,dict) and decl.get("operator_go_phrase")==GO_PHRASE)
    status=GO_STATUS if all_ok else "blocked_invalid_payload_hash_revalidation_or_operator_go_declaration"
    exp=expected_sets(bundle if isinstance(bundle,dict) and all_ok else {})
    data=dict(schema_version=SCHEMA_VERSION,task_label=TASK_LABEL,exact_operator_dispatch_go_gate_bundle_id=f"exact_operator_dispatch_go_gate_bundle_{_sha({'source':source_id,'decl':decl_id,'records':recs,'status':status})[:16]}",source_payload_hash_revalidation_gate_bundle_id=source_id,exact_operator_dispatch_go_gate_status=status,exact_operator_dispatch_go_records=recs,operator_go_declaration_id=decl_id if all_ok else "",operator_go_phrase_exact_match=all_ok,all_required_exact_operator_go_records_available=all_ok,approved_payload_hashes=exp.get("approved_payload_hashes",[]) if all_ok else [],approved_payload_preview_ids=exp.get("approved_payload_preview_ids",[]) if all_ok else [],symbolic_credential_handle_ids=exp.get("symbolic_credential_handle_ids",[]) if all_ok else [],symbolic_destination_binding_ids=exp.get("symbolic_destination_binding_ids",[]) if all_ok else [],proof_available_key_names=exp.get("required_env_key_names",[]) if all_ok else [],proof_missing_key_names=[],eligible_for_future_redacted_audit_kill_switch_manual_fallback_gate_task=all_ok,eligible_for_future_dispatch_execution_task=False,eligible_for_live_send_now=False,credential_value_read=False,credential_value_stored=False,credential_value_logged=False,env_read=False,dotenv_read=False,env_iterated=False,provider_call_made=False,network_call_made=False,browser_session_used=False,executable_request_artifact_created=False,endpoint_url_present=False,webhook_url_present=False,channel_id_present=False,account_id_present=False,token_present=False,payload_body_present=False,public_url_created=False,metrics_created=False,publication_ready=False,dispatch_allowed=False,live_send_allowed=False,runtime_truth=False,human_review_required=True,blockers=blockers,warnings=["local_exact_operator_go_intent_gate_only","no_dispatch_execution_artifact_created","future_redacted_audit_kill_switch_manual_fallback_gate_separate"])
    return ExactOperatorDispatchGoGateBundle(**{**data,"packet_sha256":_packet_sha(data)})

def blocked_bundle(reason:str)->ExactOperatorDispatchGoGateBundle:
    b=make_exact_operator_dispatch_go_gate_bundle({},{}); d=asdict(b); d["blockers"]=[reason]; d["exact_operator_dispatch_go_gate_status"]="blocked_invalid_payload_hash_revalidation_or_operator_go_declaration"; d["packet_sha256"]=_packet_sha(d); return ExactOperatorDispatchGoGateBundle(**d)
def load_json_object(path:str|Path)->dict[str,Any]:
    try: data=json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc: raise ValueError("malformed_json") from exc
    if not isinstance(data,dict): raise ValueError("json_not_object")
    return data
def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description="V6 exact operator dispatch GO gate CLI"); parser.add_argument("--payload-hash-revalidation-gate-bundle",required=True); parser.add_argument("--operator-go-declaration",required=True); parser.add_argument("--output",required=True); args=parser.parse_args(argv)
    try: packet=make_exact_operator_dispatch_go_gate_bundle(load_json_object(args.payload_hash_revalidation_gate_bundle),load_json_object(args.operator_go_declaration))
    except ValueError as exc: packet=blocked_bundle(str(exc))
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(asdict(packet),indent=2,sort_keys=True),encoding="utf-8")
    return 0 if packet.eligible_for_future_redacted_audit_kill_switch_manual_fallback_gate_task else 1
if __name__=="__main__":
    import sys; sys.exit(main())
