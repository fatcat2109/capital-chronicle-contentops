# CC-464 — private Telegram X reply drafts

Decision 124 replaces CC-458's draft delivery. The existing minute entry in
`scripts/plan_status_posts.py --publish` runs `x_reply_bot_v1.refresh_due` before
Main export and chart/publication work. No schedule or application is changed.
The operator entry is `scripts/run_sourced_replies.py bot-refresh --store <store>`;
`bot-status` exposes only configuration/binding booleans.

The code first checks exact target identity, six-market/macro relevance and age
under 60 minutes. A known count of 20 replies excludes a crowded target. Missing
reply counts stay unknown, enter AGY's ranking as uncertain, and never become zero.
The existing CDP extractor now retains `reply_count` through its existing metrics
and feed projection; an already-running reader adopts it on its normal reload.
No ingestion process is restarted.

AGY ranks at most twelve new candidates. A score below 80 produces no draft.
The strongest eligible target goes to one bounded headless `gpt-6.1-sol/max`
text call; other strong targets remain available for the next minute. The writer
runs in a temporary directory with read-only permissions, no inherited project
or MCP configuration, and no persistent session. Native calls save exact inputs,
returns, clocks and configured model/effort under the existing Runtime output
folder. Their telemetry is CONFIGURED_NOT_OBSERVED. There is no Claude or paid
model API fallback. The private GMT+7 day admits at most five delivered or
uncertain drafts, with no padding to reach three.

The mobile policy is explicit on new requests. Old issued requests and posted
objects keep their bytes and their contracts. New replies have at most two
sentences, 22 words per sentence and 240 characters, with a dated, attributed
fact missing from the target. Base rate, positioning and priced-in are the three
shapes. There is no brand, disclaimer, first-person desk claim, link or advice.
Every number and the exact fact remain bound to the held public Main projection
or frozen public prose. A private paraphrased addition summary is not required
to be a literal public substring: the real native return exposed that unnecessary
check, which was removed with a test. No authored numbers were changed.

The already-named runtime binding is the only file holding the private chat id
or one-time Start code. The same bot identity is verified, getUpdates is read
once per minute tick, and a correct code binds only a private sender chat. The
consumer never sets a webhook. A separate getChat check refuses a channel,
group, changed identity or channel-name fallback before a draft send. Returns,
logs, outbox records and these evidence files contain no production chat id or
token. Skip accepts only that bound private sender and updates the existing
internal outbox. Telegram errors are redacted before they leave the adapter.

A message quotes at most 200 characters ending at a sentence, shows the author,
age, source fact and Good until clock, and puts the exact draft in monospace.
Open reply on X uses `/intent/tweet?in_reply_to=<id>&text=<draft>`; Skip uses an
opaque delivery key. An admitted source-bound chart/table is copied as binary
to this lane's Runtime media folder and sent first. An unusable optional image
is recorded and the verified text still proceeds. No agent sends, likes or
follows on X.

The delivery outbox is written before sending. Confirmed Bot API message clocks
record post-to-draft and post-to-delivery separately. Uncertain text sends are
never retried. A confirmed text delivery immediately parks `x_reply_tabs.json`
and writes the restore step in the adjacent Runtime `PARKED.md`; a later tick
recovers a stop between confirmation and parking without sending again.
CC-458's existing tabs are left alone. The old tab gate stays on until that
first real confirmed bot draft, as the item requires.

CC-455's observer remains wired through the same minute entry after publication
work, independently of the parked draft tabs. It reuses its two-hour observation
cadence, one temporary Neo reader tab and at most one reply detail. This is no
draft admission gate. Exact own-account reply edges feed the existing dispatch,
readback and performance owners, including both post-to-draft and post-to-reply
delays. Fourteen-day cohorts include target, shape and draft delay. Actual views,
likes and profile visits are collected at/after the 24-hour due time; unavailable
metrics stay unknown. No new scheduler, watcher, store or ledger is introduced.

Evidence:

- `run-context.json`: operating base, launch arguments and preserved WIP hashes.
- `binding-tests.xml`: nine initial private-binding checks.
- `final-reply-regressions.xml`: 72 focused reply/legacy checks.
- `canonical-regressions.xml`: 29 feed, status-entry and sourced-reply checks.
- `observer-consumer-tests.xml`: 54 targeted bot/entry/old-tab checks.
- `recovery-tests.xml`: four interruption/uncertainty/media checks.
- `native-proof.json`: the real 35-second AGY timeout, retained as a failure.
- `native-proof-60s.json`: AGY returned in 28 seconds; Sol returned in 69 seconds.
- `native-proof-reconciled.json`: one retained native draft builds with exact
  returned public bytes after the private metadata check was removed.
- `desktop-intent-proof.json`: Neo showed the exact target and prefilled reply;
  X adds its own trailing editor space. No submit occurred. This is desktop
  evidence, not a claim that a phone app has opened.

Source implementation, installed consumption, private Telegram delivery,
phone-app opening and Jim's actual X reply are separate observations. Live
integration and the first consumer results are recorded in `integration.json`
and `installed-consumer.json`. The five-minute target needs a genuinely recent
eligible post; an older retained post is never backdated. The item remains open
to its real phone/reply acceptance evidence and the later audience observations.

Official references checked through Neo: [Telegram Bot API](https://core.telegram.org/bots/api#getupdates),
[X Web Intents](https://docs.x.com/x-for-websites/web-intents/overview), and
[Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).
