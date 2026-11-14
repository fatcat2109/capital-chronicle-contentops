CC-548 is live and its digest consumer is verified. On 14 November 2026, the
existing 19:15 GMT+7 task published the waiting 13 November digest and the
14 November catch-up digest. Both public pages and both email deliveries were
read back. The missed CPI article appears once across the two digests.

CC-548 repairs the daily digest's image check in the existing sole
`DurablePublicationCoordinator`. The branch starts at operating HEAD
`dfda65f03cf6f042827d37e8cd4bdd235eaca059`.

The 12 November dispatch `dispatch_eb2b3966e02acc41dff6e05958a7f067` was
`DEFINITE_NO_WRITE`, with no public object. Its frozen intent has no `output_dir`.
The image check previously tried to load `run_context_v1.json` from the current
directory before deciding that this digest has neither a market nor a release.

The chosen repair reads media directly from an intent with no run folder. It
also reads that intent's article fields directly, so an unrelated current
directory cannot supply its market scope. This keeps the full existing market,
release and image-template checks; it does not exempt a post merely because it
is a digest. Intents with a run folder retain the existing transport media
selection. Decisions 82 and 124 continue to require the correct charts.

Unexpected image-check failures keep their exception type, complete first cause
and any missing filename in the existing reconciliation row's status, following
`PUBLICATION_IMAGE_CONTRACT_INVALID: ` as JSON. The returned `reason_code` stays
`PUBLICATION_IMAGE_CONTRACT_INVALID`. A restart reads the saved cause without
rerunning the failing operation. Known contract refusals retain their existing
status codes. No schema, store or additional failure log is introduced.

The exact 12 November outbox intent and digest packet were copied through a
read-only SQLite connection into `tests/fixtures/cc548/`. Tests use these local
copies and temporary stores. The intent is 4,461 UTF-8 bytes, SHA-256
`df874981e4d393a59154d6a7b1a9db4b86ad159e6f220549089a4653ff4d2e5d`;
the packet is 4,021 bytes, SHA-256
`b4b5165d88b5e1d6ef45a4309279f8c1c4e4680227df75140131fbc32870c73b`.
The image itself is not copied or modified.

Launch arguments were read from the active `codex.exe` process: model
`gpt-6.1-sol`, reasoning effort `max`, `CONFIGURED_NOT_OBSERVED`. These are
configuration observations, not model-runtime telemetry. No editorial model
call was needed for this code repair.

The first sub-step passes 152 targeted tests in 472.69 seconds, in one pytest
process with no workers: `tests/test_publication_image_contract_cc548.py`,
`tests/test_publication_image_contract_cc463.py` and
`tests/test_publication_coordinator_v1.py`. The [JUnit result](image-contract-tests.xml)
includes the stored-intent replay, missing-chart refusal, original-exception
persistence and the coordinator's duplicate/recovery regressions. This was run
before the 13 November load restriction, at approximately 04:37–04:45 GMT+7.

The first repair is pushed as `b428c954`. The stored dispatch is also terminally
refused, so fixing validation alone would leave preparation returning the same
unsendable 12 November packet. The second sub-step changes the existing daily
digest preparation: an older `DEFINITE_NO_WRITE` with no public ID or URL carries
its held article records into the next day's digest. These records are already
held titles, links and publication clocks, so no fresh reporting or replacement
article is needed. Published digests alone consume article IDs and URLs. The
next selection deduplicates the held records against the feed and canonical
archive. Pending, unknown, partially identified and same-day attempts retain
their frozen recovery path. No old packet, intent or dispatch is rewritten.

The second sub-step passes 23 targeted checks in 29.45 seconds, recorded in
[the digest consumer JUnit result](digest-consumer-tests.xml). They cover
`tests/test_substack_daily_digest_cc548.py`, the existing CC-377 missed-article
case, the native digest identity/publish/readback loop and its email receipt,
cutoff/late-article selection, frozen pending-code continuation, existing public
page sequencing, and `tests/test_daily_digest_1900_route_v1.py`. Final review
also checks that a same-day or future refusal keeps its frozen identity. The
final total is 175 distinct passing targeted checks; no full suite or parallel
pytest workers were used.

