CC-512 is built for the first Publisher stream to integrate. The branch is `backlog/cc-512-light-caller-fallback`, cut from operating HEAD `05586a4aeac7d3dad1cb992607e22fb1ae01b9ea`. This stream has made no live-root, runtime-store, schedule, publication or desktop-control change. CC-465 and CC-466 retain their current statuses until their integrating stream observes the next real calls.

The image review, plan-post variants and reply ranking now share `live_contentops/light_model_caller_v1.py`: Antigravity first, then the same guarded prompt once to Codex on a timeout or an empty answer. Codex is explicitly `gpt-6.1-sol/low`, using ChatGPT login, a read-only sandbox, no project/user configuration, no model tools and a finite stdin request followed by EOF. Images are attached with `--image`; binary PNGs never enter logs or this delivery as base64. The existing source/copy checks and deterministic image gate still decide whether the output can be used. A second failure preserves the first named AGY cause and separately records the fallback cause. Caller, seconds, configured model/effort, observed session/usage, prompt and image hashes remain with each role's existing artifacts.

The installed AGY 1.5.5 protocol does not accept image content blocks. Its already-supported local-PNG read remains the sole AGY image tool exception; the prompt begins `Do not call any tool` and explicitly limits that exception. Codex sees the identical prompt plus the attached PNG and uses no tool. A claimed image observation without either AGY's observed local read or Codex's attachment cannot score. Model labels remain CONFIGURED_NOT_OBSERVED; session IDs and token usage are observed separately.

The diagnosis found 65 retained ranking calls: 48 returned and 17 timed out, every timeout with zero stdout. None of their prompts began with the required no-tool guard. The completed-call 90th percentile is 64.57 seconds; 45/48 answered calls fit 65 seconds. This does not establish a 90% success rate across all 65 calls: the 17 censored failures remain failures. The shared primary bound is therefore 65 seconds, using the measured answered-call percentile and a second caller instead of another long blind wait. Reply fallback stays 65 seconds so ranking plus fallback plus the unchanged 90-second writer stays within the existing 270-second lease. Images have a 120-second fallback after a measured 65-second failure. Existing AGY timeout cause names are retained for compatibility; each attempt records its actual configured limit and observed seconds separately.

The failed retained event-table review used an 87,847-byte PNG and a 2,886-byte prompt; its separate event-chart prompt is 3,834 bytes. These are not large payloads. Saved image returns include empty/invalid final JSON at roughly 123 seconds despite provider-reported model durations near seven seconds. Earlier image-block requests were explicitly unsupported. The saved CC-466 record reports stream limits of 60/120 seconds and a direct limit of 120 seconds, all without text; it does not retain the exact failed prompt bytes here. This run does not infer one universal provider cause from those observations. The CLI version command itself timed out at ten seconds; the exact executable hash and saved 1.5.5 evidence are in `cli-versions.json`. The measured Codex CLI is 0.167.0-alpha.3.2.

A separate native diagnostic exposed a caller defect: Codex emitted `turn.completed`, but generic `communicate()` still waited until its deadline. The Codex adapter now consumes that supported completion event, closes stdin explicitly, and ends only its own child if CLI teardown stalls. A real child-process test reproduces completion followed by a hanging exit. No existing user application is closed or restarted.

Successful cached results are reused. The next preparation of an old failed image review or variants call may continue once through CC-512. The original variants artifact stays byte-for-byte intact; the original image metadata is retained under its content hash. A CC-512 failure stays cached instead of silently creating a retry loop. Issued publication requests and public objects are untouched.

Validation is targeted, one pytest process at a time, with no workers or shards:

- `consumer-tests.xml`: 91 checks passed across the three existing consumer files; 484.63 seconds. This was before the final cache/teardown amendments.
- `final-caller-tests.xml`: 21 checks passed in 4.50 seconds, including timeout/empty recovery on every role, unchanged prompt and image attachment, cache continuation, retained first failures, source/copy checks and deterministic image refusal.
- `final-consumer-tests.xml`: seven selected existing vision/cache/timeout checks passed in 3.42 seconds after those amendments.

Actual native measurements are separate from forced-failure fixtures. The primary failure was simulated in the three Codex measurements; the Codex calls and timings were real. The ranking prompt was retained exactly; the variants task used the retained confirmed CC-466 article because its failed original prompt was unavailable in these artifacts. These were local adapter measurements, not production runs or published copy.

| Measurement | Actual caller | Seconds including caller overhead | Observed result |
|---|---|---:|---|
| Retained ranking prompt, normal first caller | Antigravity / configured Flash High | 34.87 | Valid ranking; no fallback |
| Same ranking prompt, forced primary timeout | Codex / configured Sol low | 53.22 | Valid ranking |
| Retained event-table PNG, forced primary timeout | Codex / configured Sol low | 12.18 | Ten answers returned; one passes, nine fail |
| Retained article variants, forced primary empty | Codex / configured Sol low | 34.27 | Schema and length checks pass |

