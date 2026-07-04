# X CDP Profile Guard — Reusable Operator Command

Task: `TASK_CONTENTOPS_V6_X_CDP_PROFILE_GUARD_REUSABLE_OPERATOR_COMMAND_V0`

## Purpose

Promote the proven TASK 0087AD profile/port lesson into a reusable guard command for supervised X browser/CDP work.

The command checks operator-supplied/process command-line metadata before any live click and blocks unsafe profiles.

## Commands

### Fixture evidence bundle

```powershell
python -m live_contentops.x_cdp_profile_guard_v6 --dry-run --fixture-bundle
```

### Direct guard report

```powershell
python -m live_contentops.x_cdp_profile_guard_v6 --dry-run --cdp-port 9222 --command-line "chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\Users\bullw\.gemini\antigravity-browser-profile"
```

### Operator browser lab wrapper

```powershell
python -m live_contentops.operator_browser_lab guard-x-cdp --dry-run --cdp-port 9222 --command-line "chrome.exe --remote-debugging-port=9222 --user-data-dir=C:\Users\bullw\.gemini\antigravity-browser-profile"
```

## Guard States

| State | Meaning | Live click allowed |
|---|---|---:|
| `contentops_profile_ok` | Approved ContentOps browser profile | yes |
| `antigravity_profile_blocked` | Antigravity browser profile | no |
| `builtin_browser_profile_blocked` | Browser default/profile root | no |
| `unknown_profile_blocked` | Any non-approved profile | no |
| `cdp_unavailable_blocked` | No CDP process metadata supplied/found | no |

## Safety Boundary

The guard does **not** read:

- `.env` values
- cookies
- localStorage
- sessionStorage
- tokens
- headers
- browser profile files
- DOM content

The guard does **not** perform:

- browser launch
- CDP probe
- X API call
- post/comment/reply/DM/repost/like/follow
- scrape
- public URL fetch
- scheduler/retry/dispatch

## Evidence

Local fixture evidence:

[task_contentops_v6_x_cdp_profile_guard_reusable_operator_command_evidence.json](file:///a:/Capital%20Chronicle/tools/cc-live-contentops/docs/automation/X_SUPERVISED_CDP_PROFILE_GUARD/task_contentops_v6_x_cdp_profile_guard_reusable_operator_command_evidence.json)

## Future Live Boundary

Future live X browser/CDP tasks must still require an exact approved GO phrase and must compare account/destination/payload before any click. This task only provides the reusable pre-click profile guard.
