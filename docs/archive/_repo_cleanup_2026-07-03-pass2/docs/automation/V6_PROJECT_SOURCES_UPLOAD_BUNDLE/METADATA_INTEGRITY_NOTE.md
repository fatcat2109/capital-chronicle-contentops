# Project Sources Metadata Integrity Note (V6)

## Context vs. Runtime Authority

> [!IMPORTANT]
> **Project Sources are Context Only**: Any task labels, HEAD hashes, or next pointers stored in the upload bundle are soft/advisory and provided for context only.
> **GitHub Remote is Runtime Authority**: The official GitHub remote repository commits and fetched files are the sole source of runtime truth and authority. Always run a local git audit to verify HEAD and current task state.

## Push Policies & Drift Detection

> [!CAUTION]
> **No Force Push Allowed**: Never use `git push -f` or force push under normal ContentOps operations.
> **Report Drift/Divergence**: If a normal `git push` is rejected, immediately stop execution and report the protected remote drift or divergence.