The image review's low score is preserved. It does not approve the template: the event table has no TradingView chart and several required visual checks fail or remain uncertain. It also questions partial probability coverage; no complement is invented. The 65-second image failure, the initial ranking failure and the completion/teardown diagnostic remain in the measurement files, not counted as successful calls. Low is the lowest supported Sol effort and now has actual returns for all three tasks; no higher-effort or API substitution was used.

The following table lists every retained reply-ranking call for 12 November UTC at the diagnosis snapshot, in GMT+7 for Jim. It covers 41 saved calls through 18:56 GMT+7, not a census of every ContentOps role or a completed 24-hour day. Exact UTC clocks, artifact paths, prompt sizes and response sizes are in `calls-20261112.json`; native measurements above have their own records.

| Started, 12 Nov GMT+7 | Caller | Seconds | Result |
|---|---|---:|---|
| 07:14:40 | Antigravity | 53.89 | RETURNED |
| 07:17:36 | Antigravity | 53.74 | RETURNED |
| 08:06:22 | Antigravity | 68.24 | RETURNED |
| 08:10:35 | Antigravity | 90.51 | TIMEOUT |
| 08:17:32 | Antigravity | 90.35 | TIMEOUT |
| 08:21:32 | Antigravity | 90.44 | TIMEOUT |
| 08:36:36 | Antigravity | 90.32 | TIMEOUT |
| 08:40:47 | Antigravity | 90.87 | TIMEOUT |
| 08:45:37 | Antigravity | 90.47 | TIMEOUT |
| 08:53:34 | Antigravity | 72.35 | RETURNED |
| 09:05:32 | Antigravity | 45.52 | RETURNED |
| 09:14:38 | Antigravity | 90.49 | TIMEOUT |
| 09:30:32 | Antigravity | 90.59 | TIMEOUT |
| 09:34:31 | Antigravity | 60.79 | RETURNED |
| 10:02:37 | Antigravity | 41.62 | RETURNED |
| 10:14:31 | Antigravity | 46.21 | RETURNED |
| 10:31:30 | Antigravity | 40.22 | RETURNED |
| 10:39:31 | Antigravity | 29.52 | RETURNED |
| 11:03:33 | Antigravity | 32.52 | RETURNED |
| 11:06:35 | Antigravity | 22.54 | RETURNED |
| 11:11:32 | Antigravity | 57.59 | RETURNED |
| 11:59:39 | Antigravity | 27.49 | RETURNED |
| 12:04:31 | Antigravity | 32.75 | RETURNED |
| 12:36:34 | Antigravity | 30.15 | RETURNED |
| 12:46:33 | Antigravity | 64.57 | RETURNED |
| 12:48:32 | Antigravity | 53.14 | RETURNED |
| 12:53:32 | Antigravity | 35.41 | RETURNED |
| 12:58:32 | Antigravity | 84.48 | RETURNED |
| 13:01:32 | Antigravity | 49.40 | RETURNED |
| 13:03:32 | Antigravity | 32.33 | RETURNED |
| 13:04:32 | Antigravity | 31.13 | RETURNED |
| 13:08:33 | Antigravity | 44.91 | RETURNED |
| 13:09:33 | Antigravity | 31.96 | RETURNED |
| 13:10:33 | Antigravity | 32.13 | RETURNED |
| 13:11:33 | Antigravity | 26.18 | RETURNED |
| 13:12:33 | Antigravity | 19.36 | RETURNED |
| 14:33:29 | Antigravity | 17.97 | RETURNED |
| 16:43:29 | Antigravity | 41.22 | RETURNED |
| 18:17:33 | Antigravity | 90.29 | TIMEOUT |
| 18:51:37 | Antigravity | 100.16 | TIMEOUT |
| 18:56:40 | Antigravity | 32.04 | RETURNED |

The first Publisher stream owns the next action: integrate this branch onto its current operating HEAD, run the targeted checks, tag and read back the installed consumer. Then observe the next image and variants calls, update only the AGY timeout parts of CC-465/CC-466 when their actual returns justify it, and retain their independent Main-export and template/week requirements. This stream changes neither those items nor the live root.

The Ops launch was observed with explicit gpt-6.1-sol/max; actual runtime model/effort is CONFIGURED_NOT_OBSERVED (`run-context.json`). No chat was messaged and no Claude session was launched.

CLI configuration follows the [official Codex CLI reference](https://developers.openai.com/codex/cli/reference/) and [configuration reference](https://developers.openai.com/codex/config-reference/), checked with the installed executable help. The user requested this native CLI route; no API model or new provider is introduced.
