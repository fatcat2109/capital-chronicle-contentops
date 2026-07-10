# AI Builder Bootstrap

Start at root `AGENTS.md`, then use this file. Repo evidence beats chat memory and archived plans.

## Verify Authority

```powershell
git remote get-url origin
git branch --show-current
git rev-parse HEAD
git ls-remote origin refs/heads/master
git status --short
```

Do not read secret values during authority checks. Preserve coherent local work; never reset or clean over an interrupted task.

## Mandatory Read Order

1. `AGENTS.md`
2. `docs/AI_BUILDER_BOOTSTRAP.md`
3. `docs/status/CURRENT_PROJECT_STATUS.md`
4. `docs/status/current_project_status.json`
5. `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/current_v6_master_plan.md`
6. `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/v6_25_task_ledger.md`
7. `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/platform_delivery_contract_v1.json`
8. `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/next_task_pointer.md`
9. `docs/automation/OPERATOR_BROWSER_LAB_AND_SOCIAL_CREDENTIAL_SETUP/operator_browser_lab_runbook.md`
10. `docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1/reliability_hardening_evidence_v3.json`

## Current North Star

Capital Chronicle ContentOps V6 is an AI-native automated editorial production and supervised distribution operating system.

```text
current headlines/CDP
-> LLM semantic selection and duplicate/hotspot policy
-> grounded source packet
-> tier-1 reader-facing editorial and SEO gates
-> at least three source-backed analytical visuals
-> canonical Substack publication/readback
-> native derivatives linked to Substack
-> exact media-manifest binding
-> sentence-aware balanced reply chains with three-image distribution
-> adapter writes, idempotency, and strict public readback
-> evidence and operator review
```

Substack is canonical. Local exports are fallback evidence. Manual action is recovery context, not the product.

## Canonical Surfaces

| Surface | Authority |
| --- | --- |
| Product UI | `ui/contentops_v5/` |
| UI entrypoint | `ui/contentops_v5/src/App.tsx` |
| Backend/read models | `live_contentops/` |
| Live runner | `live_contentops.eight_platform_substack_first_pipeline_v1` |
| Status | `docs/status/` |
| Strategy/contract | `docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/` |
| Browser | Microsoft Edge profile `A:\Capital Chronicle\operator-browser-profiles\contentops-social-main` |

V4 and archived dashboards are fallback/reference only.

## Non-Negotiable Product Rules

- LLM semantic ranking chooses ideas; keyword scoring is helper-only.
- Repeats inside 24 hours require a documented breaking/hotspot exception.
- Numeric truth comes from the Capital Chronicle source packet and cited primary data.
- Article media requires three analytical roles, provenance, captions, alt text, and body distribution.
- Derivative media comes only from exact approved manifest IDs/hashes; avatars and logos fail.
- Hard truncation fails. Use ordered replies/comments.
- Editorial-process narration, weak news pegs, generic watch lists, repeated filler, and invented quotes fail the deterministic tier-1 gate. A bounded LLM standards review is also required; it fails closed and cannot override deterministic blockers.
- X and Threads use a root plus two semantic replies and distribute all three approved article visuals exactly once.
- Instagram feed acceptance requires exact canonical URL text and CTA; caption clickability is not universal.
- YouTube defaults to Community text + image + canonical link. Video/Short is separate non-default mode.
- TikTok remains blocked until callback, OAuth, token refresh, native adapter, identity, and app audit are complete; app keys alone are insufficient.
- A click or API response is not success. Require stable public identity plus text/media/link/account readback.
- Derivative-only resume freezes Substack and every successful destination.

## Current Evidence

Run `eight_platform_live_20260710_recovery1` is the preserved transport fixture. V3 reclassifies its X and Threads chains as live quality failures while the local sentence-aware plans pass. The newest LinkedIn image-only activity was edited in place; no third post was created.

Evidence: `docs/automation/EIGHT_PLATFORM_FULL_PIPELINE_V1/eight_platform_live_20260710_recovery1/`.

For a platform failure, open `platform_delivery_contract_v1.json` and follow `failure_resolution_map.<platform>` to the compiler, adapter, readback, ledger, focused tests, and evidence.

## Task Protocol

1. Verify repo/branch/remote/dirty state.
2. Read current authority files above.
3. Search before creating files; keep one canonical surface per purpose.
4. Implement through ContentOps adapters, not ad hoc browser production clicks.
5. Run focused tests, integration checks, `py_compile`, `git diff --check`, and secret-like scans.
6. Update status and next-task authority whenever product state changes.
7. Commit and push coherent work to `master` unless a real blocker prevents it.

## Safety

Do not expose or commit raw tokens, cookies, localStorage, sessionStorage, webhook URLs, provider keys, or browser-session secrets. Do not present output as financial advice. Preserve malformed live posts as evidence unless the operator separately authorizes destructive cleanup.
