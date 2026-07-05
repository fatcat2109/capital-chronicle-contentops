"""Local-only pre-alpha manual export packet + content ledger builder (Task 0099).

Deterministic, repo-local. Consumes a clean 0098 approval packet and emits a
manual-export packet plus a content-ledger entry. These outputs are for operator
review and MANUAL copy/paste only. They NEVER imply API posting, scheduling,
metrics ingestion, or live execution.

This module performs NO network/search/provider/LLM/platform/credential access.
It NEVER posts, NEVER fetches, NEVER reads `.env`, NEVER auto-publishes, NEVER
produces public-postable output, and NEVER emits financial advice / signal /
execution language or fake Capital Chronicle alpha output.

Guardrail scans are reused from grounded_research_brief (single source of truth)
plus the 0095 numeric-market-claim detector, so an externally supplied approval
packet cannot smuggle unsafe content through export.
"""

import json
import os

from live_contentops.grounded_research_brief import (
    _scan_forbidden_language,
    _scan_alpha_implication,
)
from live_contentops.pre_alpha_content_engine import (
    STATIC_TIMESTAMP,
    _scan_numeric_market_claim,
)

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")
EXPORT_PACKET_SCHEMA_PATH = os.path.join(
    SCHEMA_DIR, "pre_alpha_manual_export_packet.schema.json"
)
LEDGER_ENTRY_SCHEMA_PATH = os.path.join(
    SCHEMA_DIR, "pre_alpha_content_ledger_entry.schema.json"
)

ALLOWED_EXPORT_FORMATS = {
    "copy_paste_text",
    "newsletter_markdown",
    "generic_markdown",
}

# Platform family -> default export format.
_DEFAULT_FORMAT = {
    "x": "copy_paste_text",
    "linkedin": "copy_paste_text",
    "threads": "copy_paste_text",
    "newsletter": "newsletter_markdown",
    "generic": "generic_markdown",
}


