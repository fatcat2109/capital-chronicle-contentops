# Capital Chronicle ContentOps — Multi-Platform Supervised Live Publishing Master Plan

## 0. Executive Position

This plan intentionally ignores the future Capital Chronicle Internal Alpha database and analysis-report lane. The assumption is that Internal Alpha will later provide high-quality source material, analysis reports, data, and artifact-backed context. This plan focuses only on the remaining product architecture required to make ContentOps a complete multi-platform supervised live publishing system.

The target is not a generic social scheduler, not a fully autonomous bot, not a browser-clicking AI agent, and not an unbounded “publish everything” pipeline. The target is a formal, evidence-grade, multi-platform publishing cockpit where Jim can generate or import content, inspect platform-specific previews, approve exact payloads, and dispatch to selected configured platforms through explicit live gates.

The final product should support:

1. LLM-assisted research, drafting, rewriting, SEO, platform adaptation, and review.
2. Exact per-platform payload previews before posting.
3. Human approval of exact payload hash, not vague intent.
4. Account/page/channel binding for each platform.
5. Credential handles and live credential hydration only inside approved live gates.
6. One-request supervised dispatch per platform attempt.
7. No auto-retry on initial live publishing path.
8. Duplicate suppression by idempotency key.
9. Kill switch and platform budget checks.
10. Redacted immutable audit events.
11. Manual fallback for every platform.
12. Platform-specific official-doc gates.
13. Separate capability states for API, browser-assisted lab, and manual-only.
14. No autonomous replies, DMs, scraping, scheduler behavior, or hidden background posting.

The correct mental model is:

```text
LLM writes and explains.
Deterministic validators inspect.
Jim approves exact payloads.
Platform adapter dispatches once after all gates.
Audit records what happened.
```

The system can become powerful and fast without becoming autonomous. “Fast” should mean “less manual assembly and safer one-click supervised publishing,” not “AI can decide and post by itself.”

---

## 1. Product Definition

### 1.1 Product Name

Working name:

**Capital Chronicle ContentOps Multi-Platform Supervised Publisher**

This is a capability track inside ContentOps V5. It should not be branded as a bot, scheduler, agent host, API console, or automation marketplace.

### 1.2 Final User Experience

A mature workflow should feel like this:

Jim opens ContentOps.

The Command Center shows:

* current live mode;
* global kill switch;
* available publishing lanes;
* blocked platform gates;
* current approval queue;
* latest audit events;
* exact next safe actions.

Jim creates or imports a content idea.

The AI Writer generates:

* long-form Substack draft;
* X short post and thread;
* Telegram channel version;
* LinkedIn profile/page version;
* Threads version;
* Facebook Page version;
* Instagram caption/media package;
* TikTok/YouTube short-video metadata package, if media exists;
* SEO title/subtitle/keywords;
* risk notes;
* citation and limitation preservation notes;
* platform fit warnings.

The Draft Inspector validates:

* no financial advice;
* no signal framing;
* no unsupported claims;
* citations and limitations preserved;
* no hidden artifact claims;
* no prohibited language;
* platform-specific constraints;
* media rights and media manifest;
* content lane eligibility.

The Platform Preview room renders exact payloads for each platform.

Jim selects platforms:

* X: selected or manual-only depending current gate.
* Telegram Channel: selected if channel gate pass.
* LinkedIn Profile or Page: selected if OAuth/scopes/role gate pass.
* Substack: manual export or future API/browser-assisted path depending gate.
* Threads/Instagram/Facebook Page: selected only after Meta official-doc and permission gates pass.
* TikTok/YouTube: selected only after media, app review, scope, visibility, and upload gates pass.

Jim clicks:

```text
Approve selected payloads
```

The approval ledger records exact payload hashes.

The outbox creates one dispatch candidate per platform.

Each platform row revalidates:

* payload hash still matches;
* destination binding still matches;
* credential handle still resolves;
* kill switch is off;
* live gate is cleared;
* request budget is available;
* audit sink is ready;
* no duplicate idempotency key has already succeeded;
* platform adapter version matches payload hash input;
* manual fallback exists.

Jim clicks:

```text
Dispatch selected approved payloads
```

Each platform adapter sends one bounded request or routes to manual/browser-assisted fallback based on the gate state.

The Evidence Vault records:

* approval ledger entry;
* outbox entry;
* live gate snapshot;
* dispatch attempt;
* platform response class;
* resulting public URL or manual fallback status;
* redacted audit event;
* no-secret proof;
* rollback/follow-up state.

The system never posts in the background. It never schedules without Jim. It never replies or DMs. It never scrapes metrics. It never lets LLM output bypass deterministic gates.

---

## 2. Product Modes

The UI must separate these modes clearly.

### 2.1 Global Modes

```yaml
global_modes:
  LOCAL_ONLY:
    meaning: no network, no credentials, no provider, no platform calls
  PROVIDER_GATE_PENDING:
    meaning: AI provider credentials are not hydrated
  PROVIDER_GATE_CLEARED:
    meaning: approved LLM provider call allowed within budget
  PLATFORM_PREVIEW_ONLY:
    meaning: payloads can be rendered but not posted
  MANUAL_EXPORT_ONLY:
    meaning: system produces copy/export package; Jim posts manually
  SUPERVISED_LIVE_GATE_PENDING:
    meaning: platform live gate exists but not cleared
  SUPERVISED_LIVE_GATE_CLEARED:
    meaning: selected platform can dispatch after approval
  LIVE_DISPATCH_ACTIVE:
    meaning: one approved dispatch attempt is currently executing
  LIVE_DISPATCH_BLOCKED:
    meaning: one or more required gates failed
  KILL_SWITCH_ACTIVE:
    meaning: all live dispatch disabled immediately
```

### 2.2 Platform Modes

Each platform must have independent states:

```yaml
platform_mode:
  unsupported
  docs_unverified
  preview_only
  manual_only
  browser_assisted_lab_only
  live_read_only_ready
  live_write_gate_pending
  live_write_gate_cleared
  live_dispatch_blocked
  live_dispatch_ready_after_approval
  live_dispatching
  dispatched
  manual_fallback_required
```

### 2.3 Credential Modes

```yaml
credential_mode:
  not_configured
  configured_symbolic
  env_presence_verified_redacted
  read_only_token_hydration_allowed
  write_token_hydration_allowed
  token_scope_verified
  token_scope_missing
  token_expired
  token_revoked
  credential_blocked
```

No UI surface should display token prefixes, suffixes, raw account IDs classified as sensitive, cookie values, browser session values, request headers, or raw response bodies.

---

## 3. Architecture Overview

The architecture should be built in layers. Each layer must have its own packet schema, tests, and audit output.

### 3.1 Layer 1 — Source and Content Input Layer

This plan ignores future Internal Alpha database mechanics, but the product still needs input lanes:

* local manual idea;
* pasted source note;
* manually provided official-source URL;
* operator-created research note;
* existing draft import;
* future artifact input placeholder;
* Telegram remote idea;
* optional future browser news capture, only if separately approved.

