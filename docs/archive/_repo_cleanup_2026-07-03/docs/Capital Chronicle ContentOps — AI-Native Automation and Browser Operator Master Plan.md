# Capital Chronicle ContentOps — AI-Native Automation and Browser Operator Master Plan

## 0. Executive Decision

Capital Chronicle ContentOps should now pivot from a cautious manual/export-first publishing cockpit into an **AI-native supervised automation system**.

This does not mean becoming an autonomous spam bot, a hidden scheduler, a social engagement agent, or a browser-clicking black box. It means the product should treat AI, LLMs, browser automation, platform adapters, media discovery, rewrite engines, and dispatch flows as first-class operating layers. Jim remains the owner, reviewer, and emergency fallback, but the intended product should automate the repetitive content operations work wherever it can do so safely, visibly, and audibly.

The previous plan correctly protected the system from unsafe live publishing. It correctly established approval ledgers, payload hashes, account binding, credential boundaries, outbox revalidation, idempotency, kill switches, and redacted audit. The new plan keeps those primitives, but changes the product center of gravity.

The old practical posture was:

```text
Prepare content locally.
Preview platform payloads.
Manual publish first.
Future supervised dispatch later.
```

The new posture should be:

```text
AI researches, drafts, rewrites, adapts, prepares media, and operates bounded automation.
ContentOps validates, hashes, binds, gates, and audits.
Jim approves, supervises, or falls back manually only when automation is blocked or risky.
```

The final product should not be manual-first. Manual should be a fallback path, not the north star. The north star is **supervised AI-driven content production and distribution**, with deterministic controls around the live edge.

The product should be able to do this:

```text
Jim gives a topic, idea, source, or intent
→ AI Research Agent grounds the topic
→ AI Writer creates canonical Substack article
→ AI SEO Agent optimizes title, subtitle, keywords, slug, and structure
→ AI Media Agent proposes image concepts and finds usable visual candidates
→ Media Rights Gate verifies source, license, attribution, and platform constraints
→ AI Platform Adapter rewrites the canonical piece for X, Telegram, LinkedIn, Threads, Instagram, Facebook, and other targets
→ Draft Inspector validates claims, citations, limitations, no-signal/no-advice rules, platform fit, media rights, and policy constraints
→ Platform Preview renders exact payloads
→ Payload Hash Lock binds copy, media, destination, visibility, credential handle, and adapter version
→ Jim approves selected payloads
→ Automation Adapter dispatches through official API, browser/CDP, or manual fallback depending platform state
→ Redacted audit records exact evidence, URL/result class, and recovery state
→ Metrics layer records manual or API-derived performance
```

This is not a social scheduler. This is not an autonomous publishing bot. This is not an LLM with broad authority. It is an **AI-powered content operating system** where AI handles the labor and ContentOps handles authority.

The strategic priority should change from “avoid automation until everything is perfect” to “build automation as the default, but constrain every automation step with explicit contracts.” That is how ContentOps becomes useful fast enough to matter.

---

## 1. Product Thesis

Capital Chronicle will need an audience before the full internal-alpha product is ready. That audience will not be built by occasionally copying manual drafts into platforms. It will be built by a repeatable publishing machine that can turn serious macro ideas into high-quality multi-platform content at low operational friction.

The wedge is not “we post more often.” The wedge is:

```text
Capital Chronicle explains research maturity, data sufficiency, uncertainty, source quality, and forecast readiness better than generic finance content.
```

The ContentOps product should therefore become a machine for converting complex thinking into public communication formats. The role of AI is not optional. AI is the production engine.

There are four production realities:

First, writing the canonical idea is not enough. Each platform has a different grammar. Substack wants structured long-form. X wants compression, hooks, sequencing, and optionally thread continuation. LinkedIn wants institutional clarity and professional context. Telegram wants concise but useful dispatch. Instagram needs visual-first packaging, caption discipline, and media rights. Threads wants conversational short-form. Facebook Page wants accessible summary. TikTok and YouTube need video metadata, titles, descriptions, and media packages.

Second, API-first is not always rational. X is cost-gated. LinkedIn is scope/review gated. Meta is app/product/scope/asset gated. TikTok and YouTube are media and review heavy. Substack does not offer a clean obvious official creator-posting API in the way a developer would prefer. In an AI era, browser/CDP automation is a legitimate adapter class when API paths are expensive, unstable, unavailable, or too slow to obtain.

Third, unofficial automation is not automatically bad. The risk is not “unofficial.” The risk is unbounded automation without payload hashes, account binding, credential isolation, pre-click comparison, stop conditions, and audit. A well-bounded browser automation adapter can be safer than an official API adapter if it is easier to visually verify destination, payload, and final action. Conversely, an official API adapter can be dangerous if it posts to the wrong account with stale approval.

Fourth, Jim’s time is the scarce resource. If the workflow still requires Jim to manually assemble copy, find images, rewrite captions, move content across tabs, and track URLs, then ContentOps is not doing enough. Jim should review, approve, correct, and override. Jim should not be the default mechanical publisher.

The new product thesis is therefore:

```text
ContentOps should be an AI-native supervised content automation system where canonical long-form thinking becomes multi-platform distribution through LLM agents, media automation, browser/CDP adapters, official APIs where practical, and deterministic approval/audit gates. Manual publishing remains first-class, but only as fallback, recovery, or operator override.
```

---

## 2. What Changes From the Previous Plan

The previous plan had a defensive posture around browser automation and OpenClaw-like systems. That posture made sense while the repo lacked enough authority primitives. Now the strategy should evolve.

The previous plan said:

```text
OpenClaw is reference-only / anti-pattern.
Browser-assisted lab is optional.
Manual export remains primary for Substack.
Provider LLM calls are future-gated.
Platform APIs are future-gated.
```

