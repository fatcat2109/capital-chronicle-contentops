# Dashboard Surface Authority

## Audit summary

Current UI surfaces under `ui/` are classified as follows.

| Surface | Classification | Authority rule |
|---|---|---|
| `ui/contentops_v5/` | Canonical current dashboard/app surface | Future product UI work must target this surface unless a newer committed authority document supersedes it. |
| `ui/institutional_operator_cockpit_v4/` | Fallback/reference only | Use for reference comparison only. Do not add new product features here. |
| `ui/institutional_operator_cockpit_v3/` | Legacy reference | Historic static cockpit. Not canonical. |
| `ui/institutional_operator_cockpit_v2/` | Legacy reference | Historic static cockpit. Not canonical. |
| `ui/institutional_shell/` | Legacy sandbox reference | Not canonical dashboard. |
| `ui/daily_content_studio/` | Legacy sandbox reference | Not canonical dashboard. |
| `ui/operator_evidence_intake_studio/` | Specialized legacy/reference intake studio | Not canonical unless a future committed authority doc promotes it. |
| `ui/operator_approval_queue_evidence_vault/` | Stale/wrong generated surface if present | Not canonical product UI; remove/deprecate in dashboard cleanup. |

## Canonical rule

`ui/contentops_v5/` is canonical. Browser QA target is V5, not V4/static pages, unless explicitly performing reference comparison.

## V4 rule

`ui/institutional_operator_cockpit_v4/` is fallback/reference only and must not receive new product features.

## Standalone page rule

Standalone generated pages must not become canonical through convenience. `ui/operator_approval_queue_evidence_vault/`, if present, is stale/wrong for product UI authority and should be removed/deprecated during dashboard cleanup.

## Runtime authority rule

GitHub remote commits and fetched repo files remain runtime authority above this status doc. If this document conflicts with the remote or a newer committed authority document, stop and report BLOCKED for reconciliation.
