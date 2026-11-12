# CC-510 — measured base rates in reply facts

The reply pack calls `x_reply_base_rates_v1.collect` once during mobile fact
collection. It asks the installed CC-481 `stats_after` owner for the target
market's stated daily-move analogue, over one and five completed sessions.
Publisher preserves the returned hits, denominator, source instrument, historical
period, outcome horizon and interval. It converts a headline's percent threshold
to the producer's logarithmic-return units; it computes no outcome or base rate.
A record headline uses an explicitly labelled prior-252-session daily-breakout
analogue, never a lifetime-record claim.

The CC-506 census contributes the target market's active measured rows and their
conditions to the writer's bound context, ordered by sample size. Its market rows
contain n and average R, not a win numerator. No numerator is inferred from those
averages or the pooled construction percentages. The desk's own trade record is
never read. Only the statistics producer's hits and n enter these reply facts.

The existing fact policy refuses another market, a mismatching condition, a
future or incomplete sample, and a draft that changes the count, condition or
forward horizon. Sources are resolved again with the original as-known query
before delivery. Statistics failures remain source-local; other held facts
continue. The private message adds `Fact: base rate through <date>`, with the
count and period below it. The existing approved editorial callers still write
the reply; this adapter supplies structured facts.

Build checkpoint: `base-rate-tests-initial.xml` records 22 passing targeted tests,
including an isolated consumer path from collection through ranking, pack build,
source recheck and private-message formatting. No live consumer, Telegram send,
schedule, Main edit, deployment or application restart is run by Publisher-B.
The first Publisher stream applies the pushed delivery and observes the next
real private draft, as CC-510's integration line requires.
