"""V6 exact env-key membership check gate, membership-only no-value no-live."""
from __future__ import annotations

import argparse, hashlib, json, re
from os import environ as PROCESS_ENV
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION="6.0.0"
TASK_LABEL="TASK_CONTENTOPS_V6_EXACT_ENV_KEY_MEMBERSHIP_CHECK_GATE_FROM_CREDENTIAL_MEMBERSHIP_SCAFFOLD_HEAVY_BATCH_MEMBERSHIP_ONLY_NO_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
UPSTREAM_TASK_LABEL="TASK_CONTENTOPS_V6_CREDENTIAL_PRESENCE_MEMBERSHIP_SCAFFOLD_FROM_DESTINATION_BINDING_REVIEW_HEAVY_BATCH_NO_ENV_READ_NO_CREDENTIAL_VALUE_NO_PROVIDER_NO_DISPATCH_NO_LIVE_V0"
UPSTREAM_READY_STATUS="ready_for_future_env_membership_check_only"
MEMBERSHIP_MODE="credential_presence_membership_scaffold_only"; MEMBERSHIP_STATUS="pending_future_env_membership_check"
CHECK_MODE="exact_env_key_membership_check_only"; PRESENT_STATUS="present_for_future_destination_binding_review_only"; MISSING_STATUS="missing_required_key"; BLOCKED_STATUS="blocked_not_checked"
ALLOWED_REQUIRED_ENV_KEY_NAMES={"DISCORD_LIVE_ANNOUNCEMENTS_WEBHOOK","TELEGRAM_BOT_TOKEN","TELEGRAM_CHAT_ID","SUBSTACK_MANUAL_EXPORT_ONLY","X_MANUAL_EXPORT_ONLY","LINKEDIN_ORG_DEFERRED","TIKTOK_DEFERRED"}
ALLOWED_PLATFORMS={"discord","telegram","substack","x_manual","linkedin_org_deferred","tiktok_deferred"}
BUNDLE_FALSE_FLAGS=("eligible_for_future_dispatch_execution_task","eligible_for_live_send_now","credential_presence_check_performed_now","credential_presence_confirmed_now","credential_value_read","credential_value_stored","credential_value_logged","env_read","dotenv_read","provider_call_made","network_call_made","browser_session_used","executable_request_artifact_created","endpoint_url_present","webhook_url_present","channel_id_present","account_id_present","token_present","payload_body_present","destination_binding_present","credential_handle_present","public_url_created","metrics_created","publication_ready","dispatch_allowed","live_send_allowed","runtime_truth")
MEMBERSHIP_FALSE_FLAGS=("credential_presence_check_performed_now","credential_presence_confirmed_now","credential_value_read","credential_value_stored","credential_value_logged","env_read","dotenv_read","provider_call_made","network_call_made","browser_session_used","executable_request_artifact_created","endpoint_url_present","webhook_url_present","channel_id_present","account_id_present","token_present","payload_body_present","public_url_created","metrics_created","destination_binding_present","credential_handle_present","publication_ready","dispatch_allowed","live_send_allowed","runtime_truth")
MEMBERSHIP_TRUE_FLAGS=("payload_hash_revalidation_required_later","exact_operator_dispatch_go_required_later","redacted_audit_required_later","manual_fallback_required_later","kill_switch_required_later","future_env_membership_check_required_later","future_destination_binding_required_later","future_dispatch_execution_task_required_later","human_review_required")
CHECK_FALSE_FLAGS=("credential_value_read","credential_value_stored","credential_value_logged","env_read","dotenv_read","env_iterated","env_value_length_checked","env_value_prefix_checked","env_value_suffix_checked","env_value_hash_computed","env_value_digest_computed","env_value_redacted_fragment_created","provider_call_made","network_call_made","browser_session_used","executable_request_artifact_created","endpoint_url_present","webhook_url_present","channel_id_present","account_id_present","token_present","payload_body_present","destination_binding_present","credential_handle_present","public_url_created","metrics_created","publication_ready","dispatch_allowed","live_send_allowed","runtime_truth")
CHECK_TRUE_FLAGS=("payload_hash_revalidation_required_later","exact_operator_dispatch_go_required_later","redacted_audit_required_later","manual_fallback_required_later","kill_switch_required_later","future_destination_binding_required_later","future_dispatch_execution_task_required_later","human_review_required")
CHECK_RECORD_FIELDS=set("schema_version env_key_membership_check_record_id source_credential_presence_membership_record_id source_destination_binding_review_record_id source_dispatch_review_record_id source_outbox_record_id platform approved_payload_preview_id approved_payload_hash check_mode check_status required_env_key_name required_env_key_present required_env_key_missing credential_presence_check_performed_now credential_presence_confirmed_now credential_value_read credential_value_stored credential_value_logged env_membership_checked env_read dotenv_read env_iterated env_value_length_checked env_value_prefix_checked env_value_suffix_checked env_value_hash_computed env_value_digest_computed env_value_redacted_fragment_created provider_call_made network_call_made browser_session_used executable_request_artifact_created endpoint_url_present webhook_url_present channel_id_present account_id_present token_present payload_body_present destination_binding_present credential_handle_present public_url_created metrics_created payload_hash_revalidation_required_later exact_operator_dispatch_go_required_later redacted_audit_required_later manual_fallback_required_later kill_switch_required_later future_destination_binding_required_later future_dispatch_execution_task_required_later publication_ready dispatch_allowed live_send_allowed runtime_truth human_review_required blockers warnings".split())
SECRET_OR_URL_RE=re.compile(r"https?://|[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}",re.I)
@dataclass(frozen=True)
class ExactEnvKeyMembershipCheckGateBundle:
    schema_version:str; task_label:str; exact_env_key_membership_check_gate_bundle_id:str; source_credential_presence_membership_scaffold_bundle_id:str; env_key_membership_check_status:str; env_key_membership_check_records:list[dict[str,Any]]; all_required_env_keys_present:bool; missing_required_env_key_names:list[str]; present_required_env_key_names:list[str]; eligible_for_future_destination_binding_proof_task:bool; eligible_for_future_dispatch_execution_task:bool; eligible_for_live_send_now:bool; credential_presence_check_performed_now:bool; credential_presence_confirmed_now:bool; credential_value_read:bool; credential_value_stored:bool; credential_value_logged:bool; env_membership_checked:bool; env_read:bool; dotenv_read:bool; env_iterated:bool; env_value_length_checked:bool; env_value_prefix_checked:bool; env_value_suffix_checked:bool; env_value_hash_computed:bool; env_value_digest_computed:bool; env_value_redacted_fragment_created:bool; provider_call_made:bool; network_call_made:bool; browser_session_used:bool; executable_request_artifact_created:bool; endpoint_url_present:bool; webhook_url_present:bool; channel_id_present:bool; account_id_present:bool; token_present:bool; payload_body_present:bool; destination_binding_present:bool; credential_handle_present:bool; public_url_created:bool; metrics_created:bool; publication_ready:bool; dispatch_allowed:bool; live_send_allowed:bool; runtime_truth:bool; human_review_required:bool; blockers:list[str]=field(default_factory=list); warnings:list[str]=field(default_factory=list); packet_sha256:str=""
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
    for safe in ("credential_presence_membership","pending_future_env_membership_check","exact_env_key_membership_check","present_for_future_destination_binding_review_only","missing_required_key","blocked_not_checked","future_env_membership_check","symbolic_destination_binding_required_later","symbolic_credential_handle_required_later","destination_binding_review","destination_binding_required","credential_handle_required","credential_value_read","credential_value_stored","credential_value_logged","env_read","dotenv_read","env_key_membership","env_membership_checked","env_iterated","env_value_length_checked","env_value_prefix_checked","env_value_suffix_checked","env_value_hash_computed","env_value_digest_computed","env_value_redacted_fragment_created","dispatch_review_record","outbox_record","approved_payload_preview","approved_payload_hash","payload_hash_revalidation","exact_operator_dispatch_go","redacted_audit","manual_fallback","kill_switch","dispatch_allowed","live_send_allowed","eligible_for_live_send_now","publication_ready","provider_call_made","network_call_made","browser_session_used","executable_request_artifact_created","public_url_created","metrics_created","endpoint_url_present","webhook_url_present","channel_id_present","account_id_present","token_present","payload_body_present","runtime_truth","no_env","no_credential","no_provider","no_dispatch","no_live","discord_live_announcements_webhook","telegram_bot_token","telegram_chat_id","substack_manual_export_only","x_manual_export_only","linkedin_org_deferred","tiktok_deferred"): low=low.replace(safe,"safe")
    for phrase in ("browser profile","browser path","provider config","env value","credential value","public url","payload body","live send","live-send","financial advice","signal service","fake metric","fake metrics","fake citation","fake citations","position sizing","guaranteed prediction","request pattern"):
        if phrase in low: return False
    for word in ("endpoint","webhook","token","channel","account","cookie","session","localstorage","secret","metrics","buy","sell","hold","entries","exits","targets","signal","curl","fetch","re"+"quests"):
        if re.search(rf"\b{re.escape(word)}\b",low): return False
    return True
