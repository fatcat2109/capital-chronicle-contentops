# Current Project Status

`ui/contentops_v5/` is the canonical product UI. `ui/institutional_operator_cockpit_v4/` is fallback/reference only. GitHub remote commits and fetched repo files remain runtime authority above this status doc. Canonical supervised publishing uses Microsoft Edge profile `A:\Capital Chronicle\operator-browser-profiles\contentops-social-main`. Substack is canonical; YouTube Community is the default YouTube text/image surface. Video and Shorts remain separate non-default modes.

## Current Classification

`AWAITING_OPERATOR_FINAL_V1_0_ACCEPTANCE_NO_ENGINEERING_BLOCKERS`

Task: `TASK_CONTENTOPS_V1_0_RC_TARGETED_EDITORIAL_REPAIR_AND_ACCEPTANCE_PREP_V1`.

No `v1.0` tag exists. Current outputs are frozen pending Jim's final visual/content acceptance.

## Database Authority

The main database repo now emits exact story-scoped publication authority without clearing global DQR. Database commits:

- `b03a1acabe0ec10794f948e61a005d4348f69ca3` adds `contentops_publication` authority.
- `49525e0f17c2eb448ac3343f63559f5021fea47c` refreshes the publication packet used by the live run.

The upstream repo has since advanced cleanly to `7793720bfe2e9beacb29dcd20e58a19f3d302cae`; that later authority work does not change the immutable packet producer commit recorded for this canary.

Packet `cc-publication-73ff151c3d3094741b6c` grants `reporting_allowed=true` and `PASS_PUBLICATION_AUTHORIZED` for the exact Treasury story. Global `dqr=BLOCKED` remains intact and was not bypassed.

## Generic Live Run

Run: `contentops_database_publication_live_20260714_1`.

Evidence: `docs/automation/DATABASE_PUBLICATION_AUTHORITY_AND_CONTENTOPS_FULL_LIVE_CLOSURE_V1/contentops_database_publication_live_20260714_1/`.

`live_contentops.eight_platform_substack_first_pipeline_v1` remained the canonical runner. It consumed the publication packet, calibrated the headline to a one-basis-point slope move, generated the Treasury analysis, built two Treasury charts plus one official Treasury data-page excerpt, passed deterministic and bounded LLM review, created the locked release artifacts, and dispatched only after browser/account preflight.

Canonical article: `https://capitalchronicle.substack.com/p/treasury-yield-curve-edges-wider`.

Substack and all eight configured derivatives passed strict identity, text, media, link, parent-chain, and stable-ID readback. A bounded update removed one duplicate third-caption fragment from draft `206928132`. The final targeted editorial repair then removed reader-facing process vocabulary, consolidated the repeated confirmation/falsification summary, and tightened redundant prose in the same draft and public URL. Strict readback reconfirmed title, subtitle, complete body, six source links, three captions, and three distributed visuals. All eight derivative evidence rows remained identical to starting commit `48320531c9bca29c5ebff1ee3dbbe6c43098ae86`; no derivative adapter ran. Telegram public screenshot navigation was unavailable because local Edge DNS could not resolve `t.me`; strict provider readback, message ID, media, text, and link verification remain PASS and the audit records this explicit fallback.

TikTok is outside this eight-destination run and remains `BLOCKED_TIKTOK_CANONICAL_PROFILE_NOT_AUTHENTICATED`.

## Historical Authority

The July 11 RC and final-closure evidence remain historical. They prove earlier transport and repair behavior but no longer describe current readiness. Current status is governed by the July 14 story-scoped packet, generic canary evidence, final platform matrix, and operator audit packet.

## Next Action

Only `TASK_CONTENTOPS_OPERATOR_FINAL_V1_0_ACCEPTANCE_AND_TAG` remains. Jim should inspect the recorded Substack article and derivative URLs. A tag may be created only after explicit acceptance and a passing release verifier. No CI PASS is claimed because no repository status checks exist for this run.
