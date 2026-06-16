# Capital Chronicle ContentOps — Supervised Remote Operator Loop Master Plan After 0174EC

## 0. Executive Decision

After `TASK_CONTENTOPS_0174EC_CREDENTIAL_HANDLE_AND_REDACTION_BOUNDARY_V0`, Capital Chronicle ContentOps should move from credential-safety foundation into the **approval-and-dispatch authority layer**, then into a **Telegram-based Remote Operator Loop** with a bounded local LLM intake/editorial agent.

The correct next architecture is not:

* an autonomous publishing bot;
* OpenClaw runtime integration;
* a Telegram command bot that can publish by itself;
* a generic agent that can run shell/files/browser/platform tools;
* a social scheduler;
* a live API console;
* a credential dashboard.

The correct architecture is:

**A local-first supervised publishing cockpit with a remote Telegram operator surface, where LLMs may understand/edit/draft but may not authorize, mutate approval state, select hidden accounts, hydrate credentials, or dispatch content.**

The final product may support supervised one-click publishing later, including remote approval via Telegram, but only after the system has:

1. An approval ledger.
2. Payload hash locking.
3. Account binding.
4. Credential handle/redaction boundary.
5. Kill switch.
6. Dispatch outbox.
7. Idempotency.
8. Platform permission proof.
9. One-request/no-auto-retry dispatch.
10. Redacted immutable audit.
11. Operator identity proof.
12. Expiring approval challenges.
13. Exact platform/account/payload/visibility binding.
14. No autonomous replies, DMs, scraping, or scheduling.

The next core task remains:

`TASK_CONTENTOPS_0174ED_APPROVAL_LEDGER_AND_PAYLOAD_HASH_CONTRACT_V0`

OpenClaw research does not change the runtime roadmap. OpenClaw remains reference-only / anti-pattern reference. The runtime should be ContentOps-native.

---

## 1. Current Accepted Capability Baseline

### 1.1 Established Automation-Core Stack

The project has now established several important safety primitives:

#### 0174EA — Social Automation Research + Architecture Context

The project clarified that automation is the long-term build path, but only as supervised automation. Manual posting is fallback. Autonomous posting is forbidden.

0174EA established the reference posture:

* supervised publishing, not autonomous posting;
* platform APIs only after explicit future gates;
* official platform constraints matter;
* no posting before account binding, approval, kill switch, redaction, audit, and budget checks;
* open-source social automation systems are useful as research references, not as drop-in runtime authority.

#### 0174DE_R1 — X OAuth Live Read-Only Identity Proof Hardening

The project accepted a tightly scoped X identity proof gate with:

* read-only endpoint only;
* exact host/path/scheme checks;
* redirect following disabled;
* final host re-verification;
* one request budget;
* no auto retry;
* token never persisted/logged/hashed;
* operator GO and execution flag both required.

This proves the project can support a tiny live-read-only validation gate if and only if the gate is explicit, bounded, redacted, and fail-closed.

#### 0174EB — Social Account Binding Model + Fake Provider Contract

The project accepted a platform-agnostic account binding model with:

* supported platform profiles;
* deterministic binding IDs from non-secret fields;
* fake provider results;
* wrong-account fail-closed behavior;
* destination mismatch blockers;
* missing-scope blockers;
* docs/audit/spend/rate blockers;
* no live write;
* no autonomous posting;
* no credential reads;
* no network.

This establishes the foundation for proving that a future post will go to the exact intended destination.

#### 0174EC — Credential Handle + Redaction Boundary

The project accepted the symbolic credential handle boundary.

0174EC established:

* credential handles are symbolic only;
* no credential value is stored, printed, hashed, fingerprinted, prefixed, suffixed, or exposed;
* no env / `.env` / keyring / browser session / credential file read by default;
* no live hydration now;
* fake credential provider results only;
* `configured_symbolic` is not live-ready;
* operator GO cannot unlock credential hydration in this layer;
* forbidden credential-shaped material fails closed.

This is the most important precondition for any future remote publishing loop.

#### 0174EF — OpenClaw Research Decision Pack

0174EF concluded that OpenClaw is not a runtime fit for ContentOps.

OpenClaw is acceptable only as:

* reference architecture;
* anti-pattern reference;
* optional isolated lab topic;
* source of future red-team negative cases.

OpenClaw is rejected as:

* runtime dependency;
* sidecar;
* installed component;
* skill runner;
* gateway;
* Telegram command layer;
* publishing automation runtime.

### 1.2 Current Baseline Meaning

The repo is now ready to build the authority layer that binds:

* human intent;
* exact content;
* exact platform;
* exact account/channel/page;
* exact media set;
* exact payload hash;
* exact approval;
* exact dispatch attempt;
* exact redacted audit record.

The repo is not ready to build live publishing yet.

The repo is not ready to let Telegram commands trigger posting.

The repo is not ready to let an LLM decide whether a post should be sent.

The repo is ready to build the deterministic model that makes those future things safe.

---

## 2. New Product Target

## 2.1 Product Name

Use the working architecture name:

**ContentOps Remote Operator Loop**

This is not a separate product. It is a capability track inside Capital Chronicle ContentOps.

## 2.2 Product Definition

ContentOps Remote Operator Loop is a local-first supervised workflow where Jim can:

1. Send ideas from Telegram while away from the machine.
2. Have a local LLM intake/editorial agent understand the natural language idea.
3. Convert the idea into a structured content brief.
4. Route the brief through ContentOps content-lane and safety gates.
5. Generate drafts and platform variants.
6. Receive previews back in Telegram.
7. Ask for revisions in natural language.
8. Approve a final exact payload hash.
9. Let the local machine perform one deterministic, audited dispatch only after all gates pass.

The key principle:

**The LLM may understand and write. The deterministic gate may post. The LLM may not post.**

## 2.3 Final User Experience

A mature version should support this flow:

Jim is outside and sends Telegram:

> Idea: write a LinkedIn post about why one CPI print is not enough to call a macro regime shift. Tone institutional, concise, no trading angle. Also make an X thread version.

Local ContentOps receives it and creates:

* inbound idea packet;
* source channel metadata;
* sender identity proof;
* content intent;
* content lane;
* claim-risk classification;
* source-needed status;
* draft request;
* editorial constraints.

Local LLM editorial agent drafts:

* LinkedIn post preview;
* X thread preview;
* caveats;
* no-advice/no-signal scan result;
* source-needed flags;
* platform fit notes.

Telegram bot sends back:

* draft preview;
* platform preview;
* blocked/caution notes;
* exact payload hash;
* target platform/account placeholders;
* approval options.

Jim replies naturally:

> LinkedIn is good. Approve LinkedIn. X hook is too dramatic; rewrite the first tweet to be calmer.

Local ContentOps parses this as:

* LinkedIn approval candidate for exact hash;
* X revision request;
* no X approval yet.

If LinkedIn payload hash, account binding, credential handle, kill switch, platform gate, and audit gate all pass, ContentOps may create a dispatch-ready outbox entry.

The dispatcher then sends once, records result class, and stores redacted audit.

If content changes after approval, the approval is invalidated.

---

## 3. Non-Negotiable Principles

## 3.1 LLM Is Not Authority

LLM output is advisory.

The LLM can:

* classify intent;
* classify content lane;
* propose content;
* rewrite content;
* generate variants;
* summarize source-provided context;
* propose SEO/social hooks;
* explain risk;
* ask clarifying questions.

The LLM cannot:

* approve content;
* publish content;
* choose hidden accounts;
* hydrate credentials;
* bypass approval ledger;
* override kill switch;
* override account binding;
* suppress caveats;
* mark a blocked item as pass;
* retry failed dispatch;
* mutate audit logs;
* treat memory as authority.

## 3.2 Telegram Is Not Authority

Telegram is an operator interface and message transport.

Telegram can:

* carry Jim’s ideas;
* carry Jim’s edit instructions;
* carry Jim’s approval challenge responses;
* notify Jim of blockers;
* return previews;
* return audit summaries.

Telegram cannot:

* bypass local approval ledger;
* cause direct posting by itself;
* authorize a post without exact payload hash;
* authorize an account/channel/page change without new challenge;
* approve changed content;
* approve hidden media attachment changes;
* override kill switch;
* serve as a secret store.

## 3.3 Approval Means Exact Hash, Not General Intent

A valid approval must bind:

* operator identity;
* timestamp;
* approval challenge ID;
* platform;
* account binding ID;
* destination kind;
* payload hash;
* media manifest hash;
* credential handle ID;
* visibility class;
* dispatch intent;
* expiration;
* approval text / response;
* policy snapshot;
* gate snapshot.

A reply like “looks good” is not enough unless it is mapped to a structured approval challenge and the hash still matches.

## 3.4 Any Edit Invalidates Prior Approval

If any of the following changes after approval, the approval is invalid:

* post text;
* thread split;
* URL;
* media file;
* media order;
* alt text;
* target platform;
* target account/channel/page;
* visibility;
* scheduled/immediate dispatch class;
* payload metadata;
* disclosure field;
* link preview class;
* platform-specific formatting.

The system must require a new approval.

## 3.5 Dispatch Is Deterministic

Dispatch is not an LLM tool.

Dispatch must be a deterministic module with:

* exact platform adapter;
* exact request budget;
* no auto retry;
* idempotency key;
* account binding proof;
* credential handle proof;
* kill switch pass;
* approval hash pass;
* redacted request/response audit;
* fail-closed errors;
* manual fallback.

## 3.6 No OpenClaw Runtime

OpenClaw must not be used for:

* Telegram gateway;
* skill execution;
* memory;
* posting;
* agent runtime;
* local control plane;
* dispatcher;
* sidecar;
* plugin registry.

The project may borrow conceptual lessons only.

---

## 4. Architecture Overview

## 4.1 Layered System

The new track should use seven layers:

1. **Remote Ingress Layer**

   * Telegram inbound messages.
   * Sender verification.
   * Anti-replay.
   * Raw message capture with redaction.
   * No command execution.

2. **Intent Interpretation Layer**

   * LLM or deterministic parser.
   * Converts natural language into structured intent.
   * Produces uncertainty labels.
   * Cannot mutate approval or dispatch state.

3. **Editorial Workflow Layer**

   * Content brief.
   * Draft generation.
   * Revision handling.
   * Platform variants.
   * Claim-risk and content-lane checks.
   * Review packet.

4. **Approval Authority Layer**

   * Approval ledger.
   * Payload hash.
   * Challenge/response.
   * Expiration.
   * Revocation.
   * Edit invalidation.

5. **Dispatch Preparation Layer**

   * Account binding.
   * Credential handle.
   * Platform capability.
   * Kill switch.
   * Rate/spend budget.
   * Idempotency.
   * Outbox.

6. **Supervised Dispatch Layer**

   * One platform adapter.
   * One bounded request.
   * No auto-retry.
   * Redacted response classification.
   * Manual fallback.

7. **Evidence and Audit Layer**

   * Redacted immutable audit.
   * Evidence Vault.
   * Git/task provenance.
   * Operator timeline.
   * Caveat registry.

## 4.2 Conceptual Flow

```text
Telegram Message From Jim
  ↓
Remote Inbound Packet
  ↓
Sender/Session/Replay Check
  ↓
LLM Intent Parser
  ↓
Structured Intent Packet
  ↓
Content Lane + Risk Gate
  ↓
Draft / Revision / Platform Preview
  ↓
Payload Hash Manifest
  ↓
Telegram Review Challenge
  ↓
Jim Approval Response
  ↓
Approval Ledger Entry
  ↓
Outbox Entry
  ↓
Dispatch Gate Matrix
  ↓
One-Request Platform Dispatch
  ↓
Redacted Audit Event
  ↓
Telegram Result Notification
```

## 4.3 Authority Split

