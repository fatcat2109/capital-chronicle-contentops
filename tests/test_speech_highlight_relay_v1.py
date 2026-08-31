"""Tests for Capital Chronicle Lightweight Speech Highlight Relay V1 — Continuous & Autonomous Discovery."""

import json
import shutil
from pathlib import Path

import pytest

from live_contentops import cli
from live_contentops.speech_highlight_relay_v1 import (
    AutonomousHighlightDiscoveryEngine,
    AutonomousHighlightProposal,
    CaptionCue,
    DeterministicQuoteTranscriptVerifier,
    DynamicMediaClipper,
    PublicWriteProhibitedError,
    SpeechHighlightRelayPipeline,
    SpeechRelayError,
    format_srt_timestamp,
    format_vtt_timestamp,
    generate_srt,
    generate_vtt,
    probe_media,
    sha256_file,
    verify_speech_highlight_relay_package,
)

SOURCE_PREDECLARED_PATH = Path("video/speech_highlight_relay_v1/source_fed_20260729.json")
SOURCE_CONTINUOUS_PATH = Path("video/speech_highlight_relay_v1/source_fed_20260729_continuous_raw.json")
SOURCE_DUAL_MANDATE_PATH = Path("video/speech_highlight_relay_v1/source_fed_20260729_dual_mandate_raw.json")


def test_source_provenance_and_rights_validation_passes_on_fed_fomc():
    pipeline = SpeechHighlightRelayPipeline(SOURCE_PREDECLARED_PATH)
    result = pipeline.validate_source_packet()
    assert result["status"] == "VALIDATED"
    assert result["source_id"] == "FED_FOMC_20260729"
    assert result["source_type"] == "PRE_DECLARED_CANDIDATES"
    assert result["rights_triage"] == "REUSE_CLEAR"
    assert result["candidate_count"] == 2


def test_continuous_raw_source_provenance_validation_passes():
    pipeline = SpeechHighlightRelayPipeline(SOURCE_CONTINUOUS_PATH)
    result = pipeline.validate_source_packet()
    assert result["status"] == "VALIDATED"
    assert result["source_id"] == "FED_FOMC_20260729_CONTINUOUS"
    assert result["source_type"] == "CONTINUOUS_RAW_SOURCE"
    assert result["rights_triage"] == "REUSE_CLEAR"
    assert result["cue_count"] == 12


def test_genuine_dual_mandate_raw_source_validation():
    pipeline = SpeechHighlightRelayPipeline(SOURCE_DUAL_MANDATE_PATH)
    result = pipeline.validate_source_packet()
    assert result["status"] == "VALIDATED"
    assert result["source_id"] == "FED_FOMC_20260729_DUAL_MANDATE_RAW"
    assert result["source_type"] == "CONTINUOUS_RAW_SOURCE"
    assert result["rights_triage"] == "REUSE_CLEAR"
    assert result["cue_count"] == 5


def test_missing_or_prohibited_rights_fails_closed(tmp_path: Path):
    bad_config = tmp_path / "bad_rights.json"
    data = json.loads(SOURCE_PREDECLARED_PATH.read_text(encoding="utf-8"))
    data["rights"]["triage_state"] = "TRANSFORMATIVE_EDITORIAL_REVIEW_REQUIRED"
    bad_config.write_text(json.dumps(data), encoding="utf-8")

    pipeline = SpeechHighlightRelayPipeline(bad_config)
    with pytest.raises(SpeechRelayError, match="rights triage state must be REUSE_CLEAR"):
        pipeline.validate_source_packet()


def test_mismatched_transcript_hash_fails_closed(tmp_path: Path):
    bad_config = tmp_path / "bad_transcript.json"
    data = json.loads(SOURCE_PREDECLARED_PATH.read_text(encoding="utf-8"))
    data["official_transcript_sha256"] = "0" * 64
    bad_config.write_text(json.dumps(data), encoding="utf-8")

    pipeline = SpeechHighlightRelayPipeline(bad_config)
    with pytest.raises(SpeechRelayError, match="Transcript hash mismatch"):
        pipeline.validate_source_packet()


def test_mismatched_clip_hash_fails_closed(tmp_path: Path):
    bad_config = tmp_path / "bad_clip.json"
    data = json.loads(SOURCE_PREDECLARED_PATH.read_text(encoding="utf-8"))
    data["highlight_candidates"][0]["clip_sha256"] = "f" * 64
    bad_config.write_text(json.dumps(data), encoding="utf-8")

    pipeline = SpeechHighlightRelayPipeline(bad_config)
    with pytest.raises(SpeechRelayError, match="Clip hash mismatch"):
        pipeline.validate_source_packet()


