# Operator Cockpit V4 — Test and Regression Plan

Task: TASK_CONTENTOPS_0174D_OPERATOR_COCKPIT_V4_NORTH_STAR_GAP_MAP_AND_COMPOSITION_BLUEPRINT_V0

No-code task. This document defines the deterministic tests and the browser QA
acceptance rubric that a future V4 build (0174E) must satisfy. 0174D itself only
ships blueprint docs and a test that validates those docs.

## 1. Stale Metadata Tests (V4 runtime)

- Fail if the V4 current gate equals or contains the stale string
  "Awaiting ChatGPT audit of 0174B V3 clean-room rebuild evidence".
- Fail if current_task is hardcoded to "0174B" in V4 global_state.
- Fail if V3's failed-candidate build commit is presented as the current product HEAD.
- Fail if any current-truth field references a superseded gate.

## 2. Current/Historical Mixing Tests

- Fail if a bare HEAD hash appears in the header without an adjacent role label.
- Fail if historical heads (15b87ff / 1c03ca0 / 444ef2c) appear in the current-truth
  block instead of historical_screen_provenance.
- Fail if V2/V3 build commits are not labeled historical / failed-candidate.

## 3. Status-Without-Reason Tests

- Fail if any critical status object lacks reason.
- Fail if any critical status object lacks evidence_ref_ids.
- Fail if any critical status object lacks allowed_actions or blocked_actions.
- Fail if current_truth / historical_provenance booleans are missing.

## 4. Evidence-Ref Missing Tests

- Fail if a Command Center verdict has no backing evidence_ref_ids.
- Fail if a Publish Readiness gate row has a non-PASS state with no reason/evidence.
- Fail if Evidence Vault validation matrix rows omit an evidence ref.

## 5. Forbidden Control Tests

- Fail if any enabled-looking control exists for publish/post/send/schedule/
  dispatch/API call/credential validation/env read/scrape/auto-reply/DM/evidence
  mutation/export/upload.
- Permit forbidden verbs ONLY as policy text or blocked_actions strings, not as
  wired handlers or action buttons.
- Fail if HTML contains forms, submit buttons, or onclick attributes.
- Allow exactly one click handler family: nav screen switching.

## 6. Layout / Static Tests

- html/body must block uncontrolled horizontal overflow (overflow-x hidden).
- Main grid children must use min-width: 0; grids use minmax(0, 1fr).
- A reserved bottom gutter must exist (body bottom padding >= footer/directive height).
- Long-label containers must wrap or use full-width bands (no truncation of critical truth).

## 7. Safety Ribbon Tests

- Ribbon must be overflow-safe (contained, max-width 100vw, no horizontal scroll).
- Ribbon must NOT rely on two-line wrapping for critical chips at 1366 width;
  critical chips (KILL SWITCH ACTIVE, LIVE DISABLED, NOT PUBLIC POSTABLE,
  NO FINANCIAL ADVICE, NO SIGNAL LANGUAGE) must remain in the always-visible cluster.
- The lost-assert defect from V3 (test_safety_ribbon_max_width_contained) must be
  replaced by a real assertion in V4 tests.

## 8. Bottom Directive Non-Overlap Tests

- Fail if any fixed-position element overlaps first-fold body content.
- The next-allowed-action must be reachable in-flow (truth rail and/or non-fixed footer).
- If a footer is fixed, the body must add matching bottom padding (assert presence).

## 9. Screenshot QA Checklist for V4 (browser QA, future task)

For each of 7 screens at 1366x768, 1440x900, 1536x864, 1920x1080:
- safety rail single-line, no horizontal scroll;
- truth rail labels readable, no truncated current gate;
- primary verdict/answer visible in first fold;
- no bottom-bar overlap clipping first-fold content;
- no large unlabeled dead zones;
- tables/matrices contained within panels.

## 10. Browser QA Acceptance Criteria (future task)

- 28 captures (7 screens x 4 viewports) minimum.
- Each finding must be itemized with severity; a "0 findings / visually acceptable"
  verdict is NOT accepted on its own and must be corroborated by an itemized rubric.
- Worker visual judgment is advisory; ChatGPT visual audit is authoritative.

## 11. Visual Acceptance Rubric (future task)

Score each screen on: mission-control composition (not card dump), evidence-first
hierarchy, state-before-action, current/historical clarity, brandkit fidelity
(flat depth, sharp 0px, 1px gridlines), futuristic-institutional feel, and
absence of SaaS/terminal-dump/social-scheduler/trading-terminal cues. Any BLOCKER
from the gap-map requirement matrix that remains unresolved fails acceptance.

## 12. Seven-Screen Coverage (per-doc requirement)

Every blueprint doc must name all seven screens: Command Center, Content Studio,
Publish Readiness Tower, Evidence Vault, Content Calendar / Workflow, Visual Export
/ Screenshot-Safe, and Settings / Safety Policy.

## 13. Strict North-Star Contract Phrases (verbatim, not weakened tokens)

Doc-validation must check these exact phrases, not broad tokens like "local" or
"platform": state before action; evidence is the interface;
current-vs-historical provenance; local-only; not public-postable; live disabled;
no financial advice; no signal language; no platform API; no credential read; no
bottom overlap; no stale 0174B current gate; no generic terminal/table dashboard;
compliance room; gate-matrix-first; lane separation; screenshot-safe;
never-display registry.


## 12. 0174D Doc-Validation Test

tests/test_operator_cockpit_v4_blueprint_docs.py validates that all four blueprint
docs exist, cover all seven screens, contain the required north-star concepts,
include the V3 rejected findings and target-capture verification, specify V4
composition differences, identify V3 as not accepted, and explicitly forbid
runtime code in 0174D. The test must be non-superficial: it asserts concrete V4
requirements, not just file existence.

Doc-validation tests must additionally:
- check that the required raw Stitch HTML references are documented in the Gap Map
  (command_center_capital_chronicle.html, publish_readiness_tower_capital_chronicle.html,
  evidence_vault_capital_chronicle.html) and that DESIGN.md plus the quarantine /
  reference-only status are mentioned;
- check strict safety / north-star contract phrases (e.g. "local-only", "no platform API",
  "not public-postable"), not broad weakened tokens like just "local" or "platform";
- detect a dangling Markdown code fence or a broken section sentence (e.g. the split
  "A status with no reason and" / "no evidence_ref_ids is invalid" defect, or a file
  ending with two consecutive code-fence lines);
- enforce seven-screen coverage per document, not only across the combined corpus.