| Component        | May Understand Natural Language | May Write Drafts |                  May Approve |              May Dispatch |                    May Read Credentials |
| ---------------- | ------------------------------: | ---------------: | ---------------------------: | ------------------------: | --------------------------------------: |
| Telegram bot     |                              No |               No | No, only transports response |                        No |                                      No |
| LLM Intake Agent |                             Yes |            Maybe |                           No |                        No |                                      No |
| Editorial Agent  |                             Yes |              Yes |                           No |                        No |                                      No |
| Approval Ledger  |                              No |               No |        Records approval only |                        No |                                      No |
| Dispatch Gate    |                              No |               No |              Checks approval |   No direct platform call |                  No raw read by default |
| Platform Adapter |                              No |               No |                           No | Yes, only after all gates | Only via future approved hydration gate |
| Audit Layer      |                              No |               No |                           No |                        No |                                      No |

---

## 5. Core Objects

## 5.1 RemoteInboundMessage

Represents a Telegram message from Jim.

Required fields:

```yaml
remote_inbound_message:
  message_id: string
  transport: telegram
  received_at: timestamp
  sender_class: verified_operator | unknown | blocked
  sender_binding_id: string
  chat_binding_id: string
  raw_text_redacted: string
  attachment_manifest: array
  reply_to_message_id: string | null
  transport_message_hash: string
  redaction_status: pass | blocked
  replay_status: fresh | duplicate | stale
  trust_status: untrusted_input
  allowed_use:
    - intent_parsing
    - idea_capture
    - review_response_candidate
  forbidden_use:
    - direct_dispatch
    - credential_access
    - approval_without_challenge
```

Rules:

* Treat every Telegram message as untrusted input even if sender is Jim.
* Sender verification proves source, not semantic safety.
* Raw message may be stored only after redaction.
* Attachments require a separate attachment safety policy.

## 5.2 IntentPacket

Represents the structured output of the LLM intent parser.

Required fields:

```yaml
intent_packet:
  intent_id: string
  source_message_id: string
  parsed_at: timestamp
  parser_type: deterministic | llm_assisted
  parser_model_class: disabled | local | approved_provider_future
  intent_class:
    - create_content_from_idea
    - revise_draft
    - approve_candidate
    - reject_candidate
    - hold_candidate
    - ask_status
    - request_preview
    - request_sources
    - unknown
  confidence_class: high | medium | low | ambiguous
  extracted_platform_targets: array
  extracted_content_lane: string
  extracted_topic: string
  extracted_tone: string
  extracted_constraints: array
  extracted_forbidden_risk_flags: array
  requires_clarification: boolean
  clarification_question: string | null
  can_create_content_brief: boolean
  can_create_approval: false
  can_dispatch: false
  blocked_reasons: array
  evidence_refs: array
```

Rules:

* LLM intent output cannot directly approve.
* If ambiguous, ask Jim for clarification.
* If approval-like language is detected, it must route to approval challenge validation.
* If message includes trading/signal language, route to blocked or transform-to-educational review.

## 5.3 ContentIdeaPacket

Represents a safe local idea record.

Required fields:

```yaml
content_idea_packet:
  idea_id: string
  source: telegram | local_ui | manual_import
  created_at: timestamp
  author_class: jim_operator
  original_message_ref: string
  topic_summary: string
  intended_content_lane: pre_alpha_general_process | grounded_news_context | future_artifact_backed | unknown
  source_requirement_status: not_required | source_needed | source_provided | blocked
  market_sensitivity: none | educational_macro | current_event | high_risk
  no_signal_constraint: true
  no_advice_constraint: true
  artifact_backed_claims_allowed: false unless future gate
  status: captured | needs_clarification | ready_for_brief | blocked
  blocked_reasons: array
```

Rules:

* Ideas are not facts.
* Ideas are not sources.
* Ideas are not approvals.
* Ideas are not public-ready content.
* Ideas only begin a local workflow.

## 5.4 EditorialBrief

Represents the structured input for drafting.

Required fields:

```yaml
editorial_brief:
  brief_id: string
  idea_id: string
  content_lane: string
  target_platforms: array
  audience_mode: string
  tone_mode: string
  source_requirements: array
  required_limitations: array
  forbidden_claims: array
  no_financial_advice: true
  no_signal_language: true
  artifact_backed_allowed: false unless artifact intake gate
  output_status: review_only
```

Rules:

* Brief may request a draft.
* Brief cannot mark anything publish-ready.
* Brief must preserve limitations.

## 5.5 DraftVariant

Represents a generated or revised draft.

Required fields:

```yaml
draft_variant:
  draft_id: string
  brief_id: string
  platform: linkedin | x | telegram | substack | threads | etc
  body: string
  body_hash: string
  platform_fit_status: pass | warning | blocked
  citation_status: not_required | needed | present | incomplete
  forbidden_language_status: pass | blocked
  no_signal_status: pass | blocked
  no_advice_status: pass | blocked
  limitations_preserved: boolean
  human_review_required: true
  public_postable: false
  approval_status: not_approved
```

Rules:

* Draft is always review-only before approval.
* If source-needed, cannot become approval-ready until source/caveat policy passes.
* If platform-specific version changes, it gets a new hash.

## 5.6 PlatformPayloadPreview

Represents exact per-platform payload before approval.

Required fields:

```yaml
platform_payload_preview:
  payload_id: string
  draft_id: string
  platform: string
  destination_binding_id: string
  credential_handle_id: string
  payload_text: string
  media_manifest_id: string | null
  visibility_class: string
  platform_constraints_status: pass | warning | blocked
  payload_hash: string
  payload_hash_algorithm: sha256
  payload_hash_inputs:
    - platform
    - destination_binding_id
    - credential_handle_id
    - payload_text
    - media_manifest_hash
    - visibility_class
    - disclosure_class
    - platform_formatting
  approval_required: true
  dispatch_ready: false
```

Rules:

* Payload hash is the central approval target.
* Payload hash must include account binding and credential handle ID, not raw credentials.
* Any payload change generates a new hash.

## 5.7 ApprovalChallenge

Represents a Telegram or UI approval request.

Required fields:

```yaml
approval_challenge:
  challenge_id: string
  created_at: timestamp
  expires_at: timestamp
  operator_id: jim
  channel: telegram | local_ui
  payload_id: string
  payload_hash: string
  payload_hash_short: string
  platform: string
  destination_summary_redacted: string
  destination_binding_id: string
  credential_handle_id: string
  required_response_class:
    - explicit_approve
    - explicit_reject
    - explicit_edit_request
  challenge_text: string
  approval_phrase_required: string
  one_time_nonce: string
  status: pending | approved | rejected | expired | invalidated
```

Rules:

* Challenge must expire.
* Challenge must be one-time use.
* Challenge must show payload hash short.
* Challenge must show target platform and destination summary.
* A natural language reply can be interpreted, but approval must map to this challenge.

## 5.8 ApprovalLedgerEntry

Represents a signed local approval event.

Required fields:

```yaml
approval_ledger_entry:
  ledger_entry_id: string
  approved_at: timestamp
  operator_id: jim
  approval_channel: telegram | local_ui
  challenge_id: string
  payload_id: string
  payload_hash: string
  payload_hash_short: string
  platform: string
  destination_binding_id: string
  credential_handle_id: string
  media_manifest_hash: string | null
  approval_text_redacted: string
  approval_method: challenge_response | local_button
  prior_payload_hash: string | null
  revoked: false
  expiration: timestamp
  valid_for_dispatch: boolean
  blocked_reasons: array
  audit_hash: string
```

Rules:

* Append-only.
* Revocation creates a new entry, not mutation.
* Validity is derived, not assumed.
* If payload hash does not match current preview, `valid_for_dispatch=false`.

## 5.9 DispatchOutboxEntry

Represents an approved payload waiting for deterministic dispatch.

Required fields:

```yaml
dispatch_outbox_entry:
  outbox_id: string
  created_at: timestamp
  approval_ledger_entry_id: string
  payload_id: string
  payload_hash: string
  platform: string
  destination_binding_id: string
  credential_handle_id: string
  idempotency_key: string
  dispatch_mode: dry_run | supervised_live_future
  request_budget: 1
  auto_retry_allowed: false
  kill_switch_required: true
  status: queued | blocked | dispatched | failed | manual_fallback_required
  blocked_reasons: array
```

Rules:

* No outbox entry without valid approval.
* Idempotency key prevents duplicate posting.
* No auto retry.
* Live mode disabled until future platform live gate.

## 5.10 DispatchAuditEvent

Represents a redacted dispatch attempt or mock attempt.

Required fields:

```yaml
dispatch_audit_event:
  audit_event_id: string
  created_at: timestamp
  outbox_id: string
  platform: string
  destination_binding_id: string
  payload_hash: string
  idempotency_key: string
  request_budget_used: integer
  response_class: success | blocked | failed | rate_limited | credential_blocked | permission_blocked | unknown
  provider_response_redacted: object
  no_secret_leak_verified: true
  raw_request_persisted: false
  raw_response_persisted: false
  token_logged: false
  retry_count: 0
  final_url_verified: boolean | null
  audit_hash: string
```

Rules:

* No raw token.
* No raw response if it may include secrets.
* No request headers.
* No full provider account IDs unless classified safe.
* Redacted provider response only.

---

## 6. LLM Agent Design

## 6.1 Agent Type

The agent should be called:

**Local LLM Intake and Editorial Agent**

Not:

* publish agent;
* automation agent;
* dispatcher agent;
* social bot;
* OpenClaw skill runner;
* remote execution agent.

## 6.2 Agent Responsibilities

The agent may:

1. Parse Jim’s Telegram messages.
2. Identify intent.
3. Extract content idea.
4. Ask clarifying questions.
5. Create editorial brief.
6. Draft content.
7. Revise content.
8. Generate platform variants.
9. Detect likely forbidden language.
10. Suggest source requirements.
11. Explain blockers in plain English.
12. Convert natural language approval-like replies into approval challenge candidates.

## 6.3 Agent Prohibited Responsibilities

The agent must not:

1. Create approval ledger entries directly.
2. Mark anything as approved.
3. Dispatch anything.
4. Hydrate credentials.
5. Select a different account/channel/page than the bound destination.
6. Modify payload after approval without invalidating approval.
7. Retry a failed dispatch.
8. Hide blockers.
9. Remove limitations.
10. Treat memory as authority.
11. Execute shell/files/browser.
12. Install skills/plugins.
13. Read environment variables.
14. Read credential files.
15. Call platform APIs.
16. Override deterministic validators.
17. Produce public-ready status.

## 6.4 Agent Output Format

The LLM must output strict JSON-like packets validated by deterministic code.

Example output:

```json
{
  "intent_class": "create_content_from_idea",
  "confidence_class": "medium",
  "topic_summary": "One CPI print is insufficient to declare a macro regime shift.",
  "target_platforms": ["linkedin", "x"],
  "content_lane": "grounded_news_context",
  "market_sensitivity": "educational_macro",
  "source_needed": true,
  "draft_request": {
    "tone": "institutional",
    "length": "concise",
    "constraints": [
      "no trading signal",
      "no buy/sell/hold",
      "no market direction claim",
      "preserve uncertainty"
    ]
  },
  "requires_clarification": false,
  "can_create_content_brief": true,
  "can_approve": false,
  "can_dispatch": false
}
```

## 6.5 LLM Confidence Policy

If confidence is low, the system must ask Jim for clarification.

Examples:

* “Do you want this for LinkedIn, X, or Substack?”
* “Is this a general educational post or tied to a specific news item?”
* “Should I treat this as an idea only, or revise an existing draft?”
* “I found approval-like language, but there is no active approval challenge. Do you want me to show the latest preview?”

## 6.6 LLM Provider Policy

At this stage, the master plan should not assume a provider API is enabled.

LLM integration should have modes:

```yaml
llm_mode:
  disabled: default
  manual_external_llm: user pastes output
  local_model_future: future gate
  approved_provider_future: future explicit provider/API gate
```

Before any LLM provider integration:

* provider policy must exist;
* API key handling must be defined;
* prompt logging/redaction policy must exist;
* source/copyright policy must exist;
* cost budget must exist;
* no secrets in prompts;
* no raw proprietary data in prompts;
* output must be validated by deterministic schema.

