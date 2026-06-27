# V6 Current Authority Index

This index defines the durable hierarchy of authority for the Capital Chronicle ContentOps V6 repository. It ensures that runtime configuration and codebase truth are dynamically verified rather than assumed from static or stale Project Sources documentation.

## Durable Authority Hierarchy

1. **GitHub Remote (Primary Runtime Authority)**
   * The fetched remote commit history, branch states, and file diffs on GitHub are the absolute runtime authority.
   * ChatGPT/Antigravity must check the remote HEAD directly at task start before relying on local handoff claims.

2. **Repo-Local Packets & Tests (Implementation Evidence)**
   * Local JSON configuration files and automated pytest verification suites represent concrete evidence of implementation completeness.

3. **V6 Master Plan (Strategic Product Authority)**
   * `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md` outlines the strategic product vision.

4. **V6 25-Task Execution Plan (Roadmap Authority)**
   * `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_25_task_ledger.md` acts as the sequence map for tasks.

5. **V6 Fast Ship Operating Profile (Execution Posture Authority)**
   * `docs/automation/V6_FAST_SHIP_OPERATING_PROFILE/fast_ship_operating_profile.md` defines the default posture (heavy batch, fast ship, live-capable adapters permitted under scoped conditions).

6. **Live / Env Scope Contract (Governance Authority)**
   * `docs/automation/V6_FAST_SHIP_OPERATING_PROFILE/live_env_scope_contract.md` dictates minimum fields for environmental or platform interaction.

7. **Standing Operating Rules (Evidence & Visual Governance)**
   * Standing Operating Rules remain evidence/audit/visual governance, but Fast Ship profile overrides repeated prompt ceremony restricting live access.

8. **Project Sources Upload Bundles (Context & Handoff Only)**
   * Project Sources bundles are meant for context bootstrap and handoff only. They never represent final repository or runtime authority.

## Dynamic Verification Rules (Strict Bans)
To prevent Project Sources from becoming stale and out-of-sync, the following properties **must not** be hardcoded or accepted as static truths in evergreen handoff files:
* stale generation hashes or final commit SHAs
* stale task labels or next tasks as permanent truths

Instead, future tasks must dynamically read the actual latest repository commit via Git.
