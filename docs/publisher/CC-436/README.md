# CC-436 — automatic Neo transport

The existing minute status-post consumer now selects an endpoint-backed
`NativeNeoExecutor` for X and Substack Notes. The coordinator, outbox, request
hashes, action claims, media bindings and readback/reconciliation remain the
existing owners. This adds no process, model invocation or schedule.

The client uses BrowserOS Neo's loopback MCP endpoint, its one existing window
and `codex/cc436-automatic-posts` group. A completed return records
`NEO_ENDPOINT_EXECUTOR` and `browseros-neo/run`, rather than an agent/model call.
Source/rights, account, exact copy, public-time and exactly-once checks stay in
force. A lost claimed publish return is recovered through readback, never sent
again by this transport. Uploads use Neo's upload tool on the bound files.

Validation at the first implementation sub-step (11 November 2026):

- `python -m pytest tests/test_neo_endpoint_executor_cc436.py -q --disable-warnings --tb=short`
  — 9 passed in 10.53 seconds.
- A plain Python child consumes a copied SQLite store through a local fixture
  MCP server and confirms one X object and one Note without a model or Codex
  child process. This proves transport/consumer mechanics, not public posting.
- Wrong account, changed composer, lost return and restart, and a changed image
  level have focused regressions. JPEG compression is accepted by measured pixel
  comparison; a changed card is rejected.
- The real Neo endpoint initialized successfully. Its existing signed-in X and
  Substack profiles and visible note readback were inspected through Neo only.

Live timing acceptance is pending: record the next genuinely new X and Notes
confirmations against their Telegram twins. Old pending objects and fixture
results do not prove the two-minute live requirement.

## Completed transport verification

- The installed entry, `scripts/plan_status_posts.py --publish`, opts into the
  endpoint transport. Other/manual callers retain their existing request/return
  path. Tests use isolated stores and a fixture endpoint.
- The same entry also consumes already-issued status/link requests whose API
  parent has completed. It preserves the original request hash and never
  rebuilds that frozen package. Expired claimed writes still get readback.
- Transient endpoint failure before an action claim keeps the exact request
  pending for the next existing tick. Wrong identity or preparation failure
  before the click is a definite no-write. A lost click/return stays uncertain
  until the coordinator reads it back.
- The real X composer retained two exact posts and a bound card, and the real
  Notes composer retained its exact text and bound upload. Both preparation
  checks stopped before Publish, and their temporary composers were dismissed.
- Real readback of [X object 2120129873830388070](https://x.com/Capitalnicle/status/2120129873830388070)
  found all five posts. Neo independently resolved its shortened canonical
  link. Both source-bound images matched X's public original representations:
  the chart's luminance delta was 30 (RMS 1.5315), and the TradingView PNG was
  byte-identical. Display thumbnails are not compared as source originals.
- The pixel check also rejects a changed level at 12, 18 and 34 pixel font
  sizes. Overflow DOM results are read from Neo's documented, bounded local
  output file; neither image bytes nor whole DOM files are printed.
- Final feature checks: 18 passed in 15.43 seconds.
- After merging the newer live suspension guard, the final feature and route
  guard run passed 21 tests in 18.55 seconds. The copied-store Python child
  explicitly uses an isolated control-file path, so tests never read the live
  suspension control.
- Final run-record verification: 22 feature/route tests passed in 16.95 seconds.
  The existing minute log now retains each drained operation, destination,
  request hash, outcome and cause, without public payload/media bytes.
- Coordinator, composed-return and CLI regressions: 124 passed in 133.97 seconds.
- Composed-return, plan distribution and restored-X checks: 49 passed in 48.80
  seconds. A historical test fixture's required destinations were aligned with
  that fixture's enabled destinations; production restrictions stay intact.

## Remaining live condition

The stored Notes identity is `@deancapitalchronicle`. At
`2026-11-10T20:26:17Z`, its live profile was unavailable; the page subsequently
reported **Profile not found**. Neo showed the signed-in business profile
`@capitalchronicle`. The executor preserves the stored binding and never
switches accounts or silently publishes as another handle.

The operating root subsequently advanced to `8cf4caec`, which records Substack's
account suspension on 10 November at 18:17 UTC. At 11 November 03:54 GMT+7,
the existing runtime control `control/suspended_routes.json` contained exactly
`{"substack_notes":"SUBSTACK_ACCOUNT_SUSPENDED"}`. CC-436 includes this newer
route guard; it leaves X available and prevents a new Notes write.

Ops Product's prepared action: resolve Substack's account suspension and restore
the verified Notes identity through the existing owner. Then observe
the next natural X and Notes confirmations against their Telegram twins. This
run's controlled endpoint results and old-object readback do not establish the
two-minute live acceptance test.

Launch arguments observed on PID 41068 at the original entry:
`--model gpt-6.1-sol`, `model_reasoning_effort="max"`;
`CONFIGURED_NOT_OBSERVED` (no runtime model/effort telemetry).
