# Capital Chronicle ContentOps V6 — Final Product 25-Task Execution Plan

## Product Goal

Build Capital Chronicle ContentOps V6 as an AI-native editorial, publishing, and community operating system.

The final product is not a generic scheduler, social bot, or manual publishing checklist. It is a controlled production loop:

```text
Jim idea / source / research context / future artifact
→ AI research and grounding
→ canonical Substack article
→ SEO and editorial refinement
→ platform-native variants
→ Discord community drop
→ Telegram/operator checkpoint
→ webhook/API/browser/manual dispatch
→ public URL and audit record
→ community feedback and questions
→ LLM summary and content backlog
→ next canonical article
```

The final product is accepted when ContentOps can reliably perform this loop:

```text
Idea → AI draft → canonical article → Discord drop → variants → approval → dispatch → audit → feedback → next idea
```

The final product does not require every external platform to be fully live. X can remain manual. LinkedIn can remain deferred until verification. TikTok can remain deferred. Discord bot/slash commands can remain deferred until after the final product. The final product does require the AI production loop, canonical article workflow, Discord webhook dispatch, Telegram operator lane, approval/outbox/audit controls, and V6 UI command surface.

---

# Phase 0 — Baseline, Governance, and V6 Product Commitment

## Purpose

Lock the new V6 direction into the repo, prevent future tasks from drifting back into the old manual-first/platform-only model, and create a clean execution lane for the remaining tasks.

## Phase outcome

After Phase 0, the repo has a committed V6 plan, a 25-task ledger, final acceptance definitions, credential capability inventory, and clear boundaries around live writes, webhooks, browser/CDP, and LLM provider use.

---

## Task 01 — V6 Master Plan Commit and Supersession Map

### Objective

Commit the V6 master plan as the current product authority and mark prior master plans as superseded or historical where appropriate.

### Implementation scope

Create or update:

```text
docs/Capital Chronicle ContentOps V6 — AI-Native Editorial, Publishing, and Community Operating System Master Plan.md
docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_supersession_map.md
docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_25_task_ledger.md
docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md
```

### Details

The task must make it explicit that:

```text
Substack = canonical long-form authority.
Discord = community feedback flywheel.
Telegram = remote operator lane.
LLM = production engine.
Webhooks = first Discord live adapter.
Browser/CDP = supervised adapter, never secret-reading/selfbot.
Manual = fallback.
Jim = final authority.
Discord bot = after final product.
```

It should also document which older docs are still useful:

```text
V5 UI north star = useful UI/design reference.
AI-native automation plan = foundation.
V6 plan = current strategic authority.
Operating rules = evidence/safety authority.
```

### Tests / validation

Docs-only validation is enough unless the repo has doc lint. Must run:

```text
git status
git diff --name-status
```

### Acceptance criteria

* V6 plan is committed.
* Supersession map exists.
* 25-task ledger exists.
* No `.env`, secrets, local browser profiles, screenshots, or credential files are staged.
* Evidence packet names current HEAD and changed files.

---

## Task 02 — Unified Redacted Credential Capability Matrix

### Objective

Build a single read-only credential capability matrix that classifies every platform and adapter according to current readiness.

### Implementation scope

Create:

```text
live_contentops/unified_credential_capability_matrix.py
tests/test_unified_credential_capability_matrix.py
docs/automation/V6_CREDENTIAL_CAPABILITY_MATRIX/redacted_capability_matrix_packet.json
docs/automation/V6_CREDENTIAL_CAPABILITY_MATRIX/implementation_report.md
```

### Required platform rows

```text
Discord webhooks
Telegram operator inbox
Telegram channel
Substack browser profile
Meta Graph
Facebook Page
Instagram Business
Threads
YouTube
X manual
LinkedIn personal deferred
LinkedIn organization deferred
TikTok deferred
AI provider / 9router
Vertex fallback
Browser operator profiles
Media dirs
Approval/outbox/audit paths
```

### Capability classes

```text
ready_webhook
ready_api
ready_browser
manual_only
deferred_credentials_missing
deferred_review_required
blocked_policy
disabled
unknown
```

### Output restrictions

The matrix must output only:

