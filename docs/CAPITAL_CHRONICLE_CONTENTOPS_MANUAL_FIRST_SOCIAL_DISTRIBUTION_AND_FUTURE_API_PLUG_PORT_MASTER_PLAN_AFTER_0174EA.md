# Capital Chronicle ContentOps — Manual-First Social Distribution + Future API Plug-Port Master Plan

## 0. Owner Decision

Capital Chronicle ContentOps should pivot from “platform API readiness as the active build lane” to a clearer two-track model:

1. **Manual Publishing Track now**
   Jim reads, reviews, edits, copy/pastes, and posts manually to social platforms.
   ContentOps prepares safe packets, platform previews, checklists, and manual record forms.
   The repo does not call platform APIs, does not read credentials, and does not publish.

2. **Future API Plug-Port Track later**
   ContentOps builds platform adapter contracts and disabled connector ports for X, LinkedIn, Telegram, Substack, Threads, Facebook, Instagram, TikTok, YouTube, Bluesky, Medium, Reddit, Discord, and Mastodon.
   Paid or gated APIs are not blockers to product design; they become future plug-in capability records.
   Live API dispatch remains disabled until explicit per-platform gates are accepted.

The correct current operating model is:

Jim manually publishes.
ContentOps governs readiness, evidence, safety, previews, and records.
Future automation is built as gated plug-port architecture, not active live behavior.

## 1. Current Product State

Current accepted baseline remains the last accepted safe baseline before the blocked 0174DE live-read-only implementation.

0174DE attempted to add the first X live-read-only identity proof gate, but it remains blocked pending redirect/final-host hardening. That means no further X live chain should proceed until the live-read-only gate is repaired.

However, this master plan intentionally moves the project away from immediate live API execution and toward platform-agnostic manual-first distribution architecture.

## 2. North Star

Capital Chronicle ContentOps is a local-first institutional editorial operating system for macro content governance.

It should help Jim:

* plan serious macro/process content;
* preserve citations, limitations, and non-signal posture;
* classify content lanes;
* review drafts;
* generate safe platform previews;
* inspect platform constraints;
* approve packets manually;
* copy/paste manually to platforms;
* record manually posted URLs and metrics;
* keep a full evidence trail;
* later connect supervised API dispatch only after platform-specific gates pass.

The product must never become:

* an autonomous publisher;
* a scheduler-first SaaS dashboard;
* a spam/cross-post bot;
* an AI trading signal engine;
* a financial advice generator;
* a live API console;
* a credential screen.

## 3. Final Product Principle

Build the product as if it will eventually support supervised one-click publishing, but operate now as manual-only.

Final future capability should be:

Jim opens an approved packet.
ContentOps shows evidence, source lineage, limitations, guardrails, platform payloads, account binding, spend/rate-limit state, approval hash, kill switch, and redacted audit.
Jim clicks one explicit supervised publish action only after every gate passes.

Current capability should be:

Jim opens a reviewed packet.
ContentOps shows safe copy/paste previews and manual posting instructions.
Jim posts manually outside the repo.
Jim records the public URL and simple metrics manually.

## 4. Content Lanes

### Lane A — Pre-Alpha General / Process

Allowed now.

Examples:

* build-in-public;
* data sufficiency;
* forecast readiness;
* failure forensics philosophy;
* product philosophy;
* macro education;
* “why no forecast can be correct”;
* “not a signal service” positioning.

No artifact claims. No market calls. No performance claims.

### Lane B — Grounded News Context

Allowed now with manual research and citations.

News is a hook, not a signal.

Use news to explain:

* why source quality matters;
* why one headline is not thesis-ready;
* why official data and revisions matter;
* what evidence is missing;
* why a research system should refuse premature certainty.

Never use news to say buy/sell/hold, target, long/short, “this asset will move,” or “our model predicts.”

### Lane C — Future Artifact-Backed Content

Blocked until real approved Capital Chronicle internal-alpha artifacts exist.

Must require:

* artifact IDs;
* lineage;
* freshness;
* limitations;
* DQR/data sufficiency status;
* forecast-readiness status;
* missing/degraded/proxy labels;
* approved content class;
* no-advice/no-signal metadata.

## 5. Platform Universe

### Tier 1 — Active Manual Publishing Now

These platforms should be represented in Writer Studio, Platform Preview, Manual Publish Log, and Metrics Record.