This layer must not claim factual authority by itself. Inputs are ideas or source candidates until validated.

### 3.2 Layer 2 — LLM Provider and Prompt Contract Layer

The LLM layer is responsible for:

* topic expansion;
* research question generation;
* draft generation;
* rewrite;
* platform variants;
* SEO title/subtitle/keywords;
* hook generation;
* content calendar suggestions;
* risk explanation;
* source-needed flags.

It is not responsible for:

* approval;
* dispatch;
* credential use;
* browser control;
* platform API calls;
* readiness claims;
* hiding caveats;
* deleting risk labels.

### 3.3 Layer 3 — Research and Grounding Layer

This layer is distinct from Capital Chronicle Internal Alpha. It should support public-source/current-event content where appropriate.

It must produce a `ResearchGroundingPacket`:

```yaml
research_grounding_packet:
  packet_id: string
  topic: string
  created_at: timestamp
  source_mode: manual | official_docs | web_search_future | operator_supplied
  source_refs: array
  official_source_refs: array
  non_official_source_refs: array
  freshness_status: current | stale | unknown
  citation_status: pass | warning | blocked
  copyright_status: pass | warning | blocked
  claim_boundary: educational | factual_summary | opinion | blocked
  no_signal_status: pass | blocked
  no_advice_status: pass | blocked
  source_needed: boolean
  allowed_for_drafting: boolean
  allowed_for_approval: boolean
  blocked_reasons: array
```

If live web search is integrated later, it must have official-doc grounding, request budgets, source allowlist policy, citation preservation, copyright-safe summarization, and no scraping.

### 3.4 Layer 4 — Editorial Workflow Layer

This layer converts input and grounding into:

* content idea packet;
* editorial brief;
* draft variant;
* platform variant;
* SEO packet;
* review packet.

Every draft remains review-only until platform preview and approval gates pass.

### 3.5 Layer 5 — Draft Inspector and Policy Gate

This layer validates:

* claim risk;
* no financial advice;
* no signal framing;
* no fake performance;
* no unsupported numeric claims;
* no hidden prediction framing;
* no platform policy obvious violations;
* citations preserved;
* limitations preserved;
* media rights status;
* AI disclosure if needed;
* platform constraints.

### 3.6 Layer 6 — Platform Preview Layer

This layer renders exact payloads:

* text;
* thread split;
* title/subtitle;
* captions;
* hashtags;
* link preview intent;
* media manifest;
* alt text;
* visibility class;
* reply/comment settings;
* platform adapter version;
* disclosure settings;
* destination binding;
* credential handle ID.

The preview layer must generate the payload hash that Jim approves.

### 3.7 Layer 7 — Approval Authority Layer

Approval must be exact, append-only, and revocation-aware.

The approval ledger must never be mutated in place. Revocation, expiration, edit invalidation, and dispatch result are separate append-only events.

### 3.8 Layer 8 — Dispatch Preparation Layer

The outbox should create one dispatch candidate per platform.

It revalidates all gates immediately before dispatch.

### 3.9 Layer 9 — Platform Adapter Layer

Each platform adapter has:

* official-doc snapshot;
* endpoint allowlist;
* method allowlist;
* host allowlist;
* credential requirement;
* permission requirement;
* account binding proof;
* payload schema;
* media schema;
* request budget;
* timeout;
* no auto-retry;
* response classifier;
* redaction rules;
* manual fallback.

### 3.10 Layer 10 — Evidence and Audit Layer

Every meaningful state transition becomes evidence:

* source packet;
* research packet;
* prompt packet;
* LLM output packet;
* draft packet;
* validation packet;
* preview packet;
* approval ledger event;
* outbox event;
* platform gate event;
* dispatch audit event;
* manual fallback event;
* final URL record;
* metrics record.

The Evidence Vault is not raw JSON by default. It should show human-readable evidence cards with raw packet drilldown available.

---

## 4. Phase 0 — Baseline Reconciliation and Repo Authority

### 4.1 Purpose

Before any new live-publishing build, Antigravity must verify the current repo baseline. Uploaded Project Sources are strategic context, but GitHub/local repo state is authority.

### 4.2 Required Work

Antigravity must:

1. Fetch latest `master`.
2. Confirm repo path.
3. Confirm branch.
4. Confirm local HEAD.
5. Confirm remote HEAD.
6. Confirm clean/dirty working tree.
7. Inspect current V5 app.
8. Inspect current live_contentops modules.
9. Inspect current docs/automation packets.
10. Produce a current-state map.

### 4.3 Files to Inspect

Minimum:

* `README.md`
* `docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md`
* `docs/CAPITAL_CHRONICLE_CONTENTOPS_V5_FINAL_MASTER_PLAN_AND_NORTH_STAR.md`
* `live_contentops/platform_universe_registry_v2.py`
* `live_contentops/primary_platform_payload_preview_contracts.py`
* `live_contentops/substack_newsletter_manual_export_contract.py`
* `live_contentops/cockpit_read_model_contract.py`
* `ui/contentops_v5/src/App.tsx`
* `ui/contentops_v5/src/state.ts`
* `ui/contentops_v5/src/types.ts`
* `ui/contentops_v5/src/data/cockpitReadModelPacket.ts`
* latest `docs/automation/**` task packets.

### 4.4 Deliverables

* `docs/automation/MULTI_PLATFORM_LIVE_MASTER_RECON/current_state_map.md`
* `docs/automation/MULTI_PLATFORM_LIVE_MASTER_RECON/capability_inventory.json`
* `docs/automation/MULTI_PLATFORM_LIVE_MASTER_RECON/next_task_sequence.md`

### 4.5 Acceptance

* No source edits except docs if task is recon-only.
* Exact starting and final HEAD reported.
* No live calls.
* No credential reads.
* Current blockers listed.
* Existing completed tasks not duplicated.
* Next task pointer generated.

---

## 5. Phase 1 — Official Platform Documentation Registry

### 5.1 Purpose

Before building or updating any platform adapter, ContentOps must know what the platform officially supports. This prevents coding from stale memory or assumptions.

### 5.2 Scope

Build a local registry:

```yaml
platform_docs_registry:
  platform_id: string
  docs_snapshot_id: string
  docs_checked_at: timestamp
  docs_source_type: official | repository_research | operator_supplied | unknown
  api_available: boolean
  api_write_available: boolean
  manual_publish_supported: boolean
  browser_assisted_supported: lab_only
  required_app_review: boolean
  required_oauth: boolean
  required_scopes: array
  required_account_roles: array
  supported_payloads: array
  media_upload_model: string
  rate_limit_notes: string
  paid_plan_notes: string
  restrictions: array
  unknowns: array
  re_ground_required_before_live: boolean
```

### 5.3 Platform Rows

Initial platform universe:

