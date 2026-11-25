"""Hermetic regression tests for P5 (daily digest 12:00Z CPI/macro cutoff fix)
and P4 (vision-review response parser fail-closed hardening).

Zero network calls, zero live store/feed writes, zero subprocess launches.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

import pytest

from live_contentops import image_quality_v1 as quality
from live_contentops import published_content_v1 as pub_content
from live_contentops import substack_daily_digest_v1 as digest
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.event_article_guard_v1 import PUBLIC_NOTICE
from live_contentops.preview_link_guard_v1 import REASON as PREVIEW_LINK_REASON, find_forbidden_link
from live_contentops.public_decision_checks_v1 import AI_LABEL, notice_counts, plan_target_present
from live_contentops.public_time_v1 import REASON as PUBLIC_TIME_REASON, find_forbidden_public_time
from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
from test_image_templates_cc465 import asset as template_asset
from test_substack_daily_digest_v1 import confirm


def _clock(iso_utc: str) -> datetime:
    return datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))


def _sealed_row(
    *,
    content_id: str,
    title: str,
    published_at_utc: str,
    url: str,
    recorded_at_utc: str | None = None,
    standfirst: str = "An attributed public macro analysis from Capital Chronicle.",
    piece_type: str = "ARTICLE",
    event_id: str | None = None,
    rights_class: str = "CC_OWN_ANALYSIS",
) -> dict:
    record = {
        "schema_version": pub_content.SCHEMA,
        "content_id": content_id,
        "type": piece_type,
        "title": title,
        "standfirst": standfirst,
        "published_at_utc": published_at_utc,
        "recorded_at_utc": recorded_at_utc or published_at_utc,
        "outlets": [{"name": "substack", "url": url}],
        "event_id": event_id,
        "conditional_calls": [],
        "rights_class": rights_class,
        "visibility": "public",
        "disclaimer": PUBLIC_NOTICE,
        "conflicts_notice": None,
    }
    record["content_sha256"] = sha256(pub_content.canonical(record)).hexdigest()
    return record


def _write_feed(path: Path, rows: list[dict]) -> Path:
    path.write_bytes(b"".join(pub_content.canonical(r) + b"\n" for r in rows))
    return path


def _store(tmp_path: Path, name: str = "digest.sqlite3") -> ContentOpsDurableStore:
    return ContentOpsDurableStore(tmp_path / name)


def _register_definite_no_write(store: ContentOpsDurableStore, packet: dict) -> dict:
    ids = DurablePublicationCoordinator._ids(
        packet["digest_id"], packet["plan"]["plan_hash"], "substack"
    )
    store.register_outbox_message(
        message_id=ids["message_id"],
        work_item_id=packet["digest_id"],
        destination="substack",
        payload="{}",
        status="DEFINITE_NO_WRITE",
    )
    store.register_platform_dispatch(
        dispatch_id=ids["dispatch_id"],
        message_id=ids["message_id"],
        platform="substack",
        status="DEFINITE_NO_WRITE",
        public_object_id=None,
        public_object_url=None,
    )
    return ids


# ---------------------------------------------------------------------------
# P5: Substack daily digest post-12:00Z CPI / NFP macro cutoff fix
# ---------------------------------------------------------------------------


def test_p5_nov10_cpi_preview_after_1200z_included_at_1215z(tmp_path: Path) -> None:
    """Real 10 Nov 2026 P5 reproduction: 12:09:49Z CPI preview must land in 10 Nov digest at 12:15Z."""
    store = _store(tmp_path)
    morning = _sealed_row(
        content_id="substack:224000001",
        title="Pre-US Market Wrap, November 10, 2026",
        published_at_utc="2026-11-10T11:30:00Z",
        url="https://capitalchronicle.substack.com/p/pre-us-wrap-nov-10",
    )
    cpi_preview = _sealed_row(
        content_id="substack:224000002",
        title="October Core CPI Preview: Gold and Yields Scenarios",
        published_at_utc="2026-11-10T12:09:49Z",
        url="https://capitalchronicle.substack.com/p/october-cpi-preview",
        piece_type="EVENT_PREVIEW",
        event_id="bls-cpi-20261110",
    )
    feed = _write_feed(tmp_path / "published.jsonl", [morning, cpi_preview])

    nov10 = digest.prepare_daily_digest(store, feed, now=_clock("2026-11-10T12:15:00Z"))
    packet = nov10["packet"]

    assert nov10["digest_id"] == "cc143-digest-2026-11-10"
    assert nov10["public_write_performed"] is False
    assert [a["content_id"] for a in packet["articles"]] == [
        "substack:224000001",
        "substack:224000002",
    ]
    assert packet["cutoff_utc"] == "2026-11-10T12:15:00+00:00"
    assert packet["plan"]["publication_window"] == {
        "window_identity": "cc143-digest-2026-11-10",
        "start_utc": "2026-11-09T12:00:00+00:00",
        "cutoff_utc": "2026-11-10T12:15:00+00:00",
    }

    # Public filters & Decision 42 / 83 / 90 / 109 / 157 / CC-729 invariants
    payload = packet["native_payload"]
    assert payload["title"] == "Capital Chronicle daily digest — November 10, 2026 (ET)"
    assert find_forbidden_public_time(payload) is None
    assert find_forbidden_link(payload) is None
    assert not AI_LABEL.search(payload["body_markdown"])
    assert not plan_target_present(payload["body_markdown"])
    assert notice_counts(payload["body_markdown"]) == {"analysis_notice": 1, "conflicts_notice": 0}
    assert digest.delivery_mode_for_plan(store, packet["digest_id"], packet["plan"]) == digest.EMAIL_DIGEST
    assert digest.delivery_mode_for_plan(store, "ordinary-article", {"destinations": []}) == digest.WEB_ONLY

    # Frozen packet immutability on same-day re-entry after 12:15Z
    again = digest.prepare_daily_digest(store, feed, now=_clock("2026-11-10T12:45:00Z"))
    assert again["packet"] == packet
    assert len(digest.packets(store)) == 1


def test_p5_nov06_nfp_preview_grace_cap_and_gap_free_next_day_rollover(tmp_path: Path) -> None:
    """Real 6 Nov 2026 NFP preview (12:58:16Z, recorded 13:27:30Z) respects no-lookahead and 14:00Z cap."""
    store = _store(tmp_path)
    nfp_preview = _sealed_row(
        content_id="substack:223763353",
        title="NFP preview: why a payroll beat needs help from unemployment",
        published_at_utc="2026-11-06T12:58:16Z",
        recorded_at_utc="2026-11-06T13:27:30Z",
        url="https://capitalchronicle.substack.com/p/nfp-preview-nov-6",
        piece_type="EVENT_PREVIEW",
        event_id="bls-emsit-20261106",
    )
    after_grace = _sealed_row(
        content_id="substack:223799999",
        title="Post-payrolls Treasury reaction",
        published_at_utc="2026-11-06T14:00:01Z",
        recorded_at_utc="2026-11-06T14:05:00Z",
        url="https://capitalchronicle.substack.com/p/post-payrolls-treasury",
    )
    feed = _write_feed(tmp_path / "published.jsonl", [nfp_preview, after_grace])

    # Before recorded_at_utc (13:27:30Z), fail closed: do not expose unrecorded articles.
    early = digest.prepare_daily_digest(store, feed, now=_clock("2026-11-06T13:20:00Z"))
    assert early["state"] == "NO_CONFIRMED_ARTICLES"
    assert digest.packets(store) == []

    # At 15:00Z, effective cutoff caps at 14:00Z (12:00Z + POST_CUTOFF_MACRO_GRACE):
    # includes 12:58:16Z NFP preview, leaves 14:00:01Z piece for Nov 7.
    nov06 = digest.prepare_daily_digest(store, feed, now=_clock("2026-11-06T15:00:00Z"))["packet"]
    assert nov06["cutoff_utc"] == "2026-11-06T14:00:00+00:00"
    assert [a["content_id"] for a in nov06["articles"]] == ["substack:223763353"]
    assert nov06["native_payload"]["title"].endswith("November 6, 2026 (ET)")

    # Confirm Nov 6, then verify Nov 7 picks up 14:00:01Z with zero gap and zero duplication.
    confirm(store, nov06)
    nov07 = digest.prepare_daily_digest(store, feed, now=_clock("2026-11-07T12:00:00Z"))["packet"]
    assert nov07["digest_id"] == "cc143-digest-2026-11-07"
    assert nov07["cutoff_utc"] == "2026-11-07T12:00:00+00:00"
    assert [a["content_id"] for a in nov07["articles"]] == ["substack:223799999"]

    # Day after with no new pieces returns NO_CONFIRMED_ARTICLES.
    confirm(store, nov07)
    assert (
        digest.prepare_daily_digest(store, feed, now=_clock("2026-11-08T12:15:00Z"))["state"]
        == "NO_CONFIRMED_ARTICLES"
    )


def test_p5_no_future_lookahead_and_exact_1200z_and_early_wake_guards(tmp_path: Path) -> None:
    """Never look ahead past now_utc; exact 12:00Z and 11:59:59Z boundaries stay fail-closed."""
    store = _store(tmp_path)
    early_am = _sealed_row(
        content_id="substack:224100001",
        title="Asian session macro note",
        published_at_utc="2026-11-10T03:00:00Z",
        url="https://capitalchronicle.substack.com/p/asian-macro-note",
    )
    post_now = _sealed_row(
        content_id="substack:224100002",
        title="CPI preview one second after now",
        published_at_utc="2026-11-10T12:15:01Z",
        url="https://capitalchronicle.substack.com/p/cpi-preview-121501",
        piece_type="EVENT_PREVIEW",
        event_id="bls-cpi-20261110",
    )
    feed = _write_feed(tmp_path / "published.jsonl", [early_am, post_now])

    # Naive clock fails closed.
    with pytest.raises(ValueError, match="EXPLICIT_DIGEST_CLOCK_REQUIRED"):
        digest.prepare_daily_digest(store, feed, now=datetime(2026, 11, 10, 12, 15))

    # Early wake (18:59:59 GMT+7 -> day=Nov 9, max_cutoff=Nov 9 14:00Z) never swallows Nov 10 pieces.
    assert (
        digest.prepare_daily_digest(store, feed, now=_clock("2026-11-10T11:59:59Z"))["state"]
        == "NO_CONFIRMED_ARTICLES"
    )

    # At 12:15:00Z, 12:15:01Z is strictly in the future and excluded.
    packet = digest.prepare_daily_digest(store, feed, now=_clock("2026-11-10T12:15:00Z"))["packet"]
    assert [a["content_id"] for a in packet["articles"]] == ["substack:224100001"]
    assert packet["cutoff_utc"] == "2026-11-10T12:15:00+00:00"


def test_p5_defer_until_utc_macro_hold_fail_closed_and_prior_recovery_preserved(tmp_path: Path) -> None:
    """Explicit defer_until_utc holds fresh freeze inside [12:00Z, 14:00Z] without blocking prior recovery."""
    store = _store(tmp_path)
    morning = _sealed_row(
        content_id="substack:224200001",
        title="Morning pre-US brief",
        published_at_utc="2026-11-10T11:30:00Z",
        url="https://capitalchronicle.substack.com/p/morning-brief",
    )
    cpi = _sealed_row(
        content_id="substack:224200002",
        title="October CPI preview",
        published_at_utc="2026-11-10T12:09:49Z",
        recorded_at_utc="2026-11-10T12:43:48Z",
        url="https://capitalchronicle.substack.com/p/cpi-preview",
        piece_type="EVENT_PREVIEW",
        event_id="bls-cpi-20261110",
    )
    feed = _write_feed(tmp_path / "published.jsonl", [morning, cpi])

    # Naive or out-of-window defer_until_utc fails closed.
    with pytest.raises(ValueError, match="EXPLICIT_DIGEST_CLOCK_REQUIRED"):
        digest.prepare_daily_digest(
            store, feed, now=_clock("2026-11-10T12:00:00Z"),
            defer_until_utc=datetime(2026, 11, 10, 13, 30),
        )
    for bad_defer in ("2026-11-10T11:59:59Z", "2026-11-10T14:00:01Z"):
        with pytest.raises(ValueError, match="DIGEST_DEFER_WINDOW_INVALID"):
            digest.prepare_daily_digest(
                store, feed, now=_clock("2026-11-10T12:00:00Z"),
                defer_until_utc=_clock(bad_defer),
            )

    # At 12:00Z with defer_until_utc=13:00Z, holds without prematurely freezing morning-only packet.
    held = digest.prepare_daily_digest(
        store, feed, now=_clock("2026-11-10T12:00:00Z"),
        defer_until_utc=_clock("2026-11-10T13:00:00Z"),
    )
    assert held["state"] == "DEFERRED_FOR_MACRO_RELEASE"
    assert held["defer_until_utc"] == "2026-11-10T13:00:00+00:00"
    assert held["public_write_performed"] is False
    assert digest.packets(store) == []

    # At 13:00Z, freezes once with BOTH morning wrap and recorded CPI preview.
    ready = digest.prepare_daily_digest(
        store, feed, now=_clock("2026-11-10T13:00:00Z"),
        defer_until_utc=_clock("2026-11-10T13:00:00Z"),
    )
    assert [a["content_id"] for a in ready["packet"]["articles"]] == [
        "substack:224200001",
        "substack:224200002",
    ]

    # Recovery of an existing unsent prior digest is NEVER blocked by next day's defer_until_utc.
    resumed = digest.prepare_daily_digest(
        store, feed, now=_clock("2026-11-11T12:05:00Z"),
        defer_until_utc=_clock("2026-11-11T13:45:00Z"),
    )
    assert resumed["packet"] == ready["packet"]


@pytest.mark.parametrize(
    "now_iso,expected_label",
    [
        ("2026-07-15T14:00:00Z", "July 15, 2026 (ET)"),        # EDT (10:00 EDT)
        ("2026-11-01T14:00:00Z", "November 1, 2026 (ET)"),     # US fall-back DST Sunday (09:00 EST)
        ("2026-11-10T14:00:00Z", "November 10, 2026 (ET)"),    # EST (09:00 EST)
    ],
)
def test_p5_dst_and_definite_no_write_carryover_preserve_et_day_and_uniqueness(
    tmp_path: Path, now_iso: str, expected_label: str
) -> None:
    """Grace ceiling (14:00Z) never drifts ET reader date across DST, and DEFINITE_NO_WRITE carries once."""
    day_prefix = now_iso[:10]
    store = _store(tmp_path)
    article = _sealed_row(
        content_id=f"substack:{day_prefix.replace('-', '')}1",
        title=f"Macro preview for {day_prefix}",
        published_at_utc=f"{day_prefix}T12:30:00Z",
        url=f"https://capitalchronicle.substack.com/p/macro-{day_prefix}",
        piece_type="EVENT_PREVIEW",
        event_id=f"macro-{day_prefix}",
    )
    feed = _write_feed(tmp_path / "published.jsonl", [article])

    first = digest.prepare_daily_digest(store, feed, now=_clock(now_iso))["packet"]
    assert first["native_payload"]["title"].endswith(expected_label)
    assert first["cutoff_utc"] == f"{day_prefix}T14:00:00+00:00"

    # Refuse the first digest (DEFINITE_NO_WRITE): same day keeps frozen identity; next day carries once.
    _register_definite_no_write(store, first)
    same_day = digest.prepare_daily_digest(store, feed, now=_clock(f"{day_prefix}T15:30:00Z"))
    assert same_day["packet"] == first

    next_day_clock = _clock(f"{day_prefix}T12:00:00Z")
    from datetime import timedelta

    next_day = next_day_clock + timedelta(days=1)
    carried = digest.prepare_daily_digest(store, feed, now=next_day)["packet"]
    assert carried["digest_id"] == "cc143-digest-" + next_day.date().isoformat()
    assert carried["articles"] == first["articles"]
    assert carried["native_payload"]["body_markdown"].count(article["outlets"][0]["url"]) == 1


def test_p5_public_filters_refuse_preview_link_forbidden_time_and_private_rights(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Public filters fail closed before freezing any packet: Decision 83, Decision 90, and rights."""
    # 1) Decision 83 preview host link via live_canonicals
    store1 = _store(tmp_path, "s1.sqlite3")
    empty_feed = _write_feed(tmp_path / "empty.jsonl", [])
    monkeypatch.setattr(
        digest,
        "live_canonicals",
        lambda _s: [
            {
                "content_id": "substack:999001",
                "title": "Preview link leak test",
                "standfirst": "Mirror at https://fatcat2109.github.io/capital-chronicle-preview/post",
                "published_at_utc": "2026-11-10T12:09:49Z",
                "url": "https://capitalchronicle.substack.com/p/preview-link-leak",
            }
        ],
    )
    with pytest.raises(ValueError, match=PREVIEW_LINK_REASON):
        digest.prepare_daily_digest(store1, empty_feed, now=_clock("2026-11-10T12:15:00Z"))
    assert digest.packets(store1) == []

    # 2) Decision 90 forbidden GMT+7 clock via live_canonicals
    store2 = _store(tmp_path, "s2.sqlite3")
    monkeypatch.setattr(
        digest,
        "live_canonicals",
        lambda _s: [
            {
                "content_id": "substack:999002",
                "title": "CPI preview at 19:09 GMT+7",
                "standfirst": "Attributed summary.",
                "published_at_utc": "2026-11-10T12:09:49Z",
                "url": "https://capitalchronicle.substack.com/p/gmt7-leak",
            }
        ],
    )
    with pytest.raises(ValueError, match=PUBLIC_TIME_REASON):
        digest.prepare_daily_digest(store2, empty_feed, now=_clock("2026-11-10T12:15:00Z"))
    assert digest.packets(store2) == []

    # 3) Non-public rights_class in feed fails closed
    store3 = _store(tmp_path, "s3.sqlite3")
    monkeypatch.setattr(digest, "live_canonicals", lambda _s: [])
    bad_feed = _write_feed(
        tmp_path / "private.jsonl",
        [
            _sealed_row(
                content_id="substack:999003",
                title="Private research piece",
                published_at_utc="2026-11-10T12:09:49Z",
                url="https://capitalchronicle.substack.com/p/private-piece",
                rights_class="INTERNAL_RESEARCH_ONLY",
            )
        ],
    )
    with pytest.raises(ValueError, match="PUBLIC_REUSE_RIGHTS_NOT_ADMITTED"):
        digest.prepare_daily_digest(store3, bad_feed, now=_clock("2026-11-10T12:15:00Z"))
    assert digest.packets(store3) == []


