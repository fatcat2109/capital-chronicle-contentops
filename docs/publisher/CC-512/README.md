CC-512 is integrated in the Publisher operating root `A:\Capital Chronicle\ContentOps`. The delivery was merged onto operating HEAD `71633590d8647ba1bee8fc3df5db582e04f37cac`, preserving CC-511. The implementation commit is `b86b26251da5b61e2e4d495235ae8f7f6a8dcf0b`; the integration branch is `backlog/cc-512-light-caller-integrate`. The initial live and rollback tags are `contentops-live-20261112-cc512` and `contentops-rollback-20261112-cc512`; the final live evidence tag is `contentops-live-20261112-cc512-verified`. `integration.json` and `installed-source-readback.json` identify the installed code and its checks.

The image review, plan-post variants and reply ranking share `live_contentops/light_model_caller_v1.py`: Antigravity first, then the same guarded prompt once to Codex on a timeout or empty answer. Codex is explicitly `gpt-6.1-sol/low`, using ChatGPT login, a read-only sandbox, an empty working folder, no inherited user/project configuration, disabled model tools, and one finite stdin request followed by EOF. Images use `--image`. Source/copy checks and the deterministic image gate judge each return. A second failure preserves the first named AGY cause and records the fallback cause. Existing successful results remain cached; a failed pre-CC-512 preparation may continue once while preserving its original bytes. This creates no retry loop, scheduler, store or publisher.

The saved-call diagnosis remains in `ranking-diagnosis.json`, `saved-ranking-calls.json`, `saved-image-calls.json`, `image-input-diagnosis.json` and `cli-versions.json`. Of 65 saved ranking calls, 48 returned and 17 timed out with zero stdout. None began with the required no-tool guard. The answered-call 90th percentile was 64.57 seconds; 45/48 answered calls fit 65 seconds. This is not a 90% success rate across all 65 attempts: the censored timeouts remain failures. The primary bound is 65 seconds, followed by a measured low-effort Codex return rather than another long blind AGY wait. Ranking's 65-second fallback keeps both light attempts plus the existing 90-second writer within the 270-second lease. Images have a 120-second fallback because a native 65-second image attempt failed. Original cause names retain their compatibility suffixes; actual limits and elapsed seconds are explicit per attempt.

The retained failed image was 87,847 bytes; its prompt was 2,886 bytes, and the separate chart prompt was 3,834 bytes. The installed image prompt was 3,038 bytes. These observations do not support image size as the universal cause. AGY's saved version is 1.5.5; its version command timed out at ten seconds, so the executable hash is retained without inventing a fresh version return. Codex reported 0.167.0-alpha.3.2. AGY 1.5.5 rejects image content blocks; its supported local-PNG read is the sole image-tool exception in the guarded prompt. AGY must show that read; Codex must have the exact image attachment. A text guess cannot create a score.

A native Codex diagnostic found `turn.completed` before CLI pipe teardown. The adapter now returns the completed turn, closes stdin explicitly and ends only its own child if teardown stalls. The real child-process regression reproduces a completed answer followed by a hanging exit. During installed observation, AGY also returned valid JSON inside a Markdown code block. The ranking parser initially tried to parse it before removing the fence; `scheduled-fenced-response-diagnosis.json` preserves that actual failure. The shared consumer parser now strips the fence before decoding. Tests cover both callers through ranking and variants; the exact observed answer replays successfully through the installed consumer without another provider call (`installed-fenced-response-readback.json`).

Installed calls completed on 12 November GMT+7:

| Role | First caller | First result / seconds | Second caller | Answer seconds | Consumer result |
|---|---|---|---|---:|---|
| Image check | Antigravity | Timeout / 65.33 | Codex, configured Sol low | 11.86 | REVIEWED, ten answers; score 1/10 |
| Plan variants | Antigravity | Timeout / 65.35 | Codex, configured Sol low | 17.57 | PREPARED; seven source/copy checks passed |

`installed-image-call.json` binds the same retained event-table PNG, its source metadata and the exact installed consumer. Its low score still refuses the image (`IMAGE_VISION_REVIEW_REQUIRED_OR_FAILED`); a complete model call does not accept a deficient template. `installed-variants-call.json` binds the confirmed EUR/USD Substack page and original source plan. The exact already-issued outbox payload remains unchanged. Its returned fields pass the normal source, copy and destination-length checks; this integration did not publish another object. The incomplete pre-interruption image attempt has no completion result; its prompt and schema remain in Runtime and are not counted as a successful or timed-out call.

