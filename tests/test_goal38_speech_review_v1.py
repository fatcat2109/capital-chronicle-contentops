"""Controlled mechanical cases; no actual listening, rights or native review proof."""

import copy
import pytest
from live_contentops import speech_highlight_current_source_v1 as current
from live_contentops import speech_highlight_review_v1 as review
from live_contentops import speech_highlight_presentation_v1 as presentation
from live_contentops import speech_highlight_relay_v1 as relay
from test_goal37_current_speech_v1 import source, returns, configured


@pytest.fixture
def job(tmp_path, monkeypatch):
    packet = source(tmp_path)
    selection, meaning = returns(packet)
    monkeypatch.setattr(
        relay.DynamicMediaClipper,
        "extract_clip",
        lambda _s, _a, _d, p: p.write_bytes(b"clip"),
    )
    monkeypatch.setattr(relay, "probe_media", lambda _p: {})
    monkeypatch.setattr(relay, "_check_media", lambda *_a, **_kw: None)
    monkeypatch.setattr(
        relay, "_render_vertical", lambda _c, p, _s, _d, _q: p.write_bytes(b"original")
    )
    path = tmp_path / ".task-runtime/speech_highlight_relay_v1/parent"
    current.prepare(packet, tmp_path, path, selection, meaning)
    evidence = tmp_path / "observed.txt"
    evidence.write_text("CONTROLLED ONLY")
    value = dict(
        schema="contentops.signal_clips.review_return.v1",
        binding=review.review_context(path, tmp_path)["binding"],
        reviewer=dict(
            identity="controlled",
            method="CONTROLLED",
            capability="VISUAL_ONLY",
            limitations="Not actual review",
            attestation="SELF_REPORTED_NOT_INDEPENDENTLY_ATTESTED",
        ),
        findings={
            d: dict(status="NOT_VERIFIED", notes="Not reviewed")
            for d in review.DIMENSIONS
        },
    )
    value["findings"]["VISUAL"] = dict(
        status="REVISION_REQUESTED",
        notes="Controlled crop",
        evidence=[dict(file=evidence.name, sha256=relay.sha256_file(evidence))],
    )
    spec = dict(
        schema="contentops.signal_clips.revision.v1",
        parent_binding=value["binding"],
        review_sha256=current.digest(value),
        change_kind="PRESENTATION",
        reason="Controlled finding",
        presentation=dict(
            style="SOURCE_CENTRAL_PHONE_V1",
            framing_reason="Controlled",
            source_evidence_preserved="Controlled",
            shots=[dict(start_seconds=0, end_seconds=6, framing="FULL_SOURCE")],
        ),
    )
    return tmp_path, path, value, spec


def test_review_immutable_dedupe_stale_and_false_attestation(job):
    root, parent, value, _ = job
    out = root / ".task-runtime/speech_highlight_relay_v1/reviews"
    first = review.ingest_review(parent, root, value, out)
    files = {p.name: p.stat().st_mtime_ns for p in out.iterdir()}
    assert review.ingest_review(parent, root, value, out) == first
    assert files == {p.name: p.stat().st_mtime_ns for p in out.iterdir()}
    assert first["unresolved"] == list(review.DIMENSIONS)
    stale = copy.deepcopy(value)
    stale["binding"]["edit_sha256"] = "stale"
    with pytest.raises(relay.SpeechRelayError, match="Stale"):
        review.ingest_review(parent, root, stale, out)
    false = copy.deepcopy(value)
    false["reviewer"]["attestation"] = "INDEPENDENTLY_VERIFIED"
    with pytest.raises(relay.SpeechRelayError, match="attestation"):
        review.ingest_review(parent, root, false, out)
    false = copy.deepcopy(value)
    false["findings"]["AUDIO"] = dict(
        false["findings"]["VISUAL"], status="PASS", method="ASR_TEXT"
    )
    with pytest.raises(relay.SpeechRelayError, match="not audio"):
        review.ingest_review(parent, root, false, out)
    false = copy.deepcopy(value)
    false["findings"]["VISUAL"]["evidence"][0]["sha256"] = "wrong"
    with pytest.raises(relay.SpeechRelayError):
        review.ingest_review(parent, root, false, out)


def test_presentation_recovery_reuses_native_clip_and_rereview_binding(
    job, monkeypatch
):
    root, parent, value, spec = job
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in parent.iterdir()}
    out = root / ".task-runtime/speech_highlight_relay_v1/successor"
    calls = []

    def render(_clip, p, _s, _m, _d, _plan, cues):
        calls.append(p.name)
        p.write_bytes(b"new" + str(bool(cues)).encode())
        if len(calls) == 2:
            raise RuntimeError("CONTROLLED INTERRUPTION")

    monkeypatch.setattr(presentation, "render", render)
    with pytest.raises(RuntimeError, match="INTERRUPTION"):
        review.revise(parent, root, out, spec, value)
    result = review.revise(parent, root, out, spec, value)
    assert len(calls) == 3  # sealed clean reused on resume
    assert "extracted_clip.mp4" in result["reused_stages"]
    assert "meaning_return.json" in result["reused_stages"]
    assert (
        result["file_hashes"]["extracted_clip.mp4"]
        == value["binding"]["affected_outputs"]["extracted_clip.mp4"]
    )
    assert review.revise(parent, root, out, spec, value) == result and len(calls) == 3
    assert before == {
        p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in parent.iterdir()
    }
    with pytest.raises(relay.SpeechRelayError, match="Stale"):
        review.ingest_review(
            out, root, value, root / ".task-runtime/speech_highlight_relay_v1/stale"
        )
    revised = copy.deepcopy(value)
    revised["binding"] = review.review_context(out, root)["binding"]
    revised["findings"]["VISUAL"]["status"] = "PASS"
    assert review.ingest_review(
        out, root, revised, root / ".task-runtime/speech_highlight_relay_v1/rereview"
    )["unresolved"] == list(review.DIMENSIONS[1:])
    surface = review.review_entry(
        out, root, root / ".task-runtime/speech_highlight_relay_v1/surface", [revised]
    )
    text = __import__("pathlib").Path(surface["path"]).read_text()
    assert (
        "15 seconds before + after" in text
        and "source_uri" in text
        and "NOT_VERIFIED" in text
    )


