from __future__ import annotations

import re
import unicodedata
from typing import Any, Mapping, Sequence

from .creative import hash_value


TRANSCRIPT_SCHEMA = "contentops.v2.canonical_spoken_transcript.v1"
VOICEOVER_QA_SCHEMA = "contentops.v2.transcript_voiceover_qa.v1"
SEO_SCHEMA = "contentops.v2.transcript_derived_seo_package.v1"
RETENTION_WINDOW_SECONDS = 30.0
_NEGATIONS = frozenset(
    {"no", "not", "never", "without", "neither", "nor", "cannot", "can't", "won't"}
)
_TITLE_STOP_WORDS = frozenset(
    {"a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "with"}
)


class TranscriptContractError(RuntimeError):
    pass


def _normalized(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    value = value.replace("−", "-").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", value).strip()


def _meaningful_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", _normalized(value))
        if token not in _TITLE_STOP_WORDS
    }


def _pronunciation_notes(segment: Mapping[str, Any]) -> list[dict[str, str]]:
    notes = segment.get("pronunciation_notes", [])
    if not isinstance(notes, list):
        raise TranscriptContractError("pronunciation_notes_not_list")
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    text = str(segment.get("text", ""))
    for note in notes:
        if not isinstance(note, Mapping):
            raise TranscriptContractError("pronunciation_note_not_object")
        surface = str(note.get("surface", "")).strip()
        spoken_as = str(note.get("spoken_as", "")).strip()
        if (
            not surface
            or surface not in text
            or surface in seen
            or not spoken_as
            or len(spoken_as) > 100
            or re.search(r"[\x00-\x1f\x7f]", spoken_as)
        ):
            raise TranscriptContractError("pronunciation_note_invalid")
        if re.search(r"\d", spoken_as):
            raise TranscriptContractError("pronunciation_spoken_form_must_spell_numbers")
        seen.add(surface)
        normalized.append({"surface": surface, "spoken_as": spoken_as})
    return normalized


def synthesis_text_for_segment(segment: Mapping[str, Any]) -> str:
    text = str(segment.get("text", ""))
    notes = _pronunciation_notes(segment)
    for note in sorted(notes, key=lambda item: len(item["surface"]), reverse=True):
        text = text.replace(note["surface"], note["spoken_as"])
    return text


def validate_editor_transcript_fields(editor: Mapping[str, Any]) -> dict[str, Any]:
    segments = editor.get("narration_segments")
    if not isinstance(segments, list) or not segments:
        raise TranscriptContractError("narration_segments_missing")
    seen_text: set[str] = set()
    segment_ids: set[str] = set()
    changed: list[str] = []
    for segment in segments:
        segment_id = str(segment.get("segment_id", ""))
        text = str(segment.get("text", "")).strip()
        normalized_text = _normalized(text)
        if not text or not re.search(r"[A-Za-z0-9]", text):
            raise TranscriptContractError(f"garbled_or_empty_segment:{segment_id}")
        if "\ufffd" in text or re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", text):
            raise TranscriptContractError(f"garbled_or_empty_segment:{segment_id}")
        if normalized_text in seen_text:
            raise TranscriptContractError(f"duplicate_spoken_segment:{segment_id}")
        seen_text.add(normalized_text)
        segment_ids.add(segment_id)
        synthesis_text = synthesis_text_for_segment(segment)
        if synthesis_text != text:
            changed.append(segment_id)

    retention = editor.get("retention_contract")
    if not isinstance(retention, Mapping):
        raise TranscriptContractError("retention_contract_missing")
    promise_ids = [str(value) for value in retention.get("promise_segment_ids", [])]
    payoff_ids = [str(value) for value in retention.get("payoff_segment_ids", [])]
    if (
        not promise_ids
        or not payoff_ids
        or not set(promise_ids).issubset(segment_ids)
        or not set(payoff_ids).issubset(segment_ids)
    ):
        raise TranscriptContractError("retention_contract_segment_binding_invalid")

    full_text = " ".join(str(item["text"]) for item in segments)
    entities = editor.get("search_entities")
    if not isinstance(entities, list) or not entities:
        raise TranscriptContractError("search_entities_missing")
    seen_entities: set[str] = set()
    for entity in entities:
        surface = str(entity).strip()
        key = _normalized(surface)
        if not surface or surface not in full_text or key in seen_entities:
            raise TranscriptContractError("search_entity_not_exact_transcript_surface")
        seen_entities.add(key)

    title = str(editor.get("title", "")).strip()
    if not title or not _meaningful_tokens(title).issubset(_meaningful_tokens(full_text)):
        raise TranscriptContractError("title_not_transcript_derived")
    return {
        "result": "PASS_EDITOR_TRANSCRIPT_FIELDS",
        "changed_pronunciation_segment_ids": changed,
        "search_entity_count": len(entities),
        "retention_promise_segment_ids": promise_ids,
        "retention_payoff_segment_ids": payoff_ids,
    }


def build_canonical_spoken_transcript(
    *,
    video_job_id: str,
    run_id: str,
    governed_input_hash: str,
    editor: Mapping[str, Any],
    placements: Sequence[Mapping[str, Any]],
    locked_narration_audio: Mapping[str, Any],
) -> dict[str, Any]:
    validate_editor_transcript_fields(editor)
    authored = list(editor["narration_segments"])
    if len(authored) != len(placements):
        raise TranscriptContractError("transcript_placement_count_mismatch")
    segments: list[dict[str, Any]] = []
    for ordinal, (segment, placement) in enumerate(zip(authored, placements), start=1):
        segment_id = str(segment["segment_id"])
        text = str(segment["text"])
        synthesis_text = synthesis_text_for_segment(segment)
        if placement.get("segment_id") != segment_id:
            raise TranscriptContractError("transcript_placement_identity_mismatch")
        if placement.get("segment_text_sha256") != hash_value(text):
            raise TranscriptContractError("transcript_placement_text_hash_mismatch")
        if placement.get("synthesis_text_sha256") != hash_value(synthesis_text):
            raise TranscriptContractError("transcript_synthesis_text_hash_mismatch")
        segments.append(
            {
                "ordinal": ordinal,
                "segment_id": segment_id,
                "kind": str(segment["kind"]),
                "text": text,
                "segment_text_sha256": hash_value(text),
                "synthesis_text": synthesis_text,
                "synthesis_text_sha256": hash_value(synthesis_text),
                "pronunciation_notes": _pronunciation_notes(segment),
                "anchor_ids": [str(value) for value in segment.get("anchor_ids", [])],
                "analysis_id": str(segment.get("analysis_id", "")),
                "cue_id": str(placement["cue_id"]),
                "timeline_start_seconds": float(placement["timeline_start_seconds"]),
                "actual_audio_duration_seconds": float(
                    placement["actual_audio_duration_seconds"]
                ),
                "timeline_end_seconds": float(placement["timeline_end_seconds"]),
                "pause_after_seconds": float(placement["pause_after_seconds"]),
                "caption_text": text,
                "audio_path": str(placement["audio_path"]),
                "audio": dict(placement["audio"]),
                "synthesis_action": str(placement.get("synthesis_action", "UNKNOWN")),
            }
        )
    plain_text = " ".join(item["text"] for item in segments)
    payload = {
        "schema": TRANSCRIPT_SCHEMA,
        "video_job_id": video_job_id,
        "run_id": run_id,
        "governed_input_hash": governed_input_hash,
        "editorial_narration_hash": hash_value(editor),
        "plain_text": plain_text,
        "plain_text_sha256": hash_value(plain_text),
        "locked_narration_audio_sha256": str(locked_narration_audio["sha256"]),
        "segments": segments,
    }
    payload["canonical_transcript_hash"] = hash_value(payload)
    return payload


def _critical_terms(segments: Sequence[Mapping[str, Any]]) -> dict[str, list[dict[str, str]]]:
    results: dict[str, list[dict[str, str]]] = {
        "names_institutions": [],
        "numbers_units_currencies": [],
        "dates": [],
        "negations": [],
        "acronyms": [],
    }
    seen: set[tuple[str, str, str]] = set()
    month = (
        r"(?:January|February|March|April|May|June|July|August|September|October|"
        r"November|December)\s+\d{1,2}(?:,\s+\d{4})?"
    )
    for segment in segments:
        segment_id = str(segment["segment_id"])
        text = str(segment["text"])
        matches = {
            "numbers_units_currencies": re.findall(
                r"(?:[$€£¥]\s*)?\d[\d,]*(?:\.\d+)?(?:\s*(?:%|percent|basis points?|"
                r"million|billion|trillion|thousand|dollars?|euros?|pounds?|yen|weeks?|months?|years?))?",
                text,
                flags=re.I,
            ),
            "dates": re.findall(month, text),
            "negations": [
                value
                for value in re.findall(r"\b[A-Za-z']+\b", text)
                if value.casefold() in _NEGATIONS
            ],
            "acronyms": re.findall(r"\b(?:[A-Z]{2,}|(?:[A-Z]\.){2,})\b", text),
            "names_institutions": re.findall(
                r"\b(?:[A-Z][A-Za-z&.-]+(?:\s+[A-Z][A-Za-z&.-]+){1,5})\b", text
            ),
        }
        for kind, surfaces in matches.items():
            for surface in surfaces:
                key = (kind, segment_id, surface)
                if key in seen:
                    continue
                seen.add(key)
                results[kind].append({"segment_id": segment_id, "surface": surface})
    return results


def validate_canonical_spoken_transcript(
    transcript: Mapping[str, Any],
    *,
    video_job_id: str,
    run_id: str,
    governed_input_hash: str,
    editor: Mapping[str, Any],
    locked_narration_audio: Mapping[str, Any],
) -> dict[str, Any]:
    if transcript.get("schema") != TRANSCRIPT_SCHEMA:
        raise TranscriptContractError("canonical_transcript_schema_invalid")
    for key, expected in {
        "video_job_id": video_job_id,
        "run_id": run_id,
        "governed_input_hash": governed_input_hash,
        "editorial_narration_hash": hash_value(editor),
        "locked_narration_audio_sha256": str(locked_narration_audio["sha256"]),
    }.items():
        if transcript.get(key) != expected:
            raise TranscriptContractError(f"canonical_transcript_identity_mismatch:{key}")
    segments = transcript.get("segments")
    if not isinstance(segments, list) or len(segments) != len(editor["narration_segments"]):
        raise TranscriptContractError("canonical_transcript_segment_count_mismatch")
    for observed, authored in zip(segments, editor["narration_segments"]):
        if observed.get("segment_id") != authored.get("segment_id"):
            raise TranscriptContractError("canonical_transcript_segment_identity_mismatch")
        text = str(authored["text"])
        synthesis_text = synthesis_text_for_segment(authored)
        if (
            observed.get("text") != text
            or observed.get("caption_text") != text
            or observed.get("segment_text_sha256") != hash_value(text)
            or observed.get("synthesis_text") != synthesis_text
            or observed.get("synthesis_text_sha256") != hash_value(synthesis_text)
        ):
            raise TranscriptContractError(
                f"canonical_transcript_segment_text_mismatch:{authored['segment_id']}"
            )
        audio = observed.get("audio")
        if not isinstance(audio, Mapping) or not str(audio.get("sha256", "")):
            raise TranscriptContractError("canonical_transcript_segment_audio_missing")
    plain_text = " ".join(str(item["text"]) for item in segments)
    if (
        transcript.get("plain_text") != plain_text
        or transcript.get("plain_text_sha256") != hash_value(plain_text)
    ):
        raise TranscriptContractError("canonical_transcript_plain_text_mismatch")
    unsigned = dict(transcript)
    observed_hash = str(unsigned.pop("canonical_transcript_hash", ""))
    if not observed_hash or hash_value(unsigned) != observed_hash:
        raise TranscriptContractError("canonical_transcript_hash_mismatch")
    return {
        "result": "PASS_CANONICAL_SPOKEN_TRANSCRIPT",
        "canonical_transcript_hash": observed_hash,
        "segment_count": len(segments),
    }


def build_voiceover_qa(
    *, transcript: Mapping[str, Any], editor: Mapping[str, Any]
) -> dict[str, Any]:
    segments = list(transcript["segments"])
    validation = validate_editor_transcript_fields(editor)
    terms = _critical_terms(segments)
    failures: list[str] = []
    changed: list[str] = []
    synthesized: list[str] = []
    reused: list[str] = []
    for segment in segments:
        segment_id = str(segment["segment_id"])
        synthesis_text = str(segment["synthesis_text"])
        notes = {
            str(item["surface"]): str(item["spoken_as"])
            for item in segment.get("pronunciation_notes", [])
        }
        if synthesis_text != str(segment["text"]):
            changed.append(segment_id)
        action = str(segment.get("synthesis_action", "UNKNOWN"))
        if action == "SYNTHESIZED":
            synthesized.append(segment_id)
        elif action == "REUSED_CACHE":
            reused.append(segment_id)
        for kind, records in terms.items():
            for record in records:
                if record["segment_id"] != segment_id:
                    continue
                surface = record["surface"]
                if surface not in synthesis_text and surface not in notes:
                    failures.append(f"{segment_id}:{kind}:{surface}")
    payoff_ids = set(validation["retention_payoff_segment_ids"])
    payoff_ends = [
        float(segment["timeline_end_seconds"])
        for segment in segments
        if segment["segment_id"] in payoff_ids
    ]
    if not payoff_ends or min(payoff_ends) > RETENTION_WINDOW_SECONDS + 0.001:
        failures.append("retention_payoff_outside_first_30_seconds")
    payload = {
        "schema": VOICEOVER_QA_SCHEMA,
        "canonical_transcript_hash": transcript["canonical_transcript_hash"],
        "result": "PASS_TRANSCRIPT_VOICEOVER_QA" if not failures else "FAIL_TRANSCRIPT_VOICEOVER_QA",
        "missing_duplicate_garbled_segment_failures": [],
        "critical_terms": terms,
        "critical_term_count": sum(len(values) for values in terms.values()),
        "pronunciation_changed_segment_ids": changed,
        "synthesized_segment_ids": synthesized,
        "reused_cached_segment_ids": reused,
        "retention_promise_segment_ids": validation["retention_promise_segment_ids"],
        "retention_payoff_segment_ids": validation["retention_payoff_segment_ids"],
        "first_30_seconds_payoff_confirmed": not any(
            item == "retention_payoff_outside_first_30_seconds" for item in failures
        ),
        "failures": failures,
    }
    payload["voiceover_qa_hash"] = hash_value(payload)
    if failures:
        raise TranscriptContractError("voiceover_qa_failed:" + ",".join(failures))
    return payload


def build_transcript_derived_seo(
    *, transcript: Mapping[str, Any], editor: Mapping[str, Any]
) -> dict[str, Any]:
    validate_editor_transcript_fields(editor)
    segments = list(transcript["segments"])
    title = str(editor["title"]).strip()
    description_parts: list[str] = []
    for segment in segments:
        candidate = " ".join([*description_parts, str(segment["text"])])
        if len(candidate) > 320 and description_parts:
            break
        description_parts.append(str(segment["text"]))
        if len(" ".join(description_parts)) >= 160:
            break
    description = " ".join(description_parts)
    chapters = []
    for segment in segments:
        words = str(segment["text"]).split()
        chapters.append(
            {
                "segment_id": segment["segment_id"],
                "start_seconds": float(segment["timeline_start_seconds"]),
                "title": " ".join(words[:8]),
            }
        )
    payload = {
        "schema": SEO_SCHEMA,
        "canonical_transcript_hash": transcript["canonical_transcript_hash"],
        "derivation_basis": "CANONICAL_SPOKEN_TRANSCRIPT_EXACT_SURFACES_ONLY",
        "title": title,
        "description": description,
        "chapters": chapters,
        "search_entities": [str(value) for value in editor["search_entities"]],
        "invented_or_strengthened_fact_count": 0,
    }
    payload["seo_package_hash"] = hash_value(payload)
    return payload


def validate_transcript_derived_seo(
    seo: Mapping[str, Any], *, transcript: Mapping[str, Any], editor: Mapping[str, Any]
) -> dict[str, Any]:
    expected = build_transcript_derived_seo(transcript=transcript, editor=editor)
    if dict(seo) != expected:
        raise TranscriptContractError("seo_not_deterministically_transcript_derived")
    return {
        "result": "PASS_TRANSCRIPT_DERIVED_SEO",
        "seo_package_hash": expected["seo_package_hash"],
        "search_entity_count": len(expected["search_entities"]),
        "chapter_count": len(expected["chapters"]),
    }


def validate_seo_transcript_identity(
    seo: Mapping[str, Any], *, transcript: Mapping[str, Any]
) -> dict[str, Any]:
    if seo.get("schema") != SEO_SCHEMA:
        raise TranscriptContractError("seo_schema_invalid")
    if seo.get("canonical_transcript_hash") != transcript.get(
        "canonical_transcript_hash"
    ):
        raise TranscriptContractError("seo_transcript_hash_mismatch")
    unsigned = dict(seo)
    observed_hash = str(unsigned.pop("seo_package_hash", ""))
    if not observed_hash or hash_value(unsigned) != observed_hash:
        raise TranscriptContractError("seo_package_hash_mismatch")
    if int(seo.get("invented_or_strengthened_fact_count", -1)) != 0:
        raise TranscriptContractError("seo_invented_or_strengthened_fact")
    plain_text = str(transcript.get("plain_text", ""))
    if not _meaningful_tokens(str(seo.get("title", ""))).issubset(
        _meaningful_tokens(plain_text)
    ):
        raise TranscriptContractError("seo_title_not_transcript_derived")
    if str(seo.get("description", "")) not in plain_text:
        raise TranscriptContractError("seo_description_not_exact_transcript_surface")
    segments = {
        str(item["segment_id"]): item for item in transcript.get("segments", [])
    }
    chapters = seo.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        raise TranscriptContractError("seo_chapters_missing")
    for chapter in chapters:
        segment = segments.get(str(chapter.get("segment_id", "")))
        if segment is None:
            raise TranscriptContractError("seo_chapter_segment_missing")
        if (
            str(chapter.get("title", "")) not in str(segment["text"])
            or abs(
                float(chapter.get("start_seconds", -1))
                - float(segment["timeline_start_seconds"])
            )
            > 0.00001
        ):
            raise TranscriptContractError("seo_chapter_not_transcript_derived")
    entities = seo.get("search_entities")
    if not isinstance(entities, list) or not entities or any(
        str(entity) not in plain_text for entity in entities
    ):
        raise TranscriptContractError("seo_search_entity_not_transcript_derived")
    return {
        "result": "PASS_SEO_TRANSCRIPT_IDENTITY",
        "seo_package_hash": observed_hash,
        "canonical_transcript_hash": transcript["canonical_transcript_hash"],
    }
