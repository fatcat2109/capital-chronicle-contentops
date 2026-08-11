from copy import deepcopy
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from live_contentops import cli
from live_contentops.tier2_asset_router_v2 import AssetRecord, AssetRightsError, resolve_real_entity_photo
from live_contentops.tier2_v2_creative_factory_v1 import (
    CRITIC_MODEL,
    DIRECTOR_FALLBACK_MODEL,
    DIRECTOR_MODEL,
    LONG_PROFILE,
    _caption_chunks,
    _xfade_name,
    apply_bounded_revision,
    build_programs,
    chapter_cache_key,
    decide_video_eligibility_v2,
    scene_cache_key,
    semantic_program_hash,
    validate_program,
)
from live_contentops.tier2_video_factory_v1 import load_governed_input


INPUT = Path("docs/automation/CONTENTOPS_FULL_AUTOMATION_LIVE_CANONICAL_BROWSER_RUN_V1/contentops_full_automation_live_20260807_1")


def _programs():
    story = load_governed_input(INPUT)
    eligibility = decide_video_eligibility_v2(story)
    return story, eligibility, build_programs(story, eligibility, {"hook": "test"})


def test_strongest_governed_story_selects_shorter_proof_without_filler():
    _story, eligibility, (long_program, short_program) = _programs()
    assert eligibility["result"] == "VIDEO_SELECTED_SHORTER_EDITORIAL_PROOF"
    assert eligibility["long_form_15_minute_decision"] == "WITHHELD_NO_FILLER"
    assert long_program["target_runtime_policy"] == "NO_15_MINUTE_FILLER"
    assert short_program["mode"] == "SHORT_FORM_NATIVE"


def test_programs_are_renderer_neutral_claim_bound_and_independently_directed():
    _story, _eligibility, (long_program, short_program) = _programs()
    assert validate_program(long_program)["status"] == "PASS"
    assert validate_program(short_program)["status"] == "PASS"
    assert {row["scene_id"] for row in long_program["scenes"]}.isdisjoint({row["scene_id"] for row in short_program["scenes"]})
    assert short_program["aspect_strategy"] == "native_9:16_independent_direction"
    assert all("render_path" not in row for row in long_program["scenes"])


def test_semantic_hash_is_separate_from_execution_state():
    _story, _eligibility, (program, _short) = _programs()
    base = semantic_program_hash(program)
    changed_runtime = deepcopy(program)
    changed_runtime["runtime_hash"] = "different-runtime"
    changed_runtime["qa_state"] = "PASS"
    assert semantic_program_hash(changed_runtime) == base
    changed_runtime["scenes"][0]["title"] = "Different creative title"
    assert semantic_program_hash(changed_runtime) != base


def _asset(tmp_path: Path, digest: str = "a" * 64) -> AssetRecord:
    path = tmp_path / "asset.png"
    path.write_bytes(b"asset")
    return AssetRecord("asset", "factual_visual", str(path), digest, "https://example.gov/source", None, "public_domain", None, "Source", "2026-08-11T00:00:00Z", False, True)


def test_scene_cache_depends_on_actual_asset_audio_and_runtime(tmp_path: Path):
    _story, _eligibility, (program, _short) = _programs()
    scene = deepcopy(program["scenes"][1])
    scene["asset_refs"] = ["asset"]
    narration = {"provider": "kokoro", "model": "Kokoro-82M", "voice": "af_heart", "script_hash": "s", "sha256": "b" * 64}
    assets = {"asset": _asset(tmp_path)}
    base = scene_cache_key(scene, narration, assets, runtime_hash="runtime-a", profile=LONG_PROFILE)
    changed_audio = dict(narration, sha256="c" * 64)
    assert scene_cache_key(scene, changed_audio, assets, runtime_hash="runtime-a", profile=LONG_PROFILE) != base
    assets_changed = {"asset": _asset(tmp_path, "d" * 64)}
    assert scene_cache_key(scene, narration, assets_changed, runtime_hash="runtime-a", profile=LONG_PROFILE) != base
    assert scene_cache_key(scene, narration, assets, runtime_hash="runtime-b", profile=LONG_PROFILE) != base


def test_chapter_cache_depends_on_scene_render_bytes_and_transition():
    chapter = {"chapter_id": "chapter", "scene_ids": ["a", "b"]}
    rows = [
        {"scene_id": "a", "render_sha256": "1", "transition": {"type": "fade"}},
        {"scene_id": "b", "render_sha256": "2", "transition": {"type": "wipeleft"}},
    ]
    base = chapter_cache_key(chapter, rows, runtime_hash="runtime")
    changed = deepcopy(rows)
    changed[1]["render_sha256"] = "3"
    assert chapter_cache_key(chapter, changed, runtime_hash="runtime") != base
    changed = deepcopy(rows)
    changed[0]["transition"]["type"] = "smoothup"
    assert chapter_cache_key(chapter, changed, runtime_hash="runtime") != base


def test_caption_chunks_are_word_level_groups_not_sentence_length_cues():
    rows = _caption_chunks("One short sentence has enough words to become several readable caption groups on screen.", 8.0)
    assert len(rows) >= 2
    assert max(len(row["text"].split()) for row in rows) <= 7
    assert rows[-1]["end_seconds"] == 8.0


def test_visual_revision_whitelist_never_changes_script_claims_or_numbers():
    _story, _eligibility, (program, _short) = _programs()
    before = {row["scene_id"]: (row["script"], deepcopy(row["claim_bindings"]), deepcopy(row["numbers"])) for row in program["scenes"]}
    critic = {"defects": [{"scene_id": program["scenes"][0]["scene_id"], "time_range": "0-5s", "class": "headline_typography_clipping"}]}
    result = apply_bounded_revision(program, critic, 1)
    assert result["applied"] is True
    for row in program["scenes"]:
        assert (row["script"], row["claim_bindings"], row["numbers"]) == before[row["scene_id"]]
    assert apply_bounded_revision(program, critic, 3)["reason"] == "revision_budget_exhausted"


def test_real_entity_photo_resolver_fails_closed_and_preserves_provenance(tmp_path: Path):
    unclear = {"asset_id": "person", "entity_name": "Person", "source_page_url": "https://agency.gov/bio", "asset_url": "https://agency.gov/photo.jpg", "rights_classification": "all_rights_reserved", "attribution": "Agency"}
    with pytest.raises(AssetRightsError, match="rights_unclear"):
        resolve_real_entity_photo(unclear, output_dir=tmp_path, get=lambda _url, _timeout: (b"", "https://agency.gov/photo.jpg"))

    image = Image.new("RGB", (640, 640), "white")
    payload = BytesIO()
    image.save(payload, format="JPEG")
    request = {**unclear, "rights_classification": "public_domain_us_government"}
    record = resolve_real_entity_photo(request, output_dir=tmp_path, get=lambda url, _timeout: (payload.getvalue(), url))
    assert record.synthetic is False
    assert record.documentary_authority is True
    assert record.source_url == request["source_page_url"]
    assert Path(record.local_path).is_file()


def test_models_are_independent_strong_authorized_entries_and_cli_registered():
    assert DIRECTOR_MODEL != CRITIC_MODEL
    assert DIRECTOR_MODEL.startswith("new/") and DIRECTOR_FALLBACK_MODEL.startswith("new/")
    assert CRITIC_MODEL.startswith("vx/")
    assert cli.COMMANDS["tier2-video-v2-creative"] is not None
    assert _xfade_name("wipeleft") == "wipeleft"
    assert _xfade_name("unknown") == "fade"
