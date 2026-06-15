# Stitch ContentOps V5 / V5.1 — Design References (Reference Only)

> [!IMPORTANT]
> These Stitch V5 and V5.1 assets are **visual / product references only**.
> They are **not** runtime implementation and are **not** a runtime dependency authority.

## What these files are

- Static HTML + PNG exports from Stitch used to communicate the intended
  visual language, layout, and product surfaces for the Capital Chronicle
  ContentOps **V5** front-end rebuild.
- A shared brand/product brief: `institutional_contentops.md`.

## Hard rules for implementation

- Do **not** copy raw Stitch HTML into runtime app code.
- Do **not** use runtime Tailwind CDN (`cdn.tailwindcss.com`).
- Do **not** use Google Fonts runtime links (`fonts.googleapis.com` / `fonts.gstatic.com`).
- Do **not** use Material Symbols runtime links.
- Do **not** use external image URLs at runtime (e.g. `lh3.googleusercontent.com`).
- V5 implementation must use **build-time dependencies only** (Vite + React + TypeScript + Tailwind build-time, bundled fonts, bundled icons).

These Stitch exports contain remote URLs (Tailwind CDN, Google Fonts, Material
Symbols, external avatar/image hosts) purely as a by-product of the Stitch
export format. They are reference-only and must never be treated as allowed
runtime dependencies.

## Visual identity decisions

- **Default V5 identity:** light institutional CMS / editorial.
- **Secondary identity:** dark Evidence Vault mode (forensic / compliance rooms).
- The V4 dark-terminal style is **historical / reference only**, not the default V5 identity.
- **`v5.1` is the preferred visual reference over `v5`** where the two conflict.

## Safety boundaries

- No live posting.
- No scheduler.
- No provider / platform API.
- No credential / env read.

## Folder structure

- `v5/` — original V5 Stitch screen set (5 HTML + 5 PNG).
- `v5.1/` — refined V5.1 Stitch screen set (5 HTML + 5 PNG), **preferred**.
- `institutional_contentops.md` — shared brand/product brief (identical across source sets; stored once).
- `manifest.json` — machine-readable reference index.

## Next task

`TASK_CONTENTOPS_0174BZ_V5_FRONTEND_SCAFFOLD_AND_DESIGN_SYSTEM_FOUNDATION_V0`
