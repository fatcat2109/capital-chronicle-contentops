# Operator Cockpit V4 — North-Star Gap Map

Task: TASK_CONTENTOPS_0174D_OPERATOR_COCKPIT_V4_NORTH_STAR_GAP_MAP_AND_COMPOSITION_BLUEPRINT_V0

No-code task. This document does not authorize or contain frontend runtime code.
It maps the gap between the current Operator Cockpit V3 and the north-star
institutional cockpit, grounded in committed repo evidence.

## 1. Files Read

V3 implementation and docs:
- ui/institutional_operator_cockpit_v3/index.html
- ui/institutional_operator_cockpit_v3/styles.css
- ui/institutional_operator_cockpit_v3/view_model.js
- ui/institutional_operator_cockpit_v3/cockpit.js
- ui/institutional_operator_cockpit_v3/README.md
- tests/test_institutional_operator_cockpit_v3.py
- docs/TASK_CONTENTOPS_0174B_V3_BRANDKIT_EXTRACTION.md
- docs/TASK_CONTENTOPS_0174B_V3_TASTE_ALIGNMENT_PLAN.md

0174C V3 browser QA evidence:
- docs/browser_qa/TASK_CONTENTOPS_0174C_OPERATOR_COCKPIT_V3_VISIBLE_ANTIGRAVITY_BROWSER_QA_V0/visible_browser_qa_report.md
- docs/browser_qa/TASK_CONTENTOPS_0174C_OPERATOR_COCKPIT_V3_VISIBLE_ANTIGRAVITY_BROWSER_QA_V0/visible_qa_manifest.json
- docs/browser_qa/TASK_CONTENTOPS_0174C_OPERATOR_COCKPIT_V3_VISIBLE_ANTIGRAVITY_BROWSER_QA_V0/screenshots/ (28 PNGs, listed in manifest)

Brandkit / Stitch references (raw Stitch references read directly in 0174D1):
- docs/design_references/STITCH_OPERATOR_COCKPIT_CLINE_README.md
- docs/design_references/stitch_institutional_ai_operator_cockpit/manifest.json
- docs/design_references/stitch_institutional_ai_operator_cockpit/raw/technical_matte_operator/DESIGN.md
- docs/design_references/stitch_institutional_ai_operator_cockpit/raw/command_center_capital_chronicle/command_center_capital_chronicle.html
- docs/design_references/stitch_institutional_ai_operator_cockpit/raw/publish_readiness_tower_capital_chronicle/publish_readiness_tower_capital_chronicle.html
- docs/design_references/stitch_institutional_ai_operator_cockpit/raw/evidence_vault_capital_chronicle/evidence_vault_capital_chronicle.html
- docs/design_references/stitch_institutional_ai_operator_cockpit/notes/extraction_notes.md
- docs/design_references/stitch_institutional_ai_operator_cockpit/notes/quarantine_policy.md
- docs/TASK_CONTENTOPS_0174R_STITCH_REFERENCE_EXTRACTION.md
### Raw Stitch Direct Read Summary

The required raw Stitch HTML/design reference files listed above were read
directly in 0174D1 (not merely referenced):
- command_center_capital_chronicle.html, publish_readiness_tower_capital_chronicle.html,
  and evidence_vault_capital_chronicle.html were opened and inspected directly.
- manifest.json, DESIGN.md, extraction_notes.md, quarantine_policy.md, the
  STITCH_OPERATOR_COCKPIT_CLINE_README.md, and TASK_CONTENTOPS_0174R_STITCH_REFERENCE_EXTRACTION.md
  were read directly.

Quarantine / reference-only status (unchanged):
- Raw Stitch HTML remains quarantined reference only and is NOT runtime authority.
- No raw HTML was copied into runtime (ui/). No raw HTML is reachable as a product
  entrypoint. The raw references carry remote CDN/Google Fonts/Material Symbols links
  that are forbidden in runtime; V4 must translate tokens into local CSS only.
- This is a text/markup read only. No pixel/image inspection of the PNG screenshots
  is claimed; the .png reference images were intentionally skipped per the manifest.

High-level design implications extracted (carried into the blueprint):
- Command Center should be mission-control (verdict-first), not a generic card grid.
- Publish Readiness should be gate-matrix-first, not platform-card-first.
- Evidence Vault should be a compliance-room / evidence-room, not a lineage list only.
- DESIGN.md should drive the technical-matte aesthetic: flat tonal depth (no shadows),
  sharp 0px corners, 1px gridline structure, mono data typography (JetBrains Mono for
  IDs/hashes/evidence refs), and status semantics where color communicates governance
  safety only and never market direction.



