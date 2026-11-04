# ContentOps V1 lane, 4 Nov 2026 (Claude, Opus 5.5 max)

Jim reported broken posts at 19:40 GMT+7. Each fault below was traced from the
production store (`contentops_daily_app_v1.sqlite3`, read-only), the run folders
under `Runtime\ContentOps\daily_app_outputs\owner-manual\` and the live pages read
through BrowserOS Neo. Times are GMT+7 unless marked Z.

## What was published, and why each fault happened

| Fault Jim saw | What the record shows | Root cause in code | Fix |
|---|---|---|---|
| SEC post "wrong image" everywhere | Every destination carries the reviewed SEC facts card (`sec-si-roundtable-event-facts-20261109`, sha `c4e7eadb...`). Telegram, X, YouTube and Facebook images were pulled and compared. No wrong file was sent. The card is mostly empty white space and its footer shows the SEC's 19 Oct announcement date, because the piece previews a 16-day-old announcement for the 9 Nov event. On Substack the card sat above the first paragraph with no caption and no alt text. | The Substack publish request carried neither the reviewed placement (`placement_after: "What the SEC has announced"`) nor the caption, so the executing agent put the image first. | `neo_destination_handoff_v1`: the media manifest now carries `placement_after`, and every Substack PUBLISH/EDIT request has a placement, caption and alt-text step. |
| Posts with no image (CPI on Discord, Facebook, Telegram, X, YouTube) | CPI's seven social copies were frozen with `media_asset_ids: []`. | The writer's per-platform image choice was applied verbatim: an empty choice sent a bare post. | `build_native_derivative_payloads`: an empty choice takes the first reviewed image. `finalize_intent`: a copy frozen with no image gets the reviewed visual or the owned card before its bytes are hashed; if building the image fails, the post still goes with its link and the cause is kept (`post_image_floor_failure`). |
| Instagram missing the SEC post (3 posts in all) | SEC's Instagram preview was `SKIPPED_IMAGE_REQUIRED` although the card existed; the plan listed the skip, so no Instagram message was registered. FOMC's Instagram ended `DERIVATIVE_RECOVERY_RETRY_EXHAUSTED_NO_WRITE`; the midterm preview had no social copies (below). | Same empty-choice rule turned into an Instagram skip, and `permitted_derivative_skips` kept Instagram unregistered. | Instagram is never left out for want of an image (`registration_skips`); the plan's own skip list still passes its structural check. |
| Instagram CPI post shows an old dark card | `DfUAKIzgfPH` carries the old delivery-only title card ("Source: CONFIRMED"). | Fixed for future sends by CC-186 (885b908e). The live post cannot be edited through the API. | Delete-and-repost needs Jim's yes. |
| LinkedIn: one post since last week | The jobs post is live on Jim's member profile (`urn:li:ugcPost:7523689467564490752`). SEC is `UNKNOWN_WRITE`, CPI expired, FOMC retry-exhausted. The company page only had the 27 Oct oil post. | Routine LinkedIn posts go only to the member profile; the company page was reachable only through an owner-selected recovery path. | Every full-V1 plan now registers a routine company-page copy of the same reviewed LinkedIn copy, sent through Neo in the main send pass. |
| Threads: nothing since last week | Every Threads row is `READY`, `AUTH_INVALID` or expired. | The Threads API token is invalid (`THREADS_AUTH_INVALID`). The Threads web session in Neo is signed in, but the pipeline posts through the API. | Jim re-issues the Threads token; follow-up: a Neo path for Threads. |
| YouTube: 4 posts | FOMC `DERIVATIVE_EXPIRED_STALE_NO_WRITE`; midterm had no social copies. | Derivative expiry counts from the outbox row, not the canonical's publication (CC-199 CLD-C11, open). | Follow-up for Codex Publisher. |
| Midterm preview reached no social platform | Canonical Substack is live, but its reconciliation is `RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE` after the credit edit, so it never counted as published: no social copies, no record in `published_content_v1.jsonl`, no digest entry. | CC-199 CLD-C7 (a post-publication edit marks the canonical incomplete). | The digest now reads the store's confirmed canonicals too. The midterm socials are stale (election day passed) and are not reposted. CLD-C7 itself is a follow-up. |
| Substack digest "November 03" | Prepared on 4 Nov 17:56 for the 3 Nov window; listed 2 of 3 pieces (midterm missing); bare link list; card read "2 articles"; image after the disclaimer. Its email can never be observed, so it would have held every later digest. | `prepare_daily_digest` read only the published-record feed, zero-padded the day, rendered an empty card and waited on email confirmation. | Day label "November 3, 2026"; live canonicals from the store are included; each entry has its standfirst; the subtitle names the pieces; the card lists the titles at the top; a web-confirmed digest no longer holds the next day's. |

## Tests

- New: `tests/test_contentops_v1_lane_20261104.py`, 17 tests (image floor on all eight
  destinations, unchanged copies that have an image, image failure never blocks the
  post, Substack placement/caption/alt, digest day/selection/summaries/card, next-day
  digest, Instagram registration, LinkedIn company copy registration and payload).
- Updated assertions that encoded the old behaviour: Instagram skip
  (`test_reader_first_data_journalism_v1`, `test_native_photoless_briefs_v1`), digest card
  and text (`test_substack_daily_digest_v1`), and counts that now include the company-page
  copy (`test_publication_coordinator_v1`, `test_native_desktop_publication_v1`).
- Regression set (13 files): the same 17 failures as the live commit 24e067d3, run on a
  clean baseline worktree; no new failure. Those 17 predate this work (CC-154 site-first
  readback in older fixtures, a percent-label test, a missing esbuild module, text-first
  and photo-rule fixtures).
</content>
</invoke>