# ---------------------------------------------------------------------------
# P4: Vision review response parser fail-closed hardening (no policy cap change)
# ---------------------------------------------------------------------------


def _fake_codex_runner(payload_obj: object):
    def run(args, *, cwd, timeout, input):
        Path(args[args.index("--output-last-message") + 1]).write_text(
            json.dumps(payload_obj), encoding="utf-8"
        )
        events = [
            {"type": "thread.started", "thread_id": "controlled-p4-session"},
            {"type": "turn.completed", "usage": {"total_tokens": 1}},
        ]
        return subprocess.CompletedProcess(
            args, 0, "\n".join(json.dumps(e) for e in events).encode(), b""
        )

    return run


@pytest.mark.parametrize(
    "bad_payload",
    [
        ["not", "a", "dict"],
        None,
        {
            "image_seen": True,
            "points": None,
            "reasons": {str(i): "ok" for i in range(1, 11)},
        },
        {
            "image_seen": True,
            "points": {str(i): True for i in range(1, 11)},
            "reasons": ["not", "a", "dict"],
        },
        {
            "image_seen": True,
            "points": {str(i): True for i in range(1, 11)},
            "reasons": {**{str(i): "ok" for i in range(1, 11)}, "11": "unexpected extra key"},
        },
        {
            "image_seen": True,
            "points": {str(i): True for i in range(1, 11)},
            "reasons": {**{str(i): "ok" for i in range(1, 11)}, "1": 42},
        },
        {
            "image_seen": True,
            "points": {str(i): True for i in range(1, 11)},
            "reasons": {**{str(i): "ok" for i in range(1, 11)}, "2": "   \t  "},
        },
    ],
)
def test_p4_vision_parser_fails_closed_on_malformed_shapes_and_blank_reasons(
    tmp_path: Path, bad_payload: object
) -> None:
    """Malformed Codex vision JSON never raises AttributeError/TypeError or accepts blank/non-string reasons."""
    image = template_asset(tmp_path)
    review = quality.review_vision(image, runner=_fake_codex_runner(bad_payload))
    assert review["status"] == "REVIEW_UNAVAILABLE"
    assert review["cause"] == "ValueError:AGY_VISION_TEN_POINTS_REQUIRED"
    assert review["points"] == {}


