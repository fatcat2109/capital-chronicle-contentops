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

First checks: 17 collector/engagement cases and three canonical store/UI checks
passed. Provider probes returned Threads views/replies and account followers,
Telegram public-page views, and Meta account followers. Comment reads returned
their own zero-like counters. Exact outcomes are in `provider-probe.json`.

The 07:00 digest renderer belongs to Main. Its proposed consumer change is
delivered as a patch for Ops; this Publisher branch never edits Main's live root.
The first production digest line and complete per-piece usage remain acceptance
claims only when their actual retained records support them.
