# CC-177: integrate the retained Publisher deliveries

Base: operating branch `codex/contentops-local-publisher-20261030` at
`a4d60fe0d10de97a06603a8de6b6c3e88c79edcd`.
Jim decision 39 permits ContentOps operating-root fast-forward and a rollback tag.
The default branch, Main live root, schedules and public objects are unchanged.

Launch readback: `--model gpt-6.1-sol`,
`-c model_reasoning_effort="high"`, `CONFIGURED_NOT_OBSERVED`.
This engineering run invokes no editorial models.

CC-043: ported only 1cc1f908/beba137c/d88a36a3 from the reviewed CC-042 lineage.
Conflicts retain the current frozen-request guidance, latency-aware media checks,
publication-feed validation and optional-field handling, while adding desk citation
validation and the fixture-publication refusal. The initial source/schema/rights
selection passed 117 tests (`cc043-tests.xml`). Retained previews remain historical;
this run does not create or reapprove an article.

CC-044: ported 5167a6cc/41e77bfa (ten-channel metrics and failed-read accounting).
CC-047: ported f527ce33 (rights-bound source routes, coverage, new-binding cap 20).
Issued six/ten-request bindings keep their exact original limits.

CC-015's renderer is already in the operating root. It remains a local structured
renderer, not a replacement for the approved native MAX editorial owner.
CC-135's append-only feed producer is already in the operating root; the external
Main/site consumer is distinct from that producer.

Final validation, operating-root identity and outstanding consumer dependencies are
recorded below when the integration checks complete.
