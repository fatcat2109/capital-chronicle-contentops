/*
 * Operator Cockpit V4 â€” Canonical View Model
 * TASK_CONTENTOPS_0174E clean-room build.
 *
 * Local-only, static, deterministic. No network, no fetch, no storage, no
 * secrets, no platform/provider/credential behavior. This object is the single
 * source of operational truth; the header and every screen read from it.
 * Historical and Stitch provenance are explicitly labeled "Not Runtime Authority".
 */
var CC_OPERATOR_EVIDENCE_BASELINES = {
  current_branch_head: "13656e91a4c0cd14c898f1700454836f82624022",
  master_baseline_head: "8e57c4aa8af6e5089c8d7bc07d8104d5260eea27",
  source_evidence_baseline_head: "add55ea1c7447770cb9382f86af1794b951ae8f1",
  prep02_bridge_head: "8e57c4aa8af6e5089c8d7bc07d8104d5260eea27",
  protected_truth_rail_head: "992a7d0"
};
var CC_OPERATOR_ENV_BOUNDARY_PATH = "A:\\Capital Chronicle\\tools\\cc-live-contentops\\.env";
var CC_OPERATOR_SURFACE_TRUE_FLAGS = [
  "evidence_only", "non_executable", "manual_review_required", "local_only",
  "ui_surface_ready"
];
var CC_OPERATOR_SURFACE_FALSE_FLAG_GROUPS = [
  { category: "readiness", flags: ["public_ready", "live_ready", "readiness_granted"] },
  { category: "dispatch/execution", flags: ["dispatch_ready", "executable_dispatch"] },
  { category: "API/provider", flags: ["platform_api_allowed_now"] },
  { category: "credential/env", flags: ["credential_read_allowed_now"] },
  { category: "scheduler/posting", flags: ["scheduler_enabled_now", "posting_enabled_now"] },
  { category: "audit event/allowlist", flags: ["audit_event_created", "audit_allowlist_modified"] }
];
var CC_OPERATOR_HOSTILE_CASES = [
  {
    case_id: "required_false_credential_read_true_blocks",
    mutation: "credential_read_allowed_now = true",
    expected_state: "BLOCKED",
    rationale: "A required-false safety flag turned true is a contradiction; fail-closed to BLOCKED."
  },
  {
    case_id: "required_true_evidence_only_false_blocks",
    mutation: "evidence_only = false",
    expected_state: "BLOCKED",
    rationale: "A required-true evidence flag turned false is a contradiction; fail-closed to BLOCKED."
  },
  {
    case_id: "missing_bridge_report_hash_unknown",
    mutation: "bridge_report_hash empty with validation_state UNKNOWN",
    expected_state: "UNKNOWN",
    rationale: "Missing lineage/hash id cannot establish lineage; computed UNKNOWN with declared state reset."
  },
  {
    case_id: "declared_pass_after_missing_bridge_hash_blocks",
    mutation: "bridge_report_hash empty while declared PASS remains",
    expected_state: "BLOCKED",
    rationale: "Declared PASS contradicting missing lineage and fail-closes to BLOCKED."
  },
  {
    case_id: "static_bridge_prefix_safe",
    mutation: "none",
    expected_state: "PASS",
    rationale: "Unmutated valid packet yields the evidence-only static JS bridge prefix."
  }
];

function operatorEvidenceSurfaceField(surface, key, fallback) {
  if (!surface || surface[key] === undefined || surface[key] === null) return fallback;
  return surface[key];
}

