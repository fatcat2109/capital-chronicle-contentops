# UI Spec — V6 Operator Approval Capture Console

This document specifies the layout and interactive behavior of the future static cockpit approval capture panel.

## Visual Design System
- **Color Theme**: Rich dark mode with amber alert status indicators.
- **Header**: Shows `"V6 Operator Approval Capture Console"`.
- **Payload Display**:
  - Bound Hash: `4bcbbf4eeab1bdfa2f3f94b4dbb042877c67efdb515f7feecaac5ffa3a2e71ff`
  - Preview Ref: `docs/automation/V6_PAYLOAD_PREVIEW_HASH/payload_preview_exact_review.json`
- **Safety Status Display**:
  - `dispatch_allowed_now`: false (Locked)
  - `live_write_allowed_now`: false (Locked)
  - `kill_switch_active`: true (Locked)

## Interactions
- **Review Decision Selection**: Dropdown or toggle (PENDING / APPROVED).
- **Signature Output**: Writes operator signature JSON locally upon operator action.