def test_caption_sidecar_generation_srt_and_vtt():
    cues = [
        CaptionCue("cue_1", 0.0, 3.5, "First phrase spoken.", "Kevin Warsh"),
        CaptionCue("cue_2", 3.5, 7.825, "Second phrase spoken clearly.", "Kevin Warsh"),
    ]

    srt = generate_srt(cues)
    assert "1\n00:00:00,000 --> 00:00:03,500\nFirst phrase spoken." in srt
    assert "2\n00:00:03,500 --> 00:00:07,825\nSecond phrase spoken clearly." in srt

    vtt = generate_vtt(cues)
    assert vtt.startswith("WEBVTT\n")
    assert "1\n00:00:00.000 --> 00:00:03.500\nFirst phrase spoken." in vtt
    assert "2\n00:00:03.500 --> 00:00:07.825\nSecond phrase spoken clearly." in vtt


# ==============================================================================
# Autonomous Discovery & Verification Tests
# ==============================================================================

def test_autonomous_highlight_discovery_proposes_ranked_candidates():
    engine = AutonomousHighlightDiscoveryEngine()
    data = json.loads(SOURCE_CONTINUOUS_PATH.read_text(encoding="utf-8"))
    cues = [
        CaptionCue(
            cue_id=c["cue_id"],
            start_seconds=float(c["start_seconds"]),
            end_seconds=float(c["end_seconds"]),
            text=str(c["text"]),
            speaker=c.get("speaker", "Speaker"),
        )
        for c in data["continuous_timed_transcript"]
    ]

    result = engine.discover_and_rank_highlights(data, cues)
    assert result["status"] == "DISCOVERED_CANDIDATES"
    assert result["candidate_count"] >= 2
    proposals = result["proposals"]
    assert proposals[0]["score"] >= proposals[1]["score"]
    assert any(p["score"] > 80.0 for p in proposals)
    assert any(
        "LABOR" in p["proposal_id"] or "POLICY" in p["proposal_id"] or "MONETARY" in p["proposal_id"]
        for p in proposals
    )


def test_autonomous_discovery_truthful_abstention_on_procedural_transcripts():
    engine = AutonomousHighlightDiscoveryEngine()
    procedural_cues = [
        CaptionCue("cue_p1", 0.0, 4.0, "Good morning, welcome everyone to today's meeting.", "Speaker"),
        CaptionCue("cue_p2", 4.0, 8.0, "Thank you very much. Let me hand it over to the committee.", "Speaker"),
    ]
    metadata = {"event_title": "Procedural Roll Call", "publisher": "Senate Committee"}
    result = engine.discover_and_rank_highlights(metadata, procedural_cues)
    assert result["status"] == "ABSTAIN_NO_SAFE_HIGHLIGHT"
    assert "No speech segment met the required financial significance" in result["reason"]
    assert len(result["proposals"]) == 0


def test_deterministic_quote_verifier_fails_closed_on_hallucinated_words():
    raw_cues = [
        CaptionCue("cue_1", 0.0, 3.8, "The economy is showing impressive resilience.", "Speaker"),
        CaptionCue("cue_2", 3.8, 8.6, "Even with recent shocks, the trends are positive and reveal solid growth.", "Speaker"),
    ]
    hallucinated_proposal = AutonomousHighlightProposal(
        proposal_id="AUTO_FAKE_01",
        rank=1,
        start_seconds=0.0,
        end_seconds=8.6,
        exact_quote="The economy is showing impressive resilience and inflation is completely defeated.",
        financial_importance="False claim",
        editorial_takeaway="Hallucinated text",
        why_it_matters="Test failure mode",
        material_qualifiers="None",
        score=99.0,
        topic_category="FAKE",
    )

    with pytest.raises(SpeechRelayError, match="Candidate quote does not match transcript cues verbatim"):
        DeterministicQuoteTranscriptVerifier.verify_and_align_candidate(hallucinated_proposal, raw_cues)


def test_dynamic_media_clipper_extracts_clean_segment(tmp_path: Path):
    source_media = Path("video/speech_highlight_relay_v1/assets/authority/fed_fomc_2026-07-29_continuous_full_speech_raw.mp4")
    out_clip = tmp_path / "dynamic_clip_test.mp4"

    DynamicMediaClipper.extract_clip(
        source_media_path=source_media,
        start_seconds=0.0,
        duration_seconds=5.0,
        output_clip_path=out_clip,
    )

    assert out_clip.is_file()
    probe = probe_media(out_clip)
    assert round(float(probe["format"]["duration"]), 1) == 5.0
    v_stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
    assert v_stream["width"] == 640
    assert v_stream["height"] == 720