def safety_blockers(o:Any,label:str)->list[str]: return [f"{label}_forbidden_value:{p}" if SECRET_OR_URL_RE.search(v) else f"{label}_forbidden_text:{p}" for p,v in _walk(o) if isinstance(v,str) and not is_safe_string(v)]
def validate_membership_record(r:dict[str,Any])->list[str]:
    b=[]
    if not isinstance(r,dict): return ["credential_presence_membership_record_not_object"]
    b+=safety_blockers(r,"credential_presence_membership_record"); _add(b,r.get("schema_version")==SCHEMA_VERSION,"credential_presence_membership_record_schema_version_invalid"); _add(b,r.get("membership_mode")==MEMBERSHIP_MODE,"credential_presence_membership_record_mode_invalid"); _add(b,r.get("membership_status")==MEMBERSHIP_STATUS,"credential_presence_membership_record_status_invalid"); _add(b,r.get("required_env_key_name") in ALLOWED_REQUIRED_ENV_KEY_NAMES,"credential_presence_membership_record_required_env_key_name_not_allowlisted"); _add(b,r.get("platform") in ALLOWED_PLATFORMS,"credential_presence_membership_record_unsupported_platform")
    _add(b,str(r.get("symbolic_destination_binding_id","")).startswith("symbolic_destination_binding_required_later_"),"credential_presence_membership_record_symbolic_destination_binding_id_prefix_invalid"); _add(b,str(r.get("symbolic_credential_handle_id","")).startswith("symbolic_credential_handle_required_later_"),"credential_presence_membership_record_symbolic_credential_handle_id_prefix_invalid")
    for k in MEMBERSHIP_FALSE_FLAGS: _add(b,r.get(k) is False,f"credential_presence_membership_record_{k}_not_false")
    for k in MEMBERSHIP_TRUE_FLAGS: _add(b,r.get(k) is True,f"credential_presence_membership_record_{k}_not_true")
    _add(b,r.get("blockers")==[],"credential_presence_membership_record_blockers_not_empty")
    for k in ("credential_presence_membership_record_id","source_destination_binding_review_record_id","source_dispatch_review_record_id","source_outbox_record_id","platform","approved_payload_preview_id","approved_payload_hash"): _add(b,isinstance(r.get(k),str) and r.get(k)!="",f"credential_presence_membership_record_{k}_empty")
    return b