1. **Substack**
   Role: canonical long-form home.
   Current mode: manual only.
   API status: no reliable public supported publishing API for new integrations; treat as manual export.
   Build now:

   * long-form issue blueprint;
   * Substack formatting checklist;
   * title/subtitle/SEO notes;
   * source/citation block;
   * manual publish URL record;
   * metrics manual entry.
     Future API: not prioritized.

2. **LinkedIn**
   Role: professional founder/operator voice.
   Current mode: manual post now.
   API status: app/product/scope gated; member posting via w_member_social exists; organization posting requires role/product validation.
   Build now:

   * member post preview;
   * organization post preview as future-gated;
   * image/document/article constraints placeholder;
   * manual post checklist;
   * manual URL/metrics record.
     Future API:
   * identity proof;
   * w_member_social proof;
   * organization role proof;
   * payload hash + approval ledger;
   * supervised publish adapter.

3. **X**
   Role: short-form distribution and concise hook layer.
   Current mode: manual post now.
   API status: paid / credit-based; write endpoints cost money.
   Build now:

   * X text/thread preview;
   * cost warning badge;
   * paid API gate;
   * duplicate/cross-post detector;
   * manual URL/metrics record.
     Future API:
   * repair 0174DE redirect/final-host hardening;
   * spend cap gate;
   * account binding;
   * payload hash;
   * supervised publish only.

4. **Threads**
   Role: softer conversational mirror.
   Current mode: manual post now.
   API status: Meta official docs inaccessible/gated in current audit; treat as official-doc-gated.
   Build now:

   * Threads text preview;
   * conversational rewrite variant;
   * manual post checklist;
   * Meta docs verification gate.
     Future API:
   * official docs packet;
   * account binding;
   * permission proof;
   * supervised publish adapter only after Meta gates.

5. **Telegram**
   Role: controlled channel / future first live pilot.
   Current mode: manual or semi-manual channel use now; no repo posting.
   API status: technically easiest; Bot API supports sendMessage; paid broadcast only for high throughput.
   Build now:

   * channel message preview;
   * Telegram-specific formatting;
   * bot token slot placeholder;
   * channel target placeholder;
   * admin permission checklist;
   * manual message log.
     Future API:
   * bot getMe identity proof;
   * channel permission proof;
   * one-request sendMessage dry-run contract;
   * one supervised test post after approval ledger and kill switch.

### Tier 2 — Build Plug-Ports Now, Manual or Later

6. **Facebook Page**
   Role: Meta page distribution later.
   Current mode: manual only.
   API status: Meta docs gated/429 in current audit; treat as developer-portal/app-review gated.
   Build now:

   * Facebook Page post preview;
   * Page identity placeholder;
   * Meta app review checklist;
   * manual URL/metrics record.
     Future API:
   * official docs verification;
   * Page access token policy;
   * page role proof;
   * payload hash;
   * supervised page post.

7. **Instagram**
   Role: visual/card/carousel distribution later.
   Current mode: manual only.
   API status: Meta docs login-gated in current audit; likely business/creator/media-container constrained but must be verified officially before code.
   Build now:

   * image/carousel caption preview;
   * alt text and media rights checklist;
   * visual export handoff;
   * manual post record.
     Future API:
   * Instagram content publishing official-doc pack;
   * account type proof;
   * media URL/hosting policy;
   * container publish gate;
   * supervised publish only.

8. **TikTok**
   Role: later video/photo format, not near-term macro text priority.
   Current mode: manual only.
   API status: Content Posting API exists but requires app registration, product enablement, video.publish approval, user authorization, access token/open ID, and audit to lift private-only restriction.
   Build now:

   * TikTok content concept card;
   * video/photo requirements placeholder;
   * app audit checklist;
   * private-only warning;
   * manual post record.
     Future API:
   * creator info proof;
   * publish scope proof;
   * audit acceptance proof;
   * supervised video/photo post gate.

9. **YouTube**
   Role: future long-form video / walkthroughs / product demos.
   Current mode: manual upload only.
   API status: YouTube Data API supports video upload but requires OAuth scope, quota, and audit/private-mode constraints for unverified projects.
   Build now:

   * video script/description preview;
   * YouTube title/description/tags checklist;
   * thumbnail/chapters checklist;
   * manual URL/metrics record.
     Future API:
   * upload scope proof;
   * quota gate;
   * audit/compliance gate;
   * supervised upload only.

### Tier 3 — Optional Future Channels