---

## 7. Telegram Design

## 7.1 Telegram Is Remote UI

Telegram should be treated as:

* remote inbox;
* notification surface;
* preview surface;
* approval challenge surface;
* status query surface.

Not as:

* command shell;
* generic agent console;
* publish authority;
* credential interface;
* source of truth.

## 7.2 Telegram Message Classes

Supported incoming message classes:

1. `idea_message`
2. `revision_instruction`
3. `approval_response`
4. `rejection_response`
5. `hold_response`
6. `status_query`
7. `source_note`
8. `manual_metric_note`
9. `unknown`

## 7.3 Telegram Bot Response Types

Supported outgoing responses:

1. `idea_captured`
2. `clarification_request`
3. `draft_preview`
4. `revision_preview`
5. `approval_challenge`
6. `approval_recorded`
7. `approval_rejected`
8. `approval_expired`
9. `dispatch_blocked`
10. `dispatch_success`
11. `manual_fallback_required`
12. `status_summary`

## 7.4 Approval Challenge UX

Example Telegram response:

```text
Review: LinkedIn Preview v3

Platform: LinkedIn
Destination: LinkedIn member profile [redacted binding: acct_ln_member_01]
Payload hash: 9f3a2c71
Status: eligible for approval, not dispatched

Blocked now:
- live dispatch disabled until platform gate
- credential hydration disabled unless future gate

Reply:
APPROVE 9f3a2c71
REJECT 9f3a2c71
EDIT 9f3a2c71: <instruction>
HOLD 9f3a2c71
```

Natural language should also be allowed:

> “Approve LinkedIn version, hold X for edit.”

But the parser must map it to exact challenge(s). If ambiguous, ask clarification.

## 7.5 Telegram Security Controls

Required controls:

* verified Jim sender ID;
* allowed chat ID;
* bot must reject unknown senders;
* inbound rate limit;
* replay detection;
* message hash;
* challenge nonce;
* challenge expiration;
* command ambiguity handling;
* no direct dispatch on raw message;
* no secret display;
* no credential setup through Telegram initially.

## 7.6 Telegram Attachments

Attachments are a separate risk.

Initial phase:

* text-only ideas and reviews;
* no media upload;
* no file attachment ingestion;
* no voice note transcription;
* no images.

Future phases may add:

* image placeholder intake;
* media manifest generation;
* manual rights classification;
* alt text drafting;
* attachment hash;
* virus/mime policy;
* platform media constraints.

---

## 8. Approval Ledger and Payload Hash

## 8.1 Why This Is Next

The entire remote operator loop depends on one invariant:

**Jim approves an exact payload, not a vague idea.**

Without approval ledger + payload hash, Telegram natural-language approval is unsafe.

0174ED must happen before any Telegram review/approval loop.

## 8.2 Approval Ledger Requirements

The approval ledger must be:

* append-only;
* deterministic;
* local-first;
* redacted;
* hash-linked;
* revocation-aware;
* expiration-aware;
* exact payload bound;
* account binding aware;
* credential handle aware;
* platform aware;
* manual fallback aware.

## 8.3 Payload Hash Inputs

The hash should include:

* platform;
* payload text;
* payload formatting;
* thread split;
* media manifest hash;
* alt text;
* link preview class;
* destination binding ID;
* credential handle ID;
* visibility class;
* disclosure class;
* content lane;
* policy snapshot ID;
* platform adapter version;
* payload schema version.

The hash must not include:

* raw token;
* raw account ID if classified sensitive;
* raw provider response;
* credential value;
* env var;
* secret path;
* local absolute path if sensitive.

## 8.4 Approval States

Suggested states:

```text
draft_review_only
preview_ready
operator_review_required
approval_challenge_sent
operator_approved_for_local_outbox
operator_approved_for_mock_dispatch
operator_approved_for_supervised_live_dispatch_future
blocked
revoked
expired
invalidated_by_edit
dispatched
manual_fallback_required
```

## 8.5 Ledger Validation

A ledger entry is valid only if:

* payload hash matches current payload;
* challenge is not expired;
* approval came from verified Jim;
* account binding matches;
* credential handle matches;
* content lane allows review;
* no forbidden language blockers;
* kill switch policy allows next step;
* platform gate exists;
* no previous revocation supersedes it.

---

## 9. Dispatch Outbox and Idempotency

## 9.1 Why Outbox Is Needed

The dispatcher should not post immediately from the approval event.

Instead:

1. Approval creates ledger entry.
2. Ledger creates eligible outbox candidate.
3. Outbox runs deterministic gates.
4. Dispatcher posts only from outbox.

This prevents Telegram approval from becoming direct execution.

## 9.2 Outbox States

```text
not_created
candidate
queued
blocked_by_kill_switch
blocked_by_account_binding
blocked_by_credential_handle
blocked_by_platform_gate
blocked_by_policy
ready_for_mock_dispatch
ready_for_supervised_live_future
dispatching
dispatched
failed
manual_fallback_required
revoked
duplicate_suppressed
```

## 9.3 Idempotency

Every dispatch attempt must have:

* idempotency key;
* payload hash;
* platform;
* account binding;
* approval ledger ID;
* request budget;
* attempt number;
* no auto retry;
* duplicate suppression.

If Telegram sends duplicate approval or network repeats, the outbox must not double post.

## 9.4 No Auto-Retry

No auto retry is allowed initially.

Failure states must require manual review.

---

## 10. Platform Dispatch Strategy

## 10.1 Platform Order

Recommended live order remains:

1. Telegram supervised channel posting.
2. X supervised posting.
3. LinkedIn member/profile posting.
4. LinkedIn organization/page posting.
5. Facebook Page / Instagram.
6. TikTok last.

## 10.2 Why Telegram First

Telegram is the lowest-friction first live destination because:

* bot/channel model is simpler;
* account binding can be explicit;
* channel is controlled by operator;
* basic Bot API posting is straightforward;
* no app review comparable to LinkedIn/Meta/TikTok for basic use.