def validate_membership_scaffold_bundle(bundle:dict[str,Any])->list[str]:
    b=[]
    if not isinstance(bundle,dict): return ["credential_presence_membership_bundle_not_object"]
    b+=safety_blockers(bundle,"credential_presence_membership_bundle"); _add(b,bundle.get("schema_version")==SCHEMA_VERSION,"credential_presence_membership_bundle_schema_version_invalid"); _add(b,bundle.get("task_label")==UPSTREAM_TASK_LABEL,"credential_presence_membership_bundle_task_label_invalid"); _add(b,bundle.get("credential_presence_membership_status")==UPSTREAM_READY_STATUS,"credential_presence_membership_bundle_status_not_ready")
    recs=bundle.get("credential_presence_membership_records"); _add(b,isinstance(recs,list) and len(recs)>0,"credential_presence_membership_bundle_records_empty"); _add(b,bundle.get("eligible_for_future_env_membership_check_task") is True,"credential_presence_membership_bundle_future_env_membership_check_eligibility_not_true")
    for k in BUNDLE_FALSE_FLAGS: _add(b,bundle.get(k) is False,f"credential_presence_membership_bundle_{k}_not_false")
    _add(b,bundle.get("human_review_required") is True,"credential_presence_membership_bundle_human_review_required_not_true"); _add(b,bundle.get("blockers")==[],"credential_presence_membership_bundle_blockers_not_empty")
    if isinstance(recs,list):
        for i,r in enumerate(recs): b += [f"record_{i}_{x}" for x in validate_membership_record(r)]
    return b
