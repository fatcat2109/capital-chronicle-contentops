# `ui/contentops_v5/` — Canonical V1 UI Contract

This is the only canonical ContentOps UI. It is a React/Vite/TypeScript surface over canonical
read models; it is not runtime/state/publication authority.

## Entry and commands

- active entry: `src/main.tsx` renders `views/DailyAppConsole.tsx`
- shared Daily App contract: `src/dailyAppTypes.ts`
- live read surface: `GET /api/daily-app/snapshot`; governed controls:
  `POST /api/daily-app/control/run-now` and `POST /api/daily-app/control/mode`
- legacy/fixture shell: `src/App.tsx`, fixtures/data adapters; do not mistake fixtures for live
  backend truth
- install/build/test from this directory with `npm ci`, `npm run build`, `npm test -- --run`

## Invariants

- Keep production truth sourced from canonical backend/read-model contracts.
- Clearly label fixture/demo data; never present it as provider/platform/readback truth.
- No credentials, browser storage/session extraction, public writes, or alternate backend state.
- Preserve accessibility, responsive desktop/mobile behavior, safety states, KILL_SWITCH,
  UNKNOWN_WRITE, readback, reconciliation, provider fallback, and incident visibility.
- Future Tier-2 UI extends this control room after product authority permits it; do not create a
  disconnected video dashboard.

`src/App.tsx`, broad fixtures, and the quarantined V6 `launchFullPipeline` surface are attractive
legacy traps, not the canonical Today runtime. Search the graph for `ui_calls_endpoint` and
`endpoint_to_read_model` before changing data flow.

Place component tests under `src/test/`; run focused Vitest tests and `npm run build` for shared
types, routing, or layout changes.
