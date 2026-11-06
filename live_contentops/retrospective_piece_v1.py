"""Validate private retrospective records using the existing source/chart owners.

This module has no store, scheduler, transport or publication entry point. A valid
record establishes a dated private artifact, not public release authority.
"""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import json
import re

from live_contentops.rolling_x_grounded_article_media_builder_v1 import (
    validate_editorial_data_chart,
)

SCHEMA = "contentops.retrospective_piece.v1"
GMT7 = timezone(timedelta(hours=7))


def _time(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("RETROSPECTIVE_EXPLICIT_TIMEZONE_REQUIRED")
    return parsed


def _hash(value):
    return sha256(value).hexdigest()


def retrospective_notice(written_at_utc):
    from live_contentops.public_time_v1 import public_datetime
    local = public_datetime(written_at_utc)
    return f"Retrospective analysis, written on {local.day} {local:%B %Y} (ET)"


def validate_retrospective_piece(piece, *, documents, chart_assets, article_text):
    """Reject hindsight, unbound chart data, missing rights and false writing dates.

    The historical knowledge cutoff may follow the event's release: both clocks
    are explicit. Representation adaptation is not a factual revision. Announced
    policy settings may become effective later; realized observations may not.
    """
    if (
        piece.get("schema_version") != SCHEMA
        or piece.get("public_write_performed") is not False
    ):
        raise ValueError("RETROSPECTIVE_PRIVATE_RECORD_REQUIRED")
    event = piece["event"]
    released, cutoff = (
        _time(event["published_at_utc"]),
        _time(event["knowledge_cutoff_utc"]),
    )
    if released > cutoff or not re.fullmatch(
        r"[a-f0-9]{64}", event.get("main_event_handoff_sha256", "")
    ):
        raise ValueError("RETROSPECTIVE_EVENT_LINEAGE_REQUIRED")
    calls = piece.get("native_calls") or []
    if not calls or any(
        not c.get("invocation_id")
        or not re.fullmatch(r"[a-f0-9]{64}", c.get("request_sha256", ""))
        for c in calls
    ):
        raise ValueError("RETROSPECTIVE_ACTUAL_NATIVE_CALL_RECORD_REQUIRED")
    first_call = min(_time(c["invocation_recorded_at_utc"]) for c in calls)
    written = _time(piece["written_at_utc"])
    written_on = datetime.fromisoformat(piece["written_on_gmt7"]).date()
    if (
        written < first_call
        or written_on < first_call.astimezone(GMT7).date()
        or written_on != written.astimezone(GMT7).date()
    ):
        raise ValueError("RETROSPECTIVE_WRITTEN_BEFORE_FIRST_MODEL_CALL")
    for call in calls:
        if call.get("configuration_status") == "CONFIGURED_NOT_OBSERVED" and (
            call.get("model") is not None or call.get("reasoning_effort") is not None
        ):
            raise ValueError("RETROSPECTIVE_CONFIGURATION_IS_NOT_OBSERVATION")
    expected_notice = retrospective_notice(written)
    # Immutable dated records from before decision 90 still validate as originally sealed.
    legacy_notice = f"Retrospective analysis, written on {written_on.day} {written_on.strftime('%B %Y')} (GMT+7)"
    if written < _time("2026-11-06T06:56:00Z") and legacy_notice.casefold() in article_text.casefold():
        expected_notice = legacy_notice
    if (
        expected_notice.casefold() not in article_text.casefold()
        or "analysis, not financial advice" not in article_text.casefold()
    ):
        raise ValueError("RETROSPECTIVE_VISIBLE_NOTICE_REQUIRED")
    source_records = {s["document_id"]: s for s in piece.get("sources", [])}
    docs = {d["document_id"]: d for d in documents}
    if not source_records or set(source_records) != set(docs):
        raise ValueError("RETROSPECTIVE_EXACT_SOURCE_SET_REQUIRED")
    for identity, doc in docs.items():
        source = source_records[identity]
        known = _time(source["original_known_at_utc"])
        if (
            not _time(doc["published_at_utc"]) <= known <= cutoff
            or known != _time(doc["known_at_utc"])
            or source["capture_sha256"] != doc["raw_sha256"]
            or source["canonical_content_sha256"]
            != _hash(doc["canonical_content_text"].encode())
        ):
            raise ValueError("RETROSPECTIVE_POST_EVENT_OR_CHANGED_SOURCE")
        if (
            source.get("factual_revision_at_utc")
            and _time(source["factual_revision_at_utc"]) > cutoff
        ):
            raise ValueError("RETROSPECTIVE_POST_EVENT_FACTUAL_REVISION")
        if source.get("edition_basis") != "RETAINED_CONTEMPORANEOUS_CAPTURE":
            raise ValueError("RETROSPECTIVE_HISTORICAL_EDITION_REQUIRED")
        raw = Path(source["original_capture_path"]).read_bytes()
        if _hash(raw) != source["original_capture_sha256"]:
            raise ValueError("RETROSPECTIVE_ORIGINAL_CAPTURE_CHANGED")
        original = json.loads(raw)["value"]

        def normalize(value):
            return " ".join(value.split())

        if (
            _time(original["knownAt"]) != known
            or original["url"] != (doc.get("url") or doc.get("source_url"))
            or any(
                normalize(part) not in normalize(original["text"])
                for part in doc["canonical_content_text"].split("\n\n")
            )
        ):
            raise ValueError("RETROSPECTIVE_ORIGINAL_CAPTURE_LINEAGE_MISMATCH")
        rights = doc.get("source_reuse_constraints") or {}
        if not (
            rights.get("attribution_required")
            and rights.get("policy_capture_sha256")
            and rights.get("source_capture_sha256") == source["capture_sha256"]
        ):
            raise ValueError("RETROSPECTIVE_SOURCE_RIGHTS_REQUIRED")
        representation = Path(source["representation_capture_path"]).read_bytes()
        if (
            source.get("capture_hash_basis")
            == "VERIFIED_RENDERED_MARKDOWN_AND_CONTAINER"
        ):
            from live_contentops.contentops_source_research_v1 import _rendered

            page = _rendered(representation, doc.get("url") or doc["source_url"])
            representation_valid = (
                _hash(representation) == source["representation_capture_sha256"]
                and page["rendered_page_sha256"] == source["capture_sha256"]
                and page.get("original_capture_sha256")
                == source["original_capture_sha256"]
            )
        else:
            representation_valid = _hash(representation) == source["capture_sha256"]
        if (
            _hash(Path(source["rights_capture_path"]).read_bytes())
            != rights["policy_capture_sha256"]
            or not representation_valid
        ):
            raise ValueError("RETROSPECTIVE_CAPTURE_OR_RIGHTS_BYTES_CHANGED")
    assets = {a["asset_id"]: a for a in chart_assets}
    records = {c["asset_id"]: c for c in piece.get("charts", [])}
    if set(assets) != set(records):
        raise ValueError("RETROSPECTIVE_EXACT_CHART_SET_REQUIRED")
    if piece.get("story_kind") == "ANALYSIS" and not 2 <= len(assets) <= 5:
        raise ValueError("RETROSPECTIVE_ANALYSIS_REQUIRES_TWO_TO_FIVE_CHARTS")
    if not assets and (
        piece.get("story_kind") not in {"NEWS", "POLICY"}
        or len(piece.get("chart_exception_reason", "")) < 40
    ):
        raise ValueError("RETROSPECTIVE_SUBSTANTIVE_CHART_EXCEPTION_REQUIRED")
    for identity, asset in assets.items():
        validate_editorial_data_chart(asset, documents)
        record, packet = records[identity], asset["editorial_data_packet"]
        start, end = _time(record["window_start_utc"]), _time(record["window_end_utc"])
        if not released <= start <= end <= cutoff:
            raise ValueError("RETROSPECTIVE_CHART_POST_EVENT_WINDOW")
        series_ids = [s.get("series_id") for s in packet["series"]]
        if (
            any(not s for s in series_ids)
            or len(set(series_ids)) != len(series_ids)
            or record["series_ids"] != series_ids
        ):
            raise ValueError("RETROSPECTIVE_CHART_EXACT_SERIES_REQUIRED")
        used_docs = {
            i["document_id"]
            for s in packet["series"]
            for p in s["points"]
            for i in p["inputs"]
        }
        if record["source_capture_hashes"] != {
            d: source_records[d]["capture_sha256"] for d in sorted(used_docs)
        }:
            raise ValueError("RETROSPECTIVE_CHART_CAPTURE_BINDING_CHANGED")
        time_bindings = record["point_times"]
        expected = {
            (s["series_id"], index)
            for s in packet["series"]
            for index, _ in enumerate(s["points"])
        }
        if {
            (p["series_id"], p["point_index"]) for p in time_bindings
        } != expected or len(time_bindings) != len(expected):
            raise ValueError("RETROSPECTIVE_CHART_POINT_TIME_REQUIRED")
        series = {s["series_id"]: s for s in packet["series"]}
        for binding in time_bindings:
            point = series[binding["series_id"]]["points"][binding["point_index"]]
            latest_known = max(
                _time(source_records[i["document_id"]]["original_known_at_utc"])
                for i in point["inputs"]
            )
            if not start <= latest_known <= _time(binding["as_of_utc"]) <= end:
                raise ValueError("RETROSPECTIVE_CHART_POST_EVENT_DATA")
            if (
                _time(binding["period_end_utc"]) > cutoff
                and point["observation_kind"] != "ANNOUNCED_POLICY"
            ):
                raise ValueError("RETROSPECTIVE_CHART_FUTURE_REALIZED_OBSERVATION")
    return {
        "schema_version": SCHEMA,
        "piece_id": piece["piece_id"],
        "status": "PRIVATE_DATED_RECORD_VALIDATED",
        "chart_count": len(assets),
        "source_count": len(docs),
        "first_native_call_record_utc": first_call.isoformat(),
        "public_write_performed": False,
        "publication_authority": False,
    }
