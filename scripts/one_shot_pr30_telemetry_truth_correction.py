from __future__ import annotations

import subprocess
from pathlib import Path

NATIVE = Path("live_contentops/native_llm_first_daily_app_supervisor_v1.py")
TESTS = Path("tests/test_native_llm_first_daily_app_supervisor_v1.py")
EXPECTED_NATIVE = "a8f8fa405129abb58d8fc87a6eee36ef0ed096ea"
EXPECTED_TESTS = "6ecd5b999a9e22aefb575241f0474ee6dc6066e2"


def blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


if blob(NATIVE) != EXPECTED_NATIVE or blob(TESTS) != EXPECTED_TESTS:
    raise RuntimeError("PR30 telemetry correction refused because source blobs drifted")

text = NATIVE.read_text(encoding="utf-8")
old = '''        if not isinstance(result, Mapping):
            return result
        return {
            **dict(result),
            "native_llm_first_selection": {
'''
new = '''        if not isinstance(result, Mapping):
            return result
        full_intake_count = int(
            (rolling_input.get("counts") or {}).get("accepted_in_full_rolling_intake")
            or len(rolling_input.get("headlines") or [])
        )
        return {
            **dict(result),
            # Generic canonical telemetry equates prepared_state=None with a full-universe
            # critical path. This path intentionally uses prepared_state=None because frontier
            # semantic checkpoints are invalid after narrowing; the actual candidate universe is
            # the exact HIGH-admitted rolling_input below, with assignment provider calls = 0.
            "full_rolling_headline_count": full_intake_count,
            "full_universe_semantic_assignment_on_critical_path": False,
            "bounded_prepared_frontier_semantic_assignment": False,
            "native_llm_first_assignment_override_reused": True,
            "high_admitted_shortlist_count": len(binding["selected_cluster_ids"]),
            "native_llm_first_selection": {
'''
if text.count(old) != 1:
    raise RuntimeError("native telemetry insertion marker drifted")
NATIVE.write_text(text.replace(old, new, 1), encoding="utf-8")

tests = TESTS.read_text(encoding="utf-8")
old_test = '''    assert result["classification"] == "PASS_PUBLICATION_PLAN_READY"
    call = cycle_calls[0]
'''
new_test = '''    assert result["classification"] == "PASS_PUBLICATION_PLAN_READY"
    assert result["full_rolling_headline_count"] == 1093
    assert result["full_universe_semantic_assignment_on_critical_path"] is False
    assert result["native_llm_first_assignment_override_reused"] is True
    assert result["high_admitted_shortlist_count"] == 1
    call = cycle_calls[0]
'''
if tests.count(old_test) != 1:
    raise RuntimeError("telemetry regression marker drifted")
TESTS.write_text(tests.replace(old_test, new_test, 1), encoding="utf-8")
print("PR30 telemetry truth correction applied")
