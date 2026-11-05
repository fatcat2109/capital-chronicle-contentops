The resumed coordinator reached an older article's reader-presentation acceptance during its existing recovery pass. The source-recovery artifact namespace introduced in this run computed a new key for that pre-existing written article, so the accepted final artifact lookup returned None. The exact stack is retained in publication-resume-trace.txt.

The key selector now retains a pre-existing final artifact once writing, an article, qualification or a public write exists. A zero-writer source failure still selects a separate recovered final, leaving the original failure immutable. Review hashes, source/rights bindings and exactly-once checks are unchanged.

Validation: python -m pytest -q tests/test_native_artifact_key_recovery_v1.py --tb=short: 5 passed in 3.73s. One process, targeted file only, no parallel workers.
