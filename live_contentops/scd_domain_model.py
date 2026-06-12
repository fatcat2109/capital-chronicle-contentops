"""Unified Supervised Content Distribution (SCD) domain-model validators.

Local-only, deterministic, fail-closed. No network, no credentials, no provider
or platform API, no scheduler, no live dispatch. This module only validates the
shape and cross-object invariants of the seven core domain objects:

    ContentIntentPacket -> CanonicalSocialPost -> PlatformPayload
        -> ApprovalPacket -> DispatchPacket -> RedactedAuditEvent -> MetricsRecord

Validators return a dict: {"validation_state": <STATE>, "reasons": [...]}
where STATE is one of PASS / BLOCKED / REVIEW_REQUIRED / UNKNOWN.
"""
import json
import re
from pathlib import Path

import jsonschema

SCHEMA_DIR = Path(__file__).parent.parent / "schemas"

PASS = "PASS"
BLOCKED = "BLOCKED"
REVIEW_REQUIRED = "REVIEW_REQUIRED"
UNKNOWN = "UNKNOWN"

# Lanes A/B are usable now (process / grounded-news-context). Lanes C-F are gated
# on real artifacts and must remain blocked unless artifact requirements are met.
LANES_ALLOWED_NOW = {"A", "B"}
LANES_ARTIFACT_GATED = {"C", "D", "E", "F"}

# Forbidden financial / signal / execution language (fail-closed -> BLOCKED).
FORBIDDEN_LANGUAGE = [
    r"\bbuy\b", r"\bsell\b", r"\bhold\b", r"\blong\b", r"\bshort\b",
    r"\bentry\b", r"\bexit\b", r"target price", r"price target",
    r"position sizing", r"\bsignal\b", r"model says (buy|sell)",
    r"\bexecution\b", r"\bbroker\b", r"\border\b", r"\bfill\b", r"\bpnl\b",
    r"order-routing", r"guaranteed (return|profit|prediction)",
    r"fake alpha", r"\bwatch this level\b",
]

# Credential / token-like patterns. Presence in audit/dispatch context -> BLOCKED.
SECRET_PATTERNS = [
    r"\bapi[_-]?key\b", r"\baccess[_-]?token\b", r"\bclient[_-]?secret\b",
    r"\brefresh[_-]?token\b", r"\bbearer\b", r"\bsk-[a-z0-9]{8,}\b",
    r"\b\d{6,}:[A-Za-z0-9_-]{30,}\b",  # telegram bot token shape
    r"\bAKIA[0-9A-Z]{12,}\b",          # aws-key shape
]