North-star / strategy docs:
- docs/INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_MASTER_PLAN_AFTER_0157.md
- docs/CONTENTOPS_RECONCILED_ROADMAP_AFTER_0126.md (available)
- docs/CONTENTOPS_STRATEGY_RECOVERY_MAP_AFTER_0126.md (available)
- docs/Capital Chronicle ContentOps - Final Master Plan for Pre-Alpha Content + API Automation Readiness.md (available)
- recovered_strategy_docs/FINAL_MASTER_PLAN_PRE_ALPHA_CONTENT_AND_API_AUTOMATION_READINESS_AFTER_0077.md (available)

## 2. Inaccessible / Substituted Files

- docs/Capital Chronicle ContentOps Master Plan ui ux plan.pdf — not found by that
  exact name. PDFs in docs/ are binary and not reliably readable as text here.
  Substitution: docs/INSTITUTIONAL_UI_UX_FRONTEND_REBUILD_MASTER_PLAN_AFTER_0157.md
  is the repo-native, text-readable north-star authority and was used instead.
- CURRENT_STATE_SUMMARY_AFTER_0174_ROLLBACK_MINIMAL.md and the AFTER_0174 bundle
  docs were not located under docs/ by those exact names; the project_sources_bundle
  and recovered_strategy_docs equivalents are present and were used for grounding.
- Conclusion: enough repo-local, text-readable north-star material exists to produce
  a grounded blueprint. NOT BLOCKED on source availability.

## 3. V3 Screenshot / Evidence Inspection

Image-interpretation limitation: this environment cannot reliably interpret PNG
pixels as visual evidence. The 28 screenshots are confirmed present and catalogued
in visible_qa_manifest.json (4 viewports x 7 screens; all capture_status PASS;
sha256 + size recorded). Their existence and capture integrity are accepted.

Because pixel-level inspection is not reliable here, per the task instruction the
ChatGPT visual audit findings embedded in the 0174D prompt are treated as the
AUTHORITATIVE visual findings. They are corroborated by direct reading of the V3
source (view_model.js, styles.css, cockpit.js), which is text-readable.

## 4. Target-Capture Verification (0174C)

Verified directly from repo evidence, not assumption:
- visible_qa_manifest.json local_file_url =
  file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/institutional_operator_cockpit_v3/index.html
  → the correct V3 file was the capture target.
- tested_head = fa86c5a (matches the 0174B2 V3 CSS structural repair commit).
- screenshots_expected = 28, screenshots_captured = 28.
- index.html loads local styles.css, view_model.js, cockpit.js (confirmed by reading index.html).

CONCLUSION: 0174C captured the correct V3 target. The "wrong target" suspicion is
NOT supported by repo evidence. The problem is V3 itself (state model + shallow
composition), not a mis-aimed capture.

## 5. Worker 0174C Visual Judgment — REJECTED

The 0174C report claims "BLOCKER 0 / MAJOR 0 / MINOR 0" and "V3 is VISUALLY
ACCEPTABLE." This judgment is explicitly REJECTED. Direct source reading proves
the report is wrong on at least two objective points:
- It claims state "accurately displays V3 status" while view_model.js still hardcodes
  current_task "0174B" and a current_gate of "Awaiting ChatGPT audit of 0174B V3
  clean-room rebuild evidence" — stale relative to the 0174C QA moment.
- It admits test_safety_ribbon_max_width_contained "appears to have lost its assert"
  yet still reports PASS, which is a self-contradicting acceptance.


## 6. V2 vs V3 Comparison

- V2 (ui/institutional_operator_cockpit_v2): earlier failed-candidate; safety-correct
  table/terminal grammar.
- V3 (ui/institutional_operator_cockpit_v3): a clean-room rebuild that kept the SAME
  structural grammar — top safety chips, 220px left nav, thin header, per-screen
  "screen state" card, generic blocker card, flat cards/tables, bottom directive bar.
- Material verdict: V3 is a tonal refinement of V2, not a re-composition. It reads as
  a safe dark terminal/table dashboard, not a mission-control cockpit. Same skeleton,
  nicer paint. This is the core reason V3 fails the north-star audit.

## 7. North-Star Requirement Matrix

Severity legend: BLOCKER / MAJOR / MINOR / OBSERVATION.
Columns: requirement | evidence source | V3 observed | severity | V4 implication | test implication.

