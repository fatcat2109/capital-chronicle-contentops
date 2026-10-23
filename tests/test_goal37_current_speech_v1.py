"""Disposable mechanics only; no real audio review or factual source proof."""

import json
import pytest
from live_contentops import speech_highlight_current_source_v1 as current
from live_contentops import speech_highlight_relay_v1 as relay


def source(tmp_path):
    media = tmp_path / "source.mp4"
    media.write_bytes(b"controlled media")
    rights = tmp_path / "rights.json"
    rights.write_text("Controlled rights evidence only")
    transcript = tmp_path / "transcript.json"
    transcript.write_text(
        json.dumps(
            [dict(start_seconds=0, end_seconds=6, text="We do not claim certainty.")]
        )
    )

    def identity(p):
        return dict(file=p.name, sha256=relay.sha256_file(p))

    return dict(
        schema=current.SCHEMA,
        source_id="controlled",
        publisher="Controlled source",
        canonical_source_url="https://example.org/source",
        event_date="2026-10-20",
        acquisition="CONTROLLED_TEST_NOT_ACTUAL_CAPTURE",
        production_eligible=False,
        media=dict(identity(media), duration_seconds=6),
        transcript=identity(transcript),
        speaker=dict(name="Controlled speaker", role="Controlled"),
        rights=dict(
            private_processing_basis="PERMITTED",
            evidence=identity(rights),
            media_sha256=relay.sha256_file(media),
            limitations=["CONTROLLED_ONLY"],
        ),
    )


def returns(packet):
    base = dict(
        source_sha256=current.digest(packet),
        model="gpt-6.1-sol",
        native_turn_id="CONTROLLED_NOT_MODEL_EXECUTION",
    )
    select = dict(
        base,
        role="SELECTION",
        reasoning_effort="low",
        format="MOMENT_CONTEXT",
        span=dict(start_seconds=0, end_seconds=6),
        exact_quote="We do not claim certainty.",
        rationale="Controlled qualifier check",
        surrounding_context="Controlled context",
    )
    meaning = dict(
        base,
        role="MEANING",
        reasoning_effort="max",
        selection_sha256=current.digest(select),
        decision="KEEP",
        headline="Controlled headline",
        context="Controlled context",
        speaker_claim="Speaker says uncertainty remains",
        independent_evidence="Not established",
        cc_interpretation="Conditional only",
    )
    return select, meaning


def test_exact_request_resume_uses_completed_stages_and_detects_artifact_drift(
    tmp_path, monkeypatch
):
    packet = source(tmp_path)
    selection, meaning = returns(packet)
    out = tmp_path / ".task-runtime/speech_highlight_relay_v1/job"
    assert (
        current.prepare(packet, tmp_path, out)["stage"] == "AWAITING_NATIVE_SELECTION"
    )
    assert (
        current.prepare(packet, tmp_path, out, selection)["stage"]
        == "AWAITING_NATIVE_MEANING"
    )
    calls = []
    monkeypatch.setattr(
        relay.DynamicMediaClipper,
        "extract_clip",
        lambda _p, _a, _d, target: target.write_bytes(b"controlled clip"),
    )

    def render(_clip, target, _packet, _duration, cues):
        calls.append(target.name)
        target.write_bytes(b"controlled render")
        if cues:
            assert cues[0].text == "We do not claim certainty."

    monkeypatch.setattr(relay, "_render_vertical", render)
    monkeypatch.setattr(relay, "probe_media", lambda _p: {})
    monkeypatch.setattr(relay, "_check_media", lambda *_a, **_k: None)
    result = current.prepare(packet, tmp_path, out, selection, meaning)
    assert result["production_eligible"] is False
    assert "ORIGINAL_AUDIO_LISTENING_NOT_VERIFIED" in result["holds"]
    assert current.prepare(packet, tmp_path, out) == result and len(calls) == 2
    review = json.loads((out / "review_request.json").read_text())
    assert review["span"] == selection["span"]
    assert review["edit_sha256"] == result["edit_sha256"]
    assert review["review_state"] == "NOT_REVIEWED"
    assert "ASSET_SPECIFIC_PUBLICATION_RIGHTS_NOT_CLEARED" in result["holds"]
    (out / "captions.srt").write_text("changed")
    with pytest.raises(relay.SpeechRelayError, match="drift"):
        current.prepare(packet, tmp_path, out, selection, meaning)


def test_qualifier_removal_and_false_native_role_are_rejected(tmp_path):
    packet = source(tmp_path)
    selection, meaning = returns(packet)
    selection["exact_quote"] = "We claim certainty."
    with pytest.raises(relay.SpeechRelayError, match="wording"):
        current.prepare(
            packet,
            tmp_path,
            tmp_path / ".task-runtime/speech_highlight_relay_v1/a",
            selection,
            meaning,
        )
    assert not (
        tmp_path / ".task-runtime/speech_highlight_relay_v1/a/selection_return.json"
    ).exists()
    selection, meaning = returns(packet)
    # Rejected input did not freeze the slot; a valid native return can resume it.
    assert (
        current.prepare(
            packet,
            tmp_path,
            tmp_path / ".task-runtime/speech_highlight_relay_v1/a",
            selection,
        )["stage"]
        == "AWAITING_NATIVE_MEANING"
    )
    selection, meaning = returns(packet)
    meaning["reasoning_effort"] = "low"
    with pytest.raises(relay.SpeechRelayError, match="provenance"):
        current.prepare(
            packet,
            tmp_path,
            tmp_path / ".task-runtime/speech_highlight_relay_v1/b",
            selection,
            meaning,
        )