def _load_schema(name):
    with open(SCHEMA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def _schema_ok(payload, schema_name):
    """Return (ok, message). ok=False means schema validation failed."""
    try:
        jsonschema.validate(instance=payload, schema=_load_schema(schema_name))
        return True, None
    except jsonschema.ValidationError as e:
        return False, e.message


def _find_language(text, patterns):
    hits = []
    low = (text or "").lower()
    for pat in patterns:
        if re.search(pat, low):
            hits.append(pat)
    return hits


def _scan_secrets(obj):
    """Recursively scan strings (keys and values) for secret-like patterns."""
    hits = []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(k, str) and _find_language(k, SECRET_PATTERNS):
                    hits.append(f"secret-like key: {k}")
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            for h in _find_language(node, SECRET_PATTERNS):
                hits.append(f"secret-like value matched: {h}")

    walk(obj)
    return hits


def _result(reasons_blocked, reasons_review=None, reasons_unknown=None):
    """Resolve precedence: BLOCKED > UNKNOWN > REVIEW_REQUIRED > PASS."""
    if reasons_blocked:
        return {"validation_state": BLOCKED, "reasons": reasons_blocked}
    if reasons_unknown:
        return {"validation_state": UNKNOWN, "reasons": reasons_unknown}
    if reasons_review:
        return {"validation_state": REVIEW_REQUIRED, "reasons": reasons_review}
    return {"validation_state": PASS, "reasons": ["ok"]}


def validate_content_intent_packet(payload):
    ok, msg = _schema_ok(payload, "scd_content_intent_packet.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    if payload.get("public_ready"):
        blocked.append("public_ready must be false in this task")
    if payload.get("live_dispatch_implied"):
        blocked.append("live_dispatch_implied must be false in this task")

    lane = payload.get("content_lane")
    text = payload.get("text_content", "")
    for hit in _find_language(text, FORBIDDEN_LANGUAGE):
        blocked.append(f"forbidden language: {hit}")
    for hit in _scan_secrets(payload):
        blocked.append(hit)

    # Lane C-F gating: require real artifact references.
    claims_backed = payload.get("claims_artifact_backed")
    artifact_ids = payload.get("source_artifact_ids", []) or []
    for a_id in artifact_ids:
        if any(bad in a_id.lower() for bad in ("fake", "mock", "invented")):
            blocked.append(f"invented artifact id: {a_id}")
    if lane in LANES_ARTIFACT_GATED:
        if not claims_backed or not artifact_ids:
            blocked.append(
                f"lane {lane} requires real artifact ids and claims_artifact_backed=true"
            )
    if claims_backed and not artifact_ids:
        blocked.append("claims_artifact_backed without source_artifact_ids")

    # UNKNOWN: cannot establish evidence / freshness / authority classification.
    if not payload.get("evidence_refs"):
        unknown.append("no evidence_refs; evidence basis cannot be established")
    if not payload.get("freshness_status"):
        unknown.append("freshness_status missing; cannot establish freshness")
    if not payload.get("authority_level") or not payload.get("classification"):
        unknown.append("authority/classification missing")

    # REVIEW_REQUIRED: required citations/limitations incomplete but recoverable.
    if lane and lane not in LANES_ALLOWED_NOW and lane not in LANES_ARTIFACT_GATED:
        review.append(f"unrecognized lane '{lane}' needs human judgment")
    if payload.get("required_citations") == []:
        review.append("required_citations empty; confirm none are needed")

    declared = payload.get("validation_state")
    res = _result(blocked, review, unknown)
    if declared and declared != res["validation_state"]:
        res.setdefault("reasons", []).append(
            f"declared validation_state '{declared}' != computed '{res['validation_state']}'"
        )
        if res["validation_state"] == PASS:
            res = {"validation_state": REVIEW_REQUIRED, "reasons": res["reasons"]}
    return res


def validate_canonical_social_post(payload):
    ok, msg = _schema_ok(payload, "scd_canonical_social_post.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    if payload.get("public_postable"):
        blocked.append("public_postable must be false in this task")
    if payload.get("live_posting_enabled"):
        blocked.append("live_posting_enabled must be false in this task")

    text = payload.get("canonical_text", "")
    for hit in _find_language(text, FORBIDDEN_LANGUAGE):
        blocked.append(f"forbidden language: {hit}")
    for hit in _scan_secrets(payload):
        blocked.append(hit)

    guard = payload.get("guardrail_summary", {})
    for flag in ("no_financial_advice", "no_signal_language", "no_execution_language"):
        if guard.get(flag) is not True:
            blocked.append(f"guardrail {flag} must be true")
    if guard.get("limitations_present") is not True:
        review.append("limitations_present not asserted; confirm limitations")

    if not payload.get("source_intent_packet_id"):
        unknown.append("source_intent_packet_id missing; lineage unknown")
    if not payload.get("limitations"):
        review.append("no limitations listed; confirm none required")

    return _result(blocked, review, unknown)


def validate_platform_payload(payload):
    ok, msg = _schema_ok(payload, "scd_platform_payload.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    # Live eligibility must be false in all current fixtures.
    if payload.get("live_eligibility"):
        blocked.append("live_eligibility must be false in this task")
    if payload.get("mode") == "supervised_live_future" and payload.get("live_eligibility"):
        blocked.append("supervised_live_future may not be live-eligible now")

    text = payload.get("payload_preview", {}).get("text", "")
    for hit in _find_language(text, FORBIDDEN_LANGUAGE):
        blocked.append(f"forbidden language: {hit}")
    for hit in _scan_secrets(payload):
        blocked.append(hit)

    limit = payload.get("character_limit", {})
    if isinstance(limit, dict) and limit.get("max") and limit.get("current"):
        if limit["current"] > limit["max"]:
            blocked.append("payload exceeds platform character limit")

    if not payload.get("canonical_post_id"):
        unknown.append("canonical_post_id missing; lineage unknown")

    return _result(blocked, review, unknown)


def validate_approval_packet(payload):
    ok, msg = _schema_ok(payload, "scd_approval_packet.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    # No automatic approval.
    if payload.get("auto_approved"):
        blocked.append("auto_approved must be false; approval cannot be automatic")
    if payload.get("operator_review_required") is not True:
        blocked.append("operator_review_required must be true")
    if payload.get("revocation_ready") is not True:
        review.append("revocation_ready should be true (approval must be revocable)")

    for hit in _scan_secrets(payload):
        blocked.append(hit)

    guard = payload.get("guardrail_report_summary", {})
    unresolved = guard.get("unresolved_states", []) or []
    if unresolved:
        blocked.append(f"unresolved upstream states present: {unresolved}")
    if guard.get("all_posts_pass") is not True:
        blocked.append("not all included posts are PASS")

    if not payload.get("included_post_refs"):
        unknown.append("no included_post_refs; nothing to approve")

    state = payload.get("approval_state")
    if state == "operator_approved_for_mock_dispatch" and not blocked:
        review.append("approved for mock dispatch; confirm operator signature exists")

    return _result(blocked, review, unknown)


def validate_dispatch_packet(payload):
    ok, msg = _schema_ok(payload, "scd_dispatch_packet.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    # No executable / live dispatch in this task.
    if payload.get("executable_dispatch"):
        blocked.append("executable_dispatch must be false in this task")
    if payload.get("live_ready"):
        blocked.append("live_ready must be false in this task")
    if payload.get("platform_live_gate_state") == "open_future" and payload.get("live_ready"):
        blocked.append("live gate may not be open with live_ready now")

    for hit in _scan_secrets(payload):
        blocked.append(hit)

    pre = payload.get("dispatch_preconditions", {})
    if pre.get("all_upstream_pass") is not True:
        blocked.append("dispatch blocked: not all upstream objects PASS")
    if pre.get("operator_approved") is not True:
        blocked.append("dispatch blocked: operator not approved")
    if pre.get("kill_switch_inactive_for_operation") is not True:
        blocked.append("dispatch blocked: kill switch not cleared for this operation")
    if payload.get("kill_switch_state_required") is not True:
        blocked.append("kill_switch_state_required must be true")

    if not payload.get("frozen_payload_hash_refs"):
        unknown.append("no frozen_payload_hash_refs; payload not frozen")
    if not payload.get("rollback_fallback_refs"):
        review.append("no rollback/manual fallback refs documented")

    return _result(blocked, review, unknown)


def validate_redacted_audit_event(payload):
    ok, msg = _schema_ok(payload, "scd_redacted_audit_event.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    # Reject/flag any secret-like content anywhere in the event.
    secret_hits = _scan_secrets(payload)
    proof = payload.get("secret_redaction_proof", {})
    if secret_hits:
        if proof.get("unsafe_secret_detected") is True and proof.get("redaction_applied") is True:
            # acknowledged + redacted: still block raw presence in fixtures
            blocked.append(f"raw secret-like content present despite redaction proof: {secret_hits}")
        else:
            blocked.append(f"unredacted secret-like content: {secret_hits}")

    if payload.get("network_accessed"):
        blocked.append("network_accessed must be false")
    if payload.get("credential_accessed"):
        blocked.append("credential_accessed must be false")
    if proof.get("redaction_applied") is not True:
        review.append("redaction_applied not asserted")

    if not payload.get("related_packet_refs"):
        unknown.append("no related_packet_refs; audit lineage unknown")

    return _result(blocked, review, unknown)


def validate_metrics_record(payload):
    ok, msg = _schema_ok(payload, "scd_metrics_record.schema.json")
    if not ok:
        return {"validation_state": BLOCKED, "reasons": [f"schema: {msg}"]}

    blocked, review, unknown = [], [], []

    # Scraping / live API import disabled by default.
    if payload.get("scraping_used"):
        blocked.append("scraping_used must be false; scraping is disabled")
    if payload.get("live_api_import_used"):
        blocked.append("live_api_import_used must be false in this task")

    src = payload.get("source_type")
    if src not in ("manual_entry", "mock_result", "future_read_only_import"):
        blocked.append(f"invalid metrics source_type: {src}")
    if src == "future_read_only_import":
        review.append("future_read_only_import is gated; confirm it stays disabled")

    for hit in _scan_secrets(payload):
        blocked.append(hit)

    if not (payload.get("related_post_ref") or payload.get("related_dispatch_ref")):
        unknown.append("no related post/dispatch ref; metrics lineage unknown")

    return _result(blocked, review, unknown)


# --- Cross-object pipeline invariant -------------------------------------------------

VALIDATORS_IN_ORDER = [
    ("content_intent_packet", validate_content_intent_packet),
    ("canonical_social_post", validate_canonical_social_post),
    ("platform_payload", validate_platform_payload),
    ("approval_packet", validate_approval_packet),
    ("dispatch_packet", validate_dispatch_packet),
    ("redacted_audit_event", validate_redacted_audit_event),
    ("metrics_record", validate_metrics_record),
]


def validate_dispatch_readiness(objects):
    """Fail-closed cross-object gate.

    `objects` is a dict keyed by object name (see VALIDATORS_IN_ORDER). The
    DispatchPacket can only be PASS-ready if every present upstream object is
    PASS. Any BLOCKED / UNKNOWN / REVIEW_REQUIRED upstream forces the dispatch
    readiness to fail closed. Live readiness is never granted by this function.
    """
    per_object = {}
    upstream_bad = []
    for name, fn in VALIDATORS_IN_ORDER:
        if name in objects:
            res = fn(objects[name])
            per_object[name] = res
            if name != "dispatch_packet" and res["validation_state"] != PASS:
                upstream_bad.append(f"{name}={res['validation_state']}")

    if "dispatch_packet" not in objects:
        dispatch_ready = False
        reasons = ["no dispatch_packet provided"]
    elif upstream_bad:
        dispatch_ready = False
        reasons = [f"upstream not PASS: {upstream_bad}"]
    else:
        dp = per_object.get("dispatch_packet", {})
        dispatch_ready = dp.get("validation_state") == PASS
        reasons = dp.get("reasons", [])

    return {
        "dispatch_ready": dispatch_ready,
        "live_ready": False,
        "per_object": per_object,
        "reasons": reasons,
    }
