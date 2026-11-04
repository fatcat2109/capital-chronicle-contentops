# CC-179 exact-object recovery repair

A stale editorial review blocked begin/submit of an already-created readback. The native owner now permits only a hash-bound readback belonging to the same operation, destination and existing dispatch. Fresh sends still require the current reviewed packet. Wrong operation, destination and content remain rejected.

The existing Neo adapter now accepts exact Telegram and Threads readbacks. Their API writers are unchanged. Telegram falls back to that native readback only when its ordinary provider readback cannot verify or establish absence; Telegram cannot fetch an old message through the Bot API. A public Threads amendment previously reached the adapter and failed because Threads was absent from its supported identities.

Validation: 18 native-publication tests passed; 70 exact-social and native-executor tests passed. The earlier failed five-test attempt is superseded by the complete 18-test run after correcting dispatch lookup and the disposable fixture. Launch is gpt-6.1-sol/max CONFIGURED_NOT_OBSERVED. Current live base subsequently advanced by unrelated CC-258 ingestion changes; preserve them on integration.

A real FOMC continuation exposed a second cause: replacement Instagram messages have a new plan hash, so recovery looked for a nonexistent second canonical. The installed coordinator now resolves the immutable replacement record back to its original removed dispatch and confirmed canonical. Wrong article, missing record and an ambiguous parent canonical still block. 36 focused social/replacement/coordinator cases passed. The real CPI Telegram, Threads and replacement Instagram readbacks are now RECONCILED_CONFIRMED in the production store.