def load_export_packet_schema():
    with open(os.path.abspath(EXPORT_PACKET_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def load_ledger_entry_schema():
    with open(os.path.abspath(LEDGER_ENTRY_SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def _scan_text(text):
    """Return guardrail findings for export text. Deterministic, no external access."""
    findings = []
    if _scan_forbidden_language(text):
        findings.append("export_text_forbidden_language")
    if _scan_alpha_implication(text):
        findings.append("export_text_implies_alpha_output")
    if _scan_numeric_market_claim(text):
        findings.append("export_text_unverified_numeric_market_claim")
    return findings


def validate_approval_packet_for_export(approval_packet):
    """Validate that an approval packet is eligible to become an export packet.

    Returns {'valid': bool, 'errors': [...]}. Fail closed on any unsafe flag or
    on a packet that is not a clean approval (manual_publish_prep_ready=true).
    """
    errors = []
    if not isinstance(approval_packet, dict):
        return {"valid": False, "errors": ["approval_packet_not_object"]}

    if not approval_packet.get("approval_packet_id"):
        errors.append("missing_approval_packet_id")
    if not approval_packet.get("draft_id"):
        errors.append("missing_draft_id")

    # Only a clean, approved-for-manual-prep packet may be exported.
    if approval_packet.get("approval_status") != "approved_manual_publish_prep":
        errors.append("approval_packet_not_approved")
    if approval_packet.get("manual_publish_prep_ready") is not True:
        errors.append("approval_packet_not_manual_publish_prep_ready")
    if approval_packet.get("blocked_reasons"):
        errors.append("approval_packet_has_blocked_reasons")

    # Non-publishing posture must be intact on the source packet.
    if approval_packet.get("public_postable") is not False:
        errors.append("approval_public_postable_must_be_false")
    if approval_packet.get("publish_allowed_now") is not False:
        errors.append("approval_publish_allowed_now_must_be_false")
    if approval_packet.get("platform_publish_allowed_now") is not False:
        errors.append("approval_platform_publish_allowed_now_must_be_false")
    if approval_packet.get("live_execution_allowed_now") is not False:
        errors.append("approval_live_execution_allowed_now_must_be_false")
    if approval_packet.get("final_operator_check_required") is not True:
        errors.append("approval_final_operator_check_required_must_be_true")

    # Source attribution: artifact IDs OR explicit general/process marker.
    has_sources = bool(approval_packet.get("source_artifact_ids"))
    is_general = bool(approval_packet.get("is_general_process_content"))
    if not has_sources and not is_general:
        errors.append("missing_source_artifact_ids_or_general_process_marker")

    # Independent re-scan of the approved text (defense in depth).
    errors.extend(_scan_text(str(approval_packet.get("approved_text", ""))))

    return {"valid": len(errors) == 0, "errors": errors}


def build_export_packet(approval_packet, export_format=None):
    """Build a manual export packet from a 0098 approval packet.

    Fails closed: on any validation error the packet is emitted with
    export_status="blocked", manual_copy_ready=false, and populated
    blocked_reasons. All non-publishing flags are pinned regardless of input.
    """
    if not isinstance(approval_packet, dict):
        approval_packet = {}

    v = validate_approval_packet_for_export(approval_packet)
    blocked_reasons = list(v["errors"])

    platform_family = approval_packet.get("platform_family")
    fmt = export_format or _DEFAULT_FORMAT.get(platform_family, "generic_markdown")
    if fmt not in ALLOWED_EXPORT_FORMATS:
        blocked_reasons.append("export_format_not_allowed")
        fmt = "generic_markdown"

    clean = len(blocked_reasons) == 0
    export_status = "prepared_for_operator_review" if clean else "blocked"
    export_text = str(approval_packet.get("approved_text", "")) if clean else ""

    approval_id = approval_packet.get("approval_packet_id") or "unknown"
    draft_id = approval_packet.get("draft_id") or "unknown"

    audit_refs = [
        "approval_packet:%s" % approval_id,
        "review_decision:%s" % approval_packet.get("review_decision_id"),
        "rendered_packet:%s" % approval_packet.get("rendered_packet_id"),
        "export_status:%s" % export_status,
    ]

    return {
        "manual_export_packet_id": "manual_export_%s" % approval_id,
        "approval_packet_id": approval_id,
        "draft_id": draft_id,
        "platform_family": platform_family,
        "content_type": approval_packet.get("content_type"),
        "export_status": export_status,
        "export_text": export_text,
        "export_format": fmt,
        "source_artifact_ids": list(approval_packet.get("source_artifact_ids") or []),
        "is_general_process_content": bool(approval_packet.get("is_general_process_content")),
        "limitations": list(approval_packet.get("limitations") or []),
        "manual_publish_only": True,
        "final_operator_check_required": True,
        "manual_copy_ready": clean,
        "public_postable": False,
        "publish_allowed_now": False,
        "platform_publish_allowed_now": False,
        "live_execution_allowed_now": False,
        "platform_api_call_allowed": False,
        "scheduler_allowed": False,
        "metrics_ingestion_allowed": False,
        "blocked_reasons": blocked_reasons,
        "audit_refs": audit_refs,
    }


def build_ledger_entry(export_packet, manual_record=None):
    """Build a content ledger entry from a manual export packet.

    manual_record is an OPTIONAL operator-supplied dict that may carry
    manual_publish_url / manual_publish_timestamp / manual_metrics. The ledger
    only advances to lifecycle_status="manually_published" when the operator has
    actually supplied a non-empty manual_publish_url. Otherwise url/timestamp/
    metrics stay null by default.
    """
    if not isinstance(export_packet, dict):
        export_packet = {}
    manual_record = manual_record if isinstance(manual_record, dict) else {}

    export_blocked = bool(export_packet.get("blocked_reasons")) or (
        export_packet.get("export_status") == "blocked"
    )

    manual_url = manual_record.get("manual_publish_url")
    manual_ts = manual_record.get("manual_publish_timestamp")
    manual_metrics = manual_record.get("manual_metrics")

    has_manual_url = isinstance(manual_url, str) and manual_url.strip() != ""

    if export_blocked:
        lifecycle_status = "blocked"
        manual_url = None
        manual_ts = None
        manual_metrics = None
    elif has_manual_url:
        # Operator manually published outside this system and recorded the URL.
        lifecycle_status = "manually_published"
    else:
        lifecycle_status = "export_prepared"
        manual_url = None
        manual_ts = None
        manual_metrics = None

    export_id = export_packet.get("manual_export_packet_id") or "unknown"
    approval_id = export_packet.get("approval_packet_id") or "unknown"
    draft_id = export_packet.get("draft_id") or "unknown"

    audit_trail = [
        "manual_export_packet:%s" % export_id,
        "approval_packet:%s" % approval_id,
        "lifecycle_status:%s" % lifecycle_status,
    ]

    return {
        "content_ledger_entry_id": "ledger_%s" % approval_id,
        "manual_export_packet_id": export_id,
        "approval_packet_id": approval_id,
        "draft_id": draft_id,
        "platform_family": export_packet.get("platform_family"),
        "content_type": export_packet.get("content_type"),
        "source_artifact_ids": list(export_packet.get("source_artifact_ids") or []),
        "is_general_process_content": bool(export_packet.get("is_general_process_content")),
        "lifecycle_status": lifecycle_status,
        "manual_publish_url": manual_url,
        "manual_publish_timestamp": manual_ts,
        "manual_metrics": manual_metrics,
        "public_postable": False,
        "publish_allowed_now": False,
        "platform_publish_allowed_now": False,
        "live_execution_allowed_now": False,
        "scheduler_allowed": False,
        "created_at": STATIC_TIMESTAMP,
        "updated_at": STATIC_TIMESTAMP,
        "audit_trail": audit_trail,
    }

def build_from_input_file(path):
    """Build {export_packet, ledger_entry} from a bundle fixture.

    Expected keys: approval_packet (required), export_format (optional),
    manual_record (optional). Local file read only.
    """
    with open(path, "r", encoding="utf-8") as f:
        bundle = json.load(f)
    export_packet = build_export_packet(
        bundle.get("approval_packet"), bundle.get("export_format")
    )
    ledger_entry = build_ledger_entry(export_packet, bundle.get("manual_record"))
    return {"export_packet": export_packet, "ledger_entry": ledger_entry}


def summary():
    """Deterministic local capability summary for the CLI. Schema reads only."""
    return {
        "status": "pre-alpha manual export packets and content ledger active",
        "local_only": True,
        "design_only": True,
        "manual_export_enabled": True,
        "content_ledger_enabled": True,
        "supported_export_formats": sorted(ALLOWED_EXPORT_FORMATS),
        "integrates_with_0098_approval_packet": True,
        "platform_api_call_allowed": False,
        "scheduler_allowed": False,
        "metrics_ingestion_allowed": False,
        "auto_publish": False,
        "provider_call_made": False,
        "network_call_made": False,
        "credential_read": False,
        "fake_alpha_output": False,
        "public_postable_output": False,
        "publish_allowed_now": False,
        "platform_publish_allowed_now": False,
        "live_execution_allowed_now": False,
        "manual_publish_url_default_null": True,
        "final_operator_check_required": True,
        "static_timestamp": STATIC_TIMESTAMP,
    }


