# CC-384 — public instrument and both entry conditions

The existing plan-status composer reads CC-383's `entries` and
`public_instrument`, including the latter's aligned `entries`. One combined
conditional call carries the limit and breakout alternatives, the direction,
window and invalidation. The idea still has one queue identity and one first
post per API destination. X keeps its existing thread route.

Mapped prices are used only as a complete set. Null or incomplete mappings
retain the plan prices, explicitly labelled, and never fill or convert a null.
The fill post names the instrument. Only declared public fields enter the
composer; execution metadata is excluded. Existing rows without the new fields
keep their original text and package behavior. New rows carry format 3 so their
conditional lines remain intact in X threads; frozen older rows keep format 2.

Initial validation: 15 targeted tests passed in 6.19 seconds, in
[focused-tests.xml](focused-tests.xml). They exercise the export queue, card
facts, existing coordinator, destination limits and repeat suppression using
isolated stores and fixture transports. No real post was sent by these tests.

The branch starts at fresh remote master and fast-forwards to the operating
root's accepted `cdb2b25e`, preserving its current consumers. The two inherited
modified ledgers stay uncommitted. This run configures gpt-6.1-sol/high,
CONFIGURED_NOT_OBSERVED; no editorial model call is made here.

Pending: compatibility regressions, operating-root integration, and the first
real Telegram/Discord/Threads post after Main CC-383 integrates. No schedule or
other chat changes are part of this item.
