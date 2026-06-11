/*
 * Operator Cockpit V4 — Canonical View Model
 * TASK_CONTENTOPS_0174E clean-room build.
 *
 * Local-only, static, deterministic. No network, no fetch, no storage, no
 * secrets, no platform/provider/credential behavior. This object is the single
 * source of operational truth; the header and every screen read from it.
 * Historical and Stitch provenance are explicitly labeled "Not Runtime Authority".
 */
window.CC_OPERATOR_COCKPIT_V4_MODEL = {
  meta: {
    version: "v4",
    build_task: "TASK_CONTENTOPS_0174E_OPERATOR_COCKPIT_V4_NORTH_STAR_CLEAN_ROOM_FRONTEND_BUILD_V0",
    mode: "static / local / fixture-driven",
    runtime_authority: false,
    generated_note: "Deterministic local fixtures only. No live data, no market data."
  },

  /* Compact grouped Safety Rail. Critical locks are always visible; the rest are
     grouped into a single system-locks cluster with a count. */
  safety_locks: {
    critical: [
      "LOCAL-ONLY",
      "REVIEW-ONLY",
      "NOT PUBLIC-POSTABLE",
      "LIVE DISABLED",
      "KILL SWITCH ACTIVE",
      "NO FINANCIAL ADVICE",
      "NO SIGNAL LANGUAGE"
    ],
    grouped_locks: [
      "NO PLATFORM API",
      "NO PROVIDER API",
      "NO SCHEDULER",
      "NO SCRAPING",
      "NO CREDENTIAL READ",
      "SECRET REDACTED"
    ]
  },

  /* Single canonical operational state. No component hardcodes these. */
  global_current_state: {
    repo_path: "A:/Capital Chronicle/tools/cc-live-contentops",
    branch: "master",
    kill_switch_status: "active",
    public_state: "not_public_postable",
    live_state: "disabled",
    platform_api_state: "disabled",
    provider_api_state: "disabled",
    scheduler_state: "disabled",
    credential_read_state: "disabled",
    network_state: "disabled"
  },

  /* Labeled truth rail. Every HEAD carries an explicit role label. No bare hashes.
     The current gate must NOT carry the stale 0174B V3 string. */
  truth_rail: [
    {
      role_label: "Current Product HEAD",
      value: "set-at-build (V4 clean-room build commit)",
      kind: "current",
      runtime_authority: true
    },
    {
      role_label: "Current Gate",
      value: "Awaiting ChatGPT audit of 0174E V4 clean-room frontend build evidence. No browser QA or next task until accepted.",
      kind: "current",
      runtime_authority: true
    },
    {
      role_label: "Next Allowed Action",
      value: "Inspect this V4 build locally and await ChatGPT audit of the 0174E evidence packet. No Antigravity, no browser QA, no Project Sources refresh in this task.",
      kind: "current",
      runtime_authority: true
    },
    {
      role_label: "V4 Build Status",
      value: "Clean-room build batch 1 (0174E)",
      kind: "current",
      runtime_authority: true
    },
    {
      role_label: "Tested HEAD (Evidence-only Browser QA)",
      value: "0174C visible Antigravity browser QA evidence commit",
      kind: "evidence_only",
      runtime_authority: false
    },
    {
      role_label: "V3 Failed-Candidate Build",
      value: "ui/institutional_operator_cockpit_v3 — historical, NOT accepted as north-star UI",
      kind: "historical",
      runtime_authority: false
    },
    {
      role_label: "V2 Historical Build Candidate",
      value: "ui/institutional_operator_cockpit_v2 — historical reference only",
      kind: "historical",
      runtime_authority: false
    },
    {
      role_label: "Reference Quarantine",
      value: "docs/design_references/stitch_institutional_ai_operator_cockpit — reference-only, Not Runtime Authority",
      kind: "reference_only",
      runtime_authority: false
    },
    {
      role_label: "Historical Screen Provenance",
      value: "15b87ff / 1c03ca0 / 444ef2c — Not Runtime Authority",
      kind: "historical",
      runtime_authority: false
    }
  ],
  /* Evidence registry. Every critical status references these by id. */
  evidence_refs: [
    { evidence_id: "EV-0174D", evidence_type: "doc", label: "V4 north-star blueprint chain (gap map, composition, wireframe, test plan)", status: "pass", source_path: "docs/TASK_CONTENTOPS_0174D_V4_*", last_validated: "0174D2" },
    { evidence_id: "EV-MASTER-PLAN", evidence_type: "doc", label: "Institutional Cockpit Master Plan authority", status: "pass", source_path: "docs/CAPITAL_CHRONICLE_CONTENTOPS_INSTITUTIONAL_COCKPIT_MASTER_PLAN.md", last_validated: "0174D2" },
    { evidence_id: "EV-0174C-QA", evidence_type: "browser_qa", label: "Visible Antigravity browser QA capture (V3)", status: "pass_with_caveat", caveat: "Capture accepted; worker visual judgment rejected.", source_path: "docs/browser_qa/TASK_CONTENTOPS_0174C_OPERATOR_COCKPIT_V3_VISIBLE_ANTIGRAVITY_BROWSER_QA_V0", last_validated: "0174C" },
    { evidence_id: "EV-DESIGN", evidence_type: "doc", label: "Technical Matte Operator DESIGN.md brandkit (quarantined reference)", status: "pass", source_path: "docs/design_references/.../technical_matte_operator/DESIGN.md", last_validated: "reference-only" },
    { evidence_id: "EV-TESTS-V4", evidence_type: "test_result", label: "V4 deterministic static test suite", status: "pass", source_path: "tests/test_institutional_operator_cockpit_v4.py", last_validated: "0174E" }
  ],

  /* Ordered active blocker stack (by severity). */
  blocker_stack: [
    { id: "BLK-AUDIT", severity: "blocked", label: "Awaiting ChatGPT audit of 0174E V4 build evidence", reason: "V4 clean-room build must be audited before browser QA or any next task.", evidence_ref_ids: ["EV-0174D", "EV-TESTS-V4"] },
    { id: "BLK-LIVE", severity: "blocked", label: "Supervised publishing blocked", reason: "Live adapter, platform API, scheduler, and posting are all disabled by policy and kill switch.", evidence_ref_ids: ["EV-MASTER-PLAN"] },
    { id: "BLK-ARTIFACT", severity: "review_required", label: "Artifact-backed content lane blocked", reason: "No real approved Capital Chronicle artifacts, lineage, freshness, or DQR state exist yet.", evidence_ref_ids: ["EV-MASTER-PLAN"] }
  ],

  /* Historical screen provenance, kept separate from current truth. */
  screen_provenance: [
    { screen_id: "shell", historical_task_label: "0160 institutional shell", historical_head_short: "1c03ca0", provenance_label: "Historical Screen Provenance", runtime_authority: false },
    { screen_id: "v2", historical_task_label: "0174A V2 candidate", historical_head_short: "444ef2c", provenance_label: "Historical Screen Provenance", runtime_authority: false },
    { screen_id: "v3", historical_task_label: "0174B/0174C V3 failed candidate", historical_head_short: "15b87ff", provenance_label: "Historical Screen Provenance (failed candidate, not accepted)", runtime_authority: false }
  ],

  /* Reusable status token registry. PASS = validation-safe only. */
  status_tokens: ["PASS", "DEGRADED", "BLOCKED", "REVIEW_REQUIRED", "LIVE_DISABLED", "NOT_PUBLIC_POSTABLE", "FUTURE_ONLY", "UNKNOWN", "SECRET_REDACTED"],


  /* Seven institutional cockpit screens. */
  screens: [
    {
      screen_id: "command_center",
      nav_label: "Command Center",
      title: "Command Center",
      primary_question: "Can anything proceed, and if not, why?",
      verdict: {
        status: "BLOCKED",
        severity: "blocked",
        label: "Current Verdict",
        text: "Nothing may proceed to publishing. System is local-only, review-only, kill switch active. Next action is audit of this V4 build.",
        reason: "Kill switch active and live behavior disabled by policy; V4 build awaits ChatGPT audit.",
        evidence_ref_ids: ["EV-0174D", "EV-MASTER-PLAN", "EV-TESTS-V4"],
        allowed_actions: ["inspect", "manual review", "await audit"],
        blocked_actions: ["publish", "post", "send", "schedule", "api call", "credential read"],
        current_truth: true,
        historical_provenance: false
      },
      what_changed: [
        "V4 clean-room frontend created under ui/institutional_operator_cockpit_v4 (0174E).",
        "Canonical truth model replaces V3 stale 0174B gate.",
        "Master plan committed as repo-native authority (0174D2)."
      ],
      evidence_dependency_map: [
        { node: "Current Verdict", depends_on: ["EV-0174D", "EV-MASTER-PLAN"] },
        { node: "Publishing blocked", depends_on: ["EV-MASTER-PLAN"] },
        { node: "V4 build integrity", depends_on: ["EV-TESTS-V4"] }
      ],
      safety_counters: { locks_active: 13, gates_open: 0, blockers: 3, review_items: 1 }
    },
    {
      screen_id: "content_studio",
      nav_label: "Content Studio",
      title: "Content Studio",
      primary_question: "What content exists, what is its claim risk, and what must be true before a human may review it?",
      studio_state: {
        status: "REVIEW_REQUIRED",
        severity: "caution",
        label: "Studio State",
        text: "review_only / not_public_postable / manual review required",
        reason: "All content is draft-for-review; nothing is public-ready and no final copy is generated.",
        evidence_ref_ids: ["EV-MASTER-PLAN"],
        allowed_actions: ["inspect", "manual review"],
        blocked_actions: ["publish final copy", "financial advice", "signal language"],
        current_truth: true,
        historical_provenance: false
      },
      lanes: [
        { lane_id: "pre_alpha_process", name: "Pre-Alpha Process", status: "REVIEW_REQUIRED", claim_risk: "low", forbidden_language: "none detected", limitations: ["build-in-public only", "no alpha output implied"], platform_fit: "dry-run preview only", checklist: ["source noted", "no signal language", "not public-postable"], evidence_ref_ids: ["EV-MASTER-PLAN"], not_public_postable: true },
        { lane_id: "grounded_news_context", name: "Grounded News Context", status: "REVIEW_REQUIRED", claim_risk: "medium", forbidden_language: "scan clean: no directional calls (buy, sell, hold, target)", limitations: ["source citation required", "educational interpretation only"], platform_fit: "dry-run preview only", checklist: ["citation complete", "no prediction", "no trade framing"], evidence_ref_ids: ["EV-MASTER-PLAN"], not_public_postable: true },
        { lane_id: "future_artifact_backed", name: "Future Artifact-Backed Content", status: "BLOCKED", claim_risk: "blocked", forbidden_language: "blocked until real artifacts", limitations: ["no artifact IDs", "no lineage", "no freshness/DQR state"], platform_fit: "unavailable", checklist: ["blocked: no approved artifacts"], evidence_ref_ids: ["EV-MASTER-PLAN"], not_public_postable: true },
        { lane_id: "failure_forensics", name: "Failure Forensics", status: "REVIEW_REQUIRED", claim_risk: "low", forbidden_language: "none detected", limitations: ["post-mortem philosophy only"], platform_fit: "dry-run preview only", checklist: ["no market call", "educational"], evidence_ref_ids: ["EV-MASTER-PLAN"], not_public_postable: true },
        { lane_id: "macro_education", name: "Macro Education", status: "REVIEW_REQUIRED", claim_risk: "low", forbidden_language: "none detected", limitations: ["education only", "no advice"], platform_fit: "dry-run preview only", checklist: ["no advice", "no signal"], evidence_ref_ids: ["EV-MASTER-PLAN"], not_public_postable: true },
        { lane_id: "product_update", name: "Product Update", status: "REVIEW_REQUIRED", claim_risk: "low", forbidden_language: "none detected", limitations: ["product/process only"], platform_fit: "dry-run preview only", checklist: ["no public-ready copy"], evidence_ref_ids: ["EV-MASTER-PLAN"], not_public_postable: true }
      ]
    },

    {
      screen_id: "publish_readiness",
      nav_label: "Publish Readiness Tower",
      title: "Publish Readiness Tower",
      primary_question: "What must be true before supervised publishing is even possible?",
      readiness_verdict: {
        status: "BLOCKED",
        severity: "blocked",
        label: "Readiness Verdict",
        text: "Supervised publishing is BLOCKED. Next blocker: official docs verification + credential policy gate.",
        reason: "No platform has cleared the gate matrix; live adapter, scheduler, and posting are disabled.",
        evidence_ref_ids: ["EV-MASTER-PLAN", "EV-0174D"],
        allowed_actions: ["inspect contract", "view dry-run shape"],
        blocked_actions: ["publish", "post", "send", "schedule", "dispatch", "api call", "credential validation"],
        current_truth: true,
        historical_provenance: false
      },
      gate_columns: ["platform", "official docs", "dry-run renderer", "approval ledger", "credential slot", "credential read", "credential validation", "redacted audit", "kill switch", "live adapter", "scheduler", "posting", "next blocker"],
      gate_matrix: [
        { platform: "Telegram", official_docs: "REVIEW_REQUIRED", dry_run_renderer: "PASS", approval_ledger: "PASS", credential_slot: "FUTURE_ONLY", credential_read: "LIVE_DISABLED", credential_validation: "LIVE_DISABLED", redacted_audit: "PASS", kill_switch: "BLOCKED", live_adapter: "LIVE_DISABLED", scheduler: "LIVE_DISABLED", posting: "LIVE_DISABLED", next_blocker: "Official docs verification + future credential gate" },
        { platform: "X", official_docs: "REVIEW_REQUIRED", dry_run_renderer: "PASS", approval_ledger: "PASS", credential_slot: "FUTURE_ONLY", credential_read: "LIVE_DISABLED", credential_validation: "LIVE_DISABLED", redacted_audit: "PASS", kill_switch: "BLOCKED", live_adapter: "LIVE_DISABLED", scheduler: "LIVE_DISABLED", posting: "LIVE_DISABLED", next_blocker: "Platform capability review (future-only)" },
        { platform: "LinkedIn", official_docs: "REVIEW_REQUIRED", dry_run_renderer: "PASS", approval_ledger: "PASS", credential_slot: "FUTURE_ONLY", credential_read: "LIVE_DISABLED", credential_validation: "LIVE_DISABLED", redacted_audit: "PASS", kill_switch: "BLOCKED", live_adapter: "LIVE_DISABLED", scheduler: "LIVE_DISABLED", posting: "LIVE_DISABLED", next_blocker: "Scope verification (future-only)" },
        { platform: "Substack / Newsletter", official_docs: "REVIEW_REQUIRED", dry_run_renderer: "PASS", approval_ledger: "PASS", credential_slot: "FUTURE_ONLY", credential_read: "LIVE_DISABLED", credential_validation: "LIVE_DISABLED", redacted_audit: "PASS", kill_switch: "BLOCKED", live_adapter: "LIVE_DISABLED", scheduler: "LIVE_DISABLED", posting: "LIVE_DISABLED", next_blocker: "CMS/email provider policy (future-only)" }
      ],
      platform_records: [
        { platform: "Telegram", current_capability: "dry-run only", live_api: "disabled", credential: "not read / redacted presence only / future operator setup required", posting: "disabled", scheduler: "disabled", allowed_now: "inspect / dry-run preview / manual review", forbidden_now: "api call / live post / schedule / scrape / autonomous reply" }
      ]
    },

    {
      screen_id: "evidence_vault",
      nav_label: "Evidence Vault",
      title: "Evidence Vault + Audit Timeline",
      primary_question: "What is the audit trail and how confident are we?",
      evidence_state: {
        status: "PASS",
        severity: "safe",
        label: "Evidence State",
        text: "Audit trail complete to current accepted HEAD (0174D2). Confidence: high for build authority, caveated for browser QA.",
        reason: "Blueprint chain and master plan accepted; browser QA capture accepted with worker-judgment caveat.",
        evidence_ref_ids: ["EV-0174D", "EV-MASTER-PLAN", "EV-0174C-QA"],
        allowed_actions: ["inspect", "view evidence"],
        blocked_actions: ["evidence mutation", "export", "upload"],
        current_truth: true,
        historical_provenance: false
      },
      validation_matrix: [
        { check: "external dependency scan", expected: "no remote URLs / content networks / fonts / sockets", observed: "none in V4 runtime files", status: "PASS", evidence_ref: "EV-TESTS-V4" },
        { check: "current-vs-historical metadata", expected: "stale heads labelled historical only", observed: "labeled truth rail; no stale 0174B gate", status: "PASS", evidence_ref: "EV-0174D" },
        { check: "forbidden controls scan", expected: "no enabled publish/post/send/schedule", observed: "no active forbidden controls", status: "PASS", evidence_ref: "EV-TESTS-V4" },
        { check: "secret scan", expected: "no tracked secrets / no secrets displayed", observed: "clean", status: "PASS", evidence_ref: "EV-TESTS-V4" }
      ],
      evidence_timeline: [
        { commit: "0174D", task: "V4 north-star blueprint", classification: "historical" },
        { commit: "0174D1", task: "blueprint doc/test repair", classification: "historical" },
        { commit: "0174D2", task: "master plan authority", classification: "current" },
        { commit: "0174C", task: "visible browser QA capture", classification: "evidence-only" }
      ],
      caveat_registry: [
        { caveat_id: "CAV-0174C", severity: "minor", source_evidence: "EV-0174C-QA", affected_screen: "evidence_vault", blocking: false, resolution_task: "future Antigravity QA of V4", note: "Worker visual judgment rejected; capture accepted." }
      ],
      forbidden_scope_registry: ["live posting", "scheduler", "platform API", "provider API", "scraping", "credential/env read", "evidence mutation", "export/upload"],
      active_blocker_registry: [
        { id: "BLK-AUDIT", status: "BLOCKED", label: "Awaiting 0174E audit" },
        { id: "BLK-LIVE", status: "LIVE_DISABLED", label: "Supervised publishing blocked" }
      ],
      confidence_legend: ["PASS = validation-safe", "DEGRADED = usable with caveat", "BLOCKED = cannot proceed", "REVIEW_REQUIRED = human decision needed"],
      browser_qa_row: { label: "0174C Browser QA Evidence", status: "pass_with_caveat", note: "Capture accepted; worker visual judgment REJECTED." }
    },

    {
      screen_id: "content_calendar",
      nav_label: "Content Calendar / Workflow",
      title: "Content Calendar / Workflow Board",
      primary_question: "What is the manual plan and what stage is each item at?",
      plan_state: {
        status: "REVIEW_REQUIRED",
        severity: "caution",
        label: "Plan State",
        text: "Manual planning only. No scheduling. No auto-post.",
        reason: "Calendar tracks manual workflow stages only; no automated dispatch exists.",
        evidence_ref_ids: ["EV-MASTER-PLAN"],
        allowed_actions: ["inspect", "manual review"],
        blocked_actions: ["schedule", "queue auto-post", "auto-publish", "dispatch", "bot reply"],
        current_truth: true,
        historical_provenance: false
      },
      allowed_states: ["idea", "source-needed", "research-brief-ready", "draft-review", "blocked", "operator-approved-for-manual", "manually-posted", "metrics-entered"],
      forbidden_states: [
        { state: "scheduled", status: "FUTURE_ONLY", note: "disabled; no scheduler" },
        { state: "queued for auto-post", status: "FUTURE_ONLY", note: "disabled" },
        { state: "auto-publish ready", status: "FUTURE_ONLY", note: "disabled" },
        { state: "live campaign", status: "FUTURE_ONLY", note: "disabled" },
        { state: "API dispatch ready", status: "FUTURE_ONLY", note: "disabled" },
        { state: "bot reply ready", status: "FUTURE_ONLY", note: "disabled" }
      ],
      date_lanes: [
        { period: "Week 1", items: [
          { title: "Build-in-public note", lane: "pre_alpha_process", state: "draft-review", evidence_ref: "EV-MASTER-PLAN" },
          { title: "Macro education explainer", lane: "macro_education", state: "research-brief-ready", evidence_ref: "EV-MASTER-PLAN" }
        ] },
        { period: "Week 2", items: [
          { title: "Grounded news context piece", lane: "grounded_news_context", state: "source-needed", evidence_ref: "EV-MASTER-PLAN" },
          { title: "Artifact-backed analysis", lane: "future_artifact_backed", state: "blocked", evidence_ref: "EV-MASTER-PLAN" }
        ] }
      ]
    },
    {
      screen_id: "visual_export",
      nav_label: "Visual Export / Screenshot-Safe",
      title: "Visual Export / Screenshot-Safe Mode",
      primary_question: "Is this surface safe to screenshot for a briefing?",
      export_state: {
        status: "SECRET_REDACTED",
        severity: "safe",
        label: "Export State",
        text: "Screenshot-safe preparation only. No export/download/upload.",
        reason: "This surface prepares views for safe manual screenshotting only; it performs no export.",
        evidence_ref_ids: ["EV-MASTER-PLAN"],
        allowed_actions: ["inspect", "manual screenshot-safe review"],
        blocked_actions: ["export", "download", "upload", "screenshot automation", "public-ready caption"],
        current_truth: true,
        historical_provenance: false
      },
      report_cards: [
        { card_id: "rc-command-center", surface: "Command Center", safe: true, redactions: ["env_paths", "raw_request_urls"], labels: ["Local fixture UI", "Not public-postable", "Review-only", "Live/API disabled"] },
        { card_id: "rc-evidence-vault", surface: "Evidence Vault", safe: true, redactions: ["credentials", "raw_platform_responses"], labels: ["Local fixture UI", "Not public-postable", "Screenshot-safe"] }
      ],
      redaction_preview: ["token: SECRET_REDACTED", "api_key: SECRET_REDACTED", "chat_id: SECRET_REDACTED", "env_path: SECRET_REDACTED"],
      limitation_strip: ["fixture-only", "no real market data", "no alpha output", "not public market research"],
      data_sufficiency_placeholder: { status: "FUTURE_ONLY", note: "No real artifacts; data sufficiency cannot be computed." },
      forecast_readiness_placeholder: { status: "FUTURE_ONLY", note: "Forecast readiness blocked: no approved artifacts/lineage/DQR state." },
      blocked_forecast_explainer: "Forecasts are blocked until real approved Capital Chronicle artifacts exist with lineage, freshness, and DQR state. No signal, no prediction, no target.",
      failure_forensics_card: { title: "Failure Forensics", note: "Post-mortem discipline only; educational, no market call." }
    },

    {
      screen_id: "settings_safety_policy",
      nav_label: "Settings / Safety Policy",
      title: "Settings / Safety Policy",
      primary_question: "What are the hard boundaries and what is never displayed?",
      policy_state: {
        status: "PASS",
        severity: "safe",
        label: "Policy State",
        text: "Hard boundaries enforced. Credentials never displayed.",
        reason: "All live capabilities disabled; this screen is policy inspection only, not a credential screen.",
        evidence_ref_ids: ["EV-MASTER-PLAN"],
        allowed_actions: ["inspect"],
        blocked_actions: ["display credential", "enable live", "enable scheduler", "enable scraping"],
        current_truth: true,
        historical_provenance: false
      },
      policy_matrix: [
        { policy: "Network", value: "disabled", enforcement: "no runtime requests / sockets / content networks", rationale: "local-only static cockpit" },
        { policy: "Live posting", value: "disabled", enforcement: "no live adapter", rationale: "kill switch active; future gate only" },
        { policy: "Scheduler", value: "disabled", enforcement: "no scheduler", rationale: "manual workflow only" },
        { policy: "Platform API", value: "disabled", enforcement: "no platform API", rationale: "future supervised gate only" },
        { policy: "Provider API", value: "disabled", enforcement: "no provider/LLM API", rationale: "repo executes no prompts" },
        { policy: "Credential read", value: "disabled", enforcement: "no env/credential read", rationale: "secrets stay out-of-band" },
        { policy: "Financial advice", value: "prohibited", enforcement: "content governance", rationale: "no advice, no directional calls" },
        { policy: "Signal language", value: "prohibited", enforcement: "forbidden-language scan", rationale: "no signal/target/prediction" },
        { policy: "Market-direction color", value: "prohibited", enforcement: "color = governance safety only", rationale: "no bullish/bearish semantics" }
      ],
      credential_never_display_registry: [
        { item: "bot token", display: "SECRET_REDACTED" },
        { item: "API key", display: "SECRET_REDACTED" },
        { item: "chat ID", display: "SECRET_REDACTED" },
        { item: "env path", display: "SECRET_REDACTED" },
        { item: "raw platform response", display: "SECRET_REDACTED" }
      ],
      platform_gate_policy: "Every platform remains future-only until official docs verification, credential policy, manual approval, and an explicit live gate are cleared.",
      future_gate_requirements: [
        { gate: "official docs verification", status: "FUTURE_ONLY" },
        { gate: "credential setup", status: "FUTURE_ONLY" },
        { gate: "live adapter enablement", status: "FUTURE_ONLY" }
      ]
    }
  ]
};