```text
key names
present/missing booleans
platform family
credential handle ID
destination binding ID
capability class
blocker class
deferred reason
live-write eligibility
```

It must never output:

```text
raw token
webhook URL
secret value
token length
token prefix/suffix
token digest/hash
cookie
session data
localStorage
browser user token
private key
```

### Acceptance criteria

* Actual `.env` can be inspected structurally without printing values.
* Discord rows include channel IDs and webhook handle IDs without webhook URLs.
* X/LinkedIn/TikTok deferred state is not treated as failure.
* Credential capability matrix becomes the canonical readiness input for later tasks.

---

## Task 03 — V6 Platform Universe and Adapter Taxonomy Reconciliation

### Objective

Reconcile platform IDs, destination binding IDs, payload classes, and adapter classes under the V6 platform taxonomy.

### Implementation scope

Update or extend:

```text
live_contentops/platform_universe_registry_v2.py
live_contentops/platform_account_binding_registry_v2_contract.py
live_contentops/primary_payload_classes_contract.py
tests/test_platform_universe_registry_v2.py
tests/test_platform_account_binding_registry_v2_contract.py
```

Only modify existing files if they are the correct current registry files. Do not rewrite unrelated registry work.

### Platform taxonomy

```text
owned_long_form:
  substack

community:
  discord

remote_operator:
  telegram

social_distribution:
  x_manual
  linkedin_personal_deferred
  linkedin_org_deferred
  threads
  facebook_page
  instagram_business

media_video_later:
  youtube
  tiktok_deferred

provider:
  nine_router
  vertex
```

### Adapter taxonomy

```text
webhook_adapter
official_api_adapter
browser_cdp_adapter
manual_fallback_adapter
deferred_adapter
```

### Acceptance criteria

* Registry can classify every current platform.
* Discord webhook adapter class exists.
* Discord bot is marked deferred.
* X manual, LinkedIn deferred, TikTok deferred are valid states, not blockers.
* Tests prove old/legacy names do not accidentally route to live write.

---

# Phase 1 — Discord Webhook Foundation and First Safe Live Adapter

## Purpose

Make Discord webhook-first distribution real, safe, and auditable. This is the first live community adapter because the server, channel IDs, role IDs, and webhook URLs already exist locally.

## Phase outcome

After Phase 1, ContentOps can generate a safe Discord payload, hash it, bind it to the right channel, approve it, dispatch through a webhook, and record a redacted audit event without exposing webhook URLs.

---

## Task 04 — Discord Environment and Binding Contract

### Objective

Formalize Discord server, channel, role, webhook, credential handle, and destination binding structure.

### Implementation scope

Create:

```text
live_contentops/discord_environment_contract.py
tests/test_discord_environment_contract.py
docs/automation/DISCORD_ENVIRONMENT_CONTRACT/discord_environment_packet.json
docs/automation/DISCORD_ENVIRONMENT_CONTRACT/implementation_report.md
```

### Contract must support

```text
DISCORD_GUILD_ID / DISCORD_SERVER_ID
DISCORD_GUILD_NAME
DISCORD_AUTOMATION_MODE=webhook_first
DISCORD channel IDs
DISCORD role IDs
DISCORD webhook credential handles
DISCORD destination binding IDs
DISCORD bot deferred placeholders
DISCORD_MESSAGE_CONTENT_INTENT_ENABLED=false
```

### Tests must prove

* Discord webhook URL keys are recognized as secrets.
* Channel IDs are not secrets.
* Role IDs are not secrets.
* Webhook URLs are never returned in reports.
* Bot placeholders can remain empty.
* Message content intent is false by default.

### Acceptance criteria

* Discord environment contract passes on local `.env`.
* No webhook URL appears in stdout, docs, packets, or tests.
* Discord is classified as `ready_webhook`.

---

## Task 05 — Discord Webhook Payload Schema and Dry-Run Renderer

### Objective

Build the schema and dry-run renderer for Discord messages without making live requests.

### Implementation scope

Create:

```text
live_contentops/discord_webhook_payload_contract.py
tests/test_discord_webhook_payload_contract.py
docs/automation/DISCORD_WEBHOOK_PAYLOAD_CONTRACT/sample_payloads.json
docs/automation/DISCORD_WEBHOOK_PAYLOAD_CONTRACT/implementation_report.md
```

### Payload types

```text
announcement
substack_drop
product_update
operator_private_summary
manual_fallback_notice
audit_summary_redacted
```

### Discord drop format

```text
Title:
One-line thesis:
Why it matters:
Read the full article:
Discussion question:
Disclosure:
```

### Safety checks

Block payloads with:

```text
financial advice
buy/sell/hold
price target
position sizing
guaranteed prediction
model says / signal says
raw secret-looking values
webhook URL
cookie/session/localStorage terms
```

### Acceptance criteria

* Renderer creates valid webhook payload JSON.
* Renderer has dry-run output that is human-readable.
* No webhook URL appears.
* Tests include unsafe finance-language blockers.
* Tests include no-secret payload proof.

---

## Task 06 — Discord Destination Binding + Payload Hash

### Objective

Bind every Discord payload to exact target channel, credential handle, payload class, and payload hash.

### Implementation scope

Create or extend:

```text
live_contentops/discord_payload_hash_contract.py
tests/test_discord_payload_hash_contract.py
docs/automation/DISCORD_PAYLOAD_HASH_CONTRACT/hash_packet.json
```

### Hash inputs

```text
payload text
payload type
guild ID
channel ID
destination binding ID
credential handle ID
adapter type
policy snapshot
content source ID
media manifest ID if any
```

### Forbidden hash inputs

```text
webhook URL
webhook token
raw secrets
cookie/session/localStorage
browser profile path
token digest/prefix/suffix
```

### Acceptance criteria

* Any payload text change changes hash.
* Any channel binding change changes hash.
* Webhook URL never enters hash.
* Same payload/destination produces deterministic hash.
* Test proves Discord webhook URL is excluded.

---

## Task 07 — Discord Webhook Dispatch Outbox Dry Run

### Objective

Create outbox entries for Discord webhook dispatch without sending live requests.

### Implementation scope

Create:

```text
live_contentops/discord_webhook_outbox_contract.py
tests/test_discord_webhook_outbox_contract.py
docs/automation/DISCORD_WEBHOOK_OUTBOX_DRY_RUN/outbox_packet.json
```

### Required outbox fields

```text
outbox_id
platform=discord
adapter_type=webhook_adapter
payload_id
payload_hash
destination_binding_id
credential_handle_id
channel_id
approval_required
request_budget=1
auto_retry_allowed=false
kill_switch_required=true
status
blocked_reasons
```

### Acceptance criteria

* Outbox refuses unapproved payloads.
* Outbox refuses missing destination binding.
* Outbox refuses missing credential handle.
* Outbox marks webhook URL as required at runtime but never prints it.
* Dry-run packet is redacted.

---

## Task 08 — Discord Webhook Live Pilot

### Objective

Send one approved controlled test message through a Discord webhook and record a redacted audit event.

### Live scope

Live write allowed only for this task and only after explicit Jim approval in the task prompt.

### Recommended test target

Use:

```text
#product-updates
```

Payload:

```text
Capital Chronicle ContentOps test dispatch.

This is a supervised webhook test for the V6 Discord community layer.
No financial advice. No trading signal. No automation bot is active.
```

### Implementation scope

Create:

```text
live_contentops/discord_webhook_dispatcher.py
tests/test_discord_webhook_dispatcher_redaction.py
docs/automation/DISCORD_WEBHOOK_LIVE_PILOT/live_pilot_report.md
docs/automation/DISCORD_WEBHOOK_LIVE_PILOT/redacted_audit_event.json
```

### Live constraints

```text
host allowlist: discord.com / discordapp.com webhook endpoint family
method: POST
request budget: 1
auto retry: false
timeout: fixed
payload hash required
approval required
kill switch checked
no webhook URL printed
no response body secrets printed
```

### Acceptance criteria

* One message posts successfully or fails with clear result class.
* Audit records target channel ID, payload hash, result class.
* Audit does not record webhook URL.
* Manual verification instructions are included.
* No retry if result uncertain.

---

