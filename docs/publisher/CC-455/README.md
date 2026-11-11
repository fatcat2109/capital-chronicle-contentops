# CC-455 — Jim's daily X reply pack

Decision 122 changes the last step of CC-386's sourced-reply workflow: the runner
writes a private JSON/HTML pack, and Jim opens, edits and posts each reply himself.
The pack path calls neither the publication coordinator nor an X transport.
CC-386's parked automated reply path stays parked.

The branch starts at accepted operating HEAD
`b671d91ea927dab3a7423a9fb5ba7b943224523b`. Fresh `origin/master` is its ancestor;
starting there preserves the applied Publisher changes. `run-context.json` records
the launch configuration (`gpt-6.1-sol/max`, CONFIGURED_NOT_OBSERVED) and hashes of
the existing lane/live edits, which remain outside the delivery.

The existing `scripts/run_sourced_replies.py` adds `pack-prepare`, `pack-build` and
`pack-status`. Preparation reads CC-258's held list and the existing production
store's public desk projection and frozen public setup calls. A native editorial
response chooses useful posts and writes the drafts. It is source-bound again at
build time. No model/effort label gates the response; actual and configured
telemetry stay distinct. No Claude call or paid model API is added.

`target-accounts.json` extends CC-386's PeterSchiff target with five finance
accounts already in the held list. It does not invent follower counts. Original
target posts must match their author/ID/URL, be younger than 60 minutes, and cover
a market or macro topic. At most five target authors enter a pack. Mentions and
quotes of @Capitalnicle enter the same drafting input, including other authors.
Retweets, stale posts and unusable drafts retain their causes; the pack is never
padded. A source used in a frozen request remains usable after a newer feed scan.

Each reply has an exact source number, its source's ET clock, the current analysis
notice and a specific addition. The existing public-copy, private-data, preview
host and public-time checks apply. Source clocks are not refreshed by preparation.
The HTML escapes held post text, shows post ages and hides each intent link at
90 minutes. Intent links carry only the exact target ID and authored draft.

Files use the private desk's GMT+7 date, matching CC-457:
`Runtime/ContentOps/daily_app_outputs/x_reply_pack/reply-pack-YYYYMMDD.json` and
`.html`. Public reply prose uses ET. The pack also has an immutable internal
outbox record, `PREPARED_FOR_JIM`; it creates no X intent or dispatch.

First sub-step: `pack-tests.xml` records 27 passing focused checks, including
CC-386 regressions, actual JSON/HTML consumption, exact intent decoding, source
and target changes, clock/expiry handling, private-copy refusals, retained source
reuse and zero agent dispatches. Ruff passes for the changed Python files.

The same runner now also has `pack-observe` and `pack-report`. Each build reads
the held own-reply feed once. `--mentions-feed` and `--reply-feed` accept the
existing signed-in reader's saved rows; they never start a browser or a reader.
A manual readback requires @Capitalnicle's exact author, URL, post ID and
`in_reply_to_status_id` (or `in_reply_to_id`). Similar wording is insufficient.
Jim's edited text is retained separately from the draft. Observed manual objects
use the existing dispatch, readback, reconciliation and performance tables;
their outbox destination stays internal and no public X outbox is created.

The dispatch registration's optional observed clock preserves the actual post
time, rather than the later import time. That clock and public identity are
write-once. The DAILY observation is due 24 hours after the actual post.
Reader rows may supply `metrics_observed_at_utc` and `metrics` (`views`, `likes`,
`profile_visits`); early captures cannot prove a 24-hour result, and missing
metrics never become zero. `pack-report` groups the last fourteen days by target,
reply shape and ET build time. The next native preparation receives that feedback
and its fourteen-day review clock, so audience evidence feeds future selection.
No target is dropped because a metric was unavailable.

`consumer-tests.xml` records 96 passes across the pack, canonical store and
existing reply tests. `final-pack-tests.xml` records 21 pack passes, including
bare-domain link refusal. `feedback-and-html-tests.xml` adds the final three
selected checks for feedback reaching the next native request and HTML handling.
These are targeted runs, one pytest process at a time; no full suite was run.

One real pack was built at **11 November 2026 07:33 GMT+7**, from the live feed,
with three drafts (202, 213 and 208 characters) bound to frozen euro, S&P futures
and WTI futures calls. Its JSON/HTML are in the agreed Runtime directory. Its
internal outbox key is
`x-reply-pack-477ed70a83a9551f0ea09a3edab044a3fce2618877946adaca3b42953887b985`.
`browser-intent-proof.json` records three actual Neo reply composers, each under
the expected author/post with the exact draft prefilled, and zero submit actions.
The real HTML was opened and its rendered pixels inspected. Jim's and other
agents' tabs were left as found. No file upload or native dialog was used.

No schedule is changed. Ops Product owns 08:15 ET and release-plus-ten-minute
cadence activation, after its consumer read. Jim's first actual manual reply and
its real readback/24-hour metrics remain future observations; controlled tests
prove the consumer path, not a reply that has not been posted.

Installed source: `b92f4c5c977bb18077979aa6183ae7d08ed34a1b` was fast-forwarded into
`A:\Capital Chronicle\ContentOps` on its existing operating branch. The fresh
installed `pack-status` read the three-draft pack; `pack-observe` found zero
manual replies. `installed-consumer.json` records those actual CLI results.
`integration.json` verifies four installed source/config files and all nine
earlier lane/live dirty files by hash. No application was restarted.

`cc457-consumer.json` also executes the exact delivered CC-457 consumer at
`baba261ee396a0796f5714e4f9b7943c0b719e5d` against the real Runtime pack: READ,
three exact intents and no issues. This is its delivered parser with the normal
file-reader interface, not an installation of the desk UI. Publisher's real HTML
consumer remains available independently. Its displayed private source clocks
use GMT+7; record clocks stay UTC and the drafts themselves keep ET.

Live tag: `contentops-live-20261111-cc455`; rollback tag:
`contentops-rollback-20261111-cc455`. The remaining acceptance step is outside
the agent's posting authority under decision 122: Jim opens one prepared link,
reviews the reply and posts it himself. The existing reader then supplies its
exact reply-edge row to `pack-observe`; no agent substitutes a reply for him.
No actual manual reply or 24-hour result is claimed in this delivery.
