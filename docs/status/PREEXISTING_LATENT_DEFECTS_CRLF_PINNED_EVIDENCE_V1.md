# Pre-Existing Latent Defect Record: CRLF-Pinned Evidence Hashes (V1)

Recorded during Wave 02 durable-operational-store work. These defects were **not introduced**
by Wave 02; they are pre-existing and are recorded here rather than repaired, because repairing
them would modify historical closeout packets outside the current task's authorized scope.

## Summary

Four committed `byte_sha256` values pin the **CRLF rendering** of their artifact rather than the
**LF bytes Git actually stores** in the blob. Because Git stores these files with LF endings, the
recorded hash can only reproduce on a Windows checkout that materializes CRLF in the working tree.
On a fresh clone, in CI, or on Linux/macOS, these hashes cannot verify.

The defect was latent while the working tree happened to contain CRLF. It becomes observable once
the checkout matches the committed LF bytes.

> [!IMPORTANT]
> These four pins are **pre-existing**. Both affected tests fail at baseline commit
> `dc228aaa0fa3ad4a478a9252f9b3cff6f8f37703` and were confirmed failing independently of any
> Wave 02 change.

## Quantified Defects

### CONTENTOPS_FAST_SHIP_TEMPORAL_AUTHORITY_AND_POINT_IN_TIME_REPLAY_INTEGRITY_V1

| Artifact | Recorded `byte_sha256` (CRLF) | Correct LF Git-blob `sha256` |
| --- | --- | --- |
| `current_readiness_parity.json` | `4ddef654ac8df591e30f5709420cf3b3e21f79138aa60540f7f8e85e4d6e320b` | `5e6b783bcfdb7e674834212f5d7c7d0a9cfd13bb32f61248131723150283cdf1` |
| `historical_replay_integrity_matrix.json` | `2da9ed1998576808a220297ce96bd6e85c3d1e4f873b7b157c337377c16eae45` | `070ca317dc8e1b09ce1900606cb184c0e21850286f8a1ab022bae98fc20b85f7` |
| `temporal_authority_records.json` | `714a90795c36c073055ffdafba0d81a0de62e0d4b1eb139a1beebc9955fd3d71` | `5b05068463f0a3c119fe93637fc303d877161e5c1650779beac7d2759d8260ff` |

Failing test (pre-existing):
`tests/test_temporal_authority_and_point_in_time_replay_integrity_v1.py::test_matrix_and_committed_temporal_artifacts_are_logically_hash_valid`

### CONTENTOPS_FAST_SHIP_DECISION_TIME_FRESHNESS_AND_CURRENT_OPERATOR_READINESS_TRUTH_V1

| Artifact | Recorded `byte_sha256` (CRLF) | Correct LF Git-blob `sha256` |
| --- | --- | --- |
| `decision_time_freshness_records.json` | `994ebd0063cc5ad8dcf3a4bf61777e2f3191c8a86b08795a50a3d5726d2c1bda` | `df400013ccf7f6e64f1da99021dcee76ae4b288c3decb0eca92259c2f522c814` |

Failing test (pre-existing):
`tests/test_decision_time_freshness_and_current_operator_readiness_v1.py::test_committed_decision_time_evidence_logical_and_byte_hashes_validate`

## Baseline Failure Evidence

Both tests were confirmed failing at baseline `dc228aaa` **before** any Wave 02 correction, by
comparing a baseline full-suite sweep against the corrected sweep:

```
FAIL@baseline  FAIL@corrected  test_matrix_and_committed_temporal_artifacts_are_logically_hash_valid
FAIL@baseline  FAIL@corrected  test_committed_decision_time_evidence_logical_and_byte_hashes_validate
```

Their state is unchanged by Wave 02: failing before, failing after.

## Repo-Wide Scope

A full scan of every declared `byte_sha256` in the repository found:

| Classification | Count |
| --- | --- |
| Declared hash matches LF blob (correct, CI-safe) | 180 |
| Declared hash matches CRLF rendering (Windows-only) | 10 |
| Unresolved / stale historical | 352 |

Of the 10 CRLF-pinned hashes:

- **4** repaired in `CONTENTOPS_FAST_SHIP_VERIFIED_HISTORICAL_PREDECESSOR_BINDING_AND_STATUS_RECONCILIATION_V1` (in scope; that packet was under active Wave 02 revision).
- **2** repaired in `CONTENTOPS_FAST_SHIP_EXECUTABLE_SNAPSHOT_REQUIREMENT_SEPARATION_V1` (in scope; this was an actual current-task regression).
- **4** recorded here, unrepaired (out of scope; pre-existing failures).

## Why Not Repaired Here

- Editing another task's committed closeout evidence requires its own authority and review.
- These are not current-task regressions, so repairing them would mix unrelated change into
  the Wave 02 commit and obscure its diff.

> [!WARNING]
> Do **not** "fix" these by adding `-text` `.gitattributes` exceptions to force CRLF on Windows,
> and do **not** normalize line endings inside a verifier before hashing. Either approach
> preserves the non-portable pinning and defeats the purpose of byte-exact evidence. The correct
> repair is to re-pin each hash to the LF Git-blob value listed above and recompute the enclosing
> manifest's `logical_hash`.

## Recommended Follow-Up

A dedicated task should re-pin the four hashes above to their correct LF values and recompute
`logical_hash` for each of the two affected `final_manifest.json` files, using each packet's own
logical-hash convention (`json.dumps(core, sort_keys=True, separators=(",", ":"))` over all keys
except `logical_hash`).
