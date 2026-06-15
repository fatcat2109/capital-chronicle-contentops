# ContentOps Strategy Recovery Map (After 0126)

**Task:** `TASK_CONTENTOPS_0126_STRATEGY_RECOVERY_AND_ROADMAP_RECONCILIATION_V0`

## Executive Summary
During extreme curation phases designed to prevent accidental live capability, the project source bundles were aggressively pruned. This inadvertently stripped the overarching strategic context from the primary repository docs, leaving the impression that ContentOps was in a purely passive "wait for alpha artifacts" state. 

By recovering the historic strategy docs from the 0075-0078 commits, we have reconciled the true architecture: **ContentOps is an active, multi-lane, automation-ready framework.** It incorporates pre-alpha process content, grounded news research, UI/UX front-end design, and deterministic dry-run platform adapters, all governed by strict local-only safety boundaries until explicit supervised live gates are cleared.

## Recovered Source Docs Read
- `FINAL_MASTER_PLAN_PRE_ALPHA_CONTENT_AND_API_AUTOMATION_READINESS_AFTER_0077.md`
- `PRE_ALPHA_GENERAL_PROCESS_AND_GROUNDED_NEWS_MASTER_PLAN_AFTER_0075.md`
- `GROUNDED_RESEARCH_BRIEF_SCHEMA_AFTER_0076.md`
- `TASK_CONTENTOPS_0077_LLM_ASSISTED_DRAFT_REVIEW_PACKET_DRY_RUN_V0.md`
- `PLATFORM_ADAPTER_CONTRACTS_AFTER_0078.md`

## Current Accepted Repo State (Through 0125)
The repository successfully enforces hard boundaries via local-only pipelines, an operator Markdown workbench, and deterministic fail-closed safety checks. Live capabilities (network, API, publishing) are explicitly deactivated. The `pre-alpha-daily-operator-markdown-export` correctly acts as the unified read-only control plane.

## Corrected Strategic Model

### The Three Content Lanes
- **Lane A (Pre-Alpha General/Process Audience-Building):** Educational content, product philosophy, and build-in-public narratives that do not require artifact-backed claims.
- **Lane B (Grounded News / Research Context):** Current events used purely as educational hooks to explain data sufficiency, failure forensics, and macroeconomic realities (no signal language allowed).
- **Lane C (Future Artifact-Backed Capital Chronicle Content):** The pipeline reserved for actual approved alpha artifacts, strictly gated by the approved artifact intake contract.

### Architectural Tracks Distinction
- **Manual Public Track:** Copy/paste from the Markdown workbench; requires human posting.
- **Local Automation-Readiness Track:** Deterministic mock publishing flows, payload schemas, and adapter contracts built locally without active keys.
- **Future Supervised Live API Track:** Explicit, individually gated rollouts for automated platform publishing.
- **UI/UX/Front-End Track:** Dedicated roadmap for interactive dashboarding, preview cards, and operator UI (local fixture/mock-data only for now).
- **SEO/Newsletter Track:** Content architecture designed for Substack, structured SEO, and long-form blogs.

## Capability Inventory

| Capability | Recovered Strategy Says | Current Repo Evidence Found | Status | Restore Action | Risk |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Pre-Alpha Content Lane Policy | Build audience actively via process/educational content. | Fixtures (`seed_macro_edu_001_draft_0`) & markdown UI mentions. | Superseded/Partial | Document formal policy | Low |
| Grounded Research Brief | Use news as a hook; formal schema required. | `grounded_research_brief.py`, schemas, tests present. | Present | Wire into UI | Low |
| LLM-Assisted Draft Review | Deterministic local review of externally generated drafts. | `contentops/phase1_review.py` & draft fixtures present. | Present | Expose in UI / Refine | Low |
| Canonical Social Post | Unified object for all platforms. | Implicit in manual templates. | Unknown/Partial | Formalize contract | Low |
| Platform Adapter Contracts | Specific rules for X, LinkedIn, Telegram, etc. | `platform_adapter_contracts.py` & schemas present. | Present | Update limits/rules | Low |
| Approval Ledger | Cryptographic/strict tracking of human approvals. | Mentioned in old tests (`approval_queue`). | Absent/Partial | Re-implement | Med |
| Kill Switch | Hard halt mechanism for all publishing. | Status output (`kill_switch_halt: active`). | Present | Validate rules | Low |
| Redacted Audit Log | Safe logging without leaking secrets. | Old history mentions. | Absent | Re-implement | Med |
| Mock Publish Flow | Full cycle payload generation and result mocking. | Exists in staging simulation schemas. | Partial | Wire into dry-run | Low |
| Metrics-Readiness Contracts | Schema to ingest post-publish performance. | `manual_performance_record` present. | Superseded | Align with API | Low |
| Credential Envelope | Safe secret injection layer. | Blocked env/credentials in policy tests. | Absent | Design spec | High |
| Official Docs Verification | Operator checklist before API usage. | Old task 0081 mentions. | Absent | Create checklists | Low |
| UI/UX Operator Dashboard | Visual queue, preview cards, calendar. | Purely conceptual in roadmap. | Absent | Design spec | Low |
| Front-End Static Prototype | Interactive local prototype. | Conceptual. | Absent | Build local mock | Low |
| SEO/Blog/Newsletter Arch | Substack/Blog mapping logic. | `seo_metadata.py` present. | Partial | Formalize spec | Low |
| Artifact Intake & MD Bridge | Safely intake real alpha data. | Fully implemented in 0123/0125. | Present | Maintain | Low |

## Recommendation
**Restore Action Plan:** Do not build live integrations yet. Proceed systematically through recovering the structural specs (Content Lanes, Grounded Briefs, Draft Review). Ensure UI/UX and Front-End tracks are formalized as specs first to visualize the operator experience, relying entirely on local fixtures.
