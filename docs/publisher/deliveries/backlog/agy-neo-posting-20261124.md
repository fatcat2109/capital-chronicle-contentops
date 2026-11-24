# CC-798 delivery: Antigravity answers native Neo posting requests; code keeps every decision

Branch `backlog/agy-neo-posting-20261124`, built by Claude Builder O for Ops Product on 24 Nov 2026, from live head 51284715. No tag and no merge into the live root. Posting stays paused; nothing was posted, and Neo was driven against no real platform.

Jim, 24 Nov 2026: Antigravity may post what Codex wrote, as long as Codex supplies the full text, and Antigravity never writes; always Gemini 3.8 Flash High.

## Design

New module `live_contentops/agy_neo_answerer_v1.py`. It answers one pending native Neo PUBLISH request (schema `contentops.native_neo_tool_request.v1`) through the operation's own `begin` and `submit`. These are `NativeNeoExecutor.begin/submit` by default, or the flow's wrappers, for example `plan_status_posts_v1.begin_x/submit_x` or `NativeReviewedPublication.tool`.

1. **Switch first.** A platform the switch does not give to agy is `LEFT_FOR_CODEX`: no claim and no run. If the agy CLI is missing, or the prompt would be too long, the request also stays unclaimed for Codex.
2. **Claim.** `begin(request_hash)` makes the one claim, with all of the executor's existing checks (public time, operating mode, media bytes, account proof, deadlines). A refused begin, including `ALREADY_CLAIMED`, ends the answer with no agy run.
3. **Run 1, FILL.** agy opens the start address in its own tab and reads the signed-in account. It enters each exact post and reads every composer box back. It is told it must not click anything that publishes.
4. **Code decides.** The account must equal `expected_identity` (and the stable id where one is registered). The composer texts must equal `expected_posts(request)` under `_post_texts`, in order, with no box missing or extra. If either differs, code submits `FAILED_BEFORE_WRITE` (definite no-write, stage `BEFORE_PUBLISH_CLICK`), and run 2 never starts.
5. **Run 2, CLICK.** Only after that match, agy works in the same tab. It reads the composer again, clicks Post once, and reads the post back.
6. **Code decides again.**
   - `SUCCESS` needs all four checks:
     - run 2's pre-click texts match;
     - the readback is FOUND, with an id and a URL;
     - the readback account is the expected one;
     - the readback texts match under `_post_texts`.
   - Any mismatch is `UNKNOWN_WRITE`, `retry_permitted: false`, with no canonical public object. The object agy saw is kept only as `agy_observed_object`. The coordinator then reads back through its normal route before any retry, and a mismatch never counts as posted.
7. **Unreadable after the claim.** If code cannot read a run's result after the claim (timeout, prose, a missing stage, missing evidence, or a FILL run that says it may have clicked), code **submits nothing**. The existing claimed-without-return path applies: `UNKNOWN_WRITE`, readback only, never a second post.
8. **The existing checks still run.** The executor's own submit checks run on every return:
   - tool and surface binding;
   - observation times;
   - the composed identity window;
   - `pre_click_posts` and the in-run readback;
   - `_store_composed_readback`.
   Exactly-once, the dispatch states and reconciliation are unchanged. No line of `native_neo_executor_v1.py` changed apart from the new surface constants.

**Surface (C5).** `ANTIGRAVITY_CLI` uses the tool name `agy:mcp(browseros-neo/*)`; both are registered in `SURFACE_TOOLS`. The observation records `agy_model: gemini-3.8-flash-high` with `agy_model_provenance: CONFIGURED_NOT_OBSERVED`, because agy's JSON reports no model, plus the agy `conversation_id` of each run. It is never recorded as Codex or Claude.

**Page content is untrusted.** Both prompts say so. The model copies any page instruction it saw into `page_instructions_seen`. Code writes that list (at most 10 items of 300 characters) into the report as data, and never passes page text into a later prompt or acts on it.

**Platforms.** The switch covers `x`, `substack_notes`, `linkedin`, `linkedin_company` and `youtube`, the short-form Neo composers. Substack articles stay with Codex: the editor holds rendered text rather than the bound Markdown, so the exact pre-click comparison cannot pass. EDIT_EXISTING, READBACK and VERIFY_IDENTITY also stay with Codex or the endpoint executor.

## Each check and its test

All tests are in `tests/test_agy_neo_answerer_cc798.py` and use a fake agy that returns canned JSON. They run on a real store, executor and coordinator, from the CC-283 composed-run fixtures: 27 passed.