def test_p4_vision_parser_accepts_valid_codex_response_and_preserves_policy_caps(
    tmp_path: Path,
) -> None:
    """Valid Codex vision JSON strips surrounding whitespace cleanly while keeping exact policy thresholds."""
    assert quality.MANDATORY == {1, 2, 3, 5, 7, 9}
    image = template_asset(tmp_path)
    good_payload = {
        "image_seen": True,
        "points": {str(i): True for i in range(1, 11)},
        "reasons": {str(i): f"  Point {i} verified visually.  " for i in range(1, 11)},
    }
    review = quality.review_vision(image, runner=_fake_codex_runner(good_payload))
    assert review["status"] == "REVIEWED"
    assert review["answered_by"] == "codex"
    assert review["reasons"]["1"] == "Point 1 verified visually."
    assert review["light_call"]["attempts"][-1]["image_attached"] is True
    code = quality.code_check(image)
    combined = quality.combine(code, review)
    assert combined["passed"] is True and combined["score"] == 10

    # Policy thresholds remain strictly unchanged: 8/10 non-mandatory passes; 7/10 or mandatory point fails.
    eight_ok = {**review, "points": {**review["points"], "4": False, "10": False}}
    assert quality.combine(code, eight_ok)["passed"] is True
    seven_fail = {**review, "points": {**review["points"], "4": False, "8": False, "10": False}}
    assert quality.combine(code, seven_fail)["passed"] is False
    mandatory_fail = {**review, "points": {**review["points"], "5": False}}
    assert quality.combine(code, mandatory_fail)["passed"] is False
