# Final Daily App Autonomous Publication Runtime and Transport Lock V1

Authority date: 2026-08-10

Status: `COMPLETE_IMPLEMENTED_AND_VALIDATED`

## Capability delivered

The Final Daily App now has one durable publication coordinator as its only new-public-object
owner. The rolling-X newsroom returns a deterministic, no-callable publication plan. Before
any adapter call the coordinator persists exact outbox intent and a
`DISPATCH_ATTEMPT_STARTED` marker. A restart before the marker safely resumes once; a restart
after the marker becomes `UNKNOWN_WRITE`, performs readback only, and never blindly retries.

The production composition wires the canonical durable store, production orchestrator,
newsroom, coordinator, transport registry, readiness probes, readback/reconciliation,
performance observation, bounded learning, and loopback V5 read-model API. The production
start command is:

```text
python -m live_contentops.cli daily-app start --store-path "A:\Capital Chronicle\Runtime\ContentOps\contentops_daily_app_v1.sqlite3" --output-root "A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs"
```

## Locked transport authority

| Surface | Transport |
|---|---|
| Substack article | Edge CDP 9223 |
| X post/thread | Edge CDP 9223 |
| LinkedIn post | Edge CDP 9223 |
| YouTube Community post | Edge CDP 9223 |
| Telegram channel post | Bot API |
| Discord announcement | Webhook/API |
| Facebook Page post | Meta Graph API |
| Instagram Business post | Meta Graph API |
| Threads post/thread | Threads API |

Chrome CDP 9222 remains ingestion-only. There is no silent transport fallback. YouTube
Community is distinct from future YouTube video/Short upload, whose future transport remains
the YouTube Data API `videos.insert` path.

## Proof summary

- Historical nine-surface live capability evidence and accepted adapter commits were inspected.
- Controlled cases A–L and historical adapter result shapes pass.
- The mixed API/CDP exactly-one-write fixture remains one adapter call per destination after a
  duplicate tick, restart, and recovery tick.
- A SHADOW_ONLY one-start proof showed a live supervisor, loopback API, V5 snapshot, nine
  destination-health rows, clean shutdown, and restart reconstruction.
- The real read-only preflight verified all nine current Tier-1 destination identities as exact
  `READY_AUTHENTICATED` or `READY_NON_BROWSER_BINDING` bindings.
- No real public write, browser write, provider write, or unknown public write occurred.
- Production schema v7 was copied and migrated losslessly, then backed up byte-for-byte before
  the append-only v8 migration. All pre-existing rows and the production epoch were preserved;
  no readiness history was fabricated.

Detailed machine-readable provenance is in `transport_provenance_v1.json`.

## Next stage

`TASK_CONTENTOPS_FINAL_DAILY_APP_FINAL_V5_UI_BROWSER_QA_V1`
