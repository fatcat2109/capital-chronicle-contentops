# Capital Chronicle ContentOps — CodeGraph Mandatory / No Superpowers / No Three-Level Delivery Owner Decision V1

Authority date: 2026-08-17
Status: `CURRENT_OWNER_DECISION`
Owner: Jim
Scope: repository-wide ContentOps implementation/audit workflow; V1 and V2 unless a later explicit owner decision supersedes it.

## Decision

Use the capability already present instead of adding a second generic process framework.

- `CODEGRAPH_MANDATORY_FOR_MEANINGFUL_IMPLEMENTATION_AND_AUDIT = TRUE`
- `SUPERPOWERS_PLUGIN_ACTIVE = FALSE`
- `THREE_LEVEL_DELIVERY_ACTIVE = FALSE`

This is a product/workflow decision, not a claim that Superpowers or Three-Level Delivery are generally poor tools.

## Canonical task workflow

For meaningful implementation, debugging, audit, refactor, or cross-file capability work:

`GitHub authority -> CodeGraph discovery/impact analysis -> exact source/tests/evidence -> implementation -> CodeGraph verification -> focused tests + real E2E/proof -> GitHub evidence audit`

Do not reduce CodeGraph to `CODEGRAPH_CURRENT` health-check ceremony.

### Required CodeGraph discovery use

In the actual writable worktree, before edits:

1. ensure/regenerate/sync CodeGraph against the exact task HEAD;
2. query the relevant component/call path;
3. identify caller/callee and impact radius;
4. identify existing analogous implementations before creating a new path;
5. identify tests that actually cover the seam;
6. use graph results to decide the smallest implementation surface.

Use `rg`/plain text search only as a fallback when the graph cannot answer the required lookup or when exact literal-byte confirmation is needed. Do not use grep-style search as the default substitute for graph routing.

### Required CodeGraph verification use

After implementation and before task completion:

1. regenerate/sync CodeGraph against the implementation tree;
2. inspect affected call paths;
3. check for newly orphaned, duplicate, bypass, or parallel execution paths;
4. verify forbidden/historical seams did not regain active callers;
5. verify intended tests and entrypoints still route through the corrected implementation.

A generated CodeGraph file that names an older source HEAD is stale for current implementation analysis even if a status packet calls it current.

## Why Superpowers is not activated

Capital Chronicle already has current owner/product authority, worktrees, heavy bounded vertical-slice execution, builder self-debugging, focused tests, GitHub evidence, and independent owner/media gates. Installing a methodology that mandates brainstorming, 2–5 minute task decomposition, mandatory generic subagent sequencing, or a second review/control workflow risks recreating microtask chains and conflicting with repo authority and V2 creative autonomy.

Useful practices such as systematic debugging, TDD where appropriate, and verification-before-completion may be used directly without installing or activating the Superpowers methodology.

## Why Three-Level Delivery is not activated

Capital Chronicle already has:

`Jim -> ChatGPT owner/alignment/audit gate -> Codex Desktop builder/coordinator -> GitHub evidence -> actual-media/real-product gate`

Adding a second Owner/Lead/Writer/Reviewer control plane would duplicate authority and encourage smaller generic slices when the project deliberately prefers one heavy bounded end-to-end capability task.

## V2 reasoning-effort topology remains unchanged

- Codex Desktop parent/session: `GPT-5.6 Sol / HIGH`.
- Bounded consequential video-creative/editorial/review work: `GPT-5.6 Sol / XHIGH`.
- XHIGH is not spent on CodeGraph generation/querying, Git, tests, rendering, transcoding, waiting, polling, evidence formatting, mechanical diagnostics, commit, or push.

## Current V2 audit finding

Evidence HEAD `d81ea603d729269d903e72e8a47e9375771ddd88` records `FAIL_QUARANTINED_AT_AUDIO_DURATION_GATE` after the HIGH-parent/XHIGH provenance correction and Windows-safe Remotion browser repair succeeded.

The committed `docs/codegraph/V2_CONTEXT.md` at that evidence HEAD still states it was generated from source HEAD `558acbdf766754f9ad2902c67c181bb4a7e14cac`, which predates implementation HEAD `8ed062577b7cb61d4ee8aec69e74822d1946c759`. Therefore the evidence label claiming committed CodeGraph current is not accepted for implementation impact analysis. The next implementation task must regenerate and actively query CodeGraph in its writable worktree before editing.
