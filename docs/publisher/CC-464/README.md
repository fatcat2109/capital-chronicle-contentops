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

Live result, 11 November 2026 23:28 GMT+7: source commit `4334924c` is pushed
and fast-forwarded into the existing operating branch. All six installed source
hashes match. All six dirty operating files were preserved at the initial merge;
the two runtime ledgers subsequently received normal runtime appends, and their
original prefixes remain byte-identical. Both dirty lane files remain preserved.
The installed tests passed 36 checks in 22.45 seconds. No schedule or application
was changed, and Main was not edited.

The actual minute task ran the new consumer; `scheduled-and-readback.json`
records its outcomes. Its original valid dated positioning text was reconciled
without redrafting or changing bytes. The same bot's getChat proved the bound
private destination, and Bot API confirmed private message 3 at 23:28:17 GMT+7.
`first-private-push.json` preserves the actual clocks: post-to-draft 39.50 minutes,
post-to-delivery 44.51 minutes. This retained target proves the delivery route,
not the five-minute target. There was no invented recent target or backdated clock.

The first confirmed draft parked CC-458 immediately. Runtime's adjacent
`PARKED.md` contains its restore action, and `installed-consumer.json` confirms
that gate is off. The exact Neo own-reply reader then ran successfully and found
no manual reply. No agent submitted anything on X.

CC-464 is **BLOCKED: FIVE_MINUTE_PHONE_AND_FIRST_JIM_REPLY_PROOF_PENDING**,
with the implementation integrated and operating. It is not waiting for Ops
review or deployment. The existing minute task can deliver the next genuine
fresh high-quality target; no polling loop was added to manufacture acceptance.
Jim's one prepared action is to tap **Open reply on X** on private bot message 3
and press Reply if he accepts the draft. A phone open and actual own-account reply
cannot be inferred from the Bot API response or desktop intent proof. The first
real reply feeds both delays and the 24-hour/fourteen-day audience record.

## Continuation — 13 November 2026

The previous result above records the first delivery. The current delivery branch
continues from operating HEAD `42af12d1`, with the installed CC-495/509/510/511/512
fact, quote, topic and caller fixes retained. The launch explicitly configured
`gpt-6.1-sol/max`; its model and effort remain `CONFIGURED_NOT_OBSERVED`.

`resume-20261113/timing-diagnosis.json` traces the second real private delivery:
target `2120872859266699313`, posted at 20:34:28 GMT+7 on 12 November, reached
Telegram at 20:43:03 GMT+7, **8.58 minutes** later. Its first ingestion lag was
38.265 seconds. At 20:37 GMT+7 it already ranked above the quality floor, but the
writer took a different target. That peer failed `FACT_DRIVER_LINK_NOT_STATED`.
The valid opportunity waited another tick and another ranking call. The earlier
tick's stage clocks also show that batching alone cannot guarantee five minutes;
upstream tick delay and actual native call duration still count.

The existing consumer now sends up to two qualified, distinct-author targets to
one bounded MAX writing call, capped by the day's remaining delivery slots.
Each draft still passes its own source, same-market, freshness, copy and private
destination checks. A rejected peer does not delay another valid draft. The
quality floor stays 80; the shared cap stays five, including uncertain sends.
No draft is added to satisfy a count. Expiry during ranking skips that target
and lets a fresh qualified peer proceed. Historical requests keep their bytes.

The writer uses the three fact records per target that were supplied to ranking,
with their complete context. Other usable sources remain in the saved request.
Two native replays reached the old 90-second limit without a final answer,
including the narrowed 9,014-byte prompt. Both failures remain in the evidence.
The writer's finite limit is now 150 seconds for at most two drafts; its MAX role
is unchanged. Neither failed replay made a delivery. The existing bounded
Codex JSONL caller now consumes `turn.completed` directly for the MAX writer,
with tool use disabled and session/usage telemetry retained. AGY's actual
65-second timeout is recorded separately from its Codex fallback's 65 seconds.

`native-budget150-replay.json` records the real MAX return after 138.67 seconds.
It authored both selected targets. Its oil draft named WTI, Russian supply and
their relationship with the verb "affect"; the check's narrow verb list rejected
it. The measured false rejection is fixed, with positive and wrong-subject tests.
`native-return-revalidated.json` admits that exact unchanged return; the other
draft still fails its market relationship check. No new writing call, historical
delivery, post clock adjustment or five-minute success is claimed. The 73 targeted
fact/driver checks pass, including the retained wrong-market and stale-fact cases.

New delivery observations retain post-to-ingestion, ingestion-to-filter and
filter-to-delivery seconds, plus `five_minute_target_met`. Revalidation preserves
the original clocks. Unavailable ingestion clocks stay unknown. Five minutes is
the measured target; CC-495's 15-minute send limit remains in force.

Build and installed evidence is under `resume-20261113/`: the 72-check regression
run, three additional clock checks, and 87 installed bot/pack/caller checks passed.
The initial regression artifact retains its obsolete 90-second timeout fixture
failure; the fixture and real timeout label were corrected. `integration-code.json`
records the operating merge, matching source hashes and six preserved dirty files.
Code `d3641bac` and its live/rollback tags are pushed. Subsequent bounded-context
verification and exact current consumer readback are recorded alongside them.

`browser-readback.json` records a fresh bounded own-replies view and the official
[Web Intents documentation](https://docs.x.com/x-for-websites/web-intents/overview).
The documented endpoint already supports reply identity, mobile web and installed
app handlers; the existing exact desktop intent proof remains available. No
matching manual reply was visible in the inspected newest posts or held readback
rows. This establishes neither a phone opening nor global reply absence.

The phone opening and Jim's first reply remain separate required observations.
Jim's prepared action is unchanged: on the next **unexpired** private bot draft,
tap **Open reply on X**, review the target and filled text, then press **Reply**
once. The existing observer imports that exact edge and both delays afterwards.
Old messages 3 and 4 are expired and must not be sent. CC-458 stays parked.
No schedule, application, Main source or trading state was changed.

Final result, checked 13 November 2026 03:28 GMT+7: code `0a6a79a6` is pushed
and integrated in the operating root, with live and rollback tags. The installed
73 fact/driver checks pass; the earlier installed 87 bot/pack/caller and nine
changed-writer checks also pass. `resume-20261113/final-live-readback.json` records
the normal consumer using `draft_limit=2`, exact installed source hashes and
preserved WIP. The latest completed tick had no candidate above the quality floor.
Confirmed delivery ages remain 44.51 and 8.58 minutes, with zero five-minute
deliveries and zero manual-reply readback rows. The 138.67-second historical MAX
return proves the bounded writer can complete; it is not a current phone delivery.

**BLOCKED: JIM_PHONE_OPEN_AND_FIRST_MANUAL_REPLY_REQUIRED (decisions 122–124).**
All repair and integration work in this continuation is complete. The separate
five-minute natural-delivery proof remains open; no replay or expired draft is
sent to manufacture it. On the next unexpired private bot draft, Jim opens the
filled reply, reviews it and sends once. The installed observer then records the
exact reply and both delays. Nothing waits for Ops review or deployment.
