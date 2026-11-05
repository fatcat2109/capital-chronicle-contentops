# CC-300: Claude can write a piece end to end when Codex is out of quota

From the ContentOps V1 lane (Claude, Opus 5.5), 5 Nov 2026. Ops Product assigned the item after Jim's 5 Nov word that Codex is over its weekly quota.

## Why

Until this change, only Codex surfaces could run the editorial stages (select, visual edit, write, revise, final visual review):

- `NativeDesktopTurn.submit` accepted only the three Codex surfaces;
- every request sealed Codex's model and effort (`gpt-6.1-sol`);
- `native_role_call` could only describe Codex collaboration calls;
- the continuation step accepted only those two tools.

A Claude Code session could not answer a stage without being recorded as Codex, and C5 forbids that.

## What changed

- **The operation chooses its editorial agent once.**
  - `run_native_desktop_editorial.py newsroom|standing --editorial-agent claude` writes `"editorial_agent": "claude"` into a new operation's binding.
  - An absent field means Codex, so Codex bindings and requests keep their exact bytes and hashes.
  - A resume that names another agent fails with `OWNER_EDITORIAL_AGENT_CHANGED_USE_NEW_OPERATION`, and the registered binding was already immutable.
- **Every turn reads it from the one registered binding.** `NativeDesktopTurn` reads `native-operation-binding-<run>`, so the editorial, media, review and publication helpers all agree on the agent.
- **Each request seals its own family.** A Claude request carries `editorial_agent: claude`, `requested_model: claude-opus-5-5` and `requested_reasoning_effort: max`.
  - Every Claude role is Opus 5.5 at max. One Claude Code session can then run every stage itself at one configured effort, and stay the same writer from visual edit to final review, as Codex's MAX writer does.
- **A return is checked against its request's family** (`submit`, `validate_final_visual_return`).
  - A Claude request accepts only `CLAUDE_CODE_SESSION`, with the Claude model and effort, observed or explicitly labelled CONFIGURED_NOT_OBSERVED.
  - A Codex request accepts only the Codex surfaces.
  - The same-writer, invocation-evidence, speed and schema checks are unchanged.
- **The next role call for Claude is `claude.session`.** It tells the same session to run the stage, save `request_sha256`, `output` and its own `invocation_observation`, submit, and advance. The observation holds:
  - the session id from its transcript and scratchpad paths;
  - the model ID its system prompt states;
  - an effort that is observed, or configured and labelled as such.
- **Reviewer prompts use the family's own label.** They no longer hard-code "gpt-6.1-sol/max" or "MAX".
- **Telemetry reports the family.** `owner` is `NATIVE_CLAUDE_CODE`, and the requested model is Claude's.

## Tests (`tests/test_native_editorial_claude_cc300.py`, 10)

- A Claude operation's request seals Claude labels, accepts a Claude return and records `NATIVE_CLAUDE_CODE`.
- A Claude return is refused when any of these holds:
  - its surface is Codex (it is never recorded as Codex);
  - its model is Codex's;
  - its configured effort is wrong;
  - it has no invocation id or no observation source.
- A Codex operation is unchanged: no field is added, and it refuses a Claude return.
- The next role call is `claude.session` with Claude labels. A revise needs the same session's configuration. A Codex-labelled continuation or a widened effort is refused.
- An unknown agent is refused.

## Not covered yet

Chart revision after publication (`release_chart_revision_v1`) still requires a Codex writer. It is not on a first piece's path.
