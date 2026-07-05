"""Local-only pre-alpha platform-specific manual export templates (Task 0110).

Deterministic, repo-local. Consumes a 0107 manual export batch packet and emits
platform-specific copy/paste template records for X, LinkedIn, Threads,
newsletter, and generic outputs. This improves the operator copy/paste workflow.

This is platform-specific MANUAL copy/paste formatting ONLY. It NEVER posts,
schedules, calls a platform/provider/LLM/network, scrapes, ingests metrics,
reads `.env`, auto-publishes, produces public-postable output, generates
platform API payloads/request bodies, verifies current platform specs, or emits
financial-advice / signal / execution language or fake Capital Chronicle alpha.

Only CLEAN 0107 export packets (export_status=prepared_for_operator_review,
manual_copy_ready=true, no blocked_reasons) produce template records. Blocked or
unsupported exports are preserved in unsupported_or_blocked_exports, never
templated as clean. The packet fails closed (packet_status="blocked") if any
hard-boundary flag is unsafe, any record implies platform/publish readiness, or
any content loses source attribution / limitations.

Platform limits below are CONSERVATIVE LOCAL GUIDANCE only; they are not
verified current platform specs. Operator final check is always required.
"""

import json
import os

from live_contentops.pre_alpha_content_engine import STATIC_TIMESTAMP

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")
SCHEMA_PATH = os.path.join(
    SCHEMA_DIR, "pre_alpha_platform_manual_template_packet.schema.json"
)

FIXTURE_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "fixtures",
    "pre_alpha_platform_manual_templates",
)
DEFAULT_CONFIG = os.path.join(
    FIXTURE_DIR, "valid_platform_manual_template_config.json"
)

SUPPORTED_PLATFORM_FAMILIES = {"x", "linkedin", "threads", "newsletter", "generic"}

# Platform family -> manual template format (formatting style for copy/paste).
_TEMPLATE_FORMAT = {
    "x": "short_form_plain_text",
    "threads": "short_form_plain_text",
    "linkedin": "professional_long_form",
    "newsletter": "newsletter_markdown",
    "generic": "generic_markdown",
}

# Conservative local-guidance soft length hints (NOT verified current specs).
_SOFT_LENGTH_HINT = {
    "x": "Conservative local guidance: keep well under ~280 characters; "
    "verify the current platform limit yourself before posting.",
    "threads": "Conservative local guidance: keep concise short-form; "
    "verify the current platform limit yourself before posting.",
    "linkedin": "Conservative local guidance: professional long-form is fine; "
    "verify the current platform limit yourself before posting.",
    "newsletter": "Conservative local guidance: markdown long-form is fine; "
    "no platform character cap assumed.",
    "generic": "Conservative local guidance: generic markdown; "
    "adapt manually to the destination before posting.",
}

# Hard-boundary flags pinned on every packet, independent of input.
_REQUIRED_FLAGS = {
    "local_only": True,
    "fixture_only": True,
    "manual_copy_paste_only": True,
    "operator_final_check_required": True,
    "platform_api_call_allowed_now": False,
    "provider_call_allowed_now": False,
    "network_call_allowed_now": False,
    "scheduler_allowed": False,
    "automatic_metrics_ingestion_allowed": False,
    "scraping_allowed": False,
    "credential_or_env_read_allowed": False,
    "live_execution_allowed_now": False,
    "auto_publish": False,
    "public_postable": False,
}

# Pinned per-record non-publishing flags.
_RECORD_PINNED = {
    "operator_final_check_required": True,
    "manual_publish_only": True,
    "public_postable": False,
    "publish_allowed_now": False,
    "platform_publish_allowed_now": False,
    "platform_api_call_allowed": False,
    "scheduler_allowed": False,
    "metrics_ingestion_allowed": False,
    "live_execution_allowed_now": False,
}

_OPERATOR_FINAL_CHECKLIST = [
    "Confirm each platform template's text is accurate before any manual copy.",
    "Confirm limitations / source attribution remain visible in the template.",
    "Platform length/format notes are conservative local guidance, NOT verified "
    "current platform specs; verify the live platform yourself.",
    "Manually copy and paste; this system never posts, schedules, or calls a "
    "platform API for you.",
    "Do not treat any template as publish-ready or platform-ready.",
]


