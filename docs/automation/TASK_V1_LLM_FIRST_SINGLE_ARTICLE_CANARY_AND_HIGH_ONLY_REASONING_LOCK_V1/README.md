# V1 LLM-first single-article canary and HIGH-only reasoning lock

Status: `IMPLEMENTED / FOCUSED_TESTS_PASS / REAL_CANARY_PENDING_PROVIDER_RESET`

Base: `839713160e6594d6a61fa8223aed98be9122ff25`

## Implemented current delta

- canonical V1 rolling-X path accepts one `LLM-FIRST / VALIDATE-AFTER` provider adapter;
- current governed candidates and published memory reach a HIGH coordinator before the old
  evidence-ready/sourceability/capability/readiness/media/SEO admission stack can veto writing;
- one fresh isolated HIGH worker performs read-only research and returns one canonical article,
  explicit cited-source records, exact supporting excerpts, and material-claim bindings;
- deterministic public retrieval verifies the exact cited bytes after generation;
- unsupported material fails closed and permits at most one same-thread HIGH revision;
- verified evidence/article bytes re-enter the existing PR #20 grounded article, final validation,
  release-lock, publication-plan, and exactly-eight-undispatched-intent path;
- zero public write is hard-coded for this canary route;
- coordinator, writer, revision, and official SDK fallback now request no effort above HIGH;
- legacy XHIGH schema/decision names remain only for historical/runtime compatibility.

## Current real-run state

The genuine current-headline run used 1,123 accepted 24-hour intake rows and completed canonical
assignment/preselection. The official ChatGPT-authenticated SDK reached the fresh isolated HIGH
writer boundary, where the host returned `RATE_LIMIT / usage limit` with a stated retry time of
5:05 PM. No writer result was accepted, no article/package was qualified, and public/provider/
unknown writes remained `0 / 0 / 0`.

The rerun remains the same architectural canary, not a 4/32 exercise. It must resume only after the
external usage state changes; no weaker model, non-Codex author, public write, or fabricated article
may substitute for it.

## Validation so far

- focused HIGH-lock/provider/worker/newsroom/production-day/handoff tests: `125 passed`;
- affected newsroom/article/production-day/Desktop/provider suite: `275 passed`;
- Python compileall: PASS;
- CodeGraph generation/check: `CODEGRAPH_CURRENT`;
- `git diff --check`: PASS.
