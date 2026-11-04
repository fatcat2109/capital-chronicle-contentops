# CC-173

The read-only Substack inventory contains 639 drafts. Two are referenced by the
ContentOps store and 637 are classified `OLD_UNREFERENCED`. The referenced drafts
are `210796285` and `210865567`. Draft `166444043` has no creation timestamp in
Substack's response, so its CSV field remains blank. Every draft has a last-edited
timestamp.

The CSV is in the run output folder at
`A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\backlog\cc173-20261104\substack-drafts.csv`.
[validation.json](validation.json) records its hash, byte length, counts, source
capture clocks, store path and the five retained metadata batch paths. The capture
used the draft-list endpoint observed in BrowserOS Neo. Its 26 uncapped pages
reported a constant total and supplied 639 unique draft IDs. The count was checked
again at 05:36:41 GMT+7 on 4 November 2026.

The inventory command opens the canonical SQLite store with `mode=ro` and
`query_only=ON`. It compares explicit Substack identities in dispatches, canonical
outbox payloads, readbacks and native requests/results. A retained draft remains
referenced regardless of age. Missing schema or unreadable input raises an error.

The existing native and production runtime compositions pass their store into
`NeoDestinationHandoff`. Substack readback requests carry the referenced draft IDs
and exact URLs. Draft fallback uses those identities. An explicitly requested
unreferenced draft returns `UNREFERENCED_SUBSTACK_DRAFT_IGNORED` before the browser
executor is called. That result preserves unresolved publication ambiguity.
Exact public-object readbacks continue through the existing coordinator.

The focused tests cover the inventory, native runtime composition, native executor
and coordinator recovery. All 119 passed in one serial pytest process. Results are recorded in
[targeted-tests.junit.xml](targeted-tests.junit.xml).

The launch arguments configured `gpt-6.1-sol/high`, read from PID 49192, and are
recorded as `CONFIGURED_NOT_OBSERVED`. This engineering run used zero editorial
model calls.

The original delivery above was `BUILT_UNMERGED`. The 4 November continuation
integrates it into the current operating root under Jim's decision 39. It retains
the captured Substack inventory rather than treating a later store comparison as
a new browser capture. The current read-only store comparison still finds two
referenced drafts and 637 old drafts; there are now 16 total store references,
including public objects absent from that captured draft list.

The continuation launch is configured `gpt-6.1-sol/high`, read from PID 18132,
labelled `CONFIGURED_NOT_OBSERVED`; no editorial model call is needed. The current
readback normalization, ten-minute recovery observations, digest email evidence,
publication clocks and pending code-tab protections survive the integration.
See [integration.json](integration.json) for installed consumer verification and
[integration-tests.junit.xml](integration-tests.junit.xml) for the targeted run.
