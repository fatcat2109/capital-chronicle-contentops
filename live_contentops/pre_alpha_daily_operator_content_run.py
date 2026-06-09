"""Local-only pre-alpha DAILY operator content run packet generator (Task 0111).

Deterministic, repo-local. Composes the accepted 0103-0110 pre-alpha ContentOps
workbench into ONE operator summary for a single manual content run:

    seed library / editorial calendar   (0103 pre_alpha_seed_library)
    operator dashboard                   (0104 pre_alpha_operator_dashboard)
    editorial batch review               (0105 pre_alpha_editorial_batch_review)
    manual decision batch                (0106 pre_alpha_manual_decision_batch)
    manual export batch                  (0107 pre_alpha_manual_export_batch)
    platform manual templates            (0110 pre_alpha_platform_manual_templates)
    manual publish record                (0108 pre_alpha_manual_publish_record)

This is a daily MANUAL operator workbench ONLY. It composes accepted local
generators rather than duplicating business logic. It NEVER approves
automatically, posts, schedules, calls a platform / provider / LLM / network,
scrapes, ingests metrics, reads `.env`, auto-publishes, or produces
public-postable / publish-ready output. Operator final check is always required.

Blocked seeds / exports / records are preserved with reasons and counted, never
dropped or shown as "ready". Revision / rejected items are surfaced as not ready,
never as templates ready for posting. The packet fails closed
(packet_status="blocked") if any hard-boundary flag is unsafe, any composed child
packet is unexpectedly blocked, any platform API payload appears, or any output
implies auto-publish / public-postable status.
"""

import json
import os

from live_contentops.pre_alpha_content_engine import STATIC_TIMESTAMP
from live_contentops import pre_alpha_seed_library as seed_lib
from live_contentops import pre_alpha_operator_dashboard as dashboard
from live_contentops import pre_alpha_editorial_batch_review as batch_review
from live_contentops import pre_alpha_manual_decision_batch as decision_batch
from live_contentops import pre_alpha_manual_export_batch as export_batch
from live_contentops import pre_alpha_platform_manual_templates as templates
from live_contentops import pre_alpha_manual_publish_record as publish_record

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")
SCHEMA_PATH = os.path.join(
    SCHEMA_DIR, "pre_alpha_daily_operator_content_run_packet.schema.json"
)

FIXTURE_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "fixtures",
    "pre_alpha_daily_operator_content_run",
)
DEFAULT_CONFIG = os.path.join(
    FIXTURE_DIR, "valid_daily_operator_content_run_config.json"
)

# Hard-boundary flags pinned on every run packet, independent of input.
_REQUIRED_FLAGS = {
    "local_only": True,
    "fixture_only": True,
    "manual_operator_workbench_only": True,
    "manual_review_required": True,
    "operator_final_check_required": True,
    "public_postable": False,
    "auto_approval": False,
    "auto_publish": False,
    "platform_api_call_allowed_now": False,
    "provider_call_allowed_now": False,
    "network_call_allowed_now": False,
    "scheduler_allowed": False,
    "automatic_metrics_ingestion_allowed": False,
    "scraping_allowed": False,
    "credential_or_env_read_allowed": False,
    "live_execution_allowed_now": False,
}

_FINAL_OPERATOR_CHECKLIST = [
    "This is a daily local workbench summary; nothing here is posted or scheduled.",
    "Review every safe review-queue item and decision before any manual copy/paste.",
    "Only ACCEPTED + clean export packets become platform copy/paste templates.",
    "Revision / rejected / blocked items are NOT ready; resolve them manually.",
    "Platform length/format notes are conservative local guidance, NOT verified "
    "current platform specs; verify the live platform yourself.",
    "Manually copy/paste and publish yourself; this system never posts for you.",
    "Record a manual publish only AFTER you have published it by hand.",
    "Do not treat any item as publish-ready or platform-ready.",
]


def load_schema():
    with open(os.path.abspath(SCHEMA_PATH), "r", encoding="utf-8") as f:
        return json.load(f)


