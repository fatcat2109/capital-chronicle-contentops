# IDE/CLI Evidence Packet Template - After TASK_CONTENTOPS_0074

LOCAL ONLY | ADVISORY ONLY | HUMAN REVIEW REQUIRED

Reusable final evidence packet template for any local IDE/CLI task in this repo.
Copy this block and fill every field. Do not omit fields; mark N/A where it does
not apply.

```
FINAL EVIDENCE PACKET
- task label:
- result: PASS / BLOCKED / FAIL
- repo path: A:\Capital Chronicle\tools\cc-live-contentops
- branch:
- starting HEAD:
- final HEAD:
- commit hash or skip reason:
- .gitignore status: (confirm not staged/committed/touched)
- files inspected:
- files created/changed:
- validation commands and exact results:
- tests result:
- suspicious scan result:
- BENIGN_GUARDRAIL_TEXT matches (if any):
- CLI status summary:
- alpha-wait-state-summary output summary:
- other CLI summaries:
- confirmation terminal wait-state preserved:
- confirmation no runtime capability added (unless docs-only summary CLI):
- confirmation no real alpha artifacts required/accessed:
- confirmation no Capital Chronicle core repo reads/writes:
- confirmation no network/provider/search/platform/API/credential access:
- confirmation no live posting/scheduling/auto-replies/DMs:
- forbidden-scope status:
- git status:
- active blockers:
- exact next task:
```

## Field notes
- starting/final HEAD: use `git -C "<repo>" rev-parse --short HEAD`.
- commit: one focused commit, explicit paths, never `git add .`.
- suspicious scan: scan changed/task-relevant files for secrets, network,
  provider/LLM/search/platform imports, scheduling/posting/DM language, browser
  automation, publish-ready language over synthetic content, and
  trading/broker/order/execution/signal-service claims.
- BENIGN_GUARDRAIL_TEXT: matches inside forbidden-claim lists, no-public-post
  docs, evidence templates, or wait-state instructions are benign; any functional
  capability or marketing/finance claim is BLOCKED.
- exact next task: copy verbatim from the operator/ChatGPT brief. Do not rename,
  shrink, or replace it.
```