## Task 24A — X CDP Identity Capture Proof and Guard Promotion

### Objective

Carry the TASK 0087AD live X lesson into the final-product roadmap without making X API a launch dependency.

### Accepted evidence

```text
TASK 0087AD proved: standard ContentOps Edge profile + CDP port 9223 can create a supervised X root post, capture browser-visible public URL, write platform publication identity, verify parent post, and write a reply identity record.
```

### Product caveat

```text
TASK 0087AE must guard the active CDP process/profile before reuse.
Block Antigravity Chrome or unknown profiles before any live click.
Do not read cookies, localStorage, sessionStorage, authorization headers, tokens, DOM dumps, or screenshots containing secrets.
```

### Launch-era policy

```text
X remains Tier 2 supervised browser/CDP assist.
Paid X API is not required for final-product acceptance.
```

---

# Phase 2 — AI Production Engine

## Purpose

Build the LLM-first content engine: prompt registry, provider gate, research grounding, canonical article object, SEO/editorial optimizer, Discord drop generator, and platform variants.

## Phase outcome

After Phase 2, Jim can enter a topic and ContentOps can produce review-only research packets, canonical Substack drafts, Discord drops, Telegram posts, X manual drafts, LinkedIn deferred drafts, Threads/Facebook/Instagram variants, and inspection packets.

---

## Task 09 — AI Provider Gate and Prompt Registry

### Objective

Create the provider-gated LLM layer for V6 workflows.

### Implementation scope

Create:

```text
live_contentops/ai_provider_gate.py
live_contentops/prompt_template_registry_v6.py
tests/test_ai_provider_gate.py
tests/test_prompt_template_registry_v6.py
docs/automation/V6_AI_PROVIDER_GATE/provider_gate_packet.json
```

### Prompt families

```text
idea_classifier
research_question_generator
research_brief_writer
canonical_substack_writer
seo_optimizer
discord_drop_writer
telegram_post_writer
platform_variant_writer
media_concept_writer
draft_inspector_explainer
community_signal_summarizer
manual_fallback_writer
```

### Provider modes

```text
disabled
dry_run_stub
nine_router_live
vertex_fallback
manual_external_llm
```

### Acceptance criteria

* Provider gate reads credential presence without printing values.
* Prompt templates are versioned.
* Prompt redaction policy exists.
* Live provider call is disabled unless explicitly allowed.
* LLM output is schema-wrapped.

---

## Task 10 — Operator Intent and Content Idea Packet

### Objective

Turn Jim’s natural-language request into structured content intent.

### Implementation scope

Create:

```text
live_contentops/operator_intent_contract.py
live_contentops/content_idea_packet.py
tests/test_operator_intent_contract.py
docs/automation/V6_OPERATOR_INTENT/sample_intents.json
```

### Intent classes

```text
create_canonical_article
summarize_source
create_discord_drop
create_platform_variants
create_product_update
create_research_question_backlog
inspect_draft
approve_payload
reject_payload
request_manual_fallback
request_webhook_dispatch
request_audit_summary
```

### Acceptance criteria

* Intent is not approval.
* Approval intent requires exact payload hash.
* Ambiguous live-write language is blocked.
* Unsafe finance signal requests are blocked or rewritten into educational framing.
* Community questions can become content ideas.

---

## Task 11 — Research Grounding Packet

### Objective

Build deterministic structure around AI research.

### Implementation scope

Create:

```text
live_contentops/research_grounding_packet.py
tests/test_research_grounding_packet.py
docs/automation/V6_RESEARCH_GROUNDING/sample_research_packets.json
```

### Packet fields

```text
topic
source_mode
source_refs
official_source_refs
non_official_source_refs
freshness_status
source_quality_status
missing_evidence
safe_angles
unsafe_angles
required_caveats
no_signal_status
no_advice_status
allowed_for_drafting
allowed_for_publication
blocked_reasons
```

### Acceptance criteria

* Source missing state is preserved.
* Unknown freshness blocks public-ready state.
* Unsupported claims are not allowed through.
* AI may summarize but not invent source refs.
* Research packet is suitable input for canonical article generation.

---

## Task 12 — Canonical Substack Article Workflow

