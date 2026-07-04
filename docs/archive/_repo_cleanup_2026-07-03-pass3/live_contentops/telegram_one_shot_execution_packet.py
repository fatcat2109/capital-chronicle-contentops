FORBIDDEN_TERMS = [
    "buy", "sell", "hold", "long", "short", "target", "entry", "exit",
    "signal", "model says", "broker", "order", "execution", "guaranteed"
]

def validate_one_shot_packet(packet: dict, post_text_override: str = "") -> dict:
    """Validates a one-shot execution packet. Returns dictionary with 'status' and 'reasons'."""
    reasons = []
    status = "DRY_RUN_READY"

    # Check basic safety flags
    if packet.get("live_execution_allowed_now") or packet.get("network_accessed") or packet.get("telegram_api_called") or packet.get("live_post_sent"):
        reasons.append("Live/network capability flags must be false")
    if packet.get("env_read_performed") or packet.get("credential_accessed_by_repo") or packet.get("env_file_read_allowed"):
        reasons.append("Env/credential access flags must be false")
    if packet.get("scheduling_enabled") or packet.get("replies_or_dms_enabled") or packet.get("scraping_enabled") or packet.get("metrics_fetched"):
        reasons.append("Autonomous/scheduler capability flags must be false")

    # Check queue validation
    if not packet.get("source_queue_item_validated"):
        reasons.append("source_queue_item_validated must be true")

    # Check policy allow state
    if packet.get("automation_policy_decision") != "allowed_for_dry_run_packet_only":
        reasons.append("automation_policy_decision must be allowed_for_dry_run_packet_only")
    if packet.get("requested_future_mode") != "sandbox_one_shot_live":
        reasons.append("requested_future_mode must be sandbox_one_shot_live")

    # Check approval ledger and kill switch
    if packet.get("approval_state") != "operator_approved_for_one_shot_later":
        reasons.append("approval_state must be operator_approved_for_one_shot_later")
    if packet.get("kill_switch_state_required") != "permit_only_scoped_telegram_live_pilot":
        reasons.append("kill_switch_state_required must be permit_only_scoped_telegram_live_pilot")

    # Check redacted target
    target = packet.get("target_channel_placeholder", "")
    if "-100" in target or target.startswith("@") and "REDACTED" not in target:
        reasons.append("target_channel_placeholder must be a safe REDACTED placeholder, not a real ID")

    # Check forbidden financial language
    text = post_text_override.lower()
    if text:
        for term in FORBIDDEN_TERMS:
            if f" {term} " in f" {text} " or text.startswith(f"{term} ") or text.endswith(f" {term}"):
                reasons.append(f"Forbidden financial/signal language found: {term}")

    if reasons:
        status = "BLOCKED"

    return {"status": status, "reasons": reasons}