The existing scheduled reply consumer independently read CC-512 after installation. `scheduled-consumer-readback.json` retains four observed calls: three successful returns and the preserved fenced-response failure. Actual Antigravity and Codex answers both occurred without forcing a failure or starting the job. No schedule was changed and no extra run was triggered. The saved fenced answer also passed the installed parser after its correction; a replay is recorded separately from a new model call.

Validation used one pytest process at a time, targeted files only, no workers, shards or full suite:

| Check | Passed | Reported seconds | Artifact |
|---|---:|---:|---|
| Merge caller checks | 21 | 4.69 | `integration-caller-tests.xml` |
| Three merge consumers | 91 | 36.95 | `integration-consumer-tests.xml` |
| Fence correction and text consumers | 71 | 28.33 | `fenced-response-consumer-tests.xml` |
| Installed caller, before fence correction | 21 | 3.77 | `installed-caller-tests.xml` |
| Installed image protocol | 4 | 1.34 | `installed-image-consumer-tests.xml` |
| Installed final caller, with fence regression | 25 | 4.35 | `installed-final-caller-tests.xml` |

The timeout and empty-answer fixtures force the second caller on all three consumers, retain its name and timing, and preserve the first cause if it also fails. They also verify the unchanged prompt, exact image attachment, retained failures, caching, source/copy refusal and deterministic image refusal. Earlier second-stream build checks and actual measurements remain in their original artifacts; their forced-primary-failure measurements are not called production runs.

CC-512 removes the resolved AGY timeout causes from CC-465 and CC-466. Their independent requirements remain: source-complete template acceptance and a twenty-image published week; explicit public signed R, week-long plan-page coverage and the X first-reply/reach observations. CC-512 does not claim those items are complete. The eight unrelated tracked WIP files retain their original hashes, with the two exec-worktree ledger changes still uncommitted. No chat, Claude session, desktop control, application restart or schedule change was used.

