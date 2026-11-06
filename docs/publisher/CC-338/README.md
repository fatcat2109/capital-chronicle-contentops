# CC-338: frozen public calls

The scorecard reads the existing confirmed publication feed and plan-post outbox.
One confirmed destination includes a call even when another channel is pending.
Removed posts remain in the population. Repeated state updates retain the original
wording. A changed call is a separate version. Execution states never enter the
public projection. Main supplies numerical scores; public states do not establish
returns or forecasting skill.

[Seven focused tests](scorecard-tests.xml) pass in 6.66 seconds in one pytest
process. [The operating-data read](observed-20261107/public-call-scorecard.md)
shows two calls since 6 November 00:00 ET: one invalidated and one triggered.
This projection is an observation through 7 November 01:35 GMT+7, not a public
publication or a numerical resolution. The exporter writes only its requested
output directory and reads the existing store without migration.

The item branch starts at the operating root's
`be449906fc6955acc984e49131111f36c9734d7e`. The fresh remote default is an
ancestor but lacks the live Publisher consumers, so retaining that live base
permits forward integration. Inherited telemetry, duplicate-ledger and CC-107
files are outside CC-338 commits.

Ops launched and resumed this run with `gpt-6.1-sol/max`.
`CONFIGURED_NOT_OBSERVED`: actual runtime model and effort telemetry is unavailable.
No editorial model call, schedule change or chat message was made by this step.
The future CPI preview, matching review attachment and event score remain to be
observed; this item is not DONE.
