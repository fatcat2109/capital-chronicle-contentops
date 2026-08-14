from __future__ import annotations

import copy
from pathlib import Path

import pytest

from live_contentops.lane_b_hybrid_bakeoff_v1 import (
    ARTICLE_HASH,
    EVIDENCE_HASH,
    MODE_MAP,
    BenchmarkIdentity,
    HybridLedger,
    build_mode_input,
    logical_hash,
    validate_creative_packet,
    zero_public_write_manifest,
)


def immutable() -> dict:
    return {
        "article_hash": ARTICLE_HASH,
        "evidence_hash": EVIDENCE_HASH,
        "asset_manifest": {"candidates": [
            {"asset_id": f"a{i}", "rights_status": "PUBLIC_DOMAIN"} for i in range(8)
        ]},
        "public_write": False,
    }


def creative(expected: dict) -> dict:
    durations = [6, 7, 7, 7, 7, 7, 7, 6]
    primitives = ["MAP_TO_VESSEL", "PHYSICAL_CHAIN", "DOCUMENT_EVIDENCE",
                  "NATIVE_FORECAST_CHART", "TRANSMISSION", "CONSEQUENCE",
                  "CONFIRM_CHALLENGE", "CHECKPOINT_TIMELINE"]
    scenes = [{"scene_id": f"s{i}", "duration_seconds": duration,
               "primitive": primitives[i], "asset_id": f"a{i}", "title": f"Title {i}",
               "body": "Concrete evidence-led explanation.", "source": "Governed source",
               "narration": "A governed sentence explains this visual mechanism clearly.",
               "caption_visible": False} for i, duration in enumerate(durations)]
    return {"owner_label": expected["owner_label"], "run_id": expected["run_id"],
            "input_hash": expected["input_hash"], "public_write": False,
            "layers": {"truth": ["source facts"], "analysis": ["mechanism"], "engagement": ["hook"]},
            "analytical_map": {"core_question": "What changed?", "physical_mechanism": "Transit to inventory",
                               "second_order_channel": "Import costs", "confirm": "Inventories build",
                               "challenge": "Disruption returns", "next_checkpoint": "Next EIA release"},
            "narration": " ".join(["governed"] * 110), "scenes": scenes}


def test_mode_mapping_is_exact_and_selectable() -> None:
    assert MODE_MAP == {
        "HIGH": {"model": "gpt-5.6-sol", "reasoning_effort": "high"},
        "XHIGH": {"model": "gpt-5.6-sol", "reasoning_effort": "xhigh"},
        "ULTRA": {"model": "gpt-5.6-sol", "reasoning_effort": "ultra"},
    }


def test_fresh_run_and_cross_mode_isolation(tmp_path: Path) -> None:
    ledger = HybridLedger(tmp_path / "ledger.sqlite3")
    identity = BenchmarkIdentity("b" * 64, "e" * 64, "a" * 64, "engine")
    jobs = ledger.create_bakeoff(identity, "i" * 64)
    assert len({row["run_id"] for row in jobs}) == 3
    assert len({row["job_id"] for row in jobs}) == 3
    assert ledger.claim(jobs[0]["job_id"], "fresh-worker") is True
    assert ledger.claim(jobs[0]["job_id"], "second-worker") is False
    assert ledger.last_valid_stage(jobs[0]["job_id"]) is None
    ledger.checkpoint(jobs[0]["job_id"], "EVIDENCE_LOCKED", "i" * 64, {"ok": True}, "test", 0.1)
    assert ledger.last_valid_stage(jobs[0]["job_id"]) == "EVIDENCE_LOCKED"
    ledger.close()


def test_immutable_identity_and_visual_safety() -> None:
    base = immutable()
    expected = build_mode_input(base, "HIGH", "fresh-high")
    expected["input_hash"] = logical_hash(expected)
    packet = creative(expected)
    result = validate_creative_packet(packet, expected)
    assert result["status"] == "PASS"
    broken = copy.deepcopy(packet)
    broken["scenes"][1]["asset_id"] = broken["scenes"][0]["asset_id"]
    with pytest.raises(ValueError, match="consecutive_asset_reuse"):
        validate_creative_packet(broken, expected)


def test_truth_numeric_and_clean_master_policy_fail_closed() -> None:
    expected = build_mode_input(immutable(), "ULTRA", "fresh-ultra")
    expected["input_hash"] = logical_hash(expected)
    packet = creative(expected)
    packet["scenes"][3]["caption_visible"] = True
    with pytest.raises(ValueError, match="clean_master_caption_policy"):
        validate_creative_packet(packet, expected)
    assert zero_public_write_manifest()["platform_actions"] == []
    assert zero_public_write_manifest()["v1_mutations"] == []
