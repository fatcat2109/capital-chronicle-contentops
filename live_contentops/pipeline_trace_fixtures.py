"""Deterministic fixture scenarios for the end-to-end pipeline trace (v0).

Local-only, fixture-only. No real Capital Chronicle alpha artifacts. Every
scenario output is NOT PUBLIC POSTABLE. No network/provider/LLM/search/platform.
"""

import json
import os

from . import pipeline_trace as pt

_FIXTURE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "tests", "fixtures", "editorial",
    "real_artifact_pipeline_trace_input.json")


def load_scenarios() -> list:
    with open(_FIXTURE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["scenarios"]


def build_all_traces() -> list:
    """Build a deterministic trace record per fixture scenario."""
    return [pt.build_pipeline_trace(s["input"]) for s in load_scenarios()]


def build_scenario_matrix() -> list:
    """Compact deterministic scenario matrix (label/route/allowed/expected)."""
    out = []
    for s in load_scenarios():
        trace = pt.build_pipeline_trace(s["input"])
        out.append({
            "label": s["label"],
            "expected_outcome": s.get("expected_outcome"),
            "bridge_route": trace["bridge_route"],
            "intake_gate_status": trace["intake_gate_status"],
            "packet_input_allowed": trace["packet_input_allowed"],
            "registry_status": trace["registry_status"],
            "dashboard_handoff_status": trace["dashboard_handoff_status"],
            "blocker_count": len(trace["blockers"]),
            "not_public_postable_reason": trace["not_public_postable_reason"],
        })
    return out
