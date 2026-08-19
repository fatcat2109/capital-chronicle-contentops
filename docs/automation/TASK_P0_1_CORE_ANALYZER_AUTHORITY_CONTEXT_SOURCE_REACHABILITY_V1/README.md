# P0-1 Core Analyzer Authority, Context, and Source Reachability Evidence

Status: `PASS_ZERO_PUBLIC_WRITE_IMPLEMENTATION_EVIDENCE`

Baseline: `407233d0aad603ecfa53a248b8c3ebdff580d13a`

Branch: `codex/p0-1-core-analyzer-authority-context-source-reachability-v1`

## Implemented slice

- exact story/consumer/use publication-authority resolution with all required high-level states;
- explicit compatible-successor discovery under the governed upstream publication directory;
- lossless, fingerprinted publication-authorized chart/data projection shared by V1 article and V2 media consumers;
- deterministic semantic activation from bounded existing story fields before read-only DuckDB context queries;
- class-aware publication/context utilization telemetry, including zero-use reasons and query budget/time;
- exact bound timestamp recovery for accessible primary/secondary documents;
- candidate-local public-source request budget inside the existing global budget;
- unresolved reputable-news listings retained as locator-only records with zero factual authority;
- ordinary latest-web evidence remains independently usable when no publication-authorized CC packet exists.

## Zero-write demo

Run:

```text
python scripts/run_p0_core_analyzer_zero_write_demo_v1.py --output docs/automation/TASK_P0_1_CORE_ANALYZER_AUTHORITY_CONTEXT_SOURCE_REACHABILITY_V1/zero_write_e2e_v1.json
```

Result: `PASS`.

The demo exercises five story classes and all six states:

- `PUBLICATION_PACKET_AVAILABLE`;
- `PUBLICATION_PACKET_NOT_AVAILABLE`;
- `PUBLICATION_PACKET_PRESENT_BUT_NOT_AUTHORIZED`;
- `PUBLICATION_PACKET_STALE_OR_BLOCKED`;
- `CONTEXT_ONLY_AVAILABLE`;
- `NO_RELEVANT_CC_CONTEXT`.

It also proves exact numeric/time-series/chart structures are unchanged in the shared projection,
both V1 and V2 validators accept the same fingerprint, independently sufficient latest-web bytes
coexist with missing CC authority, relevant context opens DuckDB read-only, the database hash is
unchanged, and a no-context story executes zero queries.

Safety from the emitted packet:

- public write: false;
- provider/model call: false;
- browser/CDP: false;
- external network: false (deterministic accessible-source transport fixture);
- secret/session read: false;
- upstream mutation: false;
- model-created numeric substitution: false;
- `llm_numeric_authority`: false.

## Regression note

Five unrelated tests fail unchanged on the exact baseline and on this branch:

- `test_intake_delta_builds_stable_zero_llm_material_event`;
- `test_full_canonical_shadow_reaches_article_review_and_platform_package`;
- `test_published_corpus_with_confirmed_publication`.
- `test_default_builder_invoked_and_path_reaches_release_gate_with_zero_public_writes`;
- `test_builder_fail_closed_surfaces_as_no_publication_not_crash`.

They concern pre-existing material-event deduplication, stale institutional-edge/readiness shadow
fixtures, and published-corpus reconciliation. The P0-1 focused suite excludes only these exact
baseline failures; no P0-1 implementation path is excluded.