function operatorEvidenceSurfaceTruth() {
  var surface = window.CC_OPERATOR_EVIDENCE_SURFACE || null;
  var availability = surface ? "PRESENT" : "MISSING";
  var missingLineage = surface ? [
    "bridge_report_id", "bridge_report_hash", "compiler_output_id",
    "compile_report_id", "payload_hash_manifest_id",
    "readiness_alignment_id", "audit_alignment_id"
  ].filter(function (k) { return !surface[k]; }) : ["CC_OPERATOR_EVIDENCE_SURFACE"];
  var falseViolations = surface ? CC_OPERATOR_SURFACE_FALSE_FLAG_GROUPS.reduce(function (acc, group) {
    group.flags.forEach(function (flag) { if (surface[flag] === true) acc.push(flag); });
    return acc;
  }, []) : [];
  var trueViolations = surface ? CC_OPERATOR_SURFACE_TRUE_FLAGS.filter(function (flag) {
    return surface[flag] !== true;
  }) : CC_OPERATOR_SURFACE_TRUE_FLAGS.slice();
  var integrity = "UNKNOWN";
  if (falseViolations.length || trueViolations.length || (surface && surface.no_grant_label !== "EVIDENCE ONLY / NO GRANT")) {
    integrity = "BLOCKED";
  } else if (missingLineage.length) {
    integrity = "UNKNOWN";
  } else if (operatorEvidenceSurfaceField(surface, "rollup_state", "UNKNOWN") === "PASS") {
    integrity = "PASS";
  } else {
    integrity = operatorEvidenceSurfaceField(surface, "rollup_state", "REVIEW_REQUIRED");
  }
  var requiredTrue = CC_OPERATOR_SURFACE_TRUE_FLAGS.map(function (flag) {
    return { flag: flag, expected: true, observed: !!operatorEvidenceSurfaceField(surface, flag, false),
      state: operatorEvidenceSurfaceField(surface, flag, false) === true ? "PASS" : "BLOCKED" };
  });
  var requiredFalse = CC_OPERATOR_SURFACE_FALSE_FLAG_GROUPS.map(function (group) {
    return { category: group.category, flags: group.flags.map(function (flag) {
      var observed = operatorEvidenceSurfaceField(surface, flag, false);
      return { flag: flag, expected: false, observed: observed, state: observed === false ? "PASS" : "BLOCKED" };
    }) };
  });
  var hostileCases = CC_OPERATOR_HOSTILE_CASES.map(function (c) {
    return { case_id: c.case_id, mutation: c.mutation, expected_state: c.expected_state, rationale: c.rationale };
  });
  return {
    availability: availability,
    integrity_state: integrity,
    no_grant_label: operatorEvidenceSurfaceField(surface, "no_grant_label", "EVIDENCE SURFACE UNAVAILABLE / NO GRANT"),
    current_branch_head: CC_OPERATOR_EVIDENCE_BASELINES.current_branch_head,
    master_baseline_head: CC_OPERATOR_EVIDENCE_BASELINES.master_baseline_head,
    source_evidence_baseline_head: CC_OPERATOR_EVIDENCE_BASELINES.source_evidence_baseline_head,
    prep02_bridge_head: CC_OPERATOR_EVIDENCE_BASELINES.prep02_bridge_head,
    protected_truth_rail_head: CC_OPERATOR_EVIDENCE_BASELINES.protected_truth_rail_head,
    surface_id: operatorEvidenceSurfaceField(surface, "surface_id", "missing-operator-evidence-surface"),
    operator_evidence_summary_id: operatorEvidenceSurfaceField(surface, "operator_evidence_summary_id", "UNKNOWN"),
    bridge_report_hash: operatorEvidenceSurfaceField(surface, "bridge_report_hash", "UNKNOWN"),
    readiness_alignment_id: operatorEvidenceSurfaceField(surface, "readiness_alignment_id", "UNKNOWN"),
    audit_alignment_id: operatorEvidenceSurfaceField(surface, "audit_alignment_id", "UNKNOWN"),
    required_true_flags: requiredTrue,
    required_false_flags: requiredFalse,
    component_state_matrix: operatorEvidenceSurfaceField(surface, "component_state_matrix", []),
    evidence_path_nodes: operatorEvidenceSurfaceField(surface, "evidence_path_nodes", []),
    hostile_matrix_summary: {
      never_pass: true,
      total_cases: hostileCases.length,
      source: "fixtures/scd_operator_evidence_surface/hostile_degraded_cases.json",
      cases: hostileCases
    },
    blocked_actions: operatorEvidenceSurfaceField(surface, "blocked_actions", [
      "no_live_posting", "no_platform_api_call", "no_provider_api_call",
      "no_credential_read", "no_scheduler_enable", "no_dispatch_execute",
      "no_audit_event_create", "no_audit_allowlist_modify",
      "no_autonomous_replies", "no_direct_messages", "no_scraping"
    ]),
    fallback_reason: surface ? "" : "Frozen operator evidence bridge missing; model exposes UNKNOWN and grants nothing.",
    credential_boundary: {
      known_credential_file_path: CC_OPERATOR_ENV_BOUNDARY_PATH,
      policy: "do not read, do not parse, do not load, do not display values",
      runtime_posture: "UI safety copy only; no file or environment access logic."
    },
    current_vs_historical_notes: [
      "13656e91a4c0cd14c898f1700454836f82624022 is the 0174BW repair branch baseline.",
      "8e57c4aa8af6e5089c8d7bc07d8104d5260eea27 is both master and Prep02 bridge baseline.",
      "add55ea1c7447770cb9382f86af1794b951ae8f1 is the source evidence baseline.",
      "992a7d0 remains protected prior V4 truth rail provenance, not the 0174BW branch head."
    ]
  };
}

