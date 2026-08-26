"""Execute the blob-guarded reset patch for the clean v2 staging branch.

The original patch script is immutable setup material. This wrapper changes only the exact
branch identity and the temporary ci-fast blob identity in memory before executing it; all
product-file blob guards remain the fresh GitHub-audited values.
"""
from __future__ import annotations

from pathlib import Path

SOURCE = Path("scripts/_one_shot_apply_v1_simple_gemini_reset.py")
text = SOURCE.read_text(encoding="utf-8")
old_branch = "agent/web-v1-simple-gemini-runtime-reset"
new_branch = "agent/web-v1-simple-gemini-runtime-reset-v2"
old_ci_sha = "4e86e52fa5ce48bc3b5e31bdb863181b8d1ca4fd"
new_ci_sha = "887bd728c2f73b902c33b91a6866a9c24d30d25d"
if text.count(old_branch) < 3:
    raise SystemExit("expected_reset_branch_bindings_missing")
if text.count(old_ci_sha) != 1:
    raise SystemExit("expected_ci_blob_binding_missing")
text = text.replace(old_branch, new_branch).replace(old_ci_sha, new_ci_sha)
namespace = {"__name__": "__main__", "__file__": str(SOURCE)}
exec(compile(text, str(SOURCE), "exec"), namespace)
