# V1 official Codex article-contract reliability and canary closeout

Status: `PASS_OFFICIAL_CODEX_DIRECT_PROVIDER_CURRENT_HEAD_CANARY_VERTICAL_PROOF`

## Outcome

The official ChatGPT-authenticated Codex App Server/SDK provider produced and locally repaired the
same governed Italy article on one fresh ephemeral `gpt-5.6-sol / XHIGH` thread. The final article,
eight derivative packages, and exact nine-surface JIT plan passed with zero public writes and
`UNKNOWN_WRITE=0`.

Exact article identity:

- title: `State Department Approves Possible APKWS II Sale to Italy`;
- mode: `DATA_OR_DOCUMENT_LENS`;
- evidence: `official-primary-ffb8e742e0932254c29d`;
- canonical URL contract:
  `https://capitalchronicle.substack.com/p/state-department-approves-possible-apkws-ii-sale-italy`.

This proof stops for Jim/ChatGPT audit. It authorizes no public write, second article, Desktop
Automation enablement, production-grade throughput claim, or `V1_FINAL_PRODUCT_ACCEPTED` status.

## Prior failure frozen accurately

The predecessor canary remains valid historical evidence of:

`MODEL_TURN_COMPLETED -> LOCAL_VALIDATION_FAILED`

Its six exact deterministic blockers were:

1. `epistemic_claim_not_present_in_public_copy`;
2. `epistemic_claim_layer_invalid`;
3. `structured_data_description_mismatch`;
4. `structured_data_dates_missing_or_unbound`;
5. `structured_data_author_identity_mismatch`;
6. `structured_data_publisher_identity_mismatch`.

The root cause was the provider transport contract: it required only an outer
`{"article_json": string}` envelope. That allowed the model to return a syntactically valid string
whose inner article had not been constrained by the canonical article shape. Provider transport
succeeded; subordinate local product validation correctly rejected the article.

## Reliability correction

The transport now receives the real 31-property canonical article projection rather than the
string wrapper. Every object is recursively closed, every declared property is required, and
semantically optional fields are nullable at transport. After decoding, only those allowed transport
null placeholders are removed. The unchanged canonical article contract and deterministic product
validators remain final authority.

Deterministic representation normalization is limited to exact copies/bindings:

- canonical headline from title;
- dek from subtitle;
- search title from SEO title;
- social hook from social lede;
- fixed Capital Chronicle author/publisher identity;
- structured-data headline/description from visible copy;
- an explicit coordinator timestamp-binding state before structured-data emission.

It invents no semantic claim, fact, date, causality, or market implication. Provider developer
instructions are passed through `thread_start` and hashed into provider input identity.

The initial secret-free TurnResult receipt is persisted before product validation. A transport-valid
article that fails deterministic validation may receive exactly one repair on the same ephemeral
thread, using sanitized concrete blockers and unchanged governed evidence/input hashes. Blind retry,
replacement threads, alternate model families, and validator weakening remain forbidden.

## Live attempts

### Attempt 1

The fresh direct-schema call passed transport and the institutional/source contract but failed the
minimum-reader-substance gate because hostname periods distorted sentence counting. Its same-thread
repair added unsupported prose and then failed source coverage. That concrete result led only to a
deterministic source-display-label correction and smaller hash/blocker-only revision feedback.

- initial duration/usage: `179746 ms`, `31716` total tokens;
- initial TurnResult hash:
  `04e223d211e1836129047fe55819570ce5dd2f96a16eed6d67209542c5fff5a1`;
- revision duration/usage: `182895 ms`, `86794` total tokens;
- revision TurnResult hash:
  `af43b22f7a685d7b01264db33cc4c3b8bbc375cd75a43edd326ec7a5522c0a53`;
- terminal blocker: `grounded_paragraph_source_coverage_incomplete:2`;
- public writes / unknown writes: `0 / 0`.

### Attempt 2

The initial result had one exact blocker,
`epistemic_claim_not_present_in_public_copy`. One bounded same-thread repair resolved it. The final
article passed transport, canonical product validation, institutional edge, source coverage,
zero-media separation, eight-derivative compilation, and nine-surface JIT readiness.

- initial duration/usage: `164193 ms`, `30734` total tokens;
- initial TurnResult hash:
  `0cb16b22a4fd9be566e62e05806c18f956597e730444e44fe805e47cbe7939d9`;
- revision duration/usage: `28300 ms`, `70011` total tokens;
- revision TurnResult hash:
  `59b584481b38e7950f4cfbfee5baf51ddc48ecccc1390d58f2667d494089d204`;
- final deterministic blockers: none;
- public writes / provider publication writes / unknown writes: `0 / 0 / 0`.

An offline resume corrected a proof-harness-only nine-surface count assertion. It reused the persisted
successful provider receipt and already captured JIT preflight, making no new model call and no new
readiness probe.

## Authority consequence

The proven heavy-editorial path is now:

`FDA-G / existing V1 runtime -> official ChatGPT-authenticated Codex provider`

Desktop Scheduled Automations are `SUPERSEDED_DO_NOT_REUSE` for V1 runtime invocation. Their
historical evidence is preserved. The four Bangkok production-day windows remain schedule policy;
no fifth window and no public-write authority are introduced.

See `canary_closeout_receipt_v1.json` for exact hashes and `validation_receipt_v1.json` for test and
CodeGraph evidence.
