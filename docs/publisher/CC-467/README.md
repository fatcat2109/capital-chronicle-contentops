CC-467 extends the existing minute consumer and sole durable publisher with
own-account X quote-posts. It reuses CC-258's fast-squawk flags and the existing
sourced-interaction outbox, leases, dispatches, readback and audience collection.
It changes no schedule. Jim's reply drafts and their posting rule keep their
existing path.

Luna MAX screens fresh original flagged posts, Sol 6.1 low prepares one held
desk figure, and Sol 6.1 MAX writes complete source-bound copy. Every call saves
its input, return, configured model/effort, available runtime telemetry and
clocks. These labels do not gate execution. CC-466's actual source/copy checks
apply. The TradingView service captures the affected market after the news;
CC-463 checks that exact chart at the sole publication boundary.

The source post's original clock starts the five-minute deadline. A fresh
write is refused after expiry, including a final check immediately before
Neo's single Post click. Exact uncertain-write readback remains available
after expiry. Five daily reservations count possible writes, including lost
returns. Stable source identities prevent a second quote of the same post.
Native uploads use the item's own media folder and never open a file dialog.

The actual quote relationship is required on both the composer and readback;
a source link in ordinary post text cannot count. The fourteen-day comparison
uses the existing daily views observations for quote-posts and ordinary X
posts. Missing views stay unknown. After the period, measured lower mean
views stop fresh quote-posts; equal or higher views keep them running.

`python scripts/run_sourced_replies.py quote-refresh --store <existing store>`
runs one bounded slice. `quote-status` reports the first live proof and the
fourteen-day observation. The installed minute task calls the same function.

Initial validation: 12 targeted checks passed (`build-tests.xml`), covering
the exact consumer payload/chart, cap, source/number/media changes, deadline,
uncertain-write recovery, role order and idle idempotency. Browser transport
validation, integration and actual live evidence are recorded below when
observed; these tests alone do not satisfy live acceptance.
