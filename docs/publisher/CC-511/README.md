# CC-511 — reply topics and the 12 November US-session funnel

The existing reply selector now admits named drivers of the covered markets.
Their explained market links reach the existing fact collector, on-demand quote
selection and ranker. A linked-market fact remains bound to its observation and
the draft must state the driver, market and relationship. Explicit indices keep
their separate identities. Historical issued requests retain their bytes.

`topic-cases.json` binds the three requested market posts and five named
off-topic acceptance examples to the retained 12 November intake. The targeted
consumer checks pass: **86 passed in 20.37 seconds**, in one pytest process
(`topic-consumer-tests.xml`). They exercise topic selection, fact relevance,
age, quote selection and the actual ranking-input builder.

The code is being integrated by the first Publisher stream. No schedule change,
application restart, public reply or manual production tick is part of this item.
Jim remains the sender of public replies.

The full 12 November US-session funnel is not yet available at this checkpoint.
The cash session is 21:30 GMT+7 on 12 November through 04:00 GMT+7 on 13 November
(14:30–21:00 UTC in the records). Premarket run records remain available; their
counts cannot establish a complete session. The report will distinguish observed
stages, first causes and unavailable timings rather than infer a sent draft.

`run-context.json` records the operating base, configured launch model and effort
(`gpt-6.1-sol / max`, `CONFIGURED_NOT_OBSERVED`) and original unrelated file hashes.