1. Telegram Remote Operator Inbox.
2. Telegram Channel Destination.
3. X Profile.
4. LinkedIn Member Profile.
5. LinkedIn Organization Page.
6. Substack Newsletter.
7. Threads Profile.
8. Instagram Professional Account.
9. Facebook Page.
10. TikTok Account.
11. YouTube Channel.

### 5.4 Official Docs Grounding Policy

Every platform task must begin with official-doc grounding if:

* the adapter touches a live endpoint;
* OAuth/scopes/permissions are involved;
* media upload is involved;
* response classification changes;
* error handling changes;
* app review or paid-plan assumptions are unclear;
* platform documentation is older than 30 days;
* platform behavior fails unexpectedly;
* Antigravity encounters an API error.

If official docs cannot be fetched, the task must stop before live write behavior and classify the platform as `docs_unverified`.

### 5.5 Deliverables

* `live_contentops/platform_docs_registry.py`
* `tests/test_platform_docs_registry.py`
* `docs/automation/PLATFORM_DOCS_REGISTRY_V1/platform_docs_registry_packet.json`
* UI binding to Publish Readiness Tower.

### 5.6 Acceptance

* Every platform has a docs state.
* Unknowns are explicit.
* No platform can become live-write eligible with `docs_unverified`.
* Official-doc refresh is a required step before each live platform gate.

---

## 6. Phase 2 — Credential Boundary and Hydration Gate

### 6.1 Purpose

Move from symbolic credential handles to formal live credential hydration, but only under explicit live/API/credential task approval.

### 6.2 Credential Philosophy

Credentials are runtime capability, not product content.

The system may know:

* credential handle ID;
* credential type;
* platform;
* required scopes;
* configured/not configured;
* hydrated/not hydrated;
* redaction status;
* expiration class;
* scope verification result.

The system must not expose:

* token value;
* token prefix/suffix;
* cookie values;
* browser session values;
* raw OAuth refresh token;
* raw account password;
* raw `.env` content;
* request headers;
* raw API response that may contain secrets.

### 6.3 Credential Objects

```yaml
credential_handle:
  credential_handle_id: string
  platform_id: string
  credential_kind: oauth_access_token | bot_token | page_access_token | refresh_token | browser_session_lab
  env_key_name: string
  configured_symbolic: boolean
  hydration_allowed: boolean
  live_task_id: string | null
  required_scopes: array
  verified_scopes: array
  missing_scopes: array
  redaction_policy_id: string
  token_value_stored: false
  token_value_logged: false
  raw_secret_exposed: false
  last_verified_at: timestamp | null
  status: not_configured | configured_symbolic | hydrated_for_task | scope_verified | blocked
```

### 6.4 Credential Hydration Rules

Credential hydration can happen only if:

1. Task explicitly says credential read is approved.
2. Platform and endpoint family are named.
3. Request budget is named.
4. Timeout is named.
5. Redaction proof is required.
6. Stop conditions are named.
7. No raw secret is printed.
8. No raw secret is committed.
9. No raw secret is screenshotted.
10. No secret fingerprint/hash/prefix/suffix is displayed.
11. Hydration ends when task ends unless persistent secure store is explicitly approved later.

### 6.5 Deliverables

* `live_contentops/credential_hydration_gate.py`
* `live_contentops/credential_redaction_policy.py`
* tests for secret-shaped strings failing closed;
* tests proving non-live modules cannot read env;
* tests proving credential values never enter audit packets;
* docs packet.

### 6.6 Acceptance

* General tests pass without env reads.
* Live credential tests require explicit flag.
* Attempted secret logging fails tests.
* UI shows credential readiness, not secret values.
* Browser runtime never reads `.env`.

---

## 7. Phase 3 — Account and Destination Binding

### 7.1 Purpose

Before any publish action, ContentOps must know exactly where it will post. One account per platform reduces risk but does not eliminate the need for explicit binding.

### 7.2 Destination Binding Object

```yaml
destination_binding:
  destination_binding_id: string
  platform_id: string
  destination_kind: profile | page | channel | organization | newsletter | business_account
  display_name_redacted: string
  handle_redacted: string
  platform_account_id_redacted: string
  operator_confirmed: boolean
  confirmation_method: local_ui | live_read_only_api | manual_screenshot_safe
  credential_handle_id: string
  permission_status: unverified | read_only_verified | write_permission_verified | blocked
  scope_status: unverified | pass | missing | blocked
  wrong_account_detection_status: pass | blocked
  last_verified_at: timestamp | null
  live_write_allowed: boolean
  blocked_reasons: array
```

### 7.3 Per-Platform Binding Requirements

Telegram Channel:

* bot identity proof;
* target channel ID or username proof;
* bot admin/write permission proof;
* no private DM route;
* no group/community automation route;
* one selected channel only initially.

X:

* authenticated user identity proof;
* account handle proof;
* write permission proof in the supervised browser profile;
* launch-era path does not require paid X API;
* browser/CDP post identity capture stores `https://x.com/<handle>/status/<id>`;
* no reply/thread continuation without stored parent `public_url` or `platform_publication_id`;
* no DM automation;
* no quote-post unless supported by current plan;
* live TASK_0087AD success reason: use the standard ContentOps profile at `A:\Capital Chronicle\operator-browser-profiles\contentops-social-main`, refuse Antigravity browser profiles, capture the visible status permalink, store it in the identity registry, then reply only to the stored parent URL;
* if CDP `9222` is occupied by Antigravity Chrome, use a free ContentOps Edge CDP port instead of attaching to the wrong browser.

LinkedIn Member:

* authenticated member proof;
* `w_member_social` availability;
* no comments/likes automation initially;
* text post first; media later.

LinkedIn Organization:

* organization URN proof;
* authenticated member page role proof;
* `w_organization_social` scope;
* text post first; media asset upload later.

Substack:

* publication identity/manual export binding;
* manual publish first;
* future API/browser-assisted lab only after official-doc verification.

Threads:

* profile binding;
* app/scopes official-doc verification;
* text post first if API supports;
* no replies/engagement automation.

Instagram:

* professional/business/creator account requirement verification;
* media container model verification;
* caption/media manifest binding;
* no Stories/Reels unless separately gated.

Facebook Page:

* Page identity proof;
* page access token proof;
* page role/task proof;
* text/link post first; media later.

TikTok:

* creator info query;
* app review/scope status;
* visibility options proof;
* video/photo constraints;
* private-mode restriction if unaudited.

YouTube:

* channel identity proof;
* OAuth scope proof;
* upload quota/audit state;
* privacyStatus default safe mode: private or unlisted for test;
* public publish only after explicit final gate.

### 7.4 Deliverables

* `live_contentops/destination_binding_registry.py`
* `tests/test_destination_binding_registry.py`
* `docs/automation/DESTINATION_BINDING_REGISTRY_V1/binding_packet.json`
* V5 Publish Readiness Tower rows.

### 7.5 Acceptance

