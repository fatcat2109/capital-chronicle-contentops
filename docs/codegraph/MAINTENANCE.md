# CodeGraph maintenance

CodeGraph locates source and candidate dependencies. Control Tower locates capabilities, historical work and other repositories. Current authority documents and actual source remain decisive; neither map proves production behavior.

Run `python scripts/generate_codex_context_index.py --check` before relying on generated navigation for a changed source generation. Regenerate only when relevant inputs changed. After generator edits, run `python -m pytest -q tests/test_codex_context_index.py`, then a real generation and `--check`. Commit source changes first, regenerate outputs second: source provenance follows the latest indexed-source commit. V1_CONTEXT.md stays curated and is validated, never overwritten by generation.

The graph covers configured source/document roots and exclusions, including eligible untracked worktree files. It is not a complete filesystem inventory. Python symbols are public top-level definitions plus selected hot paths; call edges are static candidates, not exact runtime dispatch. Parse failures are exposed in coverage and prevent an unqualified CODEGRAPH_CURRENT message. Source changes during generation cause refusal rather than a mixed snapshot. Inspect source and consumers before editing.

For another Builder checkout, run the reviewed generator without editing that checkout:

```
python scripts/generate_codex_context_index.py --repo <source-checkout> --output-dir <external-snapshot-directory>
python scripts/generate_codex_context_index.py --repo <source-checkout> --output-dir <external-snapshot-directory> --check
```

The external directory must be outside the source checkout. Record the checkout path, HEAD, dirty state and generated source digest in the task receipt. The local ContentOps checkout can differ from remote master; an external WIP snapshot does not supersede remote authority. A default-branch graph does not include unmerged branch work. Use Control Tower and Git to find those branches, then inspect only the relevant ones.

No runtime, provider, browser, model or publication cycle is needed for this maintenance. A stale graph does not block work that can verify its source directly. Do not initialize an additional external .codegraph index without a concrete unmet requirement.
