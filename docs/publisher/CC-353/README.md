# CC-353: explain each new plan

The existing Main-export reader, plan-status outbox and sole publication coordinator now carry the supplied base case, main alternative, probabilities, confirmations, invalidation explanation and CC-355 reason fields into new-plan posts. WAITING explains the plan; TRIGGERED explains it when the plan has no confirmed announcement. Missing probabilities are never complemented. An absent scenario retains the existing post and increments `SCENARIO_ANALYSIS_MISSING` in the existing run result.

Telegram, Discord and Substack Notes receive the full public rationale. Oversize Telegram captions and Discord messages use bounded continuation dispatches in the same durable store, with stable part identities and the existing coordinator's readback-before-retry behavior. Threads receives a source excerpt within 500 characters. X receives the same short explanation through its existing ordered-post format. The conditional call, public notices, ET validity and TradingView credit remain. Notes uses the existing Neo executor; the minute task registers X and Notes requests after the API copies and never waits for browser work.

The signed-in Notes profile was read back on 9 November at approximately 16:42 GMT+7: `https://substack.com/@deancapitalchronicle`, with the profile's publication link pointing to `capitalchronicle.substack.com`. The new Notes surface pins that exact handle and exact `/note/c-...` public-object URL. The article destination and its canonical URL rules are unchanged.

Only named public reason fields enter copy. Target and R:R clauses, position sizes, account and execution details, P&L and prediction-market numbers are omitted under decisions 40 and 84. A projected destination price is removed; its preceding mechanism remains usable. Sentence fragments containing an undated UTC clock are omitted because their event date cannot be faithfully converted to ET. No source fact, probability or alternative is invented.

The existing `CapitalChronicle-PlanStatusPosts-V1` task runs `pythonw.exe -B scripts\plan_status_posts.py --publish` in `A:\Capital Chronicle\ContentOps`; integration therefore updates its next invocation without a schedule change or process restart. Browser continuations use the same script's `--pending-x`, `--pending-notes`, `--x-begin` and `--x-submit` commands. `--notes-start` can resume a specific Note through that same route.

The branch starts from the operating root's `31fd90987006707fe9259e96537171a62d488e03`, preserving its already-integrated changes; remote master predates that operating lineage. The two dirty telemetry/dispatch ledgers and unrelated retained CC-107 files are outside this item and its commits.

Launch arguments read from the active exec process configured `gpt-6.1-sol` / `high`, labelled **CONFIGURED_NOT_OBSERVED**: no supported runtime model telemetry was supplied. This implementation makes no editorial model call.

Validation and the final operating-root/tag identities are in this folder's evidence. The 9 November 16:15 GMT+7 plan announcements were already confirmed before this change; their frozen copy and identities are preserved. Live public-readback acceptance requires the next eligible new-plan transition, rather than a duplicate announcement of those confirmed rows.
