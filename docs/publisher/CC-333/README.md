# CC-333: distinct images, two articles per day, Main scenarios

Decision 93 is applied through the existing publication coordinator, native writer,
media binding and eight-channel compiler. The first feature selection passed:
[feature-tests.xml](feature-tests.xml), 46 checks in 19.85 seconds. It started at
22:30:18 GMT+7, after the machine-load blackout, in one pytest process with a
55-second limit. All 104 canonical coordinator regressions also pass in
`coordinator-regression-1.xml` through `coordinator-regression-4.xml`. One initial
whole-file selection exceeded the 55-second load limit and was stopped; the
complete file then passed in four sequential bounded selections. Further affected
consumer and operating-root verification follow.

Native execution checks pass: 32 and 51 checks in the two executor selections,
plus 31 composed-action/surface checks (including CC-333's native-result resume
regression). A broader combined selection was stopped at 55 seconds before
these smaller sequential selections completed. Consuming a saved native return
does not rerun pre-write policy; `executor.begin` still checks an actual new
browser action. This preserves reconciliation of already-completed writes.

The affected source/renderer checks also pass: 24 production-day/TradingView,
44 native editorial/media, 87 image/time and 53 writer/compiler checks. Their
JUnit results are saved alongside this file. These selections use isolated
stores and fixture transports; they do not claim any new public article.

All 30 read-model regressions pass in six bounded selections. The final merged
feature selection passes 49 checks (48 CC-333 and the preserved CC-306 FILLED
export regression), in 32.24 seconds. It includes the actual current read model
showing the two-article ceiling with no deficit against the superseded target.
The operating root's intervening CC-306 commit
`e3ec0779fb06bab4b0aadcdfb37adadeb86ae15c` is retained by the merge.

The branch uses the operating root's `17836e3330e09b98d7b0f2cf7dd34389c345d94a`
source, preserving the Publisher consumers already 610 commits ahead of the
fresh remote default. This permits a forward integration into that live root.

The [public image inventory](public-image-inventory.json) records 22 Substack pages
and 51 content-image occurrences observed through BrowserOS Neo. The
[seed result](image-seed-result.json) also reads 245 retained coordinator send
records, including social copies and removed historical objects. Older social
cards held only in hosting manifests are included. Fingerprints feed the shared
runtime register beside `published_content_v1.jsonl`; source images stay binary
in the audit operation's media folder. Repeated Federal Reserve and Capitol
photographs are retained as published-image evidence.

The resulting register has 262 active records, 63 distinct exact image hashes and
62 distinct perceptual hashes. Five historical canonical dispatches have no
retained image binding after checking their run contexts and hosting manifests;
the seed result names them. That observation is preserved rather than inventing
an image. All images found in the current public archive and retained send
bindings feed the register; retrieval produced no errors.

The register stores SHA256 and a 64-bit perceptual hash. An article reserves its
image and a daily slot before its adapter runs. Unknown writes retain the
reservation until exact readback; confirmed objects retain their fingerprints.
The existing production day rolls over at 02:00 GMT+7. Public copy uses ET and
records use UTC. Images from one article can reach that article's own social
destinations without consuming another article slot.

Main's supplied probabilities, confirmation, six-market implications and
invalidation feed the article's scenarios section. Each field retains its exact
Main source span. The compiler carries the two authored scenario lines to all
eight social packages. TradingView snapshots use the existing CC-316 module,
before media review/registration, with its original attribution and free-page
rights. Release cards remain first in event pieces.

The run configured `gpt-6.1-sol/max`; actual runtime model/effort telemetry is
unavailable (`CONFIGURED_NOT_OBSERVED`). No editorial model was called by this
engineering step. Existing dirty telemetry/duplicate-ledger files remain outside
this item's commits. No chat, schedule or native desktop action was used.

No pytest run starts during the 6 November 18:30–22:30 GMT+7 machine-load
restriction. Targeted checks, integration tags and the two future public
readbacks will be recorded here when observed. Four articles were already
confirmed for 6 November before this item, so decision 93 permits no additional
article in that production day.
