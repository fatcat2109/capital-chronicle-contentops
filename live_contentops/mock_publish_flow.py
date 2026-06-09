"""Local-only mock publish flow + metrics capture dry-run (Task 0080).

Wires the automation-readiness rails end to end against MOCK transports only:
grounded research brief -> draft review packet -> canonical social post ->
platform dry-run payload -> approval check -> kill-switch check -> mock publish
result -> mock post URL -> simulated/manual metrics placeholder -> redacted
audit event.

This module performs NO network/search/provider/LLM/platform/credential access.
It never posts, schedules, scrapes, replies, or DMs. Live publishing is
impossible here. Metrics are simulated/manual placeholders only (never fetched
or scraped). Mock URLs use a clearly-fake mock:// scheme and are not real
platform endpoints. Nothing is promoted to public-ready status.
"""

import json
import os

from live_contentops import platform_adapter_contracts as pac
from live_contentops import approval_audit_contracts as aac

SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "schemas")
REQUEST_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "mock_publish_request.schema.json")
RESULT_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "mock_publish_result.schema.json")
METRICS_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "mock_metrics_placeholder.schema.json")
RUN_SCHEMA_PATH = os.path.join(SCHEMA_DIR, "mock_publish_flow_run.schema.json")


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_request_schema():
    return _load(REQUEST_SCHEMA_PATH)


def load_result_schema():
    return _load(RESULT_SCHEMA_PATH)


def load_metrics_schema():
    return _load(METRICS_SCHEMA_PATH)


def load_run_schema():
    return _load(RUN_SCHEMA_PATH)


# Clearly-fake mock URL scheme. NOT a real platform endpoint; not for verification.
def _mock_post_url(platform_id, post_id):
    return "mock://%s/local-dry-run/%s" % (platform_id, post_id)


def _mock_platform_post_id(platform_id, post_id):
    return "mock-%s-%s" % (platform_id, post_id)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def build_mock_request(post_id, platform_id, dry_run_payload_id, approval_id,
                       kill_switch_id):
    """Build a mock publish request. Mock-only; no transport is invoked."""
    return {
        "request_id": "req-%s-%s" % (platform_id, post_id),
        "source_post_id": post_id,
        "platform_id": platform_id,
        "dry_run_payload_id": dry_run_payload_id,
        "approval_id": approval_id,
        "kill_switch_id": kill_switch_id,
        "mock_only": True,
        "dry_run": True,
        "not_public_postable": True,
        "live_posting_enabled": False,
        "credential_accessed": False,
        "network_accessed": False,
    }


def build_metrics_placeholder(platform_id, mock_platform_post_id,
                              metrics_source="simulated_placeholder"):
    """Build a simulated/manual metrics placeholder. Never fetched or scraped."""
    return {
        "metrics_id": "metrics-%s-%s" % (platform_id, mock_platform_post_id),
        "mock_platform_post_id": mock_platform_post_id,
        "platform_id": platform_id,
        "metrics_source": metrics_source,
        "fetched_from_platform": False,
        "scraped": False,
        "network_accessed": False,
        "values": None,
    }



# ---------------------------------------------------------------------------
# Core flow (one platform)
# ---------------------------------------------------------------------------