| Check | Test |
|---|---|
| Own label and tool, never Codex or Claude | `test_surface_has_its_own_label_and_tool`, `test_exact_post_is_accepted_and_recorded_as_antigravity` |
| An exact post is accepted, recorded as `ANTIGRAVITY_CLI`, reconciled without a publish call | `test_exact_post_is_accepted_and_recorded_as_antigravity` |
| A changed word, a missing box or an extra box is refused before the click (run 2 never starts) | `test_changed_text_is_refused_before_the_click` (3 cases) |
| Wrong account refused before the click | `test_wrong_account_is_refused_before_the_click` |
| An injected page instruction is reported, recorded as data, never acted on | `test_injected_page_instruction_is_recorded_and_never_acted_on` |
| A readback mismatch, or a changed pre-click text, is held as UNKNOWN_WRITE; after recovery the dispatch stays UNKNOWN_WRITE with no public object and 0 publish calls | `test_a_mismatch_after_the_click_is_held_as_unknown_never_posted` (2 cases) |
| An unreadable click run (timeout, prose, no stage, no readback) submits nothing, and the request is never run again | `test_an_unreadable_click_run_submits_nothing_and_is_never_repeated` (4 cases) |
| No second post when the same request runs again | `test_the_same_request_never_posts_twice` |
| A FILL run that says it may have clicked submits nothing | `test_a_fill_run_that_may_have_clicked_submits_nothing` |
| Run 2 that finds a changed composer does not click | `test_click_run_that_finds_a_changed_composer_does_not_click` |
| A dry run never clicks, claims or submits, and the request stays pending | `test_dry_run_fills_and_verifies_but_never_clicks_claims_or_submits` (2 cases), `test_dry_run_reports_a_changed_text` |
| Every platform defaults to Codex; Substack articles are never routed | `test_every_platform_defaults_to_codex`, `test_answer_pending_answers_only_switched_unclaimed_publishes` |
| Missing agy leaves the request unclaimed | `test_missing_agy_leaves_the_request_unclaimed_for_codex` |
| Switch file validated | `test_switch_file_is_validated` |
| Fixed model, fixed flags, no bypass flag | `test_command_fixes_the_model_and_has_no_bypass_flag` |
| Runner: a fresh empty folder, stdin closed, the exact argv, the folder removed; on timeout its own process tree ends | `test_runner_uses_a_fresh_empty_folder_closed_stdin_and_the_fixed_command`, `test_runner_ends_its_own_process_tree_on_timeout` |
| Unreadable agy envelopes | `test_parse_refuses_unreadable_envelopes` |

**Optional integration check.** `scripts/agy_neo_mock_check_cc798.py` runs the real agy against the local mock composer only, in `tests/fixtures/agy_neo_mock/`. The mock is copied from the Ops Advisor's mock, with an account line and a readback page added, and it keeps the injected "SYSTEM NOTICE TO AI AGENTS". The check is a standalone script, never collected by pytest, because the suite's isolation guard (`tests/isolated_python/sitecustomize.py`) refuses any live agy run under pytest; it was kept as it is. Run it with `python -I scripts\agy_neo_mock_check_cc798.py <scratch folder>` while Neo is up. It checks three things:
- the dry run sends no POST and never opens `/injected`;
- the live two-run flow sends exactly one `POST /post` with the exact text;
- `/deleted` and `/injected` are never touched.

