from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from live_contentops.breaking_news_crisp_v1 import (
    BANNED_VOICE_IDS,
    BreakingNewsLedger,
    codex_execution_plane_manifest,
    sha256_file,
    validate_annotation_geometry,
    validate_audio_contract,
    validate_authority_clip,
    validate_breaking_event,
    validate_claim_bindings,
    validate_creative_source,
    validate_crisp_master,
    validate_editorial,
    validate_material_audit,
    validate_microbeat_timeline,
    validate_zero_public_write,
    zero_public_write_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "video" / "breaking_news_v1"
SOURCE = PROJECT / "src" / "generated" / "retailBreaking.tsx"


class BreakingNewsCrispTests(unittest.TestCase):
    def test_breaking_event_and_bound_claims(self) -> None:
        event = {"event_id":"retail","published_at":"2026-08-14T08:30:00-04:00",
                 "observed_at":"2026-08-14T19:00:00+07:00","primary_source_url":"https://census.gov",
                 "concrete_change":"-0.6% m/m","urgency_fabricated":False,
                 "market_reaction_status":"OMITTED_NO_GOVERNED_MARKET_DATA"}
        self.assertEqual("PASS", validate_breaking_event(event)["status"])
        packet = {"sources":[{"source_id":"census"}],"claims":[
            {"claim_id":"total","source_id":"census","kind":"OBSERVATION"},
            {"claim_id":"significant","source_id":"census","kind":"DERIVED","derivation":"-0.6 ±0.4 excludes zero"},
        ]}
        self.assertEqual("PASS", validate_claim_bindings(packet)["status"])

    def test_rights_safe_skip_and_broadcaster_rejection(self) -> None:
        receipt = {"decision":"SKIP_NO_SAFE_HIGH_VALUE_CLIP","broadcaster_scrape_attempted":False,
                   "synthetic_real_official":False}
        self.assertEqual("PASS", validate_authority_clip(receipt)["status"])
        receipt["broadcaster_scrape_attempted"] = True
        self.assertEqual("FAIL", validate_authority_clip(receipt)["status"])

    def test_market_native_editorial_wit_gate(self) -> None:
        editorial = {"format":"BREAKING_NATIVE","layers":{"truth":{"x":1},"analysis":{"x":1},"engagement":{"x":1}},
                     "wit_candidates":[{"candidate_id":"w1","decision":"ACCEPTED","fact_safe":True,
                     "relevant":True,"market_literate":True,"non_advice":True}]}
        self.assertEqual("PASS", validate_editorial(editorial)["status"])

    def test_audio_requires_identity_search_segments_and_no_global_atempo(self) -> None:
        row = {"segment_id":"s","text_sha256":"x","model_id":"eleven_v3","voice_id":"v",
               "settings":{"stability":.45},"duration_seconds":5,"audio_sha256":"a"}
        stage_a = [{"voice_id":f"voice-{i}"} for i in range(8)]
        stage_b = [{"voice_id":f"voice-{i}"} for i in range(3)]
        contract = {"audition":{"identity_search":{"stage_a_candidates":stage_a,"stage_b_finalists":stage_b},
                    "selected_model_id":"eleven_v3","selected_voice_id":"voice-1"},
                    "segments":[{**row,"segment_id":str(i)} for i in range(6)],
                    "global_atempo_used":False,"maximum_segment_time_correction_percent":0,
                    "professional_audio_eligibility":"ELEVENLABS_API_ELIGIBLE","api_key_serialized":False}
        self.assertEqual("PASS", validate_audio_contract(contract)["status"])
        contract["global_atempo_used"] = True
        self.assertIn("global_atempo_forbidden", validate_audio_contract(contract)["errors"])
        contract["global_atempo_used"] = False
        contract["audition"]["selected_voice_id"] = next(iter(BANNED_VOICE_IDS))
        self.assertIn("banned_voice_selected", validate_audio_contract(contract)["errors"])

    def test_document_annotation_is_bound_to_target_and_clear_of_metrics(self) -> None:
        record = {
            "source_document_sha256":"a" * 64,
            "source_page":1,
            "exact_target_text":"not adjusted for price changes",
            "document_target_bbox":[100,200,700,260],
            "rendered_target_bbox":[110,580,870,660],
            "annotation_bbox":[100,570,880,670],
            "annotation_padding":{"x":10,"y":10},
            "transform_identity":{"kind":"AFFINE","scale_x":1.0,"scale_y":1.0,"translate_x":0,"translate_y":0},
            "frame_size":[1080,1920],
            "unrelated_glyph_bboxes":[{"label":"$763.6B","bbox":[110,760,430,860]}],
            "settled_frames":{
                "1080x1920":{"annotation_bbox":[100,570,880,670]},
                "2160x3840":{"annotation_bbox":[200,1140,1760,1340]},
            },
        }
        self.assertEqual("PASS", validate_annotation_geometry(record)["status"])
        record["annotation_bbox"] = [100,570,880,830]
        errors = validate_annotation_geometry(record)["errors"]
        self.assertTrue(any(error.startswith("annotation_overreach") for error in errors))
        self.assertTrue(any("$763.6B" in error for error in errors))

    def test_microbeats_require_evidence_function_and_explain_long_holds(self) -> None:
        timeline = {"beats":[
            {"beat_id":"a","start_seconds":0,"end_seconds":2.4,"evidence_function":"state headline"},
            {"beat_id":"b","start_seconds":2.4,"end_seconds":5.2,"evidence_function":"reveal exact value"},
        ]}
        self.assertEqual("PASS", validate_microbeat_timeline(timeline)["status"])
        timeline["beats"][1]["end_seconds"] = 6.2
        self.assertTrue(any(error.startswith("unexplained_static_hold") for error in validate_microbeat_timeline(timeline)["errors"]))

    def test_story_specific_source_is_sandboxed(self) -> None:
        result = validate_creative_source(SOURCE, PROJECT)
        self.assertEqual("PASS", result["status"], result["errors"])

    def test_import_manifest_retains_exact_source_snapshot_hashes(self) -> None:
        path = ROOT / "docs" / "automation" / "CONTENTOPS_V2_BREAKING_NEWS_OWNER_DEFECT_REPAIR_V2" / "import_manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        source_root = Path(manifest["source_root"])
        self.assertEqual("PASS_EXACT_BYTE_PARITY", manifest["validation_at_import"])
        self.assertEqual(12, len(manifest["files"]))
        for row in manifest["files"]:
            self.assertEqual(row["source_sha256"], sha256_file(source_root / row["source"]))
            self.assertEqual(row["source_sha256"], row["after_import_sha256"])

    def test_codex_execution_plane_bypasses_nine_router(self) -> None:
        receipt = codex_execution_plane_manifest()
        self.assertIsNone(receipt["nine_router_route"])
        self.assertEqual("not_exposed", receipt["reasoning_effort"])

    def test_elevenlabs_key_is_not_serialized_in_scoped_source(self) -> None:
        source_text = "\n".join(path.read_text(encoding="utf-8") for path in (
            ROOT / "live_contentops" / "breaking_news_crisp_v1.py",
            ROOT / "scripts" / "run_v2_breaking_news_crisp_v1.py",
        ))
        secret = os.environ.get("ELEVENLABS_API_KEY", "")
        if secret:
            self.assertNotIn(secret, source_text)

    def test_crisp_gate_checks_resolution_bitrate_and_bt709(self) -> None:
        fake = {"format":{"bit_rate":"40000000"},"streams":[{"codec_type":"video","codec_name":"h264",
                "profile":"High","width":2160,"height":3840,"avg_frame_rate":"30/1","pix_fmt":"yuv420p",
                "color_range":"tv","color_space":"bt709","color_transfer":"bt709","color_primaries":"bt709"}]}
        with patch("live_contentops.breaking_news_crisp_v1.probe_media", return_value=fake):
            result = validate_crisp_master(Path("master.mp4"), expected_width=2160, expected_height=3840,
                                           minimum_bitrate=35_000_000, proxy_lineage=False,
                                           source_assets=[{"asset_id":"mall","native_width":4831,"minimum_width":2160}])
        self.assertEqual("PASS", result["status"], result["errors"])

    def test_material_audit_beats_qh1_darkness(self) -> None:
        report = {"pixels_below_luma_64_fraction":.38,"material_family_count":6,"max_equivalent_dark_run":1}
        self.assertEqual("PASS", validate_material_audit(report)["status"])

    def test_ledger_reuses_and_rejects_regression(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ledger = BreakingNewsLedger(Path(directory) / "ledger.sqlite3")
            ledger.create("job")
            first = ledger.checkpoint("job", "EVIDENCE_LOCKED", "i", {"status":"PASS"})
            second = ledger.checkpoint("job", "EVIDENCE_LOCKED", "i", {"status":"PASS"})
            self.assertEqual("REUSED", second["status"])
            self.assertEqual(first["id"], second["id"])
            with self.assertRaisesRegex(ValueError, "stage_regression"):
                ledger.checkpoint("job", "QUALIFIED", "x", {"status":"PASS"})
            ledger.close()

    def test_zero_public_write(self) -> None:
        manifest = zero_public_write_manifest()
        self.assertEqual("PASS", validate_zero_public_write(manifest)["status"])
        self.assertFalse(manifest["public_write_authority"])
        self.assertFalse(manifest["heygen_used"])


if __name__ == "__main__":
    unittest.main()