def run_mock_publish_for_platform(post, platform_id, approval_record,
                                  kill_switch_state):
    """Run the mock publish gate for one platform.

    Returns a dict with the dry-run payload, mock result, metrics placeholder,
    and a redacted audit event. Fails closed: status is "blocked" unless the
    safety render passes AND approval permits mock publish AND the kill switch
    permits mock publish. No transport is ever invoked.
    """
    post_id = post.get("post_id", "")

    payload = pac.render_platform_payload(post, platform_id)
    dry_run_payload_id = "dryrun-%s-%s" % (platform_id, post_id)

    approval_id = (approval_record or {}).get("approval_id", "")
    kill_switch_id = (kill_switch_state or {}).get("kill_switch_id", "")

    request = build_mock_request(
        post_id, platform_id, dry_run_payload_id, approval_id, kill_switch_id
    )

    blocking_errors = []
    warnings = list(payload.get("warnings", []))

    if payload.get("render_status") != "rendered":
        blocking_errors.extend(
            "dry_run:%s" % e for e in payload.get("blocking_errors", [])
        )

    gate = aac.can_proceed_to_mock_publish(approval_record, kill_switch_state)
    if not gate["allowed"]:
        blocking_errors.extend("gate:%s" % r for r in gate["reasons"])

    status = "blocked" if blocking_errors else "mock_published"

    if status == "mock_published":
        mock_post_url = _mock_post_url(platform_id, post_id)
        mock_platform_post_id = _mock_platform_post_id(platform_id, post_id)
        metrics = build_metrics_placeholder(platform_id, mock_platform_post_id)
    else:
        mock_post_url = None
        mock_platform_post_id = None
        metrics = build_metrics_placeholder(platform_id, None)

    result = {
        "result_id": "res-%s-%s" % (platform_id, post_id),
        "request_id": request["request_id"],
        "platform_id": platform_id,
        "status": status,
        "mock_post_url": mock_post_url,
        "mock_platform_post_id": mock_platform_post_id,
        "warnings": warnings,
        "blocking_errors": blocking_errors,
        "live_posting_enabled": False,
        "credential_accessed": False,
        "network_accessed": False,
    }

    audit = aac.build_redacted_audit_event(
        audit_event_id="audit-%s-%s" % (platform_id, post_id),
        event_type="mock_publish_dry_run",
        source_post_id=post_id,
        decision=status,
        platform_id=platform_id,
        approval_id=approval_id or None,
        dry_run_payload_id=dry_run_payload_id,
        warnings=warnings,
        blocking_errors=blocking_errors,
    )

    return {
        "request": request,
        "dry_run_payload": payload,
        "result": result,
        "metrics": metrics,
        "audit_event": audit,
    }



# ---------------------------------------------------------------------------
# Core flow (all platforms) + run summary
# ---------------------------------------------------------------------------

def run_mock_publish_flow(post, approval_record, kill_switch_state,
                          platforms=None):
    """Run the mock publish gate across platforms (default: all six).

    Returns {"per_platform": {pid: result_dict}, "run_summary": {...}}.
    Fails closed per platform. No transport is ever invoked.
    """
    if platforms is None:
        platforms = list(pac.SUPPORTED_PLATFORMS)

    per_platform = {}
    passed = []
    blocked = []
    audit_ids = []

    for pid in platforms:
        out = run_mock_publish_for_platform(
            post, pid, approval_record, kill_switch_state
        )
        per_platform[pid] = out
        if out["result"]["status"] == "mock_published":
            passed.append(pid)
        else:
            blocked.append(pid)
        audit_ids.append(out["audit_event"]["audit_event_id"])

    run_summary = {
        "run_id": "run-%s" % post.get("post_id", ""),
        "platforms_attempted": list(platforms),
        "platforms_mock_passed": passed,
        "platforms_blocked": blocked,
        "audit_event_ids": audit_ids,
        "all_live_disabled": True,
        "all_network_disabled": True,
        "all_credentials_disabled": True,
    }

    return {"per_platform": per_platform, "run_summary": run_summary}


def summary():
    """Local mock-flow capability summary. No external calls."""
    return {
        "status": "ok",
        "local_only": True,
        "advisory_only": True,
        "mock_publish_flow_enabled": True,
        "mock_only": True,
        "supported_platforms": list(pac.SUPPORTED_PLATFORMS),
        "live_publish_possible_now": False,
        "metrics_fetched_or_scraped": False,
        "metrics_source_modes": ["simulated_placeholder", "manual_placeholder"],
        "credential_read_allowed_now": False,
        "network_accessed": False,
        "scheduling_allowed_now": False,
        "replies_or_dms_allowed_now": False,
        "all_outputs_not_public_postable": True,
        "requires_operator_approval": True,
    }

    return "mock-%s-%s" % (platform_id, post_id)