The new plan should say:

```text
AI and browser automation are first-class capability tracks.
OpenClaw or similar agentic browser frameworks may be evaluated as bounded execution adapters.
Browser/CDP automation becomes a formal platform adapter type.
Substack browser automation becomes the primary near-term automation target.
Provider LLM integration becomes a core product layer, not a distant UI placeholder.
Manual export remains fallback, not the primary operating model.
```

This is a meaningful shift, but it does not remove the existing safety architecture. It repositions it.

The existing safety primitives become more important, not less important:

```text
Approval ledger: required before any dispatch.
Payload hash: required before browser or API action.
Destination binding: required before the browser can publish anywhere.
Credential handle: required before API or browser session usage is treated as a capability.
Media manifest: required before uploading or attaching any image.
Pre-click visual checkpoint: required for browser automation.
Outbox: required before dispatch.
Idempotency: required to prevent duplicates.
Kill switch: required globally and per platform.
Audit: required for all outcomes.
Manual fallback: required when automation fails or stops.
```

The difference is that these controls no longer block automation as a concept. They enable automation as a product.

The new product should have three execution classes:

```yaml
execution_class:
  official_api_adapter:
    description: uses official platform API where docs, scopes, account binding, and credentials are accepted
    examples:
      - Telegram Bot API sendMessage
      - LinkedIn member post if scope is available
      - Meta Page post if app/page token is available
      - YouTube private/unlisted upload if OAuth scope and media manifest pass

  browser_cdp_adapter:
    description: uses controlled browser automation against a logged-in operator profile
    examples:
      - Substack article compose and publish
      - LinkedIn compose if API is blocked
      - X compose if API cost is unacceptable
      - Instagram manual-style compose if API/media path is too heavy
      - Threads compose if API scope is blocked

  manual_fallback_adapter:
    description: produces exact copy/export/checklist/URL record for Jim when automation is blocked
    examples:
      - copy Substack markdown manually
      - paste X thread manually
      - manually record metrics
      - manually reconcile unknown post result
```

The browser/CDP adapter is the new strategic layer.

---

## 3. New Product Name and Capability Track

The working product name remains:

```text
Capital Chronicle ContentOps
```

The new capability track should be named:

```text
AI Web Operator + Supervised Publishing Automation
```

Short internal names:

```text
AI Web Operator
Browser Operator Lane
ContentOps Automation Core
```

Avoid names like:

```text
Auto Poster
Social Bot
OpenClaw Runtime
Publishing Agent
Growth Bot
Scheduler
```

The product language matters. “AI Web Operator” is acceptable because it describes a bounded operator that performs web tasks. “Auto Poster” is not acceptable because it implies hidden autonomous posting. “Publishing Agent” is ambiguous and too close to authority leakage. “OpenClaw Runtime” incorrectly makes a third-party or external agent framework the product center.

The correct product definition:

```text
The AI Web Operator is a bounded automation layer inside ContentOps that can use LLM planning, browser/CDP actions, official platform APIs, and deterministic replay scripts to prepare and execute approved publishing workflows. It cannot approve content, select hidden accounts, bypass payload hashes, read raw credentials, ignore media rights, or dispatch without an outbox entry.
```

The AI Web Operator may:

```text
navigate browser pages
open compose screens
paste approved content
attach approved media
search for image candidates
capture screenshot-safe checkpoints
compare visible payload against approved hash inputs
click one approved publish action after Jim GO
record URL/result evidence
route failure to manual fallback
```

The AI Web Operator may not:

```text
read cookies or session storage
export browser profiles
dump DOM containing tokens
handle passwords or 2FA invisibly
choose a different account
publish without approval
schedule posts
reply to other users
DM anyone
scrape metrics
auto-retry unknown results
alter payload after approval
use unapproved media
hide blockers
```

This makes browser automation a tool of the system, not a sovereign actor.

---

## 4. High-Level Architecture

The new architecture should have fourteen layers.

### Layer 1 — Operator Intent and Ingress

Inputs may come from:

```text
local UI
Telegram remote operator message
pasted source note
manual idea entry
uploaded research brief
approved internal-alpha artifact later
browser-captured source candidate later
content calendar backlog
```

All inputs are untrusted until classified. Even Jim’s own Telegram message is not automatically a source or approval. It is an operator input. The system must create an `OperatorIntentPacket` or `ContentIdeaPacket`.

Intent classes:

```yaml
intent_class:
  create_canonical_article
  revise_existing_article
  create_platform_variants
  research_topic
  find_media
  approve_payload
  reject_payload
  request_browser_publish
  request_manual_export
  request_metrics_update
  ask_status
  unknown
```

The key policy:

```text
Natural language can start workflows.
Natural language cannot bypass approval state.
```

### Layer 2 — Research and Grounding Agent

The AI Research Agent is responsible for turning a topic into a safe research packet.

It can:

```text
generate research questions
search approved sources if web/search gate is enabled
summarize source-provided context
classify source type
extract citation candidates
identify missing evidence
separate official sources from news/commentary
suggest safe angles
suggest unsafe angles
```

It cannot:

```text
invent facts
invent citations
treat news as signal
turn a market event into advice
use paywalled text beyond allowed summary
redistribute vendor data
claim Capital Chronicle model output exists if it does not
```

Output object:

```yaml
research_grounding_packet:
  packet_id: string
  topic: string
  source_mode: manual | approved_web_search | official_sources | operator_supplied | artifact_future
  source_refs: array
  official_source_refs: array
  non_official_source_refs: array
  source_license_status: pass | warning | blocked | unknown
  freshness_status: current | stale | mixed | unknown
  claim_boundary: educational | factual_summary | opinion | blocked
  source_needed: boolean
  safe_angles: array
  unsafe_angles: array
  required_caveats: array
  no_signal_status: pass | blocked
  no_advice_status: pass | blocked
  allowed_for_drafting: boolean
  allowed_for_approval: boolean
  blocked_reasons: array
```

