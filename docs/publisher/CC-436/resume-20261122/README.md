# CC-436 · Neo status-post latency

Publisher installed the operation-scoped Neo identity lookup at
`2026-11-21T17:41:35.421318Z`. The two-minute live acceptance awaits the
next eligible Main status event. The Main transition export refreshed at
`2026-11-21T17:45:06.973040Z`; it contained zero transitions after the
installation. The production outbox also contained zero new status rows.

## Measured delay

The figures below use each copy's first verified receipt for its exact public
object, measured against the Telegram receipt for the same operation. The
durable X and Notes publish returns identify the BrowserOS Neo local endpoint.

| Main status post | X after Telegram | Notes after Telegram |
| --- | ---: | ---: |
| Oil fill | 173.979 s | 98.377 s |
| US 500 fill | 200.310 s | 175.590 s |
| Dollar-yen setup | 113.957 s | 103.948 s |
| Gold result | 157.908 s | 142.888 s |
| Bitcoin setup | 209.747 s | 108.882 s |

On the gold result, the browser routes claimed their attempts about 93 seconds
after Telegram confirmed. The just-in-time identity lookup loaded every Neo
outbox payload and then filtered by operation. A read-only SQLite sample counted
22,925 rows and 101,755,709 payload bytes in 17.63 seconds. The installed
lookup selects the operation's existing identity work item through the
work-item index. The request binding, five-minute identity freshness, composed
account check, atomic dispatch claim and exact-object recovery still apply.

## Verification

- Branch and installed focused runs each passed 20 tests. The plain Python
  copied-store child sent and verified an X card and a Note through the local
  MCP fixture. The tests also cover account mismatch, identity freshness,
  concurrent replies and recovery from a lost publish response.
- The existing `CapitalChronicle-PlanStatusPosts-V1` task runs
  `pythonw.exe -B scripts\plan_status_posts.py --publish` from the operating
  root. Its post-install run recorded `PLAN_ALERT_FANOUT` as `OK` at
  `2026-11-21T17:44:29.001311Z`, with zero newly queued posts.
- Source commit `c3fab8ee476c5f499a4c0e7d029246ce3e77b71e` is bound to
  `contentops-live-20261122-cc436-identity-scope`. Rollback tag
  `contentops-rollback-20261122-cc436-identity-scope` binds
  `05916cef16757aebfde259cbaa8ad7f89275dd3c`.

The branch starts at the operating root because it contains the installed
minute consumer and the earlier CC-436 changes. A clean checkout kept the
earlier worktree's local edits out of the delivery. Launch arguments select
`gpt-6.2-sol` at `max`, recorded as `CONFIGURED_NOT_OBSERVED`.

The read-only timing capture and JUnit files are under
`C:/CapitalChronicleScratch/cc-436-evidence-20261122/`. After Main supplies
the next eligible status event, Publisher reads the first exact X, Notes and
Telegram confirmations from the existing consumer and checks the 120-second
limit.
