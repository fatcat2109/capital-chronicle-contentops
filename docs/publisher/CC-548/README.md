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

Validation, delivery and the scheduled public readback are separate. The latest
direct run instruction says this second stream must not perform a live or
deploy step. The delivery therefore remains `BUILT_UNMERGED` for the first
Publisher runner to integrate. The existing 13 November task
`cc-contentops-digest-1900-bp`, due at 19:15 GMT+7, supplies the public readback.
Its accepted output must contain `substack:224293572` exactly once and record
the public digest URL here. No public digest URL has been observed by this run.