window.CC_OPERATOR_COCKPIT_V4_MODEL = {
  meta: {
    version: "v4",
    build_task: "TASK_CONTENTOPS_0174E_OPERATOR_COCKPIT_V4_NORTH_STAR_CLEAN_ROOM_FRONTEND_BUILD_V0",
    mode: "static / local / fixture-driven",
    runtime_authority: false,
    generated_note: "Deterministic local fixtures only. No live data, no market data."
  },

  operator_evidence_surface_truth: operatorEvidenceSurfaceTruth(),

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

  /* Concise collapsed-disclosure summary for the Global Truth Rail (0174Z).
     Shown when the truth rail is collapsed; communicates enough current truth
     without the full provenance wall. The full grid (truth_rail) stays the
     authoritative expanded source. */
  truth_rail_summary: {
    product_head: "992a7d0 / V4 executive cockpit surfaces + hardening (0174AJ_AK)",
    gate: "0174AJ_AK executive cockpit surfaces + hardening implemented; awaiting 0174AL Extreme Browser QA + Source Audit.",
    next_action: "Run 0174AL read-only Extreme Browser QA + Source Audit on the 0174AJ_AK implementation. No source edits during QA. No live/platform/API behavior.",
    safety_status: "Live posting, platform API, provider API, and scheduler disabled; kill switch active"
  },

  /* Labeled truth rail. Every HEAD carries an explicit role label. No bare hashes.
     The current gate must NOT carry the stale 0174B V3 string. */
  truth_rail: [
    {
      role_label: "Current Product HEAD",
      value: "992a7d0 / V4 executive cockpit surfaces + hardening (0174AJ_AK). Prior implementation heads: 152b855 / 0174AI object-centric inspection model; 9570bdc / 0174AIa state-truth + inspect-affordance patch.",
      kind: "current",
      runtime_authority: true
    },
    {
      role_label: "Current Gate",
      value: "0174AJ_AK implementation committed: DecisionSpine, executive command surfaces, productive motion tokens, reduced-motion hardening, and object-centric inspection preservation. Awaiting 0174AL Extreme Browser QA + Source Audit.",
      kind: "current",
      runtime_authority: true
    },
    {
      role_label: "Next Allowed Action",
      value: "Run 0174AL read-only Browser QA + Source Audit using the 20-shot 0174AJ_AK screenshot packet and GitHub source audit. No source edits, no commits, no live/platform/API/credential behavior.",
      kind: "current",
      runtime_authority: true
    },
    {
      role_label: "Build Lineage (Historical Provenance)",
      value: "Clean-room build (0174E); root layout stabilized at 0174I; readable scan layer at 0174S; truth/redundancy cleanup at 0174V; truth-rail progressive disclosure at 0174Z; institutional visual system rebuild at 0174AA (047ca7a); brand-language and state-grammar patches at 0174AB (1f9ed89 / 1e12953); current-state + matte brand composition at 0174AC (4ffe650); dashboard IA + modern matte language pass at 0174AD; screen specialization at 0174AE/0174AF; workspace shell + screen-specific inspector at 0174AG/0174AH; object-centric inspection model at 0174AI (152b855); state-truth + inspect-affordance patch at 0174AIa (9570bdc); executive cockpit surfaces + hardening at 0174AJ_AK (992a7d0). Not Runtime Authority.",
      kind: "historical",
      runtime_authority: false
    },
    {
      role_label: "Tested HEAD (Evidence-only Browser QA)",
      value: "0174C visible Antigravity browser QA evidence commit",
      kind: "evidence_only",
      runtime_authority: false
    },
    {
      role_label: "V3 Failed-Candidate Build",
      value: "ui/institutional_operator_cockpit_v3 â€” historical, NOT accepted as north-star UI",
      kind: "historical",
      runtime_authority: false
    },
    {
      role_label: "V2 Historical Build Candidate",
      value: "ui/institutional_operator_cockpit_v2 â€” historical reference only",
      kind: "historical",
      runtime_authority: false
    },
    {
      role_label: "Reference Quarantine",
      value: "docs/design_references/stitch_institutional_ai_operator_cockpit â€” reference-only, Not Runtime Authority",
      kind: "reference_only",
      runtime_authority: false
    },
    {
      role_label: "Historical Screen Provenance",
      value: "15b87ff / 1c03ca0 / 444ef2c â€” Not Runtime Authority",
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
    { id: "BLK-VISUAL", severity: "review_required", label: "0174AJ_AK executive cockpit surfaces + hardening pending Extreme Browser QA + Source Audit", reason: "The 0174AJ_AK executive cockpit surfaces + hardening are implemented (head 992a7d0); extreme browser QA screenshots and the source audit are still pending before final verification.", evidence_ref_ids: ["EV-0174D", "EV-TESTS-V4"] },
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
  status_tokens: ["PASS", "DEGRADED", "BLOCKED", "REVIEW_REQUIRED", "LIVE_DISABLED", "NOT_PUBLIC_POSTABLE", "FUTURE_ONLY", "UNKNOWN", "SECRET_REDACTED", "SCREENSHOT_SAFE"],


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
        "DecisionSpine flagship executive header added to Command Center (0174AJ).",
        "Productive motion system and tokens added; prefers-reduced-motion coverage hardened (0174AK).",
        "Command tile inspect affordance restyled to matte secondary; native white default button removed (0174AIa).",
        "Selected-object visual state and inspector readability strengthened without glow or neon (0174AIa).",
        "Current-state truth realigned to the implemented head 992a7d0 (0174AJ_AK); prior heads moved to historical provenance."
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
        text: "Audit trail complete to current implemented head 992a7d0 (0174AJ_AK). Confidence: high for build authority, caveated for browser QA.",
        reason: "Blueprint chain and master plan accepted; browser QA capture accepted with worker-judgment caveat; 0174AJ_AK executive cockpit surfaces + hardening awaiting Extreme Browser QA.",
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
        { commit: "0174AA / 047ca7a", task: "institutional visual system rebuild", classification: "historical" },
        { commit: "0174AB / 1e12953", task: "brand-language + state-grammar patch", classification: "historical" },
        { commit: "0174AC / 4ffe650", task: "current-state + matte brand composition", classification: "historical" },
        { commit: "0174AD\u20130174AH", task: "dashboard IA, screen specialization, workspace shell + inspector", classification: "historical" },
        { commit: "0174AI / 152b855", task: "object-centric inspection model", classification: "historical" },
        { commit: "0174AIa / 9570bdc", task: "state-truth + inspect-affordance patch", classification: "historical" },
        { commit: "0174AJ_AK / 992a7d0", task: "executive cockpit surfaces + hardening", classification: "current" },
        { commit: "0174C", task: "visible browser QA capture (V3)", classification: "evidence-only" }
      ],
      caveat_registry: [
        { caveat_id: "CAV-0174C", severity: "minor", source_evidence: "EV-0174C-QA", affected_screen: "evidence_vault", blocking: false, resolution_task: "future Antigravity QA of V4", note: "Worker visual judgment rejected; capture accepted." }
      ],
      forbidden_scope_registry: ["live posting", "scheduler", "platform API", "provider API", "scraping", "credential/env read", "evidence mutation", "export/upload"],
      active_blocker_registry: [
        { id: "BLK-VISUAL", status: "REVIEW_REQUIRED", label: "0174AJ_AK executive surfaces pending Extreme Browser QA + Source Audit" },
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
        status: "SCREENSHOT_SAFE",
        severity: "safe",
        label: "Capture State",
        text: "Screenshot-safe briefing surface. Redacted, fixture-only, no export/download/upload.",
        reason: "This surface prepares views for safe manual screenshotting into a briefing; it performs no export, download, or upload and renders no live secret.",
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
        { policy: "Market-direction color", value: "prohibited", enforcement: "color = governance safety only", rationale: "no market-sentiment direction semantics" }
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
