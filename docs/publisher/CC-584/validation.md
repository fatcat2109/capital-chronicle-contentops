# CC-584 validation

Implementation: `52d8a73d2ef49c6ad1654842e7694dda666845db`, built on ContentOps operating base
`2f2ea9ff9ba30e52d119e9760ebbeb002f151eec`. The branch is
`backlog/cc-584-current-plan-publication`.

Cards and run headers now use the 60-minute state clock at preparation and at the
final send. Retired rows cannot resume a send. Possibly sent copies retain exact
coordinator readback, without another publish. A header requires a postable call
on its own destination and an image; plan cards cannot fall back to text.

Plan pages reread the existing public export and exact registration, status and
quote immediately before sending, including a delayed native action. A changed
state, stale quote or price outside the zone waits for an updated page. This build
chooses waiting instead of inventing a new dated market explanation.

New phase-bound pages, cards and charts distinguish cancellation before entry from
the stop after entry. The gold fixture retains Spot 3,972.6 and MGC 4,004.4 on their
own price bases. Its chart names both conditions without plotting a futures price
on the spot axis. The shared image consumer verifies the source and actual pixels;
an unannotated futures/spot mismatch still fails. Whole-sentence X continuations
retain these facts and clocks when they exceed one reply, keeping the canonical
link first and the authored points second.

New reader copy rejects pipeline wording, unnamed pricing percentages and prediction
market numbers. A source name must occur in bound evidence, not just writer metadata.
The existing coordinator can complete the EUR/USD Telegram/Notes links whose exact
stored cause is `TRADINGVIEW_FIRST_IMAGE_REQUIRED`, preserving their bytes and
identities. Known or uncertain writes cannot use that repair.

## Verification

All pytest runs used one process, no workers or parallel shards, and explicit
target files. No full suite, live publication, deployment or schedule change ran.
The controlled stores and media outputs are under `local-evidence/cc584/` in this
worktree; that directory is retained locally and is not committed.

| Evidence file | Outcome |
| --- | --- |
| `base-reproduction.xml` | 15 expected failures, zero errors, on the original base: stored late card/header, image fallback, page reread and copy defects |
| `base-phase-reproduction.xml` | 1 expected assertion failure on the original base: gold alert lacks the entry-phase labels |
| `cards-final.xml` | 30 passed: real card preparation, parent references and coordinator consumption |
| `final-action-after.xml` | 138 passed: native protocol and freshness tests; delayed action revalidates before claiming a write |
| `action-consumers.xml` plus `endpoint-cli.xml` | 68 passed and one obsolete fixture assumption, then the corrected fixture passed; it now distinguishes the immediate API pass from the later Neo pass |
| `phase-thread-after.xml` plus `phase-thread-points.xml` | 53 passed, then the explicit second-reply points assertion passed |
| `audit-acceptance-final.xml` | 42 passed: stored rows, current pages, source attribution, phase labels and exact link repair |
| `phase-image-consumer-after.xml` | 47 passed: final page/phase assertions and the shared publication image contract |
| `pages-links-final.xml` | 65 passed: canonical page, distribution and exact link-recovery regressions |

The before/after tests consume the retained rows in
`tests/fixtures/cc584/stored-plan-rows.json`, including gold work-item clock
`2026-11-12T17:48:36.204344Z` and header key `plan-run-post-6abb3bc55001d7b9ea3861ede3a19ae3`.
The original-base import overlay and its runner remain in
`local-evidence/cc584/baseline-overlay/`; this changed no checkout or operating source.

The rendered gold annotation was inspected from
`local-evidence/cc584/visual-review-accepted/test_new_page_alert_and_chart_0/tradingview-70f9d96a70a7f52b-16x9-levels-d0be07b2032e92fb.png`:
60,123 bytes, SHA256 `aab0946db3e04c509d3b0c0908a37503b66782e5c543cd39827bd2b0e7baa8fe`.
Both phase labels are legible, the original TradingView header/logo remain visible,
and no futures level is plotted. This is a retained-fixture render, not a live post.

Observed launch arguments configured `gpt-6.1-sol` and `model_reasoning_effort="max"`:
`CONFIGURED_NOT_OBSERVED` for actual model/effort runtime telemetry. Editorial tests
used controlled returns.

## Integration remaining

The first Publisher stream integrates this branch onto the operating HEAD through
CC-584's existing route. It then verifies the next plan's page/card/chart levels and
state clocks, and completes/readbacks the retained EUR/USD Telegram and Notes link
replies through the existing coordinator. This delivery is `BUILT_UNMERGED` until
that integration and live consumer verification; it does not claim public writes.
