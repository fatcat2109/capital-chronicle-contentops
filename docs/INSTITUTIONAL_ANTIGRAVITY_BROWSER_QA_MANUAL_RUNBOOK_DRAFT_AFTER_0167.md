# Institutional Antigravity Browser QA Manual Runbook Draft (After 0167)

## Status Update
* Antigravity has **not** been run in task 0167.
* Browser QA requires a separate, explicit operator/ChatGPT GO.

## Runbook for Future Browser QA
When an explicit task is approved to run Antigravity on this institutional shell, the agent MUST adhere to the following contract:

1. **No Env/Credential Access**: Browser QA must not read environment variables or credentials.
2. **No Network/API Calls**: Browser QA must not call any platform, API, or external network.
3. **No Screenshots by Default**: Browser QA must not capture or share screenshots unless explicitly approved by the operator in the specific QA task.
4. **Local Static Focus**: Browser QA must only inspect local static file rendering against `ui/institutional_shell/index.html`.
5. **Validation Scope**: Browser QA must verify:
   * No secrets are visible in the rendered UI.
   * Disabled controls remain properly disabled and marked.
   * Required screenshot-safe and watermark labels are visible.
   * Navigation links map correctly to local fixture screens.
   * Layout stability for the 12 institutional screens.
