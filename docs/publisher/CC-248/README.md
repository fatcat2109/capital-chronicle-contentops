# CC-248: the article-triggered preview hook in the ContentOps root

From the ContentOps V1 lane (Claude, Opus 5.5), 5 Nov 2026. The item was assigned by Ops Product (CC-256 R11).

## What is integrated

- **Commits:** CC-149 b7913310 and c3d5e581, CC-246 1e5e0ff9, and CC-254 d2efd9d8. They are merged onto the live head as one merge commit.
- **The hook:** after `published_content_v1.append_record` confirms an append to the production feed (`Runtime\ContentOps\published_content_v1.jsonl`), `preview_article_hook_v1.launch_preview_mirror` starts the preview worker as one detached child.
  - The worker is `tools.product.republish_preview_articles_v1 --execute --record <feed>`.
  - It runs in the pinned consumer root `Worktrees/codex-web-cc254-clean`.
  - Before launching, the hook checks:
    - the pinned module hash 1193e2a3...;
    - `ui/node_modules` is the consumer root's own folder, not shared;
    - pythonw is present;
    - `jsonschema` imports in the appending interpreter.
  - Any other outcome is a named NOT_STARTED cause. The hook never undoes or blocks the publication itself.
- **The worker:** it waits out its ten-minute interval, rebuilds from the latest feed, and publishes to the existing noindex preview (`fatcat2109/capital-chronicle-preview`). No new host or domain is used.

## Checks, 4 Nov 22:10-22:20Z

| Check | Result |
|---|---|
| Consumer root `codex-web-cc254-clean` | Commit 7f605a4902, clean; module hash matches the binding; its own `ui/node_modules` |
| `jsonschema` with `-E` in the consumer root | System Python 3.13.4 (the `python` the runbook uses): present. ContentOps runtime venv: missing |
| Child launched exactly as the hook does | Outlived the shell command that started it by 46 s and finished |
| `tests/test_preview_article_hook_v1.py` | 11 passed |
| Every test file that touches the publication record | 164 passed (hook, published_content, cc124 resume, finished-piece dispatch, site-first, digest, V1 lane) |
| Read-only `load_publications` on the live feed | 2 public articles; 3 refused pieces named, each `NEWSROOM_MEDIA_TYPE_REFUSED`: substack:223199520, 223246940, 223408612 |

- **The venv case:** an append made from the runtime venv returns `CONSUMER_PYTHON_DEPENDENCY_MISSING:jsonschema` and does not update the preview.
- **The refused pieces:** the build no longer fails as a whole.

## Effect and acceptance

- The last preview build (4 Nov 13:12Z) showed 5 articles. The next hook-triggered build will show the admitted ones (2 today, plus the new piece) and name the 3 refused pieces until CC-253 fixes their media.
- **Acceptance:** the next natural CC-135 append builds the live feed with the refused pieces named, and the guarded output reaches the existing preview. The worker's state is kept in `Runtime\ContentOps\preview_article_republish_v1.json` and its log in `preview_article_worker.log`.

## First natural appends, 5 Nov

Read-only readings at 02:46Z from four sources: the feed, the worker state, the preview repository's commits, and the worker's own reader run on the live feed.

| Time (UTC) | Event |
|---|---|
| 00:34:37 | The PPI piece (substack:223555673) is appended. The hook returns STARTED, pid 52368 (`docs/publisher/CC-124/run-20261105-0610/publication-resume-06-expanded.json`). |
| 00:34:37-02:30:00 | The worker waits in its load window. `build_after` chains T0±2 h around the BoJ minutes (23:50Z) and the S&P Global Japan services PMI (00:30Z). |
| 02:28:37 | The Southwest piece (substack:223564454) is appended. Its worker queues on the mutex. |
| 02:32:12 | One build pushes preview commit e57b0f1c: guard PASS, 2 articles, 5 refused pieces named. The state reads PUBLISHED at 02:32:21. |
| after 02:32:21 | The queued worker finds the feed already published and returns UNCHANGED. |

No hand step was needed. The guarded output reached the existing preview, with the refused pieces named. Neither new article is on it, for these reasons:

- **NEWSROOM_MEDIA_TYPE_REFUSED** (PPI, and the SEC, FOMC and CPI pieces). The reader admits article media only by `modality`, either `source_backed_chart` or `documentary_photo` (consumer `public_newsroom_articles_v1.py:499-513`).
  - The hosting step `live_contentops/cloudinary_delivery_media_v1.py:351-378` writes each hosted asset without `modality` and without the photo rights fields, though it validates `modality` on its input at :186-195.
  - PPI's four assets carry exactly that step's 20 keys. The 4 Nov jobs piece, which is admitted, has `modality` on every asset.
  - The older pieces also tag post cards `editorial_data_journalism` with `article_inclusion: true`.
  - Owner: CC-253 (Codex Publisher).
- **NEWSROOM_UTC_CLOCK_REQUIRED** (Southwest). Two sources are undated CFTC explainer pages with `published_at_utc: ''`, and the reader (:444-446) requires a clock on every source. The fix belongs in the reader (Codex Web): accept an undated source and show no date, since a filled-in date would be invented.
- **Delay.** The PPI preview waited 1 h 55 min for two Japanese releases that have no arming run. The worker adds T0±2 h around all 128 calendar releases (`republish_preview_articles_v1.py:244-275`), on top of its hard-coded NFP, CPI and PPI windows. That is Codex Web's call. The worker is hash-pinned, so the hook is rebound after any change.

### The worker log, fixed here

Each launch opened the log with a plain write handle, so a child wrote from the offset its handle had at launch. On 5 Nov both workers wrote from byte 0, and the queued worker's UNCHANGED result replaced the PUBLISHED result. The rest of the PUBLISHED result survives in the log, starting at `"site"`.

`_open_worker_log` now opens the log on Windows with FILE_APPEND_DATA and no FILE_WRITE_DATA, so every write lands at the end. `tests/test_preview_article_hook_log_append_cc248.py` has 3 tests:

- two queued child processes;
- a write at offset 0;
- the hook's own launch.

The first two fail on the old handle, and the first reproduces the 5 Nov log. With the hook tests, 17 pass.

## Rebind to CC-295 (5 Nov)

Codex Web's CC-295 (`backlog/cc-295-article-admission`, 142907e620) changes the reader and the worker:

- the reader takes undated sources, nested chart sources and hosted data cards;
- the worker drops the per-release and daily waits, and keeps the 6, 10 and 13 Nov 18:30-22:30 GMT+7 windows and a check for 4 GB of free RAM.

The worker is hash-pinned, so the binding moves with it:

- **The consumer root:** `Worktrees/codex-web-cc254-clean`, which only this hook uses, moves from 7f605a49 to 142907e6, an exact descendant.
  - `ui/package.json` and the lockfile are unchanged, so its own `ui/node_modules` serves the new code.
- **`consumer_module_sha256`:** 1193e2a3... becomes f73feffd... It matches the worker bytes on disk and Codex Web's `tests/evidence/cc-295/worker-sha256.txt`.
- **Reviewed before the rebind:**
  - the worker diff adds no network, process, delete or write path, and the publish path is unchanged;
  - the reader diff keeps the photo rights checks;
  - it admits a data card only under the hosting step's `attributed_facts_independent_chart` condition.
- **Rollback:** check out 7f605a49 in the consumer root and restore 1193e2a3.
