class AutomationCapabilityDecision:
    def __init__(self, decision: str, reasons: list, required_next_evidence: list, forbidden_scope_flags: list):
        self.decision = decision
        self.reasons = reasons
        self.required_next_evidence = required_next_evidence
        self.forbidden_scope_flags = forbidden_scope_flags

    def to_dict(self):
        return {
            "decision": self.decision,
            "reasons": self.reasons,
            "required_next_evidence": self.required_next_evidence,
            "forbidden_scope_flags": self.forbidden_scope_flags
        }

def validate_automation_capability(request: dict) -> AutomationCapabilityDecision:
    reasons = []
    forbidden_scope_flags = []
    decision = "allowed"
    
    # 1. Broadly blocked capabilities across all modes
    if request.get("credential_source") == "env_file":
        reasons.append("env_file credential source is strictly forbidden")
        decision = "blocked"
        
    if request.get("target_identifier_committed"):
        reasons.append("committed target identifier is strictly forbidden")
        decision = "blocked"
        
    if request.get("scheduler_requested"):
        reasons.append("scheduler capability is strictly forbidden")
        decision = "blocked"
        
    if request.get("autonomous_requested") or request.get("replies_or_dms_requested"):
        reasons.append("autonomous posting/replies/DMs is strictly forbidden")
        decision = "blocked"
        
    if request.get("scraping_requested") or request.get("metrics_requested"):
        reasons.append("scraping/metrics fetching is strictly forbidden")
        decision = "blocked"
        
    if request.get("financial_advice_language_present"):
        reasons.append("financial advice language is strictly forbidden")
        decision = "blocked"
        
    if request.get("artifact_backed_claim_present"):
        reasons.append("artifact-backed claims are blocked until future implementation")
        decision = "blocked"
        
    # 2. Mode-specific checks
    mode = request.get("requested_mode")
    platform = request.get("platform_id")
    
    if mode in ["approved_batch_live", "scheduled_approved_live"]:
        return AutomationCapabilityDecision(
            decision="design_only_not_currently_allowed",
            reasons=["This mode requires future queue, idempotency, per-item approval, batch cap, and rollback design"],
            required_next_evidence=["QUEUE_IMPLEMENTATION", "SCHEDULING_POLICY_IMPLEMENTATION"],
            forbidden_scope_flags=forbidden_scope_flags
        )
        
    if mode == "autonomous_live":
        reasons.append("autonomous_live is permanently forbidden")
        decision = "blocked"
        
    if mode == "supervised_live":
        return AutomationCapabilityDecision(
            decision="design_only_not_currently_allowed",
            reasons=["supervised_live remains design_only until queue and idempotency exist"],
            required_next_evidence=["IDEMPOTENCY_IMPLEMENTATION", "QUEUE_IMPLEMENTATION"],
            forbidden_scope_flags=forbidden_scope_flags
        )

    # Sandbox checks
    if mode == "sandbox_one_shot_live":
        if platform != "telegram":
            reasons.append(f"sandbox_one_shot_live is not allowed for platform {platform}")
            decision = "blocked"
            
        if request.get("public_target_requested"):
            reasons.append("public target requested for sandbox mode")
            decision = "blocked"
            
        if request.get("live_attempt_count", 0) > 1:
            reasons.append("live attempt count > 1 in sandbox_one_shot_live")
            decision = "blocked"
            
        if not request.get("authorization_phrase_present"):
            reasons.append("missing exact GO phrase for sandbox_one_shot_live")
            decision = "blocked"
            
        if not all([request.get("approval_state"), request.get("kill_switch_state"), 
                    request.get("redaction_state"), request.get("audit_state")]):
            reasons.append("missing approval, kill-switch, redaction, or audit states for live mode")
            decision = "blocked"

    if decision == "blocked":
        forbidden_scope_flags.append("VIOLATES_STRICT_SAFETY_POSTURE")

    return AutomationCapabilityDecision(
        decision=decision,
        reasons=reasons,
        required_next_evidence=[],
        forbidden_scope_flags=forbidden_scope_flags
    )
