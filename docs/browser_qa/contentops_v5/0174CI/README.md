# Browser QA — ContentOps V5 · Manual Publish + Metrics Capture (0174CI)

Task: `TASK_CONTENTOPS_0174CI_V5_MANUAL_PUBLISH_AND_METRICS_CAPTURE_CONTRACT_V0`

These screenshots capture the new V5 **Manual Publish** surface and confirm the
existing shell (Platform Preview, Command Center) still renders after the change.

> [!IMPORTANT]
> This is **not** a final visual PASS. These are functional QA captures of a
> local, fixture-only dry-run surface. Visual polish, responsive breakpoints,
> and cross-theme review are out of scope for this task.

## Viewport

- All captures: **1440 x 900** (desktop).
- Dev server: `npm run dev` (Vite) at `http://localhost:5173/`.
- Theme: light (default). Evidence Vault is the only forced dark surface and is
  not part of this task's capture set.

## Captures

| File | Surface | Notes |
| --- | --- | --- |
| manual_publish_overview_1440x900.png | Manual Publish — overview | Stage tabs, policy banner, candidate list, selected record detail. |
| manual_publish_record_selected_1440x900.png | Manual Publish — record selected | Inspector rail shows the selected manual publish record + locked states. |
| manual_metrics_snapshot_selected_1440x900.png | Manual Publish — metrics snapshot selected | Manually-entered metrics card selected; inspector shows snapshot with `Manual entry only`. |
| platform_preview_after_0174CI_1440x900.png | Platform Preview (regression) | Prior 0174CF dry-run surface unchanged. |
| command_center_after_0174CI_1440x900.png | Command Center (regression) | Shell intact, nav now includes Manual Publish. |

## Validation

- `npm run build` — clean (`tsc -b && vite build`, 50 modules).
- `npm run test` — 76 passed (5 files), incl. 14 new Manual Publish tests and
  the static forbidden-token safety scan (31 checks).
- `git diff --check` — clean (only harmless LF/CRLF advisories).

## Visual notes

- The "Mark manual posted" control is always **disabled** (fixture-only) and
  never mutates persisted data.
- The manual post URL field is **read-only** and shows a local mock string; it
  is never fetched or validated against any platform.
- Required policy states render as chips on the banner:
  `MANUAL_ONLY`, `NO_PLATFORM_API`, `NO_CREDENTIAL_READ`, `NO_SCHEDULER`,
  `NO_AUTONOMOUS_POSTING`, `METRICS_MANUAL_ENTRY_ONLY`, `HUMAN_REVIEW_REQUIRED`.
- Every record carries `can_post_live: false` (structurally unrepresentable as
  true).

**This is not a final visual PASS.**
