"""Content performance review + editorial feedback loop contract, 0174UD.

Deterministic local-only review of operator-attested manual metrics. No API,
provider, network, env, credential, scraping, scheduler, browser, DM, approval,
dispatch, public-post, current-truth, DQR, readiness, or ingestion mutation.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any
from live_contentops import manual_publish_record_metrics_ledger_contract as uc
from live_contentops import redacted_immutable_audit_ledger_v2_contract as audit
TASK_LABEL="TASK_CONTENTOPS_0174UD_CONTENT_PERFORMANCE_REVIEW_AND_EDITORIAL_FEEDBACK_LOOP_CONTRACT_V0"
MODEL_VERSION="0174UD_CONTENT_PERFORMANCE_REVIEW_EDITORIAL_FEEDBACK_CONTRACT_V1"
SOURCE_BASELINE_COMMIT="5c5e7b3d038f8c012b4275ef3056fd8636c6f51f"
DOC_REL_DIR=Path("docs")/"automation"/"0174UD"
PACKET_FILENAME="content_performance_review_editorial_feedback_contract_packet.json"
RUNBOOK_FILENAME="content_performance_review_editorial_feedback_contract.md"
HASH_ALGORITHM="sha256"
NEXT_HEAVY_BATCH="TASK_CONTENTOPS_0174UE_LOCAL_CONTENT_GOVERNANCE_SUMMARY_MART_CONTRACT_V0"
VALID="content_performance_validation_passed_review_only"
BLOCKED="blocked"
REVIEW_STATUS="review_only_feedback_recorded"
NUMERIC=uc.NUMERIC_METRIC_KEYS
BLOCKERS={"hash":"performance_metrics_payload_hash_mismatch","platform":"performance_metrics_platform_mismatch","negative":"performance_negative_metrics_blocked","time":"performance_metric_time_order_invalid","future":"performance_future_api_import_blocked","api":"performance_api_verified_metrics_blocked","scraped":"performance_scraped_metrics_blocked","attest":"performance_metrics_not_operator_attested","publish":"performance_publish_record_not_bound","claim":"public_performance_claim_blocked","live":"live_behavior_blocked"}
@dataclass(frozen=True)
class ContentPerformanceReviewPacket: performance_review_id:str; source_manual_publish_record_id:str; source_manual_metrics_record_id:str; source_payload_hash:str; platform_id:str; payload_class_id:str; content_lane:str; reviewed_at_epoch:int; operator_identity_ref:str; metric_snapshot:dict[str,Any]; metric_quality_class:str; performance_summary:str; performance_interpretation_class:str; confidence_class:str; public_claim_authorized:bool; can_create_editorial_feedback:bool; can_create_content_idea:bool; can_create_approval:bool; can_dispatch:bool; evidence_refs:tuple[str,...]; safety_flags:dict[str,bool]; blocked_reasons:tuple[str,...]
@dataclass(frozen=True)
class EditorialFeedbackSignal: editorial_feedback_signal_id:str; source_performance_review_id:str; source_payload_hash:str; platform_id:str; payload_class_id:str; feedback_class:str; feedback_summary:str; recommended_future_action_class:str; editorial_constraints:tuple[str,...]; required_human_review:bool; can_update_writer_guidance:bool; can_update_platform_defaults:bool; can_auto_generate_content:bool; can_auto_publish:bool; can_dispatch:bool; public_postable:bool; evidence_refs:tuple[str,...]; safety_flags:dict[str,bool]; blocked_reasons:tuple[str,...]
@dataclass(frozen=True)
class EditorialFeedbackLoopPacket: feedback_loop_packet_id:str; source_performance_review_ids:tuple[str,...]; source_feedback_signal_ids:tuple[str,...]; candidate_next_idea_seed_refs:tuple[str,...]; writer_guidance_note:str; platform_guidance_notes:dict[str,str]; feedback_loop_status:str; can_create_content_idea_candidate:bool; can_create_editorial_brief_candidate:bool; can_update_writer_guidance:bool; can_update_platform_defaults:bool; can_approve:bool; can_dispatch:bool; public_postable:bool; evidence_refs:tuple[str,...]; safety_flags:dict[str,bool]; blocked_reasons:tuple[str,...]
@dataclass(frozen=True)
class ContentPerformanceValidationResult: validation_id:str; source_performance_review_id:str; source_feedback_loop_packet_id:str; metrics_operator_attested:bool; metrics_not_api_verified:bool; metrics_not_scraped:bool; metrics_non_negative:bool; metric_time_order_valid:bool; publish_record_bound:bool; payload_hash_match:bool; platform_match:bool; no_public_claim:bool; no_auto_generation:bool; no_auto_publish:bool; no_dispatch:bool; no_live_behavior:bool; validation_status:str; blocked_reasons:tuple[str,...]; evidence_refs:tuple[str,...]; safety_flags:dict[str,bool]
@dataclass(frozen=True)
class ContentPerformanceReviewLedgerPacket: packet_id:str; performance_reviews:tuple[ContentPerformanceReviewPacket,...]; feedback_signals:tuple[EditorialFeedbackSignal,...]; feedback_loop_packets:tuple[EditorialFeedbackLoopPacket,...]; validation_results:tuple[ContentPerformanceValidationResult,...]; audit_ledger_entries:tuple[audit.RedactedAuditLedgerEntry,...]; packet_hash:str; packet_hash_algorithm:str; all_records_redacted:bool; all_feedback_review_only:bool; no_api_verification:bool; no_scraping:bool; no_auto_generation:bool; no_auto_publish:bool; no_dispatch:bool; no_public_claim_authorized:bool; evidence_refs:tuple[str,...]; safety_flags:dict[str,bool]; blocked_reasons:tuple[str,...]; next_required_gate:str
def _asdict(v:Any)->Any:
    if hasattr(v,"__dataclass_fields__"): return asdict(v)
    if isinstance(v,tuple): return [_asdict(x) for x in v]
    if isinstance(v,list): return [_asdict(x) for x in v]
    if isinstance(v,dict): return {str(k):_asdict(x) for k,x in v.items()}
    return v
def _json(v:Any)->str: return json.dumps(_asdict(v),ensure_ascii=False,sort_keys=True,separators=(",",":"))+"\n"
def _digest(v:Any)->str: return sha256(_json(v).encode()).hexdigest()
def _unique(v)->tuple[str,...]: return tuple(dict.fromkeys(str(x) for x in v if x))
def safety_flags()->dict[str,bool]:
    false=("metrics_api_verified","metrics_scraped","can_auto_generate_content","can_auto_publish","can_dispatch","dispatch_ready","public_postable","public_claim_authorized","approval_granted","live_dispatch_enabled","platform_api_called","telegram_api_called","provider_api_called","llm_provider_called","credential_hydrated","env_read","network_performed","scheduler_enabled","autonomous_posting_allowed","scraping_performed","dm_or_reply_automation_allowed","browser_session_used","current_truth_promoted","dqr_cleared","readiness_cleared","ingestion_repo_mutated")
    return {**{k:False for k in false},"manual_metrics_only":True,"operator_attested_only":True,"no_public_performance_claim":True}
def _valid_metrics(m:uc.ManualMetricsRecord,p:uc.ManualPublishRecord)->tuple[bool,tuple[str,...]]:
    b=list(m.blocked_reasons); checks=[m.source_manual_publish_record_id==p.manual_publish_record_id,m.source_payload_hash==p.source_payload_hash,m.platform_id==p.platform_id,uc._non_negative_metrics(m.metrics),m.metric_observed_at_epoch>=p.manually_published_at_epoch and m.metric_recorded_at_epoch>=m.metric_observed_at_epoch,m.metric_values_are_operator_attested,m.metric_values_are_api_verified is False,m.metric_values_are_scraped is False,m.metric_source_class!=uc.METRIC_SOURCE_FUTURE_API_BLOCKED]
    for ok,key in zip(checks,("publish","hash","platform","negative","time","attest","api","scraped","future")):
        if not ok: b.append(BLOCKERS[key])
    return all(checks) and not _unique(b),_unique(b)
def build_performance_review(publish_record:uc.ManualPublishRecord, metrics_record:uc.ManualMetricsRecord, *, content_lane:str="pre_alpha_general_process", reviewed_at_epoch:int=1600)->ContentPerformanceReviewPacket:
    valid,blocked=_valid_metrics(metrics_record,publish_record); metric_count=sum(1 for k in NUMERIC if metrics_record.metrics.get(k) not in (None,"")); incomplete=metric_count<3
    quality="operator_attested_only" if valid and not incomplete else ("incomplete_manual_snapshot" if valid else "unknown_or_blocked")
    interp="useful_learning_signal" if valid and not incomplete else ("needs_more_manual_observations" if valid else "blocked_metrics_invalid")
    conf="medium_manual_consistent" if valid and not incomplete else ("low_manual_only" if valid else "blocked")
    material={"publish":publish_record.manual_publish_record_id,"metrics":metrics_record.manual_metrics_record_id,"blocked":blocked,"quality":quality,"interp":interp}
    return ContentPerformanceReviewPacket("performance_review_"+_digest(material)[:24],publish_record.manual_publish_record_id,metrics_record.manual_metrics_record_id,publish_record.source_payload_hash,publish_record.platform_id,publish_record.payload_class_id,content_lane,int(reviewed_at_epoch),metrics_record.operator_identity_ref,dict(metrics_record.metrics),quality,"Manual metrics reviewed as operator-attested local evidence only; no public performance truth created.",interp,conf,False,valid,valid,False,False,_unique(tuple(publish_record.evidence_refs)+tuple(metrics_record.evidence_refs)+(f"{DOC_REL_DIR.as_posix()}/{RUNBOOK_FILENAME}",)),safety_flags(),blocked)
def build_feedback_signal(review:ContentPerformanceReviewPacket)->EditorialFeedbackSignal:
    valid=not review.blocked_reasons and review.can_create_editorial_feedback
    fc="hook_learning" if valid and review.performance_interpretation_class=="useful_learning_signal" else ("insufficient_data_hold" if not review.blocked_reasons else "blocked_invalid_metrics")
    action="create_new_content_idea_candidate" if valid else ("collect_more_manual_metrics" if not review.blocked_reasons else "blocked_no_action")
    constraints=("Use manual metrics as bounded future-learning input only.","Do not claim platform performance truth.","Human review required before any future brief.")
    material={"review":review.performance_review_id,"fc":fc,"action":action}
    return EditorialFeedbackSignal("editorial_feedback_signal_"+_digest(material)[:24],review.performance_review_id,review.source_payload_hash,review.platform_id,review.payload_class_id,fc,"Review-only editorial feedback derived from manual metrics.",action,constraints,True,valid,False,False,False,False,False,review.evidence_refs,safety_flags(),review.blocked_reasons)
def build_feedback_loop_packet(reviews:tuple[ContentPerformanceReviewPacket,...], signals:tuple[EditorialFeedbackSignal,...])->EditorialFeedbackLoopPacket:
    blocked=_unique(tuple(b for r in reviews for b in r.blocked_reasons)+tuple(b for s in signals for b in s.blocked_reasons)); valid=bool(reviews and signals) and not blocked and all(s.recommended_future_action_class!="blocked_no_action" for s in signals)
    status=REVIEW_STATUS if valid else ("blocked_invalid_metrics" if blocked else "blocked_insufficient_evidence")
    seeds=tuple("idea_seed_from_"+s.editorial_feedback_signal_id for s in signals if valid and s.recommended_future_action_class=="create_new_content_idea_candidate")
    material={"reviews":[r.performance_review_id for r in reviews],"signals":[s.editorial_feedback_signal_id for s in signals],"status":status}
    refs=_unique(tuple(x for r in reviews for x in r.evidence_refs)+tuple(x for s in signals for x in s.evidence_refs))
    return EditorialFeedbackLoopPacket("feedback_loop_packet_"+_digest(material)[:24],tuple(r.performance_review_id for r in reviews),tuple(s.editorial_feedback_signal_id for s in signals),seeds,"Review-only future writer guidance candidate; no automatic generation or publication.",{s.platform_id:"Preserve observation as bounded future guidance." for s in signals},status,valid,valid,valid,False,False,False,False,refs,safety_flags(),blocked)
def validate_content_performance(review:ContentPerformanceReviewPacket, loop:EditorialFeedbackLoopPacket, publish_record:uc.ManualPublishRecord, metrics_record:uc.ManualMetricsRecord)->ContentPerformanceValidationResult:
    nonneg=uc._non_negative_metrics(metrics_record.metrics); timeok=metrics_record.metric_observed_at_epoch>=publish_record.manually_published_at_epoch and metrics_record.metric_recorded_at_epoch>=metrics_record.metric_observed_at_epoch
    checks={"metrics_operator_attested":metrics_record.metric_values_are_operator_attested,"metrics_not_api_verified":not metrics_record.metric_values_are_api_verified,"metrics_not_scraped":not metrics_record.metric_values_are_scraped,"metrics_non_negative":nonneg,"metric_time_order_valid":timeok,"publish_record_bound":metrics_record.source_manual_publish_record_id==publish_record.manual_publish_record_id,"payload_hash_match":metrics_record.source_payload_hash==publish_record.source_payload_hash,"platform_match":metrics_record.platform_id==publish_record.platform_id,"no_public_claim":not review.public_claim_authorized,"no_auto_generation":not any(safety_flags()[k] for k in ("can_auto_generate_content",)),"no_auto_publish":True,"no_dispatch":not loop.can_dispatch,"no_live_behavior":not any(safety_flags()[k] for k in ("platform_api_called","telegram_api_called","provider_api_called","llm_provider_called","env_read","network_performed","scheduler_enabled","scraping_performed","browser_session_used"))}
    blocked=_unique(tuple(review.blocked_reasons)+tuple(loop.blocked_reasons)+tuple(k for k,v in checks.items() if not v)); status=VALID if not blocked and all(checks.values()) else BLOCKED
    return ContentPerformanceValidationResult("content_performance_validation_"+_digest({"review":review.performance_review_id,"loop":loop.feedback_loop_packet_id,"blocked":blocked})[:24],review.performance_review_id,loop.feedback_loop_packet_id,checks["metrics_operator_attested"],checks["metrics_not_api_verified"],checks["metrics_not_scraped"],nonneg,timeok,checks["publish_record_bound"],checks["payload_hash_match"],checks["platform_match"],checks["no_public_claim"],checks["no_auto_generation"],checks["no_auto_publish"],checks["no_dispatch"],checks["no_live_behavior"],status,blocked,_unique(tuple(review.evidence_refs)+tuple(loop.evidence_refs)),safety_flags())
def _audit_entries(review,signal,loop):
    a=audit.build_redacted_ledger_entry(entry_sequence=1,previous_entry_hash=audit.GENESIS_HASH,entry_family="content_performance_review",source_model="0174UD",source_model_version=MODEL_VERSION,payload=_asdict(review),created_at_epoch=review.reviewed_at_epoch)
    b=audit.build_redacted_ledger_entry(entry_sequence=2,previous_entry_hash=a.entry_hash,entry_family="editorial_feedback_signal",source_model="0174UD",source_model_version=MODEL_VERSION,payload=_asdict(signal),created_at_epoch=review.reviewed_at_epoch+1)
    c=audit.build_redacted_ledger_entry(entry_sequence=3,previous_entry_hash=b.entry_hash,entry_family="editorial_feedback_loop",source_model="0174UD",source_model_version=MODEL_VERSION,payload=_asdict(loop),created_at_epoch=review.reviewed_at_epoch+2)
    return a,b,c
def build_contract_packet()->ContentPerformanceReviewLedgerPacket:
    uc_packet=uc.build_contract_packet(); p=uc_packet.manual_publish_records[0]; m=uc_packet.manual_metrics_records[0]; r=build_performance_review(p,m); s=build_feedback_signal(r); l=build_feedback_loop_packet((r,),(s,)); v=validate_content_performance(r,l,p,m); entries=_audit_entries(r,s,l); draft={"performance_reviews":(r,),"feedback_signals":(s,),"feedback_loop_packets":(l,),"validation_results":(v,),"audit_ledger_entries":entries,"all_records_redacted":all(e.redacted_summary for e in entries),"all_feedback_review_only":True,"no_api_verification":True,"no_scraping":True,"no_auto_generation":True,"no_auto_publish":True,"no_dispatch":True,"no_public_claim_authorized":True,"evidence_refs":_unique(tuple(r.evidence_refs)+tuple(s.evidence_refs)+tuple(l.evidence_refs)+tuple(x for e in entries for x in e.retained_evidence_refs)),"safety_flags":safety_flags(),"blocked_reasons":_unique(tuple(v.blocked_reasons)),"next_required_gate":NEXT_HEAVY_BATCH}; h=_digest(draft); return ContentPerformanceReviewLedgerPacket("content_performance_review_ledger_packet_"+h[:24],packet_hash=h,packet_hash_algorithm=HASH_ALGORITHM,**draft)
def render_runbook(packet)->str:
    return "\n".join(["# 0174UD Content Performance Review + Editorial Feedback Loop Contract","",f"- task_label: `{TASK_LABEL}`",f"- model_version: `{MODEL_VERSION}`",f"- source_baseline_commit: `{SOURCE_BASELINE_COMMIT}`",f"- packet_id: `{packet.packet_id}`",f"- packet_hash: `{packet.packet_hash}`","","## Rules","","- Metrics are operator-attested manual snapshots only.","- API-verified, scraped, future API import, mismatched, negative, or time-invalid metrics block.","- Feedback is review-only future guidance; it cannot approve, dispatch, auto-generate, auto-publish, or authorize public claims.","- U9 redacted ledger entries preserve evidence without secrets.","","## Next heavy batch","",f"`{NEXT_HEAVY_BATCH}`",""])
def write_artifacts(repo_root:str|Path=".", output_dir:str|Path|None=None)->dict[str,Any]:
    root=Path(repo_root).resolve(); allowed=(root/DOC_REL_DIR).resolve(); out=allowed if output_dir is None else Path(output_dir).resolve()
    if out!=allowed: raise ValueError("artifact_writer_refuses_paths_outside_docs_automation_0174UD")
    out.mkdir(parents=True,exist_ok=True); packet=build_contract_packet(); (out/PACKET_FILENAME).write_text(json.dumps(_asdict(packet),ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n"); (out/RUNBOOK_FILENAME).write_text(render_runbook(packet),encoding="utf-8",newline="\n"); return {"packet":packet,"packet_path":str(out/PACKET_FILENAME),"runbook_path":str(out/RUNBOOK_FILENAME)}
def contract_checksum()->str: return build_contract_packet().packet_hash
