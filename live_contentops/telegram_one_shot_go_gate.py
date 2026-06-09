REQUIRED_PHRASE = "I APPROVE TELEGRAM PRIVATE SANDBOX ONE-SHOT LIVE POST FROM PROCESS ENV ONLY"

def validate_go_gate(gate: dict) -> dict:
    """Validates the exact GO gate state. Returns dictionary with 'status' and 'reasons'."""
    reasons = []
    status = "GO_GATE_DRY_RUN_ALLOWED"

    if gate.get("exact_go_phrase_present") != REQUIRED_PHRASE:
        reasons.append("Exact GO phrase is missing or incorrect")

    if not gate.get("source_packet_dry_run_ready"):
        reasons.append("source_packet_dry_run_ready must be true")

    if not gate.get("source_queue_item_validated"):
        reasons.append("source_queue_item_validated must be true")

    if gate.get("approval_ledger_state") != "operator_approved_for_one_shot_later":
        reasons.append("approval_ledger_state must be operator_approved_for_one_shot_later")

    if gate.get("kill_switch_state") != "permit_only_scoped_telegram_live_pilot":
        reasons.append("kill_switch_state must be permit_only_scoped_telegram_live_pilot")

    if gate.get("redaction_state") != "redacted" or gate.get("target_channel_state") != "private_sandbox_placeholder_only":
        reasons.append("target must be redacted sandbox placeholder only")

    if gate.get("live_attempt_count", 0) > 0:
        reasons.append("live_attempt_count must be 0 prior to execution")

    if gate.get("platform_id") != "telegram":
        reasons.append("platform_id must be telegram")

    if gate.get("credential_source_required_later") != "process_env_only" or gate.get("env_file_read_allowed"):
        reasons.append("Credential source must be process_env_only with env_file reads disallowed")

    if gate.get("network_accessed") or gate.get("env_read_performed") or gate.get("telegram_api_called") or gate.get("live_post_sent"):
        reasons.append("Live execution flags must be false during GO gate check")

    if gate.get("scheduling_enabled") or gate.get("replies_or_dms_enabled") or gate.get("scraping_enabled") or gate.get("metrics_fetched") or gate.get("autonomous_mode"):
        reasons.append("Scheduler/autonomous flags must be false")

    if reasons:
        status = "BLOCKED"

    return {"status": status, "reasons": reasons}
