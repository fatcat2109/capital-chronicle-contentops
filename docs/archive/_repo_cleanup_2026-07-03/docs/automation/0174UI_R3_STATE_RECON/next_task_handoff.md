# ContentOps Next Task Handoff Guide

## 1. Safety Checklist Before Proceeding

> [!IMPORTANT]
> **Do not proceed** to `0174UJ` or any subsequent roadmap steps until ChatGPT has accepted this repository state reconciliation (`0174UI_R4`).

### Exact Blocker List
Before any live deployment or automated execution task can be scheduled:
1. ChatGPT must review and verify this state report (R4).
2. The UI surface boundaries must be strictly observed.
3. No active environment secrets or credential values must ever be loaded into the front-end.
4. Next task matrix `0174UJ` (Permission and App Review scopes) must be structured and validated.

---

## 2. Worker Instructions for Future Tasks

### Warnings & Strict Rules
- **UI Surface Inspection Requirement**: Future UI workers **MUST** inspect the UI surface authority map ([ui_surface_authority_map.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/automation/0174UI_R3_STATE_RECON/ui_surface_authority_map.md)) before writing any front-end code.
- **V5 Boundary**: Do not write new visual layouts, cards, or scripts inside `ui/institutional_operator_cockpit_v4/` and call it V5.
- **Stand-alone HTML Warning**: Standalone cockpit/dashboard HTML mock files generated during regression runs are evidence artifacts only. They do not constitute the primary app surface.

### Exact Files to Inspect
Before building or modifying any user interface elements, workers must read:
1. UI surface authority map: [ui_surface_authority_map.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/automation/0174UI_R3_STATE_RECON/ui_surface_authority_map.md)
2. The V5 Master Plan: [CAPITAL_CHRONICLE_CONTENTOPS_V5_FINAL_MASTER_PLAN_AND_NORTH_STAR.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/CAPITAL_CHRONICLE_CONTENTOPS_V5_FINAL_MASTER_PLAN_AND_NORTH_STAR.md)
3. Operating policy: [CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md](file:///A:/Capital%20Chronicle/tools/cc-live-contentops/docs/governance/CONTENTOPS_PRELAUNCH_OPERATING_POLICY.md)

---

## 3. Recommended Next Task

When this state reconciliation is accepted, the next task in the pre-launch sequence is:

**`TASK_CONTENTOPS_0174UJ_PLATFORM_PERMISSION_SCOPE_AND_APP_REVIEW_GATE_MATRIX_V0`**
- *Objective*: Build the structured matrix mapping permission scopes and meta verification requirements across all 10 platform destinations.