* No platform live gate clears without binding.
* Binding hash uses non-secret stable fields.
* Wrong-account mismatch blocks dispatch.
* UI shows one configured destination per platform.
* Destination changes invalidate approvals.

---

## 8. Phase 4 — Approval Ledger and Payload Hash Lock

### 8.1 Purpose

This is the central safety layer. Jim approves an exact payload, not an idea, not an LLM response, not a draft object, and not a platform name.

### 8.2 Payload Hash Inputs

The payload hash must include:

* platform ID;
* destination binding ID;
* credential handle ID;
* adapter version;
* payload schema version;
* text;
* platform formatting;
* thread split;
* title/subtitle;
* caption;
* hashtags;
* media manifest hash;
* alt text;
* link preview class;
* visibility class;
* disclosure class;
* AI disclosure if applicable;
* content lane;
* policy snapshot ID;
* source/citation packet ID;
* guardrail result ID.

The hash must not include:

* raw credential;
* env var;
* secret path;
* raw provider response;
* raw browser session;
* raw cookie;
* sensitive local absolute path;
* raw account ID if classified sensitive.

### 8.3 Approval Channels

Supported approval channels:

1. Local dashboard button.
2. Telegram approval challenge.
3. Future mobile UI if built.

The local dashboard button is the primary approval path for early live publishing. Telegram approval is convenient but must remain challenge-bound.

### 8.4 Approval States

```yaml
approval_state:
  draft_review_only
  preview_ready
  approval_requested
  approved_for_outbox
  approved_for_supervised_live
  invalidated_by_edit
  invalidated_by_destination_change
  invalidated_by_credential_change
  invalidated_by_policy_change
  revoked
  expired
  dispatched
  manual_fallback_required
```

### 8.5 Deliverables

* `live_contentops/approval_ledger_payload_hash.py`
* append-only ledger writer;
* read-only ledger verifier;
* revocation/expiration contract;
* edit invalidation tests;
* destination-change invalidation tests;
* policy-snapshot invalidation tests;
* UI Approval Queue binding.

### 8.6 Acceptance

* No approval without exact payload hash.
* Any payload or destination change invalidates approval.
* Ledger is append-only.
* Revocation does not delete prior approval; it supersedes it.
* UI never shows “publish-ready” without approval and gate state.

---

## 9. Phase 5 — AI Provider Gate and Prompt Template System

### 9.1 Purpose

Build LLM integration as a bounded editorial service, not an execution engine.

### 9.2 Provider Modes

```yaml
provider_mode:
  disabled
  manual_external_llm
  approved_provider_read_write
  local_model
```

The default remains disabled. The first provider integration should be explicit, credential-scoped, redacted, and budgeted.

### 9.3 Prompt Template Families

Build prompt templates for:

1. Idea classification.
2. Grounded research question generation.
3. Source summary.
4. Research brief.
5. Long-form Substack draft.
6. X short post.
7. X thread.
8. Telegram channel post.
9. LinkedIn profile post.
10. LinkedIn page post.
11. Threads post.
12. Facebook Page post.
13. Instagram caption.
14. TikTok title/description/hashtags.
15. YouTube title/description/tags.
16. SEO title.
17. SEO subtitle.
18. Hook variants.
19. Rewrite for institutional tone.
20. Claim-risk explanation.
21. No-signal rewrite.
22. Platform fit critique.
23. Final operator review packet.

### 9.4 Prompt Contract Object

```yaml
prompt_contract:
  prompt_contract_id: string
  template_id: string
  version: string
  input_schema_id: string
  output_schema_id: string
  allowed_context_classes: array
  forbidden_context_classes: array
  secret_redaction_required: boolean
  source_citation_required: boolean
  limitations_required: boolean
  no_advice_required: true
  no_signal_required: true
  output_public_postable: false
  max_tokens: integer
  cost_budget_class: string
```

### 9.5 LLM Output Validation

Every provider response must pass deterministic validation before entering draft workflow.

Validation checks:

* JSON/schema validity where required;
* no hidden dispatch commands;
* no secret-shaped strings;
* no claims of approval;
* no “I posted” claims;
* no buy/sell/hold;
* no price targets;
* no false source IDs;
* no invented URLs;
* no unsupported numeric claims;
* citations preserved if input had citations;
* limitations preserved;
* platform target matches request.

### 9.6 Deliverables

* `live_contentops/ai_provider_gate.py`
* `live_contentops/prompt_template_registry.py`
* `live_contentops/llm_output_validator.py`
* tests with fake provider responses;
* redaction tests;
* prompt injection tests;
* UI AI Writer / SEO Lab binding.

### 9.7 Acceptance

* Provider disabled by default.
* Provider call requires explicit mode.
* Prompt templates cannot dispatch.
* LLM output cannot approve.
* LLM output cannot become public without deterministic validation and human approval.
* Provider logs redact prompts if they contain sensitive content.
* Cost/request budget recorded.

---

## 10. Phase 6 — Grounded Search and Research Workbench

### 10.1 Purpose

Build a research workflow that can support timely content before or alongside Internal Alpha data, while remaining citation-first and copyright-safe.

### 10.2 Grounding Modes

```yaml
grounding_mode:
  manual_sources_only
  official_sources_only
  approved_web_search
  approved_news_api_future
  blocked
```

### 10.3 Source Classes

```yaml
source_class:
  official_government
  central_bank
  exchange_or_regulator
  company_ir
  platform_official_docs
  reputable_news
  analyst_commentary
  social_post
  operator_note
  unknown
```

### 10.4 Source Policy

Official sources are preferred. News can be used as a hook, not as signal. Social posts are never authority unless the post itself is the object being discussed. Copyrighted articles should be summarized, not copied. Paywalled content should not be redistributed. Vendor/raw data should not be copied into public posts unless licensing allows.

### 10.5 Research Packet

```yaml
research_packet:
  research_packet_id: string
  topic: string
  source_refs: array
  source_classification: array
  freshness_status: current | stale | mixed | unknown
  official_source_available: boolean
  citation_requirements: array
  key_points: array
  limitations: array
  forbidden_claims: array
  safe_angles: array
  unsafe_angles: array
  ready_for_drafting: boolean
  blocked_reasons: array
```

### 10.6 Difficulty Handling

If research encounters difficulty:

* ambiguous fact;
* conflicting sources;
* paywalled source;
* stale source;
* platform policy uncertainty;
* macro data discrepancy;
* API docs discrepancy;
* source license uncertainty;

then Antigravity must stop the assumption chain and ground-search official docs or authoritative sources again. The result must be added to the research packet as a source-status event.

### 10.7 Deliverables

* `live_contentops/research_grounding_packet.py`
* `live_contentops/source_classification_policy.py`
* `live_contentops/research_packet_validator.py`
* V5 Grounded News Workbench;
* tests for official-source-first behavior;
* tests for source-needed blockers;
* tests for copyright-safe summarization.

### 10.8 Acceptance