The consumer test uses the retained `substack:224293572` record with and without
the public feed entry, builds the 13 November packet, passes its folderless
intent through the actual coordinator and repaired image validator, and confirms
one Substack dispatch with a fixture transport. A later digest excludes it.
The existing native loop reaches `VERIFY_IDENTITY`, `PUBLISH` and `READBACK`
with controlled tool returns. These are executable consumer checks, not public
publication observations.

At the initial delivery on 13 November, this stream's run prohibited live and
deploy steps, so the pushed repair remained `BUILT_UNMERGED`. Ops Product then
integrated it at `11830c6c16bdc709c2be249ce5a5d8a885db305a`, tag
`contentops-live-20261114-cc548`; the rollback tag is
`contentops-rollback-20261114-cc548` at `10fdbc53`. That live commit includes the
pushed repair `0bf688b269e6fa7d683542b79d39d63b2cc5e013`.

The completion run changes only this README, on
`backlog/cc-548-digest-live-readback`, cut from the operating HEAD
`d82c62829a73010ee97b613f4d0b56df9f3fb304`. Fresh Git ancestry checks confirm
the repair is in that base and in the current operating root. No live or
deploy command was run by this stream.

BrowserOS Neo readback on 14 November, 21:59-22:01 GMT+7
(`2026-11-14T14:59:00Z` through `2026-11-14T15:01:00Z`):

| Digest | Confirmed public page | Public post ID | Email stats |
|---|---|---|---|
| `cc143-digest-2026-11-13` | [13 November digest](https://capitalchronicle.substack.com/p/capital-chronicle-daily-digest-november-87f) | `224876543` | 5 recipients; 1 open; 20% open rate |
| `cc143-digest-2026-11-14` | [14 November digest](https://capitalchronicle.substack.com/p/capital-chronicle-daily-digest-november-7ee) | `224877983` | 5 recipients; 1 open; 20% open rate |

The email observations come from Substack's own post stats at
`/publish/posts/detail/224876543` and `/publish/posts/detail/224877983`.
They confirm platform-reported delivery and an open for each digest. No mailbox
or individual recipient list was read. The earlier "Data still processing"
observation remains valid for its earlier clock; it no longer describes the
current stats.

The 13 November digest contains exactly one body link to
`https://capitalchronicle.substack.com/p/if-october-core-cpi-is-03-or-higher`,
the retained article `substack:224293572`. The 14 November digest contains zero
links to that article and one to "How we measure a trading rule before trusting
it". Both pages contain their own digest card. This checks the live consumer's
missed-article recovery and the catch-up pass without sending another post.

The 19:40 GMT+7 backlog note names `224849463` for today's digest; that is the
linked article's ID. The digest's ID is `224877983`, confirmed by its route
result, native readback request, public page and matching stats title. The
earlier 19:16:21 and 19:32:33 GMT+7 dispatch clocks also precede the actual
publication actions: the saved publish observations show the single send
clicks at `2026-11-14T12:21:25.839Z` and
`2026-11-14T12:34:30.337Z` (19:21 and 19:34 GMT+7). The stats pages show
"Published at 7:21 PM" and "Published at 7:34 PM", respectively. These clocks
are kept distinct from packet freezing and dispatch preparation.

The original route artifacts remain at
`A:/Capital Chronicle/Runtime/ContentOps/daily_app_outputs/owner-manual/route-1900/`:

- `20261114T121519Z/10-publish-observation.json` records the first send;
  `result.json` preserves its then-pending email readback.
- `20261114T123154Z/10-publish-observation.json` records the catch-up send;
  `16-readback-observation.json` records 5 recipients and 1 open at
  `2026-11-14T12:55:12.512Z`; `result.json`, saved at
  `2026-11-14T12:55:43Z`, records `CONFIRMED`. It was absent at the earlier Ops
  inspection and is now present.

This documentation-only completion uses the existing passing targeted tests
and fresh live readbacks. No pytest process was needed or started. The launch
was configured as `gpt-6.1-sol` / `max`, `CONFIGURED_NOT_OBSERVED`; no editorial
model calls were made. The existing Monday follow-up remains as configured.