def test_caption_and_semantic_descendants_and_unreviewed_mutations(job, monkeypatch):
    root, parent, value, spec = job
    for kind, dimension in (("CAPTIONS", "CAPTIONS"), ("SEMANTIC", "CONTEXT")):
        v = copy.deepcopy(value)
        v["findings"][dimension] = copy.deepcopy(v["findings"]["VISUAL"])
        s = dict(spec, change_kind=kind, review_sha256=current.digest(v))
        s.pop("presentation")
        if kind == "CAPTIONS":
            cues = review.read(parent / "captions.json")
            cues[0]["end_seconds"] = 5.5
            s["cues"] = cues
        else:
            m = review.read(parent / "meaning_return.json")
            m["native_turn_id"] = "CONTROLLED_FRESH_ROLE"
            m["headline"] = "Corrected bounded context"
            s["meaning_return"] = m
        out = root / (".task-runtime/speech_highlight_relay_v1/" + kind)
        calls = []
        monkeypatch.setattr(
            relay,
            "_render_vertical",
            lambda _c, p, _s, _d, q: (
                calls.append(p.name),
                p.write_bytes(b"controlled correction"),
            ),
        )
        result = review.revise(parent, root, out, s, v)
        assert len(calls) == (1 if kind == "CAPTIONS" else 2)
        if kind == "CAPTIONS":
            assert (
                result["file_hashes"][relay.ARTIFACT_FILES["clean_master"]]
                == value["binding"]["affected_outputs"][
                    relay.ARTIFACT_FILES["clean_master"]
                ]
            )
        assert (
            result["production_eligible"] is False
            and "MEDIA_REVIEW" in result["invalidated_stages"]
        )
    bad = copy.deepcopy(spec)
    bad["cues"] = []
    with pytest.raises(relay.SpeechRelayError, match="Unexpected caption"):
        review.revise(
            parent,
            root,
            root / ".task-runtime/speech_highlight_relay_v1/bad",
            bad,
            value,
        )
    with pytest.raises(relay.SpeechRelayError, match="wording correction"):
        review.validate_cues(
            [
                dict(
                    cue_id="0",
                    start_seconds=0,
                    end_seconds=6,
                    text="We claim certainty.",
                )
            ],
            6,
            "We do not claim certainty.",
        )


def test_phone_text_files_keep_lf_to_match_measured_bounds(job, monkeypatch):
    root, parent, _, spec = job
    packet = review.read(parent / "current_source.json")
    meaning = review.read(parent / "meaning_return.json")
    monkeypatch.setattr(
        relay,
        "probe_media",
        lambda _p: {"streams": [dict(codec_type="video", width=960, height=540)]},
    )
    monkeypatch.setattr(relay, "_font", lambda *_a: root / "font.ttf")
    measured = []
    monkeypatch.setattr(
        relay,
        "_wrapped",
        lambda *args: (measured.append(args[0]), "first line\nsecond line")[1],
    )
    meaning["context"] = "Line one\nLine two\nLine three\nEssential qualifier remains"
    commands = []
    monkeypatch.setattr(relay, "_run_local", lambda cmd, **_kw: commands.append(cmd))
    presentation.render(
        parent / "extracted_clip.mp4",
        parent / "controlled-render.mp4",
        packet,
        meaning,
        6,
        spec["presentation"],
        None,
    )
    assert (parent / "phone_hook.txt").read_bytes() == b"first line\nsecond line"
    assert "Line one Line two Line three Essential qualifier remains" in measured
    assert commands and commands[0][commands[0].index("-c:a") + 1] == "copy"


def test_semantic_revision_accepts_labelled_configured_max_and_keeps_open_audio(job, monkeypatch):
    root, parent, value, _ = job
    value["findings"]["CONTEXT"] = dict(value["findings"]["VISUAL"],
        notes="Controlled context correction")
    meaning = configured(review.read(parent / "meaning_return.json"))
    meaning.update(native_turn_id="CONTROLLED_NEW_MAX_TURN", context="Controlled revised context")
    spec = dict(schema="contentops.signal_clips.revision.v1",
        parent_binding=value["binding"], review_sha256=current.digest(value),
        change_kind="SEMANTIC", reason="Controlled source-bound correction", meaning_return=meaning)
    result = review.revise(parent, root,
        root / ".task-runtime/speech_highlight_relay_v1/configured-successor", spec, value)
    assert result["production_eligible"] is False
    assert result["publication_control"]["public_writes"] == 0
    saved = review.read(root / ".task-runtime/speech_highlight_relay_v1/configured-successor/meaning_return.json")
    assert saved["model"] is None and saved["configured_reasoning_effort"] == "max"