10. **Bluesky**
    Role: open short-form mirror; technically attractive.
    Current mode: manual now or future supervised.
    API status: AT Protocol docs are clear; create session returns tokens; createRecord can post.
    Build now:

    * Bluesky text preview;
    * 300-ish character/URL/card constraints placeholder;
    * account/session plug-port.
      Future API:
    * app password/session boundary;
    * record create gate;
    * image blob sanitization gate;
    * supervised publish.

11. **Mastodon**
    Role: open-web / technical audience.
    Current mode: optional manual.
    API status: REST API supports POST /api/v1/statuses with OAuth write:statuses; instance-specific behavior matters.
    Build now:

    * instance-aware post preview;
    * visibility/sensitive/content-warning fields;
    * idempotency-key design.
      Future API:
    * instance binding;
    * OAuth token gate;
    * idempotency proof;
    * supervised post.

12. **Discord**
    Role: internal/community announcement channel, not public macro authority.
    Current mode: optional manual.
    API status: incoming webhooks can post to channels; webhook token is a secret.
    Build now:

    * Discord announcement preview;
    * allowed_mentions policy;
    * webhook secret placeholder;
    * no public market claim warning.
      Future API:
    * webhook URL redaction gate;
    * selected channel binding;
    * no @everyone/@here unless explicit approval;
    * supervised webhook execute.

13. **Reddit**
    Role: low-priority discussion/community distribution.
    Current mode: manual only.
    API status: API supports submit, but subreddit rules/moderation/reputation risk dominate.
    Build now:

    * Reddit post draft checklist;
    * subreddit rule checklist;
    * “not broadcast channel” warning.
      Future API:
    * probably avoid; manual preferred.

14. **Medium**
    Role: optional syndication if Substack not enough.
    Current mode: manual only.
    API status: official API repo archived; API no longer supported / not recommended for new integration.
    Build now:

    * manual article export format only.
      Future API:
    * do not prioritize.

## 6. Platform Capability Registry

Create a deterministic local registry for every platform.

Each platform record should include:

* platform_id;
* display_name;
* current_mode;
* manual_supported_now;
* api_plug_port_status;
* official_docs_status;
* paid_required_status;
* app_review_status;
* credential_type;
* account_binding_required;
* media_requirements;
* payload_types;
* max_text_length_or_unknown;
* requires_public_media_url;
* requires_business_or_creator_account;
* live_posting_status;
* scheduler_status;
* metrics_status;
* risk_level;
* next_blocker;
* manual_fallback;
* future_gate_sequence.

Initial statuses:

* `manual_supported_now`
* `api_plug_port_only`
* `official_docs_verified`
* `official_docs_gated`
* `paid_api_required`
* `permission_review_required`
* `app_audit_required`
* `unsupported_api_manual_only`
* `future_optional`

## 7. Manual Publishing Workflow

Every content item should flow through:

1. Research Brief
2. Draft Review Packet
3. Canonical Content Object
4. Platform Preview Packet
5. Guardrail Scan
6. Manual Approval Packet
7. Copy/Paste Checklist
8. Jim Manual Post
9. Manual URL Record
10. Manual Metrics Entry
11. Evidence Vault Archive

No platform API call. No credential. No scheduler. No auto-post. No scraping.

## 8. Platform Preview Contract

Each platform preview must include:

* platform;
* content lane;
* preview_text;
* media_placeholders;
* formatting_notes;
* character/length warnings;
* citation handling;
* hashtag policy;
* link policy;
* AI disclosure field if relevant;
* platform-specific risks;
* manual_post_steps;
* not_public_postable_until_manual_review;
* approval_required;
* payload_hash_for_future;
* future_api_endpoint_family;
* future_api_status;
* paid_or_review_warning;
* no_external_call_performed.

The preview should be useful enough that Jim can copy/paste manually, but it must not imply the repo posted it.

## 9. Manual Publish Record

After Jim posts manually, the repo may record:

* content_id;
* platform;
* manual_post_url;
* manual_post_timestamp;
* posted_by = Jim;
* content_hash;
* payload_hash;
* approval_packet_id;
* notes;
* simple observed metrics entered manually;
* caveats.

No scraping. No API metrics. No browser automation.

## 10. Future API Plug-Port Architecture

For each platform, build inactive adapter ports:

* identity proof gate;
* account binding gate;
* credential source policy;
* permission/scope proof;
* official docs proof;
* paid/cost/rate-limit proof;
* payload hash proof;
* manual approval ledger proof;
* kill switch proof;
* redacted audit proof;
* one-request/no-retry live pilot proof;
* rollback/manual fallback proof.