### Objective

Build the canonical long-form article object and review-only article generator.

### Implementation scope

Create:

```text
live_contentops/canonical_article_workflow.py
tests/test_canonical_article_workflow.py
docs/automation/V6_CANONICAL_ARTICLE/sample_article_packet.json
```

### Article fields

```text
article_id
research_packet_id
title
subtitle
slug_candidate
lede
body_markdown
section_map
citations
limitations
disclosure
media_request
seo_packet_id
draft_status
human_review_required
```

### Acceptance criteria

* Article remains review-only.
* Citation placeholders cannot be fake IDs.
* No financial advice.
* No forecast authority claim unless future artifact permits it.
* Limitations section is required.
* Source uncertainty is preserved.

---

## Task 13 — SEO and Editorial Optimization

### Objective

Add SEO and editorial intelligence without removing caveats.

### Implementation scope

Create:

```text
live_contentops/seo_editorial_packet_v6.py
tests/test_seo_editorial_packet_v6.py
docs/automation/V6_SEO_EDITORIAL/sample_seo_packet.json
```

### SEO output

```text
primary keyword
secondary keywords
search intent
title candidates
subtitle candidates
slug candidates
meta description
readability score
editorial score
audience fit score
rejected clickbait
limitations_preserved
```

### Acceptance criteria

* SEO output cannot remove caveats.
* Clickbait market-call titles are rejected.
* No price-target/trade-call phrasing.
* SEO packet links to canonical article ID.
* Output remains review-only.

---

## Task 14 — Discord Drop Generator

### Objective

Generate Discord-native community drops from canonical articles.

### Implementation scope

Create:

```text
live_contentops/discord_drop_generator.py
tests/test_discord_drop_generator.py
docs/automation/V6_DISCORD_DROP_GENERATOR/sample_drops.json
```

### Required drop types

```text
substack_drop
product_update
announcement
research_question_prompt
build_in_public_update
```

### Required fields

```text
title
one_line_thesis
why_it_matters
summary
discussion_question
source_link
disclosure
target_channel
payload_hash_candidate
```

### Acceptance criteria

* Discord drop is community-oriented, not just a link dump.
* Discussion question is required.
* Disclosure is required.
* Unsafe financial language is blocked.
* Drop can be routed to correct Discord channel class.

---

## Task 15 — Platform Variant Generator V6

### Objective

Generate platform-native variants from canonical article and Discord drop.

### Implementation scope

Create:

```text
live_contentops/platform_variant_generator_v6.py
tests/test_platform_variant_generator_v6.py
docs/automation/V6_PLATFORM_VARIANTS/sample_variant_set.json
```

### Platforms

```text
substack
discord
telegram
x_manual
linkedin_personal_deferred
linkedin_org_deferred
threads
facebook_page
instagram_business
youtube_metadata_future
tiktok_metadata_deferred
```

### Acceptance criteria

* Execution readiness is separate from generation.
* X manual variant is generated but not auto-dispatchable.
* LinkedIn variants are generated but deferred.
* TikTok metadata can be generated but deferred.
* Discord bot is not required.
* No unsafe finance language passes.

---

# Phase 3 — Safety, Approval, Outbox, and Multi-Adapter Dispatch

## Purpose

Unify payload preview, draft inspection, payload hash, approval ledger, outbox, adapters, and audit. This makes live writes safe.

## Phase outcome

After Phase 3, ContentOps can prepare and dispatch only approved, hashed, destination-bound payloads through Discord webhook, Telegram API, Substack browser/manual, or manual fallback.

---

## Task 16 — Draft Inspector V2

### Objective

Validate all article, Discord, Telegram, and platform variants before approval.

### Implementation scope

Create or extend:

```text
live_contentops/draft_inspector_v2.py
tests/test_draft_inspector_v2.py
docs/automation/V6_DRAFT_INSPECTOR/inspection_packet.json
```

### Checks

```text
unsupported claims
missing citations
no-advice violations
no-signal violations
source freshness
market prediction language
model authority leakage
trade/execution language
content lane mismatch
platform constraints
media rights
Discord tone
community safety
disclosure presence
```

### Acceptance criteria