But Telegram as destination is different from Telegram as command interface.

Both must be separately gated:

* Telegram Remote Operator Inbox Gate.
* Telegram Supervised Channel Dispatch Gate.

## 10.3 Destination Account Binding

Before any live post:

* bot identity proof;
* target channel ID proof;
* channel permission proof;
* account binding ID;
* destination redaction;
* no wrong-channel failure;
* no DM/reply mode;
* no group/community automation.

## 10.4 Dispatch Request Policy

Every live adapter must have:

* exact endpoint allowlist;
* method allowlist;
* host allowlist;
* path allowlist;
* timeout;
* request budget 1;
* no redirect unless explicitly justified;
* final host verification where applicable;
* no auto retry;
* redacted response class;
* no raw response persistence;
* no credential logging;
* no scheduler.

---

## 11. Content Safety and Editorial Gates

## 11.1 Content Lanes

Every idea/draft must be classified into:

1. `pre_alpha_general_process`
2. `grounded_news_context`
3. `future_artifact_backed`
4. `blocked_or_unknown`

## 11.2 Pre-Alpha General / Process

Allowed:

* build-in-public;
* product philosophy;
* macro education;
* data sufficiency;
* forecast readiness;
* failure forensics philosophy;
* why no forecast can be correct;
* why Capital Chronicle is not a signal service.

Blocked:

* fake artifact-backed claims;
* fake DQR/readiness states;
* market calls;
* performance claims;
* public-ready fixture content.

## 11.3 Grounded News Context

Allowed:

* news as hook;
* source-cited explainers;
* official-source checking;
* data sufficiency discussion;
* forecast-readiness education;
* uncertainty explanation;
* non-advisory platform variants.

Blocked:

* buy/sell/hold;
* long/short;
* price targets;
* “our model predicts”;
* “our signal says”;
* “watch this level”;
* implied forecast authority;
* unsupported numeric market claims.

## 11.4 Future Artifact-Backed

Blocked until:

* approved internal-alpha artifact exists;
* artifact ID exists;
* lineage exists;
* freshness exists;
* DQR/data sufficiency/forecast readiness exists;
* limitations exist;
* content eligibility exists.

## 11.5 Telegram Ideas Are Not Source Authority

If Jim sends an idea:

> “Do a post about payrolls weakness.”

The system must treat that as an idea, not evidence.

If the post needs factual claims, it must request source context or mark source-needed.

---

## 12. UI / Cockpit Implications

## 12.1 Command Center

Must show:

* Remote Operator Loop disabled/enabled state;
* Telegram inbox state;
* LLM provider state;
* approval ledger state;
* payload hash state;
* outbox state;
* dispatch gate state;
* current blockers;
* next allowed action.

## 12.2 Content Studio

Must support:

* inbound ideas;
* content brief;
* LLM draft/revision status;
* platform variants;
* review packet;
* source-needed flags;
* approval status;
* not-public-postable labels.

## 12.3 Approval Queue

Must become the core operator authority surface.

Show:

* payload preview;
* payload hash;
* platform;
* destination binding;
* credential handle;
* approval challenge;
* expiration;
* revocation;
* edit invalidation;
* dispatch eligibility.

## 12.4 Publish Readiness Tower

Must show two separate Telegram rows:

1. Telegram Remote Operator Inbox
2. Telegram Channel Dispatch Destination

Do not collapse them.

## 12.5 Evidence Vault

Must archive:

* inbound message packet;
* intent packet;
* brief packet;
* draft variant;
* payload preview;
* approval challenge;
* ledger entry;
* outbox entry;
* dispatch audit event.

---

## 13. Security Model

## 13.1 Threats

The Remote Operator Loop creates new risks:

1. Fake Telegram sender.
2. Stolen Telegram account.
3. Replay of old approval.
4. Ambiguous natural language approval.
5. LLM misclassification.
6. Prompt injection in Jim’s own pasted content or source text.
7. Content edit after approval.
8. Wrong platform target.
9. Wrong account/channel.
10. Credential leakage.
11. Duplicate posting.
12. Silent retry.
13. Bot posts without audit.
14. Bot treats “ok” as approval without hash.
15. Approval challenge spoofing.
16. Telegram outage during audit.
17. Local machine online/offline state mismatch.
18. Queue drift.
19. Untrusted media attachment.
20. LLM provider prompt leakage.

## 13.2 Controls

Each threat needs a deterministic control:

| Threat                | Control                                                   |
| --------------------- | --------------------------------------------------------- |
| Fake sender           | Telegram sender binding and allowlist                     |
| Stolen account        | optional approval challenge phrase / second factor future |
| Replay                | nonce + expiration + one-time challenge                   |
| Ambiguous approval    | clarification required                                    |
| LLM misclassification | deterministic validator + no side effects                 |
| Prompt injection      | LLM output is advisory only                               |
| Edit after approval   | payload hash invalidation                                 |
| Wrong target          | account binding gate                                      |
| Credential leakage    | credential handle boundary                                |
| Duplicate posting     | idempotency key                                           |
| Silent retry          | no auto retry                                             |
| No audit              | dispatch blocked without audit sink                       |
| Generic “ok”          | not accepted unless maps to active challenge              |
| Spoof challenge       | local challenge ID + nonce                                |
| Outage                | manual fallback                                           |
| Queue drift           | outbox validation at dispatch time                        |
| Media risk            | media manifest gate                                       |
| Prompt leakage        | provider gate + redaction policy                          |

## 13.3 Security Scan Additions

Future tests should scan for:

* Telegram token leakage;
* raw chat IDs if classified sensitive;
* bot token patterns;
* approval challenge nonce leaks;
* unsupported `requests/httpx` imports in non-live modules;
* environment reads outside live gates;
* direct send calls outside dispatch adapter;
* approval bypass strings;
* auto-retry behavior;
* scheduler behavior;
* direct LLM-to-tool execution;
* persistent memory authority files;
* OpenClaw/ClawHub dependency strings.

---

## 14. Task Roadmap

## 14.1 Immediate Track: Approval Authority

