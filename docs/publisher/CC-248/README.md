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

## Checks, 5 Nov 22:10-22:20Z

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