| Requirement | Evidence source | V3 observed | Severity | V4 design implication | Test implication |
|---|---|---|---|---|---|
| Truth consistency | view_model.js global_state | Single canonical model exists but stale | MAJOR | Keep single model; refresh per task | Stale-metadata test |
| Current-vs-historical separation | finding #3 | HEADs shown without role labels | BLOCKER | Labeled HEAD-role rail | Current/historical mixing test |
| Operator-clear under 10s | finding #8 | No dominant verdict | BLOCKER | Full-width verdict band | Verdict-region presence test |
| State before action | master plan section 4 | Partial (state cards exist) | MINOR | Keep, make composed | Grammar test |
| Evidence is the interface | master plan section 3 | Evidence is a list, not the spine | MAJOR | Evidence dependency map | Evidence-ref test |
| Missing/degraded/proxy visibility | master plan section 3 | Not surfaced | MAJOR | DEGRADED/UNKNOWN tokens visible | Status vocab test |
| Review-only by default | global_state | Present | OBSERVATION | Preserve | Safety-label test |
| No public-ready false state | content safety | Present | OBSERVATION | Preserve | not_public_postable test |
| No live/platform/API/credential affordance | findings | Present (disabled) | OBSERVATION | Preserve as gate-matrix | Forbidden-control test |
| Safety ribbon containment + proportionality | finding #7 | Contained but heavy, wraps 2 lines | MAJOR | Compact grouped rail | Ribbon proportionality test |
| No bottom bar overlap | finding #6 | Fixed directive bar clips first-fold | BLOCKER | No fixed overlap; reserved gutter | Bottom-overlap test |
| Command Center mission-control quality | finding #8 | Generic cards | BLOCKER | Verdict band + blocker stack + dep map | Composition test |
| Content Studio editorial-control quality | finding #11 | Lane cards only | MAJOR | Source/brief/claim-risk/forbidden-language panels | Lane-panel test |
| Publish Readiness gate-matrix quality | finding #10 | Cards first, matrix below fold | BLOCKER | Gate matrix first | Matrix-first test |
| Evidence Vault compliance-room quality | finding #9 | Lineage list only | BLOCKER | Validation matrix + registries first-fold | Registry test |
| Calendar manual workflow quality | finding #12 | Rows/cards, not a calendar | MAJOR | Date lanes + cadence + metrics state | Calendar-structure test |
| Visual Export screenshot-safe studio quality | finding #13 | Checklist only | MAJOR | Report cards + redaction preview | Export-safe test |
| Settings policy-inspection quality | finding #14 | Bullet list | MINOR | Policy matrix + never-display registry | Settings-policy test |
| Layout robustness 1366/1440/1536/1920 | finding #6 | Bottom clip at 1366/1440 | MAJOR | Reserved gutter + internal scroll | Layout test |
| Brandkit fidelity | DESIGN.md | Tokens used; flat/sharp partial | MINOR | Sharp 0px, flat depth, 1px gridlines | Brandkit token test |
| Futuristic institutional control-room feel | finding #2 | Reads as terminal dashboard | BLOCKER | Re-compose surfaces | Visual rubric (browser QA) |
| Not generic SaaS | finding #1 | Borderline | MAJOR | Instrumentation grammar | Visual rubric |
| Not terminal table dump | finding #1 | Yes, it is | BLOCKER | Composed modules | Visual rubric |
| Not social scheduler | content safety | OK | OBSERVATION | Preserve | Forbidden-control test |
| Not trading terminal | content safety | OK | OBSERVATION | Preserve | No-market-semantics test |

## 8. Gap Severity Roll-Up

- BLOCKERS (must be fixed in V4, cannot be patched in V3 grammar): current/historical
  HEAD-role labeling, under-10s verdict, no bottom overlap, Command Center mission
  control, Publish Readiness matrix-first, Evidence Vault compliance-room, futuristic
  feel / not-terminal-table-dump.
- MAJORS: truth freshness, evidence-as-spine, degraded visibility, ribbon
  proportionality, Content Studio depth, Calendar structure, Visual Export depth,
  layout robustness, not-generic-SaaS.
- MINORS: state-before-action polish, settings matrix, brandkit sharpness.

These require a re-composition (V4), not incremental V3 CSS edits.

## 9. Explicit Conclusion

V3 is NOT accepted as the north-star UI. V3 is retained as a failed-candidate
evidence artifact. The next build is a clean-room V4 under a new folder
(ui/institutional_operator_cockpit_v4/) per the composition blueprint. 0174D adds
no runtime code.

0174C is accepted as EVIDENCE CAPTURE only. Its visual acceptance verdict is void.
