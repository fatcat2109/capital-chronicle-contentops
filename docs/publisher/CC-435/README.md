# CC-435 - analysis links on every plan distribution route

Implementation is prepared on `backlog/cc-435-all-platform-analysis-links` from
operating HEAD `17c49b960d54a7dc6e090ab048fb047bd6c04a89`. The fresh remote default
branch predates the installed Publisher changes, so the new branch was first
advanced to that operating commit. Earlier lane edits are excluded from this item.

The existing status-post consumer now distributes confirmed CC-432 pages through
the sole DurablePublicationCoordinator. Telegram, Discord and Threads retain
their existing link identities. Facebook and Instagram use the existing official
comment adapters under their exact confirmed card or carousel. X uses the existing
Neo reply-thread owner and weighted text limits. Notes receives a standalone Note
with its canonical link card, whose visibility and target are checked at readback.
LinkedIn receives an official member API run index, keeping every confirmed page
link within its text allowance. No new scheduler, store or publication owner is added.

New run packets carry their available structured summaries and links. LinkedIn
gets one run post rather than separate roots for each card. Historical run packets
retain their existing destinations. A page confirmed after the run is consumed by
the same scheduled entry, with a separate exact link identity. A later new page
in a Main run produces an updated LinkedIn index snapshot; an unchanged snapshot
reuses its identity. Repeated ticks skip fully reconciled links. Missing parents
remain destination-local and never turn into an unrelated root.

Static parsing passes on all eight changed Python files. The focused Ruff
correctness check passes on seven feature/test files; the shared transport has
six unchanged baseline unused-import findings and no new finding, as recorded in
[validation.json](validation.json). The added regression file exercises the actual status-post entry and real
coordinator with controlled transports for all eight routes, duplicate resumes,
Facebook/Instagram comments, changed parents, X text limits, Notes link-card
readback and LinkedIn run binding. It has not been executed yet. Jim's instruction
for this run prohibits starting a test process before 10 November 22:30 GMT+7
(CC-035). The operating root and production publication state have not been changed.

Live access observations are in [route-readiness.json](route-readiness.json):
LinkedIn's official member API is ready; `DISCORD_BOT_TOKEN` is absent. CC-440
already owns the person-only Discord credential action. The existing Instagram
profile also shows no analysis website link. Before a new caption can truthfully
say "link in our profile", Ops Product adds the canonical Substack publication
link to that profile through its owned bio/about route. No browser edit was made.

Resume after 22:30 GMT+7 with one targeted pytest process on
`tests/test_plan_analysis_distribution_cc435.py`,
`tests/test_plan_analysis_pages_cc432.py` and
`tests/test_plan_call_cards_cc399.py`. Keep each run under one minute until 23:00
GMT+7. Fix any regression, commit and push, then fast-forward the Publisher
operating root while preserving its unrelated edits. The existing
`CapitalChronicle-PlanStatusPosts-V1` task already invokes the changed consumer;
no task definition needs changing. Complete and read back the pending destinations
through the same coordinator. Do not mark DONE until the next run's links are
confirmed on every required route.

The page/link CLI now supports `links` and `link-resume`, `link-readback`,
`link-begin`, `link-submit` with `--link-id`. Pass the actual native invocation ID
when handling a browser request. Use `--result` to save complete requests and
print identifiers only; media remains binary. Launch configuration was
`gpt-6.1-sol/max`, `CONFIGURED_NOT_OBSERVED` for actual model telemetry.
