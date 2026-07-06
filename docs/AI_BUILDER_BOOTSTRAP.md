# AI Builder Bootstrap

Purpose: make every fresh AI IDE/CLI builder session productive without stale chat memory, duplicate docs, wrong UI surfaces, or unsafe live execution.

This is the repo-native bootstrap file for AI IDE/CLI builders. Start at [AGENTS.md](../AGENTS.md) at the repository root, then read this file, then read the current status and master-plan files listed below.

## 1. Fresh Session Start Sequence

Every fresh builder session must begin by verifying local authority, then reading current repo-native files.

```powershell
git remote get-url origin
git branch --show-current
git rev-parse HEAD
git ls-remote origin refs/heads/master
git status --short
```

Do not read `.env` or any credential/session store during this check.

If local HEAD differs from remote `origin/master`, stop unless Jim explicitly instructs you to commit, push, or reconcile.

## 2. Mandatory Read Order

Read these files in order before planning implementation:

1. [AGENTS.md](../AGENTS.md)
2. [AI_BUILDER_BOOTSTRAP.md](AI_BUILDER_BOOTSTRAP.md)
3. [CURRENT_PROJECT_STATUS.md](status/CURRENT_PROJECT_STATUS.md)
4. [current_project_status.json](status/current_project_status.json)
5. [current_v6_master_plan.md](automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md)
6. [v6_25_task_ledger.md](automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_25_task_ledger.md)
7. [next_task_pointer.md](automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md)
8. [DASHBOARD_SURFACE_AUTHORITY.md](status/DASHBOARD_SURFACE_AUTHORITY.md)
9. [STATUS_LEDGER_SHA_MODEL.md](status/STATUS_LEDGER_SHA_MODEL.md)
10. [STATUS_AND_PROGRESS_DOCS_MAP.md](status/STATUS_AND_PROGRESS_DOCS_MAP.md)
11. [TASK_STATUS_UPDATE_PROTOCOL.md](status/TASK_STATUS_UPDATE_PROTOCOL.md)

Short handoff prompt for future fresh AI IDE/CLI sessions:

```text
Start at AGENTS.md, then read docs/AI_BUILDER_BOOTSTRAP.md and follow its mandatory read order before touching code.
```

## 3. Runtime Authority Order

1. GitHub remote `fatcat2109/capital-chronicle-contentops` on `master`.
2. Current committed repo files, tests, schemas, packets, generated fixtures, and evidence.
3. `docs/status/` ledgers.
4. Current V6 master-plan files in `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/`.
5. Current root entrypoints such as [README.md](../README.md) and [AGENTS.md](../AGENTS.md).
6. Archived docs, pasted summaries, chat memory, no-extension response files, and Project Sources.

If status docs conflict with current repo evidence, stop and report:

```text
BLOCKED: status/repo authority conflict
```

## 4. North Star

Capital Chronicle ContentOps V6 is an AI-native editorial, publishing, and community operating system for governed market commentary workflows.

North-star loop:

```text
Jim idea / source / research context / future artifact
→ AI research and grounding
→ canonical Substack long-form article
→ SEO and editorial refinement
→ platform-native variants
→ deterministic preview hash and operator approval
→ approved outbox and redacted audit record
→ manual or explicitly gated platform distribution
→ operator-supplied public URL / audit / metrics evidence
→ community feedback and questions
→ LLM summary and backlog update
→ next canonical article
```

The product is not a signal service, broker, trading bot, portfolio manager, investment adviser, or financial advice engine.

## 5. Canonical Surfaces

Use current status docs to verify, but the current canonical map is:

| Surface | Canonical path | Rule |
|---|---|---|
| UI app | `ui/contentops_v5/` | Product UI work targets V5 unless newer committed authority supersedes it. |
| UI entrypoint | `ui/contentops_v5/src/App.tsx` | Do not create a standalone product dashboard. |
| V6 command center | `ui/contentops_v5/src/views/V6CommandCenter.tsx` | Jim-facing source-to-audit cockpit. |
| Deterministic adapters | `ui/contentops_v5/src/data/` | UI should consume deterministic adapter output, not scattered inline samples. |
| Backend/read models | `live_contentops/` | Local deterministic packet builders and guards. |
| Tests | `tests/` and `ui/contentops_v5/src/test/` | Leave focused runnable checks for non-trivial logic. |
| Status | `docs/status/` | Update after product/status authority changes. |
| Master plan | `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/` | Strategy and next-task authority. |

