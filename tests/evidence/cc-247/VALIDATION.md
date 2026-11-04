# CC-247 media recovery

Started 4 November 2026 22:53 GMT+7. Base: operating root 4c156632505d08732360f2e46ea720722849759d, including Ops' d41e363f repost implementation. Remote master was refreshed; it predates the operating changes.

Launch readback: PID 20840, started 2026-11-04T15:49:56.999684Z, codex exec explicitly gpt-6.1-sol/high. CONFIGURED_NOT_OBSERVED; actual model telemetry is unavailable. The native media editor was explicitly assigned gpt-6.1-sol/max and records its own configuration and findings in sec-editor-response.json.

Focused checks: 44 initial recovery regressions passed; 53 repost, derivative and final-visual tests passed after the owner-removal and HTML-provenance repair; 18 media-repair and repost tests passed. XML results are alongside this file. Tests use disposable stores. No schedule or user application was changed.

Live deletion observations are in deletions-first.json and deletions-second.json. Both old Instagram posts, SEC Telegram 75 and SEC YouTube are unavailable. SEC Facebook is visible to its owner only in Trash. CPI Facebook 1443815231270226 remains Public and SEC X 2117784321562124568 remains live; neither is safe to repost. Jim's report is preserved separately from these live observations.

The shared HTML preview changed after CPI acceptance; exact approved PNGs, assets, payloads and source bindings did not. Existing acceptance now retains the original HTML hash as provenance while still checking exact accepted PNG and media bytes. Fresh assemblies still verify their actual HTML source.

The integrated recovery produced six confirmed public objects. LIVE_READBACKS.md lists exact URLs, five observed owner removals, two still-live originals, Discord's actual webhook failures and the retained browser requests. Focused tests include compiler continuity, exactly-once first-copy recovery, wrong-operation unclaimed request replacement, claimed-action readback fencing, and avoiding repeated full database/day scans. XML files record each targeted run; no whole-suite result is claimed.

CC-247 remains incomplete: two original deletions are still pending, both Discord edits failed exact-message readback, and the browser work requires Jim's file-picker check before continuation. No default-branch merge, schedule change, chat message or native desktop control occurred. Earlier telemetry WIP was preserved; live adapters appended this run's records to the existing telemetry/freeze files without replacing them.