Each adapter must expose only:

* `build_payload_preview()`
* `validate_payload_contract()`
* `build_manual_post_instructions()`
* `build_future_api_capability_record()`

No active method named `publish`, `send`, `post`, `dispatch`, `schedule`, or `upload` should exist until future explicit live gate tasks.

## 11. API Cost / Access Policy

Classify platforms:

### Paid / Credit-Based

* X

### Free Basic API But Paid High-Throughput or Operationally Limited

* Telegram: basic Bot API appears free; paid broadcast only for high throughput.

### Permission/App Review/Audit Gated

* LinkedIn
* Facebook Page
* Instagram
* Threads
* TikTok
* YouTube

### Public/Open or Self-Hosted Friendly, But Still Credential-Gated

* Bluesky
* Mastodon
* Discord webhooks

### Unsupported / Manual Preferred

* Substack
* Medium
* Reddit for now

## 12. UI Product Changes

V5 should add or emphasize:

1. Platform Capability Registry screen
2. Manual Publish Workbench
3. Platform Preview Studio
4. API Plug-Port Readiness Matrix
5. Manual URL / Metrics Record room
6. Spend / API Risk Ledger
7. Official Docs Verification Pack
8. Account Binding Placeholder Registry
9. Credential Slot Registry with no values
10. Future Dispatch Gate Matrix

The UI copy must say:

* “Manual publishing active”
* “API plug-port prepared”
* “Live dispatch disabled”
* “Credential not read”
* “Paid API required”
* “Official docs gated”
* “Future supervised dispatch only”

## 13. Revised Roadmap

### Task 0174DE_R1 — Repair Blocked X Live-Read-Only Gate

Only if we want to keep the current X live chain.

Purpose:
Disable redirect following / verify final host / prove request budget 1.

This is corrective, not expansion.

### Task 0174EA — Manual-First Social Distribution Master Plan Commit

Docs only.

Deliver:

* this master plan in repo;
* official platform verdict table;
* revised platform list;
* manual-first vs future-API mode model;
* no source code;
* no network inside repo.

### Task 0174EB — Platform Capability Registry Contract

Build local deterministic registry for:
X, LinkedIn, Telegram, Substack, Threads, Facebook Page, Instagram, TikTok, YouTube, Bluesky, Medium, Reddit, Discord, Mastodon.

No network. No credentials. No live calls.

### Task 0174EC — Platform Preview Contract + Manual Copy/Paste Packets

Build platform preview packets and manual posting instructions.

Preview outputs:

* Substack long-form;
* LinkedIn post;
* X post/thread;
* Threads post;
* Telegram message;
* Facebook Page post;
* Instagram caption/card;
* TikTok concept/caption;
* YouTube description;
* Bluesky post;
* optional Discord/Mastodon/Reddit/Medium manual previews.

### Task 0174ED — Manual Publish Record + Metrics Entry Ledger

Build manual URL and manually observed metrics record.

No scraping. No platform API.

### Task 0174EE — API Plug-Port Readiness Matrix

Build future connector ports as disabled capability records.

No active publish/send/post functions.
Only contracts and readiness gates.

### Task 0174EF — UI Integration: Manual Publish + Platform Registry

Update V5 / cockpit UI to show:

* manual publishing now;
* API plug-ports later;
* paid/review-gated status per platform;
* future supervised dispatch gates.

### Task 0174EG — Telegram Future Live Pilot Re-entry

Only after manual-first platform registry and approval ledger are stable.

Telegram remains first supervised live pilot candidate.

### Task 0174EH — X Paid API Spend-Control + Hardening Re-entry

Only after 0174DE_R1 and spend policy gates pass.

## 14. Acceptance Criteria

The master plan is accepted only if:

* it includes all old platforms: X, LinkedIn, Telegram, Substack, Threads, Facebook, Instagram, TikTok;
* it adds reasonable missing platforms: YouTube, Bluesky, Medium, Reddit, Discord, Mastodon;
* it distinguishes manual now vs future API;
* it records official docs status and uncertainty;
* it treats X as paid;
* it treats Meta as official-doc-gated until portal verification;
* it treats Substack/Medium as manual-first;
* it treats Telegram as first future live pilot;
* it never claims live posting is available now;
* it never adds credential reads;
* it never adds runtime network;
* it preserves no-advice/no-signal posture.

## 15. Final Operating Principle

Manual now.
Plug-port architecture now.
Supervised API later.
Autonomous publishing never.