### TASK_CONTENTOPS_0174ED_APPROVAL_LEDGER_AND_PAYLOAD_HASH_CONTRACT_V0

Objective:
Build the local approval ledger and payload hash contract.

Allowed:

* stdlib-only Python module;
* schema or deterministic dict contract;
* tests;
* docs;
* fake fixtures.

Forbidden:

* live platform calls;
* Telegram integration;
* credential reads;
* LLM provider calls;
* posting;
* scheduler;
* env reads.

Deliverables:

* `live_contentops/approval_ledger_payload_hash_contract.py`
* tests for approval/hash invalidation/revocation/expiration
* docs/automation/0174ED packet
* no source side effects on import

Acceptance:

* exact payload hash built deterministically;
* approval invalidates on content/account/platform/media change;
* append-only ledger model;
* revocation supported;
* no live behavior.

### TASK_CONTENTOPS_0174EE_DISPATCH_OUTBOX_AND_IDEMPOTENCY_CONTRACT_V0

Objective:
Build outbox and idempotency model.

Allowed:

* outbox model;
* idempotency keys;
* state transitions;
* no live transport.

Acceptance:

* duplicate suppression;
* no outbox without approval;
* no auto retry;
* blocked states explicit;
* redacted audit precondition.

## 14.2 Remote Operator Intake Track

### TASK_CONTENTOPS_0174TG_TELEGRAM_REMOTE_OPERATOR_INBOX_CONTRACT_V0

Objective:
Define Telegram inbound message contract.

Allowed:

* schemas/models/tests/docs;
* fake Telegram messages;
* no live bot.

Acceptance:

* verified/unknown sender classes;
* replay detection;
* redaction;
* no command execution;
* text-only initial scope.

### TASK_CONTENTOPS_0174TH_LLM_INTENT_PARSER_CONTRACT_V0

Objective:
Define local LLM intent parser contract for Telegram natural language.

Allowed:

* deterministic parser stubs;
* fake LLM outputs;
* strict schema validation;
* ambiguity tests.

Forbidden:

* provider API calls;
* actual model integration;
* shell/tool execution.

Acceptance:

* natural language maps to structured intent;
* low confidence asks clarification;
* approval-like text cannot approve without challenge;
* parser output cannot dispatch.

### TASK_CONTENTOPS_0174TI_TELEGRAM_REVIEW_CHALLENGE_CONTRACT_V0

Objective:
Define review/approval challenge surface.

Allowed:

* fake Telegram challenge messages;
* approval parsing;
* nonce/expiration/hash binding;
* tests.

Acceptance:

* exact hash required;
* ambiguous replies rejected;
* edit requests invalidate approval path;
* reply must map to active challenge.

## 14.3 Editorial Agent Track

### TASK_CONTENTOPS_0174TJ_EDITORIAL_AGENT_DRAFT_REVISION_CONTRACT_V0

Objective:
Define LLM editorial agent contract for content drafting/revision.

Allowed:

* prompt contract docs;
* fake LLM drafts;
* review packet validation;
* no provider call.

Acceptance:

* agent can draft/revise;
* agent cannot approve;
* agent cannot publish;
* output is not-public-postable;
* forbidden language blocked.

### TASK_CONTENTOPS_0174TK_PLATFORM_PREVIEW_AND_HASH_INTEGRATION_V0

Objective:
Connect drafts to platform payload previews and hash contract.

Allowed:

* local renderer integration;
* fake previews;
* hash manifest.

Acceptance:

* LinkedIn/X/Telegram previews hash correctly;
* changes invalidate hash;
* platform constraints visible.

## 14.4 Dispatch Dry Run Track

### TASK_CONTENTOPS_0174TL_SUPERVISED_DISPATCH_DRY_RUN_CONTRACT_V0

Objective:
End-to-end dry-run flow from Telegram idea to approved mock dispatch.

Flow:

* fake Telegram idea;
* fake intent parser;
* draft;
* preview;
* approval challenge;
* ledger;
* outbox;
* mock dispatch;
* audit.

Acceptance:

* no network;
* no credentials;
* no posting;
* full audit generated;
* duplicate suppressed.

## 14.5 First Live Track

### TASK_CONTENTOPS_0174TM_TELEGRAM_BOT_IDENTITY_AND_OPERATOR_INBOX_LIVE_READ_ONLY_V0

Objective:
Live-read-only Telegram bot identity proof / inbound configuration proof.

Scope must be explicitly approved later.

Requirements:

* one request budget;
* no posting;
* no sendMessage;
* no credential logging;
* token redaction;
* final host verification if applicable;
* operator GO required.

### TASK_CONTENTOPS_0174TN_TELEGRAM_CHANNEL_PERMISSION_PROOF_LIVE_READ_ONLY_OR_SAFE_PROBE_V0

Objective:
Prove bot can target intended channel without posting public content, if Telegram supports safe proof.

If not possible, document manual proof.

### TASK_CONTENTOPS_0174TO_TELEGRAM_SUPERVISED_CHANNEL_POST_ONE_REQUEST_LIVE_PILOT_V0

Objective:
First live supervised channel post.

Only after:

* approval ledger;
* payload hash;
* account binding;
* credential handle;
* kill switch;
* outbox;
* idempotency;
* audit;
* live token handling gate;
* explicit operator GO.

---

## 15. Acceptance Milestones

## 15.1 Milestone A — Local Authority Foundation

Includes:

* 0174ED approval ledger + payload hash;
* 0174EE outbox + idempotency.

Result:
The system can prove what Jim approved and prevent changed content from using stale approval.

## 15.2 Milestone B — Remote Intake Foundation

Includes:

* Telegram remote inbox contract;
* LLM intent parser contract;
* review challenge contract.

Result:
Jim can send ideas/replies conceptually, but no live bot and no provider calls yet.

## 15.3 Milestone C — Editorial Agent Foundation

Includes:

* editorial draft/revision contract;
* platform preview integration;
* review packet integration.

Result:
The system can transform ideas into review-only content and produce hashable previews.

## 15.4 Milestone D — End-to-End Dry Run

Includes:

