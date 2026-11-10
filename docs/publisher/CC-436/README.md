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

Launch arguments observed on PID 41068 at the original entry:
`--model gpt-6.1-sol`, `model_reasoning_effort="max"`;
`CONFIGURED_NOT_OBSERVED` (no runtime model/effort telemetry).
