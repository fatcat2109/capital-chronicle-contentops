from __future__ import annotations

import json

from live_contentops.retention_native_motion_author_v2 import (
    SCHEMA_VERSION,
    batch_validator,
    compile_director_source,
)


def _row(shot_id: str) -> dict[str, str]:
    return {
        "shot_id": shot_id,
        "component_name": f"Shot_{shot_id}",
        "component_source": (
            f"const Shot_{shot_id}: React.FC<AuthoredShotProps> = "
            "({frame,fps,width,height,progress}) => { const x = frame/fps; "
            "return <AbsoluteFill style={{width,height,opacity:progress}}>{x}</AbsoluteFill>; };"
        ),
    }


def test_motion_batch_validator_accepts_exact_safe_source() -> None:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "shots": [_row("s01"), _row("s02")],
        "public_write": False,
        "publication_authority": False,
        "factual_authority": False,
    }
    assert batch_validator(("s01", "s02"))(json.dumps(payload))[0] is True


def test_motion_batch_validator_rejects_network_and_partial_coverage() -> None:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "shots": [_row("s01")],
        "public_write": False,
        "publication_authority": False,
        "factual_authority": False,
    }
    payload["shots"][0]["component_source"] += " fetch('https://bad.example')"
    assert batch_validator(("s01", "s02"))(json.dumps(payload))[0] is False
    assert batch_validator(("s01",))(json.dumps(payload))[3] == "unsafe_or_invalid_component"


def test_blueprint_compiler_preserves_authored_duration_and_governed_ids() -> None:
    blueprint = {
        "viewer_promise": "promise",
        "variants": {
            variant: {
                "hook": "hook",
                "payoff_seconds": payoff,
                "shots": [
                    {
                        "id": shot_id, "t0": 0, "t1": duration,
                        "narration_excerpt": "line", "purpose": "why",
                        "visual": "Hormuz route map and inventory mechanism",
                        "motion": "route flows", "transition": "hard cut",
                        "asset_ids": ["primary"],
                        "claim_ids": ["eia:global_output_near_pre_conflict_by_year_end"],
                        "evidence_ids": ["eia-release-press590"],
                    }
                ],
            }
            for variant, shot_id, duration, payoff in (
                ("short_9x16", "s01", 45, 10),
                ("midform_16x9", "m01", 90, 45),
            )
        },
    }
    base = {
        "director_identity": {}, "revision_history": [],
        "engagement_brief": {"core_promise": "old", "open_loops": [{"loop_id": "loop"}]},
        "variants": [
            {"variant_id": variant, "beats": [], "hook_copy": "", "min_duration_seconds": 1, "max_duration_seconds": 2}
            for variant in ("short_9x16", "midform_16x9")
        ],
        "audio_plan": {"sfx_cues": []},
    }
    compiled = compile_director_source(blueprint, base, blueprint_hash="a" * 64)
    short, mid = compiled["variants"]
    assert (short["min_duration_seconds"], short["max_duration_seconds"]) == (45.0, 60.0)
    assert (mid["min_duration_seconds"], mid["max_duration_seconds"]) == (90.0, 150.0)
    assert short["beats"][0]["target_duration_seconds"] == 45.0
    assert short["beats"][0]["claim_ids"] == ["eia:pre_conflict_year_end"]
    assert "wti-current-volatility-chart" in short["beats"][0]["asset_ids"]
    assert compiled["director_identity"]["facts_may_be_added"] is False
