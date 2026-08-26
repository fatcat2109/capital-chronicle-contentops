from __future__ import annotations

import json

from scripts import run_v1_llm_first_single_article_canary_v1 as canary


def test_stale_present_assignment_checkpoint_recomputes_from_current_input(
    monkeypatch, tmp_path
):
    current_input = {"counts": {"accepted": 1}, "headlines": []}
    (tmp_path / "rolling_x_assignment_v1.json").write_text(
        json.dumps({"schema_version": "old-assignment"}), encoding="utf-8"
    )
    (tmp_path / "rolling_x_story_routing_v1.json").write_text(
        json.dumps({"story_type_by_cluster": {}}), encoding="utf-8"
    )
    (tmp_path / "rolling_x_intake_v1.json").write_text(
        json.dumps({"counts": {"accepted": 999}}), encoding="utf-8"
    )

    monkeypatch.setattr(
        canary, "load_rolling_x_headline_sidecars", lambda **_kwargs: current_input
    )
    monkeypatch.setattr(
        canary,
        "load_terminal_editorial_continuity",
        lambda **_kwargs: {"published_memory": {}},
    )
    monkeypatch.setattr(
        canary,
        "semantic_resume_bindings_from_probe",
        lambda _probe: (_ for _ in ()).throw(
            ValueError("probe_semantic_resume_checkpoint_missing_or_unaccepted")
        ),
    )
    monkeypatch.setattr(canary, "newsroom_production_day_id", lambda _cutoff: "day-1")
    monkeypatch.setattr(
        canary,
        "qualify_zero_write_article",
        lambda **_kwargs: {"qualified": False, "derivative_package_intents": []},
    )

    captured = {}

    def fake_cycle(**kwargs):
        captured.update(kwargs)
        return {
            "classification": "NO_PUBLICATION",
            "public_write_performed": False,
            "unknown_write_detected": False,
        }

    monkeypatch.setattr(canary, "run_rolling_x_newsroom_cycle", fake_cycle)

    result = canary.run(output_dir=tmp_path, cutoff_utc="2026-08-26T12:00:00Z")

    assert captured["rolling_input"] is current_input
    assert captured["cutoff_utc"] == "2026-08-26T12:00:00Z"
    assert "assignment_override" not in captured
    assert "leaf_checkpoints" not in captured
    assert result["current_ingested_headline_count"] == 1
