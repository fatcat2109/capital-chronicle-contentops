# Stitch Institutional AI Operator Cockpit — Quarantined Visual Reference

Quarantined, read-only design reference. NOT runtime authority. NOT product UI.

This folder holds raw Stitch reference files copied verbatim from the
operator-supplied local Stitch governance terminal folder so that future Cline
tasks can inspect the visual reference directly from the repo, without
depending on the operator remembering a local path.

## Read This First

Before any Operator Cockpit V2 frontend work, read:

`docs/design_references/STITCH_OPERATOR_COCKPIT_CLINE_README.md`

## Contents

- `raw/` — verbatim Stitch reference HTML and the design-token Markdown,
  relative structure preserved. These files MAY contain external links
  (Tailwind CDN, Google Fonts, Material Symbols). Those links are FORBIDDEN in
  runtime product UI. They are kept only because this is a quarantined
  reference area.
- `manifest.json` — imported/skipped file list with source path, destination
  path, size, sha256, and classification.
- `notes/extraction_notes.md` — distilled visual tokens and pattern notes.
- `notes/quarantine_policy.md` — the rules that govern this folder.

## Hard Rules

- Do not import these raw files into `ui/`.
- Do not make raw Stitch HTML reachable as a product entrypoint.
- Do not execute these files as the product shell.
- Runtime external-dependency scans must target product runtime assets
  (`ui/`), NOT this quarantined reference folder.
- No secrets are permitted in this folder.
