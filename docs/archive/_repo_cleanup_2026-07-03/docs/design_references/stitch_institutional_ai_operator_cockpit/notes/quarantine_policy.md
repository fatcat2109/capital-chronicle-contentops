# Quarantine Policy — Stitch Visual Reference

## Scope

This folder (`docs/design_references/stitch_institutional_ai_operator_cockpit/`)
is a read-only design reference area. It is not runtime authority and not
product UI.

## Rules

- This folder is read-only design reference. Treat contents as advisory visual
  reference only.
- It is not runtime authority. Nothing here defines current operational truth.
- Raw HTML here MAY contain external links (Tailwind CDN, Google Fonts,
  Material Symbols, other remote references). These are FORBIDDEN in runtime
  product UI. They exist here only because this is a quarantined reference.
- Future runtime external-dependency scans MUST scope product runtime assets
  (e.g. `ui/`) separately from this quarantined reference folder. A remote URL
  inside `raw/` is NOT a runtime dependency and must not be treated as one.
- Future tasks MAY inspect raw files but MUST NOT import them directly into
  `ui/` or make them reachable as a product entrypoint.
- Future UI code MUST use local CSS/JS only (no CDN, remote fonts, remote
  icons, remote scripts, or runtime network).
- Secrets are forbidden in this folder. If secret-like content is ever found,
  remove it and report. No `.env` or credential files may be placed here.
- Do not add generated screenshots/logs here. Browser QA artifacts belong
  under `docs/browser_qa/<TASK_LABEL>/`, not in this reference folder.

## Translation Obligation

When a future task builds runtime UI from this reference, it must translate
visual tokens into local CSS, replace remote icons with local text/CSS-only
indicators, and convert action-looking controls into inspect-only,
disabled-with-reason, or future-only records.