def test_end_to_end_autonomous_discovery_package_rendering(tmp_path: Path):
    output_dir = tmp_path / "autonomous_output_package"
    pipeline = SpeechHighlightRelayPipeline(SOURCE_CONTINUOUS_PATH, workspace_root=tmp_path)

    # Note: candidate_id is None -> system autonomously discovers, ranks, verifies, and selects top highlight!
    result = pipeline.render_package(candidate_id=None, output_dir=output_dir)

    assert result["status"] == "SUCCESS"
    assert result["publication_state"] == "PUBLICATION_HOLD"
    assert result["public_writes"] == 0
    assert result["unknown_writes"] == 0
    assert result["manifests_written"] == 7  # Includes autonomous_discovery_manifest.json

    # Check files exist
    clean_master = output_dir / "master_vertical_clean_1080x1920.mp4"
    captioned_derivative = output_dir / "derivative_vertical_captioned_1080x1920.mp4"
    disc_manifest = output_dir / "autonomous_discovery_manifest.json"
    package_manifest = output_dir / "package_manifest.json"

    assert clean_master.is_file()
    assert captioned_derivative.is_file()
    assert disc_manifest.is_file()
    assert package_manifest.is_file()

    # Verify autonomous discovery manifest content
    disc_data = json.loads(disc_manifest.read_text(encoding="utf-8"))
    assert disc_data["discovery_status"] == "DISCOVERED_AND_VERIFIED"
    assert disc_data["total_proposals"] >= 2
    assert "AUTO_CANDIDATE_01" in disc_data["selected_candidate_id"]

    # Package verification check
    verification = verify_speech_highlight_relay_package(output_dir)
    assert verification["status"] == "PASS"
    assert verification["publication_state"] == "PUBLICATION_HOLD"
    assert verification["public_writes"] == 0
    assert verification["unknown_writes"] == 0


def test_custom_llm_evaluator_injection(tmp_path: Path):
    def mock_custom_llm(prompt: str) -> str:
        # LLM returns structured JSON proposals
        return json.dumps([
            {
                "rank": 1,
                "start_seconds": 42.915,
                "end_seconds": 63.315,
                "exact_quote": "Any central banker, especially a central banker where the labor markets are more or less at equilibrium— any central banker, when he or she sees underlying inflation moving higher— he or she is more inclined to tighten policy.",
                "financial_importance": "Reaction function under rising inflation and balanced labor markets.",
                "editorial_takeaway": "Central bank tightening bias when inflation accelerates.",
                "why_it_matters": "Chair Warsh explains policy inclination when labor is in balance but inflation rises.",
                "material_qualifiers": "Labor markets at equilibrium.",
                "score": 98.0,
                "topic_category": "INFLATION_REACTION",
            }
        ])

    output_dir = tmp_path / "custom_llm_package"
    pipeline = SpeechHighlightRelayPipeline(
        SOURCE_CONTINUOUS_PATH,
        workspace_root=tmp_path,
        llm_fn=mock_custom_llm,
    )

    result = pipeline.render_package(candidate_id=None, output_dir=output_dir)
    assert result["status"] == "SUCCESS"
    assert "inflation_reaction" in result["package_id"].lower()

    disc_data = json.loads((output_dir / "autonomous_discovery_manifest.json").read_text(encoding="utf-8"))
    assert disc_data["proposals"][0]["topic_category"] == "INFLATION_REACTION"
    assert disc_data["proposals"][0]["score"] == 98.0


def test_genuine_dual_mandate_raw_source_autonomous_package_rendering(tmp_path: Path):
    output_dir = tmp_path / "genuine_dual_mandate_package"
    pipeline = SpeechHighlightRelayPipeline(SOURCE_DUAL_MANDATE_PATH, workspace_root=tmp_path)

    result = pipeline.render_package(candidate_id=None, output_dir=output_dir)

    assert result["status"] == "SUCCESS"
    assert result["publication_state"] == "PUBLICATION_HOLD"
    assert result["public_writes"] == 0
    assert result["unknown_writes"] == 0
    assert result["manifests_written"] == 7

    # Check generated files
    clean_master = output_dir / "master_vertical_clean_1080x1920.mp4"
    captioned_derivative = output_dir / "derivative_vertical_captioned_1080x1920.mp4"
    disc_manifest = output_dir / "autonomous_discovery_manifest.json"

    assert clean_master.is_file()
    assert captioned_derivative.is_file()
    assert disc_manifest.is_file()

    disc_data = json.loads(disc_manifest.read_text(encoding="utf-8"))
    assert disc_data["discovery_status"] == "DISCOVERED_AND_VERIFIED"
    assert "model_execution_evidence" in disc_data
    assert "AUTO_CANDIDATE" in disc_data["selected_candidate_id"]

    verification = verify_speech_highlight_relay_package(output_dir)
    assert verification["status"] == "PASS"
    assert verification["publication_state"] == "PUBLICATION_HOLD"


def test_cli_registers_speech_highlight_relay_command():
    assert "speech-highlight-relay" in cli.COMMANDS
    assert cli.COMMANDS["speech-highlight-relay"] is not None