* Drafts cannot cite unsupported facts.
* Current-event claims require source refs.
* No raw article copying.
* No market signal framing.
* Research uncertainty is visible in the UI.

---

## 11. Phase 7 — Editorial Workflow and Draft Inspector

### 11.1 Purpose

Create an editorial system that can produce high-quality content but still pass deterministic safety gates.

### 11.2 Editorial Objects

* `ContentIdea`
* `EditorialBrief`
* `DraftVariant`
* `SeoPacket`
* `PlatformVariantSet`
* `DraftInspectionReport`
* `OperatorReviewPacket`

### 11.3 Draft Inspector Checks

The Draft Inspector must evaluate:

* source completeness;
* citation completeness;
* limitation preservation;
* content lane;
* platform suitability;
* tone;
* SEO quality;
* title/hook quality;
* forbidden phrase scan;
* no advice;
* no signal;
* no fake data;
* no unsupported metric;
* no model-prediction claim;
* no broker/execution language;
* no guarantee;
* no autonomous publishing phrase.

### 11.4 SEO Packet

```yaml
seo_packet:
  seo_packet_id: string
  primary_keyword: string
  secondary_keywords: array
  search_intent: informational | educational | opinion | update
  title_candidates: array
  subtitle_candidates: array
  slug_candidates: array
  meta_description: string
  platform_hashtags: object
  readability_score: integer
  editorial_score: integer
  platform_fit_scores: object
  limitations_preserved: boolean
```

### 11.5 Deliverables

* `live_contentops/editorial_workflow.py`
* `live_contentops/draft_inspector.py`
* `live_contentops/seo_packet.py`
* V5 Writer Studio upgrade;
* V5 Draft Inspector room;
* tests for no-advice/no-signal;
* tests for citation/limitation preservation;
* tests for platform variants.

### 11.6 Acceptance

* Drafts are high quality but never auto-approved.
* SEO suggestions cannot remove limitations.
* Platform variants preserve safety constraints.
* The UI exposes why a draft is blocked or approval-ready.

---

## 12. Phase 8 — Platform Preview and Media Manifest

### 12.1 Purpose

The platform preview must represent the exact payload that will be approved and dispatched.

### 12.2 Payload Types

Supported payload classes:

* `text_post`
* `thread`
* `newsletter_issue`
* `link_post`
* `image_post`
* `multi_image_post`
* `short_video_post`
* `long_video_upload`
* `story_or_reel_future`
* `manual_export_package`

### 12.3 Media Manifest

```yaml
media_manifest:
  media_manifest_id: string
  media_items: array
  rights_status: owned | licensed | generated | unknown | blocked
  source_path_redacted: string
  checksum: string
  mime_type: string
  size_bytes: integer
  dimensions: string | null
  duration_sec: integer | null
  alt_text: string | null
  platform_constraints: object
  upload_ready: boolean
  blocked_reasons: array
```

### 12.4 Platform Preview Requirements

Each preview card must show:

* platform;
* destination;
* account binding;
* credential handle;
* payload hash;
* text;
* media;
* visibility;
* link preview;
* reply/comment settings;
* AI disclosure;
* paid partnership setting if relevant;
* official-doc gate;
* adapter version;
* approval state;
* dispatch eligibility;
* current blocker.

### 12.5 Deliverables

* `live_contentops/platform_preview_renderer.py`
* `live_contentops/media_manifest_policy.py`
* V5 Platform Payload Preview room;
* screenshot-safe preview cards;
* tests for hash invalidation;
* tests for media changes invalidating approval.

### 12.6 Acceptance

* Preview equals dispatch input.
* Any final transformation after approval is forbidden unless it invalidates approval.
* Media changes invalidate approval.
* Platform formatting is visible before approval.

---

## 13. Phase 9 — Dispatch Outbox, Idempotency, Kill Switch, and Audit

### 13.1 Purpose

Approval should not directly trigger platform calls. Approval creates eligibility. The outbox performs deterministic revalidation.

### 13.2 Outbox Object

```yaml
dispatch_outbox_entry:
  outbox_id: string
  platform_id: string
  destination_binding_id: string
  credential_handle_id: string
  approval_ledger_entry_id: string
  payload_hash: string
  idempotency_key: string
  request_budget: 1
  auto_retry_allowed: false
  status: candidate | blocked | ready | dispatching | dispatched | failed | manual_fallback_required
  created_at: timestamp
  last_revalidated_at: timestamp
  blocked_reasons: array
```

### 13.3 Kill Switch

Global kill switch:

* disables all live dispatch;
* does not disable previews;
* does not delete outbox;
* turns ready items into blocked-by-kill-switch;
* must be visible in Command Center.

Per-platform kill switch:

* disables selected platform only;
* records reason;
* records operator;
* records timestamp.

### 13.4 Idempotency

Idempotency must prevent duplicate posting:

* one idempotency key per platform/payload/destination/approval;
* successful dispatch locks key;
* retry requires manual creation of a new attempt with explicit reason;
* unknown result routes to manual reconciliation;
* no automatic retry.

### 13.5 Audit Event

```yaml
dispatch_audit_event:
  audit_event_id: string
  outbox_id: string
  platform_id: string
  destination_binding_id: string
  payload_hash: string
  request_budget_used: integer
  retry_count: 0
  endpoint_family: string
  method: string
  response_class: success | blocked | failed | permission_error | rate_limited | unknown
  public_url: string | null
  platform_object_id_redacted: string | null
  redaction_status: pass | blocked
  no_secret_output: true
  raw_request_persisted: false
  raw_response_persisted: false
  manual_fallback_status: none | required | completed
  audit_hash: string
```

### 13.6 Deliverables

* `live_contentops/dispatch_outbox.py`
* `live_contentops/idempotency_policy.py`
* `live_contentops/kill_switch_policy.py`
* `live_contentops/redacted_dispatch_audit.py`
* tests for duplicate suppression;
* tests for no retry;
* tests for kill switch;
* Evidence Vault integration.

### 13.7 Acceptance

* No dispatch without approval.
* No duplicate success.
* No retry by default.
* Audit required before and after dispatch.
* Failed/unknown state cannot silently retry.

---

## 14. Phase 10 — UI Integration: Publish Readiness Tower and Dispatch Cockpit

### 14.1 Purpose

The UI must make live status impossible to misunderstand.

### 14.2 Required Screens

Update:

1. Command Center.
2. Approval Queue + Dispatch Control.
3. Platform Payload Preview.
4. Publish Readiness Tower.
5. Evidence Vault.
6. Settings / Safety.
7. Manual Publish + Metrics.
8. AI Writer / SEO Lab.
9. Grounded News Workbench.
10. Media Studio.

### 14.3 Publish Readiness Tower Rows

Rows:

* Global Kill Switch.
* LLM Provider Gate.
* Research/Grounding Gate.
* Approval Ledger.
* Payload Hash.
* Outbox.
* Redacted Audit.
* Telegram Remote Operator Inbox.
* Telegram Channel Destination.
* X Profile.
* LinkedIn Member.
* LinkedIn Organization.
* Substack Newsletter.
* Threads.
* Instagram.
* Facebook Page.
* TikTok.
* YouTube.