def load_config(config_path=None):
    """Load the 0111 run config if present. Local file read only.

    The config is optional; when absent the run composes child generators from
    their own default fixtures. Supported keys:
        * run_label: str
        * manual_records: list of operator-supplied manual publish records
        * source_refs: list of str
    """
    target = config_path or DEFAULT_CONFIG
    try:
        with open(os.path.abspath(target), "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


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


def _child_blocked(blocked_reasons, label, child_packet):
    """Record a fail-closed reason if a composed child packet is blocked."""
    if isinstance(child_packet, dict) and child_packet.get("packet_status") == "blocked":
        blocked_reasons.append("child_packet_blocked:%s" % label)



def build_daily_operator_content_run_packet(config=None,
                                            daily_operator_content_run_packet_id=None,
                                            source_refs=None):
    """Build a deterministic daily operator content run packet.

    Composes the accepted 0103-0110 generators. Counts reconcile with the
    composed child summaries. Blocked / not-ready items are preserved and
    counted. Nothing is approved, exported as public, published, scheduled, or
    sent. Safety flags are pinned and the packet fails closed on any unsafe or
    unexpectedly-blocked condition.
    """
    if not isinstance(config, dict):
        config = {}
    blocked_reasons = []

    run_label = str(config.get("run_label") or "daily_operator_content_run")
    manual_records = list(config.get("manual_records") or [])

    # --- Compose accepted child generators (each builds its chain locally). ---
    dash = dashboard.build_dashboard_packet()
    review = batch_review.build_batch_review_packet_from_files()
    decisions = decision_batch.build_from_config_file()
    exports = export_batch.build_from_config_file()
    tmpl = templates.build_platform_manual_template_packet(exports)
    # Drive the publish-record stage with config records (default [] = nothing
    # published yet) rather than the 0108 negative-test default fixture.
    records = publish_record.build_manual_publish_record_packet(
        exports, manual_records=manual_records
    )

    for label, child in (
        ("dashboard", dash),
        ("review_batch", review),
        ("decision_batch", decisions),
        ("export_batch", exports),
        ("platform_templates", tmpl),
        ("manual_publish_record", records),
    ):
        _child_blocked(blocked_reasons, label, child)

    # --- Summaries (read-only projections of child packets). ---
    seed_and_calendar_summary = {
        "library_id": review.get("seed_library_summary", {}).get("library_id"),
        "total_seeds": review.get("seed_library_summary", {}).get("total_seeds", 0),
        "safe_seed_count": review.get("seed_library_summary", {}).get("safe_seed_count", 0),
        "blocked_seed_count": review.get("seed_library_summary", {}).get("blocked_seed_count", 0),
        "planning_window": review.get("planning_window"),
        "supported_content_zones": sorted(seed_lib.ALLOWED_CONTENT_ZONES),
    }

    dashboard_summary = {
        "dashboard_packet_id": dash.get("dashboard_packet_id"),
        "packet_status": dash.get("packet_status"),
        "pipeline_demo_status": dash.get("pipeline_demo_summary", {}).get("demo_status"),
        "unsafe_flag_count": dash.get("safety_audit", {}).get("unsafe_flag_count", 0),
    }

    review_batch_summary = {
        "batch_review_packet_id": review.get("batch_review_packet_id"),
        "packet_status": review.get("packet_status"),
        "selected_safe_seed_count": len(review.get("selected_safe_seed_ids") or []),
        "blocked_seed_count": len(review.get("blocked_seed_ids") or []),
        "review_queue_item_count": len(review.get("review_queue_items") or []),
    }

    _dec_records = decisions.get("decision_records") or []
    _rev_count = sum(
        1 for r in _dec_records if r.get("decision_status") == "revision_requested"
    )
    _rej_count = sum(
        1 for r in _dec_records if r.get("decision_status") == "rejected"
    )
    _blk_count = sum(
        1 for r in _dec_records
        if r.get("decision_status") not in (
            "approved_manual_publish_prep", "revision_requested", "rejected"
        )
    )
    decision_batch_summary = {
        "manual_decision_batch_packet_id": decisions.get("manual_decision_batch_packet_id"),
        "packet_status": decisions.get("packet_status"),
        "decision_record_count": len(_dec_records),
        "approval_packet_count": len(decisions.get("approval_packets") or []),
        "revision_requested_count": _rev_count,
        "rejected_count": _rej_count,
        "blocked_decision_count": _blk_count,
    }

    export_batch_summary = {
        "manual_export_batch_packet_id": exports.get("manual_export_batch_packet_id"),
        "packet_status": exports.get("packet_status"),
        "manual_export_packet_count": len(exports.get("manual_export_packets") or []),
        "content_ledger_entry_count": len(exports.get("content_ledger_entries") or []),
        "non_exported_decision_count": len(exports.get("non_exported_decision_report") or []),
        "manually_published_count": sum(
            1 for le in (exports.get("content_ledger_entries") or [])
            if le.get("lifecycle_status") == "manually_published"
        ),
    }

    platform_template_summary = {
        "platform_manual_template_packet_id": tmpl.get("platform_manual_template_packet_id"),
        "packet_status": tmpl.get("packet_status"),
        "platform_template_record_count": len(tmpl.get("platform_template_records") or []),
        "unsupported_or_blocked_count": len(tmpl.get("unsupported_or_blocked_exports") or []),
        "platform_family_counts": tmpl.get("platform_family_summary") or {},
    }

    manual_publish_record_summary = {
        "manual_publish_record_packet_id": records.get("manual_publish_record_packet_id"),
        "packet_status": records.get("packet_status"),
        "eligible_export_packet_count": records.get("eligible_export_packet_count", 0),
        "recorded_publish_count": records.get("recorded_publish_count", 0),
        "not_recorded_count": records.get("not_recorded_count", 0),
        "blocked_record_count": records.get("blocked_record_count", 0),
    }

    # --- Ready vs not-ready reconciliation. ---
    # Ready = clean platform copy/paste templates the operator may manually post.
    ready_count = len(tmpl.get("platform_template_records") or [])
    # Not ready = blocked seeds + non-exported decisions + unsupported/blocked
    # templates + blocked records + eligible-but-not-yet-recorded exports.
    blocked_or_not_ready_count = (
        len(review.get("blocked_seed_ids") or [])
        + len(exports.get("non_exported_decision_report") or [])
        + len(tmpl.get("unsupported_or_blocked_exports") or [])
        + records.get("blocked_record_count", 0)
        + records.get("not_recorded_count", 0)
    )

    # --- Preserved blocked-content report (never dropped). ---
    blocked_content_report = []
    for item in (review.get("blocked_content_report") or []):
        blocked_content_report.append({"stage": "editorial_batch_review", **item})
    for item in (exports.get("non_exported_decision_report") or []):
        blocked_content_report.append({"stage": "manual_export_batch", **item})
    for item in (tmpl.get("unsupported_or_blocked_exports") or []):
        blocked_content_report.append({"stage": "platform_templates", **item})
    for item in (records.get("blocked_record_report") or []):
        blocked_content_report.append({"stage": "manual_publish_record", **item})

    operator_action_queue = _operator_action_queue(
        review_batch_summary, decision_batch_summary, platform_template_summary,
        manual_publish_record_summary, ready_count, blocked_or_not_ready_count
    )

    flags = _hard_boundary_flags()
    flag_violations = _audit_flags(flags)
    if flag_violations:
        blocked_reasons.extend("safety:%s" % v for v in flag_violations)

    # Defense in depth: no composed export/ledger may be manually_published here,
    # and no platform template may imply publish/platform readiness.
    if export_batch_summary["manually_published_count"] != 0:
        blocked_reasons.append("export_manually_published_in_run")
    for rec in (tmpl.get("platform_template_records") or []):
        if (
            rec.get("public_postable") is not False
            or rec.get("platform_api_call_allowed") is not False
        ):
            blocked_reasons.append(
                "template_implies_publish_readiness:%s"
                % rec.get("manual_export_packet_id")
            )
        if rec.get("platform_api_payload") is not None:
            blocked_reasons.append(
                "template_platform_api_payload:%s"
                % rec.get("manual_export_packet_id")
            )

    safety_audit = {
        "violations": flag_violations,
        "unsafe_flag_count": len(flag_violations),
    }

    packet_status = "pass" if not blocked_reasons else "blocked"

    source_packet_ids = {
        "dashboard_packet_id": dash.get("dashboard_packet_id"),
        "batch_review_packet_id": review.get("batch_review_packet_id"),
        "manual_decision_batch_packet_id": decisions.get(
            "manual_decision_batch_packet_id"
        ),
        "manual_export_batch_packet_id": exports.get(
            "manual_export_batch_packet_id"
        ),
        "platform_manual_template_packet_id": tmpl.get(
            "platform_manual_template_packet_id"
        ),
        "manual_publish_record_packet_id": records.get(
            "manual_publish_record_packet_id"
        ),
    }

    return {
        "daily_operator_content_run_packet_id": daily_operator_content_run_packet_id
        or "daily_run_%s" % run_label,
        "created_at": STATIC_TIMESTAMP,
        "run_label": run_label,
        "source_refs": list(source_refs or []),
        "source_packet_ids": source_packet_ids,
        "seed_and_calendar_summary": seed_and_calendar_summary,
        "dashboard_summary": dashboard_summary,
        "review_batch_summary": review_batch_summary,
        "decision_batch_summary": decision_batch_summary,
        "export_batch_summary": export_batch_summary,
        "platform_template_summary": platform_template_summary,
        "manual_publish_record_summary": manual_publish_record_summary,
        "ready_for_operator_copy_paste_count": ready_count,
        "blocked_or_not_ready_count": blocked_or_not_ready_count,
        "operator_action_queue": operator_action_queue,
        "blocked_content_report": blocked_content_report,
        "final_operator_checklist": list(_FINAL_OPERATOR_CHECKLIST),
        "hard_boundary_flags": flags,
        "safety_audit": safety_audit,
        "blocked_reasons": blocked_reasons,
        "packet_status": packet_status,
    }


def _operator_action_queue(review_s, decision_s, template_s, record_s,
                           ready_count, not_ready_count):
    """Deterministic suggested MANUAL operator actions (review-only)."""
    actions = []
    if review_s.get("review_queue_item_count", 0) > 0:
        actions.append(
            "Manually review %d review-queue item(s) before any draft work."
            % review_s["review_queue_item_count"]
        )
    if decision_s.get("revision_requested_count", 0) > 0:
        actions.append(
            "Address %d revision-requested decision(s); they are NOT ready to post."
            % decision_s["revision_requested_count"]
        )
    if decision_s.get("rejected_count", 0) > 0:
        actions.append(
            "%d decision(s) were rejected and are excluded from export; no action to post."
            % decision_s["rejected_count"]
        )
    if ready_count > 0:
        actions.append(
            "Manually copy/paste %d platform template(s) after final operator check; "
            "this system never posts for you." % ready_count
        )
    if template_s.get("unsupported_or_blocked_count", 0) > 0:
        actions.append(
            "Resolve %d unsupported/blocked export(s) before templating."
            % template_s["unsupported_or_blocked_count"]
        )
    if record_s.get("not_recorded_count", 0) > 0:
        actions.append(
            "%d eligible export(s) have no manual publish record yet; record only "
            "AFTER you publish by hand." % record_s["not_recorded_count"]
        )
    if record_s.get("blocked_record_count", 0) > 0:
        actions.append(
            "Fix %d blocked manual publish record(s); invalid records never imply publication."
            % record_s["blocked_record_count"]
        )
    actions.append(
        "All publishing remains manual and human-reviewed; no automation is enabled."
    )
    return actions


def build_from_config_file(config_path=None):
    """Build the run packet from a local config fixture. Local reads only."""
    config = load_config(config_path)
    if not config.get("source_refs"):
        config["source_refs"] = [
            os.path.basename(os.path.abspath(config_path or DEFAULT_CONFIG)),
        ]
    return build_daily_operator_content_run_packet(
        config, source_refs=list(config.get("source_refs") or [])
    )


def summary(config_path=None):
    """Deterministic local capability summary for the CLI. Fixture read only."""
    out = {
        "status": "pre-alpha daily operator content run packet active",
        "local_only": True,
        "fixture_only": True,
        "design_only": True,
        "manual_operator_workbench_only": True,
        "manual_review_required": True,
        "operator_final_check_required": True,
        "provider_call_made": False,
        "network_call_made": False,
        "credential_read": False,
        "fake_alpha_output": False,
        "public_postable_output": False,
        "auto_approval": False,
        "auto_publish": False,
        "platform_api_call_allowed_now": False,
        "platform_api_payload_generated": False,
        "scheduler_allowed": False,
        "automatic_metrics_ingestion_allowed": False,
        "scraping_allowed": False,
        "live_execution_allowed_now": False,
    }
    try:
        packet = build_from_config_file(config_path)
        out["packet_status"] = packet.get("packet_status")
        out["ready_for_operator_copy_paste_count"] = packet.get(
            "ready_for_operator_copy_paste_count"
        )
        out["blocked_or_not_ready_count"] = packet.get("blocked_or_not_ready_count")
        out["review_queue_item_count"] = packet["review_batch_summary"][
            "review_queue_item_count"
        ]
        out["decision_record_count"] = packet["decision_batch_summary"][
            "decision_record_count"
        ]
        out["export_packet_count"] = packet["export_batch_summary"][
            "manual_export_packet_count"
        ]
        out["platform_template_record_count"] = packet["platform_template_summary"][
            "platform_template_record_count"
        ]
        out["recorded_publish_count"] = packet["manual_publish_record_summary"][
            "recorded_publish_count"
        ]
        out["unsafe_flag_count"] = packet["safety_audit"]["unsafe_flag_count"]
    except Exception:
        out["packet_status"] = "unavailable"
    return out