### Layer 3 — Canonical Article Agent

The canonical article should usually be the Substack article. Substack becomes the owned long-form source of truth for a topic. The platform posts become derivatives of that canonical article.

The Canonical Article Agent creates:

```text
title candidates
subtitle candidates
canonical thesis
lede
outline
body sections
pull quotes
source/citation notes
limitations section
SEO title
SEO description
slug candidates
image concept list
platform adaptation brief
```

Output object:

```yaml
canonical_article_draft:
  article_id: string
  source_research_packet_id: string
  title: string
  subtitle: string
  slug_candidate: string
  lede: string
  body_markdown: string
  section_map: array
  citations: array
  limitations: array
  no_advice_disclaimer_needed: boolean
  no_signal_status: pass | warning | blocked
  claim_risk_status: pass | warning | blocked
  seo_packet_id: string
  media_request_packet_id: string
  human_review_required: true
  public_postable: false
```

This article is not automatically published. It becomes the canonical payload source for downstream variants.

### Layer 4 — SEO and Editorial Optimization Agent

This agent improves discoverability and readability.

It can:

```text
suggest title variants
suggest subtitles
suggest SEO keywords
suggest slug candidates
generate meta descriptions
score readability
score audience fit
suggest hooks
suggest content framing
suggest evergreen/temporal classification
```

It cannot:

```text
remove caveats
turn uncertainty into certainty
invent sources
remove no-signal constraints
create clickbait market calls
claim prediction authority
```

Output object:

```yaml
seo_editorial_packet:
  seo_packet_id: string
  article_id: string
  primary_keyword: string
  secondary_keywords: array
  search_intent: informational | educational | opinion | update
  title_candidates: array
  subtitle_candidates: array
  slug_candidates: array
  meta_description: string
  readability_score: integer
  editorial_score: integer
  audience_fit_scores: object
  limitations_preserved: boolean
  unsafe_clickbait_rejected: array
```

### Layer 5 — Media Discovery and Rights Agent

This is a new first-class layer. Platform publishing increasingly requires media. Instagram especially is media-first. X and LinkedIn perform better with visual support. Substack benefits from a hero image.

The Media Agent can:

```text
derive visual concepts from the article
generate image search queries
search approved image sources if browser/search gate is enabled
collect candidate image metadata
suggest AI-generated image prompts if allowed
suggest owned-media reuse
suggest chart/card concepts
write alt text
detect platform crop constraints
```

It cannot:

```text
use arbitrary Google Images as safe media
download and attach images without license classification
claim commercial rights without evidence
strip attribution requirements
use copyrighted news images without permission
ignore platform media rules
upload media before approval
```

The image-search workflow should not be “find a nice image and post it.” It should be:

```text
AI creates image concepts
→ browser/CDP searches Google Images, Creative Commons sources, stock/owned libraries, or approved sources
→ system stores metadata, not raw media first
→ Media Rights Gate checks license and source page
→ Jim or policy approves candidate
→ local media file is downloaded or generated only after approval
→ file hash, dimensions, license, attribution, alt text, and platform constraints are locked
```

Media object:

```yaml
media_candidate:
  candidate_id: string
  source_type: google_image_result | creative_commons | stock | owned | generated | screenshot_safe_card
  source_url: string
  preview_url_redacted: string
  creator: string | null
  license_url: string | null
  license_name: string | null
  commercial_use_allowed: boolean | null
  modification_allowed: boolean | null
  attribution_required: boolean | null
  attribution_text: string | null
  rights_status: pass | warning | blocked | unknown
  platform_constraints: object
  alt_text_candidate: string
  local_file_hash: string | null
  approved_for_download: boolean
  approved_for_publish: boolean
  blocked_reasons: array
```

Media manifest:

```yaml
media_rights_manifest:
  manifest_id: string
  article_id: string
  media_items: array
  manifest_hash: string
  license_status: pass | warning | blocked
  attribution_status: pass | warning | blocked
  platform_use_status: object
  approved_platforms: array
  human_review_required: true
```

### Layer 6 — Platform Variant Agent

The Platform Variant Agent converts the canonical article into platform-native payloads.

It creates:

```text
X post
X thread
Telegram channel post
LinkedIn member post
LinkedIn organization post
Threads post
Facebook Page post
Instagram caption/carousel plan
Substack publish payload
TikTok title/description/hashtags
YouTube title/description/tags
```

Each platform version should be adapted, not merely truncated.

For X:

```text
The output may be a single post, a thread, or a post plus self-thread continuation.
No replies to other accounts.
No engagement automation.
No likes, reposts, follows, DMs.
```

For LinkedIn:

```text
The output should be institutional, concise, professional, no trading call, no signal framing.
Member and organization versions are separate.
```

For Instagram:

```text
The output should begin with the image/carousel concept, caption, alt text, hashtags, and media constraints.
Text-only Instagram is not assumed.
```

For Telegram:

```text
The output should be concise, direct, and optionally link to Substack.
```

For Substack:

```text
The output is canonical long-form article with title, subtitle, markdown/html, tags, audience, email/app inbox options, and optional image.
```

Output object:

