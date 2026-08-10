# TASK_CONTENTOPS_V1_CHROME_PROFILE_CONTINUITY_LOCK_AND_LAUNCHER_CLOSEOUT_V1

Authority date: 2026-08-10

Result: `COMPLETE_IMPLEMENTED_AND_VALIDATED`

Owner fact: Jim manually reauthenticated X successfully in the existing canonical
`CapitalChronicleBot` Chrome profile. This task locks that binding permanently and closes the
remaining V1 desktop-ingestion reliability gap. FDA-G remains active; no newsroom cycle or
publication was manufactured.

## Permanent invariant

The canonical X ingestion binding is the existing operator-owned `CapitalChronicleBot`
persistent profile on Chrome CDP 9222:

- browser_family: CHROME
- profile_id: CapitalChronicleBot
- cdp_port: 9222
- role: INGESTION_ONLY
- user_data_dir: `%LOCALAPPDATA%\Google\Chrome\User Data\CapitalChronicleBot`
- canonical_route: `https://x.com/i/lists/1843870469143048642`

Single source in code: `live_contentops/ingestion_bootstrap_v1.py::CANONICAL_INGESTION_BINDING`.
ContentOps never creates, clones, migrates, resets, cleans, replaces, renames, deletes, or
silently falls back from it. No alternate path, no fallback profile, no Default/personal
Chrome fallback, no Edge fallback. Missing binding → `PROFILE_BINDING_MISSING` (never
mkdir/created). Unproven 9222 owner → `PORT_OWNER_UNPROVEN` (never killed/replaced). This task
does not guarantee X server-side session lifetime; it guarantees ContentOps preserves and
always reuses the exact operator-owned persistent browser state.

## Implementation

1. Hard profile continuity lock: explicit binding constants; fail-closed missing-directory and
   wrong-owner paths; `canonical_ingestion_readiness()` is the single-source readiness used by
   both the launcher and the run-now preflight.
2. Run-now fail-fast: `POST /api/daily-app/control/run-now` now performs the bounded canonical
   ingestion-session readiness check. Only READY accepts a new operator trigger. Logged-out
   session → `INGESTION_REAUTH_REQUIRED` with zero durable trigger. Unverified session →
   `INGESTION_SESSION_UNVERIFIED` (fail closed). CDP absent → one exact one-click bootstrap
   attempt then recheck; still unproven → `INGESTION_UNAVAILABLE`. Downstream
   freshness/evidence gates unchanged.
3. Launcher output: `Chrome Profile Binding: LOCKED`, `Chrome 9222 Ingestion: …`,
   `X Ingestion Session: …` lines; profile continuity != provider authentication lifetime.
4. Preservation invariant regression suite: no profile delete/clear/clone/rename path, no
   guest/incognito/temp profile flags, no non-canonical user-data-dir launch, no Edge
   ingestion binary path, no indiscriminate Chrome termination.

## Validation

- Pre-check (visible-URL/CDP method only): CDP 9222 owner = exact CapitalChronicleBot
  profile; canonical X list route active; no login redirect → READY.
- Focused tests: `tests/test_contentops_profile_continuity_lock_v1.py` 13 passed; refreshed
  ingestion/launcher/operator-trigger/read-model suites 74 passed.
- Bounded cold-reopen continuity proof (ingestion idle, no capture active):
  A. authenticated READY verified;
  B. graceful close of ONLY the exact proven browser (WM_CLOSE; no taskkill /F);
  C. CDP 9222 confirmed gone;
  D. `Start_ContentOps_Daily_App.cmd` → reopened exact user-data-dir, CDP returned,
     X session READY;
  E/F/G. two more launcher runs → exactly one ingestion browser, session stayed READY.
- No new profile created, no duplicate browser, no profile reset/delete/clone, no fallback.
- One controlled safe-idle production restart deployed the run-now fail-fast; production
  store/epoch preserved; FDA-G soak epoch restarted from the corrected source SHA with all
  prior soak evidence preserved.
- No secret/session exposure; protected `v1.0` untouched.

Machine evidence: [chrome_profile_continuity_lock_evidence_v1.json](chrome_profile_continuity_lock_evidence_v1.json)
