from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from live_contentops.lane_b_asset_first_v1 import (
    AssetFirstLedger,
    ExecutionProvenance,
    validate_asset_board,
    validate_creative_source,
    validate_dependencies,
    validate_audio_provider,
    validate_editorial_layers,
    validate_layout,
    validate_microbeats,
    validate_visual_needs,
    validate_zero_public_write,
    zero_public_write_manifest,
)
from scripts.run_lane_b_asset_first_v1 import (
    CREATIVE_SOURCE,
    RENDERER,
    VISUAL_NEEDS,
    dependency_manifest,
    layout_report,
    microbeat_report,
)


class AssetFirstControlsTests(unittest.TestCase):
    def test_story_specific_source_and_actual_dependencies_pass(self) -> None:
        self.assertEqual("PASS", validate_creative_source(CREATIVE_SOURCE, RENDERER)["status"])
        result = validate_dependencies(dependency_manifest(), CREATIVE_SOURCE)
        self.assertEqual("PASS", result["status"], result["errors"])
        self.assertEqual(6, result["dependency_count"])

    def test_fixed_scene_renderer_and_network_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "proof.tsx"
            source.write_text(
                "// CODEX_VIEWER_FACING_AUTHORSHIP\n"
                "export const AssetFirstTreasuryShort=()=>fetch('https://x');\n"
                "export const AssetFirstTreasuryMidform=SceneRenderer;\n",
                encoding="utf-8",
            )
            errors = validate_creative_source(source, root)["errors"]
        self.assertIn("forbidden_source:network", errors)
        self.assertIn("forbidden_source:fixed_scene_renderer", errors)

    def test_visual_needs_and_microbeat_cadence_pass(self) -> None:
        self.assertEqual("PASS", validate_visual_needs(VISUAL_NEEDS)["status"])
        result = validate_microbeats(microbeat_report())
        self.assertEqual("PASS", result["status"], result["errors"])

    def test_asset_visual_fit_is_a_hard_gate(self) -> None:
        row = {
            "need_id": "N01_HOOK", "asset_id": "bad.jpg", "license_id": "PUBLIC_DOMAIN",
            "attribution": "public domain", "source_url": "https://example.invalid",
            "decision": "SELECTED", "decision_reason": "test", "visual_fit_score": .4,
            "width": 1920, "height": 1080,
        }
        result = validate_asset_board({"candidates": [row, {**row, "asset_id": "other.jpg", "decision": "REJECTED", "visual_fit_score": .3}]})
        self.assertEqual("FAIL", result["status"])
        self.assertTrue(any(error.startswith("asset_visual_fit_below_gate") for error in result["errors"]))

    def test_durable_ledger_rejects_stage_regression(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            book = AssetFirstLedger(Path(directory) / "ledger.sqlite3")
            book.create_job("job", "candidate")
            book.checkpoint("job", "EVIDENCE_LOCKED", "i", {"status": "PASS"}, model_or_tool="test", execution_plane="LOCAL_DETERMINISTIC", runtime_seconds=0)
            with self.assertRaisesRegex(ValueError, "stage_regression"):
                book.checkpoint("job", "QUALIFIED", "i", {"status": "PASS"}, model_or_tool="test", execution_plane="LOCAL_DETERMINISTIC", runtime_seconds=0)
            book.close()

    def test_durable_ledger_reuses_identical_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            book = AssetFirstLedger(Path(directory) / "ledger.sqlite3")
            book.create_job("job", "candidate")
            kwargs = {"model_or_tool":"test","execution_plane":"LOCAL_DETERMINISTIC","runtime_seconds":0}
            first = book.checkpoint("job", "EVIDENCE_LOCKED", "same", {"status":"PASS"}, **kwargs)
            second = book.checkpoint("job", "EVIDENCE_LOCKED", "same", {"status":"PASS"}, **kwargs)
            self.assertEqual("WRITTEN", first["status"])
            self.assertEqual("REUSED", second["status"])
            self.assertEqual(first["stage_row_id"], second["stage_row_id"])
            book.close()

    def test_editorial_route_layout_and_audio_policy(self) -> None:
        editorial = {"layers":{"truth":{"x":1},"analysis":{"x":1},"engagement":{"x":1}},
                     "nine_router_route":None,"mode_policy":"UNSELECTED","legacy_hormuz_raster_used":False,
                     "quantitative_claims":[{"claim_id":"c","source_id":"treasury","status":"OBSERVATION"}]}
        self.assertEqual("PASS", validate_editorial_layers(editorial)["status"])
        self.assertEqual("PASS", validate_layout(layout_report())["status"])
        self.assertEqual("PASS", validate_audio_provider("kokoro-82m")["status"])
        self.assertEqual("FAIL", validate_audio_provider("windows-sapi")["status"])

    def test_mode_bakeoff_and_public_write_are_forbidden(self) -> None:
        with self.assertRaisesRegex(ValueError, "mode_bakeoff_forbidden"):
            ExecutionProvenance("CODEX_TASK_SESSION", "codex", "ULTRA").validate()
        manifest = zero_public_write_manifest()
        self.assertFalse(manifest["public_write_authority"])
        self.assertEqual(0, manifest["network_publication_calls"])
        self.assertEqual(0, manifest["v1_store_mutations"])
        self.assertEqual("PASS", validate_zero_public_write(manifest)["status"])


if __name__ == "__main__":
    unittest.main()
