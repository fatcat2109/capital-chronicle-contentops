"""Apply the owner-approved V1 simple Gemini reset on the single clean v7 branch."""
from __future__ import annotations

import os
from pathlib import Path

RESET_BRANCH = "agent/web-v1-simple-gemini-runtime-reset-v7"
BASE_PATCH = Path(".github/reset/patch_base.py")
PRIVATE_IMPL = "live_contentops/_eight_platform_substack_first_pipeline_impl_v1.py"


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
expected_blobs[".github/workflows/ci-fast.yml"] = "0a6dc67fd6d1b7e2b4702ea0d8d038de4a66e055"
expected_blobs["live_contentops/eight_platform_substack_first_pipeline_v1.py"] = "df7a24eb70bd9e3becc2560105f9a0910b7dabc1"
expected_blobs["tests/test_canonical_production_entrypoint_and_legacy_quarantine_v1.py"] = "29f9ba9ba6ac23510126934dc6b91c8927dc81e2"
expected_blobs[PRIVATE_IMPL] = "68e65c0249701d7a3185586a82b5cff6d81a491d"

run = namespace["run"]
read = namespace["read"]
write = namespace["write"]
replace_once = namespace["replace_once"]
append_before = namespace["append_before"]
assert callable(run) and callable(read) and callable(write)
assert callable(replace_once) and callable(append_before)

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

# Donor compatibility tests import these runtime dependencies. Install them only in the ephemeral
# apply worker; the permanent ci-fast dependency line is corrected below for future exact-head CI.
run(
    "python",
    "-m",
    "pip",
    "install",
    "--disable-pip-version-check",
    "python-dotenv",
    "jsonschema",
)

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

# The base patch originally used an orchestrator-local special case. That violated the repository's
# canonical-entrypoint invariant. Restore normal dispatcher ownership and add a lazy private-map
# adapter instead, so public CANONICAL_OPERATIONS and the private exact map remain identical.
orchestrator = "live_contentops/production_orchestrator_v1.py"
special_method = '''    def _dispatch_operation(self, operation: str, **kwargs: Any) -> Any:\n        if operation == "run_v1_simple_gemini_newsroom":\n            module = import_module("live_contentops.v1_simple_gemini_newsroom_v1")\n            runner = getattr(module, "run_v1_simple_gemini_newsroom")\n            if not callable(runner):\n                raise TypeError("v1_simple_gemini_newsroom_runner_not_callable")\n            return runner(**kwargs)\n        return self._resolve_dispatcher()(operation, **kwargs)\n\n'''
replace_once(orchestrator, special_method, "")
replace_once(
    orchestrator,
    '        if active_store is None:\n            return self._dispatch_operation(operation, **kwargs)\n',
    '        if active_store is None:\n            return self._resolve_dispatcher()(operation, **kwargs)\n',
)
replace_once(
    orchestrator,
    '            result = self._dispatch_operation(operation, **kwargs)\n',
    '            result = self._resolve_dispatcher()(operation, **kwargs)\n',
)
replace_once(
    orchestrator,
    '"run_v1_simple_gemini_newsroom": _operation_contract(restart_mode=RESTART_SAFE, capability="MODEL_ASSISTED_ZERO_WRITE"),',
    '"run_v1_simple_gemini_newsroom": _operation_contract(restart_mode=RESTART_SAFE, capability="LOCAL_PREPARATION"),',
)

private_adapter = '''\n\ndef _run_v1_simple_gemini_newsroom_impl(**kwargs: Any) -> Any:\n    """Lazy private adapter for the current V1 Gemini-primary zero-write operation."""\n    from live_contentops.v1_simple_gemini_newsroom_v1 import run_v1_simple_gemini_newsroom\n\n    return run_v1_simple_gemini_newsroom(**kwargs)\n'''
append_before(
    PRIVATE_IMPL,
    "\n\n_CANONICAL_OPERATIONS: Mapping[str, Callable[..., Any]] = {",
    private_adapter,
)
replace_once(
    PRIVATE_IMPL,
    '    "run_rolling_x_newsroom_cycle": _run_rolling_x_newsroom_cycle,\n',
    '    "run_rolling_x_newsroom_cycle": _run_rolling_x_newsroom_cycle,\n    "run_v1_simple_gemini_newsroom": _run_v1_simple_gemini_newsroom_impl,\n',
)
# Stage this exact path explicitly because the setup workflow's final git-add list predates this
# canonical-map correction. It remains staged through the later explicit final commit step.
run("git", "add", "--", PRIVATE_IMPL)

