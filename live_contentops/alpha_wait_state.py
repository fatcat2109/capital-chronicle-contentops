"""Local-only deterministic alpha wait-state operator runbook + final bundle (v0).

Closeout / wait-state task. Leaves the repo in a clean, reviewable local-only
state while real Capital Chronicle internal alpha artifacts are not yet available.

Fixture-only and advisory only. No network/provider/LLM/search/platform calls.
No real alpha artifact dependency. No core repo reads/writes. No public posting.
Grants no approval/publish/platform/trading/forecast/execution authority.
"""

WAIT_STATE_STATUS = "WAITING_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS"

REPO_PATH = r"A:\Capital Chronicle\tools\cc-live-contentops"
ACCEPTED_STARTING_HEAD = "c8bd94e"
NEXT_RECOMMENDED_TASK = (
    "WAIT_FOR_REAL_CAPITAL_CHRONICLE_ALPHA_ARTIFACTS_OR_OPERATOR_SELECTED_"
    "LOCAL_MAINTENANCE")

BUILT_CAPABILITIES = [
    "Grounded research / SEO / prompt / citation guardrail.",
    "Editorial QA / preview / selection.",
    "Grounded editorial packet export.",
    "Packet audit / review queue.",
    "Operator decision capture / review history.",
    "Packet registry / review ledger.",
    "Operator dashboard query / handoff.",
    "Project Sources bundle / export.",
    "Real-artifact intake contract / readiness gate.",
    "Artifact-to-packet bridge / synthetic route guard.",
    "End-to-end fixture-only real-artifact pipeline trace.",
]

INTENTIONALLY_DISABLED = [
    "Provider / LLM API calls.",
    "Network / search.",
    "Platform APIs.",
    "Credentials / env reads.",
    "Scheduling.",
    "Live posting.",
    "Autonomous replies / DMs.",
    "Browser automation / scraping.",
    "Public-postable synthetic content.",
    "Real alpha artifact access.",
    "Capital Chronicle core repo reads/writes.",
]

REQUIRED_BEFORE_REAL_ALPHA_INTAKE = [
    "Capital Chronicle internal alpha artifact spec exists.",
    "Approved export location/path provided by operator.",
    "Source artifact IDs available.",
    "Lineage / freshness / limitations included.",
    "DQR / data sufficiency / forecast readiness states explicit.",
    "Missing / proxy / degraded data explicit.",
    "Content type mapped.",
    "No financial advice / execution / signal claims.",
    "Local-only copy or fixture approved by operator.",
    "No direct core repo mutation by ContentOps.",
]

REQUIRED_BEFORE_PUBLIC_CONTENT = [
    "Real approved artifact has passed the intake gate.",
    "Bridge route is not blocked.",
    "Packet export / audit / review queue pass.",
    "Operator decision record exists.",
    "Public-post status is still manual-only.",
    "No auto-posting.",
    "Platform-specific human review.",
    "Freshness / limitations / source IDs visible.",
    "No buy/sell/hold / position sizing / guaranteed prediction / execution language.",
    "Final copy reviewed by Jim.",
]

REQUIRED_BEFORE_LIVE_INTEGRATION = [
    "Separate explicit GO from operator.",
    "New task label specifically authorizing live/provider/platform scope.",
    "Credential policy and secret handling tested.",
    "Dry-run adapter contracts.",
    "Redacted audit events.",
    "Rate-limit / error handling.",
    "Kill switch.",
    "Rollback / manual fallback.",
    "No autonomous posting or replies without later explicit approval.",
]

SAFE_OPERATOR_ACTIONS_NOW = [
    "Inspect local fixture-only summaries and reports.",
    "Review the pipeline trace scenario matrix.",
    "Prepare a real alpha artifact spec offline.",
    "Curate the Project Sources upload bundle.",
    "Plan the next local-only maintenance task.",
]

FORBIDDEN_OPERATOR_ACTIONS_NOW = [
    "Posting fixture/demo/synthetic content publicly.",
    "Enabling provider/search/platform calls.",
    "Reading credentials or env files.",
    "Treating any fixture as a real approved artifact.",
    "Mutating the Capital Chronicle core repo.",
    "Granting approval/publish/platform authority.",
]

KNOWN_CAVEATS = [
    ".gitignore is modified in the working tree, unstaged, and outside task "
    "commit scope. Do not edit, stage, clean, revert, normalize, or commit it.",
    "0072 evidence prose had inconsistent path wording; committed docs use the "
    "underscore convention (AFTER_0072 / TASK_CONTENTOPS_0072).",
]


def build_wait_state_record() -> dict:
    """Deterministic JSON-compatible alpha wait-state record."""
    return {
        "wait_state_id": "alpha_wait_state_after_0073",
        "repo_path": REPO_PATH,
        "accepted_starting_head": ACCEPTED_STARTING_HEAD,
        "current_phase": "LOCAL_ONLY_ALPHA_WAIT_STATE",
        "wait_state_status": WAIT_STATE_STATUS,
        "reason_for_wait_state": (
            "Local ContentOps review infrastructure is complete. Real Capital "
            "Chronicle internal alpha artifacts do not exist in this sidecar yet "
            "and must not be faked. The correct posture is a safe wait-state."),
        "built_capabilities_summary": list(BUILT_CAPABILITIES),
        "intentionally_disabled_capabilities": list(INTENTIONALLY_DISABLED),
        "required_before_real_alpha_intake": list(REQUIRED_BEFORE_REAL_ALPHA_INTAKE),
        "required_before_public_content": list(REQUIRED_BEFORE_PUBLIC_CONTENT),
        "required_before_any_live_integration": list(REQUIRED_BEFORE_LIVE_INTEGRATION),
        "safe_operator_actions_now": list(SAFE_OPERATOR_ACTIONS_NOW),
        "forbidden_operator_actions_now": list(FORBIDDEN_OPERATOR_ACTIONS_NOW),
        "known_caveats": list(KNOWN_CAVEATS),
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
        "local_only": True,
        "advisory_only": True,
        "fixture_only": True,
        "requires_real_alpha_artifacts_now": False,
        "public_content_allowed_now": False,
        "live_integration_allowed_now": False,
        "human_review_required": True,
        "approval_granted": False,
        "publish_ready": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
    }


def build_summary() -> dict:
    """Deterministic CLI summary for the alpha wait-state + final bundle."""
    from . import final_bundle_manifest as fbm
    manifest = fbm.build_manifest()
    return {
        "status": "deterministic local alpha wait-state and final bundle active",
        "local_only": True,
        "advisory_only": True,
        "fixture_only": True,
        "alpha_wait_state_enabled": True,
        "wait_state_status": WAIT_STATE_STATUS,
        "requires_real_alpha_artifacts_now": False,
        "public_content_allowed_now": False,
        "live_integration_allowed_now": False,
        "provider_call_allowed": False,
        "search_call_allowed": False,
        "platform_action_allowed": False,
        "approval_granted": False,
        "publish_ready": False,
        "recommended_upload_count": len(manifest["recommended_uploads"]),
        "excluded_category_count": len(manifest["excluded_categories"]),
        "all_exports_safe_for_project_sources": True,
        "validation_rules_enabled": True,
        "next_recommended_task": NEXT_RECOMMENDED_TASK,
    }

