# X CDP Operator GO-Phrase Live-Click Gate Dry Run

Task: `TASK_CONTENTOPS_V6_X_CDP_OPERATOR_GO_PHRASE_LIVE_CLICK_GATE_DRY_RUN_V0`

## Purpose

Validate operator intent against a specific X CDP pre-live packet before any future supervised live-click task.

This gate is **not** a live-click executor. It proves, locally and deterministically, whether a future separately approved live task could proceed to the next decision point.

## Exact GO Phrase

The dry-run fixture phrase is:

```text
I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY
```

The raw phrase is never stored in evidence. The packet stores only SHA-256 hash evidence and match status.

## Command

```powershell
python -m live_contentops.x_cdp_operator_go_phrase_live_click_gate_dry_run_v6 --dry-run --payload-text "Capital Chronicle educational briefing: supervised pre-live X payload validation." --operator-go-phrase "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY" --cdp-port 9223 --command-line "msedge.exe --remote-debugging-port=9223 --user-data-dir=A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"
```

Operator wrapper:

```powershell
python -m live_contentops.operator_browser_lab gate-x-live-click --dry-run --payload-text "Capital Chronicle educational briefing: supervised pre-live X payload validation." --operator-go-phrase "I APPROVE X CDP LIVE CLICK GATE DRY RUN FOR THIS PRELIVE PACKET ONLY" --cdp-port 9223 --command-line "msedge.exe --remote-debugging-port=9223 --user-data-dir=A:\Capital Chronicle\operator-browser-profiles\contentops-social-main"
```

Fixture evidence:

```powershell
python -m live_contentops.x_cdp_operator_go_phrase_live_click_gate_dry_run_v6 --dry-run --fixture-bundle
```

## Safety Boundary

- `--dry-run` is required.
- No browser launch.
- No CDP probe.
- No DOM read.
- No cookie, localStorage, sessionStorage, token, header, env, or credential read.
- No X API or paid API call.
- No public URL fetch.
- No registry append.
- No click, publish, scheduler, retry, comment, DM, or reaction.
- No raw GO phrase storage in evidence.

## Passing Gate Requirements

A packet is eligible only when all checks pass:

1. Source packet is an X CDP pre-live post packet.
2. Pre-live packet status is ready for operator review.
3. Pre-live packet ID recomputes exactly.
4. Payload hash recomputes exactly.
5. Optional expected packet ID and payload hash match when supplied.
6. Profile guard is `contentops_profile_ok`.
7. Registry expectation is platform `x` with expected account/destination refs.
8. Registry append remains blocked now.
9. Operator GO phrase hash matches the exact expected phrase.

Even when all checks pass, `live_click_allowed` remains `false`; a separate future live task is required.

## Evidence

- Evidence bundle: `docs/automation/X_SUPERVISED_CDP_GO_PHRASE_GATE/task_contentops_v6_x_cdp_operator_go_phrase_live_click_gate_dry_run_evidence.json`
- Tests: `tests/test_x_cdp_operator_go_phrase_live_click_gate_dry_run_v6.py`