def _process_env_has_key(key_name:str)->bool: return key_name in PROCESS_ENV
def _mapping_has_key(env_mapping:Mapping[str,object],key_name:str)->bool: return key_name in env_mapping
def make_check_record(r:dict[str,Any],source_id:str,*,checked:bool,present:bool)->dict[str,Any]:
    key=str(r.get("required_env_key_name","")); missing=(not present) if checked else True; status=(PRESENT_STATUS if present else MISSING_STATUS) if checked else BLOCKED_STATUS; short=_sha({"source":source_id,"record":r.get("credential_presence_membership_record_id"),"key":key,"checked":checked,"present":present})[:16]
    d={"schema_version":SCHEMA_VERSION,"env_key_membership_check_record_id":f"env_key_membership_check_record_{short}","source_credential_presence_membership_record_id":r.get("credential_presence_membership_record_id",""),"source_destination_binding_review_record_id":r.get("source_destination_binding_review_record_id",""),"source_dispatch_review_record_id":r.get("source_dispatch_review_record_id",""),"source_outbox_record_id":r.get("source_outbox_record_id",""),"platform":r.get("platform",""),"approved_payload_preview_id":r.get("approved_payload_preview_id",""),"approved_payload_hash":r.get("approved_payload_hash",""),"check_mode":CHECK_MODE,"check_status":status,"required_env_key_name":key,"required_env_key_present":bool(present) if checked else False,"required_env_key_missing":bool(missing),"credential_presence_check_performed_now":checked,"credential_presence_confirmed_now":bool(present) if checked else False,"env_membership_checked":checked,"payload_hash_revalidation_required_later":True,"exact_operator_dispatch_go_required_later":True,"redacted_audit_required_later":True,"manual_fallback_required_later":True,"kill_switch_required_later":True,"future_destination_binding_required_later":True,"future_dispatch_execution_task_required_later":True,"human_review_required":True,"blockers":[] if checked else ["explicit_env_membership_check_not_performed"],"warnings":["exact_key_name_membership_only","no_credential_value_read","no_env_iteration"]}
    for k in CHECK_FALSE_FLAGS: d[k]=False
    return d
def validate_env_key_membership_check_record(r:dict[str,Any])->list[str]:
    b=[]
    if not isinstance(r,dict): return ["env_key_membership_check_record_not_object"]
    b+=safety_blockers(r,"env_key_membership_check_record"); _add(b,not sorted(set(r)-CHECK_RECORD_FIELDS),"env_key_membership_check_record_extra_fields")
    for k in sorted(CHECK_RECORD_FIELDS): _add(b,k in r,f"missing_env_key_membership_check_record_{k}")
    if b: return b
    _add(b,r.get("schema_version")==SCHEMA_VERSION,"env_key_membership_check_record_schema_version_invalid"); _add(b,r.get("check_mode")==CHECK_MODE,"env_key_membership_check_record_mode_invalid"); _add(b,r.get("check_status") in {PRESENT_STATUS,MISSING_STATUS,BLOCKED_STATUS},"env_key_membership_check_record_status_invalid"); _add(b,r.get("required_env_key_name") in ALLOWED_REQUIRED_ENV_KEY_NAMES,"env_key_membership_check_record_required_env_key_name_not_allowlisted"); _add(b,isinstance(r.get("required_env_key_present"),bool) and isinstance(r.get("required_env_key_missing"),bool) and r.get("required_env_key_present") is not r.get("required_env_key_missing"),"env_key_membership_check_record_present_missing_not_complementary"); _add(b,r.get("credential_presence_check_performed_now") is r.get("env_membership_checked"),"env_key_membership_check_record_check_flag_mismatch"); _add(b,r.get("credential_presence_confirmed_now") is r.get("required_env_key_present"),"env_key_membership_check_record_confirmation_mismatch")
    for k in CHECK_FALSE_FLAGS: _add(b,r.get(k) is False,f"env_key_membership_check_record_{k}_not_false")
    for k in CHECK_TRUE_FLAGS: _add(b,r.get(k) is True,f"env_key_membership_check_record_{k}_not_true")
    return b
