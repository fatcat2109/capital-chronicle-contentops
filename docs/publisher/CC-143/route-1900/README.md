# CC-143: the 19:00 GMT+7 digest route without Codex

## The old route, and why it stopped

- The 19:00 executor was never a Windows task. It was the Codex Desktop automation `v1-newsroom-brief-us-1900` (weekdays 19:00 GMT+7, ACTIVE). Its `scheduled` startup calls `with_due_digest` (`scripts/run_native_desktop_editorial.py`), which freezes the digest (`production_digest_housekeeping`) and hands the same Codex conversation a `digest-resume` continuation for the Neo loop.
- The three Windows tasks are not that route. `CapitalChronicle_ContentOps_V1_Daily_App_Runtime` (the resident host tick, which also prepares the digest packet) was disabled by the ContentOps L2 chat on 30 Oct 05:52 GMT+7 under Jim's temporary Codex pause (`orchestrators/contentops/HANDOFF.md` in the Tower), and was kept off afterwards. `Simple_Scheduler` (legacy Gemini scheduler, "do not revive") and `Hourly_Audit` were already disabled. None needs to come back for the digest.
- What failed in practice: on 4 Nov the Codex window entered at 18:59:59.78 GMT+7 (11:59:59.78Z), before the cutoff, so the owner returned the 3 Nov digest rather than freezing the 4 Nov one; the 4 Nov digest went out only on 5 Nov 10:32 GMT+7 through a manual Codex exec. With Codex over its weekly quota, the window cannot be relied on for the Neo steps.

## The route

One Claude Desktop scheduled task, daily at 19:05 GMT+7 (plus its fixed dispatch delay), running `SCHEDULED_TASK_PROMPT.md` in `A:\Capital Chronicle\ContentOps`:

1. `scripts/run_daily_digest_1900.py preflight` (reads only): due time passed, no LLM operator pause, AUTONOMOUS_DEFAULT, live rollout, feed present.
2. `scripts/run_daily_digest_1900.py resume`: the same owners as the CLI's `digest-resume` (`prepare_daily_digest`, `continue_daily_digest`), refusing before 19:00 GMT+7, returning one flat `next_request`.
3. The agent claims each request with the existing `digest-tool-begin`, acts once in BrowserOS Neo, and returns it with `digest-tool-submit` under the `CLAUDE_CODE_SESSION` surface (CC-283).

The agent is needed only for step 3: Substack has no publish API here, so the identity check, the publish click with email ON and the readback are BrowserOS Neo actions. Jim enters Substack's code only if Substack asks; the run leaves that tab untouched and records PENDING_JIM_EMAIL_CODE (decision 52; CC-242). Exactly-once stays with the coordinator: a claimed publish is never reclaimed, and an existing public page only gets a readback.

## Dry run (no shared write, nothing published)

`scripts/run_daily_digest_1900.py dry-run --scratch <new C: folder> [--now <UTC>] [--simulate-identity]` backs up the production store into the scratch folder, freezes the digest on the copy, and drives the coordinator to its first native request. Writes outside the scratch folder and network connections are refused and counted; the production store's size, mtime and row counts are compared before and after. `--simulate-identity` answers the read-only identity request on the copy with a return labelled DRY_RUN_SIMULATED_NOT_BROWSER, to prove the Claude surface passes `submit`, and stops at the PUBLISH request without beginning it. Evidence: `dry-run-sim1905.json` here.

## Install (Ops Product, under C11)

- Old owner off first: the Codex automation `v1-newsroom-brief-us-1900` still exposes the digest continuation. Codex Publisher keeps writing, so do not pause it; this task is the digest's one owner from its first real run. The coordinator's claims make a second actor harmless (it gets NATIVE_NEO_ACTION_ALREADY_CLAIMED_READBACK_ONLY), but record the ownership in the BACKLOG.
- Create the task from a session whose permission mode is Bypass, or reuse a disabled `-bp` slot, so a run never stalls on an approval (the 2 Nov `cc-l1-resume-main-0345-bp` stall). It needs the BrowserOS Neo MCP tools.
- `create_scheduled_task`: taskId `cc-contentops-digest-1900-bp`, title `CC Product · 19:05 GMT+7 daily digest (CC-143)`, cronExpression `5 19 * * *`, prompt = the text of `SCHEDULED_TASK_PROMPT.md`, notifyOnCompletion true.
- Test run (no shared write): `PY -B scripts/run_daily_digest_1900.py dry-run --scratch C:\CapitalChronicleScratch\cc143-route\install-test-<stamp> --now <today 12:05Z> --simulate-identity`; expect `production_unchanged: true`, no refused writes or connections, and a PUBLISH next request with `substack_delivery_policy.mode = DAILY_EMAIL_DIGEST`.
- One real run through its consumer: after 19:00 GMT+7, `run_scheduled_task` once; check `<run>\result.json`, then `PY -B scripts/run_daily_digest_1900.py preflight` shows the day's digest WEB_CONFIRMED or CONFIRMED with its public URL.
- Then leave the cadence on.

## Rollback

- Schedule: disable `cc-contentops-digest-1900-bp` (`update_scheduled_task` enabled false). The digest then waits for the Codex window's continuation as before; no state needs undoing (packets and dispatches stay exactly once).
- Code: the route only adds files (this folder, `scripts/run_daily_digest_1900.py`, `tests/test_daily_digest_1900_route_v1.py`); nothing else imports them, so they are inert once the task is off. The previous live head is tagged `contentops-rollback-20261105-cc143-1900-route`.
