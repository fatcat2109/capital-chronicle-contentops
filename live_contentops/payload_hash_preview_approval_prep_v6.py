"""V6 payload hash preview and approval ledger preparation, local-only no-provider no-send."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"
TASK_LABEL = "TASK_CONTENTOPS_V6_PAYLOAD_HASH_PREVIEW_AND_APPROVAL_LEDGER_PREP_FROM_DRAFT_INSPECTION_HEAVY_BATCH_NO_PROVIDER_NO_SEND_V0"
UPSTREAM_TASK_LABEL = "TASK_CONTENTOPS_V6_DRAFT_INSPECTOR_FOR_CONTENT_PRODUCTION_REVIEW_BUNDLE_HEAVY_BATCH_NO_PROVIDER_NO_SEND_V0"
PREVIEW_MODE = "deterministic_local_review_only"
APPROVAL_MODE = "approval_ledger_preparation_only"

HARD_FALSE_FLAGS = ("eligible_for_live_send_now", "provider_call_made", "env_read", "credential_value_read", "network_call_made", "browser_session_used", "public_url_created", "metrics_created", "publication_ready", "dispatch_allowed", "runtime_truth")
SUPPORTED_PLATFORMS = ("substack", "discord", "telegram", "x_manual", "linkedin_org_deferred", "tiktok_deferred")
BLOCKED_TARGETS = ("live_send", "dispatch", "publication", "public_url_creation", "metrics_creation", "provider_call", "browser_session", "env_read", "credential_value_read")
PROHIBITED_APPROVAL_TARGETS = {"live_send", "dispatch", "publication", "public_url", "metrics"}

SECRET_OR_URL_RE = re.compile(r"https?://|discord(?:app)?\.com/api/webhooks|[A-Za-z0-9_-]{24,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}", re.I)

@dataclass(frozen=True)
class PayloadPreviewShell:
    schema_version: str
    payload_preview_id: str
    source_draft_inspection_bundle_id: str
    source_draft_inspection_report_id: str
    platform: str
    payload_class: str
    adapter_class: str
    destination_binding_id: str
    credential_handle_id: str
    preview_mode: str
    preview_text: str
    preview_contains_public_url: bool
    preview_contains_secret: bool
    preview_contains_endpoint_or_webhook: bool
    preview_contains_channel_or_account_id: bool
    preview_contains_financial_advice: bool
    preview_contains_signal_service_claim: bool
    preview_contains_fake_metric: bool
    preview_contains_fake_citation: bool
    preview_contains_model_authority_claim: bool
    preview_contains_live_dispatch_claim: bool
    preview_publication_ready: bool
    preview_dispatch_ready: bool
    preview_live_send_ready: bool
    human_review_required: bool
    payload_hash: str
    hash_inputs_redacted: bool
    hash_excludes_secret_material: bool
    hash_excludes_webhook_url: bool
    hash_excludes_browser_profile: bool
    hash_excludes_cookie_session_storage: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class ApprovalLedgerPreparationCandidate:
    schema_version: str
    approval_ledger_prep_id: str
    source_draft_inspection_bundle_id: str
    payload_preview_ids: list[str]
    payload_hashes: list[str]
    approval_mode: str
    approval_status: str
    human_approval_required: bool
    approval_granted_now: bool
    valid_for_outbox: bool
    valid_for_dispatch: bool
    publication_ready: bool
    dispatch_allowed: bool
    live_send_allowed: bool
    revocation_supported: bool
    expires_at_required_later: bool
    destination_binding_required_later: bool
    credential_handle_required_later: bool
    payload_hash_revalidation_required_later: bool
    redacted_audit_required_later: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

@dataclass(frozen=True)
class PayloadHashPreviewApprovalPrepBundle:
    schema_version: str
    task_label: str
    payload_hash_preview_approval_prep_bundle_id: str
    source_draft_inspection_bundle_id: str
    payload_previews: list[dict[str, Any]]
    approval_ledger_preparation_candidate: dict[str, Any]
    eligible_for_future_operator_approval_task: bool
    eligible_for_future_outbox_preparation_task: bool
    eligible_for_live_send_now: bool
    provider_call_made: bool
    env_read: bool
    credential_value_read: bool
    network_call_made: bool
    browser_session_used: bool
    executable_request_artifact_created: bool
    public_url_created: bool
    metrics_created: bool
    publication_ready: bool
    dispatch_allowed: bool
    runtime_truth: bool
    human_review_required: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    packet_sha256: str = ""

def _sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()

def _packet_sha(payload: dict[str, Any]) -> str:
    clone = dict(payload); clone.pop("packet_sha256", None)
    return _sha(clone)

def _walk(obj: Any, path: str = "") -> list[tuple[str, Any]]:
    if isinstance(obj, dict):
        out: list[tuple[str, Any]] = []
        for key, value in obj.items(): out.extend(_walk(value, f"{path}.{key}" if path else str(key)))
        return out
    if isinstance(obj, list):
        out = []
        for idx, value in enumerate(obj): out.extend(_walk(value, f"{path}[{idx}]"))
        return out
    return [(path, obj)]

def is_safe_string(val: str) -> bool:
    low = val.lower()
    
    # Check secret or url regex
    if SECRET_OR_URL_RE.search(val):
        return False
        
    # Check forbidden words, but ignore safe system terms
    clean_low = low
    safe_terms = (
        "browser_session",
        "webhook_adapter",
        "announcements_webhook",
        "webhook_url_included",
        "webhook_token_included",
        "endpoint_url_included",
        "endpoint_or_webhook",
    )
    for term in safe_terms:
        clean_low = clean_low.replace(term, "safe_system_term")
        
    forbidden = (
        "cookie", "session", "localstorage", "fake citation", "fake metric", "fake metrics",
        "financial advice", "signal service", "buy", "sell", "hold", "entries", "exits", "targets", "position sizing",
        "guaranteed prediction", "model says", "ai guarantees", "publication approved", "dispatch allowed",
        "live send", "executable request", "webhook", "endpoint", "secret", "public url",
        "publication ready", "dispatch ready", "live send ready", "model authority", "live dispatch claim",
    )
    for f in forbidden:
        if f in clean_low:
            return False
            
    return True

def _assert_safe(obj: dict[str, Any], label: str) -> None:
    for path, value in _walk(obj):
        if isinstance(value, str):
            if not is_safe_string(value):
                # Check if it's value-like or text-like
                if SECRET_OR_URL_RE.search(value):
                    raise ValueError(f"{label}_forbidden_value:{path}")
                else:
                    raise ValueError(f"{label}_forbidden_text:{path}")

def _add(blockers: list[str], ok: bool, message: str) -> None:
    if not ok: blockers.append(message)

def _upstream_blockers(bundle: dict[str, Any]) -> list[str]:
    b: list[str] = []
    _add(b, bundle.get("schema_version") == SCHEMA_VERSION, "upstream_schema_version_invalid")
    _add(b, bundle.get("task_label") == UPSTREAM_TASK_LABEL, "upstream_task_label_invalid")
    _add(b, isinstance(bundle.get("draft_inspection_report"), dict), "upstream_report_missing")
    _add(b, bundle.get("eligible_for_payload_hash_preview_task") is True, "upstream_payload_hash_eligibility_not_true")
    _add(b, bundle.get("eligible_for_approval_ledger_preparation_task") is True, "upstream_approval_ledger_prep_eligibility_not_true")
    for flag in HARD_FALSE_FLAGS:
        _add(b, bundle.get(flag) is False, f"upstream_{flag}_not_false")
    _add(b, bundle.get("human_review_required") is True, "upstream_human_review_required_not_true")
    _add(b, bundle.get("blockers", []) == [], "upstream_blockers_not_empty")
    
    report = bundle.get("draft_inspection_report", {})
    if isinstance(report, dict):
        targets = set(report.get("approval_eligible_targets", []))
        _add(b, not (targets - {"payload_hash_preview_only", "approval_ledger_preparation_only"}), "report_approval_targets_invalid")
        blocked = set(report.get("blocked_targets", []))
        for target in BLOCKED_TARGETS:
            _add(b, target in blocked, f"report_blocked_target_missing_{target}")
        for status in ("citation_status", "missing_evidence_status", "source_freshness_status"):
            _add(b, report.get(status) in {"source_review_required", "review_required"}, f"report_{status}_invalid")
            
    return b

def compute_payload_hash(platform: str, payload_class: str, adapter_class: str, preview_text: str, report_id: str) -> str:
    policy_snapshot = {
        "no_secrets": True,
        "no_webhooks": True,
        "no_browser_profile": True,
        "no_cookie_session": True
    }
    inputs = {
        "platform": platform,
        "payload_class": payload_class,
        "adapter_class": adapter_class,
        "preview_text": preview_text,
        "source_draft_inspection_report_id": report_id,
        "policy_snapshot": policy_snapshot
    }
    serialized = json.dumps(inputs, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def get_preview_text(platform: str, review_bundle: dict[str, Any]) -> str:
    article = review_bundle.get("canonical_article_review_packet", {})
    article_title = article.get("title", "Unknown Title")
    
    variants = review_bundle.get("platform_variant_set_candidate_packet", {}).get("variants", {})
    if isinstance(variants, dict) and platform in variants:
        txt = variants[platform].get("review_only_text")
        if txt:
            return txt
            
    if platform == "discord":
        drop = review_bundle.get("discord_drop_candidate_packet", {})
        title = drop.get("title")
        dq = drop.get("discussion_question")
        if title and dq:
            return f"{title} - Discussion: {dq}"
            
    return f"Review-only {platform} candidate for {article_title}"

def get_adapter_class(platform: str) -> str:
    if platform == "x_manual":
        return "manual_fallback_adapter"
    elif platform in ("linkedin_org_deferred", "tiktok_deferred"):
        return "deferred_adapter"
    elif platform in ("substack", "discord", "telegram"):
        return "future_webhook_adapter"
    return "review_only"

def make_payload_hash_preview_approval_prep_bundle(
    draft_inspection_bundle: dict[str, Any],
    content_production_review_bundle: dict[str, Any]
) -> PayloadHashPreviewApprovalPrepBundle:
    _assert_safe(draft_inspection_bundle, "draft_inspection_bundle")
    _assert_safe(content_production_review_bundle, "content_production_review_bundle")
    
    upstream = _upstream_blockers(draft_inspection_bundle)
    
    previews = []
    preview_ids = []
    hashes = []
    
    report = draft_inspection_bundle.get("draft_inspection_report", {})
    report_id = str(report.get("draft_inspection_report_id", ""))
    bundle_id = str(draft_inspection_bundle.get("draft_inspection_bundle_id", ""))
    
    blockers = upstream[:]
    
    for platform in SUPPORTED_PLATFORMS:
        preview_text = get_preview_text(platform, content_production_review_bundle)
        payload_class = "review_only_draft_candidate"
        adapter_class = get_adapter_class(platform)
        
        # Safe check preview text
        try:
            _assert_safe({"txt": preview_text}, "preview_text")
        except ValueError as exc:
            blockers.append(f"preview_text_safety_failure:{platform}:{str(exc)}")
            
        p_hash = compute_payload_hash(platform, payload_class, adapter_class, preview_text, report_id)
        p_id = "payload_preview_" + _sha(platform + report_id)[:16]
        
        preview = PayloadPreviewShell(
            schema_version=SCHEMA_VERSION,
            payload_preview_id=p_id,
            source_draft_inspection_bundle_id=bundle_id,
            source_draft_inspection_report_id=report_id,
            platform=platform,
            payload_class=payload_class,
            adapter_class=adapter_class,
            destination_binding_id="symbolic_destination_binding_placeholder_only",
            credential_handle_id="symbolic_credential_handle_placeholder_only",
            preview_mode=PREVIEW_MODE,
            preview_text=preview_text,
            preview_contains_public_url=False,
            preview_contains_secret=False,
            preview_contains_endpoint_or_webhook=False,
            preview_contains_channel_or_account_id=False,
            preview_contains_financial_advice=False,
            preview_contains_signal_service_claim=False,
            preview_contains_fake_metric=False,
            preview_contains_fake_citation=False,
            preview_contains_model_authority_claim=False,
            preview_contains_live_dispatch_claim=False,
            preview_publication_ready=False,
            preview_dispatch_ready=False,
            preview_live_send_ready=False,
            human_review_required=True,
            payload_hash=p_hash,
            hash_inputs_redacted=True,
            hash_excludes_secret_material=True,
            hash_excludes_webhook_url=True,
            hash_excludes_browser_profile=True,
            hash_excludes_cookie_session_storage=True,
            blockers=[],
            warnings=["local_preview_only", "human_review_required"]
        )
        previews.append(asdict(preview))
        preview_ids.append(p_id)
        hashes.append(p_hash)
        
    prep_id = "approval_ledger_prep_" + _sha(bundle_id)[:16]
    candidate = ApprovalLedgerPreparationCandidate(
        schema_version=SCHEMA_VERSION,
        approval_ledger_prep_id=prep_id,
        source_draft_inspection_bundle_id=bundle_id,
        payload_preview_ids=preview_ids,
        payload_hashes=hashes,
        approval_mode=APPROVAL_MODE,
        approval_status="not_approved",
        human_approval_required=True,
        approval_granted_now=False,
        valid_for_outbox=False,
        valid_for_dispatch=False,
        publication_ready=False,
        dispatch_allowed=False,
        live_send_allowed=False,
        revocation_supported=True,
        expires_at_required_later=True,
        destination_binding_required_later=True,
        credential_handle_required_later=True,
        payload_hash_revalidation_required_later=True,
        redacted_audit_required_later=True,
        blockers=[],
        warnings=["not_approved_for_outbox", "not_approved_for_dispatch", "human_approval_required"]
    )
    
    candidate_dict = asdict(candidate)
    
    if blockers:
        candidate_dict = {
            **candidate_dict,
            "blockers": blockers[:],
            "approval_status": "blocked"
        }
        
    eligible = not blockers
    
    bundle_prep_id = "payload_hash_preview_approval_prep_bundle_" + _sha(prep_id)[:16]
    
    bundle = PayloadHashPreviewApprovalPrepBundle(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        payload_hash_preview_approval_prep_bundle_id=bundle_prep_id,
        source_draft_inspection_bundle_id=bundle_id,
        payload_previews=previews,
        approval_ledger_preparation_candidate=candidate_dict,
        eligible_for_future_operator_approval_task=eligible,
        eligible_for_future_outbox_preparation_task=False,
        eligible_for_live_send_now=False,
        provider_call_made=False,
        env_read=False,
        credential_value_read=False,
        network_call_made=False,
        browser_session_used=False,
        executable_request_artifact_created=False,
        public_url_created=False,
        metrics_created=False,
        publication_ready=False,
        dispatch_allowed=False,
        runtime_truth=False,
        human_review_required=True,
        blockers=blockers,
        warnings=["review_only", "no_live_send", "future_operator_approval_task_required"]
    )
    
    data = asdict(bundle)
    return PayloadHashPreviewApprovalPrepBundle(**{**data, "packet_sha256": _packet_sha(data)})

def blocked_bundle(reason: str) -> PayloadHashPreviewApprovalPrepBundle:
    empty_cand = {
        "schema_version": SCHEMA_VERSION,
        "approval_ledger_prep_id": "approval_ledger_prep_blocked",
        "source_draft_inspection_bundle_id": "",
        "payload_preview_ids": [],
        "payload_hashes": [],
        "approval_mode": APPROVAL_MODE,
        "approval_status": "blocked",
        "human_approval_required": True,
        "approval_granted_now": False,
        "valid_for_outbox": False,
        "valid_for_dispatch": False,
        "publication_ready": False,
        "dispatch_allowed": False,
        "live_send_allowed": False,
        "revocation_supported": True,
        "expires_at_required_later": True,
        "destination_binding_required_later": True,
        "credential_handle_required_later": True,
        "payload_hash_revalidation_required_later": True,
        "redacted_audit_required_later": True,
        "blockers": [reason],
        "warnings": ["blocked_fail_closed"]
    }
    bundle = PayloadHashPreviewApprovalPrepBundle(
        schema_version=SCHEMA_VERSION,
        task_label=TASK_LABEL,
        payload_hash_preview_approval_prep_bundle_id="payload_hash_preview_approval_prep_bundle_blocked",
        source_draft_inspection_bundle_id="",
        payload_previews=[],
        approval_ledger_preparation_candidate=empty_cand,
        eligible_for_future_operator_approval_task=False,
        eligible_for_future_outbox_preparation_task=False,
        eligible_for_live_send_now=False,
        provider_call_made=False,
        env_read=False,
        credential_value_read=False,
        network_call_made=False,
        browser_session_used=False,
        executable_request_artifact_created=False,
        public_url_created=False,
        metrics_created=False,
        publication_ready=False,
        dispatch_allowed=False,
        runtime_truth=False,
        human_review_required=True,
        blockers=[reason],
        warnings=["blocked_fail_closed"]
    )
    data = asdict(bundle)
    return PayloadHashPreviewApprovalPrepBundle(**{**data, "packet_sha256": _packet_sha(data)})

def load_json_object(path: str | Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError("malformed_json") from exc
    if not isinstance(data, dict):
        raise ValueError("json_not_object")
    return data

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V6 payload hash preview and approval ledger preparation CLI")
    parser.add_argument("--draft-inspection-bundle", required=True)
    parser.add_argument("--content-production-review-bundle", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    
    try:
        draft_bundle = load_json_object(args.draft_inspection_bundle)
        review_bundle = load_json_object(args.content_production_review_bundle)
        packet = make_payload_hash_preview_approval_prep_bundle(draft_bundle, review_bundle)
    except ValueError as exc:
        packet = blocked_bundle(str(exc))
        
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(asdict(packet), indent=2, sort_keys=True), encoding="utf-8")
    return 0 if packet.eligible_for_future_operator_approval_task else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