def test_rights_hold_prevents_media_render_and_dedupe_is_bounded(tmp_path):
    packet = source(tmp_path)
    packet["rights"] = {}
    selection, meaning = returns(packet)
    result = current.prepare(
        packet,
        tmp_path,
        tmp_path / ".task-runtime/speech_highlight_relay_v1/a",
        selection,
        meaning,
    )
    assert result["stage"] == "RIGHTS_HOLD"
    rows = [
        dict(source_id=str(i), canonical_source_url="https://example.org/" + str(i))
        for i in range(5)
    ]
    assert len(current.candidates(rows[0], rows)) == 3


def test_interrupted_render_discards_partial_and_reuses_sealed_clip(
    tmp_path, monkeypatch
):
    packet = source(tmp_path)
    selection, meaning = returns(packet)
    out = tmp_path / ".task-runtime/speech_highlight_relay_v1/interrupted"
    clips = []
    renders = []

    def clip(_p, _a, _d, target):
        clips.append(target)
        target.write_bytes(b"controlled clip")

    def render(_clip, target, _packet, _duration, _cues):
        renders.append(target.name)
        target.write_bytes(b"partial")
        if len(renders) == 1:
            raise RuntimeError("controlled interruption")
        target.write_bytes(b"complete")

    monkeypatch.setattr(relay.DynamicMediaClipper, "extract_clip", clip)
    monkeypatch.setattr(relay, "_render_vertical", render)
    monkeypatch.setattr(relay, "probe_media", lambda _p: {})
    monkeypatch.setattr(relay, "_check_media", lambda *_a, **_k: None)
    with pytest.raises(RuntimeError, match="interruption"):
        current.prepare(packet, tmp_path, out, selection, meaning)
    result = current.prepare(packet, tmp_path, out, selection, meaning)
    assert len(clips) == 1 and len(renders) == 3
    assert result["stage"] == "PRIVATE_PREPARED_REVIEW_REQUIRED"


def test_source_timing_nan_and_unbound_review_fail_closed(tmp_path):
    packet = source(tmp_path)
    packet["media"]["duration_seconds"] = float("nan")
    with pytest.raises(relay.SpeechRelayError, match="timing"):
        current.validate_source(packet, tmp_path)
    packet = source(tmp_path)
    packet["audio_review"] = dict(status="HEARD_REVIEWED")
    with pytest.raises(relay.SpeechRelayError, match="review evidence"):
        current.validate_source(packet, tmp_path)


def test_cross_selection_meaning_and_unqualified_comparison_are_rejected(tmp_path):
    packet = source(tmp_path)
    selection, meaning = returns(packet)
    meaning["selection_sha256"] = "another selected span"
    with pytest.raises(relay.SpeechRelayError, match="exact selection"):
        current.prepare(
            packet,
            tmp_path,
            tmp_path / ".task-runtime/speech_highlight_relay_v1/a",
            selection,
            meaning,
        )
    assert not (
        tmp_path / ".task-runtime/speech_highlight_relay_v1/a/meaning_return.json"
    ).exists()
    for format_name in ("WHAT_CHANGED", "CLAIM_CHECK", "QUESTION_ANSWER"):
        selection, meaning = returns(packet)
        selection["format"] = format_name
        meaning["selection_sha256"] = current.digest(selection)
        with pytest.raises(relay.SpeechRelayError, match="evidence binding"):
            current.prepare(
                packet,
                tmp_path,
                tmp_path / (".task-runtime/speech_highlight_relay_v1/" + format_name),
                selection,
                meaning,
            )


def test_source_review_must_match_exact_recording_and_transcript(tmp_path):
    packet = source(tmp_path)
    evidence = tmp_path / "heard.json"
    evidence.write_text(
        json.dumps(
            dict(
                status="HEARD_REVIEWED",
                media_sha256="another recording",
                transcript_sha256=packet["transcript"]["sha256"],
            )
        )
    )
    packet["audio_review"] = dict(
        status="HEARD_REVIEWED",
        reviewer="CONTROLLED",
        method="CONTROLLED",
        evidence=dict(file=evidence.name, sha256=relay.sha256_file(evidence)),
    )
    with pytest.raises(relay.SpeechRelayError, match="not bound"):
        current.validate_source(packet, tmp_path)


def test_discovery_cli_reuses_exact_plan_and_refuses_changed_inputs(tmp_path, capsys):
    stream = tmp_path / "stream.json"
    stream.write_text(
        json.dumps(
            [
                dict(
                    source_id="stream-1",
                    canonical_source_url="https://example.org/source",
                )
            ]
        )
    )
    out = tmp_path / ".task-runtime/speech_highlight_relay_v1/discovery"
    args = [
        "--stream-file",
        str(stream),
        "--repo-root",
        str(tmp_path),
        "--output-dir",
        str(out),
    ]
    assert current.command(args) == 0
    first = capsys.readouterr().out
    plan = out / "candidate_plan.json"
    before = (plan.read_bytes(), plan.stat().st_mtime_ns)
    assert current.command(args) == 0 and capsys.readouterr().out == first
    assert (plan.read_bytes(), plan.stat().st_mtime_ns) == before
    stream.write_text(
        json.dumps(
            [
                dict(
                    source_id="stream-2",
                    canonical_source_url="https://example.org/changed",
                )
            ]
        )
    )
    with pytest.raises(relay.SpeechRelayError, match="preserve prior plan"):
        current.command(args)
    assert plan.read_bytes() == before[0]


def test_incomplete_or_credential_bearing_source_urls_are_not_retained(tmp_path):
    for url in ("https:///source", "https://user:secret@example.org/source"):
        with pytest.raises(relay.SpeechRelayError, match="HTTPS"):
            current.candidates(
                dict(source_id="controlled", canonical_source_url=url), []
            )
