# ContentOps Browser-Rendered Source Recovery V1

Status: `IMPLEMENTED / LIVE_SHADOW_PROVEN / NO_PUBLICATION_AUTHORITY`

Authority date: 2026-09-01

This slice addresses the isolated `BROWSER_RENDERED_SOURCE_RECOVERY_ARCHITECTURE` objective.
It improves evidence acquisition when a current, exact publisher URL is useful but ordinary
HTTP cannot obtain the rendered article body. It does not replace the V1 scheduler, store,
editorial owner, publication coordinator, browser publication profile, or Core Analyzer.

## Architecture

The recovery order is:

```text
exact allowlisted HTTPS publisher URL
-> ordinary bounded HTTP retrieval first
-> one BrowserOS Neo rendered-page recovery only after an eligible 403/429,
   rendered-body insufficiency, or exact route-health suppression
-> final URL/host, publisher identity, timestamp, semantic text, and dual hash validation
-> existing evidence resolver and epistemic/claim validation
-> existing Simple Gemini writer and native eight-package compiler
```

The new adapter is `live_contentops/browser_rendered_source_recovery_v1.py`. It uses a small
stdlib MCP client pinned to the loopback BrowserOS Neo endpoint, protocol `2025-06-18`, and
server identity `browseros-neo`. It opens a task-owned background tab and uses only
`name_session`, `tabs`, and `read`; it closes the tab in a `finally` path.

The browser result is a distinct evidence class:
`READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE`. Its rendered Markdown and canonical visible text have
separate hashes. It never claims to be raw HTTP bytes. The loader still assigns reputable
secondary source class only after exact host/final-URL identity, hash, timestamp, and safety
checks pass.

Hard boundaries:

- one browser recovery attempt per loader invocation, inside the existing six-request ledger;
- any BrowserOS tool-reported truncation or rendered payload above the configured byte ceiling
  fails closed before a `PASS` result exists;
- the evidence loader independently rejects any rendered response whose `content_truncated` field
  is absent or not exactly `false`, so truncated bytes can never set `public_claim_allowed=true`;
- no click/type/evaluate/upload/download/login/consent interaction;
- no cookie, token, storage, credential, or session-material read;
- no model call in browser acquisition;
- no factual, numeric, editorial, publication, or Core Analyzer authority from the browser;
- no scheduler, durable-store, publication-coordinator, or public-write call;
- HTTP route health is preserved as routing telemetry; browser success does not erase an HTTP
  failure or turn it into HTTP success.

## Integration

`SimpleFirstPartyAwareEvidenceResolver` accepts an injected `rendered_source_get` callback and
keeps browser and HTTP acquisitions on the same shared request ledger. The default Simple V1
loader now wires `BrowserOSNeoRenderedSourceRecovery` for the existing reputable-secondary
allowlist. The existing `epistemic_state`, material-claim, writer, revision, and native
derivative validators remain unchanged owners of admission and reader-facing truth.

The browser lane is deliberately not used for discovery URLs, arbitrary social posts, cross-
publisher redirects, or authentication failures. A paywall/login screen is rejected as
`browser_rendered_access_gate_detected`, not treated as article evidence.

## Tests

Focused coverage includes:

- MCP protocol/server identity and loopback endpoint validation;
- exact publisher hash-bound read-only recovery;
- cross-publisher redirect rejection;
- login/subscribe gate rejection;
- tool-reported and configured-byte-ceiling truncation rejection;
- defense-in-depth loader rejection of any truncated rendered response before claim authority;
- 401 non-recovery and route-health-suppression recovery;
- HTTP 403 and 200 JavaScript-shell fallback;
- shared request ledger, one-attempt cap, distinct retrieval provenance;
- existing report/event epistemic-state integration;
- existing scheduler/coordinator/publication regressions.

