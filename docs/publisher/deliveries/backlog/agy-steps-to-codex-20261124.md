# Antigravity steps to Codex (24 Nov 2026)

Branch `backlog/agy-steps-to-codex-20261124`, Builder P for Ops Product. Built on `ops/agy-tos-block-20261124` (a43b5c33).

**Why.** Google disabled the Antigravity (agy) account on 24 Nov 2026 at 04:12Z for a Terms of Service violation. Jim's order (24 Nov, before 05:21:31Z): pause Antigravity and use Codex, gpt-6.2-sol, with the reasoning effort chosen per task.

**Outcome.** No ContentOps light step names Antigravity as its caller any more. Every step that used agy now makes one Codex call (`gpt-6.2-sol`) through `light_model_caller_v1`, with the effort set in code and the reason written beside it. Each module keeps its own checks on the answer and its fixed fallback. Records name `caller: codex`, `model: gpt-6.2-sol`, the effort, and `CONFIGURED_NOT_OBSERVED`.

## Correction to the brief

The brief said the steps routed through `light_model_caller_v1` "fall back to Codex when agy is refused". That was true only for callers using the default. Four steps passed `callers=("antigravity",)` explicitly, and the caller stopped on a refused agy attempt without trying Codex. Under the terms block those steps were getting the fixed fallback every time, with no model call:

- the claim check (`public_draft_claims_v1`);
- the plan layer lines and the first two plan-page attempts (`plan_reader_editorial_v1`);
- the wrap's "what changed" stage and its desk fallback (`market_wrap_editorial_v1`).

All of them are on Codex now. As a safety net, the caller also treats a refused agy attempt as eligible for the next caller, so any remaining `("antigravity", "codex")` caller reaches Codex.

## Steps, effort and reason

| Step | Module | Effort | Reason |
|---|---|---|---|
| Light caller default | `light_model_caller_v1.call_light` | low (`CODEX_EFFORT`) | Callers default to `("codex",)`, so no refused agy attempt is recorded. |
| X reply drafts | `x_reply_tabs_v1.draft_with_agy` / `_draft_post_with_agy` | low | One reply of at most 280 characters per target from a few source lines. It is checked by exact substrings, the public-number validator and the claim review, and Jim sends it himself. |
| Daily Note first draft | `daily_note_first_draft_v1.prepare_first_draft` | medium | A whole reader article with facts. `_validate_worker_text` and `check_article` check it before the editor's one pass. |
| Editorial light text (CC-378) | `agy_editorial_assist_v1.prepare_assist` | medium | Lists every claim with its source line and writes public alt text and variants. The checks only flag what the model listed, so low effort would be too loose. |
| Claim check | `public_draft_claims_v1.check_draft` | low | Lists claims only. The code checks every number, date and id itself. |
| Plan layer lines | `plan_reader_editorial_v1.prepare_plan_layers` | low | Picks one of up to three supplied lines per layer. Each pick is validated, with the frozen quote as fallback. |
| Plan page selection | `plan_reader_editorial_v1.draft_plan_page` | medium, then one high retry | Returns excerpt indexes only, checked by `validate_manuscript`. The fallback is the analyst's own order. This replaces agy, agy, then Codex high. |
| Plan variants / X ranking / image check | `text_call`, `x_reply_bot_v1._text_call`, `image_quality_v1.review_vision` | low (default) | Unchanged effort. These now pass `callers=("codex",)` explicitly, and the initial record labels are Codex, not gemini. |
| Wrap "what changed" | `market_wrap_editorial_v1.draft` | medium | Orders supplied lines. `check_lines` verifies ids and exact text. |
| Wrap desk | same | max (unchanged) | The second agy call after a failed desk call is removed. The code fallback answers at once. |

## Provenance and statuses

- Codex records name `caller: codex`, `model: gpt-6.2-sol`, the effort and `CONFIGURED_NOT_OBSERVED`. The Codex CLI reports no runtime model or effort.
- The old `agy` and `agy_version` fields are gone. No agy `--version` probe runs.
- The status codes stay unchanged because their consumers key on them: `AGY_AVAILABLE`, `AGY_UNAVAILABLE`, `DRAFT_CHECKS_PASS`. The same goes for the module and function names and the `agy` output folder of the reply tabs.
- `agy_decision_metrics_v1._legacy_record` now reads the record's `caller`. Codex output is therefore no longer counted as Antigravity in CC-690.
- The X reply-tab stage label is now `CODEX_DRAFT`.
- Reply-tab drafts reach the claim review with origin `codex_light`. As before with `antigravity`, an unsupported sentence is dropped (`DROPPED_ORIGINS`). The writer's `codex` origin is unchanged.

## Other paths checked

