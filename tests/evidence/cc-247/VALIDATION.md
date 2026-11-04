# CC-247 media recovery

Started 4 November 2026 22:53 GMT+7. Base: operating root 4c156632505d08732360f2e46ea720722849759d, including Ops' d41e363f repost implementation. Remote master was refreshed; it predates the operating changes.

Launch readback: PID 20840, started 2026-11-04T15:49:56.999684Z, codex exec explicitly gpt-6.1-sol/high. CONFIGURED_NOT_OBSERVED; actual model telemetry is unavailable. The native media editor was explicitly assigned gpt-6.1-sol/max and records its own configuration and findings in sec-editor-response.json.

Focused checks: 44 initial recovery regressions passed; 53 repost, derivative and final-visual tests passed after the owner-removal and HTML-provenance repair; 18 media-repair and repost tests passed. XML results are alongside this file. Tests use disposable stores. No schedule or user application was changed.

Live deletion observations are in deletions-first.json and deletions-second.json. Both old Instagram posts, SEC Telegram 75 and SEC YouTube are unavailable. SEC Facebook is visible to its owner only in Trash. CPI Facebook 1443815231270226 remains Public and SEC X 2117784321562124568 remains live; neither is safe to repost. Jim's report is preserved separately from these live observations.

The shared HTML preview changed after CPI acceptance; exact approved PNGs, assets, payloads and source bindings did not. Existing acceptance now retains the original HTML hash as provenance while still checking exact accepted PNG and media bytes. Fresh assemblies still verify their actual HTML source.

The integrated recovery produced twelve destination repairs verified on live URLs in LIVE_READBACKS.md. SEC Substack's exact image edit and all four LinkedIn copies plus YouTube's new copy have accepted coordinator readbacks. The later fixes passed 3 focused publication-store tests and 2 completed-envelope tests. The latter accepts only the exact finalized hash and rejects a changed fact; no public write occurs in these tests.

The live continuation now scopes its projection to the current edition and its editorial opportunity rather than loading all historical outbox media. A first-send return can reconstruct the same deterministic canonical-bound envelope used at send time, preserving exact hashes and preventing a second send. Test fixtures prove those behaviors, while the actual public-object readbacks prove their live use.

One interrupted CPI company continuation left two own leases behind. Its Python worker was absent in the host process inventory; the exact lease IDs, owner refs and fencing tokens were released through the existing store API before resumption. No other worker or application was stopped.

CC-247 remains incomplete only because CPI Facebook and SEC X originals are still live and the two original Discord messages could not be edited by the configured webhook. The earlier file-picker concern is cleared: all actual uploads used Neo or input interception, and no native dialog opened. Earlier telemetry WIP remains uncommitted and preserved; this run's adapters appended their normal telemetry/freeze records without replacing it. No default-branch merge, schedule change, chat message or native desktop control occurred.
