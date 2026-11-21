# CC-489 continuation — 22 November 2026

The CC-489 implementation is at `86c942ac9183ff5bd56ffd9574b918afae3b1834`
and is tagged `contentops-live-20261122-cc489-r1`. This evidence package is
integrated in operating-root commit `0beb6253c6ce24cec27122e50791fc2d24fc410e`
under `contentops-live-20261122-cc489-r2`, with rollback
`contentops-rollback-20261122-cc489-r2`. The focused consumer and audit checks
pass with 48 tests.

The audit now excludes derivative rows for a canonical article from the plan
chart denominator. A derivative can carry the same chart bytes without a
plan-status market or price-scale check. Counting that row as a plan chart
created a false missing-comparison result. The regression is in
`tests/test_chart_price_audit_cc489.py`.

The read-only live register audit is in [live-audit.json](live-audit.json).
The complete 17 November production day has 5/5 compared plan charts (100%),
with no missing-quote refusal. The later observed days retain named gaps,
including stale or unavailable source clocks, and are not rewritten as
compared.

The three-day calibration window beginning 17 November is incomplete for
US500, EURUSD, USDJPY and USOIL. XAUUSD and BTCUSD have three observed ET
dates. The four pending markets retain the approved starting limits until
natural live captures provide the missing dates. No quote, chart, image,
publication, schedule or runtime state was written by this audit.

Verification: [targeted-tests.xml](targeted-tests.xml), 48 passed in one
pytest process.
