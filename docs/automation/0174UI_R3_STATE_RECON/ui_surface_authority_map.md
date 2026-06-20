# ContentOps UI Surface Authority Map

This document establishes the authoritative hierarchy for all user interface surfaces, mock shells, and static HTML files in the repository.

---

## 1. Audited UI Surface Inventory

The following user interface surfaces and directories are cataloged in the repository:

| Path | Classification | Purpose & State |
|---|---|---|
| `ui/contentops_v5/` | **V5 Authoritative App** | The primary active surface for the ContentOps React/Vite/TypeScript/Tailwind application. |
| `ui/institutional_operator_cockpit_v4/` | **V4 Fallback / Reference** | Frozen V4 layout used for visual baseline and safety references. *Do not write new features here.* |
| `ui/institutional_operator_cockpit_v3/` | **Visual Anti-Pattern / Legacy Reference** | Historic draft rejected by North Star audit. Retained for regression/history only. |
| `ui/institutional_operator_cockpit_v2/` | **Visual Anti-Pattern / Legacy Reference** | Historic draft. Retained for regression/history only. |
| `ui/daily_content_studio/` | **Legacy Sandbox Reference** | Static prototype. Retained for reference. |
| `ui/institutional_shell/` | **Legacy Sandbox Reference** | Static prototype. Retained for reference. |
| `docs/browser_qa/` | **Docs / Evidence Artifact** | Subagent screenshot repository confirming layout rendering. |

---

## 2. Strict Interface Rules

### Exact Path to Open for V5
- **Authoritative Surface**: [ui/contentops_v5/](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/contentops_v5/)
- This is a fully structured, React + Vite application. It contains its own package manifests, tsconfig, and vitest unit test suite.

### Paths That Are NOT V5
- **Do NOT treat** `ui/institutional_operator_cockpit_v4/index.html` or any other directory besides `ui/contentops_v5/` as the primary V5 surface.
- Stands as a visual fallback and reference only.

### Structure of V5 App
- **Structure**:
  - `src/App.tsx` (main shell)
  - `src/index.css` (Tailwind and styling rules)
  - `src/types.ts` (data models)
  - `src/fixtures.ts` (local mock data models)
  - `src/test/` (Vitest spec files checking state logic, AI variants, and safety compliance)

### V5 Visual QA Status
- **Existence of Visual QA**: Yes, screenshots exist under `docs/browser_qa/contentops_v5/` capturing viewport renders at multiple stages (e.g. BZ, CA, CI runs).
- **Audit Requirement**: No visual `PASS` can be claimed without raw screenshot files captured by the browser subagent and independently inspected by ChatGPT. Standalone generated HTML pages are strictly evidence artifacts and do not represent active product surfaces unless verified.
