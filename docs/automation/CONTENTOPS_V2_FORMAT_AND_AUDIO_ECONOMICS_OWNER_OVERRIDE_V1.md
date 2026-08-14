# ContentOps V2 — Format and Audio Economics Owner Override V1

Authority date: 2026-08-15
Status: `CURRENT_OWNER_OVERRIDE`
Scope: V2 format contract, build/review audio economics, publication-audio policy, and next-task sequencing.

## 1. Owner product contract

V2 is not a `short + ~2 minute midform` product.

Canonical V2 deliverables are:

### Short

- native vertical `9:16`;
- intended for TikTok and YouTube Shorts;
- genuinely short-form, normally about `30–60 seconds` unless a platform/product reason justifies a nearby variation;
- independently authored for short-form retention;
- never padded to satisfy a duration target.

### Longform

- native landscape `16:9`;
- minimum duration `5:00`;
- maximum duration `45:00`;
- duration must be selected from evidence/story depth and viewer value inside that range;
- the current 2–3 minute `midform` proofs are historical development artifacts, not the final V2 longform contract;
- if a story cannot sustain at least five useful minutes without filler, abstain/defer longform or select a stronger story rather than padding.

Short and longform share governed factual/numeric authority but are separately authored editorial products. They are not blind crops, speed changes, or simple shortened/lengthened copies of one another.

## 2. Audio economics owner decision

ElevenLabs materially improved V2 voice quality, but the free-credit pool was consumed too quickly during audition/revision work to support the iterative build loop economically.

Owner direction:

- do not use ElevenLabs as the default build/revision voice backend;
- preserve ElevenLabs as an optional premium finalization/publication backend only after explicit owner authorization and appropriate commercial licensing/credit economics;
- use a local or genuinely low-cost/free professional-enough TTS path for build, proxy, revision, and mode-bakeoff work;
- never regress to Windows SAPI/legacy Windows voices for owner-review or professional candidates.

The current ElevenLabs free plan is not a production dependency. Vendor policy/pricing may change and must be rechecked before any paid/public use.

## 3. Audio-stage separation

V2 must distinguish:

`BUILD_TTS`

from:

`PUBLICATION_TTS`

### BUILD_TTS

Purpose:

- storyboard/proxy timing;
- visual editing;
- Codex repair loops;
- reasoning-mode bakeoffs;
- owner-review drafts when the selected local quality is acceptable.

Requirements:

- zero or very low marginal cost;
- deterministic/provenance-bound;
- no terrible legacy/system voices;
- semantic-segment timing;
- no global `atempo` as the primary cadence controller;
- acceptable diction and cadence for reviewing editorial timing.

### PUBLICATION_TTS

Purpose:

- final public/master voice after editorial/visual lock.

Requirements:

- commercial-use rights/license appropriate for the intended publication;
- owner-accepted voice identity/prosody;
- generated only after expensive visual/editorial iteration is substantially complete;
- no repeated premium re-synthesis for mechanical video repairs when audio content has not changed.

A public-ready local/open model may satisfy both stages if quality and licensing are accepted.

## 4. Current local/open TTS candidates

### Kokoro-82M

Current status: `DEFAULT_BUILD_BASELINE`

Rationale:

- already integrated/proven in prior V2 work;
- low compute and zero marginal API-credit cost when run locally;
- Apache-2.0 model license according to the official model card;
- suitable as the immediate build/proxy baseline even when a future premium voice is used for publication.

Kokoro is not automatically accepted as the final public narrator. Jim/ChatGPT may reject a voice/style while retaining Kokoro as build timing audio.

### Parler-TTS Mini v1.1

Current status: `LOCAL_QUALITY_CHALLENGER`

Rationale:

- Apache-2.0 model license;
- prompt-controlled speaker style, pitch, pacing and recording characteristics;
- can generate a random or named built-in speaker without requiring cloning of a third-party public figure;
- larger/heavier than Kokoro, so runtime/GPU cost must be measured locally.

Do not assume it beats Kokoro without an actual owner-audition pack.

### Chatterbox / Chatterbox-Turbo

Current status: `CONDITIONAL_LOCAL_QUALITY_CHALLENGER`

Rationale:

- MIT-licensed open-source implementation;
- current official project describes Turbo as a lower-compute 350M English model that also targets narration/creative workflows;
- supports expressive/paralinguistic controls.

Important boundary:

