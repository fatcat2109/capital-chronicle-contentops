/*
 * Capital Chronicle ContentOps — Operator Cockpit V3 view model.
 *
 * Local-only, fixture-driven. No network, no remote dependency. This file is the
 * SINGLE canonical source of operational truth for the cockpit. Every screen and
 * the header read from CC_COCKPIT_V3_VIEW_MODEL.global_state. Historical and
 * Stitch reference provenance are explicitly labelled "Not Runtime Authority".
 */
window.CC_COCKPIT_V3_VIEW_MODEL = {
  meta: {
    task_label:
      "TASK_CONTENTOPS_0174B_OPERATOR_COCKPIT_V3_BRANDKIT_GROUNDED_CLEAN_ROOM_REBUILD_V0",
    product_name: "Capital Chronicle ContentOps",
    surface_name: "Operator Cockpit V3",
    build_kind: "local / static / fixture-driven",
    runtime_authority: false
  },

  // Canonical current operational truth. Read by every screen/header.
  global_state: {
    current_mode: "local_pre_alpha",
    current_product_state: "local / static / fixture-driven",
    product_ui_track: "V3 clean-room rebuild",
    product_ui_status: "AWAITING_0174B_V3_AUDIT",
    current_task: "0174B",
    current_repo_baseline: "c56ccd9",
    current_repo_baseline_note:
      "Current repo baseline and visible browser QA evidence (0174A2) entering V3.",
    v2_build_candidate: "dd55114",
    design_reference_quarantine: "1024cdf",
    automated_browser_qa_evidence: "75f9d47",
    visible_browser_qa_evidence: "c56ccd9",
    historical_pre_0174r_baseline: "680d03d",
    last_product_code_baseline: "496591f",
    kill_switch: "active",
    live_state: "disabled",
    platform_api_state: "disabled",
    provider_api_state: "disabled",
    scheduler_state: "disabled",
    credential_read_state: "disabled",
    public_state: "not_public_postable",
    review_state: "review_only",
    runtime_authority: false,
    current_gate:
      "Awaiting ChatGPT audit of 0174B V3 clean-room rebuild evidence",
    next_allowed_action:
      "ChatGPT audit of 0174B evidence packet; if accepted, run visible browser QA for V3"
  },

  // Top safety ribbon chips. severity drives color (system safety only).
  safety_ribbon: [
    { label: "LOCAL ONLY", severity: "info" },
    { label: "FIXTURE DRIVEN", severity: "info" },
    { label: "REVIEW ONLY", severity: "info" },
    { label: "MANUAL REVIEW REQUIRED", severity: "info" },
    { label: "NOT PUBLIC POSTABLE", severity: "info" },
    { label: "LIVE DISABLED", severity: "info" },
    { label: "PLATFORM API DISABLED", severity: "info" },
    { label: "SCHEDULER DISABLED", severity: "info" },
    { label: "CREDENTIAL READ DISABLED", severity: "info" },
    { label: "KILL SWITCH ACTIVE", severity: "block" },
    { label: "SECRET REDACTED", severity: "info" },
    { label: "NO FINANCIAL ADVICE", severity: "info" },
    { label: "NO SIGNAL LANGUAGE", severity: "info" }
  ],

  nav: [
    { id: "command_center", label: "Command Center" },
    { id: "content_studio", label: "Content Studio" },
    { id: "publish_readiness", label: "Publish Readiness Tower" },
    { id: "evidence_vault", label: "Evidence Vault" },
    { id: "content_calendar", label: "Content Calendar / Workflow" },
    { id: "visual_export", label: "Visual Export / Screenshot-Safe" },
    { id: "settings", label: "Settings / Safety Policy" }
  ],

  // Historical screen provenance. NOT runtime authority.
  historical_screen_provenance: {
    label: "Historical Screen Provenance",
    runtime_authority: false,
    not_runtime_authority: true,
    note: "Historical per-screen build provenance. Not current operational truth.",
    entries: [
      { head: "15b87ff", label: "Historical Screen Provenance", runtime_authority: false, note: "0159 view-model baseline (historical). Not current." },
      { head: "1c03ca0", label: "Historical Screen Provenance", runtime_authority: false, note: "Historical prior shell screen baseline. Not current." },
      { head: "444ef2c", label: "Historical Screen Provenance", runtime_authority: false, note: "Historical pre-0174 accepted baseline. Not current." }
    ]
  },

  // Stitch visual reference provenance. NOT runtime authority.
  stitch_reference_provenance: {
    label: "Visual Reference Only",
    runtime_authority: false,
    not_runtime_authority: true,
    source: "operator-supplied local Stitch governance terminal folder (quarantined at 1024cdf)",
    note: "Stitch HTML/CSS/PNG used as advisory visual reference only. Not copied, not imported, not runtime."
  },

  status_vocabulary: [
    "PASS", "DEGRADED", "BLOCKED", "REVIEW_REQUIRED", "LIVE_DISABLED",
    "NOT_PUBLIC_POSTABLE", "FUTURE_ONLY", "UNKNOWN", "SECRET_REDACTED"
  ],

  screens: {
    command_center: {
      title: "Command Center",
      purpose:
        "Answer one question in under 10 seconds: can anything proceed, and if not, why? Local, static, fixture-driven governance overview.",
      runtime_authority: false,
      screen_state: {
        what_for: "Single decision surface summarising whether any operation may proceed under current safety gates.",
        static_local_fixture_driven: true,
        runtime_authority: false
      },
      decision_panel: {
        question: "Can anything proceed, and if not, why?",
        answer: "No automated/live/public action may proceed. V3 is in clean-room rebuild, awaiting 0174B audit.",
        reason: "Kill switch active. Live/platform/provider/scheduler/credential reads disabled. Review-only, not public-postable.",
        current_truth: true,
        historical_provenance: false
      },
      primary_gate: {
        status: "REVIEW_REQUIRED",
        severity: "review",
        label: "Awaiting ChatGPT audit of 0174B V3 rebuild",
        reason: "V3 is a brandkit-grounded clean-room rebuild. Nothing may proceed to the next QA pass until the 0174B evidence packet is audited and accepted.",
        evidence_ref_ids: ["EV-0174B-V3", "EV-0174A2-QA"],
        next_allowed_action: "ChatGPT audit of 0174B evidence packet; if accepted, run visible browser QA for V3.",
        current_truth: true,
        historical_provenance: false,
        caveat: "REVIEW_REQUIRED means audit-pending; it does not claim acceptance."
      },
      safety_counters: [
        { label: "Evidence packets indexed", value: "see Evidence Vault" },
        { label: "Active blockers", value: "1 (audit pending)" },
        { label: "Forbidden capabilities enabled", value: "0" },
        { label: "Tracked secrets", value: "0" }
      ],
      status_tokens: [
        {
          status: "PASS", severity: "ok", label: "System Safety",
          reason: "Kill switch active, live disabled, review-only, not public-postable.",
          evidence_ref_ids: ["EV-0174B-V3"],
          allowed_actions: ["inspect", "review"],
          blocked_actions: ["publish", "schedule", "live_api"],
          current_truth: true, historical_provenance: false,
          caveat: "PASS means system-safe only; never publish/forecast/market-ready."
        },
        {
          status: "REVIEW_REQUIRED", severity: "review", label: "Next Task Gate",
          reason: "Audit of 0174B V3 evidence not yet performed.",
          evidence_ref_ids: ["EV-0174B-V3"],
          allowed_actions: ["await_audit"],
          blocked_actions: ["start_next_task", "browser_qa"],
          current_truth: true, historical_provenance: false
        },
        {
          status: "LIVE_DISABLED", severity: "block", label: "Publish Automation",
          reason: "Live/platform API disabled; one-button publish-all does not exist.",
          evidence_ref_ids: ["EV-SAFETY-POLICY"],
          allowed_actions: ["inspect_contract"],
          blocked_actions: ["post", "dispatch", "schedule"],
          current_truth: true, historical_provenance: false
        }
      ],
      build_provenance: {
        screen_build_task: "0174B", label: "Historical Screen Provenance",
        runtime_authority: false,
        note: "This screen build provenance is not current operational authority."
      }
    },


    content_studio: {
      title: "Content Studio",
      purpose:
        "Editorial QA cockpit separating content lanes. No public-ready copy, no financial advice, no signal language.",
      runtime_authority: false,
      screen_state: {
        what_for: "Separate content lanes and show claim-risk, source/artifact requirements, and manual-review gates.",
        static_local_fixture_driven: true,
        runtime_authority: false
      },
      primary_gate: {
        status: "NOT_PUBLIC_POSTABLE",
        severity: "review",
        label: "All lanes review-only / not public-postable",
        reason: "Content is pre-alpha process material. No final public-ready copy may be produced here.",
        evidence_ref_ids: ["EV-CONTENT-SAFETY"],
        next_allowed_action: "Manual editorial review only.",
        current_truth: true, historical_provenance: false,
        caveat: "No buy/sell/hold, no position sizing, no signal-service framing."
      },
      lanes: [
        { label: "Pre-Alpha Process", status: "review", description: "Internal process notes. Not public-ready. Manual review required.", claim_risk: "low", requires: "source + manual review" },
        { label: "Grounded News Context", status: "review", description: "Context grounded in cited sources. No unverified numeric market claims.", claim_risk: "medium", requires: "source citation + manual review" },
        { label: "Future Artifact-Backed", status: "block", description: "Reserved for artifact-backed content. Future-only; no live artifacts yet.", claim_risk: "gated", requires: "artifact + manual review" },
        { label: "Failure Forensics", status: "review", description: "Post-mortem analysis of process failures. Internal only.", claim_risk: "low", requires: "evidence ref + manual review" },
        { label: "Macro Education", status: "review", description: "Educational macro explainers. No financial advice, no signal language.", claim_risk: "medium", requires: "source + manual review" },
        { label: "Product Update", status: "review", description: "ContentOps product updates. Not public-postable until approved.", claim_risk: "low", requires: "manual review" }
      ],
      status_tokens: [
        {
          status: "REVIEW_REQUIRED", severity: "review", label: "Editorial Gate",
          reason: "All lanes require manual editorial review before any downstream use.",
          evidence_ref_ids: ["EV-CONTENT-SAFETY"],
          allowed_actions: ["draft", "review", "annotate"],
          blocked_actions: ["publish", "auto_generate_final_copy"],
          current_truth: true, historical_provenance: false,
          caveat: "PASS on a lane means review-complete, never publish-ready."
        }
      ],
      build_provenance: { screen_build_task: "0174B", label: "Historical Screen Provenance", runtime_authority: false }
    },


    publish_readiness: {
      title: "Publish Readiness Tower",
      purpose:
        "A gate matrix, not a platform control dashboard. Per-platform readiness records with no send/post/publish/dispatch affordances.",
      runtime_authority: false,
      screen_state: {
        what_for: "Display readiness gates per platform: docs, credential slot, approval, audit, kill switch, live adapter, scheduler, posting.",
        static_local_fixture_driven: true,
        runtime_authority: false
      },
      primary_gate: {
        status: "LIVE_DISABLED",
        severity: "block",
        label: "All live posting disabled",
        reason: "No platform adapter is live. Posting/scheduling/dispatch do not exist as runtime actions.",
        evidence_ref_ids: ["EV-PUBLISH-GATES"],
        next_allowed_action: "Inspect readiness records only.",
        current_truth: true, historical_provenance: false,
        caveat: "Gate matrix shows readiness, never an enabled publish control."
      },
      platforms: [
        { name: "Telegram", note: "Readiness record only. Live adapter disabled." },
        { name: "X / Twitter", note: "Readiness record only. Live adapter disabled." },
        { name: "LinkedIn", note: "Readiness record only. Live adapter disabled." },
        { name: "Substack", note: "Readiness record only. Live adapter disabled." }
      ],
      gate_rows: [
        { gate: "Official docs gate", state: "review", label: "inspect contract" },
        { gate: "Dry-run renderer", state: "PASS", label: "view dry-run shape" },
        { gate: "Credential slot defined", state: "review", label: "future gate" },
        { gate: "Credential read", state: "block", label: "disabled" },
        { gate: "Credential validation", state: "block", label: "disabled" },
        { gate: "Manual approval gate", state: "review", label: "manual review only" },
        { gate: "Redacted audit logging", state: "review", label: "future gate" },
        { gate: "Kill switch", state: "block", label: "active / blocks live" },
        { gate: "Live adapter", state: "block", label: "disabled" },
        { gate: "Scheduler", state: "block", label: "disabled" },
        { gate: "Posting", state: "block", label: "disabled" }
      ],
      next_blocker: "Kill switch active and live adapters disabled. No posting path exists.",
      status_tokens: [
        {
          status: "BLOCKED", severity: "block", label: "Live Posting Path",
          reason: "No live adapter, no scheduler, no posting. Kill switch active.",
          evidence_ref_ids: ["EV-PUBLISH-GATES"],
          allowed_actions: ["inspect_contract", "view_dry_run"],
          blocked_actions: ["post", "send", "schedule", "dispatch", "validate_credential"],
          current_truth: true, historical_provenance: false,
          caveat: "PASS on a gate means readiness-checked, never live-ready."
        }
      ],
      build_provenance: { screen_build_task: "0174B", label: "Historical Screen Provenance", runtime_authority: false }
    },


    evidence_vault: {
      title: "Evidence Vault + Audit Timeline",
      purpose:
        "Compliance-grade evidence room. Distinguishes build commits, evidence commits, and historical references. 680d03d is historical, not current build truth.",
      runtime_authority: false,
      screen_state: {
        what_for: "Index task evidence, lineage timeline, validation matrix, caveat/forbidden-scope registries, and active blockers.",
        static_local_fixture_driven: true,
        runtime_authority: false
      },
      primary_gate: {
        status: "PASS",
        severity: "ok",
        label: "Evidence read-only",
        reason: "Evidence is read-only; no mutation, export, or upload is possible from this surface.",
        evidence_ref_ids: ["EV-0174B-V3"],
        next_allowed_action: "Inspect evidence only.",
        current_truth: true, historical_provenance: false,
        caveat: "PASS means evidence integrity/read-only, not publish-readiness."
      },
      evidence_index: [
        { id: "EV-0174R-BUILD", task: "0174R", classification: "build", head: "dd55114", artifact: "Operator Cockpit V2 static frontend build candidate" },
        { id: "EV-0174H-REF", task: "0174H", classification: "reference", head: "1024cdf", artifact: "Quarantined Stitch visual references" },
        { id: "EV-0174A-QA", task: "0174A", classification: "browser_qa_evidence", head: "75f9d47", artifact: "Automated/headed browser QA evidence" },
        { id: "EV-0174A2-QA", task: "0174A2", classification: "browser_qa_evidence", head: "c56ccd9", artifact: "Visible Antigravity/headed browser QA evidence" },
        { id: "EV-0174B-V3", task: "0174B", classification: "build_pending_audit", head: "pending-commit", artifact: "V3 clean-room rebuild (this task) — pending ChatGPT audit" },
        { id: "EV-SAFETY-POLICY", task: "policy", classification: "safety", head: "dd55114", artifact: "Hard boundary / safety policy fixture" },
        { id: "EV-CONTENT-SAFETY", task: "policy", classification: "content", head: "dd55114", artifact: "Content safety / claim-risk fixture" },
        { id: "EV-PUBLISH-GATES", task: "policy", classification: "publish", head: "dd55114", artifact: "Publish readiness gate matrix fixture" }
      ],
      commit_timeline: [
        { head: "496591f", label: "Last Product Code Baseline", note: "test: add institutional shell view model drift guard", current_truth: false, historical_provenance: true, kind: "historical" },
        { head: "680d03d", label: "Historical Pre-0174R Docs/Setup Baseline", note: "docs: add minimal project sources bundle (NOT current build truth)", current_truth: false, historical_provenance: true, kind: "historical" },
        { head: "dd55114", label: "V2 Static Build Candidate (0174R)", note: "feat: add reference-driven operator cockpit v2 static frontend", current_truth: false, historical_provenance: false, kind: "build" },
        { head: "1024cdf", label: "Stitch Reference Quarantine (0174H)", note: "docs: quarantine Stitch operator cockpit visual references", current_truth: false, historical_provenance: false, kind: "reference" },
        { head: "75f9d47", label: "Automated Browser QA Evidence (0174A)", note: "test: add operator cockpit v2 browser qa evidence", current_truth: false, historical_provenance: false, kind: "evidence" },
        { head: "c56ccd9", label: "Visible Browser QA Evidence / V3 Start (0174A2)", note: "test: add visible operator cockpit v2 browser qa evidence", current_truth: true, historical_provenance: false, kind: "evidence" },
        { head: "pending-commit", label: "V3 Clean-Room Rebuild (0174B)", note: "feat: add brandkit-grounded operator cockpit v3 frontend — pending ChatGPT audit", current_truth: false, historical_provenance: false, kind: "build_pending_audit" }
      ],
      validation_matrix: [
        { check: "external dependency scan", expected: "no remote URLs / CDNs / fonts / fetch / sockets" },
        { check: "current-vs-historical metadata", expected: "stale heads labelled historical only" },
        { check: "forbidden controls scan", expected: "no enabled publish/post/send/schedule" },
        { check: "secret scan", expected: "no tracked secrets / no secrets displayed" }
      ],
      caveat_registry: [
        "PASS never means publish/forecast/live/market-ready.",
        "Color communicates system safety only, never market direction.",
        "Stitch reference is visual-only and not runtime authority.",
        "680d03d is a historical pre-0174R baseline, not current build truth."
      ],
      forbidden_scope_matrix: [
        "live posting", "scheduler", "platform api", "provider/llm api",
        "telegram api", "scraping", "autonomous replies/dms", "one-button publish-all",
        "export/upload/download", "screenshot automation", "credential read", "env read"
      ],
      active_blockers: [
        { id: "BLK-AUDIT", label: "ChatGPT audit of 0174B V3 rebuild pending", severity: "block" }
      ],
      next_task_discipline:
        "Do not start, shrink, rename, or invent the next phase. Await audit acceptance.",
      build_provenance: { screen_build_task: "0174B", label: "Historical Screen Provenance", runtime_authority: false }
    },


    content_calendar: {
      title: "Content Calendar / Workflow Board",
      purpose:
        "Manual workflow only. No scheduling, no auto-post, no live campaign, no API dispatch.",
      runtime_authority: false,
      screen_state: {
        what_for: "Track manual content workflow states. Auto/scheduled/live states are forbidden and shown as unavailable.",
        static_local_fixture_driven: true,
        runtime_authority: false
      },
      primary_gate: {
        status: "REVIEW_REQUIRED",
        severity: "review",
        label: "Manual workflow only",
        reason: "Only manual states are allowed. Scheduling and auto-posting do not exist as runtime capabilities.",
        evidence_ref_ids: ["EV-SAFETY-POLICY"],
        next_allowed_action: "Move items through manual states only.",
        current_truth: true, historical_provenance: false,
        caveat: "operator-approved-for-manual is not a publish action."
      },
      allowed_states: [
        "idea", "source-needed", "research-brief-ready", "draft-review",
        "blocked", "operator-approved-for-manual", "manually-posted", "metrics-entered"
      ],
      forbidden_states: [
        "scheduled", "queued for auto-post", "auto-publish ready",
        "live campaign", "API dispatch ready", "bot reply ready"
      ],
      cards: [
        { title: "Macro CPI explainer (internal draft)", state: "draft-review" },
        { title: "Process retro: 0174 rollback", state: "research-brief-ready" },
        { title: "Grounded news context note", state: "source-needed" },
        { title: "ContentOps product update", state: "idea" },
        { title: "Failure forensics writeup", state: "blocked" }
      ],
      status_tokens: [
        {
          status: "FUTURE_ONLY", severity: "review", label: "Automation States",
          reason: "Scheduling/auto-post/live campaign/API dispatch are future-only and not available.",
          evidence_ref_ids: ["EV-SAFETY-POLICY"],
          allowed_actions: ["manual_move", "manual_post_offline"],
          blocked_actions: ["schedule", "auto_post", "api_dispatch", "bot_reply"],
          current_truth: true, historical_provenance: false
        }
      ],
      build_provenance: { screen_build_task: "0174B", label: "Historical Screen Provenance", runtime_authority: false }
    },


    visual_export: {
      title: "Visual Export / Screenshot-Safe Mode",
      purpose:
        "Screenshot-safe preparation only. Not an export engine. No download/upload/automation.",
      runtime_authority: false,
      screen_state: {
        what_for: "Confirm the surface is screenshot-safe: local-only, redacted, not public-postable.",
        static_local_fixture_driven: true,
        runtime_authority: false
      },
      primary_gate: {
        status: "NOT_PUBLIC_POSTABLE",
        severity: "review",
        label: "Screenshot-safe preparation only",
        reason: "No export/download/upload/automation exists. This screen only confirms screenshot safety.",
        evidence_ref_ids: ["EV-SAFETY-POLICY"],
        next_allowed_action: "Manual screenshot by operator only.",
        current_truth: true, historical_provenance: false,
        caveat: "No public-ready caption generation."
      },
      checklist: [
        { item: "Local only (file://)", state: "PASS" },
        { item: "Secrets redacted", state: "PASS" },
        { item: "Live disabled visible", state: "PASS" },
        { item: "Not public postable label present", state: "PASS" },
        { item: "No financial advice / signal language", state: "PASS" }
      ],
      forbidden: [
        "actual image export", "PDF generation", "platform upload",
        "file download", "screenshot automation", "public-ready caption generation", "live sharing"
      ],
      limitation_notes: [
        "This is preparation guidance, not an export tool.",
        "Operator performs any screenshot manually and reviews before use.",
        "No data leaves the local machine from this surface."
      ],
      status_tokens: [
        {
          status: "PASS", severity: "ok", label: "Screenshot Safety",
          reason: "Surface is local-only, redacted, and not public-postable.",
          evidence_ref_ids: ["EV-SAFETY-POLICY"],
          allowed_actions: ["manual_screenshot_review"],
          blocked_actions: ["export", "download", "upload", "auto_screenshot"],
          current_truth: true, historical_provenance: false,
          caveat: "PASS means screenshot-safe only, never publish-ready."
        }
      ],
      build_provenance: { screen_build_task: "0174B", label: "Historical Screen Provenance", runtime_authority: false }
    },


    settings: {
      title: "Settings / Safety Policy",
      purpose:
        "Safety policy and hard boundaries. Not a credential display. No token/API key/chat ID/env path/value shown.",
      runtime_authority: false,
      screen_state: {
        what_for: "Declare active hard boundaries, policies, and the never-display list.",
        static_local_fixture_driven: true,
        runtime_authority: false
      },
      primary_gate: {
        status: "SECRET_REDACTED",
        severity: "review",
        label: "Safety policy only / secrets never displayed",
        reason: "This surface shows policy, not credentials. No secret, token, key, chat ID, env path, or raw platform response is shown.",
        evidence_ref_ids: ["EV-SAFETY-POLICY"],
        next_allowed_action: "Review safety policy only.",
        current_truth: true, historical_provenance: false,
        caveat: "No credential entry or validation is available here."
      },
      hard_boundaries: [
        "Local-only, static, fixture-driven. No runtime network.",
        "Kill switch active. Live posting disabled.",
        "Platform/provider/Telegram APIs disabled.",
        "Scheduler disabled. Scraping disabled.",
        "Credential read disabled. Env read disabled.",
        "No autonomous replies/DMs. No one-button publish-all.",
        "No financial advice. No buy/sell/hold. No position sizing. No signal-service framing."
      ],
      policies: [
        { name: "Credential policy", value: "No credentials read, stored, or displayed." },
        { name: "Redaction policy", value: "All secrets redacted; never logged or shown." },
        { name: "Platform gate policy", value: "Platforms exist as readiness records only; no live adapters." },
        { name: "Content safety policy", value: "Manual review required; no public-ready copy here." },
        { name: "Financial advice prohibition", value: "No advice, signals, or market-direction claims." },
        { name: "Network policy", value: "No fetch/XHR/WebSocket/EventSource; no remote dependency." }
      ],
      never_display: [
        "real token", "API key", "chat ID", "env path with secrets", "raw platform response"
      ],
      status_tokens: [
        {
          status: "LIVE_DISABLED", severity: "block", label: "Live Behavior",
          reason: "All live/platform/scheduler/credential behavior is disabled by policy and kill switch.",
          evidence_ref_ids: ["EV-SAFETY-POLICY"],
          allowed_actions: ["review_policy"],
          blocked_actions: ["enable_live", "read_credential", "read_env", "call_api"],
          current_truth: true, historical_provenance: false,
          caveat: "Policy is descriptive; it grants no runtime capability."
        }
      ],
      build_provenance: { screen_build_task: "0174B", label: "Historical Screen Provenance", runtime_authority: false }
    }
  }
};
