# IDE / CLI Quickstart - After TASK_CONTENTOPS_0112

LOCAL ONLY | NO NETWORK | NO PROVIDER | NO PLATFORM | NO CREDENTIALS | NO POSTING

## Repo
- Path: A:\Capital Chronicle\tools\cc-live-contentops
- Branch: master
- Accepted HEAD: 35adc4a

## Confirm baseline
```
git -C "A:\Capital Chronicle\tools\cc-live-contentops" rev-parse --short HEAD
git -C "A:\Capital Chronicle\tools\cc-live-contentops" branch --show-current
git -C "A:\Capital Chronicle\tools\cc-live-contentops" status --short
```
Expected drift (do not touch): `.gitignore`, 15 older 0085-0094* task docs,
untracked `.env`, untracked `project_sources_bundle_AFTER_0074/`.

## Status / summaries (read-only, local)
```
python -m live_contentops.cli status
python -m live_contentops.cli pre-alpha-daily-operator-content-run-summary
python -m live_contentops.cli pre-alpha-platform-manual-templates-summary
python -m live_contentops.cli pre-alpha-manual-publish-record-summary
```

## Tests
```
python -m pytest -q tests/test_security_scans.py
python -m pytest -q
```

## Daily operator flow (manual/supervised)
See `PRE_ALPHA_DAILY_MANUAL_PUBLISH_RUNBOOK_AFTER_0112.md` for the full runbook.
In short: check status, run the daily operator content run summary, inspect ready
vs blocked/not-ready counts, review platform manual templates, then manually
copy/paste externally only after the operator final check. Record manual publish
URL/timestamp/metrics only after external posting; never infer publication.

## Hard boundaries (active)
- No network/provider/LLM/web/search calls.
- No platform API/posting/scheduling/replies/DMs/scraping/automatic metrics.
- No credential or `.env` reads.
- No fake alpha output; no public-postable default; no auto-approval/auto-publish.
- No financial advice/signal language.
- No sibling/core repo mutation.
- Telegram lane remains STOPPED.

## Git safety
- Stage explicit paths only; never `git add .`.
- Do not stage `.gitignore`, `.env`, or any `project_sources_bundle_*` dir.
- Do not push.

## Next recommended product task
TASK_CONTENTOPS_0114_PRE_ALPHA_WORKFLOW_AUDIT_AND_SIMPLIFICATION_MAP_V0