```yaml
platform_variant_set:
  variant_set_id: string
  canonical_article_id: string
  generated_at: timestamp
  variants:
    - platform: substack
      payload_class: newsletter_issue
      title: string
      subtitle: string
      body_markdown: string
      tags: array
      media_manifest_id: string | null
    - platform: x
      payload_class: single_post | thread
      parts: array
      media_manifest_id: string | null
    - platform: instagram
      payload_class: image_post | carousel | reel_future
      caption: string
      media_manifest_id: string
      hashtags: array
    - platform: linkedin_member
      payload_class: text_or_image_post
      body: string
      media_manifest_id: string | null
  limitations_preserved: boolean
  source_refs_preserved: boolean
  no_advice_status: pass | warning | blocked
  no_signal_status: pass | warning | blocked
  human_review_required: true
```

### Layer 7 — Draft Inspector and Policy Compiler

The Draft Inspector is deterministic. It validates AI output.

Checks:

```text
source completeness
citation completeness
unsupported claim detection
market advice language
signal language
broker/execution language
performance claims
forecast authority claims
model prediction claims
forbidden platform behavior
unsafe disclaimers
missing limitations
media rights status
platform payload constraints
thread ordering
copy length
hashtag policy
image availability
link availability
```

It produces:

```yaml
draft_inspection_report:
  report_id: string
  article_id: string
  variant_set_id: string
  claim_risk_status: pass | warning | blocked
  citation_status: pass | warning | blocked
  no_advice_status: pass | warning | blocked
  no_signal_status: pass | warning | blocked
  media_rights_status: pass | warning | blocked
  platform_constraints_status: object
  approval_eligible_platforms: array
  blocked_platforms: array
  required_edits: array
  warnings: array
  evidence_refs: array
```

AI may explain the report, but deterministic validators own the state.

### Layer 8 — Platform Preview and Payload Hash

Every approved post must come from an exact preview.

The Platform Preview layer renders what will be sent, pasted, uploaded, or manually exported. It includes:

```text
platform
destination binding
credential handle
payload text
thread parts
title/subtitle
media manifest
alt text
visibility class
reply/comment settings
link preview intent
adapter type: API / browser / manual
adapter version
policy snapshot
payload hash
```

Payload hash must include:

```text
platform
destination binding ID
credential handle ID
adapter type
adapter version
payload schema version
text
thread structure
title/subtitle
media manifest hash
alt text
visibility
disclosure class
link preview class
platform formatting
policy snapshot
source/citation packet
guardrail result
```

Payload hash must not include:

```text
raw token
cookie
session value
password
raw browser storage
sensitive local path
secret filename
raw provider response
```

### Layer 9 — Approval Ledger

Jim approves exact payload hashes.

Approval may come through:

```text
local UI
Telegram challenge
future mobile UI
```

Approval must bind:

```text
operator
platform
destination
credential handle
payload hash
media manifest hash
adapter type
visibility
policy snapshot
challenge ID
expiration
approval text
```

Any edit invalidates approval:

```text
text edit
thread split change
media change
media order change
alt text change
destination change
platform change
visibility change
adapter version change
policy snapshot change
link preview change
caption change
hashtag change
```

Approval object:

```yaml
approval_ledger_entry:
  ledger_entry_id: string
  operator_id: jim
  approval_channel: local_ui | telegram
  payload_id: string
  payload_hash: string
  media_manifest_hash: string | null
  destination_binding_id: string
  credential_handle_id: string
  adapter_type: official_api | browser_cdp | manual_fallback
  adapter_version: string
  approved_at: timestamp
  expires_at: timestamp
  valid_for_outbox: boolean
  valid_for_dispatch: boolean
  revoked: boolean
  blocked_reasons: array
  audit_hash: string
```

### Layer 10 — Browser Automation Plan

This is the central new object.

A browser automation run must be planned before it starts. The plan is not a prompt that says “go publish.” It is a bounded execution packet.

```yaml
browser_automation_plan:
  plan_id: string
  platform: substack | x | linkedin | threads | instagram | facebook | other
  objective: compose_only | pre_click_checkpoint | supervised_publish | result_reconciliation
  engine: openclaw | browser_use | stagehand | playwright_cdp | plain_playwright
  browser_profile_id: string
  target_url: string
  destination_binding_id: string
  credential_handle_id: string
  payload_id: string
  payload_hash: string
  media_manifest_hash: string | null
  allowed_actions:
    - navigate
    - click_known_control
    - paste_text
    - upload_approved_media
    - set_visible_option
    - take_screenshot
    - read_visible_page_text
  forbidden_actions:
    - read_cookies
    - read_local_storage
    - read_session_storage
    - dump_full_dom
    - inspect_auth_headers
    - change_account
    - alter_payload_text
    - choose_unapproved_media
    - click_publish_without_go
    - schedule_post
    - reply_to_unapproved_users
    - send_dm
    - scrape_metrics
  stop_conditions:
    - account_uncertain
    - destination_uncertain
    - visible_payload_mismatch
    - media_mismatch
    - publish_button_uncertain
    - login_or_2fa_required
    - unexpected_modal
    - platform_ui_changed
    - secret_detected_on_screen
  requires_pre_click_checkpoint: true
  requires_jim_go: true
  request_budget: 1
  auto_retry_allowed: false
```

This allows OpenClaw or another engine to be used without making it the authority.

### Layer 11 — Visual Compose Checkpoint

Before a browser/CDP adapter clicks publish, it must create a checkpoint.

```yaml
visual_compose_checkpoint:
  checkpoint_id: string
  plan_id: string
  platform: string
  screenshot_path: string
  screenshot_safe_status: pass | warning | blocked
  visible_destination_match: pass | fail | uncertain
  visible_payload_match: pass | fail | uncertain
  visible_media_match: pass | fail | uncertain | not_applicable
  visible_visibility_match: pass | fail | uncertain
  visible_account_match: pass | fail | uncertain
  payload_hash: string
  media_manifest_hash: string | null
  pre_click_status: ready_for_jim_go | blocked | uncertain
  jim_go_required: true
  blocked_reasons: array
```

