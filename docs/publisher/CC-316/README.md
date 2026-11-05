# CC-316 — article TradingView snapshots

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