* fake Telegram inbound;
* fake LLM parser;
* fake draft generation;
* approval challenge;
* ledger;
* outbox;
* mock dispatch;
* redacted audit.

Result:
Full remote operator loop exists without live network or credentials.

## 15.5 Milestone E — Telegram Live Read-Only

Includes:

* bot identity proof;
* operator/channel binding proof;
* no posting.

Result:
The system can verify Telegram configuration without posting.

## 15.6 Milestone F — First Supervised Live Post

Includes:

* one selected platform;
* one selected account/channel;
* one approved payload;
* one request;
* no retry;
* audit;
* manual fallback.

Result:
The system proves final product direction: supervised publish after human approval.

---

## 16. What Not To Build Yet

Do not build yet:

* OpenClaw runtime;
* generic AI agent host;
* ClawHub-style skill marketplace;
* persistent agent memory authority;
* Telegram command execution;
* live bot post;
* platform scheduler;
* autonomous replies/DMs;
* social engagement automation;
* auto-thread replies;
* auto-DM;
* raw credential setup through Telegram;
* voice note transcription;
* media upload ingestion;
* provider LLM API integration;
* background always-on dispatcher;
* publish-all button;
* cron posting;
* browser automation;
* scraping;
* metrics scraping.

---

## 17. Future UI Language

The UI and Telegram messages must never say:

* “Auto-post enabled”
* “Bot will handle it”
* “AI approved”
* “Ready to publish” without exact gate context
* “Signal”
* “Market call”
* “Trade idea”
* “Model says buy/sell”
* “Guaranteed”
* “Publish all”
* “Schedule automatically”

Preferred language:

* “Review-only”
* “Approval challenge”
* “Payload hash”
* “Exact platform preview”
* “Manual approval required”
* “Future supervised dispatch”
* “Live disabled”
* “Blocked by kill switch”
* “Source needed”
* “No signal framing”
* “No financial advice”
* “Dispatch eligible after gates”
* “One-request supervised dispatch”

---

## 18. Example Remote Operator Loop Scenarios

## 18.1 Scenario 1 — Idea Capture

Jim:

> Idea: one CPI print is not a regime call. Make LinkedIn post, institutional tone.

System:

* captures idea;
* classifies lane as grounded_news_context or macro education;
* marks source-needed if factual CPI details included;
* creates brief;
* draft is review-only.

No approval yet.

No dispatch.

## 18.2 Scenario 2 — Revision

Jim:

> Make the hook less dramatic and remove the phrase “market reaction”.

System:

* maps to revision_instruction;
* modifies draft;
* new body hash;
* old payload hash invalidated;
* sends updated preview.

No approval yet unless Jim explicitly approves new hash.

## 18.3 Scenario 3 — Ambiguous Approval

Jim:

> ok looks good

System:

If active challenge exists and one payload only:

* ask confirmation:
  “Do you approve payload hash 9f3a2c71 for LinkedIn destination acct_ln_member_01?”

If multiple challenges exist:

* ask clarification.

Do not approve directly.

## 18.4 Scenario 4 — Explicit Approval

Jim:

> Approve LinkedIn 9f3a2c71

System:

* verifies active challenge;
* verifies sender;
* verifies nonce/expiration;
* verifies payload hash;
* creates ledger entry;
* creates outbox candidate;
* dispatch remains blocked if live gate disabled.

## 18.5 Scenario 5 — Dispatch After All Gates

System checks:

* ledger valid;
* payload hash current;
* account binding pass;
* credential handle symbolic/live gate pass;
* kill switch pass;
* platform live gate pass;
* idempotency no duplicate;
* request budget available.

Then dispatches once and audits.

---

## 19. Required Evidence Packet Standard For Each Task

Every future task in this track must report:

* task label;
* mode;
* result;
* repo;
* branch;
* starting HEAD;
* final HEAD;
* origin/master SHA;
* commit message;
* changed files;
* validation commands;
* whether full suite ran;
* whether unrelated working tree changes existed;
* no live/network/credential/provider/platform behavior statement;
* no OpenClaw runtime statement;
* protected path statement;
* current blockers;
* exact next task.

For live tasks, also include:

* endpoint allowlist;
* host/path/scheme;
* method;
* request budget;
* timeout;
* redirect policy;
* final host verification;
* credential redaction proof;
* no retry proof;
* audit proof;
* manual fallback;
* rollback plan.

---

## 20. New Canonical Roadmap Summary

```text
0174ED — Approval Ledger + Payload Hash Contract
0174EE — Dispatch Outbox + Idempotency Contract

0174TG — Telegram Remote Operator Inbox Contract
0174TH — LLM Intent Parser Contract
0174TI — Telegram Review Challenge Contract

0174TJ — Editorial Agent Draft/Revision Contract
0174TK — Platform Preview + Payload Hash Integration
0174TL — End-to-End Supervised Dispatch Dry Run

0174TM — Telegram Bot Identity / Inbox Live Read-Only Gate
0174TN — Telegram Channel Permission Proof Gate
0174TO — Telegram First Supervised Live Post Pilot

Later:
- X supervised publishing gate
- LinkedIn supervised publishing gate
- Meta/Instagram gate
- TikTok last
- metrics manual capture first
- read-only metrics API later
```

---

## 21. Final Operating Rule

The correct mental model is:

**Remote natural language is allowed. Remote autonomous execution is not.**

Jim can send natural language from Telegram.

A local LLM agent can understand and draft.

Jim can approve exact payloads remotely.

The local system can post after approval, but only through deterministic dispatch gates.

OpenClaw should not be used as the runtime because it combines natural-language messaging, persistent memory, broad tools, skills, gateway, and execution authority in one layer.

ContentOps should build the same user convenience with a stricter architecture:

* Telegram as remote UI;
* LLM as parser/editor;
* approval ledger as authority;
* payload hash as lock;
* account binding as destination proof;
* credential handle as secret boundary;
* outbox as dispatch queue;
* platform adapter as one-request executor;
* audit as evidence;
* Jim as final approver.

This is the path from local automation-readiness into a real supervised publishing product without becoming an unsafe bot.
