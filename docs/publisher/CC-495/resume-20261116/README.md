# CC-495 — three natural private deliveries verified

The remaining delivery acceptance passes. The first three private drafts after
the original CC-495 installation were Bot API-confirmed within 15 minutes of
their target posts. Each uses an immutable same-session observation, retains its
source and market binding, and has a plain-language fact-age field. These are
existing natural deliveries; this continuation sent no message and ran no model.

| Private message | Confirmed delivery, GMT+7 | Fact and source | Post to delivery | Fact age label |
|---|---|---|---:|---|
| 4 | 12 Nov 2026 20:43:03 | Brent futures; Yahoo Finance, 12 Nov | 8.5797 min | today, 8:31 AM ET (11 min old) |
| 5 | 13 Nov 2026 20:43:38 | Dollar index as an explicit gold driver; CNBC, 13 Nov | 8.3204 min | today, 8:40 AM ET (3 min old) |
| 6 | 13 Nov 2026 20:53:12 | WTI futures; Yahoo Finance, 13 Nov | 5.5920 min | today, 8:40 AM ET (12 min old) |

The Brent and WTI drafts explicitly connect their market to Russian energy
supply. The dollar draft states its relationship to gold. The exact source
artifacts still match their hashes. The existing production fact checker and
send-time checker pass against each original saved pack at its original check
clock. The labels above are a replay of the installed phone-message formatter
with the persisted send-time binding; Telegram message bodies and phone screens
were not read. The delivery records confirm messages 4, 5 and 6, not that Jim
opened them or sent a public reply.

[readback.json](readback.json) binds each delivery, receipt, pack and source by
identity and SHA256, and preserves the editorial calls' model, effort and
timings. Configured identities remain `CONFIGURED_NOT_OBSERVED` where runtime
model and effort telemetry are absent. CC-509's existing quote collector supplied
these same-session sources; it reads held Main/native observations before its
public quote route. The historical missing-source result is superseded by the
three actual source bindings.

| Private message | Filter | Ranking | Drafting | Checks | Telegram send |
|---|---:|---:|---:|---:|---:|
| 4 | 4.78 s | 37.23 s | 50.17 s | 0.22 s | 0.88 s |
| 5 | 9.19 s | 58.63 s | 117.78 s | 0.26 s | 0.92 s |
| 6 | 10.32 s | 52.00 s | 94.36 s | 0.36 s | 0.96 s |

All three missed the five-minute target. The saved records retain post-to-draft
and post-to-send-attempt minutes separately from confirmed delivery. Messages 5
and 6 also retain ingestion and selection clocks; message 4 predates that added
breakdown. Missing historical ingestion clocks remain unknown. The original
44.51-minute rejected draft remains the documented startup/reconciliation case:
it was already 37.67 minutes old at the first tick. Its record is
[first-draft-timing.json](../first-draft-timing.json).

[dropped-candidates.json](dropped-candidates.json) reads the original run records
from the installed-policy readback through 16 Nov 2026 04:10:43 GMT+7. It lists
3,379 distinct dropped candidates and 6,143 distinct candidate/cause pairs across
2,846 saved records. Repeated appearances retain their first and last clocks,
count, original artifact and payload hash. No candidate lacks its identity or
recorded cause. Two non-code causes retain their exact recorded wording; no
retained target text, private chat identity or raw model response is exported.
Six post-policy private delivery receipts exist at this snapshot; the acceptance
uses the first three in time order.

The installed baseline run passed 87 tests and exposed one outdated test fixture:
CC-603's new follow-up hook reached an uninitialized temporary test store.
The fixture now isolates that hook and the plan-page consumer, prevents a Main
export read, and verifies private drafts precede both slower consumers even with
a stale export. Production code is unchanged. The corrected targeted run passed
all 88 tests in 85.17 seconds with one pytest process. Its fixtures use temporary
stores. The original failed run remains in
[installed-tests-initial.xml](installed-tests-initial.xml); the passing run is
[targeted-tests.xml](targeted-tests.xml).

Eight installed source/entry files match this branch byte for byte. The saved
minute-consumer result at 16 Nov 2026 04:09:45 GMT+7 is
`NO_NEW_ELIGIBLE_TARGETS`. Its existing scheduled entry remains
`pythonw.exe -B scripts\plan_status_posts.py --publish` in the operating root.
The continuation changed no schedule, application, source producer or trading
state. Its only implementation change repairs the isolated test fixture.

Reproduce the one-shot saved-evidence read from the repository root:

```powershell
python -B docs/publisher/CC-495/resume-20261116/readback.py
```

The reader opens SQLite with `mode=ro` and `query_only=ON`; it never invokes the
consumer, a source fetch, a model, a bot API or a browser. It writes only these
item evidence files. [run-context.json](run-context.json) records the actual
launch configuration, operating base and the original uncommitted-file hashes.
The Publisher operating-root merge, installed check, live/rollback tags and
preservation readback are recorded in `integration.json` when applied.