The initial focused run passed **210 tests** across browser recovery, secondary evidence, Simple
resolver/epistemic/article paths, scheduler/process, publication handoff/recovery, and
publication coordinator suites. After the fail-closed correction, the local regression run passed
**324 tests** (including **28** browser-rendered/evidence/authority tests) across the same product
path. The browser/evidence subset now covers route health, provenance propagation, wrapper removal,
tool-reported truncation, byte-ceiling overflow, and loader defense-in-depth claim blocking.

## Measured live improvement

The proof reused one real fresh V1 candidate from the natural PR #53 epoch, without rerunning
selection, scheduler work, or publication:

- candidate: `simple-story-41216eee7974418f024946e3`;
- prior natural receipt: `NO_PUBLICATION`,
  `ALL_ADMITTED_CANDIDATES_SOURCE_RETRIEVAL_BLOCKED`, accepted source count `0`;
- prior primary attempt: `3` ordinary source requests and an observed HTTP 403;
- BrowserOS Neo `0.0.49`, MCP `2025-06-18`, semantic `article` scope;
- recovery result: `PASS`, one accepted source, `2` total acquisitions (HTTP failure + one
  rendered recovery), retrieval method
  `READ_ONLY_BROWSEROS_NEO_RENDERED_PAGE`;
- source identity: `www.bloomberg.com`, title
  `Bond Investors Wary After Warsh Speech Fuels Rate-Hike Bets`;
- rendered source had dual hash-bound content and `EXACT_BOUND_DISCOVERY_TIMESTAMP`;
- existing epistemic lifecycle: `DIRECT_REPUTABLE_REPORT`, `UNCONFIRMED`,
  `SINGLE_SOURCE`, reader label `SINGLE-SOURCE REPORT - BLOOMBERG`;
- existing deterministic article proof: `PASS`, `9` supported material claims, `0` unsupported;
- existing native compiler: exactly `8/8` derivative packages and `8/8` intents,
  `PREVIEW_ONLY_UNDISPATCHED`;
- acquisition model calls `0`; Codex runtime model calls `0`; publication-coordinator dispatch
  `0`; public writes `0`; `UNKNOWN_WRITE` `0`.

The live readback artifact is outside the repository at:

`A:\Capital Chronicle\Runtime\ContentOps\browser_rendered_source_recovery_proof_v1\live-readback-20260901T074510Z.json`

The final direct Neo readback after wrapper-removal and truncation fail-closed guards is:

`A:\Capital Chronicle\Runtime\ContentOps\browser_rendered_source_recovery_proof_v1\final-live-readback-20260901T075626Z.json`

The end-to-end zero-write article proof is at:

`A:\Capital Chronicle\Runtime\ContentOps\browser_rendered_source_recovery_proof_v1\browser-rendered-source-proof-20260901T015200Z`

This is a one-candidate measured conversion improvement, not a claim that the 5–8/day target
is proven. It is also not current account/session readiness or live-publication proof.

## Resume state

The isolated browser architecture objective is complete enough to return to the main V1
objective. `PRODUCT_FIRST_AUTONOMOUS_V1_RESUME` applies from the locked PR #53 epoch
(`1c0354347e51d7b84bd7e41386d7bf428709e4bf`) and its natural autonomous windows:

```text
merge/deploy corrected source-recovery bytes
-> four already-activated natural routine windows
-> observe real evidence/article/publication/reconciliation failures
-> fix the measured blockers toward 5–8 useful articles/day
```

A fresh standalone preflight or one-off canary is not a prerequisite. Use either only when current
evidence materially requires bounded diagnosis of an exact identity/readiness ambiguity,
unresolved `UNKNOWN_WRITE`, irreversible-risk boundary, or other hard stop. Existing inline
live-write identity, readiness, canonical readback, and reconciliation gates remain fail-closed.
Do not rerun the historical Italy canary, create a second scheduler/store/coordinator, replace CDP
publication transports, or treat this shadow proof as a public-write canary. BrowserOS Neo remains
a source-recovery/diagnostic layer; `SIMPLE_GEMINI_RUNTIME` and
`DurablePublicationCoordinator` remain the V1 owners.