* Unsafe payloads are blocked.
* Warnings and blockers are separated.
* Discord-specific safety exists.
* Inspector does not mutate text.
* LLM may explain but cannot override result.

---

## Task 17 — Unified Payload Preview and Hash Lock

### Objective

Create exact previews and deterministic hashes for every platform payload.

### Implementation scope

Create:

```text
live_contentops/payload_preview_hash_v6.py
tests/test_payload_preview_hash_v6.py
docs/automation/V6_PAYLOAD_HASH/hash_samples.json
```

### Supported payloads

```text
Discord webhook payload
Telegram message
Substack article package
X manual post/thread
LinkedIn deferred post
Threads post
Facebook Page post
Instagram caption/media plan
YouTube metadata
TikTok metadata deferred
```

### Acceptance criteria

* Changing text changes hash.
* Changing destination changes hash.
* Changing adapter changes hash.
* Webhook URLs never enter hash.
* Browser profile path never enters hash.
* Exact preview is available for Jim review.

---

## Task 18 — Approval Ledger V6

### Objective

Bind Jim approval to exact payload hashes and destination bindings.

### Implementation scope

Create or extend:

```text
live_contentops/approval_ledger_v6.py
tests/test_approval_ledger_v6.py
docs/automation/V6_APPROVAL_LEDGER/sample_approval_packet.json
```

### Required approval fields

```text
approval_id
operator_id
payload_id
payload_hash
destination_binding_id
credential_handle_id
adapter_type
media_manifest_hash
approved_at
expires_at
revoked
valid_for_outbox
valid_for_dispatch
```

### Acceptance criteria

* Approval cannot exist without payload hash.
* Approval cannot exist without destination binding.
* Text edits invalidate approval.
* Destination changes invalidate approval.
* Approval does not dispatch directly.
* Approval packet contains no secrets.

---

## Task 19 — Dispatch Outbox V6

### Objective

Create the dispatch outbox that supports webhook/API/browser/manual adapter classes.

### Implementation scope

Create:

```text
live_contentops/dispatch_outbox_v6.py
tests/test_dispatch_outbox_v6.py
docs/automation/V6_DISPATCH_OUTBOX/sample_outbox_packet.json
```

### Adapter classes

```text
webhook_adapter
official_api_adapter
browser_cdp_adapter
manual_fallback_adapter
deferred_adapter
```

### Acceptance criteria

* Outbox accepts only approved payloads.
* Outbox blocks kill switch.
* Outbox enforces request budget.
* Outbox blocks auto retry by default.
* Outbox distinguishes dispatched, failed, unknown, manual fallback required.
* Deferred platforms can generate outbox-disabled records for planning.

---

## Task 20 — Telegram + Discord Operator Bridge

### Objective

Create redacted operator notifications across Telegram and private Discord operator channels.

### Implementation scope

Create:

```text
live_contentops/operator_bridge_v6.py
tests/test_operator_bridge_v6.py
docs/automation/V6_OPERATOR_BRIDGE/sample_operator_notifications.json
```

### Notification types

```text
draft_ready
approval_required
webhook_dispatch_ready
dispatch_success
dispatch_failed
browser_checkpoint_required
manual_fallback_required
audit_summary
```

### Acceptance criteria

* Telegram remains primary remote operator lane.
* Discord private operator channels receive redacted summaries only.
* No raw payload secrets.
* No webhook URLs.
* No token values.
* No autonomous approval via Discord bot.

---

## Task 21 — Substack Browser Compose Dry Run

### Objective

Prepare Substack browser/CDP compose workflow without live publish.

### Implementation scope

Create or extend:

```text
live_contentops/substack_browser_compose_plan.py
tests/test_substack_browser_compose_plan.py
docs/automation/V6_SUBSTACK_BROWSER_DRY_RUN/compose_plan_packet.json
```

### Allowed actions

```text
open dashboard
verify publication URL
create new post
paste title/subtitle/body
attach approved media if available
capture checkpoint
stop before publish
```

### Forbidden actions

```text
read cookies
read localStorage/sessionStorage
export profile
click publish without Jim GO
change publication
alter approved payload
```

### Acceptance criteria