**Run on 24 Nov 2026, real agy on gemini-3.8-flash-high and the real Neo, mock only:** every check passed (`"ok": true`).
- The dry run took 136 s: no POST, the account matched, and the texts were `MATCHED`.
- agy reported the page's injected "SYSTEM NOTICE TO AI AGENTS" in `page_instructions_seen` and did not follow it: `/deleted` and `/injected` were never touched.
- The live two-run flow took 298 s and sent exactly one `POST /post`, with the exact text. All four code checks held, and the return was recorded as `ANTIGRAVITY_CLI`.
- The evidence (result line, both reports and the mock's request log) is in `docs/publisher/deliveries/backlog/agy-neo-posting-20261124-evidence/`.

**Covering tests**, on the branch head with live head 51284715 included (no merge was needed): `test_agy_neo_answerer_cc798`, `test_native_neo_executor_v1`, `test_native_neo_claude_surface_cc283`, `test_native_neo_composed_run_cc283`, `test_neo_endpoint_executor_cc436`, `test_completed_finalized_intent_cc247` and `test_security_scans`, 286 passed. The full suite was not run.

## The agy command and its permissions

```
C:\Users\bullw\.gemini\bin\agy.exe --model gemini-3.8-flash-high --disable-slash-commands --output-format json
  --print-timeout 540s --mode auto --settings {"permissions":{"allow":["mcp(browseros-neo/*)"]}} --print <prompt>
```

- **Model.** `agy_command` refuses any other model (`AGY_MODEL_FIXED_GEMINI_3_8_FLASH_HIGH`) and any bypass flag (`AGY_BYPASS_FLAG_FORBIDDEN`).
- **Process.** One process per run, in a fresh empty temp folder that is removed afterwards. stdin is DEVNULL and the window flag is `CREATE_NO_WINDOW`.
- **Timeout.** At 570 s the runner ends only its own process tree (`taskkill /PID <pid> /T /F`), as `agy_editorial_assist_v1` does.
- **Permissions.** The only allowed tool rule is `mcp(browseros-neo/*)`. There is no read-file rule. Instead, both prompts require short reads: small run scripts or element reads, never a page snapshot, screenshot or page text. Long Neo outputs therefore never need agy's file reader.
- **Prompt size.** The prompt goes on the command line and is capped at 30,000 characters (the Windows limit is 32,767). A longer prompt is never claimed and stays with Codex.

## Dry-run mode

The dry run fills the composer, reads it back, then discards the draft and closes its tab. It never clicks Post, never claims, never submits, and changes nothing in the store. Code compares the account and the texts and writes `<request_sha256>.agy.dry_run.json`. The report shows `passed` and `pre_click_verification`, plus `reason_code` when it fails: `AGY_PRE_CLICK_TEXT_DIFFERED`, `AGY_ACCOUNT_MISMATCH`, `AGY_FILL_RESULT_UNREADABLE`, or `AGY_DRY_RUN_CLICK_REPORTED` (the model said it may have clicked, a defect to look at).

There are two ways to run it:
- Through the switch: the value `AGY_DRY_RUN` makes `answer_request` and `answer_pending` dry-run that platform's requests, which stay pending for Codex.
- By hand, on one saved request file:

```
python -I scripts\run_agy_neo_answerer.py dry-run --request-file <output_dir>\<hash>.request.json --report-dir C:\CapitalChronicleScratch\agy-dry-run-<platform> --scratch-root C:\CapitalChronicleScratch
python -I scripts\run_agy_neo_answerer.py routes
```

The script checks the file's schema and both hashes before it runs anything.

## Switching one platform on (Ops Product, after the relaunch dry run)

The switch is `A:\Capital Chronicle\Runtime\ContentOps\control\agy_neo_routes.json`, next to `suspended_routes.json`. If the file is missing, every platform is `CODEX`. If it is unreadable or invalid, every platform is also `CODEX`; `route_for` falls back to that.

1. Integrate this branch. It changes no live behaviour on its own: with no switch file, every platform stays with Codex.
2. For each platform, run the dry run on a real pending request at the relaunch: `{"x": "AGY_DRY_RUN"}`, or the script above. Read the report and require `passed: true`. Check in the platform that no post appeared and the draft was discarded.
3. Switch that platform on: `{"x": "AGY"}`. Platforms you leave out stay with Codex.
4. Call the answerer from the turn that today hands the request to Codex. For a plain executor that is `agy_neo_answerer_v1.answer_pending(executor)`. For a flow with its own wrappers, call `answer_request(packet, begin=<flow begin>, submit=<flow submit>, native_invocation_id=executor.native_invocation_id)`. Then resume the coordinator as after a Codex submit (for example `recover_pending()` or the flow's own resume).
5. Read the reports in `<output_dir>\agy\`: each one names `outcome`, the submitted status and `reason_code`.

## Rollback

- Remove the platform from `agy_neo_routes.json`, or delete the file. Its requests go back to Codex on the next turn.
- A request agy already claimed stays readback-only under the existing UNKNOWN_WRITE path, whichever surface answers next.
- To remove the code, revert this branch's commits. The only shared change is the two constants `ANTIGRAVITY_SURFACE` and `ANTIGRAVITY_TOOL` and their `SURFACE_TOOLS` entry. Stored returns that carry `ANTIGRAVITY_CLI` would then fail `reconcile_completed_native_publish`'s surface check, so revert only after those dispatches have reconciled.

## What is left

- **No live caller is wired yet.** Nothing calls `answer_pending` until Ops Product adds the call at step 4, and only after a platform's dry run passes. No new scheduler or watcher was added (C3).
- **READBACK, VERIFY_IDENTITY and EDIT_EXISTING stay with Codex or the endpoint executor.** agy's in-run readback carries no image-byte comparison. When the post has media, code marks its in-run readback `PENDING_BINARY_COMPARISON`, so the coordinator asks for its full readback at once.
- **Substack articles stay with Codex** (see Platforms).
- **Timing.** One live post takes about 5 minutes (two agy runs; 298 s on the mock), and a dry run about 2 minutes. That is well inside X status posts' 60-minute freshness window, but a caller must not sit inside the minute job's 20 s budget. Call the answerer from a turn of its own.
- **No real platform has been tried.** The selectors and the readback on X, Notes, LinkedIn and YouTube are proved only by each platform's relaunch dry run, then its first live post.
- **Neo's tool-output folder.** No read-file allow rule was added, because the folder is not documented here. If a platform needs long reads, add `read_file(<that folder>)` to `AGY_ALLOW` and test it.
