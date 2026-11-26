"""CC-463 / CC-465 (P4): bounded transient vision retry, IMAGE_HELD outcome dedup, and 7-market acceptance.

All tests exercise real PNG rendering, real code_check, real sidecar persistence,
real light_model_caller_v1.call_light (injecting only the CLI subprocess runner),
and real tradingview_snapshot_v1.plan_snapshot state machines with zero live posts.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

import pytest

from live_contentops import image_quality_v1 as quality
from live_contentops import image_template_inputs_v1 as inputs
from live_contentops import light_model_caller_v1 as light
from live_contentops import tradingview_snapshot_v1 as tv
from test_image_templates_cc465 import capture, input_record, vision_response


T0 = datetime(2026, 11, 26, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _codex_cli_stub(monkeypatch):
    monkeypatch.setattr(light, "codex_executable", lambda: "codex.exe")


def _usage_limit_stdout() -> bytes:
    return (
        b'{"type":"thread.started","thread_id":"thr-quota-1"}\n'
        + '{"type":"error","message":"You\u2019ve hit your usage limit. Try again later."}\n'.encode("utf-8")
        + b'{"type":"turn.failed","error":{"message":"You\'ve hit your usage limit."}}\n'
    )


def _passing_vision_runner(calls: list[dict], *, points: dict[str, bool] | None = None):
    def run(args, *, cwd, timeout, input=None):
        calls.append({"args": list(args), "prompt": (input or b"").decode("utf-8"), "cwd": cwd})
        payload = None
        if points is not None:
            merged = {str(i): True for i in range(1, 11)}
            merged.update(points)
            payload = {
                "image_seen": True,
                "points": merged,
                "reasons": {str(i): "controlled visual response" for i in range(1, 11)},
            }
        return vision_response(args, cwd=cwd, timeout=timeout, input=input, value=payload)
    return run


def _quota_failure_runner(calls: list[dict]):
    def run(args, *, cwd, timeout, input=None):
        calls.append({"args": list(args), "prompt": (input or b"").decode("utf-8"), "cwd": cwd})
        return subprocess.CompletedProcess(args, 1, _usage_limit_stdout(), b"")
    return run


def _timeout_runner(calls: list[dict]):
    def run(args, *, cwd, timeout, input=None):
        calls.append({"args": list(args), "prompt": (input or b"").decode("utf-8"), "cwd": cwd})
        raise subprocess.TimeoutExpired(args, timeout, output=b"", stderr=b"")
    return run


def _read_outcomes(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_prepare_asset_retries_transient_usage_limit_and_timeout_after_cooldown_then_caches_pass(tmp_path):
    snap = capture(tmp_path)
    data = input_record("call")
    calls: list[dict] = []

    # Initial attempt at T0 hits Codex usage limit -> held with REVIEW_UNAVAILABLE.
    with pytest.raises(ValueError, match="IMAGE_VISION_REVIEW_REQUIRED_OR_FAILED"):
        quality.prepare_asset(data, "W", tmp_path, snap, vision_runner=_quota_failure_runner(calls), now=T0)
    assert len(calls) == 1
    sidecar_path = next(tmp_path.glob("controlled-fixture-call-*.json"))
    first_bytes = sidecar_path.read_bytes()
    first_doc = json.loads(first_bytes)
    assert first_doc["image_quality"]["vision"]["status"] == "REVIEW_UNAVAILABLE"
    assert first_doc["image_quality"]["vision"]["cause"] == "ValueError:CODEX_USAGE_LIMIT"
    assert first_doc["image_quality"]["vision"]["ended_at_utc"] == T0.isoformat()

    # Inside cooldown (299s) and negative clock skew (-5s): ZERO Codex calls.
    for clock in (T0 - timedelta(seconds=5), T0 + timedelta(seconds=299)):
        with pytest.raises(ValueError, match="IMAGE_VISION_REVIEW_REQUIRED_OR_FAILED"):
            quality.prepare_asset(
                data, "W", tmp_path, snap,
                vision_runner=lambda *a, **k: pytest.fail("must not retry inside cooldown"),
                now=clock,
            )

    # Exact 300s boundary: retry #1 runs, hits Codex timeout, preserves prior bytes + provenance.
    t1 = T0 + timedelta(seconds=quality.REVIEW_UNAVAILABLE_RETRY_COOLDOWN_SECONDS)
    with pytest.raises(ValueError, match="IMAGE_VISION_REVIEW_REQUIRED_OR_FAILED"):
        quality.prepare_asset(data, "W", tmp_path, snap, vision_runner=_timeout_runner(calls), now=t1)
    assert len(calls) == 2
    second_bytes = sidecar_path.read_bytes()
    second_vision = json.loads(second_bytes)["image_quality"]["vision"]
    assert second_vision["status"] == "REVIEW_UNAVAILABLE"
    assert second_vision["cause"] == "ValueError:CODEX_LIGHT_TIMEOUT_120S"
    assert second_vision["transient_retry_count"] == 1
    assert second_vision["prior_unavailable_causes"] == ["ValueError:CODEX_USAGE_LIMIT"]
    assert second_vision["first_unavailable_at_utc"] == T0.isoformat()
    assert Path(second_vision["retained_prior_failure_path"]).read_bytes() == first_bytes

    # Retry #2 at T0 + 600s succeeds with 10/10 -> recovers cleanly without re-rendering PNG.
    t2 = t1 + timedelta(seconds=quality.REVIEW_UNAVAILABLE_RETRY_COOLDOWN_SECONDS)
    recovered = quality.prepare_asset(data, "W", tmp_path, snap, vision_runner=_passing_vision_runner(calls), now=t2)
    assert len(calls) == 3
    final_vision = recovered["image_quality"]["vision"]
    assert recovered["image_quality"]["passed"] is True
    assert recovered["image_quality"]["score"] == 10
    assert final_vision["status"] == "REVIEWED"
    assert final_vision["transient_retry_count"] == 2
    assert final_vision["prior_unavailable_causes"] == [
        "ValueError:CODEX_USAGE_LIMIT",
        "ValueError:CODEX_LIGHT_TIMEOUT_120S",
    ]
    assert final_vision["first_unavailable_at_utc"] == T0.isoformat()
    assert Path(final_vision["retained_prior_failure_path"]).read_bytes() == second_bytes

    # Subsequent call well after recovery uses cached REVIEWED result with zero model calls.
    cached = quality.prepare_asset(
        data, "W", tmp_path, snap,
        vision_runner=lambda *a, **k: pytest.fail("cached pass must not re-call Codex"),
        now=t2 + timedelta(hours=2),
    )
    assert cached["image_quality"]["vision"] == final_vision


def test_prepare_asset_stops_retrying_at_max_transient_review_retries(tmp_path):
    snap = capture(tmp_path)
    data = input_record("call")
    calls: list[dict] = []

    # 1 initial + MAX_TRANSIENT_REVIEW_RETRIES (3) = 4 total calls, then exhausted.
    for step in range(quality.MAX_TRANSIENT_REVIEW_RETRIES + 1):
        at = T0 + timedelta(seconds=step * quality.REVIEW_UNAVAILABLE_RETRY_COOLDOWN_SECONDS)
        with pytest.raises(ValueError, match="IMAGE_VISION_REVIEW_REQUIRED_OR_FAILED"):
            quality.prepare_asset(data, "W", tmp_path, snap, vision_runner=_quota_failure_runner(calls), now=at)
    assert len(calls) == quality.MAX_TRANSIENT_REVIEW_RETRIES + 1

    sidecar_path = next(tmp_path.glob("controlled-fixture-call-*.json"))
    vision = json.loads(sidecar_path.read_bytes())["image_quality"]["vision"]
    assert vision["transient_retry_count"] == quality.MAX_TRANSIENT_REVIEW_RETRIES
    assert len(vision["prior_unavailable_causes"]) == quality.MAX_TRANSIENT_REVIEW_RETRIES

    # Call far past cooldown after exhaustion must NOT invoke Codex again.
    with pytest.raises(ValueError, match="IMAGE_VISION_REVIEW_REQUIRED_OR_FAILED"):
        quality.prepare_asset(
            data, "W", tmp_path, snap,
            vision_runner=lambda *a, **k: pytest.fail("exhausted transient retries must not re-call Codex"),
            now=T0 + timedelta(hours=12),
        )


@pytest.mark.parametrize("failed_points", [
    {"4": False, "8": False, "10": False},  # score 7/10 (< 8)
    {"3": False},                           # score 9/10, mandatory point 3 failed
])
def test_prepare_asset_never_retries_scored_reviewed_rejection(tmp_path, failed_points):
    snap = capture(tmp_path)
    data = input_record("call")
    calls: list[dict] = []

    with pytest.raises(ValueError, match="IMAGE_VISION_REVIEW_REQUIRED_OR_FAILED"):
        quality.prepare_asset(
            data, "W", tmp_path, snap,
            vision_runner=_passing_vision_runner(calls, points=failed_points),
            now=T0,
        )
    assert len(calls) == 1

    # Even 24 hours later, a scored REVIEWED rejection stays permanently held without re-calling Codex.
    with pytest.raises(ValueError, match="IMAGE_VISION_REVIEW_REQUIRED_OR_FAILED"):
        quality.prepare_asset(
            data, "W", tmp_path, snap,
            vision_runner=lambda *a, **k: pytest.fail("scored REVIEWED rejection must never retry"),
            now=T0 + timedelta(hours=24),
        )


@pytest.mark.parametrize("bad_cause", [
    "ValueError:AGY_VISION_TEN_POINTS_REQUIRED",
    "ValueError:AGY_IMAGE_PIXELS_NOT_OBSERVED",
    "ValueError:CODEX_LIGHT_TOOL_USE_REFUSED",
    "ValueError:IMAGE_REVIEW_BYTES_CHANGED",
    "ValueError:IMAGE_REVIEW_FILE_UNAVAILABLE",
    "ValueError:AGY_TERMS_BLOCK",
])
def test_prepare_asset_never_retries_non_transient_unavailable_causes_even_without_light_call(tmp_path, bad_cause):
    snap = capture(tmp_path)
    data = input_record("call")
    # First build a valid PNG + sidecar via sample_after_publication so PNG bytes & code_check are real.
    prepared = quality.prepare_asset(data, "W", tmp_path, snap, sample_after_publication=True, now=T0)
    sidecar_path = Path(prepared["path"]).with_suffix(".json")
    doc = json.loads(sidecar_path.read_bytes())
    doc["image_quality"]["vision"] = {
        "policy": quality.VISION_POLICY,
        "model": light.CODEX_MODEL,
        "image_sha256": prepared["sha256"],
        "status": "REVIEW_UNAVAILABLE",
        "cause": bad_cause,
        "ended_at_utc": T0.isoformat(),
        "points": {},
    }
    doc["image_quality"]["passed"] = False
    sidecar_path.write_text(json.dumps(doc), encoding="utf-8")

    with pytest.raises(ValueError, match="IMAGE_VISION_REVIEW_REQUIRED_OR_FAILED"):
        quality.prepare_asset(
            data, "W", tmp_path, snap,
            vision_runner=lambda *a, **k: pytest.fail(f"non-transient cause {bad_cause} must not retry"),
            now=T0 + timedelta(hours=6),
        )


def test_pre_call_light_oserror_respects_cooldown_and_does_not_trigger_legacy_retry(tmp_path):
    snap = capture(tmp_path)
    data = input_record("call")
    prepared = quality.prepare_asset(data, "W", tmp_path, snap, sample_after_publication=True, now=T0)
    sidecar_path = Path(prepared["path"]).with_suffix(".json")
    doc = json.loads(sidecar_path.read_bytes())
    # Simulate an OSError caught before call_light populated light_call (current policy + codex model).
    doc["image_quality"]["vision"] = {
        "policy": quality.VISION_POLICY,
        "model": light.CODEX_MODEL,
        "image_sha256": prepared["sha256"],
        "status": "REVIEW_UNAVAILABLE",
        "cause": "OSError:temporary pipe error",
        "ended_at_utc": T0.isoformat(),
        "points": {},
    }
    doc["image_quality"]["passed"] = False
    sidecar_path.write_text(json.dumps(doc), encoding="utf-8")

    # Inside cooldown: must NOT bypass cooldown via legacy_retry.
    with pytest.raises(ValueError, match="IMAGE_VISION_REVIEW_REQUIRED_OR_FAILED"):
        quality.prepare_asset(
            data, "W", tmp_path, snap,
            vision_runner=lambda *a, **k: pytest.fail("pre-call_light OSError must honor cooldown"),
            now=T0 + timedelta(seconds=120),
        )

    # Past cooldown: retries cleanly and recovers.
    calls: list[dict] = []
    recovered = quality.prepare_asset(
        data, "W", tmp_path, snap,
        vision_runner=_passing_vision_runner(calls),
        now=T0 + timedelta(seconds=quality.REVIEW_UNAVAILABLE_RETRY_COOLDOWN_SECONDS),
    )
    assert len(calls) == 1 and recovered["image_quality"]["passed"] is True
    assert recovered["image_quality"]["vision"]["transient_retry_count"] == 1


@pytest.mark.parametrize("bad_review", [
    {"status": "REVIEW_UNAVAILABLE", "cause": "ValueError:CODEX_USAGE_LIMIT"},  # missing clock
    {"status": "REVIEW_UNAVAILABLE", "cause": "ValueError:CODEX_USAGE_LIMIT", "ended_at_utc": "2026-11-26T12:00:00"},  # naive
    {"status": "REVIEW_UNAVAILABLE", "cause": "ValueError:CODEX_USAGE_LIMIT", "ended_at_utc": T0.isoformat(), "transient_retry_count": True},
    {"status": "REVIEW_UNAVAILABLE", "cause": "ValueError:CODEX_USAGE_LIMIT", "ended_at_utc": T0.isoformat(), "transient_retry_count": -1},
    {"status": "REVIEW_UNAVAILABLE", "cause": "ValueError:CODEX_USAGE_LIMIT", "ended_at_utc": T0.isoformat(), "transient_retry_count": "0"},
])
def test_transient_retry_predicate_fails_closed_on_malformed_clock_or_counter(bad_review):
    assert quality._can_retry_transient_unavailable(bad_review, now=T0 + timedelta(hours=1)) is False


def test_naive_now_clock_rejected_fail_closed(tmp_path):
    snap = capture(tmp_path)
    data = input_record("call")
    naive = datetime(2026, 11, 26, 12, 0, 0)
    with pytest.raises(ValueError, match="IMAGE_REVIEW_CLOCK_TIMEZONE_REQUIRED"):
        quality.prepare_asset(data, "W", tmp_path, snap, now=naive)
    prepared = quality.prepare_asset(data, "W", tmp_path, snap, sample_after_publication=True, now=T0)
    with pytest.raises(ValueError, match="IMAGE_REVIEW_CLOCK_TIMEZONE_REQUIRED"):
        quality.sampled_review({"sha256": prepared["sha256"], "image_quality": prepared["image_quality"]},
                               run_vision=True, now=naive)


def test_sampled_review_and_publication_sample_recover_from_transient_usage_limit(tmp_path):
    snap = capture(tmp_path)
    data = input_record("call")
    prepared = quality.prepare_asset(data, "W", tmp_path, snap, sample_after_publication=True, now=T0)
    sidecar_path = Path(prepared["path"]).with_suffix(".json")
    registered = {"sha256": prepared["sha256"], "image_quality": prepared["image_quality"]}
    rows = [{"state": "PUBLISHED", "day": "2026-11-26", "images": [registered]}]
    calls: list[dict] = []

    # Evening run 1 at T0 hits CODEX_USAGE_LIMIT -> sidecar becomes REVIEW_UNAVAILABLE, weekly observed == 0.
    run1 = quality.publication_sample(rows, "2026-11-26", run_vision=True, vision_runner=_quota_failure_runner(calls), now=T0)
    assert len(calls) == 1
    assert run1["images"][0]["image_quality"]["vision"]["status"] == "REVIEW_UNAVAILABLE"
    assert run1["weekly"]["observed"] == 0 and run1["weekly"]["selected"] == 1
    unavailable_bytes = sidecar_path.read_bytes()

    # Run 2 inside cooldown: zero Codex calls.
    run2 = quality.publication_sample(
        rows, "2026-11-26", run_vision=True,
        vision_runner=lambda *a, **k: pytest.fail("sampled_review must honor cooldown"),
        now=T0 + timedelta(seconds=299),
    )
    assert run2["weekly"]["observed"] == 0

    # Run 3 past cooldown with run_vision=False (read-only): zero Codex calls.
    t1 = T0 + timedelta(seconds=quality.REVIEW_UNAVAILABLE_RETRY_COOLDOWN_SECONDS)
    run3 = quality.publication_sample(
        rows, "2026-11-26", run_vision=False,
        vision_runner=lambda *a, **k: pytest.fail("run_vision=False must not call Codex"),
        now=t1,
    )
    assert run3["weekly"]["observed"] == 0

    # Run 4 past cooldown with run_vision=True: retries Codex, retains prior failure bytes, counts toward weekly sample.
    run4 = quality.publication_sample(rows, "2026-11-26", run_vision=True, vision_runner=_passing_vision_runner(calls), now=t1)
    assert len(calls) == 2
    q4 = run4["images"][0]["image_quality"]
    assert q4["passed"] is True and q4["score"] == 10
    assert q4["vision"]["status"] == "REVIEWED"
    assert q4["vision"]["transient_retry_count"] == 1
    assert Path(q4["vision"]["retained_prior_failure_path"]).read_bytes() == unavailable_bytes
    assert run4["weekly"]["observed"] == 1 and run4["weekly"]["images"] == [prepared["sha256"]]

    # Run 5 after recovery: cached REVIEWED result, zero Codex calls.
    run5 = quality.publication_sample(
        rows, "2026-11-26", run_vision=True,
        vision_runner=lambda *a, **k: pytest.fail("completed sample must not re-call Codex"),
        now=t1 + timedelta(hours=1),
    )
    assert run5["weekly"]["observed"] == 1


def test_sampled_review_never_retries_scored_rejection_and_refuses_tampered_png(tmp_path):
    snap = capture(tmp_path)
    data = input_record("call")
    prepared = quality.prepare_asset(data, "W", tmp_path, snap, sample_after_publication=True, now=T0)
    registered = {"sha256": prepared["sha256"], "image_quality": prepared["image_quality"]}
    calls: list[dict] = []

    # Scored 7/10 rejection in sampled_review must never retry later.
    first = quality.sampled_review(
        registered, run_vision=True,
        vision_runner=_passing_vision_runner(calls, points={"4": False, "8": False, "10": False}),
        now=T0,
    )
    assert len(calls) == 1 and first["vision"]["status"] == "REVIEWED" and first["passed"] is False
    again = quality.sampled_review(
        registered, run_vision=True,
        vision_runner=lambda *a, **k: pytest.fail("scored rejection in sampled_review must never retry"),
        now=T0 + timedelta(hours=4),
    )
    assert again["vision"]["status"] == "REVIEWED" and again["passed"] is False

    # Separate asset: transient unavailable followed by PNG tampering fails code_check before Codex.
    sub = tmp_path / "tampered"
    sub.mkdir()
    snap2 = capture(sub)
    prepared2 = quality.prepare_asset(data, "W", sub, snap2, sample_after_publication=True, now=T0)
    reg2 = {"sha256": prepared2["sha256"], "image_quality": prepared2["image_quality"]}
    calls2: list[dict] = []
    quality.sampled_review(reg2, run_vision=True, vision_runner=_quota_failure_runner(calls2), now=T0)
    assert len(calls2) == 1
    Path(prepared2["path"]).write_bytes(Path(prepared2["path"]).read_bytes() + b"\x00")
    t1 = T0 + timedelta(seconds=quality.REVIEW_UNAVAILABLE_RETRY_COOLDOWN_SECONDS)
    tampered_res = quality.sampled_review(
        reg2, run_vision=True,
        vision_runner=lambda *a, **k: pytest.fail("tampered PNG must fail code_check before Codex"),
        now=t1,
    )
    assert tampered_res["vision"]["status"] == "CODE_REFUSED"
    assert tampered_res["passed"] is False


def test_plan_snapshot_deduplicates_repeated_timeout_image_held_outcomes(tmp_path, monkeypatch):
    outcomes_path = tmp_path / "outcomes.jsonl"
    monkeypatch.setattr(tv, "OUTCOMES", outcomes_path)
    row = {"key": "nov12-timeout-flood", "symbol": "USDJPY", "at_utc": T0.isoformat(), "levels": {}}
    attempts = []

    def timeout_capture(*args, **kwargs):
        attempts.append(1)
        raise tv.SnapshotError("TRADINGVIEW_SNAPSHOT_TIMEOUT")

    # First call exhausts 2 attempts -> records exactly ONE IMAGE_HELD row.
    with pytest.raises(tv.SnapshotPending, match="TRADINGVIEW_SNAPSHOT_TIMEOUT"):
        tv.plan_snapshot(row, tmp_path / "held", snapshot=timeout_capture, image_input=input_record(), now=T0)
    assert len(attempts) == 2
    rows_after_first = _read_outcomes(outcomes_path)
    assert len(rows_after_first) == 1
    assert rows_after_first[0]["status"] == "IMAGE_HELD"
    assert rows_after_first[0]["cause"] == "TRADINGVIEW_SNAPSHOT_TIMEOUT"

    # 10 repeated minute ticks on the unchanged exhausted IMAGE_HELD state must emit ZERO duplicate rows.
    for tick in range(1, 11):
        with pytest.raises(tv.SnapshotPending, match="TRADINGVIEW_SNAPSHOT_TIMEOUT"):
            tv.plan_snapshot(
                row, tmp_path / "held",
                snapshot=lambda *a, **k: pytest.fail("exhausted state must not recapture"),
                image_input=input_record(),
                now=T0 + timedelta(minutes=tick),
            )
    assert len(_read_outcomes(outcomes_path)) == 1


def test_plan_snapshot_deduplicates_cached_vision_image_held_and_recovers_after_cooldown(tmp_path, monkeypatch):
    outcomes_path = tmp_path / "outcomes.jsonl"
    monkeypatch.setattr(tv, "OUTCOMES", outcomes_path)
    row = {"key": "vision-hold-recovery", "symbol": "USDJPY", "at_utc": T0.isoformat(), "levels": {}}
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    snap = capture(source_dir)
    capture_calls: list[str] = []
    vision_calls: list[dict] = []
    mode = {"runner": _quota_failure_runner(vision_calls)}

    real_review = quality.review_vision

    def controlled_review(asset, *, runner=None, now=None):
        return real_review(asset, runner=mode["runner"], now=now)

    monkeypatch.setattr(quality, "review_vision", controlled_review)

    def take(market, interval, folder):
        capture_calls.append(market)
        return snap

    # Tick 1 at T0: single capture, transient CODEX_USAGE_LIMIT -> 1 IMAGE_HELD outcome.
    with pytest.raises(tv.TemplateImageRefused, match="IMAGE_VISION_REVIEW_REQUIRED_OR_FAILED"):
        tv.plan_snapshot(row, tmp_path / "post", snapshot=take, image_input=input_record(), now=T0)
    assert capture_calls == ["USDJPY"] and len(vision_calls) == 1
    assert [r["status"] for r in _read_outcomes(outcomes_path)] == ["IMAGE_HELD"]

    # Ticks 2-4 inside 300s cooldown: ZERO recaptures, ZERO Codex retries, ZERO duplicate outcome rows.
    for minute in (1, 2, 4):
        with pytest.raises(tv.TemplateImageRefused, match="IMAGE_VISION_REVIEW_REQUIRED_OR_FAILED"):
            tv.plan_snapshot(
                row, tmp_path / "post",
                snapshot=lambda *a, **k: pytest.fail("held snapshot must be reused"),
                image_input=input_record(),
                now=T0 + timedelta(minutes=minute),
            )
    assert capture_calls == ["USDJPY"] and len(vision_calls) == 1
    assert [r["status"] for r in _read_outcomes(outcomes_path)] == ["IMAGE_HELD"]

    # Tick 5 at T0 + 5m: Codex recovers -> ZERO recaptures, 1 vision retry, state transitions IMAGE_HELD -> CAPTURED.
    mode["runner"] = _passing_vision_runner(vision_calls)
    recovered = tv.plan_snapshot(
        row, tmp_path / "post",
        snapshot=lambda *a, **k: pytest.fail("held snapshot must be reused on recovery"),
        image_input=input_record(),
        now=T0 + timedelta(seconds=quality.REVIEW_UNAVAILABLE_RETRY_COOLDOWN_SECONDS),
    )
    assert capture_calls == ["USDJPY"] and len(vision_calls) == 2
    assert recovered["image_quality"]["passed"] is True
    assert recovered["image_quality"]["vision"]["transient_retry_count"] == 1
    assert [r["status"] for r in _read_outcomes(outcomes_path)] == ["IMAGE_HELD", "CAPTURED"]
    state = json.loads((tmp_path / "post" / "tradingview_capture_cc465_v1.json").read_bytes())
    assert state["status"] == "CAPTURED"


def test_plan_snapshot_cache_hit_vision_hold_persists_snapshot_past_cache_ttl(tmp_path, monkeypatch):
    outcomes_path = tmp_path / "outcomes.jsonl"
    monkeypatch.setattr(tv, "OUTCOMES", outcomes_path)
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    snap = capture(source_dir)
    # Seed the shared market cache file so Tick 1 enters via cache hit before the capture loop.
    cache_dir = tmp_path / "tradingview_cache"
    cache_dir.mkdir()
    (cache_dir / "USDJPY_cc465.json").write_text(json.dumps(snap, sort_keys=True), encoding="utf-8")
    row = {"key": "cache-hit-hold", "symbol": "USDJPY", "at_utc": T0.isoformat(), "levels": {}}
    vision_calls: list[dict] = []
    mode = {"runner": _quota_failure_runner(vision_calls)}
    real_review = quality.review_vision
    monkeypatch.setattr(quality, "review_vision", lambda a, *, runner=None, now=None: real_review(a, runner=mode["runner"], now=now))

    # Tick 1 at snap capture time: cache hit fails vision -> persists IMAGE_HELD + snapshot + 1 outcome.
    snap_time = datetime.fromisoformat(snap["captured_at_utc"].replace("Z", "+00:00"))
    with pytest.raises(tv.TemplateImageRefused, match="IMAGE_VISION_REVIEW_REQUIRED_OR_FAILED"):
        tv.plan_snapshot(
            row, tmp_path / "post",
            snapshot=lambda *a, **k: pytest.fail("should use market cache"),
            image_input=input_record(),
            now=snap_time + timedelta(seconds=30),
        )
    assert len(vision_calls) == 1
    assert [r["status"] for r in _read_outcomes(outcomes_path)] == ["IMAGE_HELD"]
    held_state = json.loads((tmp_path / "post" / "tradingview_capture_cc465_v1.json").read_bytes())
    assert held_state["status"] == "IMAGE_HELD" and held_state["snapshot"]["sha256"] == snap["sha256"]

    # Tick 2 after 15-minute cache TTL expires: still reuses persisted state["snapshot"] and recovers!
    mode["runner"] = _passing_vision_runner(vision_calls)
    recovered = tv.plan_snapshot(
        row, tmp_path / "post",
        snapshot=lambda *a, **k: pytest.fail("persisted held snapshot must prevent recapture after cache expiry"),
        image_input=input_record(),
        now=snap_time + timedelta(minutes=25),
    )
    assert len(vision_calls) == 2 and recovered["image_quality"]["passed"] is True
    assert [r["status"] for r in _read_outcomes(outcomes_path)] == ["IMAGE_HELD", "CAPTURED"]


def test_template_acceptance_requires_all_seven_core_markets_including_ustec():
    revision = "cc788-rev"
    all_reviews = [
        {"template": "call", "template_revision": revision, "score": 10, "passed": True,
         "real_snapshot": True, "market": market, "master": master, "image_sha256": f"{market}-{master}"}
        for market in inputs.ORDER for master in ("W", "T")
    ]
    assert len(inputs.ORDER) == 7 and "USTEC" in inputs.ORDER

    # 12 PNGs (six markets only, missing USTEC W & T) must fail with required == 14.
    six_only = [r for r in all_reviews if r["market"] != "USTEC"]
    partial = quality.template_acceptance(six_only, "call", revision)
    assert partial["required"] == 14 and partial["observed"] == 12 and partial["passed"] is False
    assert partial["missing"] == [{"market": "USTEC", "master": "T"}, {"market": "USTEC", "master": "W"}]

    # All 14 distinct real PNGs pass with required == observed == 14.
    full = quality.template_acceptance(all_reviews, "call", revision)
    assert full["required"] == 14 and full["observed"] == 14 and full["passed"] is True and full["missing"] == []


@pytest.mark.parametrize("leaked_model", ["ChatGPT", "Sonnet", "Haiku", "Luna"])
def test_code_check_blocks_decision_109_model_names_and_prompt_omits_antigravity(tmp_path, leaked_model):
    snap = capture(tmp_path)
    data = input_record("call")
    prepared = quality.prepare_asset(data, "W", tmp_path, snap, sample_after_publication=True, now=T0)

    # Vision prompt must stay Codex-only with zero retired Antigravity/read_file instructions.
    calls: list[dict] = []
    res = quality.review_vision(prepared, runner=_passing_vision_runner(calls), now=T0)
    assert res["status"] == "REVIEWED" and len(calls) == 1
    prompt_text = calls[0]["prompt"]
    assert prompt_text.startswith("Do not call any tool.")
    assert "Antigravity" not in prompt_text and "read_file" not in prompt_text

    # code_check must refuse Decision 109 model names in rendered template texts.
    tampered = json.loads(json.dumps(prepared))
    tampered["image_template"]["texts"] = [
        *tampered["image_template"]["texts"],
        {"text": f"Reviewed by {leaked_model}", "field": "footer", "box": [0, 0, 10, 10],
         "zone": [0, 0, 20, 20], "size": 36, "colour": "#111111"},
    ]
    checked = quality.code_check(tampered)
    assert checked["passed"] is False and "IMAGE_INTERNAL_LANGUAGE" in checked["causes"]