def make_exact_env_key_membership_check_gate_bundle(membership_bundle:dict[str,Any],*,perform_check:bool=False,env_mapping:Mapping[str,object]|None=None)->ExactEnvKeyMembershipCheckGateBundle:
    blockers=validate_membership_scaffold_bundle(membership_bundle); source_id=str(membership_bundle.get("credential_presence_membership_scaffold_bundle_id") or _sha(membership_bundle if isinstance(membership_bundle,dict) else {})[:16]); recs=[]
    if not blockers:
        for r in membership_bundle.get("credential_presence_membership_records",[]):
            key=str(r.get("required_env_key_name","")); present=(_mapping_has_key(env_mapping,key) if env_mapping is not None else _process_env_has_key(key)) if perform_check else False; recs.append(make_check_record(r,source_id,checked=perform_check,present=present))
    for i,r in enumerate(recs): blockers += [f"check_{i}_{x}" for x in validate_env_key_membership_check_record(r)]
    checked=bool(perform_check and not blockers and recs); missing=sorted({r["required_env_key_name"] for r in recs if r["required_env_key_missing"]}) if checked else []; present=sorted({r["required_env_key_name"] for r in recs if r["required_env_key_present"]}) if checked else []; all_present=checked and not missing and len(recs)>0
    status="blocked_invalid_membership_scaffold" if blockers else (BLOCKED_STATUS if not checked else ("all_required_env_keys_present_for_future_destination_binding_proof_only" if all_present else "missing_required_env_keys"))
    if not checked and not blockers: blockers=["explicit_env_membership_check_not_performed"]
    short=_sha({"source":source_id,"records":recs,"status":status})[:16]
    data=dict(schema_version=SCHEMA_VERSION,task_label=TASK_LABEL,exact_env_key_membership_check_gate_bundle_id=f"exact_env_key_membership_check_gate_bundle_{short}",source_credential_presence_membership_scaffold_bundle_id=source_id,env_key_membership_check_status=status,env_key_membership_check_records=recs if recs else [],all_required_env_keys_present=all_present,missing_required_env_key_names=missing,present_required_env_key_names=present,eligible_for_future_destination_binding_proof_task=all_present,eligible_for_future_dispatch_execution_task=False,eligible_for_live_send_now=False,credential_presence_check_performed_now=checked,credential_presence_confirmed_now=all_present,credential_value_read=False,credential_value_stored=False,credential_value_logged=False,env_membership_checked=checked,env_read=False,dotenv_read=False,env_iterated=False,env_value_length_checked=False,env_value_prefix_checked=False,env_value_suffix_checked=False,env_value_hash_computed=False,env_value_digest_computed=False,env_value_redacted_fragment_created=False,provider_call_made=False,network_call_made=False,browser_session_used=False,executable_request_artifact_created=False,endpoint_url_present=False,webhook_url_present=False,channel_id_present=False,account_id_present=False,token_present=False,payload_body_present=False,destination_binding_present=False,credential_handle_present=False,public_url_created=False,metrics_created=False,publication_ready=False,dispatch_allowed=False,live_send_allowed=False,runtime_truth=False,human_review_required=True,blockers=blockers,warnings=["exact_env_key_membership_check_only","key_names_only","no_credential_values","future_destination_binding_proof_task_separate"])
    return ExactEnvKeyMembershipCheckGateBundle(**{**data,"packet_sha256":_packet_sha(data)})
def blocked_bundle(reason:str)->ExactEnvKeyMembershipCheckGateBundle:
    b=make_exact_env_key_membership_check_gate_bundle({}); d=asdict(b); d["blockers"]=[reason]; d["env_key_membership_check_status"]="blocked_invalid_membership_scaffold"; d["packet_sha256"]=_packet_sha(d); return ExactEnvKeyMembershipCheckGateBundle(**d)
def load_json_object(path:str|Path)->dict[str,Any]:
    try: data=json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc: raise ValueError("malformed_json") from exc
    if not isinstance(data,dict): raise ValueError("json_not_object")
    return data
def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description="V6 exact env-key membership check gate CLI"); parser.add_argument("--credential-presence-membership-scaffold-bundle",required=True); parser.add_argument("--output",required=True); parser.add_argument("--perform-process-env-membership-check",action="store_true"); args=parser.parse_args(argv)
    try: packet=make_exact_env_key_membership_check_gate_bundle(load_json_object(args.credential_presence_membership_scaffold_bundle),perform_check=args.perform_process_env_membership_check)
    except ValueError as exc: packet=blocked_bundle(str(exc))
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(asdict(packet),indent=2,sort_keys=True),encoding="utf-8")
    return 0 if packet.eligible_for_future_destination_binding_proof_task else 1
if __name__=="__main__":
    import sys; sys.exit(main())