If any field is fail or uncertain, automation stops and routes to manual fallback.

### Layer 12 — Dispatch Outbox

Approval does not post directly. Approval creates an outbox candidate.

Outbox entry:

```yaml
dispatch_outbox_entry:
  outbox_id: string
  platform: string
  destination_binding_id: string
  credential_handle_id: string
  payload_id: string
  payload_hash: string
  media_manifest_hash: string | null
  adapter_type: official_api | browser_cdp | manual_fallback
  approval_ledger_entry_id: string
  idempotency_key: string
  request_budget: 1
  auto_retry_allowed: false
  kill_switch_required: true
  pre_dispatch_revalidation_status: pass | blocked
  status: candidate | blocked | ready | dispatching | dispatched | failed | unknown | manual_fallback_required
  blocked_reasons: array
```

Browser dispatch is still dispatch. It needs outbox and idempotency.

### Layer 13 — Dispatch Adapter

Adapters may be API, browser, or manual.

Official API adapter:

```text
uses platform API
requires endpoint allowlist
requires method allowlist
requires credential hydration gate
requires final host/path verification
requires no-retry
```

Browser/CDP adapter:

```text
uses logged-in browser profile
requires browser plan
requires pre-click checkpoint
requires Jim GO
requires screenshot-safe audit
requires stop on uncertainty
```

Manual fallback adapter:

```text
creates copy/export package
shows checklist
records manual result URL
records manual metrics later
```

Manual fallback is not failure. It is a controlled recovery path.

### Layer 14 — Audit and Metrics

Every transition becomes evidence.

Audit event:

```yaml
automation_audit_event:
  audit_event_id: string
  event_type: research | draft | media_candidate | preview | approval | browser_checkpoint | dispatch | fallback | metrics
  created_at: timestamp
  platform: string | null
  payload_hash: string | null
  media_manifest_hash: string | null
  destination_binding_id: string | null
  adapter_type: string | null
  response_class: success | blocked | failed | unknown | manual_fallback_required
  public_url: string | null
  screenshot_refs: array
  no_secret_output_verified: boolean
  raw_secret_persisted: false
  raw_browser_session_persisted: false
  retry_count: integer
  audit_hash: string
```

Metrics object:

```yaml
metrics_record:
  metrics_id: string
  platform: string
  public_url: string
  posted_at: timestamp
  source: manual_entry | official_api_future | browser_visible_manual_copy
  impressions: integer | null
  likes: integer | null
  comments: integer | null
  shares: integer | null
  saves: integer | null
  opens: integer | null
  clicks: integer | null
  notes: string
  missing_metrics: array
```

No scraping metrics by default. Browser-visible metrics capture can be a manual copy action, not an automated scraper, unless a future read-only metrics gate is built.

---

## 5. Role of OpenClaw and Alternative Browser Engines

The new plan should not ban OpenClaw. It should classify OpenClaw properly.

OpenClaw can be:

```text
a browser automation engine candidate
a rapid prototype tool
a research reference
a lab executor
an adapter backend if it passes controls
```

OpenClaw cannot be:

```text
the ContentOps authority layer
the approval ledger
the dispatcher brain
the credential store
the Telegram runtime
the persistent memory authority
the hidden scheduler
the product's source of truth
```

The same applies to browser-use, Stagehand, Skyvern, plain Playwright, or any other browser automation tool. The engine is replaceable. The ContentOps contracts are not.

The browser engine selection policy:

```yaml
browser_engine_selection:
  openclaw:
    use_when: rapid agentic browser exploration, complex UI navigation, early lab
    risk: broad tool surface, prompt injection, hard-to-audit decisions
    required_controls:
      - bounded plan
      - no secret reads
      - checkpoint required
      - no publish without Jim GO
      - screenshot audit
      - deterministic fallback

  browser_use:
    use_when: robust AI browser navigation, UI exploration, agentic workflows
    risk: similar agentic autonomy concerns
    required_controls:
      - same as OpenClaw

  stagehand:
    use_when: hybrid code plus AI browser actions, productionizing known flows
    risk: still needs destination/payload checks
    required_controls:
      - same as OpenClaw

  playwright_cdp:
    use_when: deterministic replay after workflow stabilizes
    risk: less adaptive to UI changes
    required_controls:
      - selectors versioned
      - visual checkpoints
      - stop on selector drift

  manual:
    use_when: platform UI uncertainty, credential challenge, legal uncertainty, failed automation
    risk: slow
    required_controls:
      - exact copy package
      - manual URL record
```

Preferred strategy:

```text
Use AI browser engine for discovery and lab.
Convert stable flows into deterministic Playwright/CDP where practical.
Keep agentic engine available for UI drift recovery, but require checkpoint and Jim GO.
```

This gives the product speed without sacrificing long-term reliability.

---

## 6. Platform Strategy Under the AI Automation Plan

### 6.1 Substack — Canonical Long-Form and First Browser Automation Target

Substack becomes the canonical publishing target.

Why:

```text
Owned channel.
Long-form authority.
Newsletter distribution.
Central URL for other platforms.
API path is not clearly reliable enough for official-first automation.
Browser compose flow is visually verifiable.
```

Substack automation modes:

```yaml
substack_modes:
  manual_export:
    description: ContentOps produces markdown/html package and Jim posts
    status: fallback

  browser_compose_lab:
    description: browser/CDP opens dashboard, creates article, pastes content, stops before publish
    status: near-term automation target

  browser_supervised_publish:
    description: after checkpoint and Jim GO, browser clicks publish once
    status: first production automation candidate

  unofficial_api_lab:
    description: research-only or test-publication only if browser path fails
    status: secondary
```