- `v1_simple_gemini_newsroom_v1` and `_eight_platform_substack_first_pipeline_impl_v1` only consume or apply suggestions and make no model call. The "gemini" newsroom goes through 9router, not agy.
- `scripts/run_native_desktop_editorial.py` calls `prepare_assist`, which is now Codex.
- `x_reply_bot_v1` ranking goes to Codex, and its writer was already Codex.
- The posting answerer (`agy_neo_answerer_v1`, route `AGY`) stays refused by Ops' block. Posting is paused.

## Tests

New file: `tests/test_agy_steps_to_codex_20261124.py` (21 tests, fake runners only).

- An autouse fixture makes `subprocess.Popen` fail on any start and name agy if it appears.
- The light caller defaults to `("codex",)`. An explicit `("antigravity", "codex")` reaches Codex, and its agy attempt is `NOT_STARTED`.
- Each of the three modules:
  - calls Codex with `gpt-6.2-sol` and its effort;
  - a good answer passes the module's checks (pack build, `check_article`, the compiler consuming alt text and variants);
  - a bad answer (empty, exit, schema, unsupported number) falls back to the fixed text or the editor's pass;
  - with no runner, only `codex.exe` is ever started.
- The claim check uses Codex low and drops a light-draft sentence it cannot source.
- A static check confirms that no light step names `"antigravity",` as a caller or builds an `[AGY, …]` command.

Existing tests changed to the Codex route, with their intent kept:

- `test_agy_editorial_assist_cc378`: Codex fake. The version-probe tests are replaced by "one call, resume does not repeat" and a Codex-timeout test.
- `test_daily_note_first_draft_cc403`.
- `test_image_templates_cc465`: Codex image fake with `--image` attached.
- `test_light_model_caller_cc512`: one Codex answer per consumer. The two-caller mechanics are still tested with a fake agy and the terms block lifted inside the test.
- `test_market_wrap_cc689`: desk failure goes to the code fallback, so calls are codex then codex, with efforts medium and max.
- `test_plan_analysis_copy_cc688`: page attempts are medium then high.
- `test_plan_analysis_layers_cc730`.
- `test_plan_reader_editorial_cc466`.
- `test_x_reply_bot_cc464`.
- `test_x_reply_fact_cc495`: the ranker differs from the writer by effort, low against max.
- `test_x_reply_tabs_cc458`.

Covering run: every test file that names a changed module (46 files, the new one included), with `python -B -m pytest -q -p no:cacheprovider`.

1. First full run on the finished code: 1123 passed and 85 failed, plus 1 error. All the failures were in the 11 test files above, and all came from asserting the old agy route.
2. The code did not change after that run; only those 11 test files were edited. Each edited file was then rerun on its own, and all passed:
   - cc378 with cc403: 43 passed;
   - cc465: 106 passed;
   - cc512: 21 passed;
   - cc689: 23 passed;
   - cc466, cc688 and cc458: 60 passed;
   - cc730, cc464 and cc495: 95 passed (rerun on the merged head).
3. After merging the live head e0032b0a (agy block integrated), the new file and `test_agy_terms_block_20261124` ran again: 24 passed.

No second full 46-file run was made. Free memory stayed at 0.4-0.7 GB, held by Jim's own backtests, and the coordinator said to deliver with the smaller runs. The merge brought no file change into this branch (`git diff --stat` was empty).

## Codex calls per day expected after the relaunch (estimates from code bounds)

| Step | Calls |
|---|---|
| X reply drafts | ≤ 5 per two-hour refresh, so ≤ 60 a day at full cadence; fewer when fewer distinct authors are eligible |
| Daily Note first draft | 1 a day (cached per exact prompt) |
| Editorial light text | 1 per canonical article package (about 1 to 3 a day) |
| Claim check | 1 per public draft (plan posts, plan pages, X replies), cached per exact draft; roughly 10 to 30 a day |
| Plan layer lines | 1 per plan post set (a few a day) |
| Plan page selection | 1 per new plan, 2 when the first answer fails its check |
| Plan variants, X ranking, image check | unchanged: 1 each per request; these already fell back to Codex before |
| Market wrap | 2 per wrap (1 a day): changes medium plus desk max. This was one agy call plus one Codex call. |

Net new Codex load against the agy days is roughly the agy volume moved over. Timeouts were raised to 180 s on the three long steps, so a slow answer is not paid for twice.

## What is left

- `agy_decision_metrics_v1` (CC-690 daily checks) still counts only `antigravity` attempts for its pass rates. With every step on Codex, those job rows show no Antigravity calls; plan pages show as Codex takeovers. Making the daily checks count the Codex light calls is a reporting change for Ops Product.
- Status codes and field names that still say AGY (`AGY_AVAILABLE`, `AGY_UNAVAILABLE`, `agy_light_assist`, the `agy` output folder) are kept for their consumers. Renaming them is optional and touches the readback, the native editor prompt and stored records.
- After `ops/agy-tos-block-20261124` is integrated into the live root, merge the live HEAD into this branch again before integrating.