def load_schema():
    with open(os.path.abspath(SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def load_config(config_path=None):
    """Load the 0110 template config. Local file read only."""
    target = config_path or DEFAULT_CONFIG
    with open(os.path.abspath(target), "r", encoding="utf-8") as f:
        return json.load(f)


def _hard_boundary_flags():
    return dict(_REQUIRED_FLAGS)


def _audit_flags(flags):
    violations = []
    for flag, expected in _REQUIRED_FLAGS.items():
        if flag not in flags:
            violations.append("missing_flag:%s" % flag)
        elif flags[flag] is not expected:
            violations.append("%s=%r" % (flag, flags[flag]))
    return violations


def _export_packet_clean(export_packet):
    """Return True only for a CLEAN, eligible 0107 export packet."""
    if not isinstance(export_packet, dict):
        return False
    return (
        export_packet.get("export_status") == "prepared_for_operator_review"
        and export_packet.get("manual_copy_ready") is True
        and not export_packet.get("blocked_reasons")
    )


def _record_unsafe(record):
    """Return violation strings if a template record implies publish readiness."""
    violations = []
    for flag, expected in _RECORD_PINNED.items():
        if record.get(flag) is not expected:
            violations.append("record_%s=%r" % (flag, record.get(flag)))
    # Defense in depth: a template must never carry a platform API payload.
    if record.get("platform_api_payload") is not None:
        violations.append("record_platform_api_payload_present")
    return violations


def _format_copy_paste_text(platform_family, export_text):
    """Deterministically wrap export text for a platform family.

    Pure local string formatting. No external calls. Preserves the approved text
    verbatim; only adds a leading operator-check marker and trailing reminder.
    """
    header = (
        "[MANUAL COPY/PASTE - OPERATOR FINAL CHECK REQUIRED - NOT PUBLIC POSTABLE]"
    )
    footer = (
        "[Verify accuracy, limitations, and current platform rules before posting.]"
    )
    body = (export_text or "").strip()
    if platform_family in ("x", "threads", "linkedin"):
        return "%s\n\n%s\n\n%s" % (header, body, footer)
    # newsletter / generic use markdown.
    return "%s\n\n%s\n\n> %s" % (header, body, footer)


def _build_template_record(export_packet):
    """Build one platform_template_record from a clean export packet."""
    platform_family = export_packet.get("platform_family")
    source_format = export_packet.get("export_format") or "generic_markdown"
    template_format = _TEMPLATE_FORMAT.get(platform_family, "generic_markdown")
    export_text = str(export_packet.get("export_text", ""))

    formatting_notes = [
        _SOFT_LENGTH_HINT.get(platform_family, _SOFT_LENGTH_HINT["generic"]),
        "Template format: %s." % template_format,
        "Source export format: %s." % source_format,
        "No platform API payload is generated; copy/paste manually.",
    ]

    record = {
        "manual_export_packet_id": export_packet.get("manual_export_packet_id"),
        "draft_id": export_packet.get("draft_id"),
        "platform_family": platform_family,
        "content_type": export_packet.get("content_type"),
        "source_export_format": source_format,
        "manual_template_format": template_format,
        "copy_paste_text": _format_copy_paste_text(platform_family, export_text),
        "formatting_notes": formatting_notes,
        "source_artifact_ids": list(export_packet.get("source_artifact_ids") or []),
        "is_general_process_content": bool(
            export_packet.get("is_general_process_content")
        ),
        "limitations": list(export_packet.get("limitations") or []),
        "blocked_reasons": [],
    }
    record.update(_RECORD_PINNED)
    return record


def build_platform_manual_template_packet(export_batch_packet,
                                          platform_manual_template_packet_id=None,
                                          source_refs=None):
    """Build a deterministic platform manual template packet from a 0107 packet.

    Only clean 0107 manual export packets become platform template records.
    Blocked / unsupported exports are preserved in unsupported_or_blocked_exports.
    Nothing is published, scheduled, posted, or sent. Safety flags are pinned and
    the packet fails closed on any unsafe condition.
    """
    blocked_reasons = []

    if not isinstance(export_batch_packet, dict):
        export_batch_packet = {}

    export_packets = export_batch_packet.get("manual_export_packets") or []

    template_records = []
    unsupported_or_blocked = []
    family_counts = {}

    for ep in export_packets:
        if not isinstance(ep, dict):
            continue
        platform_family = ep.get("platform_family")
        eid = ep.get("manual_export_packet_id")

        if platform_family not in SUPPORTED_PLATFORM_FAMILIES:
            unsupported_or_blocked.append({
                "manual_export_packet_id": eid,
                "draft_id": ep.get("draft_id"),
                "platform_family": platform_family,
                "reason": "unsupported_platform_family",
            })
            blocked_reasons.append("unsupported_platform_family:%s" % eid)
            continue

        if not _export_packet_clean(ep):
            unsupported_or_blocked.append({
                "manual_export_packet_id": eid,
                "draft_id": ep.get("draft_id"),
                "platform_family": platform_family,
                "reason": "export_packet_not_clean",
                "export_status": ep.get("export_status"),
                "export_blocked_reasons": list(ep.get("blocked_reasons") or []),
            })
            continue

        record = _build_template_record(ep)
        rec_violations = _record_unsafe(record)
        if rec_violations:
            blocked_reasons.extend("safety:%s" % v for v in rec_violations)
        # Attribution must survive into the template.
        if (
            not record["source_artifact_ids"]
            and not record["is_general_process_content"]
        ):
            record["blocked_reasons"].append("missing_source_attribution")
            blocked_reasons.append("missing_source_attribution:%s" % eid)

        template_records.append(record)
        family_counts[platform_family] = family_counts.get(platform_family, 0) + 1

    if export_batch_packet.get("packet_status") == "blocked":
        blocked_reasons.append("source_export_batch_packet_blocked")

    flags = _hard_boundary_flags()
    flag_violations = _audit_flags(flags)
    if flag_violations:
        blocked_reasons.extend("safety:%s" % v for v in flag_violations)

    safety_audit = {
        "violations": flag_violations,
        "unsafe_flag_count": len(flag_violations),
    }

    packet_status = "pass" if not blocked_reasons else "blocked"

    src_id = export_batch_packet.get("manual_export_batch_packet_id")

    return {
        "platform_manual_template_packet_id": platform_manual_template_packet_id
        or "platform_templates_%s" % (src_id or "unknown"),
        "created_at": STATIC_TIMESTAMP,
        "source_refs": list(source_refs or []),
        "source_manual_export_batch_packet_id": src_id,
        "platform_template_records": template_records,
        "unsupported_or_blocked_exports": unsupported_or_blocked,
        "operator_final_checklist": list(_OPERATOR_FINAL_CHECKLIST),
        "platform_family_summary": family_counts,
        "hard_boundary_flags": flags,
        "safety_audit": safety_audit,
        "blocked_reasons": blocked_reasons,
        "packet_status": packet_status,
    }


def build_from_config(config):
    """Build the template packet from an in-memory config bundle.

    Expected keys:
        * export_batch_packet: a 0107 manual export batch packet
    """
    if not isinstance(config, dict):
        config = {}
    export_batch_packet = config.get("export_batch_packet") or {}
    return build_platform_manual_template_packet(
        export_batch_packet,
        source_refs=list(config.get("source_refs") or []),
    )


def build_from_config_file(config_path=None):
    """Build the template packet from a local config fixture.

    If the config only references the 0107 export batch (no inline packet), build
    the 0107 packet from its own default fixture first. Local reads only.
    """
    config = load_config(config_path)
    if not config.get("export_batch_packet"):
        from live_contentops import pre_alpha_manual_export_batch
        config["export_batch_packet"] = (
            pre_alpha_manual_export_batch.build_from_config_file()
        )
    if not config.get("source_refs"):
        config["source_refs"] = [
            os.path.basename(os.path.abspath(config_path or DEFAULT_CONFIG)),
        ]
    return build_from_config(config)


def summary(config_path=None):
    """Deterministic local capability summary for the CLI. Fixture read only."""
    out = {
        "status": "pre-alpha platform-specific manual export templates active",
        "local_only": True,
        "fixture_only": True,
        "design_only": True,
        "manual_copy_paste_only": True,
        "operator_final_check_required": True,
        "supported_platform_families": sorted(SUPPORTED_PLATFORM_FAMILIES),
        "provider_call_made": False,
        "network_call_made": False,
        "credential_read": False,
        "fake_alpha_output": False,
        "public_postable_output": False,
        "auto_publish": False,
        "platform_api_call_allowed_now": False,
        "platform_api_payload_generated": False,
        "scheduler_allowed": False,
        "automatic_metrics_ingestion_allowed": False,
        "scraping_allowed": False,
        "live_execution_allowed_now": False,
        "current_platform_spec_verified": False,
    }
    try:
        packet = build_from_config_file(config_path)
        out["packet_status"] = packet.get("packet_status")
        records = packet.get("platform_template_records") or []
        out["source_export_packet_count"] = len(records) + len(
            packet.get("unsupported_or_blocked_exports") or []
        )
        out["platform_template_record_count"] = len(records)
        out["unsupported_or_blocked_count"] = len(
            packet.get("unsupported_or_blocked_exports") or []
        )
        out["platform_family_counts"] = packet.get("platform_family_summary") or {}
        out["unsafe_flag_count"] = packet["safety_audit"]["unsafe_flag_count"]
    except Exception:
        out["packet_status"] = "unavailable"
    return out

