CC-199's Instagram recovery repair is pushed and live at
`a8e08a4b7ae90f71470d7a611b7df17f64a74bfa`, tagged
`contentops-live-20261115-cc199-instagram-validation`. Its rollback tag is
`contentops-rollback-20261115-cc199-instagram-validation`. Integration was a
fast-forward into `A:\Capital Chronicle\ContentOps` at **18:00:59 GMT+7 on
15 November**. [Integration](integration.json) and
[installed module identity](installed-consumer.json) retain the exact bytes.

Local Instagram image validation no longer trips the destination's failure
circuit for the ET day. Existing validation incidents remain readable and no
longer hold a repaired image. The coordinator now writes the per-attempt
outcomes that its retry and Neo freshness consumers already expect. Repeated
definite validation refusals do not exhaust the retry reserved for a possibly
sent post. An ambiguous retry still requires readback and cannot reuse an
earlier validation refusal. Actual provider failures retain the day circuit.
No new store, scheduler or publication owner was added.

[Thirty affected checks](affected-coordinator-tests-final.xml) and
[six checks from the installed operating root](installed-consumer-tests.xml)
pass. They use disposable stores and the real coordinator. The installed
module matches the tested builder bytes; no application restart was needed.
The [test history](test-execution.json) preserves the earlier failure and
interrupted selections. Three existing site-link cases remain skipped under
decision 83 in the initial selection; no full-suite result is claimed.

**Publication acceptance remains 0/3.** The
[read-only installed-consumer reading](installed-three-piece-acceptance.json)
uses the latest three original articles. Digests and plan pages keep their
separate contracts. This retained sample does not replace the three new pieces
requested by Ops on 12 November.

| Article | First text approval, GMT+7 | Destinations with stored image proof | Last verified readback after approval |
| --- | --- | --- | --- |
| Measured odds, 14 November | Not observed | 8/10 | Unknown |
| CPI preview, 10 November | 18:32:49 | 7/10 | 51.45 minutes |
| Pre-US wrap, 9 November | 19:10:35 | 10/10 | 31.36 minutes |

The 14 November export omitted existing opportunity-bound reviews. The
corrected reader uses `NativeReviewedPublication.projection`, retains CPI's
three reviews and the wrap's one review, and restores their original approval
clocks. The outcome remains failing. Creation, dispatch, media refresh and
later readback clocks never replace text approval. Missing media proof remains
unknown rather than becoming a confirmed image.

The outside blocker is **YOUTUBE_EXTERNAL_LINK_VERIFICATION_REQUIRED**.
The current route control still suspends only YouTube; the exact retained
14 November pre-publish refusal and its original wording are bound in
[source and route state](source-and-route-state.json). This run did not probe
the restricted destination, retry a send or claim a new platform observation.
The earlier LinkedIn absences and Southwest Threads missing-image recovery
remain available under their exact original identities.

A new Main report completed during this run. The installed source and clock
consumers admitted its original **16:54:47 GMT+7** capture at the
**17:33 GMT+7** source check; its 60-minute deadline was **17:54:47 GMT+7**.
It was used in the source assessment and was not turned into a new article by
this delivery-verification run. No publication or timing acceptance is claimed
for it, and its original clock remains bound.

The [preservation check](preservation.json) verifies all eight inherited WIP
paths across both checkouts. No public post, native editorial role, browser or
desktop control, chat message, schedule change or live-store migration occurred.
The observed launch configuration is `gpt-6.1-sol/max`,
`CONFIGURED_NOT_OBSERVED`; actual model/effort telemetry is unavailable.

Next: complete the one-time external-link verification for
`@CapitalChronicleYouTube`; Ops Product clears only that route's suspension.
Publisher then measures the next three timely, approved Main pieces through
the existing coordinator, with exact image proof and readbacks inside 30
minutes. Old sends and late repairs cannot create a passing sample.