Substack Browser Plan:

```text
Open Substack dashboard.
Verify logged-in owner account.
Verify publication destination.
Create new article.
Paste title, subtitle, body.
Attach approved hero image if available.
Set tags/audience/email options.
Capture visible checkpoint.
Compare visible content and media to payload hash inputs.
Ask Jim for GO.
Click publish once.
Capture result URL or route to manual fallback.
```

Stop if:

```text
wrong publication
login required
2FA/magic link required
editor UI changed
title/body mismatch
image mismatch
publish visibility unclear
modal appears
secret visible
URL/result uncertain
```

### 6.2 X — API or Browser Depending Cost and Reliability

X should support:

```text
single post
thread
image post
Substack link post
```

Execution modes:

```text
API if paid access and scopes accepted.
Browser/CDP if API cost or permission is not worth it.
Manual fallback if UI/API blocked.
```

X thread rule:

```text
Thread continuation is allowed only as self-thread payload parts.
No replies to others.
No engagement automation.
No likes, reposts, follows, or DMs.
```

For browser flow:

```text
Open compose.
Verify account handle.
Paste post or thread part.
Attach approved image if applicable.
Checkpoint each thread step.
Click post once per approved outbox item.
If partial thread succeeds and later part fails, route to manual reconciliation.
```

### 6.3 LinkedIn — Professional Distribution

LinkedIn has two separate destinations:

```text
Jim member profile
Capital Chronicle organization/page if available
```

Do not collapse them.

Automation modes:

```text
API if OAuth/scope/role gate is available.
Browser/CDP if API product/scopes are delayed.
Manual fallback for high-risk or role uncertainty.
```

LinkedIn browser flow must verify:

```text
profile/page destination
composer state
body text
media attachment
visibility
no scheduling
no wrong page
```

### 6.4 Telegram — Remote Operator and Channel Destination

Telegram has two roles:

```text
Remote Operator Inbox
Channel Dispatch Destination
```

Remote Operator Inbox:

```text
receives ideas
returns previews
carries approval challenges
returns audit summaries
```

Channel Destination:

```text
publishes approved content to public/private channel
```

Telegram API is likely the first official API live adapter because the Bot API flow is simpler. But Telegram must not become a command shell. It should remain a remote UI plus a channel destination.

### 6.5 Threads — Short-Form Expansion

Threads should be treated as:

```text
short-form derivative of canonical article
text-first if API supports it
browser/CDP fallback if API permission is blocked
no replies/engagement automation
```

Threads profile binding must be separate from Instagram even if the account relationship is shared.

### 6.6 Instagram — Visual-First Distribution

Instagram should not be text-first. The system should require:

```text
approved image or carousel
caption
alt text
hashtags
media rights manifest
platform crop/size constraints
account binding
```

Execution modes:

```text
Meta API if account type, media container, and scopes pass.
Browser/CDP if API is too slow or blocked.
Manual fallback if image rights, account, or UI state is uncertain.
```

Instagram should be a strong candidate for AI Media Agent integration.

### 6.7 Facebook Page — Accessible Summary and Link Distribution

Facebook Page is an expansion platform. It should support:

```text
summary post
link post
image post later
```

No personal profile automation unless explicitly supported by current policy and approved later. Page identity and permission proof are mandatory.

### 6.8 TikTok and YouTube — Media-Heavy Later Stage

TikTok and YouTube are not early automation targets unless media production is ready.

They require:

```text
video asset
thumbnail/cover
title/description/tags
visibility policy
OAuth/app scope
quota or app review state
private/unlisted test mode first
```

AI can generate metadata early, but upload automation should come later.

---

## 7. AI Provider Integration

The previous plan treated provider calls as future-gated. The new plan makes provider integration a core product track.

Provider modes:

```yaml
provider_mode:
  disabled:
    description: no provider call

  manual_external_llm:
    description: Jim pastes model output manually

  approved_provider_editorial:
    description: ContentOps calls LLM provider for research, drafting, rewrite, SEO, platform variants

  approved_provider_browser_planner:
    description: LLM can assist browser action planning but cannot dispatch directly

  local_model:
    description: local LLM for lower-risk classification, draft critique, or offline operation
```

Provider gate requirements:

```text
provider selected
API key present only as credential handle
cost budget defined
prompt redaction policy defined
allowed context classes defined
forbidden context classes defined
output schema defined
copyright/source policy defined
logs redacted
no raw secrets in prompts
no raw proprietary data unless allowed
no model output accepted without validation
```

Prompt families:

```text
idea classifier
research question generator
source summarizer
canonical Substack article writer
SEO optimizer
title/subtitle generator
platform variant writer
image concept generator
media search query generator
claim-risk reviewer
no-signal rewriter
platform-fit critic
approval packet explainer
browser action planner
browser checkpoint evaluator
audit summary writer
```

LLM output must never be accepted directly. It is input to validators.

LLM output contract:

```yaml
llm_output_packet:
  packet_id: string
  provider_mode: string
  model_class: string
  prompt_contract_id: string
  input_refs: array
  output_type: research | draft | rewrite | platform_variant | media_query | browser_plan | critique
  body: object
  schema_valid: boolean
  secret_scan_status: pass | blocked
  citation_status: pass | warning | blocked
  no_advice_status: pass | warning | blocked
  no_signal_status: pass | warning | blocked
  approval_claim_detected: boolean
  dispatch_claim_detected: boolean
  accepted_for_workflow: boolean
  blocked_reasons: array
```

The most important rule:

```text
LLM can propose.
Validators decide eligibility.
Jim approves.
Adapters execute.
Audit records.
```

---

## 8. Browser/CDP Integration Policy

Browser/CDP integration should be a formal product feature, not a hack.