The Ops launch and its resume explicitly passed gpt-6.1-sol/max; runtime model/effort remains CONFIGURED_NOT_OBSERVED. Every model attempt records configured caller/model/effort, elapsed seconds and any observed session/usage separately. The native CLI arguments were checked against the installed executable help and the retained [official CLI reference](https://developers.openai.com/codex/cli/reference/) and [configuration reference](https://developers.openai.com/codex/config-reference/); this task uses ChatGPT login, not an API model.

The table below lists all saved reply-ranking attempts dated 12 November UTC, plus this integration's installed image and variants attempts, through 12 November 20:54 GMT+7. It is a partial-day snapshot: 78 attempts (75 antigravity, 3 codex), not a completed 24-hour census of every ContentOps role. Forced-primary-failure measurements and unfinished calls are excluded. An attempt marked RETURNED can still fail its consumer's independent checks. Exact clocks, causes and artifact paths are in `installed-calls-20261112.json`.

| Started, 12 Nov GMT+7 | Role | Caller | Seconds | Attempt / consumer |
|---|---|---|---:|---|
| 07:14:40 | ranking | antigravity | 53.89 | RETURNED |
| 07:17:36 | ranking | antigravity | 53.74 | RETURNED |
| 08:06:22 | ranking | antigravity | 68.24 | RETURNED |
| 08:10:35 | ranking | antigravity | 90.51 | TIMEOUT |
| 08:17:32 | ranking | antigravity | 90.35 | TIMEOUT |
| 08:21:32 | ranking | antigravity | 90.44 | TIMEOUT |
| 08:36:36 | ranking | antigravity | 90.32 | TIMEOUT |
| 08:40:47 | ranking | antigravity | 90.87 | TIMEOUT |
| 08:45:37 | ranking | antigravity | 90.47 | TIMEOUT |
| 08:53:34 | ranking | antigravity | 72.35 | RETURNED |
| 09:05:32 | ranking | antigravity | 45.52 | RETURNED |
| 09:14:38 | ranking | antigravity | 90.49 | TIMEOUT |
| 09:30:32 | ranking | antigravity | 90.59 | TIMEOUT |
| 09:34:31 | ranking | antigravity | 60.79 | RETURNED |
| 10:02:37 | ranking | antigravity | 41.62 | RETURNED |
| 10:14:31 | ranking | antigravity | 46.21 | RETURNED |
| 10:31:30 | ranking | antigravity | 40.22 | RETURNED |
| 10:39:31 | ranking | antigravity | 29.52 | RETURNED |
| 11:03:33 | ranking | antigravity | 32.52 | RETURNED |
| 11:06:35 | ranking | antigravity | 22.54 | RETURNED |
| 11:11:32 | ranking | antigravity | 57.59 | RETURNED |
| 11:59:39 | ranking | antigravity | 27.49 | RETURNED |
| 12:04:31 | ranking | antigravity | 32.75 | RETURNED |
| 12:36:34 | ranking | antigravity | 30.15 | RETURNED |
| 12:46:33 | ranking | antigravity | 64.57 | RETURNED |
| 12:48:32 | ranking | antigravity | 53.14 | RETURNED |
| 12:53:32 | ranking | antigravity | 35.41 | RETURNED |
| 12:58:32 | ranking | antigravity | 84.48 | RETURNED |
| 13:01:32 | ranking | antigravity | 49.40 | RETURNED |
| 13:03:32 | ranking | antigravity | 32.33 | RETURNED |
| 13:04:32 | ranking | antigravity | 31.13 | RETURNED |
| 13:08:33 | ranking | antigravity | 44.91 | RETURNED |
| 13:09:33 | ranking | antigravity | 31.96 | RETURNED |
| 13:10:33 | ranking | antigravity | 32.13 | RETURNED |
| 13:11:33 | ranking | antigravity | 26.18 | RETURNED |
| 13:12:33 | ranking | antigravity | 19.36 | RETURNED |
| 14:33:29 | ranking | antigravity | 17.97 | RETURNED |
| 16:43:29 | ranking | antigravity | 41.22 | RETURNED |
| 18:17:33 | ranking | antigravity | 90.29 | TIMEOUT |
| 18:51:37 | ranking | antigravity | 100.16 | TIMEOUT |
| 18:56:40 | ranking | antigravity | 32.04 | RETURNED |
| 19:01:38 | ranking | antigravity | 54.53 | RETURNED |
| 19:06:43 | ranking | antigravity | 134.05 | TIMEOUT |
| 19:11:48 | ranking | antigravity | 97.48 | TIMEOUT |
| 19:28:30 | ranking | antigravity | 20.48 | RETURNED |
| 19:30:30 | ranking | antigravity | 45.90 | RETURNED |
| 19:33:33 | ranking | antigravity | 17.73 | RETURNED |
| 19:35:31 | ranking | antigravity | 20.44 | RETURNED |
| 19:37:30 | ranking | antigravity | 25.13 | RETURNED |
| 19:39:31 | ranking | antigravity | 25.47 | RETURNED |
| 19:41:31 | ranking | antigravity | 49.29 | RETURNED |
| 19:46:33 | ranking | antigravity | 42.63 | RETURNED |
| 19:50:33 | ranking | antigravity | 33.69 | RETURNED |
| 19:54:31 | ranking | antigravity | 29.62 | RETURNED |
| 19:56:31 | ranking | antigravity | 33.77 | RETURNED |
| 19:58:31 | ranking | antigravity | 28.44 | RETURNED |
| 20:01:31 | ranking | antigravity | 35.01 | RETURNED |
| 20:03:31 | ranking | antigravity | 29.03 | RETURNED |
| 20:08:31 | ranking | antigravity | 33.54 | RETURNED |
| 20:10:31 | ranking | antigravity | 27.68 | RETURNED |
| 20:12:31 | ranking | antigravity | 31.48 | RETURNED |
| 20:14:31 | ranking | antigravity | 55.76 | RETURNED |
| 20:17:30 | ranking | antigravity | 55.98 | RETURNED |
| 20:19:36 | ranking | antigravity | 37.01 | RETURNED |
| 20:22:34 | ranking | antigravity | 90.31 | TIMEOUT |
| 20:25:36 | ranking | antigravity | 55.77 | RETURNED |
| 20:29:38 | ranking | antigravity | 57.30 | RETURNED |
| 20:34:34 | ranking | antigravity | 42.27 | RETURNED |
| 20:37:35 | ranking | antigravity | 42.77 | RETURNED |
| 20:41:34 | ranking | antigravity | 37.19 | RETURNED |
| 20:44:32 | image | antigravity | 65.33 | TIMEOUT / REVIEWED |
| 20:45:15 | variants | antigravity | 65.35 | TIMEOUT / PREPARED |
| 20:45:37 | image | codex | 11.86 | RETURNED / REVIEWED |
| 20:45:42 | ranking | antigravity | 44.50 | RETURNED / FAILED |
| 20:46:20 | variants | codex | 17.57 | RETURNED / PREPARED |
| 20:48:44 | ranking | antigravity | 52.34 | RETURNED |
| 20:51:39 | ranking | antigravity | 65.32 | TIMEOUT / RETURNED |
| 20:52:44 | ranking | codex | 26.25 | RETURNED |