# Keep the new operation inside the canonical public boundary. The public facade remains import-safe
# and zero-write; it delegates exactly once to ContentOpsProductionOrchestrator.
facade = '''\n\ndef run_v1_simple_gemini_newsroom(\n    *,\n    output_dir: Path,\n    cutoff_utc: str,\n    rolling_input: Mapping[str, Any] | None = None,\n    published_memory: Sequence[Any] = (),\n    capital_chronicle_context: Mapping[str, Any] | None = None,\n    llm_invoke: Any = None,\n    evidence_loader: Any = None,\n    run_id: str | None = None,\n) -> dict[str, Any]:\n    """Run the current V1 Gemini-primary zero-public-write newsroom operation."""\n    return _execute(\n        "run_v1_simple_gemini_newsroom",\n        output_dir=output_dir,\n        cutoff_utc=cutoff_utc,\n        rolling_input=rolling_input,\n        published_memory=published_memory,\n        capital_chronicle_context=capital_chronicle_context,\n        llm_invoke=llm_invoke,\n        evidence_loader=evidence_loader,\n        run_id=run_id,\n    )\n'''
append_before(
    "live_contentops/eight_platform_substack_first_pipeline_v1.py",
    "\ndef reconcile_public_substack_for_derivative_resume(",
    facade,
)
replace_once(
    "tests/test_canonical_production_entrypoint_and_legacy_quarantine_v1.py",
    '        "run_rolling_x_newsroom_cycle": lambda: public_module.run_rolling_x_newsroom_cycle(run_id="r", output_dir=tmp_path, cutoff_utc="2026-08-08T00:00:00Z", publication_enabled=False),\n',
    '        "run_rolling_x_newsroom_cycle": lambda: public_module.run_rolling_x_newsroom_cycle(run_id="r", output_dir=tmp_path, cutoff_utc="2026-08-08T00:00:00Z", publication_enabled=False),\n        "run_v1_simple_gemini_newsroom": lambda: public_module.run_v1_simple_gemini_newsroom(output_dir=tmp_path, cutoff_utc="2026-08-27T00:00:00Z", rolling_input={"headlines": []}),\n',
)

# Convert temporary setup CI into the permanent reset validation workflow. Preserve V2/hybrid
# assertions; replace only stale V1/Desktop routing claims. Permanent CI must carry the two donor
# test dependencies that the guarded apply run proved are required.
ci_path = ".github/workflows/ci-fast.yml"
ci_text = read(ci_path)
old_install = "run: python -m pip install --disable-pip-version-check pytest pillow"
if ci_text.count(old_install) != 2:
    raise SystemExit(f"ci_install_line_count:{ci_text.count(old_install)}")
