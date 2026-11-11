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

Manual-reply readback, installed-consumer evidence and the live Neo link check
are the next sub-step. No schedule is changed; Ops Product owns cadence activation.
