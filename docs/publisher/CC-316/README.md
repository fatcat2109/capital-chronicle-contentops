# CC-316 — article TradingView snapshots

## Completed verification — 9 November 2026

CC-316's implementation is already integrated into the Publisher operating root.
Merge `53295992bd7249f8dacb5a0cada16c6212887372` on 7 November included all three
original commits, including `b3d166f8` removing the RAM gate. CC-333's subsequent
`69a6b3898bf911665385b47f7ac7013a48fb2d8f` preserves the daily snapshot lead and
release-card-first ordering. The earlier pending-integration notes below describe
the original build, not the current state. This continuation fast-forwards the
existing item branch to operating HEAD `43461a35` before recording acceptance.

The [installed-consumer verification](resume-20261109/live-consumer-verification.json)
executes the operating root's `publication-status` against both existing bindings.
It confirms two reconciled articles, each with Substack, all eight standard social
destinations and the LinkedIn company copy, no unknown writes and no pending
requests. Their frozen packages all select their approved TradingView image;
the source bytes pass the snapshot validator and match the coordinator's sealed
media hashes. Every destination retains an image-verified readback clock.

- [Weekend wrap](https://capitalchronicle.substack.com/p/tanker-strikes-us-strikes-on-iran):
  the first post-integration market wrap, USOIL, published 9 November at 07:41 GMT+7;
  image SHA256 `7af80bd55b91edf4d55c30c512319d5dd2ff1caa9db7c81363f030a1aeeff327`.
- [Pre-US daily wrap](https://capitalchronicle.substack.com/p/capital-chronicle-pre-us-wrap-dollar):
  EURUSD, published 9 November at 19:17:45 GMT+7;
  image SHA256 `1badc076e1605a49c0f2ba5af43f1ee6062b129379dad6f98349e7a47523b393`.

The earlier exact browser/API observations remain in
[CC-341](../CC-341/README.md) and
[CC-124](../CC-124/pre-us-wrap-20261109/README.md). This continuation re-reads their
installed coordinator state and saved source bytes; it makes no new browser visit,
capture or public write. Those runs missed the separate 15-minute dispatch target;
their original approval and readback clocks remain unchanged.

All **36 focused checks pass**: 19 article/registration/order/fallback/rights/hosting
checks and 17 capture checks, including capture without a RAM gate. The three
article selections are disjoint. One initial combined attempt was stopped at
55 seconds without a complete result; the subsequent four serial selections each
finished in under 12 seconds. JUnit and text results are in `resume-20261109/`.
No runtime source change was needed. All seven affected installed source modules
match this branch's Git blobs and file hashes. Eight inherited modified files
across the two checkouts remain byte-identical and outside these commits.

The explicit tags are `contentops-live-20261109-cc316` and
`contentops-rollback-20261109-cc316`. The rollback names `7dfecb46`, the actual
pre-CC-316-integration parent of `53295992`, and therefore also predates the
associated CC-333 changes. It is a recovery reference, not an instruction to
remove subsequent Publisher work. Integration and tag readback are recorded in
[integration.json](resume-20261109/integration.json).

Launch process 27412, started 9 November at 22:10:35 GMT+7, explicitly configured
`gpt-6.1-sol/high`; model and effort remain `CONFIGURED_NOT_OBSERVED`. This
engineering verification made zero editorial model calls, changed no schedule
and sent no chat messages. The chosen path reuses the already-published market
wraps because their exact image readbacks satisfy the item without another post.

## Original build — 6 November 2026

Built on `backlog/cc-316-article-tradingview-snapshot`. Integration is intentionally pending: the item says to integrate only after the Friday 6 November NFP release piece is published. No operating-root merge, live/rollback tag, production store mutation, article send, browser action or schedule change was made in this run.

The base is operating HEAD `8e0ee573eb76a7255de601dd3c4d3ea89513bb8a`, which contains CC-314's snapshot module. Fresh `origin/master` was `5be8fc63317be06d8319f3dd51ac4137a107cbb5` and lacks that operational dependency. The previous lane telemetry/duplicate-ledger changes and unrelated CC-124 artifacts remain outside these commits.

The article writer names `market_asset`; a single structured candidate asset can also supply it. The native CC-124 article path captures the guest chart before the article manifest, preview media ids and coordinator plan freeze. The six reviewed mappings are reused. Snapshot bytes enter both `media.assets` and `media.delivery_only_assets`; hosting validates them through the delivery-only contract. The snapshot remains display media, never a source series for analytical claims.

Every image destination selects the snapshot. Existing API transports accept one image, so when a current card exists an exact-pixel panel puts that card above the full snapshot. Substack receives the separate card first and the snapshot after the standfirst; the panel is derivative-only. TradingView's creation header and logo remain uncropped, and each derivative carries `Chart: TradingView.` The snapshot and panel validators compare original pixels and hashes, and panel hosting also validates the embedded card's source/rights contract. Official-history requirements for release analysis remain enforced.

Capture failure preserves the current card and records the exact cause; a resume reuses the operation's saved capture/failure. Paid pages omit the snapshot until written TradingView permission (public redistribution rights). Retrospectives omit a new snapshot under decision 19 b. The existing preview-host guard remains on the final transport. Jim decision 87's RAM gate removal is commit `b3d166f84bc1800675e9b34587994c496b8a478a`.

Validation uses one pytest process at a time and only the affected files, outside the prohibited windows. Logs are adjacent:

- `targeted-tests.txt`: article capture/registration, all six mapping routes/eight image destinations, actual transport inputs, current card first, failure fallback, retry reuse, rights/bytes, hosting, CC-314 status posts and affected media/bridge tests.
- `editorial-regressions.txt`: 127 passed; native editorial protocol, reader-first data journalism and existing newsroom.
- `publication-regressions.txt`: 24 passed; native reviewed handoffs, immutable seals and publication/recovery.

`layout/card-and-tradingview-64f6c4d01e0766c92239.png` was visually inspected through the file-image viewer: 1600 x 1758, card above the full chart, creation header/logo intact. SHA-256 `ddcfed5e98da9dd96b95ad36c6e34d4a99dbe0ca0bfb4dc15041b9f0576aa15b`. It combines controlled test copy with CC-314's retained US500 download. The other six-market tests use that same retained image as controlled transport bytes; they prove symbol routing, not fresh captures of six markets. No fresh live capture or public readback is claimed.

Launch readback: PID 30492 started this exact CC-316 exec with `--model gpt-6.1-sol` and `model_reasoning_effort="high"`. These are CONFIGURED_NOT_OBSERVED; runtime model/effort telemetry is unavailable. No editorial model call occurred in this engineering run; test returns are explicitly controlled.

After the NFP canonical publication is confirmed, resume this same item/branch, re-read current operating HEAD and WIP, create the rollback tag on that exact pre-integration HEAD, integrate the CC-316 commits into the Publisher operating root and create/push its live tag. Then use the next eligible daily market article through the existing CC-124/coordinator path and read back the canonical and every image destination. Record those exact objects and tags in this item before DONE. Do not retrofit frozen/dispatched historical packages, start an extra run or add a schedule to satisfy the future acceptance step.

Evidence recorded UTC: 2026-11-05T20:59:23.148337+00:00 (Jim-facing build session: 6 November 2026, GMT+7).