* Dry-run plan is generated.
* Browser checkpoint schema exists.
* Publish is blocked.
* Manual fallback package exists.
* No browser secrets are read.

---

# Phase 4 — Campaign Loop, Media, Community Feedback, and Metrics

## Purpose

Close the production loop. A single idea becomes a campaign, goes through approval/outbox/dispatch, and returns feedback into the backlog.

## Phase outcome

After Phase 4, ContentOps can create campaign objects, handle media/visual cards, ingest manual Discord feedback, and record metrics.

---

## Task 22 — Multi-Platform Campaign Object

### Objective

Create the campaign object that groups one canonical article, variants, Discord drops, outbox entries, dispatch results, metrics, and feedback.

### Implementation scope

Create:

```text
live_contentops/campaign_v6.py
tests/test_campaign_v6.py
docs/automation/V6_CAMPAIGN_OBJECT/sample_campaign.json
```

### Campaign fields

```text
campaign_id
canonical_article_id
selected_platforms
discord_drop_ids
variant_set_id
approval_packet_id
outbox_entries
dispatch_results
metrics_records
feedback_summary
status
```

### Acceptance criteria

* Campaign can include ready, manual, and deferred platforms.
* Campaign can be approved per-payload or as a bundle only if exact hashes are locked.
* Discord drop is first-class.
* Campaign status reflects blockers.

---

## Task 23 — Media Rights and Internal Visual Card System

### Objective

Build safe media handling and internal visual card workflow.

### Implementation scope

Create:

```text
live_contentops/media_rights_manifest_v6.py
live_contentops/internal_visual_card_packet.py
tests/test_media_rights_manifest_v6.py
tests/test_internal_visual_card_packet.py
docs/automation/V6_MEDIA_SYSTEM/sample_media_manifest.json
```

### Supported media

```text
internal visual cards
article quote cards
data sufficiency cards
source trust cards
forecast readiness blocked cards
rights-checked external images
hero image candidates
thumbnail candidates
```

### Acceptance criteria

* External media requires rights status.
* Internal cards cannot contain fake numbers.
* Internal cards cannot contain secrets.
* Alt text required.
* Media hash participates in payload hash.
* Media not required for non-media platforms.

---

## Task 24 — Community Signal Intake and Feedback Summary

### Objective

Turn manually selected Discord questions/feedback into structured content backlog.

### Implementation scope

Create:

```text
live_contentops/community_signal_intake_v6.py
live_contentops/discord_feedback_summary_v6.py
tests/test_community_signal_intake_v6.py
tests/test_discord_feedback_summary_v6.py
docs/automation/V6_COMMUNITY_SIGNAL/sample_signal_packets.json
```

### Input modes

```text
manual_paste
operator_note
future_slash_command
future_bot_export
```

### Signal fields

```text
source_channel_id
input_mode
question_text
theme
content_potential
required_sources
safe_angle
unsafe_angle
recommended_next_action
backlog_candidate
```

### Acceptance criteria

* No bot required.
* No message scraping.
* No private message ingestion.
* Community input cannot become factual claim without research grounding.
* LLM can summarize but cannot approve next content.

---

## Task 25 — Metrics, Final V6 UI Command Center, Red-Team, and Release Evidence

### Objective

Finish the product by building the operator-facing V6 command center, metrics/feedback view, red-team harness, and release evidence packet.

### Implementation scope

This is the final integration task. It can be split internally by Antigravity, but should ship as one final release milestone.

Create or update:

```text
ui/contentops_v6/
live_contentops/v6_release_readiness.py
tests/test_v6_release_readiness.py
docs/automation/V6_FINAL_RELEASE/final_release_evidence_packet.json
docs/automation/V6_FINAL_RELEASE/red_team_report.md
docs/automation/V6_FINAL_RELEASE/browser_qa_report.md
docs/automation/V6_FINAL_RELEASE/final_acceptance_record.md
```

### UI rooms

```text
Command Center
AI Writer Studio
Research Workbench
Canonical Article Studio
Platform Variant Studio
Discord Community Console
Media Studio
Draft Inspector
Platform Preview
Approval Queue
Dispatch Outbox
Browser Operator Console
Evidence Vault
Metrics and Feedback
Settings / Credential Capability Matrix
```