ci_text = ci_text.replace(
    old_install,
    "run: python -m pip install --disable-pip-version-check pytest pillow python-dotenv jsonschema",
)
write(ci_path, ci_text)
replace_once(
    ci_path,
    "  group: ci-fast-${{ github.ref }}-${{ github.sha }}\n  cancel-in-progress: false\n",
    "  group: ci-fast-${{ github.ref }}\n  cancel-in-progress: true\n",
)
authority_marker = "      - name: Validate current hybrid execution and V1 owner authority\n"
reset_tests = (
    "      - name: Run V1 simple Gemini reset regressions\n"
    "        shell: bash\n"
    "        run: |\n"
    "          python -m pytest -q tests/test_v1_simple_gemini_newsroom_v1.py\n"
    "          python -m pytest -q tests/test_newsroom_production_day_v1.py\n"
    "          python -m pytest -q tests/test_canonical_production_entrypoint_and_legacy_quarantine_v1.py\n"
    "          python -m pytest -q tests/test_nine_router_ordered_model_router_v2.py\n\n"
)
replace_once(ci_path, authority_marker, reset_tests + authority_marker)
ci_text = read(ci_path)
old_block = '''          assert 'pr #19 provider-resilient quota-efficient batch/tail discovery is accepted and reusable' in v1_pointer.lower()\n          assert 'zero-write routine starvation / ownership correction and prospective calendar proof' in v1_pointer.lower()\n          assert 'routine host prompts now match the repo-derived fast-ship hash' in v1_pointer.lower()\n          assert 'pass_fda_g_scheduled_window_observed' in v1_pointer.lower()\n          assert 'fail_routine_output_starvation_policy' in v1_pointer.lower()\n          assert 'current_host_runtime_proof_required' in v1_pointer.lower()\n          assert 'pass_native_calendar_trigger_observed' not in v1_pointer.lower()\n          assert 'all four are held paused' in v1_pointer.lower()\n          assert 'Desktop standalone fresh-run Automations are the primary routine V1' in authority_map\n          assert 'App Server/SDK provider remains the currently proven' in authority_map\n          assert 'no fifth' in authority_map.lower()\n'''
new_block = '''          reset = Path('docs/automation/CONTENTOPS_V1_SIMPLE_GEMINI_RUNTIME_RESET_V1.md').read_text(encoding='utf-8')\n          desktop_doc = Path('docs/automation/CODEX_DESKTOP_V1_NEWSROOM_OPERATOR.md').read_text(encoding='utf-8')\n          desktop_code = Path('live_contentops/codex_desktop_newsroom_operator_v1.py').read_text(encoding='utf-8')\n          simple = Path('live_contentops/v1_simple_gemini_newsroom_v1.py').read_text(encoding='utf-8').lower()\n          from live_contentops.production_orchestrator_v1 import CANONICAL_OPERATIONS\n          from live_contentops.nine_router_llm_seam_v2 import integration_manifest\n          from live_contentops.nine_router_ordered_model_router_v2 import authority_packet\n          assert 'Status: `CURRENT_V1_EXECUTION_AUTHORITY`' in reset\n          assert 'run_v1_simple_gemini_newsroom' in CANONICAL_OPERATIONS\n          assert 'maximum 6 requests' in reset\n          assert 'Codex runtime model calls required: `0`' in reset\n          assert 'SUPERSEDED_DO_NOT_REUSE' in reset and 'PR #30' in reset and 'PR #31' in reset\n          assert 'SIMPLE_GEMINI_RUNTIME' in agents\n          assert 'simple Gemini' in v1_pointer\n          assert 'CURRENT_HOST_RUNTIME_PROOF_REQUIRED' in v1_pointer\n          assert 'SUPERSEDED_FOR_ROUTINE_V1_PRODUCTION' in desktop_doc\n          assert 'SUPERSEDED_CODEX_NEWSROOM_AUTOMATION_NOOP' in desktop_code\n          assert 'official_codex' not in simple and 'codex_desktop' not in simple\n          manifest = integration_manifest()\n          packet = authority_packet()\n          assert manifest['v1_simple_gemini_runtime_primary'] is True\n          assert manifest['codex_runtime_model_calls_required'] is False\n          assert packet['publication_qualified_article_uses_9router_gemini'] is True\n          assert packet['publication_qualified_article_uses_native_codex_desktop_xhigh'] is False\n          assert packet['codex_runtime_model_calls_required'] is False\n          assert 'no fifth' in authority_map.lower()\n'''
if ci_text.count(old_block) != 1:
    raise SystemExit(f"ci_stale_v1_assertion_block_count:{ci_text.count(old_block)}")
ci_text = ci_text.replace(old_block, new_block, 1)
apply_marker = "\n  apply-v1-simple-gemini-reset:\n"
idx = ci_text.find(apply_marker)
if idx < 0:
    raise SystemExit("temporary_apply_job_marker_missing")
ci_text = ci_text[:idx].rstrip() + "\n"
write(ci_path, ci_text)
