# CC-177 continuation, 5 November 2026

The Publisher source was already integrated at the start of this run (336824d1).
This continuation fixes the remaining Publisher desk-reader compatibility gap:
Main exports 1.3.0, while the reader validated only 1.0.0. The three newer schemas
are copied byte for byte from Main commit 98150b81; the original schema remains
unchanged. Unknown schema versions, changed bytes, future exports and unknown
fields still fail. Published reports now retain their event id when that id is a
Field, so the existing evidence join accepts them.

Both new-input profiles now preserve their existing public-report and research
roots and add the real retained non-fixture CC-014 export by exact path and hash.
That export was generated on 30 October 2026 at 22:22:05 GMT+7. It supplies dated
source facts, not fresh news. This does not move Ops' recurring after-NFP binding
or mutate any already-frozen operation. No fixture is enabled in these bindings.

The three-file schema/desk-consumer selection passes 104 checks. Its new cases
execute the existing feed through native selection for schemas 1.0 to 1.3, retain
exact public values and precision, reject unsupported contracts and future bytes,
and keep private execution fields outside public model input. One old assertion
expected superseded J8 photo-less guidance; it now checks Jim decision 42's current
image requirement while retaining exact request-resumption/conflict assertions.

Main weekly digest readers, CC-136 integration and the recurring finished-run
export are still separate Main/Ops work. Final installed readback and dispositions
are recorded below after integration. No editorial models or public sends were
invoked. Launch: gpt-6.1-sol/high, CONFIGURED_NOT_OBSERVED.
