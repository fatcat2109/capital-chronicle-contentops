# 12 November continuation

The continuation branch is `backlog/cc-402-audience-live`, cut from operating
HEAD `1c21bcfa` with the original two CC-402 delivery commits applied. Newer
CC-466 consumers and both unrelated telemetry/duplicate-ledger edits survive.
The launch configures `gpt-6.1-sol/max` (`CONFIGURED_NOT_OBSERVED`).

The weekly exporter now writes the installed overview's exact input,
`Runtime/ContentOps/audience-weekly/latest.json`. It carries the platform lines,
post-type/platform medians, publication-hour ET samples and exact observation
identities. CC-470's installed Publisher panel also reads those same durable
observations directly. Neither route needs a Main digest patch.

The exporter evaluates three complete weeks of confirmed public objects.
Every object in every week must have a measured zero reader counter; missing
counters or positive interactions cannot imply no readers. The sole publisher
settles a stopped type's new messages before transport. Issued messages and
existing attempts retain their exact readback and recovery. The stop evidence
stays in the same weekly export when the old posts age out.

Lane CLI usage is read from terminal counters in the existing launch/run files.
An item and local date must bind exactly one retained publication piece. Resume
counters are cumulative; the largest reported total is retained separately
from native role input/output tokens. No subscription tariff, fabricated split
or dollar charge is inferred. A multi-piece binding is left unassigned.

The installed run and acceptance results are in `integration.json` and
`live-acceptance.json` once observed. The original delivery evidence follows.

# CC-402: audience collection and piece usage

The existing minute plan-status consumer runs a bounded batch of read-only
observations for Threads, Facebook, Instagram, Discord and Telegram. It adds no
schedule or platform write. It reuses the durable observations, leases, exact
dispatch/reconciliation records, and existing weekly engagement exporter.

Each daily sample binds the dispatch, public object and CC-399 call/plan record.
Comments use comment counters, rather than media insights. Multiple call records
sharing one Instagram carousel retain their links; weekly platform totals count
that public object once and call totals disclose shared metrics. Collection is
dated when performed, never at a missed historical checkpoint. The weekly report
labels cumulative post snapshots and net account-snapshot differences separately.

The existing `model_invocations` table imports retained native responses. One
nullable metadata column preserves observed/configured model and effort, exact
source record, tokens and reported USD cost. Native subscription records without
usage or a per-piece bill retain null values. They never inherit an API tariff or
a fabricated zero. The UI reads those nullable values.

The branch was cut from operating HEAD
`789dcfc4a9ba4d1dfb9153730c595edf252b9732`; remote master is an older deployment
and would remove current consumers. Earlier telemetry/duplicate-ledger changes
remain outside this delivery.

Launch readback: codex.exe PID 21460, started 11 November 2026 12:58:56 GMT+7,
`--model gpt-6.1-sol`, `model_reasoning_effort="max"`.
Identity is `CONFIGURED_NOT_OBSERVED`; no runtime model telemetry is inferred.

The 10 November GMT+7 store readback has observations for all **143 confirmed
dispatches** across the five requested routes: Threads 42, Facebook 20,
Instagram 20, Discord 18 and Telegram 43. Instagram's 20 dispatches refer to
nine public objects. The aggregate does not multiply shared carousel counts.
The five ordinary CPI-preview derivatives carry no call id; the other 138 rows
carry their retained call/plan link. Existing damaged posts with a verified
identity supply their actual metrics while preserving their incomplete-content
state; those observations do not validate the planned copy. See
`day-acceptance.json` and the bounded `day-20261110-batch*.json` results.

The existing invocation table has **289** retained native response records.
The CPI preview binds six of them to its canonical work item. None of these
retained records exposes tokens or a per-piece USD bill; its cost readout says
`USD_COST_NOT_EXPOSED_BY_RUN_RECORD`, with null values. This is the exact
remaining telemetry limit, rather than a priced or zero-cost piece.

The real weekly export is
`A:/Capital Chronicle/Runtime/ContentOps/daily_app_outputs/weekly-engagement/engagement.json`.
It includes one digest line per platform and per-call totals. Current account
reads include Threads 3, Facebook 5,191, Instagram 1,192, Telegram 6 and an
approximate Discord member count of 2. These are snapshots, not acquired
followers; a comparable prior account snapshot is still required for a weekly
net change. Instagram's insights endpoint reports native error **#10**,
"Application does not have permission for this action"; its available comment,
like and follower reads continue. No wider scope was requested.

There are **205 distinct passing targeted cases** across collector, weekly
aggregation, learning, store, UI and call-card checks. The initial request-budget
assertion failure and its passing correction are retained in `validation.json`
and the XML artifacts. Tests ran one pytest process at a time. The initial
combined store/UI check was stopped at 55 seconds during a decision-run window;
the canonical files completed separately after 13:30 GMT+7.

The first delivery prepared `main-digest.patch` for the Main 07:00 digest.
Ops Product's 11 November OV-P4 amendment supersedes that dependency: the
installed private desk is the weekly table's consumer, and Publisher integrates
this item itself. The old patch and preview remain evidence of that delivery;
Main's source and production digest are not changed by CC-402.

The existing minute consumer runs collection even when Main's newest plan export
is stale, and records the collection result in its existing run record. It does
not publish, retry a write, adjust a schedule, launch another worker or change
account scope. Historical observation bytes and the ten old missed scheduled
samples remain unchanged; new daily snapshots retain the actual collection time.
