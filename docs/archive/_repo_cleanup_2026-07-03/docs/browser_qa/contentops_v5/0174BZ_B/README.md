# ContentOps V5 — Browser QA 0174BZ_B

Task: `TASK_CONTENTOPS_0174BZ_B_V5_REAL_DESKTOP_BROWSER_QA_AND_LAYOUT_CONTAINMENT_FIX_V0`

Supersedes the invalid 0174BZ_A capture (narrow 500x715 viewport, squeezed
workspace). This round fixes the AppShell layout containment and captures real
desktop-width screenshots with on-disk pixel dimensions verified.

> [!IMPORTANT]
> No final visual PASS is claimed here. These screenshots are layout-containment
> evidence only, captured to confirm the desktop shell no longer squeezes the
> workspace. Flagship visual buildout and visual sign-off happen in a later task.

## Layout containment fix

Root cause of 0174BZ_A: the shell pinned a `w-80` inspector with `shrink-0`
while the `w-60` nav and `flex-1` main had no minimum width. At narrow capture
widths the inspector held 320px and the main column collapsed into vertical
single-letter text.

Fix (in `ui/contentops_v5/src/App.tsx`):

- Left nav: added `shrink-0` so it holds a stable 240px and never collapses.
- Main workspace: `min-w-[28rem]` floor + inner `mx-auto w-full max-w-6xl`
  content wrapper so the reading column stays usable and centered.
- Inspector rail: `hidden ... xl:block` — only renders at >=1280px, so narrower
  viewports give the full width to nav + workspace instead of squeezing.
- Existing `overflow-y-auto` internal scroll containers on main and inspector
  are retained; no page-level horizontal compression.

Light default theme and forced dark Evidence Vault mode are preserved. All five
views and all safety states are unchanged.

## Captures

All PNG dimensions below were verified on disk with `System.Drawing` after the
files were copied into this directory.

| View | Requested viewport | Actual PNG | File |
|---|---|---|---|
| Command Center | 1440x900 | 1440x900 | command_center_1440x900.png |
| Content Inventory | 1440x900 | 1440x900 | content_inventory_1440x900.png |
| Writer Studio | 1440x900 | 1440x900 | writer_studio_1440x900.png |
| Approval & Dispatch | 1440x900 | 1440x900 | approval_dispatch_1440x900.png |
| Evidence Vault | 1440x900 | 1440x900 | evidence_vault_1440x900.png |
| Command Center | 1536x864 | 1536x864 | command_center_1536x864.png |
| Command Center | 1920x1080 | 1920x1080 | command_center_1920x1080.png |

## Visible layout result

- Left nav visible and intact at ~240px across all widths; no collapse.
- Main workspace has usable, wide reading width; no vertical single-letter
  text columns at any captured size.
- Inspector rail visible on the right at all three desktop widths (all are
  >=1280px, above the `xl` breakpoint).
- Evidence Vault renders in dark evidence mode; other views render in light
  default theme.
- No page-level horizontal scroll / compression observed.

## Known caveats

- Viewports were achieved by sizing the browser window to compensate for
  chrome; the inner content viewport was verified to match the requested size
  before each capture, and the saved PNG pixel dimensions match exactly.
- Below the `xl` (1280px) breakpoint the inspector is intentionally hidden.
  Sub-1280px responsive behavior was not part of this task's capture matrix.
- This is layout-containment evidence only. No final visual PASS is claimed.

## Validation

- `npm run build` — green (tsc -b && vite build).
- `npm test` — 36/36 passing (5 app + 31 safety).
- `git diff --check` — clean.
- Static forbidden-token scan over `src/` — clean (only comments / fixture
  copy / safety-test regex literals; no executable forbidden behavior).
- Screenshot dimensions — verified on disk (table above).
