# CC-435 continuation, 15 November 2026

The reporting repair is integrated into the Publisher operating root at
`f0b2351b0e2fde65fdb917676ccb31e0996e1b4a`. Full publication acceptance remains
incomplete. The existing Neo MCP endpoint returns
`NEO_ENDPOINT_CONNECTIONERROR`; LinkedIn's official API read fails with
`TRANSPORT_TLS_HANDSHAKE_UNAVAILABLE` despite current authentication. These are
current connection failures, separate from the resolved 11 November Substack
suspension. Only YouTube is in the current suspended-routes file.

## Repair and verification

The minute consumer now records each analysis link's exact dispatch identity,
public identity, reconciliation status, reconciliation clock and confirmation
boolean. A transport-confirmed Note with incomplete copy is explicitly
`confirmed: false`. The repair changes no issued copy, public object or retry rule.
It uses the existing distribution, coordinator, store and minute record.

The branch starts at operating HEAD `09e437371a04353173942183342c362e8d891a30`;
the remote default predates the installed Publisher work. The configured launch
is `gpt-6.1-sol/max`, `CONFIGURED_NOT_OBSERVED`. No editorial model was called.

- [Focused verification](reconciliation-tests-fixed.xml): 38 passed. The earlier
  [failed run](reconciliation-tests.xml) is retained; its new fixture attempted to
  replace an existing reconciliation using an insert-only method. The fixture
  now uses the store's status-update method.
- [Installed consumer verification](installed-consumer-tests.xml): 3 passed,
  35 deselected. It exercises eight-route distribution and both complete and
  incomplete readbacks through the actual minute-record consumer.
- [Integration and preservation](integration.json): exact file parity, unchanged
  operating WIP, and pushed live/rollback tags. No schedule or application changed.

Tags are `contentops-live-20261115-cc435-readback` and
`contentops-rollback-20261115-cc435-readback`. The first passing sub-step is
`f4c077e4`; the repair is `f0b2351b`. Both were pushed before integration.

## Current route evidence

This table concerns the latest confirmed plan page, Gold from
`shock-20261112T123542Z`, at its
[existing canonical](https://capitalchronicle.substack.com/p/gold-our-bearish-plan-39543964-entry).
It does not claim a fresh plan or an eight-route completed run.

| Route | Verified state | Remaining cause |
|---|---|---|
| Telegram | Existing exact link reconciled at `/182` | Its retained readback is from 13 November GMT+7; no new public-page read is claimed. |
| Discord | Exact API readback passed at 19:46 GMT+7 | None for this retained link. |
| Threads | Exact API readback passed at 19:46 GMT+7 | None for this retained link. |
| Facebook | No confirmed parent card for this page | `PLAN_ANALYSIS_PARENT_NOT_CONFIRMED`; no unrelated root or comment was created. |
| Instagram | No confirmed parent card; profile API read completed | `PLAN_ANALYSIS_PARENT_NOT_CONFIRMED`; `INSTAGRAM_PROFILE_ANALYSIS_LINK_MISSING`. |
| X | No confirmed parent card for this page | `PLAN_ANALYSIS_PARENT_NOT_CONFIRMED`; current Neo endpoint unavailable. |
| Substack Notes | Existing `c-385656965` has incomplete-content reconciliation | `RECONCILED_PUBLIC_OBJECT_CONTENT_INCOMPLETE`; exact readback needs Neo. |
| LinkedIn member | Existing run-index attempt is a definite no-write | Official user-info GET still fails during TLS; authentication expires 19 December. |

The [route matrix](route-matrix.json) holds exact identities, original dispatch
clocks and readback checks. [API readbacks](api-readbacks.json) keep this run's
actual observation clocks separate from the retained reconciliation clock.
The [Instagram profile observation](instagram-profile-readback.json) makes no
profile-link claim. [LinkedIn readiness](linkedin-readiness.json) is local auth
metadata; the [network read](linkedin-network-readback.json) is a separate failed
official GET. [Unauthenticated transport probes](linkedin-transport-diagnosis.json)
also fail using urllib and requests; urllib records connection reset 10054.

The [Neo observation](neo-endpoint.json) records failure of the existing local
MCP initialization. No browser tab, application or desktop control was used.
The minute-task observation is in
[installed-minute-observation.json](installed-minute-observation.json). The real
scheduled run at **19:54:54 GMT+7** records readback fields for 31 of its 53 link
rows, including the Gold Note's exact identity, incomplete reconciliation and
`confirmed: false`. Rows without an issued link retain their existing cause.
This proves the operating minute consumer uses the repair.

## Recovery

Ops Product restores the existing Neo MCP listener and LinkedIn API connectivity.
Publisher then reads back the exact Note before any possible send, and uses the
next eligible plan's existing coordinator path for the remaining routes. Closed
old attempts, retired work and the unresolved historical S&P Note retain their
identities; they are not a fresh publication queue.

Ops Product's separate profile action is to put
`https://capitalchronicle.substack.com/` in the Instagram profile website through
its owned bio route. The consumer already withholds the profile CTA until the
official API verifies it. This action does not prevent the other routes from
continuing.

No new post, reply, schedule, application restart or global KILL_SWITCH change was
made in this continuation. CC-435 cannot be marked DONE until the next eligible
run's full-analysis links have actually been read back on all eight routes.