Each row shows:

* current mode;
* official docs state;
* account binding;
* credential handle;
* permission proof;
* preview renderer;
* media support;
* approval ledger;
* outbox readiness;
* live adapter;
* last audit;
* next blocker;
* allowed now;
* forbidden now.

### 14.4 Dispatch Cockpit UX

No “Publish All” as default.

Instead:

1. Select payloads.
2. Review platform matrix.
3. Approve selected payload hashes.
4. Revalidate gates.
5. Select dispatch attempts.
6. Confirm one-request dispatch.
7. Show live progress.
8. Show audit result.
9. Show manual fallback where needed.

### 14.5 Deliverables

* V5 UI components:

  * `DispatchGateMatrix`
  * `PlatformLiveGateCard`
  * `CredentialHandleStatus`
  * `DestinationBindingCard`
  * `ApprovalHashPanel`
  * `OutboxQueuePanel`
  * `RedactedAuditTimeline`
  * `KillSwitchBanner`
  * `ManualFallbackPanel`
* Playwright screenshots.
* Vitest UI tests.
* Accessibility pass.

### 14.6 Acceptance

* No hidden live controls.
* Every live button is disabled unless gates pass.
* UI clearly separates preview/manual/live.
* Evidence cards are readable.
* No secrets in screenshot.

---

## 15. Phase 11 — Live Read-Only Gates

### 15.1 Purpose

Before any platform write action, prove identity, scopes, account binding, and permission state with read-only or harmless calls.

### 15.2 Live Read-Only Gate Template

Every live-read-only gate needs:

```yaml
live_read_only_gate:
  gate_id: string
  platform_id: string
  endpoint_family: string
  host_allowlist: array
  path_allowlist: array
  method_allowlist: array
  credential_handle_id: string
  request_budget: integer
  timeout_sec: integer
  redirect_policy: disabled_or_justified
  final_host_verification: boolean
  redaction_policy_id: string
  operator_go_required: boolean
  no_write_guarantee: boolean
  response_classification: object
  audit_event_id: string
```

### 15.3 Platforms

Telegram:

* `getMe` for bot identity.
* `getChat` or equivalent for channel proof.
* `getChatMember` if needed for permission/admin proof.
* No `sendMessage` in read-only gate.

X:

* OAuth identity proof.
* User lookup.
* Scope/token proof if available.
* API tier/spend gate.
* No create post.

LinkedIn:

* member identity proof.
* organization/page role proof.
* scope availability.
* no post creation.

Meta platforms:

* re-ground official docs;
* prove page/account/profile identity;
* prove scopes and roles;
* no post creation.

TikTok:

* creator info query.
* app review/scope status if available.
* no publish.

YouTube:

* channel identity proof.
* OAuth scope check.
* no upload.

### 15.4 Deliverables

* one module per platform read-only gate;
* one test suite per platform;
* live tests gated behind explicit operator flags;
* audit packet per read-only gate.

### 15.5 Acceptance

* No write endpoint called.
* Request budget respected.
* No retry.
* No raw secrets.
* Account binding updated only with redacted safe fields.
* Failure blocks live write.

---

## 16. Phase 12 — Platform Live Write Gates

This phase is platform-by-platform. Do not attempt all platforms in one task.

### 16.1 Telegram Channel Destination

#### Purpose

First live write candidate because the Bot API model is comparatively straightforward and the destination can be bound to one controlled channel.

#### Build Order

1. Official docs refresh.
2. Bot identity read-only proof.
3. Channel binding proof.
4. Permission proof.
5. Text-only `sendMessage` dry-run equivalent, if possible; otherwise mock.
6. First live supervised text post.
7. Photo post gate.
8. Rich formatting gate.
9. Error and fallback hardening.

#### Adapter Contract

```yaml
telegram_channel_adapter:
  endpoint: sendMessage | sendPhoto
  host: api.telegram.org
  method: POST
  request_budget: 1
  auto_retry: false
  destination: channel
  forbidden_destinations:
    - private_dm
    - arbitrary_group
    - unknown_chat
  response_success_fields:
    - ok
    - result.message_id
  audit_url_policy: channel_url_if_available_or_manual
```

#### Acceptance

* No DM route.
* No group spam route.
* One selected channel only.
* Text post first.
* Media later.
* Audit includes message ID redacted or safe.
* Unknown result requires manual reconciliation.

---

### 16.2 X Profile

#### Purpose

Support X posts if API access/cost is acceptable; otherwise keep X as manual-only with exact payload preview.

#### Build Order

1. Official docs refresh.
2. OAuth identity proof.
3. Scope proof.
4. API tier/spend/limit proof.
5. Text-only post gate.
6. Thread gate.
7. Media upload gate.
8. Quote-post disabled unless plan supports it.
9. Error/fallback hardening.

#### Adapter Contract

```yaml
x_post_adapter:
  endpoint: POST /2/tweets
  host: api.x.com
  method: POST
  auth: oauth_user_token
  request_budget: 1
  auto_retry: false
  payload_classes:
    - text_post
    - thread_future
    - media_future
  disabled_features_initially:
    - quote_post
    - dm
    - replies
    - likes
    - reposts
    - follows
```

#### Acceptance

* If API plan restriction blocks write, route to manual.
* No engagement automation.
* No DM automation.
* Thread posts must be sequential but each request requires explicit outbox modeling.
* Unknown partial thread result requires manual reconciliation.

---

### 16.3 LinkedIn Member Profile

#### Purpose

Publish thought-leadership posts to Jim’s member profile after OAuth and `w_member_social` gate.

#### Build Order

1. Official docs refresh.
2. OAuth/member identity proof.
3. Scope proof.
4. Text-only post adapter.
5. Image asset upload gate.
6. Video/document support later.
7. Error/fallback hardening.

#### Adapter Contract

```yaml
linkedin_member_adapter:
  endpoint: /rest/posts
  host: api.linkedin.com
  method: POST
  auth: oauth_member_token
  required_scope: w_member_social
  author: member_urn
  request_budget: 1
  auto_retry: false
  headers:
    - Linkedin-Version
    - X-Restli-Protocol-Version
  initial_payload: text_only
```

#### Acceptance

* No comments/likes automation.
* No organization posting through member adapter.
* Author URN must match binding.
* `201` plus post ID header/classified response required for success.
* Media upload is separate gate.

---

### 16.4 LinkedIn Organization Page

#### Purpose

Publish to an official company/page identity if roles/scopes allow.

#### Build Order

1. Official docs refresh.
2. Organization identity proof.
3. Authenticated member role proof.
4. `w_organization_social` proof.
5. Text-only post adapter.
6. Media asset upload later.
7. Error/fallback hardening.

#### Acceptance