Browser profile policy:

```text
one operator browser profile per platform or group
profile path outside repo or under ignored local runtime directory
no cookie export
no localStorage/sessionStorage read
no DevTools token scraping
no screenshot of secrets
no password handling by AI
2FA/magic link handled by Jim manually
```

Browser automation run types:

```yaml
browser_run_type:
  browse_research:
    description: search/read public pages for research or image candidates
    live_state_change: false

  compose_dry_run:
    description: open platform composer and fill approved content, stop before publish
    live_state_change: no public post

  pre_click_checkpoint:
    description: inspect visible compose state and screenshot evidence
    live_state_change: false

  supervised_publish:
    description: click publish once after Jim GO
    live_state_change: true

  result_reconciliation:
    description: capture URL/status after post
    live_state_change: false

  manual_fallback_assist:
    description: prepare copy/checklist for Jim if automation stops
    live_state_change: operator manual
```

Browser adapter must never say “ready” just because it can open a browser. It is ready only if:

```text
destination verified
payload visible match pass
media visible match pass
visibility pass
no secret visible
publish control identified
Jim GO present
outbox entry ready
kill switch off
audit sink ready
```

---

## 9. Media and Image Strategy

The product should not rely on generic stock images forever. It should build a visual style.

Media types:

```text
licensed/stock images
Creative Commons images with attribution
owned screenshots
AI-generated conceptual images if allowed
internal screenshot-safe report cards
chart-like visual explainers
quote cards
data sufficiency cards
forecast readiness cards
```

The strongest Capital Chronicle visual lane may not be found images. It may be **screenshot-safe visual cards** generated by ContentOps:

```text
uncertainty map
data sufficiency ladder
source quality card
forecast readiness blocked card
macro evidence checklist
no-signal explainer card
```

These visuals are safer than scraped/found images and match the brand. They can feed Instagram, LinkedIn, X, and Substack hero images.

AI Media Agent should therefore support two paths:

```text
external media discovery
internal visual card generation
```

External media requires rights manifest.

Internal visual cards require screenshot-safe content rules:

```text
no fake data
no raw vendor data
no secret info
no misleading market direction
no prediction claims
no fake readiness
```

---

## 10. UI Implications

V5 UI should change from “static governance cockpit” toward “AI automation command center.”

Required rooms:

```text
Command Center
AI Writer Studio
Research Workbench
Canonical Article Studio
Media Studio
Platform Variant Studio
Draft Inspector
Platform Preview
Approval Queue
Browser Operator Console
Publish Readiness Tower
Outbox and Dispatch Control
Evidence Vault
Manual Fallback and Metrics
Settings / Safety / Provider Gates
```

### Command Center

Must answer:

```text
What is the next automation-ready content item?
Which AI tasks are available?
Which browser tasks are waiting for checkpoint?
Which platform gates are cleared?
Which platforms are API, browser, manual, or blocked?
What needs Jim approval?
What failed and needs fallback?
```

### AI Writer Studio

Should support:

```text
prompt template selection
source packet selection
canonical article draft
rewrite controls
SEO panel
audience modes
risk notes
platform adaptation brief
```

### Media Studio

Should support:

```text
image concept generation
image search query list
candidate images
license/rights status
attribution text
platform crop preview
visual card generator
alt text
media manifest approval
```

### Browser Operator Console

This is new.

It should show:

```text
platform
browser engine
profile ID
destination binding
payload hash
media hash
allowed actions
forbidden actions
current browser step
screenshot checkpoint
visible match status
stop condition status
Jim GO button
manual fallback button
audit trail
```

No hidden browser automation. Jim should see exactly what the browser operator is doing.

### Platform Preview

Should show adapter options:

```text
API
Browser/CDP
Manual fallback
```

Each platform card should display:

```text
current mode
destination
credential handle
payload hash
media manifest
approval status
dispatch eligibility
browser checkpoint status
manual fallback status
last audit
```

---

## 11. Roadmap

### Batch A — AI Automation Master Plan and Repo Reconciliation

Purpose:

```text
Commit this new AI-native automation master plan.
Reconcile current repo contracts with new browser/CDP strategy.
Identify existing modules that must be extended.
Create next task sequence.
```

Deliverables:

```text
docs/automation/AI_NATIVE_AUTOMATION_MASTER_PLAN/current_master_plan.md
docs/automation/AI_NATIVE_AUTOMATION_MASTER_PLAN/repo_gap_map.md
docs/automation/AI_NATIVE_AUTOMATION_MASTER_PLAN/next_task_sequence.md
```

No code changes except docs.

### Batch B — Provider Gate and Prompt Template Registry

Build:

```text
AI provider gate
prompt template registry
prompt contract schemas
provider cost budget
secret redaction tests
LLM output validator
```

Goal:

```text
LLM provider integration becomes usable for drafting/rewrite/SEO/research under controlled budget.
```

### Batch C — Canonical Article and SEO Workflow

Build:

```text
canonical Substack article object
SEO packet
article draft validator
source/citation preservation tests
Writer Studio read model
```

Goal:

```text
Given a topic and source packet, ContentOps can generate a review-only canonical Substack draft.
```

### Batch D — Media Discovery and Rights Manifest

Build:

```text
Media concept generator contract
image search query packet
media candidate metadata schema
media rights manifest
alt text contract
visual card generator contract
rights-gate tests
```

Goal:

```text
Images become safe, hashable, auditable content inputs.
```

### Batch E — Platform Variant Generator

Build:

```text
platform variant set
X thread model
LinkedIn member/org variants
Telegram post
Threads post
Instagram caption/carousel plan
Facebook Page post
TikTok/YouTube metadata placeholders
```

Goal:

```text
Canonical Substack article becomes platform-native derivative payloads.
```

### Batch F — Draft Inspector V2

Build:

```text
claim-risk scanner
no-advice/no-signal scanner
source/citation checker
platform constraints validator
media manifest validator
approval eligibility report
```

Goal:

```text
AI output becomes inspection-ready and blocked when unsafe.
```

### Batch G — Browser Automation Plan Contract

Build:

```text
BrowserAutomationPlan
VisualComposeCheckpoint
BrowserDispatchAdapter contract
Browser profile registry
Stop condition registry
No-cookie/no-session/no-DOM-token tests
```

Goal:

```text
Browser/CDP automation becomes a formal adapter type.
```

### Batch H — Substack Browser Compose Dry Run

Build:

```text
Substack browser profile binding
Substack compose plan
open dashboard
create article
paste title/body
attach approved image if available
pre-click checkpoint
manual fallback package
```

No live publish yet unless explicitly approved later.

### Batch I — Substack Supervised Publish Pilot

Requirements:

```text
test/private publication preferred
approved payload hash
media manifest pass
destination binding pass
browser checkpoint pass
Jim GO
one click
audit
URL capture
manual fallback
```

Goal:

```text
First browser/CDP supervised publish proof.
```

### Batch J — X API/Browser Decision Gate

Build:

```text
X mode decision: API vs browser vs manual
X browser compose plan if API blocked
X thread outbox model
partial-success reconciliation
```

Goal:

```text
X becomes usable by some path, not ambiguous.
```

### Batch K — LinkedIn Browser/API Gate

Build:

```text
member profile binding
organization/page binding
API scope check if available
browser compose flow if API blocked
checkpoint and manual fallback
```

Goal:

```text
LinkedIn member and org are separate automation rows.
```

### Batch L — Meta Family Browser/API Gate

Build:

```text
Facebook Page
Instagram Professional
Threads
Meta docs registry refresh
browser/API mode classification
media-first Instagram plan
```

Goal:

```text
Meta family platforms become classified as API/browser/manual/blocked.
```

### Batch M — Telegram Remote Operator + Automation Notifications

Build:

```text
Telegram idea intake
draft preview return
approval challenge
browser checkpoint notification
dispatch result notification
manual fallback notification
```

Goal:

```text
Jim can supervise automation remotely.
```

### Batch N — Multi-Platform Campaign Orchestration

Build:

```text
campaign object
canonical article plus variants
selected platforms
batch approval
per-platform outbox entries
API/browser/manual routing
partial success handling
```

Goal:

```text
One idea becomes a supervised campaign across selected platforms.
```

### Batch O — Metrics Capture

Build:

```text
URL record
manual metrics entry
platform metrics placeholders
read-only API future gates
performance summary
content iteration recommendations
```

Goal:

```text
ContentOps learns what worked without scraping or engagement automation.
```

### Batch P — Red-Team Harness

Test:

```text
LLM says approved
LLM says posted
browser account mismatch
payload changed after checkpoint
media license unknown
cookie visible
2FA appears
wrong publication selected
X partial thread failure
LinkedIn org/member mismatch
Instagram media missing
duplicate publish request
unknown result after click
manual fallback recovery
```

Goal:

```text
Automation is fast but fail-closed.
```

### Batch Q — V5 UI Automation Command Center

Build UI:

```text
AI Writer Studio
Media Studio
Browser Operator Console
Platform Preview
Approval Queue
Outbox
Evidence Vault
Publish Readiness Tower
Manual Fallback
Metrics
```

Goal:

```text
Jim can run the system like an AI-native content operations desk.
```

---

## 12. Acceptance Criteria

The AI-native automation product is accepted only when:

```text
LLM provider gate is explicit and redacted.
Prompt templates are versioned.
LLM outputs are schema-validated.
Research packets preserve sources and uncertainty.
Canonical Substack article generation works.
SEO packet generation works.
Media discovery produces rights manifests.
Platform variants preserve limitations and no-signal rules.
Draft Inspector blocks unsafe claims.
Payload preview equals dispatch input.
Payload hash includes text, media, destination, visibility, adapter version, and policy snapshot.
Jim approval is exact and append-only.
Browser automation requires a plan.
Browser automation cannot read cookies/session/localStorage.
Browser automation stops on destination or payload uncertainty.
Browser automation requires pre-click checkpoint.
Supervised publish requires Jim GO.
Official API adapters require endpoint/method/host/request budget gates.
Outbox prevents duplicate dispatch.
Kill switch blocks all live actions.
Manual fallback exists for every platform.
Audit records every step.
No hidden scheduler exists.
No autonomous replies/DMs exist.
No engagement automation exists.
No scraping metrics by default.
UI shows API/browser/manual/blocked modes clearly.
```

---

## 13. Final Product Definition

The final product is not simply a safer manual publishing assistant. It is an AI-native content automation platform.

A complete version can:

```text
take a Jim idea
research it
write a canonical Substack article
improve SEO
find or create media candidates
validate rights
generate platform variants
inspect claims
render exact previews
lock payload hashes
ask Jim for approval
operate browser/API adapters
publish selected approved payloads
record public URLs
capture metrics
learn from performance
preserve audit evidence
fall back manually when automation is blocked
```

The correct final posture:

```text
Automation is default.
Approval is mandatory.
Manual is fallback.
Audit is permanent.
AI is powerful but never authority.
Browser/CDP is a first-class adapter but never a secret-reading black box.
```

This plan keeps the safety architecture but removes unnecessary hesitation. Capital Chronicle ContentOps should move quickly toward AI-native production, because the core value is not merely controlling risk. The core value is turning serious macro thinking into disciplined, high-quality public distribution at a speed and consistency that manual workflows cannot match.
