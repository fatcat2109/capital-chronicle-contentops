# Shortest Path to Useful V6 Product

To evolve the cc-live-contentops codebase from a series of blocked dry-run contracts into a useful, live AI-native operating system, we must build out local/manual components and review workflows before introducing live platform/provider integrations. Live integrations must remain deferred until explicitly scoped under independent tasks.

## Recommended Build Sequence

### 1. Canonical article review-candidate intake from local markdown, review-only
- **Objective**: Import operator-provided local Markdown drafts into the workflow queue as review candidates.
- **Goal**: Transition from blocked preflight validations to parsing and staging actual draft text files on disk without committing to final approvals.

### 2. Research grounding/source-pack import contract for operator-provided sources, review-only
- **Objective**: Implement review-only source pack import templates allowing operator-provided references to ground the drafted contents.
- **Goal**: Reconcile factual checks with local files rather than using placeholder data.

### 3. SEO/editorial packet generation dry-run or provider-gated stub
- **Objective**: Setup prompt registry and provider gate dry-runs or explicitly scoped provider API stubs.
- **Goal**: Polish the drafts using simulated/stubbed LLM operations under the operator's supervision.

### 4. Platform variant staging/preview, review-only
- **Objective**: Generate and preview localized platform variant Markdown drafts (e.g. Discord drop previews) in local directories.
- **Goal**: Allow operators to review formatting and structure before any approval action.

### 5. Payload preview/hash and approval ledger strengthening
- **Objective**: Build cryptographic and hash-checking utilities to trace and lock approved payloads locally.
- **Goal**: Bind the operator's decision signature directly to the payload hash.

### 6. Discord webhook contract/outbox dry-run
- **Objective**: Establish the outbox contract and webhook dispatch templates in dry-run mode.
- **Goal**: Prove that payload serialization is correct and ready for future transmission.

### 7. Separately scoped live webhook pilot only after explicit approval
- **Objective**: Implement active webhooks to dispatch approved messages to live platforms, deferred until a separately scoped pilot task with explicit Jim authorization.
- **Goal**: Test live writing under full security and manual gate conditions.