- many Chatterbox workflows use reference audio/voice cloning;
- do not clone a real person/public figure or use a reference voice without explicit rights/permission;
- if a rights-safe non-cloned/default path cannot satisfy quality, do not force it into the canonical pipeline.

### F5-TTS pretrained models

Current status: `NOT_ELIGIBLE_FOR_COMMERCIAL_V2_PUBLICATION`

Reason:

- official F5-TTS code is MIT, but the official pretrained base models are CC-BY-NC because of the training data;
- the project maintainer explicitly states the Emilia-trained pretrained base model cannot be used commercially even after fine-tuning.

Do not use those pretrained weights for a monetized/public commercial Capital Chronicle path.

### Windows SAPI / legacy Windows voices

Current status: `DIAGNOSTIC_ONLY / NOT_PROFESSIONAL_MEDIA_ELIGIBLE`

Never use them for owner-review/public candidates.

## 5. Optional low-cost cloud alternatives

These are optional fallbacks, not required accounts for the current task.

- Google Cloud Text-to-Speech currently advertises free monthly character allowances on several voice families, including Chirp 3 HD, but requires a Google Cloud/billing setup and vendor terms/costs must be checked at execution time.
- Amazon Polly currently offers large free-tier allowances for eligible/new accounts and low per-character paid pricing after the free tier, but account eligibility is time-bounded and voice quality must be auditioned.

Do not ask Jim to create these accounts merely for this task unless local quality proves insufficient and the owner explicitly chooses to add a cloud fallback.

## 6. ElevenLabs policy

Current owner-approved ElevenLabs voice-pool history from the Retail repair:

- acceptable by Jim: River, Roger, Matilda, Eric, Bill;
- owner-rejected: Brian, Chris;
- Adam remains banned from the previous repair direction.

This pool is historical evidence, not a requirement to consume ElevenLabs credits during build.

Do not lock one permanent narrator. If ElevenLabs is later used for a publication master, an approved voice may rotate by story/format fit and recent-use cooldown.

Critical commercial boundary:

- the current ElevenLabs Free tier provides credits for testing but does not include the commercial-license benefit shown on paid tiers;
- do not treat Free-tier output as automatically eligible for monetized/public Capital Chronicle publication;
- before publication through ElevenLabs, re-check the then-current plan/license and obtain explicit owner authorization for any paid plan/usage-based billing.

## 7. Correct next sequencing

Do not immediately spend ElevenLabs credits on longform iteration.

Next product work must first prove the final V2 format/economics substrate:

1. short `30–60s` + longform `>=5:00 and <=45:00` contract;
2. local/low-cost build-TTS seam;
3. bounded local voice-quality audition, with Kokoro as the immediate baseline and Parler/Chatterbox as challengers only when safely runnable;
4. one real short + longform vertical slice using a story that genuinely supports longform depth;
5. actual cost/runtime measurements;
6. no MAX/ULTRA comparison until the short+longform/audio substrate is demonstrated cleanly, unless Jim explicitly overrides this sequence.

After that substrate is accepted, the corrected Codex reasoning-effort comparison should focus on at least `MAX` vs `ULTRA` using the same governed story/evidence/starting asset universe/audio backend/revision budget, with longform length sufficient to test long-range analytical/editorial coherence.

## 8. Longform quality doctrine

`5–45 minutes` is a capability envelope, not a quota.

A longform video must earn its duration through:

- primary evidence;
- hard data;
- mechanism depth;
- counter-case;
- second-order channels;
- documentary/context assets;
- native charts/maps/documents;
- narrative re-hooks;
- meaningful chapter progression;
- explicit confirmation/invalidation/checkpoints.

Do not stretch a 2-minute story to five minutes.

Abundant analysis means more evidence and mechanism, not more on-screen paragraphs.

## 9. Safety and provenance

- `ZERO_VIDEO_PUBLIC_WRITE_AUTHORITY` remains in force.
- no V1 runtime/store/scheduler/publication mutation;
- no secret/API-key serialization;
- no real-person voice cloning without permission;
- generated/synthetic narration is not factual authority;
- every TTS output records backend/model/voice/settings/input hash/output hash/runtime and commercial-eligibility state.

## 10. Owner gate

Builder technical/audio metrics cannot self-pass voice aesthetics.

Any new local/public voice considered canonical must be supplied as an actual audition/media artifact for Jim/ChatGPT review.
