"""Execute the blob-guarded reset patch for the clean v3 staging branch."""
from __future__ import annotations

from pathlib import Path

SOURCE = Path("scripts/_one_shot_apply_v1_simple_gemini_reset.py")
text = SOURCE.read_text(encoding="utf-8")
old_branch = "agent/web-v1-simple-gemini-runtime-reset"
new_branch = "agent/web-v1-simple-gemini-runtime-reset-v3"
old_ci_sha = "4e86e52fa5ce48bc3b5e31bdb863181b8d1ca4fd"
new_ci_sha = "04f498760d42e73e531fe0d5b87bde48872eadce"
if text.count(old_branch) < 3:
    raise SystemExit("expected_reset_branch_bindings_missing")
if text.count(old_ci_sha) != 1:
    raise SystemExit("expected_ci_blob_binding_missing")
text = text.replace(old_branch, new_branch).replace(old_ci_sha, new_ci_sha)
namespace = {"__name__": "__main__", "__file__": str(SOURCE)}
exec(compile(text, str(SOURCE), "exec"), namespace)

# The setup-only apply job lives in the trusted ci-fast workflow so it can start on the
# feature branch. Remove that job from the final product tree after the patch has restored
# normal CI concurrency/freshness rules. The running job is unaffected by editing its file.
ci_path = Path(".github/workflows/ci-fast.yml")
ci_text = ci_path.read_text(encoding="utf-8")
marker = "\n  apply-v1-simple-gemini-reset:\n"
if ci_text.count(marker) != 1:
    raise SystemExit("temporary_apply_job_marker_invalid")
ci_path.write_text(ci_text.split(marker, 1)[0] + "\n", encoding="utf-8")
