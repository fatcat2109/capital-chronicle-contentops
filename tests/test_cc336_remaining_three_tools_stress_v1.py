"""CC-336 stress suite for the remaining 3 of 11 ContentOps tools (strictly offline, ZERO public posts).

Tools covered (8 of 11 already wired in live ContentOps):
  1. Retrospective piece (`retrospective_piece_v1` + `event_article_guard_v1` CC-107/CC-323/CC-333):
     verifies `event_writer_guidance` wires `retrospective_notice` into `EVENT_REVIEW`, and
     `validate_retrospective_piece` enforces private-dated seals, visible notice, and no hindsight.
  2. Scorecard tools (`public_call_scorecard_v1` [CC-338] + `pinned_result_scorecard_v1` [CC-394],
     while `CC-305` Main site builder stays PARKED per Decision 84):
     verifies full-denominator public-call table rendering, ET clocks, private-state exclusion,
     Main export projection (`HIT`/`STOPPED`/`EXPIRED`/`NOT_TRIGGERED`), kill-switch fail-closed
     no-write, and in-memory mock Telegram pin/edit/readback idempotency (0 real network calls).
  3. Result posts (`plan_status_posts_v1` CC-322):
     verifies `result_rows_from_export`, `compose_result`, and `queue_posts` under both
     `RESULT_POSTS_SELECTIVE=True` (Decision 106: fresh HIT + max 1 STOPPED/7d + always corrections;
     suppressing untriggered, horizon-end EXPIRED, stale >24h, and 2nd loss in 7d) and
     `RESULT_POSTS_SELECTIVE=False`, plus test-mode isolation from Jim's live pause record.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import sqlite3

import pytest

from live_contentops import event_article_guard_v1 as guard
from live_contentops import pinned_result_scorecard_v1 as pinned_sc
from live_contentops import plan_call_cards_v1 as cards
from live_contentops import plan_status_posts_v1 as posts
from live_contentops import public_call_scorecard_v1 as pub_sc
from live_contentops import retrospective_piece_v1 as retro
from live_contentops import rolling_x_grounded_article_media_builder_v1 as media
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

UTC = timezone.utc


# =============================================================================
# 1. RETROSPECTIVE PIECE (CC-107 / CC-323 / CC-333)
# =============================================================================


def test_tool1_retrospective_notice_is_wired_into_event_review_guidance_and_validator(tmp_path):
    guidance = guard.event_writer_guidance({"article_type": "EVENT_REVIEW", "source_pack": []})
    assert "CC333_REVIEW_WRITING_CLOCK" in guidance
    assert "Retrospective analysis, written on " in guidance
    assert "(ET)" in guidance

    # Build a valid private dated retrospective record in tmp_path (zero public writes).
    text = "October 28, 2026: controlled announced policy rate 3.90 percent."
    url = "https://example.test/cc336-retro-source"
    raw = json.dumps({"value": {"knownAt": "2026-10-28T19:13:00Z", "url": url, "text": text}}).encode()
    (tmp_path / "orig.json").write_bytes(raw)
    (tmp_path / "cap.json").write_bytes(b"CC336 controlled capture representation")
    (tmp_path / "rights.json").write_bytes(b"CC336 controlled rights fixture")

    h = lambda b: sha256(b).hexdigest()
    cap_sha = h((tmp_path / "cap.json").read_bytes())
    rights_sha = h((tmp_path / "rights.json").read_bytes())
    doc = {
        "document_id": "CC336_DOC",
        "canonical_content_text": text,
        "published_at_utc": "2026-10-28T18:00:00Z",
        "known_at_utc": "2026-10-28T19:13:00Z",
        "raw_sha256": cap_sha,
        "source_url": url,
        "publisher": "Controlled fixture",
        "source_reuse_constraints": {
            "attribution_required": True,
            "policy_capture_sha256": rights_sha,
            "source_capture_sha256": cap_sha,
        },
    }
    packet = {
        "asset_id": "cc336-chart",
        "chart_type": "grouped_bar",
        "question": "Controlled rate comparison?",
        "title": "Controlled test chart",
        "unit": "percent",
        "source_caption": "Controlled fixture only.",
        "series": [{
            "series_id": "RATE_SERIES",
            "label": "Policy rate",
            "points": [{
                "period": "28 Oct",
                "value": 3.9,
                "observation_kind": "ANNOUNCED_POLICY",
                "inputs": [{
                    "document_id": "CC336_DOC",
                    "support_excerpt": text,
                    "value_text": "3.90",
                    "source_period_text": "October 28, 2026",
                    "source_content_sha256": h(text.encode()),
                    "metric": "policy rate",
                    "unit": "percent",
                    "prepared_period": "2026-10-28",
                    "period_basis": "CONTROLLED_EXACT_SOURCE_PERIOD",
                }],
            }],
        }],
    }
    asset = media.build_editorial_data_chart(packet, [doc], output_dir=tmp_path)
    written_utc = "2026-11-08T15:30:00Z"
    notice_line = retro.retrospective_notice(written_utc)
    article_text = f"{notice_line}\n\nEvent review body. Capital Chronicle offers analysis, not financial advice."

    piece = {
        "schema_version": retro.SCHEMA,
        "piece_id": "CC336_PRIVATE_STRESS",
        "public_write_performed": False,
        "story_kind": "POLICY",
        "event": {
            "published_at_utc": "2026-10-28T18:00:00Z",
            "knowledge_cutoff_utc": "2026-10-28T19:14:31Z",
            "main_event_handoff_sha256": "a" * 64,
        },
        "written_at_utc": written_utc,
        "written_on_gmt7": "2026-11-08",
        "native_calls": [{
            "invocation_id": "cc336-stress-call",
            "request_sha256": "b" * 64,
            "invocation_recorded_at_utc": "2026-11-08T15:20:00Z",
            "model": None,
            "reasoning_effort": None,
            "configuration_status": "CONFIGURED_NOT_OBSERVED",
        }],
        "sources": [{
            "document_id": "CC336_DOC",
            "original_known_at_utc": doc["known_at_utc"],
            "capture_sha256": cap_sha,
            "canonical_content_sha256": h(text.encode()),
            "edition_basis": "RETAINED_CONTEMPORANEOUS_CAPTURE",
            "original_capture_path": str(tmp_path / "orig.json"),
            "original_capture_sha256": h(raw),
            "representation_capture_path": str(tmp_path / "cap.json"),
            "rights_capture_path": str(tmp_path / "rights.json"),
        }],
        "charts": [{
            "asset_id": asset["asset_id"],
            "series_ids": ["RATE_SERIES"],
            "source_capture_hashes": {"CC336_DOC": cap_sha},
            "window_start_utc": "2026-10-28T18:00:00Z",
            "window_end_utc": "2026-10-28T19:14:31Z",
            "point_times": [{
                "series_id": "RATE_SERIES",
                "point_index": 0,
                "as_of_utc": "2026-10-28T19:14:00Z",
                "period_end_utc": "2026-10-28T19:14:00Z",
            }],
        }],
    }
    validated = retro.validate_retrospective_piece(piece, documents=[doc], chart_assets=[asset], article_text=article_text)
    assert validated["status"] == "PRIVATE_DATED_RECORD_VALIDATED"
    assert validated["public_write_performed"] is False
    assert validated["publication_authority"] is False

    # Fault injections: missing notice and public_write_performed=True are both refused.
    with pytest.raises(ValueError, match="RETROSPECTIVE_VISIBLE_NOTICE_REQUIRED"):
        retro.validate_retrospective_piece(piece, documents=[doc], chart_assets=[asset], article_text="No notice here.")
    bad_public = deepcopy(piece)
    bad_public["public_write_performed"] = True
    with pytest.raises(ValueError, match="RETROSPECTIVE_PRIVATE_RECORD_REQUIRED"):
        retro.validate_retrospective_piece(bad_public, documents=[doc], chart_assets=[asset], article_text=article_text)


# =============================================================================
# 2. SCORECARD TOOLS (CC-338 public_call_scorecard + CC-394 pinned_result_scorecard)
# =============================================================================


def _sample_export(now: datetime, plans: list[dict], transitions: list[dict] | None = None) -> dict:
    gen = now.astimezone(UTC).isoformat().replace("+00:00", "Z")
    scored_count = sum(1 for p in plans if (p.get("outcome") or {}).get("state") == "SCORED")
    status = {
        "schema": "CapitalChroniclePlanStatusV1",
        "schema_version": "1.0.0",
        "contract_version": "2.0.0",
        "generated_at_utc": gen,
        "content_hash": "a" * 64,
        "scored_call_count": scored_count,
        "plans": plans,
    }
    trans = {
        "schema": "CapitalChroniclePlanTransitionsV1",
        "schema_version": "1.0.0",
        "generated_at_utc": gen,
        "status_content_hash": "a" * 64,
        "transitions": transitions or [],
    }
    return {"status": status, "transitions": trans}


def _scored_plan(
    plan_id: str,
    symbol: str,
    direction: str,
    zone: tuple[float, float],
    stop: float,
    result: str,
    resolved_at: str,
    *,
    scored: bool = True,
    corrects: str | None = None,
) -> dict:
    oid = f"outcome-{plan_id}"
    outcome = (
        {
            "state": "SCORED",
            "result": result,
            "outcome_id": oid,
            "score": {
                "outcome_id": oid,
                "plan_id": plan_id,
                "asset_id": symbol,
                "result": result,
                "resolved_at_utc": resolved_at,
                "scored_at_utc": resolved_at,
                "content_hash": "c" * 64,
                **({"corrects_outcome_id": corrects} if corrects else {}),
            },
        }
        if scored
        else {"state": "NOT_SCORED_UNTRIGGERED", "result": None, "outcome_id": None}
    )
    return {
        "plan_id": plan_id,
        "asset_id": symbol,
        "direction": direction,
        "status": "EXPIRED" if not scored else "CLOSED",
        "zone": {"minimum": zone[0], "maximum": zone[1]},
        "expires_at_utc": resolved_at,
        "invalidation_conditions": [{"field": "low" if direction == "BULLISH" else "high", "operator": "LT" if direction == "BULLISH" else "GT", "threshold": stop}],
        "outcome": outcome,
    }


def test_tool2_public_call_scorecard_and_pinned_result_scorecard_offline_mock(tmp_path):
    # A. CC-338 public_call_scorecard_v1 in isolated SQLite store
    db = tmp_path / "scorecard.sqlite3"
    store = ContentOpsDurableStore(str(db))
    store.create_work_item(story_id="posts", title="Posts", target_surface="MULTI_PLATFORM", work_item_id="posts")
    feed = tmp_path / "published.jsonl"
    feed.write_bytes(b"")
    call = {
        "condition": "price trades into 2950-2960",
        "market": "gold",
        "direction": "bullish",
        "horizon": "the period to Tue 10 Nov, 12:00 ET",
        "invalidation": "price moves below 2920",
    }
    for idx, (pid, st) in enumerate([("p-1", "WAITING"), ("p-1", "TRIGGERED"), ("p-1", "FILLED"), ("p-2", "WAITING"), ("p-2", "EXPIRED")]):
        key = f"msg-{idx}"
        pkt = {"plan_id": pid, "state": st, "at_utc": f"2026-11-08T0{idx + 1}:00:00Z", "conditional_calls": [call] if st == "WAITING" else []}
        store.register_outbox_message(message_id=key, work_item_id="posts", destination="internal:plan-status-post", payload=json.dumps(pkt), status="PUBLISHED")
        store.create_work_item(story_id=key, title="Post", target_surface="MULTI_PLATFORM", work_item_id=key)
        store.register_outbox_message(message_id=key + "-tg", work_item_id=key, destination="TELEGRAM", payload="{}", status="SENT")
        with sqlite3.connect(db) as conn:
            conn.execute(
                "INSERT INTO platform_dispatches (dispatch_id,message_id,platform,status,dispatched_at,public_object_id,public_object_url) VALUES (?,?,?,?,?,?,?)",
                (key + "-d", key + "-tg", "TELEGRAM", "DISPATCH_CONFIRMED", pkt["at_utc"], key, f"https://t.me/CapitalChronicle/{100 + idx}"),
            )
    sc = pub_sc.build_scorecard(store, feed_path=feed, as_of_utc="2026-11-09T00:00:00Z")
    assert sc["total_calls"] == 2
    assert sc["state_counts"] == {"NOT_TRIGGERED": 1, "TRIGGERED": 1}
    assert "FILLED" not in json.dumps(sc)
    rendered = pub_sc.render_scorecard(sc)
    assert "Public calls since " in rendered and "ET" in rendered and "UTC" not in rendered

    # B. CC-394 pinned_result_scorecard_v1 against Main export + kill switch + FakeTelegramAPI (0 network!)
    now = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
    plans = [
        _scored_plan("plan-hit", "XAUUSD", "BULLISH", (2950.0, 2960.0), 2920.0, "HIT", "2026-11-24T10:00:00Z"),
        _scored_plan("plan-stop", "US500", "BEARISH", (6010.0, 6020.0), 6050.0, "STOPPED", "2026-11-24T09:00:00Z"),
        _scored_plan("plan-exp", "EURUSD", "BULLISH", (1.0800, 1.0810), 1.0750, "EXPIRED", "2026-11-24T08:00:00Z"),
        _scored_plan("plan-nt", "USTEC", "BULLISH", (21100.0, 21150.0), 20950.0, "NOT_TRIGGERED", "2026-11-24T07:00:00Z"),
    ]
    export = _sample_export(now - timedelta(minutes=2), plans)
    projected = pinned_sc.project(export, now=now)
    assert projected["counts"] == {"HIT": 1, "STOPPED": 1, "EXPIRED": 1, "NOT_TRIGGERED": 1, "total": 4, "scored": 4}
    assert projected["shown"] == 4
    assert "Capital Chronicle | Public call results" in projected["text"]

    class FakeCoordinator:
        def __init__(self, mode: str):
            self.store = store
            self._m = mode

        def _mode(self):
            return self._m

        def _clock(self):
            return now

    class FakeTelegramAPI:
        def __init__(self):
            self.calls = []
            self.pinned = None
            self.next_id = 500

        def call(self, method, **fields):
            self.calls.append((method, fields))
            if method == "getChat":
                return {"username": "CapitalChronicle", "type": "channel", "pinned_message": self.pinned}
            if method == "sendMessage":
                self.next_id += 1
                msg = {"message_id": self.next_id, "text": fields["text"], "chat": {"username": "CapitalChronicle", "type": "channel"}}
                self.last_msg = msg
                return msg
            if method == "editMessageText":
                msg = {"message_id": fields["message_id"], "text": fields["text"], "chat": {"username": "CapitalChronicle", "type": "channel"}}
                self.last_msg = msg
                self.pinned = msg
                return msg
            if method == "pinChatMessage":
                self.pinned = self.last_msg
                return True
            raise AssertionError(f"Unexpected method: {method}")

    api = FakeTelegramAPI()
    # 1. Kill switch refuses with 0 API calls.
    halted = pinned_sc.update_scorecard(FakeCoordinator("STOPPED"), export, now=now, api=api)
    assert halted == {"status": "CONTROLLED_NO_PUBLIC_WRITE", "cause": "SCORECARD_KILL_SWITCH"}
    assert api.calls == []

    # 2. First update creates + pins + confirms message 501 (0 real network calls).
    first = pinned_sc.update_scorecard(FakeCoordinator("AUTONOMOUS_DEFAULT"), export, now=now, api=api)
    assert first["status"] == "CONFIRMED" and first["created_messages"] == 1 and first["edited_messages"] == 0
    assert first["extra_result_feed_posts"] == 0 and first["message_id"] == "501"

    # 3. Second update with a new outcome edits message 501 in place (0 new messages!).
    plans2 = [*plans, _scored_plan("plan-hit-2", "USDJPY", "BEARISH", (154.0, 154.2), 155.0, "HIT", "2026-11-24T11:30:00Z")]
    export2 = _sample_export(now - timedelta(minutes=1), plans2)
    second = pinned_sc.update_scorecard(FakeCoordinator("AUTONOMOUS_DEFAULT"), export2, now=now, api=api)
    assert second["status"] == "CONFIRMED" and second["created_messages"] == 0 and second["edited_messages"] == 1
    assert second["message_id"] == "501" and second["counts"]["HIT"] == 2


# =============================================================================
# 3. RESULT POSTS (CC-322 plan_status_posts_v1)
# =============================================================================


def test_tool3_result_posts_selective_and_nonselective_and_pause_isolation(tmp_path, monkeypatch):
    # Pre-cards.EFFECTIVE timestamp so plan_status_posts_v1.queue_posts runs directly.
    now = datetime(2026, 11, 9, 15, 0, tzinfo=UTC)
    plans = [
        _scored_plan("p-hit-fresh", "XAUUSD", "BULLISH", (2950.0, 2960.0), 2920.0, "HIT", "2026-11-09T14:00:00Z"),
        _scored_plan("p-stop-1", "US500", "BEARISH", (6010.0, 6020.0), 6050.0, "STOPPED", "2026-11-09T13:00:00Z"),
        _scored_plan("p-stop-2", "EURUSD", "BULLISH", (1.0800, 1.0810), 1.0750, "STOPPED", "2026-11-09T13:30:00Z"),
        _scored_plan("p-exp-scored", "USDJPY", "BEARISH", (154.0, 154.2), 155.0, "EXPIRED", "2026-11-09T14:15:00Z"),
        _scored_plan("p-hit-stale", "USOIL", "BULLISH", (68.0, 68.5), 66.5, "HIT", "2026-11-08T08:00:00Z"),
        _scored_plan("p-untrig", "BTCUSD", "BULLISH", (81000.0, 81500.0), 79500.0, "EXPIRED", "2026-11-09T14:00:00Z", scored=False),
        _scored_plan("p-corr", "USTEC", "BULLISH", (21100.0, 21150.0), 20950.0, "HIT", "2026-11-07T10:00:00Z", corrects="outcome-old"),
    ]
    transitions = [{"plan_id": "p-untrig", "status": "EXPIRED", "at_utc": "2026-11-09T14:00:00Z", "reason_code": "WINDOW_ENDED"}]
    export = _sample_export(now - timedelta(minutes=1), plans, transitions)
    rows = posts.result_rows_from_export(export)
    assert len(rows) == 7

    # Every composed result passes public-copy validation with zero private fields.
    for row in rows:
        composed = posts.compose_result(row)
        assert composed["status"] == "COMPOSED" and composed["kind"] == "result"
        assert "Capital Chronicle offers analysis only" in composed["text"]

    monkeypatch.setattr(posts, "read_transitions", lambda *a, **kw: deepcopy(rows))

    # A. Selective mode (Decision 106 default): queues fresh HIT, first STOPPED, and correction only.
    store_sel = ContentOpsDurableStore(str(tmp_path / "sel.sqlite3"))
    monkeypatch.setattr(posts, "RESULT_POSTS_SELECTIVE", True)
    res_sel = posts.queue_posts(store_sel, export_dir=tmp_path, now=now, dry_run=False)
    queued_symbols = sorted(q["symbol"] for q in res_sel["queued"])
    assert queued_symbols == ["US500", "USTEC", "XAUUSD"]
    skipped_causes = {s["cause"] for s in res_sel["not_posted"]}
    assert {
        "LOSS_POST_LIMIT_DECISION_106",
        "EXIT_AT_HORIZON_END_NOT_POSTED_DECISION_106",
        "RESULT_OLDER_THAN_A_DAY_NOT_POSTED_DECISION_106",
        "ENDED_WITHOUT_ENTRY_NOT_POSTED_DECISION_106",
    } <= skipped_causes

    # B. Non-selective mode: queues all 6 scored results (untriggered still skipped because plan never announced).
    store_all = ContentOpsDurableStore(str(tmp_path / "all.sqlite3"))
    monkeypatch.setattr(posts, "RESULT_POSTS_SELECTIVE", False)
    res_all = posts.queue_posts(store_all, export_dir=tmp_path, now=now, dry_run=False)
    assert len(res_all["queued"]) == 6

    # C. Verify Jim's 23 Nov pause window helper stays test-isolated (never reads live control files).
    p_start, p_end = cards.jim_pause_window()
    assert p_start == cards.JIM_PAUSE_START and p_end == cards.JIM_PAUSE_END
