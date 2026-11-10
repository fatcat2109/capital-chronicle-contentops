# CC-394 — One public result scorecard

The existing `scripts/plan_status_posts.py --publish` minute consumer now
updates one pinned Telegram message through `DurablePublicationCoordinator`.
It uses the official Bot API and the existing store, outbox and lease. No
schedule changes. Decision 106's selective feed posts remain unchanged.

The projection reads Main through its own export reader, then reuses
`result_rows_from_export`. HIT, STOPPED and EXPIRED share one dated ET form.
Main-supplied scored NOT_TRIGGERED results enter this record without adding
unfilled feed posts. Current untriggered expiries remain explicitly unscored.
Window-end direction is never inferred from prices. Public instruments and
mapped levels use the existing CC-384 projection; incomplete mappings keep
the original plan levels, identified in the line.

All held outcomes feed running totals. The message keeps the newest complete
lines within 4,096 UTF-16 units; it never selects by result. The existing
CC-379 weekly record remains the complete weekly publication. Removed export
rows cannot erase outcomes already held in this scorecard's outbox revisions.
Corrections replace their plan's current result without a second denominator;
the old immutable revision remains retained.

Only initial setup sends a scorecard message. Later results edit that same
public object. A store lease serializes updates. Lost writes require exact
Bot API readback and reconciliation before another write. Unknown creation
never sends a second message. Channel identity, current operating mode, Main
source bindings, private-data checks and the public notice remain enforced.

`--scorecard-only` updates just this record. Add `--dry-run` to render it
without any API or store writes. Normal `--dry-run --publish` also remains
read-only. No editorial model is called for this structured result record.

The initial targeted run passes 216 checks across the scorecard, CC-322
results, CC-400 export contracts, public output guard and CC-379 weekly
record. `targeted-tests.xml` is the evidence. The old CC-322 replay fixture
was corrected to put an aged outcome in a fresh export; advancing the whole
export four days tested the later freshness refusal instead of old results.
`live-preview.json` binds the actual five current results and their source
hashes. Integration and public readback are recorded separately after they
occur; the next newly scored result's 60-minute observation is not yet met.

Base: operating root `8e7b6f51e8ab8c4ce192a5fe054c203b047fbdcd`;
fresh `origin/master` is its ancestor. Branch:
`backlog/cc-394-pinned-results-scorecard`. Existing unrelated work is excluded.
The launch arguments configure `gpt-6.1-sol` / `max`, recorded as
`CONFIGURED_NOT_OBSERVED`.
