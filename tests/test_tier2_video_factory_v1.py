from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest

from live_contentops import cli
from live_contentops.content_intelligence_contracts_v2 import logical_hash
from live_contentops.tier2_video_factory_v1 import (
    build_video_program,
    decide_video_eligibility,
    load_governed_input,
    verify_hash_manifest,
)


INPUT = Path("docs/automation/CONTENTOPS_FULL_AUTOMATION_LIVE_CANONICAL_BROWSER_RUN_V1/contentops_full_automation_live_20260807_1")


@pytest.fixture(scope="module")
def media_authorized_input(tmp_path_factory):
    target = tmp_path_factory.mktemp("explicit-media-display") / "input"
    shutil.copytree(INPUT, target)
    support_path = target / "grounded_support_v1.json"
    support = json.loads(support_path.read_text(encoding="utf-8"))
    permissions = support["official_source_packet"]["public_claim_permissions"]
    permissions["public_display_allowed"] = True
    permissions["allowed_uses"] = ["public_reporting", "public_media_display"]
    support_path.write_text(json.dumps(support), encoding="utf-8")
    return target


def _program(input_dir):
    story = load_governed_input(input_dir)
    eligibility = decide_video_eligibility(story)
    return story, eligibility, build_video_program(story, eligibility)


def test_historical_treasury_reporting_packet_is_not_media_display_authority():
    with pytest.raises(RuntimeError, match="public_media_display"):
        load_governed_input(INPUT)


def test_explicit_media_display_grant_is_video_selected(media_authorized_input):
    story, eligibility, program = _program(media_authorized_input)
    assert story["packet_id"] == "cc-evidence-bde0048ee1ebe31f"
    assert eligibility["result"] == "VIDEO_SELECTED"
    assert eligibility["rights_ready"] is True
    assert len(program["chapters"]) == 5
    assert len(program["scenes"]) == 10
    assert len(program["short_variant"]["scenes"]) == 5
    assert story["capital_chronicle_publication_authority"]["state"] == (
        "PUBLICATION_PACKET_AVAILABLE"
    )
    assert story["publication_authorized_cc_projection"]["exact_numeric_claims"] == list(
        story["claims"].values()
    )
    assert story["publication_authorized_cc_projection"]["values_regenerated_or_repaired"] is False


def test_every_factual_scene_has_exact_claim_and_source_bindings(media_authorized_input):
    _story, _eligibility, program = _program(media_authorized_input)
    expected = {
        "UST:2Y:2026-07-13",
        "UST:10Y:2026-07-13",
        "UST:30Y:2026-07-13",
        "UST:2S10S:2026-07-13",
    }
    coverage = set()
    for scene in program["scenes"] + program["short_variant"]["scenes"]:
        assert scene["claim_bindings"]
        assert scene["source_bindings"]
        assert scene["credits"].startswith("Source: U.S. Department of the Treasury")
        coverage.update(row["claim_id"] for row in scene["claim_bindings"])
    assert coverage == expected


def test_short_is_independently_directed_native_layout(media_authorized_input):
    _story, _eligibility, program = _program(media_authorized_input)
    long_ids = {row["scene_id"] for row in program["scenes"]}
    short_ids = {row["scene_id"] for row in program["short_variant"]["scenes"]}
    assert long_ids.isdisjoint(short_ids)
    assert program["aspect_strategy"]["short_derivative"] == "independent_9:16"
    assert program["short_variant"]["scenes"][0]["display_title"] == "THE 30-YEAR AT 5.10%"


def test_one_scene_field_only_invalidates_that_scene_and_chapter_input(media_authorized_input):
    _story, _eligibility, program = _program(media_authorized_input)
    before = {row["scene_id"]: logical_hash(row) for row in program["scenes"]}
    patched = deepcopy(program)
    patched["scenes"][4]["semantic_purpose"] += " corrected"
    after = {row["scene_id"]: logical_hash(row) for row in patched["scenes"]}
    changed = [scene_id for scene_id in before if before[scene_id] != after[scene_id]]
    assert changed == [program["scenes"][4]["scene_id"]]
    target_chapter = program["scenes"][4]["chapter_id"]
    before_chapters = {row["chapter_id"]: logical_hash({"chapter": row, "scene_hashes": [before[item] for item in row["scene_ids"]]}) for row in program["chapters"]}
    after_chapters = {row["chapter_id"]: logical_hash({"chapter": row, "scene_hashes": [after[item] for item in row["scene_ids"]]}) for row in patched["chapters"]}
    assert [item for item in before_chapters if before_chapters[item] != after_chapters[item]] == [target_chapter]


def test_missing_rights_blocks_video_selection(media_authorized_input):
    story = load_governed_input(media_authorized_input)
    story["media_assets"][0]["rights_status"] = "unknown"
    assert decide_video_eligibility(story)["result"] == "VIDEO_BLOCKED"


def test_missing_governed_input_fails_closed(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_governed_input(tmp_path)


def test_canonical_cli_registers_local_tier2_command():
    assert cli.COMMANDS["tier2-video-local"] is not None


def test_hash_manifest_verification_fails_closed_on_byte_change(tmp_path: Path):
    import hashlib
    import json

    artifact = tmp_path / "artifact.txt"
    artifact.write_text("accepted", encoding="utf-8")
    expected = hashlib.sha256(artifact.read_bytes()).hexdigest()
    (tmp_path / "hash_manifest.json").write_text(json.dumps({"artifact.txt": expected}), encoding="utf-8")
    assert verify_hash_manifest(tmp_path)["status"] == "PASS"
    artifact.write_text("changed", encoding="utf-8")
    result = verify_hash_manifest(tmp_path)
    assert result["status"] == "BLOCK"
    assert result["blockers"] == ["hash_mismatch:artifact.txt"]
