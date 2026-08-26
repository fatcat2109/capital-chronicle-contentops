"""Apply the owner-approved V1 simple Gemini reset on clean v6 staging."""
from __future__ import annotations

import ast
import os
from pathlib import Path

RESET_BRANCH = "agent/web-v1-simple-gemini-runtime-reset-v6"
BASE_PATCH = Path(".github/reset/patch_base.py")


def copy_template(src: str, dst: str) -> None:
    source = Path(src).read_text(encoding="utf-8")
    target = Path(dst)
    if target.exists():
        raise SystemExit(f"new_product_path_already_exists:{dst}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source, encoding="utf-8")


base_text = BASE_PATCH.read_text(encoding="utf-8")
namespace: dict[str, object] = {
    "__name__": "v1_simple_gemini_reset_patch_library",
    "__file__": str(BASE_PATCH),
}
exec(compile(base_text, str(BASE_PATCH), "exec"), namespace)
namespace["RESET_BRANCH"] = RESET_BRANCH
expected_blobs = namespace["EXPECTED_BLOBS"]
assert isinstance(expected_blobs, dict)
expected_blobs[".github/workflows/ci-fast.yml"] = "b1a26817719b491e087cdd1b43d587a459b73bce"

run = namespace["run"]
assert callable(run)
branch = os.environ.get("GITHUB_REF_NAME") or ""
expected_sha = os.environ.get("GITHUB_SHA") or ""
if branch != RESET_BRANCH:
    raise SystemExit(f"wrong_github_ref:{branch}")
actual_sha = run("git", "rev-parse", "HEAD")
if not expected_sha or actual_sha != expected_sha:
    raise SystemExit(f"checkout_sha_mismatch:{actual_sha}:{expected_sha}")
for path, expected in expected_blobs.items():
    actual = run("git", "hash-object", path)
    if actual != expected:
        raise SystemExit(f"blob_drift:{path}:{actual}:{expected}")

copy_template(
    ".github/reset/v1_simple_gemini_newsroom_v1.py.src",
    "live_contentops/v1_simple_gemini_newsroom_v1.py",
)
copy_template(
    ".github/reset/test_v1_simple_gemini_newsroom_v1.py.src",
    "tests/test_v1_simple_gemini_newsroom_v1.py",
)
copy_template(
    ".github/reset/run_v1_simple_gemini_newsroom.py.src",
    "scripts/run_v1_simple_gemini_newsroom.py",
)

for name in (
    "patch_simple_runtime",
    "patch_qualified_record_helper",
    "patch_orchestrator",
    "patch_router_authority",
    "patch_codex_noop",
    "patch_authority_docs",
):
    fn = namespace[name]
    assert callable(fn)
    fn()

# Reuse the audited final authority assertion block from the patch library but patch the
# untouched post-merge master ci-fast workflow directly; there are no temporary CI special cases.
tree = ast.parse(base_text)
authority_step: str | None = None
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == "patch_final_ci":
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                if any(isinstance(target, ast.Name) and target.id == "authority_step" for target in stmt.targets):
                    if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                        authority_step = stmt.value.value
                        break
if not authority_step:
    raise SystemExit("final_authority_assertion_block_not_found")

replace_once = namespace["replace_once"]
replace_between = namespace["replace_between"]
assert callable(replace_once) and callable(replace_between)
ci_path = ".github/workflows/ci-fast.yml"
authority_marker = "      - name: Validate current hybrid execution and V1 owner authority\n"
reset_tests = (
    "      - name: Run V1 simple Gemini reset regressions\n"
    "        run: |\n"
    "          python -m pytest -q tests/test_v1_simple_gemini_newsroom_v1.py\n"
    "          python -m pytest -q tests/test_newsroom_production_day_v1.py tests/test_nine_router_ordered_model_router_v2.py\n\n"
)
replace_once(ci_path, authority_marker, reset_tests + authority_marker)
replace_between(
    ci_path,
    authority_marker,
    "      - name: Check CodeGraph freshness and prepare repair artifact\n",
    authority_step,
)
