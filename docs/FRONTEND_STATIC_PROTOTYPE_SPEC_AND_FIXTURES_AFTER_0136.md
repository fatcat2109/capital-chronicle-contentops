# Frontend Static Prototype Spec (0136)

## Purpose
This document defines the static HTML/CSS prototype requirements. This prototype provides a visual mock of the 0135 UI/UX spec without instantiating any real frontend application runtime, packages, servers, or APIs.

## How to Inspect
You can inspect the prototype locally by navigating to `static_prototypes/contentops_operator_console/index.html` and opening it in any standard web browser. No server or backend is required.

## Restrictions
- **No NPM/React/Vite**: No framework scaffolding is present.
- **No Live API or Backends**: The code will not execute fetches or handle credentials.
- **Placeholder Controls Only**: All buttons are strictly placeholders (e.g. `Record manual URL placeholder`). Actionable live commands like `Live publish` are forbidden.
- **Safety Banners**: Every page explicitly renders banners like `NOT PUBLIC POSTABLE` and `NO CREDENTIALS LOADED` to warn operators that this is a simulated dry-run view.

## Relationship to Future Work
This confirms the structural data binding contracts required before any true interactive frontend or secure live-gate is built. No Project Sources refresh is executed after this step.
