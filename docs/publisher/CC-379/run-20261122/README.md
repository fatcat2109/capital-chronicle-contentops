# CC-379 weekend wrap, 22 November 2026

The [22 November wrap](https://capitalchronicle.substack.com/p/weekend-market-wrap-november-22-2026)
was published web-only at 13:38:58.939 UTC as Substack object `226039671`.
The public heading, count line and all 17 ordered rows match the frozen
16–20 November ET section. It contains 9 scored calls, including 2 hits,
1 stop and 6 window-end closes, plus 8 unscored expiries.

The existing weekly route used operation `cc689-weekly-2026-11-22`, plan
`351e7f275e5d0f00882e78d8df4873c06531ee50cbbbedfb660d97f8a4fdc817` and the post's
original Substack dispatch `dispatch_6aa47ffdb24a2ec46a47e356254df270`.
The runtime `wrap-pack.json` SHA-256 is
`a2509f2eb4383692ef8223ad81fb8b30cd7b2c6db00623e4724c15b472cf0f11`.
The weekly plan export content hash is
`64534117699a3cbfb5335c89ea9e7e0ac92bda300526f998bcde07925814123f`.
The 9–13 November edition missed its original publication window.

The first Substack attempt saved draft `226039671` and returned
`PLAN_SUBSTACK_EXACT_DRAFT_MISMATCH` before any publish click. The editor had
retained literal list bullets while the check had removed them from the expected text.
Before the readback fix, this run directly set the retry state in the live store,
then published the same draft in Neo outside the coordinator. The installed
coordinator subsequently read back that exact public object, verified its copy
and chart, and recorded `RECONCILED_CONFIRMED` without a further Substack write.

The repair is live at `1b3ae1b353f7e6e43ac9b7ddc583c5af9cf79a59`.
It compares rendered list text on both sides and admits an observed canonical
through the existing wrap dispatch and strict readback owner. The branch
passed 57 tests on the editor fix, 69 on the reconciliation change, and 63
after the final readback comparison adjustment. The installed source passed
51 targeted tests. Live tag `contentops-live-20261122-cc379`. Rollback tag
`contentops-rollback-20261122-cc379`.

Antigravity's section draft timed out after 65 seconds. The existing fallback
used the exact eligible source lines. The desk pass returned and passed its
source checks, with `gpt-6.2-sol/max` configured. Per-call provenance is in
the operation's `wrap-changes/light-call.json` and `wrap-desk/light-call.json`.