* Organization URN must match binding.
* Role must be one of allowed roles per docs.
* Member profile token cannot silently switch to organization posting unless org gate passes.
* Page post and member post are separate destinations.

---

### 16.5 Substack Newsletter

#### Purpose

Substack should remain manual export first unless official API capability is verified and safe.

#### Build Order

1. Official docs/support refresh.
2. Manual export package hardening.
3. Browser-assisted lab feasibility review.
4. If no official API exists, keep manual-only.
5. If official API exists or becomes available, build read-only/account proof first.
6. Live write only after docs, credential, audit, and fallback gates.

#### Manual Export Package

```yaml
substack_manual_export:
  title: string
  subtitle: string
  markdown_body: string
  tags: array
  canonical_url: string | null
  seo_packet: object
  checklist: array
  payload_hash: string
  copy_button_safe: true
```

#### Browser-Assisted Lab

If used, it must be isolated:

* not default runtime;
* no raw cookie logging;
* no DOM dumps containing secrets;
* screenshot-safe only;
* Jim must be present;
* final browser compose content must be compared to approved payload before pressing publish;
* if UI changes or uncertainty appears, stop and manual publish.

#### Acceptance

* Manual export remains primary.
* Browser-assisted path is lab-only until proven.
* No hidden scheduler.
* No session/cookie audit leakage.

---

### 16.6 Threads

#### Purpose

Support short-form text publishing if Meta Threads official API capabilities and permissions are verified.

#### Build Order

1. Re-ground official Meta Threads docs.
2. Identify required app/scopes.
3. Bind Threads profile.
4. Prove identity read-only.
5. Text post adapter.
6. Media support later.
7. Error/fallback hardening.

#### Acceptance

* No cross-post assumption from Instagram unless docs confirm.
* No replies/engagement automation.
* No DM features.
* If official docs cannot be fetched or permissions unclear, route to manual/browser-assisted lab only.

---

### 16.7 Instagram

#### Purpose

Support image/video caption publishing when account type and media constraints are verified.

#### Build Order

1. Re-ground official Instagram Graph/API docs.
2. Verify business/creator/professional account requirement.
3. Verify Facebook Page/IG account linkage if required.
4. Build media container preview.
5. Build media publish gate.
6. Add caption/hashtag rules.
7. Reels/Stories later.

#### Acceptance

* Text-only Instagram post is not assumed.
* Media is required if docs require.
* Media URL/domain requirements must be verified.
* No scraping/manual browser upload as default runtime.
* Comment/reply automation forbidden.

---

### 16.8 Facebook Page

#### Purpose

Support official Facebook Page publishing, not personal profile automation.

#### Build Order

1. Re-ground official Meta Pages docs.
2. Page identity proof.
3. Page access token proof.
4. Page role/task proof.
5. Text/link post adapter.
6. Photo/video support later.
7. Error/fallback hardening.

#### Acceptance

* Personal profile posting not supported unless official docs and permissions explicitly allow, which should not be assumed.
* Page ID must match binding.
* Page token must match page.
* No group posting.
* No comment/DM automation.

---

### 16.9 TikTok

#### Purpose

Support TikTok direct posting only after app review/scope/visibility constraints are proven. Treat as later-stage.

#### Build Order

1. Official docs refresh.
2. App registration proof.
3. Content Posting API product proof.
4. Direct Post config proof.
5. Scope approval proof.
6. User authorization proof.
7. Creator info query.
8. Private test post if unaudited.
9. Public visibility only after audit/compliance.
10. Video/photo upload gate.

#### Acceptance

* No public TikTok post from unaudited client if platform restricts visibility.
* Creator info must be queried before posting.
* Media constraints must pass before approval.
* Visibility options must be displayed to Jim.
* TikTok remains late-stage because review/scope/media constraints are heavier.

---

### 16.10 YouTube

#### Purpose

Support video upload only after media pipeline, OAuth, quota, and audit constraints are ready.

#### Build Order

1. Official docs refresh.
2. OAuth client setup proof.
3. Channel identity proof.
4. `youtube.upload` scope proof.
5. Private/unlisted upload pilot.
6. Metadata validation.
7. Thumbnail gate.
8. Public publish only after explicit production gate.

#### Acceptance

* Test uploads default to private or unlisted.
* Public upload requires explicit final gate.
* Video file must pass media manifest.
* Quota use recorded.
* Unverified project restrictions must be visible.

---

## 17. Phase 13 — Browser-Assisted Publishing Lab

### 17.1 Purpose

Browser-assisted publishing may be useful when APIs are unavailable, expensive, restricted, or not worth implementing. But it must be isolated from the formal adapter path until it proves stable.

### 17.2 Allowed Uses

* manual-assist compose;
* final preview comparison;
* paste approved payload into UI;
* screenshot-safe verification;
* manual click with Jim present;
* experimental lab for platform feasibility.

### 17.3 Forbidden Uses

* autonomous background browser publishing;
* cookie/session dumps;
* raw DOM dumps;
* password handling;
* 2FA handling by AI;
* bypassing approval ledger;
* bypassing payload hash;
* clicking publish when UI target is uncertain;
* handling DMs/replies/comments;
* mass posting;
* scheduler behavior.

### 17.4 Browser Lab Safety Contract

```yaml
browser_assisted_publish_lab:
  platform_id: string
  chrome_profile_id: string
  session_class: operator_logged_in
  payload_hash_required: true
  pre_click_compare_required: true
  jim_present_required: true
  screenshot_safe: true
  dom_dump_allowed: false
  cookie_read_allowed: false
  credential_read_allowed: false
  auto_publish_allowed: false
  stop_on_ui_uncertainty: true
```

### 17.5 Acceptance

* Browser lab cannot mark platform as formal live-ready.
* Browser lab can complete manual fallback.
* Browser lab evidence must avoid secrets.
* Any uncertainty stops the run.

---

## 18. Phase 14 — Metrics and Performance Capture

### 18.1 Purpose

Record what happened after publishing without scraping or engagement automation.

### 18.2 Initial Mode

Manual metrics entry:

* URL;
* posted timestamp;
* platform;
* account/page/channel;
* impressions;
* likes;
* comments;
* shares/reposts;
* saves;
* newsletter opens/clicks if manually available;
* notes.

### 18.3 Future Read-Only Metrics API

Only after platform-specific read-only gates:

* X analytics if available and permitted.
* LinkedIn post stats if API/scope allows.
* Meta insights if page/account scope allows.
* TikTok/YouTube analytics later.
* Substack manual or official export.

### 18.4 Acceptance

* No scraping.
* No browser metrics scraping.
* No automated engagement.
* Metrics are clearly manual/API-derived.
* Missing metrics remain missing.

---

## 19. Phase 15 — Testing and Red-Team Harness

### 19.1 Test Families

