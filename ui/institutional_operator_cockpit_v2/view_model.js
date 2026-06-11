/*
 * Capital Chronicle ContentOps — Operator Cockpit V2 view model.
 *
 * Local-only, fixture-driven. No network, no fetch, no remote dependency.
 * This file is the SINGLE canonical source of operational truth for the
 * cockpit. No screen component hardcodes current baseline / current gate /
 * kill switch / public state independently; they all read from
 * CC_COCKPIT_V2_VIEW_MODEL.global_state.
 *
 * Current operational truth is distinct from historical screen provenance
 * and from Stitch visual reference provenance. Historical and reference
 * provenance are explicitly labelled "Not Runtime Authority".
 */
window.CC_COCKPIT_V2_VIEW_MODEL = {
  meta: {
    task_label:
      "TASK_CONTENTOPS_0174R_REFERENCE_DRIVEN_OPERATOR_COCKPIT_V2_FRONTEND_REBUILD_V0",
    product_name: "Capital Chronicle ContentOps",
    surface_name: "Operator Cockpit V2",
    build_kind: "local / static / fixture-driven",
    runtime_authority: false
  },

  // Canonical current operational truth. Read by every screen/header.
  global_state: {
    current_mode: "local_pre_alpha",
    current_product_state: "local / static / fixture-driven",
    current_repo_baseline: "680d03d",
    current_repo_baseline_note:
      "Current repo baseline entering 0174R (docs-only rollback bundle).",
    last_product_code_baseline: "496591f",
    last_product_code_baseline_note:
      "Last accepted product/code baseline before the docs-only rollback bundle.",
    kill_switch: "active",
    live_state: "disabled",
    platform_api_state: "disabled",
    provider_api_state: "disabled",
    scheduler_state: "disabled",
    credential_read_state: "disabled",
    public_state: "not_public_postable",
    review_state: "review_only",
    current_gate:
      "Awaiting ChatGPT audit of 0174R after build",
    next_allowed_action:
      "ChatGPT audit of Cline evidence packet, then only if accepted proceed to Antigravity/browser QA by explicit approval"
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
    { id: "publish_readiness", label: "Publish Readiness Gate Matrix" },
    { id: "evidence_vault", label: "Evidence Vault" },
    { id: "content_calendar", label: "Content Calendar / Workflow Board" },
    { id: "visual_export", label: "Visual Export / Screenshot-Safe Mode" },
    { id: "settings", label: "Settings / Safety Policy" }
  ],

  // Historical screen provenance. NOT runtime authority. Stale heads live
  // here only, explicitly labelled, so they never read as current truth.
  historical_screen_provenance: {
    label: "Historical Screen Provenance",
    runtime_authority: false,
    not_runtime_authority: true,
    note:
      "Historical per-screen build provenance. Not current operational truth.",
    entries: [
      {
        head: "15b87ff",
        label: "Historical Screen Provenance",
        runtime_authority: false,
        note: "0159 view-model baseline (historical). Not current."
      },
      {
        head: "1c03ca0",
        label: "Historical Screen Provenance",
        runtime_authority: false,
        note: "Historical prior shell screen baseline. Not current."
      },
      {
        head: "444ef2c",
        label: "Historical Screen Provenance",
        runtime_authority: false,
        note: "Historical pre-0174 accepted baseline. Not current."
      }
    ]
  },

  // Stitch visual reference provenance. NOT runtime authority.
  stitch_reference_provenance: {
    label: "Visual Reference Only",
    runtime_authority: false,
    not_runtime_authority: true,
    source: "operator-supplied local Stitch governance terminal folder",
    note:
      "Stitch HTML/CSS/PNG used as advisory visual reference only. Not copied, not imported, not runtime."
  },

  status_vocabulary: [
    "PASS", "DEGRADED", "BLOCKED", "REVIEW_REQUIRED", "LIVE_DISABLED",
    "NOT_PUBLIC_POSTABLE", "FUTURE_ONLY", "UNKNOWN", "SECRET_REDACTED"
  ],

  screens: {
    command_center: {
      title: "ContentOps Command Center",
      purpose:
        "Answer one question: can anything proceed, and if not, why? Local, static, fixture-driven governance overview.",
      runtime_authority: false,
      screen_state: {
        what_for:
          "Single decision surface summarising whether any operation may proceed under current safety gates.",
        static_local_fixture_driven: true,
        runtime_authority: false
      },
      primary_gate: {
        status: "BLOCKED",
        severity: "block",
        label: "Awaiting ChatGPT audit of 0174R",
        reason:
          "0174R is a local static frontend rebuild. Nothing may proceed to QA or any next task until the evidence packet is audited and accepted.",
        evidence_ref_ids: ["EV-0174R-BUILD", "EV-0174G-SYNC"],
        next_allowed_action:
          "ChatGPT audit of Cline evidence packet; if accepted, explicit approval for Antigravity/browser QA."
      },
      decision_panel: {
        question: "Can anything proceed, and if not, why?",
        answer: "No automated/live/public action may proceed.",
        reason:
          "Kill switch active. Live disabled. Platform/provider/scheduler/credential reads disabled. Review-only, not public-postable.",
        current_truth: true,
        historical_provenance: false
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
          evidence_ref_ids: ["EV-0174R-BUILD"],
          allowed_actions: ["inspect", "review"],
          blocked_actions: ["publish", "schedule", "live_api"],
          current_truth: true, historical_provenance: false,
          caveat: "PASS means system-safe only; never publish/forecast/market-ready."
        },
        {
          status: "BLOCKED", severity: "block", label: "Next Task Gate",
          reason: "Audit of 0174R evidence not yet performed.",
          evidence_ref_ids: ["EV-0174R-BUILD"],
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
        screen_build_task: "0174R",
        label: "Historical Screen Provenance",
        runtime_authority: false,
        note: "This screen build provenance is not current operational authority."
      }
    },


    publish_readiness: {
      title: "Publish Readiness Gate Matrix",
      purpose:
        "A gate matrix, not a platform control dashboard. Shows per-platform readiness gates with no send/post/publish affordances.",
      runtime_authority: false,
      screen_state: {
        what_for:
          "Display readiness gates per platform: contract, dry-run shape, docs gate, credential slot, approval, audit, kill switch, next blocker.",
        static_local_fixture_driven: true,
        runtime_authority: false
      },
      primary_gate: {
        status: "LIVE_DISABLED",
        severity: "block",
        label: "Live posting disabled across all platforms",
        reason:
          "Kill switch active. No live adapter, scheduler, or posting path exists. Credential reads disabled.",
        evidence_ref_ids: ["EV-SAFETY-POLICY", "EV-PUBLISH-GATES"],
        next_allowed_action: "Inspect contracts and dry-run shapes only."
      },
      platforms: [
        { name: "Telegram", note: "future pilot channel" },
        { name: "X", note: "short education hooks" },
        { name: "LinkedIn", note: "long-form context" },
        { name: "Instagram", note: "visual asset export prep" }
      ],
      gate_rows: [
        { gate: "platform contract exists", state: "PASS", label: "inspect contract" },
        { gate: "dry-run renderer exists", state: "PASS", label: "view dry-run shape" },
        { gate: "official docs gate", state: "REVIEW_REQUIRED", label: "future gate" },
        { gate: "credential slot defined", state: "PASS", label: "slot only" },
        { gate: "credential read status", state: "LIVE_DISABLED", label: "disabled / not read" },
        { gate: "credential validation", state: "LIVE_DISABLED", label: "disabled" },
        { gate: "manual approval gate", state: "REVIEW_REQUIRED", label: "manual review only" },
        { gate: "redacted audit logging gate", state: "PASS", label: "redacted only" },
        { gate: "kill switch gate", state: "BLOCKED", label: "disabled by kill switch" },
        { gate: "live adapter", state: "LIVE_DISABLED", label: "disabled" },
        { gate: "scheduler", state: "LIVE_DISABLED", label: "disabled" },
        { gate: "posting", state: "LIVE_DISABLED", label: "disabled" }
      ],
      status_tokens: [
        {
          status: "LIVE_DISABLED", severity: "block", label: "Live Adapters",
          reason: "No platform has an enabled live adapter; kill switch active.",
          evidence_ref_ids: ["EV-PUBLISH-GATES"],
          allowed_actions: ["inspect_contract", "view_dry_run"],
          blocked_actions: ["post", "publish", "dispatch", "schedule", "api_call"],
          current_truth: true, historical_provenance: false
        },
        {
          status: "REVIEW_REQUIRED", severity: "review", label: "Manual Approval Gate",
          reason: "Manual operator approval is a precondition that is not satisfied and cannot be automated here.",
          evidence_ref_ids: ["EV-PUBLISH-GATES"],
          allowed_actions: ["manual_review"],
          blocked_actions: ["auto_approve"],
          current_truth: true, historical_provenance: false
        }
      ],
      next_blocker: "Official docs verification + manual approval (future, gated).",
      build_provenance: {
        screen_build_task: "0174R",
        label: "Historical Screen Provenance",
        runtime_authority: false
      }
    },


    evidence_vault: {
      title: "Evidence Vault + Audit Timeline",
      purpose:
        "Compliance-grade evidence room. Every critical status elsewhere traces to evidence IDs here. Read-only.",
      runtime_authority: false,
      screen_state: {
        what_for:
          "Index evidence packets, commit/evidence timeline, validation matrix, caveat registry, forbidden-scope matrix, blocker registry.",
        static_local_fixture_driven: true,
        runtime_authority: false
      },
      primary_gate: {
        status: "PASS",
        severity: "ok",
        label: "Evidence read-only",
        reason: "Evidence is read-only; no mutation, export, or upload is possible from this surface.",
        evidence_ref_ids: ["EV-0174R-BUILD"],
        next_allowed_action: "Inspect evidence only.",
        caveat: "PASS means evidence integrity/read-only, not publish-readiness."
      },
      evidence_index: [
        { id: "EV-0174G-SYNC", task: "0174G", classification: "setup", head: "680d03d", artifact: "GitHub evidence sync setup" },
        { id: "EV-0174R-BUILD", task: "0174R", classification: "frontend rebuild", head: "680d03d", artifact: "Operator Cockpit V2 static frontend" },
        { id: "EV-SAFETY-POLICY", task: "policy", classification: "safety", head: "680d03d", artifact: "Hard boundary / safety policy fixture" },
        { id: "EV-CONTENT-SAFETY", task: "policy", classification: "content", head: "680d03d", artifact: "Content safety / claim-risk fixture" },
        { id: "EV-PUBLISH-GATES", task: "policy", classification: "publish", head: "680d03d", artifact: "Publish readiness gate matrix fixture" }
      ],
      commit_timeline: [
        { head: "496591f", label: "Last Product Code Baseline", note: "test: add institutional shell view model drift guard", current_truth: false },
        { head: "680d03d", label: "Current Repo Baseline", note: "docs: add minimal project sources bundle after 0174 rollback", current_truth: true }
      ],
      validation_matrix: [
        { check: "external dependency scan", expected: "no remote URLs / CDNs / fetch / sockets" },
        { check: "current-vs-historical metadata", expected: "stale heads labelled historical only" },
        { check: "forbidden controls scan", expected: "no enabled publish/post/send/schedule" },
        { check: "secret scan", expected: "no tracked secrets / no secrets displayed" }
      ],
      caveat_registry: [
        "PASS never means publish/forecast/live/market-ready.",
        "Color communicates system safety only, never market direction.",
        "Stitch reference is visual-only and not runtime authority."
      ],
      forbidden_scope_matrix: [
        "live posting", "scheduler", "platform api", "provider/llm api",
        "telegram api", "scraping", "autonomous replies/dms", "one-button publish-all",
        "export/upload/download", "screenshot automation", "credential read", "env read"
      ],
      active_blockers: [
        { id: "BLK-AUDIT", label: "ChatGPT audit of 0174R pending", severity: "block" }
      ],
      next_task_discipline:
        "Do not start, shrink, rename, or invent the next phase. Await audit acceptance.",
      build_provenance: {
        screen_build_task: "0174R",
        label: "Historical Screen Provenance",
        runtime_authority: false
      }
    },
    content_studio: {
      title: "Content Studio",
      purpose:
        "Editorial QA cockpit separating pre-alpha process, grounded news context, and future artifact-backed content. No public-ready copy.",
      runtime_authority: false,
      screen_state: {
        what_for:
          "Show claim-risk visibility, forbidden-language results, and source/brief/lineage placeholders. Manual review required.",
        static_local_fixture_driven: true,
        runtime_authority: false
      },
      primary_gate: {
        status: "REVIEW_REQUIRED",
        severity: "review",
        label: "Manual review required",
        reason:
          "No content is public-ready. All drafts require manual operator review; no live/auto path exists.",
        evidence_ref_ids: ["EV-CONTENT-SAFETY"],
        next_allowed_action: "Manual operator review only."
      },
      lanes: [
        { id: "pre_alpha_process", label: "Pre-Alpha Process", description: "Internal process scaffolding. Not public output.", status: "REVIEW_REQUIRED" },
        { id: "grounded_news_context", label: "Grounded News Context", description: "Context lane for grounded sourcing. Requires source/brief/lineage. Not public output.", status: "REVIEW_REQUIRED" },
        { id: "future_artifact_backed", label: "Future Artifact-Backed Content", description: "Future-only lane. Requires verified artifacts before any drafting.", status: "FUTURE_ONLY" }
      ],
      status_tokens: [
        {
          status: "REVIEW_REQUIRED", severity: "review", label: "Claim Risk Visibility",
          reason: "Claims must be classified and manually reviewed; no unverified numeric market claims.",
          evidence_ref_ids: ["EV-CONTENT-SAFETY"],
          allowed_actions: ["inspect", "classify", "manual_review"],
          blocked_actions: ["publish", "auto_generate_final_copy"],
          current_truth: true, historical_provenance: false
        },
        {
          status: "PASS", severity: "ok", label: "Forbidden Language Result",
          reason: "No financial advice, no signal/buy/sell/hold language present in fixture.",
          evidence_ref_ids: ["EV-CONTENT-SAFETY"],
          allowed_actions: ["inspect"],
          blocked_actions: ["signal_language", "financial_advice"],
          current_truth: true, historical_provenance: false,
          caveat: "PASS means safety-checked only; not publish-ready."
        },
        {
          status: "NOT_PUBLIC_POSTABLE", severity: "block", label: "Publish State",
          reason: "Content is review-only and not public-postable.",
          evidence_ref_ids: ["EV-SAFETY-POLICY"],
          allowed_actions: ["manual_review"],
          blocked_actions: ["post", "publish"],
          current_truth: true, historical_provenance: false
        }
      ],
      source_lineage_placeholder: {
        source: "(manual entry placeholder — not populated)",
        brief: "(manual entry placeholder — not populated)",
        lineage: "(manual entry placeholder — not populated)"
      },
      build_provenance: {
        screen_build_task: "0174R",
        label: "Historical Screen Provenance",
        runtime_authority: false
      }
    },

    content_calendar: {
      title: "Content Calendar / Workflow Board",
      purpose:
        "Manual workflow board only. No scheduling, queuing, auto-publish, or live campaign state exists.",
      runtime_authority: false,
      screen_state: {
        what_for:
          "Track manual editorial workflow states. All movement is manual; no automation, no scheduler, no live dispatch.",
        static_local_fixture_driven: true,
        runtime_authority: false
      },
      primary_gate: {
        status: "REVIEW_REQUIRED",
        severity: "review",
        label: "Manual workflow only",
        reason: "Every state transition is manual. Scheduling and auto-publish states are forbidden.",
        evidence_ref_ids: ["EV-SAFETY-POLICY"],
        next_allowed_action: "Manual workflow tracking only."
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
        { title: "Macro context note", state: "idea" },
        { title: "Grounded news brief", state: "source-needed" },
        { title: "Education hook draft", state: "draft-review" },
        { title: "Awaiting operator sign-off", state: "operator-approved-for-manual" }
      ],
      status_tokens: [
        {
          status: "REVIEW_REQUIRED", severity: "review", label: "Workflow Movement",
          reason: "Manual-only. No scheduler/queue/auto-publish exists.",
          evidence_ref_ids: ["EV-SAFETY-POLICY"],
          allowed_actions: ["manual_move", "manual_review"],
          blocked_actions: ["schedule", "queue", "auto_publish"],
          current_truth: true, historical_provenance: false
        }
      ],
      build_provenance: {
        screen_build_task: "0174R",
        label: "Historical Screen Provenance",
        runtime_authority: false
      }
    },
    visual_export: {
      title: "Visual Export / Screenshot-Safe Mode",
      purpose:
        "Screenshot-safe preparation only. Not an export engine. No image export, PDF, upload, download, or screenshot automation.",
      runtime_authority: false,
      screen_state: {
        what_for:
          "Confirm screenshot-safe preparation: local-only, not public-postable, live-disabled, secret-redacted. No export action exists.",
        static_local_fixture_driven: true,
        runtime_authority: false
      },
      primary_gate: {
        status: "NOT_PUBLIC_POSTABLE",
        severity: "block",
        label: "Preparation only — no export",
        reason: "This surface prepares views for safe manual screenshotting only. It performs no export, upload, or download.",
        evidence_ref_ids: ["EV-SAFETY-POLICY"],
        next_allowed_action: "Manual, local screenshot-safe review only."
      },
      checklist: [
        { item: "screenshot-safe preparation only", state: "PASS" },
        { item: "local-only", state: "PASS" },
        { item: "not public-postable", state: "NOT_PUBLIC_POSTABLE" },
        { item: "live disabled", state: "LIVE_DISABLED" },
        { item: "no financial advice", state: "PASS" },
        { item: "secret redaction confirmed", state: "SECRET_REDACTED" }
      ],
      forbidden: [
        "actual image export", "PDF generation", "platform upload", "file download",
        "screenshot automation", "public-ready caption generation", "live sharing"
      ],
      limitation_notes: [
        "No export/download/upload behavior exists in this surface.",
        "Screenshots, if taken, are a manual operator action outside this app."
      ],
      status_tokens: [
        {
          status: "SECRET_REDACTED", severity: "ok", label: "Redaction State",
          reason: "No secrets, tokens, keys, chat IDs, or raw platform responses are displayed.",
          evidence_ref_ids: ["EV-SAFETY-POLICY"],
          allowed_actions: ["inspect"],
          blocked_actions: ["export", "upload", "download"],
          current_truth: true, historical_provenance: false
        }
      ],
      build_provenance: {
        screen_build_task: "0174R",
        label: "Historical Screen Provenance",
        runtime_authority: false
      }
    },

    settings: {
      title: "Settings / Safety Policy",
      purpose:
        "Safety policy surface, not a credential display screen. Never shows real tokens, keys, chat IDs, env paths, or raw platform responses.",
      runtime_authority: false,
      screen_state: {
        what_for:
          "Document active hard boundaries, forbidden actions, and the credential/redaction/platform/content/financial-advice/live-gate policies.",
        static_local_fixture_driven: true,
        runtime_authority: false
      },
      primary_gate: {
        status: "PASS",
        severity: "ok",
        label: "Policy display only",
        reason: "This surface displays policy only; it cannot read, validate, or reveal credentials.",
        evidence_ref_ids: ["EV-SAFETY-POLICY"],
        next_allowed_action: "Inspect policy only.",
        caveat: "PASS means policy is intact, not publish-readiness."
      },
      hard_boundaries: [
        "Kill switch active.", "Live posting disabled.", "Scheduler disabled.",
        "Platform API disabled.", "Provider/LLM API disabled.", "Telegram API disabled.",
        "Credential reads disabled.", "Env reads disabled.", "Scraping disabled.",
        "Autonomous replies/DMs disabled.", "No one-button publish-all.", "Review-only, not public-postable."
      ],
      policies: [
        { name: "credential policy", value: "Credential slots are policy placeholders only; never read or validated here." },
        { name: "redaction policy", value: "Secrets/tokens/keys/chat IDs are never displayed; redacted presence only." },
        { name: "platform gate policy", value: "Each platform is gated; no live adapter is enabled." },
        { name: "content safety policy", value: "No financial advice, no signal language, no unverified numeric market claims." },
        { name: "financial advice prohibition", value: "No buy/sell/hold, position sizing, or signal-service framing." },
        { name: "live behavior disablement", value: "All live behavior is disabled pending future explicit gates." }
      ],
      never_display: [
        "real token", "API key", "sensitive chat ID", "env path with secrets", "raw platform response"
      ],
      status_tokens: [
        {
          status: "PASS", severity: "ok", label: "Hard Boundaries Intact",
          reason: "All hard boundaries are declared active in fixture; no boundary is relaxed.",
          evidence_ref_ids: ["EV-SAFETY-POLICY"],
          allowed_actions: ["inspect"],
          blocked_actions: ["edit_policy", "reveal_credential"],
          current_truth: true, historical_provenance: false,
          caveat: "PASS means safety boundaries intact only."
        }
      ],
      build_provenance: {
        screen_build_task: "0174R",
        label: "Historical Screen Provenance",
        runtime_authority: false
      }
    }
  }
};