### Metrics support

```text
manual metrics entry
Discord feedback summary
Substack URL record
Discord message URL or result class
Telegram dispatch result
manual X/LinkedIn URL record
campaign performance notes
```

### Red-team cases

```text
webhook URL leak attempt
wrong Discord channel
missing approval
payload changed after approval
selfbot attempt
browser cookie read attempt
community signal becomes unsupported claim
LLM claims approval
LLM claims dispatch success
bot credentials absent
manual fallback required
kill switch active
X manual state misread as API-ready
LinkedIn deferred state misread as ready
TikTok deferred state misread as ready
```

### Final acceptance criteria

The final product passes if:

```text
V6 master plan committed.
Credential capability matrix works.
Discord webhook contract works.
Discord webhook live pilot has passed or is ready with approval.
AI provider gate and prompt registry exist.
Canonical article workflow exists.
Discord drop generator exists.
Platform variants exist.
Draft Inspector blocks unsafe content.
Payload hash and approval ledger work.
Dispatch outbox supports webhook/API/browser/manual.
Telegram + Discord operator bridge works in redacted mode.
Substack browser dry-run plan exists.
Campaign object exists.
Media rights/internal card system exists.
Community signal intake exists.
Metrics/feedback loop exists.
V6 UI command center exists.
Red-team report passes.
No raw secrets are printed or committed.
Discord bot remains deferred until after final product.
```

### Final product definition

ContentOps V6 is final when Jim can do this:

```text
Give one serious content idea.
Receive a grounded research packet.
Generate a canonical Substack article.
Generate SEO metadata.
Generate a Discord drop.
Generate Telegram and other platform variants.
Inspect all payloads for safety.
Approve exact payload hashes.
Dispatch to Discord webhook and Telegram, or prepare manual/browser fallback.
Record audit.
Capture feedback.
Turn feedback into next backlog item.
```

That is the product. Everything after this is expansion.

---

# Phase Summary

## Phase 0 — Baseline and Governance

Tasks 01–03.

Locks V6 direction, capability model, and platform taxonomy.

## Phase 1 — Discord Webhook Foundation

Tasks 04–08.

Makes Discord webhook-first distribution real, safe, and auditable.

## Phase 2 — AI Production Engine

Tasks 09–15.

Builds LLM gate, research grounding, canonical article workflow, SEO, Discord drop generation, and platform variants.

## Phase 3 — Safety and Dispatch Core

Tasks 16–21.

Builds Draft Inspector, payload hash, approval ledger, outbox, operator bridge, and Substack browser dry-run.

## Phase 4 — Campaign, Feedback, and Final Release

Tasks 22–25.

Builds campaign object, media system, community feedback loop, metrics, V6 UI, red-team, and final release evidence.

---

# Recommended Execution Rule

Each task should be run in Antigravity fast-ship implementation mode with:

```text
repo path
branch
starting HEAD
allowed files
forbidden files
env read policy
live write policy
secret redaction policy
tests
commit
push
evidence packet
```

Live writes are allowed only in explicitly named pilot tasks:

```text
Task 08 — Discord Webhook Live Pilot
Future Telegram/Discord live integration tasks if explicitly approved
Future Substack supervised publish pilot if explicitly approved
```

All other tasks are contracts, dry-runs, schemas, UI, tests, and evidence.

---

# Final Product Scope Boundary

Included in final product:

```text
AI-native content production
canonical Substack workflow
Discord community drop
Discord webhook adapter
Telegram operator bridge
platform variants
manual X output
deferred LinkedIn/TikTok states
Meta/Threads/Facebook/Instagram capability states
payload hash
approval ledger
dispatch outbox
redacted audit
community feedback intake
V6 UI command center
```

Deferred until after final product:

```text
Discord bot/slash commands
LinkedIn business page live posting
TikTok live posting
YouTube video upload automation
full autonomous metrics ingestion
paid community/subscriber automation
X API posting
autonomous browser self-posting
DM/reply engagement automation
```

This sequencing keeps the product shippable, useful, and safe without waiting for every platform to become perfect.