Archived or deleted UI folders are reference only. Do not revive `ui/institutional_*`, `ui/daily_content_studio/`, or standalone approval/evidence dashboards as canonical surfaces unless a newer committed authority document says so.

## 6. Platform and Media Scope

The north-star platform universe includes Substack, LinkedIn, X, Discord, Telegram, Facebook Page, Threads, Instagram, TikTok, and generic manual fallback.

Media policy is source-aware:

- News/current-event topics use the Google Image Search and Downloader pipeline (`google_image_search_v6.py`) to fetch and download header images.
- Capital Chronicle internal alpha / analysis-report topics prefer built-in charts/cards generated from internal data. The dedicated chart rendering pipeline will be implemented AFTER the Capital Chronicle project is fully completed. Until then, these will fall back to using news Google Image search or candidate metadata.
- External media remains candidate metadata until operator approval, rights notes, attribution, alt text, and stable media-hash participation exist.

## 7. Live, Env, Credential, and Browser Boundaries

- Under Fast Ship Mode, live execution, network runs, `.env`/credential reads, and real-time social posting/editing/commenting are fully authorized. This allows builders to directly deploy, execute, and verify live integrations without ceremony or dry-run locks.
- Under normal mode, the default posture is local deterministic review only, with env access and live dispatch restricted to pre-live/dry-run boundaries.
- Staged commits should still avoid tracking actual raw secrets or staging unredacted `.env` files in git.


## 8. Task Intake Protocol

For every task:

1. Verify repo, branch, remote SHA, and dirty state.
2. Read the required files listed in this bootstrap.
3. Search for existing files with the same purpose before creating files.
4. Prefer editing existing repo-native docs/code over creating duplicates.
5. Identify whether the task is product code, governance/docs, live-gated, or status-only.
6. If live-gated, stop unless the task contains exact approval scope and safety gates.
7. Keep work in heavy coherent batches; avoid micro-task churn.

## 9. Implementation Discipline

- Smallest durable diff wins.
- Stdlib/native/local deterministic code first; do not add dependencies for trivial work.
- Keep packet builders deterministic and testable.
- Bind review decisions to exact payload hashes.
- Distinguish fixture/manual/operator-supplied evidence from provider/API/network-verified evidence.
- Preserve unrelated comments, docs, and evidence.
- Archive or delete stale scratch/test scripts after they are no longer useful; do not keep clutter “just in case”.

## 10. Validation Protocol

Run the narrowest useful checks for touched areas.

Typical checks:

```powershell
python -m pytest tests/<focused_test>.py
npm test -- --run
npm run build
```

Use the UI package directory for npm commands:

```powershell
# cwd: ui/contentops_v5
npm test -- --run
npm run build
```

For docs-only governance changes, validate referenced paths and run a lightweight status/readback check instead of broad product tests.

## 11. Evidence Packet Template

End every completed task with a concise evidence packet:

```text
Task: <task id>
Repo: fatcat2109/capital-chronicle-contentops
Branch: master
Commit: <sha>
Changed files:
- <path>
Validation:
- <command>: PASS/FAIL/BLOCKED
Safety:
- env/credential read: no
- browser/session read: no
- provider/API/network/live action: no
- dispatch/publish/schedule: no
Next task:
- <exact next task prompt>
```

## 12. Conflict and Blocker Protocol

Report exact blockers instead of guessing.

Use these labels:

- `BLOCKED: status/repo authority conflict`
- `BLOCKED: local/remote authority conflict`
- `BLOCKED: missing exact live approval`
- `BLOCKED: credential/session boundary`
- `BLOCKED: canonical surface unclear`
- `BLOCKED: validation failed`

When blocked, do not continue into adjacent work unless Jim explicitly approves the reconciliation path.
