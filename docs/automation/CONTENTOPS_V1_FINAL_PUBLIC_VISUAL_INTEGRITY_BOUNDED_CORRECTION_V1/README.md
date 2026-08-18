# V1 final public visual-integrity bounded correction

Classification: `PASS_PUBLIC_VISUAL_INTEGRITY_SOURCE_CORRECTION_READY_FOR_CHATGPT_AUDIT`.

This is Phase 1 source correction and zero-write proof only. It does not classify Task 2 as passing, does not grant `V1_FINAL_PRODUCT_ACCEPTED`, and did not repair any live public object.

## Authority and scope

- Verified `origin/master`: `458be8c7e011c617e04433e52523448e2f2b6fba`.
- Verified recovery base: `5701f1039a7f229f636d54bdf0a2133bb2bdcf23` (`Close V1 Facebook X and Instagram recovery`).
- Task branch: `codex/v1-final-public-visual-integrity-bounded-correction-v1`, created from the exact recovery base.
- Public/provider writes: `0`.
- Production-store mutations: `0`.
- Model/GO calls: `0`.
- Automation mutations: `0`; the four existing V1 automations were read-only inspected and remain `PAUSED`.
- V2 mutations: `0`.

## Root cause and permanent correction

The prior public audit treated the canonical media manifest as a lower bound (`actual >= expected`) and allowed text correctness to classify overall success. It therefore accepted two unexpected public images for a text-only article whose canonical article-media manifest was empty. Resume/update logic likewise did not establish an exact editor-media contract before the public transition.

The correction makes canonical article media an exact count-and-SHA-256 multiset contract for public readback and editor resume. Unexpected editor media blocks ordinary publication before any transition and is never auto-deleted. Delivery-only rows remain outside canonical article media. A narrow internal repair helper is bound to the exact destination, draft ID, public URL, title/subtitle/body hashes, expected article-media manifest hash, and unexpected-media identity manifest hash; ordinary newsroom/scheduler execution has no caller or authorization route to it.

The delivery-card renderer now prefers the repo-established Windows Arial path, falls back to DejaVu Sans when available, and finally uses deterministic ASCII-safe punctuation transliteration. Exact Unicode remains preserved as `source_title`; display output records its font/fallback identity and cannot contain replacement glyphs.

## Exact current Substack contract

- Article: `https://capitalchronicle.substack.com/p/ft-flags-lender-insurance-gap-around`
- Draft/public object: `211677374`
- Expected canonical article-media count: `0`.
- Actual public body-image count: `2`.
- Both observed S3 objects are 38,986 bytes and independently hash to the frozen delivery-only card: `0839a7488a843299767f560bffc2f8e819719593750dcff730a4944dbc7b0ad7`.
- Required classification under corrected source: `FAILED_SUBSTACK_PUBLIC_VISUAL_READBACK`; never full content/visual success.

Fresh read-only screenshot: `substack_public_defect_before_source_correction.png` (`d9d078a00318d687c260604852984ebf63a0ed5559de7e43ef0d5e1837aca0d5`). It visibly records both duplicate delivery cards and the corrupted title glyph. A second post-implementation browser readback was attempted but the canonical Edge CDP 9223 owner was no longer running; the registry returned `READY_TO_LAUNCH`, and the audit failed closed with `canonical_edge_profile_not_owner_of_requested_cdp_port`. No alternate profile or quarantined direct-launch path was used. The two exact public object hashes were then re-read without mutation.

## Instagram read-only evidence and repair semantics

Fresh read-only screenshot: `instagram_public_readonly_before_source_correction.png` (`c35d1d6acc6189e9e662794e9dbafa9328119172d9a0aa5a50260e819e11140b`). The public object was accessible and visibly contains the corrupted `Meta�BlackRock’s` title glyph.

Current first-party Meta authority documents publishing as a new upload/container followed by `media_publish`, whose response is a new IG Media ID. Meta's current generated `IGMedia` SDK object exposes `media_url` as a readable field and generic CRUD scaffolding, but it documents no exact operation for replacing the image bytes of an already-published object while preserving its media ID/permalink. This is an inference from the current first-party contract, not a claim about undocumented internals.

Classification: `OWNER_DECISION_REQUIRED_FOR_INSTAGRAM_DESTRUCTIVE_REPAIR`.

Smallest valid owner choices are: preserve the existing object and accept the visual defect; explicitly authorize deletion and publication of a corrected new media object (new identity/permalink and lost engagement continuity); or publish a corrected follow-up/new post while retaining the original (non-destructive, but the original defect remains).

First-party references:

- Meta Instagram API collection: https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api?entity=request-23987686-5216d45b-1e24-4bff-bdc8-e1bf15358477
- Meta Business SDK `IGMedia`: https://raw.githubusercontent.com/facebook/facebook-nodejs-business-sdk/main/src/objects/ig-media.js

## Validation

- Python compilation: pass.
- Combined Edge publishing, media manifest, Cloudinary delivery, pipeline, publication coordinator, Facebook, Instagram recovery, and CodeGraph tests: `176 passed`.
- CodeGraph generator check: `CODEGRAPH_CURRENT`.
- Production-shaped frozen-canary smoke: `PASS_FROZEN_CANARY_ZERO_WRITE_SMOKE`; returned `BLOCKED_SUBSTACK_RESUME_UNEXPECTED_MEDIA`, with `public_write_attempted=false`, `public_transition_performed=false`, `automatic_media_cleanup_performed=false`, provider writes `0`, production-store mutations `0`, model/GO calls `0`, and all frozen hashes unchanged.

CodeGraph/caller inspection found the canonical publisher remains `publish_substack_article_via_edge`; the new repair helper is private and has no production caller, facade, CLI, scheduler, or newsroom route. No duplicate publisher or repair path was added.

## Post-audit operation that remains forbidden in this phase

For Substack only, a later exact owner authorization would bind object `211677374`, the same public URL, exact title/subtitle, body SHA-256 `33d48d5b8ad1250673009c93fc3f1469688b15ec05d3b1a327074f9b69827ddc`, empty canonical article-media manifest, and both observed S3 identities/hashes. The internal helper would re-read the public/editor bindings, remove only those two authorized unexpected image nodes, use the existing-object Update transition, and require same-URL text plus exact zero-media readback. It cannot change title, subtitle, or prose.

No Substack or Instagram repair described here was executed.