1. No secret output tests.
2. No credential read in non-live modules.
3. No network in local tests.
4. Payload hash stability tests.
5. Approval invalidation tests.
6. Revocation tests.
7. Expiration tests.
8. Destination mismatch tests.
9. Wrong account tests.
10. Kill switch tests.
11. Duplicate suppression tests.
12. No auto-retry tests.
13. Provider output schema tests.
14. Prompt injection tests.
15. Platform docs stale-state tests.
16. API error classifier tests.
17. Manual fallback tests.
18. Browser lab stop-condition tests.
19. UI blocked-state tests.
20. Screenshot no-secret tests.

### 19.2 Red-Team Cases

* LLM says “approved.”
* LLM says “posted successfully.”
* Jim edits text after approval.
* Destination changes after approval.
* Credential handle changes after approval.
* Token appears in exception string.
* API returns success but missing ID.
* API timeout after possible post.
* Duplicate outbox attempt.
* Platform returns rate limit.
* Browser UI changed.
* Platform docs stale.
* Wrong LinkedIn author URN.
* Wrong Telegram chat ID.
* TikTok unaudited public visibility attempted.
* YouTube public upload attempted in test mode.
* Meta page token mismatched.
* X quote-post attempted without plan support.

### 19.3 Acceptance

A platform cannot graduate to live-ready unless its red-team cases pass.

---

## 20. Phase 16 — Final Multi-Platform Release Criteria

The product reaches “multi-platform live complete” only when:

1. V5 UI shows every platform state accurately.
2. LLM provider gate is explicit and redacted.
3. Research/grounding packets exist.
4. Draft Inspector blocks unsafe content.
5. Platform previews are exact.
6. Approval ledger is append-only.
7. Payload hashes include destination and adapter version.
8. Outbox revalidates immediately before dispatch.
9. Kill switch works globally and per platform.
10. Credential hydration is scoped and redacted.
11. Each platform has official-doc registry.
12. Each platform has account binding.
13. Each platform has read-only identity/permission proof.
14. Each live platform has one-request adapter.
15. No auto retry exists by default.
16. Duplicate suppression works.
17. Redacted audit exists.
18. Manual fallback exists.
19. Metrics capture exists.
20. Screenshots have been inspected.
21. No platform claims live-ready while blockers exist.
22. No autonomous replies/DMs/scheduler/scraping.
23. Every live task evidence packet includes endpoint allowlist, method, host/path, request budget, timeout, redirect policy, credential redaction proof, no retry proof, audit proof, manual fallback, and rollback plan.

---

## 21. Recommended Heavy Prompt Sequence

This roadmap should be implemented as heavy batched prompts, not micro-tasks.

### Batch 1 — Current Repo and Live Roadmap Reconciliation

Goal:
Create current-state map and reconcile existing repo modules with this master plan.

Output:
No code or minimal docs only.

### Batch 2 — Platform Docs Registry and Capability Matrix

Goal:
Build official-doc registry and Publish Readiness Tower platform rows.

### Batch 3 — Credential Hydration Gate and Redaction Policy

Goal:
Build explicit credential gate, redaction, env-read boundaries, and tests.

### Batch 4 — Destination Binding Registry

Goal:
Create account/page/channel binding model for every platform.

### Batch 5 — Approval Ledger and Payload Hash Upgrade

Goal:
Ensure exact payload approval and invalidation.

### Batch 6 — Dispatch Outbox, Idempotency, Kill Switch, Audit

Goal:
Build deterministic dispatch preparation layer.

### Batch 7 — AI Provider Gate and Prompt Template Registry

Goal:
Enable bounded AI writing/SEO without authority leakage.

### Batch 8 — Research/Grounding Workbench

Goal:
Support grounded current-event/source-cited content independent of Internal Alpha.

### Batch 9 — Editorial Workflow and Draft Inspector

Goal:
Create safe draft generation, review, SEO, and variant workflow.

### Batch 10 — Platform Preview and Media Manifest

Goal:
Exact payload previews and media constraints for all platforms.

### Batch 11 — V5 UI Binding and Browser QA

Goal:
Make the cockpit usable, credible, and screenshot-worthy.

### Batch 12 — Telegram Read-Only and First Live Pilot

Goal:
Telegram channel first supervised live text post.

### Batch 13 — X Gate

Goal:
Either live X adapter if API access/cost is acceptable, or formal manual-only path.

### Batch 14 — LinkedIn Member Gate

Goal:
Supervised LinkedIn profile post.

### Batch 15 — LinkedIn Organization Gate

Goal:
Supervised LinkedIn page post.

### Batch 16 — Substack Manual/Assisted Gate

Goal:
Manual export hardened; browser/API only if official path is verified.

### Batch 17 — Meta Docs Reground + Facebook/Instagram/Threads Capability Gates

Goal:
Build Meta capability matrix and first safe destination.

### Batch 18 — TikTok Gate

Goal:
Late-stage media direct post gate after scope/app review proof.

### Batch 19 — YouTube Gate

Goal:
Private/unlisted video upload pilot, public later.

### Batch 20 — Metrics and Performance Capture

Goal:
Manual metrics first, API read-only later.

### Batch 21 — Multi-Platform Dispatch Orchestration

Goal:
One approved campaign creates separate outbox entries and dispatches only selected eligible platforms.

### Batch 22 — Full Red-Team and Visual QA

Goal:
Run all safety, UI, live-gate, and evidence tests.

### Batch 23 — Production Readiness Review

Goal:
Final release decision: which platforms are live, manual, lab, or blocked.

---

## 22. Difficulty Handling Rule

In every phase, if Antigravity encounters:

* unclear platform permission;
* API error not covered by docs;
* OAuth scope mismatch;
* changed API endpoint;
* app review uncertainty;
* media upload failure;
* rate limit ambiguity;
* paid plan restriction;
* browser UI mismatch;
* official docs unavailable;
* credential policy ambiguity;
* response shape mismatch;
* platform object ID uncertainty;

then it must:

1. Stop assumptions.
2. Ground-search official docs again.
3. Compare docs to current implementation.
4. Patch only within approved scope.
5. Update docs registry.
6. Add regression test.
7. Record caveat if unresolved.
8. Keep platform blocked if unresolved.

No platform should be force-passed based on memory, LLM confidence, or observed one-off behavior.

---

## 23. Final Product Definition

The final product is complete when ContentOps can do this safely:

```text
Generate / import / research content
→ create platform variants
→ inspect claims / citations / SEO / media
→ render exact platform payloads
→ bind exact destination accounts
→ approve exact payload hashes
→ create per-platform outbox entries
→ revalidate platform gates
→ dispatch selected platforms once
→ record public URLs or fallback states
→ preserve redacted immutable audit
→ collect manual or approved read-only metrics
```

It is not complete merely because it can post once.

It is complete when posting is:

* repeatable;
* gated;
* reviewable;
* auditable;
* platform-specific;
* revocable before dispatch;
* fail-closed;
* manually recoverable;
* visually understandable;
* free of secret exposure;
* free of autonomous behavior.

That is the north-star version of multi-platform live publishing for Capital Chronicle ContentOps.
