# Canonical Dashboard Pointer

## Canonical product dashboard

Open/build/test only the current canonical product dashboard:

```text
ui/contentops_v5/
```

Entrypoint:

```text
ui/contentops_v5/src/App.tsx
```

Package:

```text
ui/contentops_v5/package.json
```

## Reference-only surfaces

`ui/institutional_operator_cockpit_v4/` is fallback/reference only. Do not open it as the active product dashboard and do not add new product features there.

## Stale standalone surfaces

`ui/operator_approval_queue_evidence_vault/` is not canonical product UI. It is absent in the repaired checkout and must remain non-canonical if reintroduced as evidence.

## QA target

Browser QA target is V5. V4 may only be opened for reference comparison and must be labeled reference.
