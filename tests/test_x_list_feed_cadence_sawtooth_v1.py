"""CC-785 sawtooth cadence regression tests: zero false ~62s STALE flaps on healthy quiet feeds.

Strictly hermetic: local fakes only, all files under tmp_path, zero live browser/CDP/network
calls, zero production file writes.

Operator: T3 Code, Gemini 4 Neon xhigh, antigravity_14
"""
from __future__ import annotations

from datetime import timedelta
import json

from live_contentops import x_list_feed_v1 as feed
from test_x_list_feed_cc785 import FakeBootstrap, FakeCDP, FakeIngestion, Harness, NOW


class LatencyHarness(Harness):
    """Simulates realistic reload latency and light-refresh settle elapsed time on the virtual clock."""

    def __init__(self, tmp_path, *, reload_latency: float = 3.5, light_settle: float = 5.06,
                 after_response: float = 1.0, cdp: FakeCDP | None = None):
        self.reload_latency = reload_latency
        self.light_settle = light_settle
        self.after_response = after_response
        super().__init__(tmp_path, cdp=cdp)

        harness = self

        class RealisticCapture(feed.MinuteCapture):
            def _drain(self, client, seconds, counts, page_call, *, until_response):
                before_resp = counts["responses"]
                super()._drain(client, min(seconds, 0.05), counts, page_call, until_response=until_response)
                if until_response:
                    if counts["responses"] > before_resp:
                        # Timeline response landed at reload/light latency; settle finishes after_response later.
                        harness.t[0] += harness.reload_latency
                        self.last_timeline_mono = harness.t[0]
                        self.last_timeline_utc = feed._iso(harness.now())
                        harness.t[0] += harness.after_response
                    else:
                        # Quiet settle expired without a timeline response.
                        harness.t[0] += seconds

            def tick(self, **kwargs):
                kwargs.setdefault("settle_seconds", feed.TIMELINE_SETTLE_SECONDS)
                kwargs.setdefault("light_settle_seconds", harness.light_settle)
                kwargs.setdefault("scroll_seconds", 0)
                return super().tick(**kwargs)

        self.capture = RealisticCapture(
            module=FakeIngestion(tmp_path),
            targets_fn=self.cdp.targets,
            client_factory=self.cdp.client,
            http_open=self.cdp.http_open,
            now_fn=self.now,
            mono_fn=lambda: self.t[0],
        )
        self.runner = self.new_runner()


def test_healthy_quiet_feed_with_realistic_reload_latency_never_flaps_stale(tmp_path):
    """Replays live ~3.5s reload + 5.06s light-settle cadence across 10 minutes: zero STALE flaps."""
    h = LatencyHarness(tmp_path, reload_latency=3.5, light_settle=5.06, after_response=1.0)
    records = []
    # 15s market-hours ticks over 10 minutes (41 ticks total, t=0..600s).
    for tick_start in range(0, 601, 15):
        h.t[0] = float(tick_start)
        records.append(h.runner.iterate())

    health_states = [rec["health"]["state"] for rec in records]
    max_age = max(rec["health"]["last_good_age_seconds"] for rec in records)

    assert all(state == "OK" for state in health_states), f"Unexpected non-OK states: {health_states}"
    assert max_age < feed.STALE_AFTER_MARKET_SECONDS
    # Reload rate stays bounded to at most 1 per minute (11 reloads across t=0,60,120,...,600).
    assert h.cdp.count("Page.reload") == 11
    assert h.runner.failure_streak == 0
    assert h.runner.p1 is None


def test_slow_11s_reload_reloads_on_next_minute_without_75s_sawtooth(tmp_path):
    """Replays live 11:19:41Z slow reload (10.3s capture + 1.0s settle): Tick 4 reloads at t=60s cleanly."""
    h = LatencyHarness(tmp_path, reload_latency=10.3, light_settle=5.07, after_response=1.0)
    seen = []
    for tick_start in (0, 15, 30, 45, 60, 75, 90, 105, 120):
        h.t[0] = float(tick_start)
        seen.append(h.runner.iterate())

    assert [r["health"]["state"] for r in seen] == ["OK"] * len(seen)
    assert seen[4]["capture"]["refresh"] == "reload"
    assert seen[4]["capture"]["state"] == "CAPTURED"
    assert seen[8]["capture"]["refresh"] == "reload"
    assert h.cdp.count("Page.reload") == 3
    assert max(r["health"]["last_good_age_seconds"] for r in seen) < 50.0


def test_subsecond_tick_jitter_does_not_skip_minute_reload_or_light_refresh(tmp_path):
    """Replays live 13ms-150ms scheduling jitter so neither light refresh nor 60s reload slips 15s."""
    h = LatencyHarness(tmp_path, reload_latency=3.4, light_settle=5.06, after_response=1.0)
    h.t[0] = 0.0
    first = h.runner.iterate()
    assert first["capture"]["refresh"] == "reload" and first["health"]["state"] == "OK"

    # Tick 1 (15s), Tick 2 (30s -> light), Tick 3 arrives 13ms early (44.987s -> light still fires),
    # Tick 4 arrives 150ms early (59.85s -> reload still fires instead of slipping to 75s STALE).
    for ts in (15.0, 30.0, 44.987):
        h.t[0] = ts
        rec = h.runner.iterate()
        assert rec["health"]["state"] == "OK"
    assert h.capture.light_misses == 2

    h.t[0] = 59.85
    tick4 = h.runner.iterate()
    assert tick4["capture"]["refresh"] == "reload"
    assert tick4["capture"]["state"] == "CAPTURED"
    assert tick4["health"]["state"] == "OK"
    assert h.cdp.count("Page.reload") == 2


def test_post_light_capture_quiet_stretch_reloads_before_60s_stale_boundary(tmp_path):
    """After a light-refresh hit at t=33.0s, quiet ticks reload at t=90s (tl_age=57.0s) without flapping STALE."""
    h = LatencyHarness(tmp_path, reload_latency=3.0, light_settle=5.08, after_response=1.0)
    h.t[0] = 0.0
    h.runner.iterate()  # reload at t=0 -> last_timeline=3.0

    # Tick 1 at t=15.0 listens (tl_age=12.0 < 14.5); Tick 2 at t=30.0 fires light refresh (captures t=33.0).
    h.cdp.light_serves = True
    h.t[0] = 15.0
    assert h.runner.iterate()["health"]["state"] == "OK"
    h.t[0] = 30.0
    hit = h.runner.iterate()
    assert hit["capture"]["refresh"] == "light" and hit["capture"]["state"] == "CAPTURED"

    # Quiet stretch after the light hit: ticks at 45, 60, 75, 90.
    h.cdp.light_serves = False
    recs = []
    for ts in (45.0, 60.0, 75.0, 90.0):
        h.t[0] = ts
        recs.append(h.runner.iterate())

    assert [r["health"]["state"] for r in recs] == ["OK", "OK", "OK", "OK"]
    # At t=90, tl_age=57.0 >= 45.0 and rel_age=90.0 >= 59.5 -> reloads cleanly instead of 62s STALE.
    assert recs[-1]["capture"]["refresh"] == "reload"
    assert recs[-1]["capture"]["state"] == "CAPTURED"


def test_c7_honesty_genuine_timeline_stall_still_goes_stale_and_raises_p1(tmp_path):
    """Genuine reload failure / stalled timeline MUST still go STALE at >=60s and P1 at streak=3 (C7)."""
    h = LatencyHarness(tmp_path, reload_latency=3.0, light_settle=5.0, after_response=1.0)
    h.t[0] = 0.0
    assert h.runner.iterate()["health"]["state"] == "OK"

    # X stops returning ListLatestTweetsTimeline completely.
    h.cdp.reload_serves = False
    h.cdp.light_serves = False
    for ts in (15.0, 30.0, 45.0):
        h.t[0] = ts
        rec = h.runner.iterate()
        assert rec["capture"]["state"] == "LISTENING"
        assert rec["health"]["state"] == "OK"

    # At t=60, reload fires, waits full settle (15s -> t=75), gets NO_TIMELINE_RESPONSE -> STALE!
    h.t[0] = 60.0
    stalled = h.runner.iterate()
    assert stalled["capture"]["refresh"] == "reload"
    assert stalled["capture"]["state"] == "NO_TIMELINE_RESPONSE"
    assert stalled["health"]["state"] == "STALE"
    assert stalled["health"]["stale_since_utc"] == feed._iso(NOW + timedelta(seconds=3.0))
    assert stalled["health"]["last_good_age_seconds"] >= feed.STALE_AFTER_MARKET_SECONDS
    assert stalled["health"]["failure_streak"] == 1

    # Subsequent quiet ticks while reload budget is spent stay STALE (light_refresh misses NEVER mask staleness).
    h.t[0] = 90.0
    still_stale = h.runner.iterate()
    assert still_stale["capture"]["state"] == "LISTENING"
    assert still_stale["health"]["state"] == "STALE"

    # Continued reload failures at t=120 and t=180 trigger step-1 heal (streak=2) and P1 (streak=3).
    h.t[0] = 120.0
    fail2 = h.runner.iterate()
    assert fail2["capture"]["state"] == "NO_TIMELINE_RESPONSE"
    assert fail2["health"]["failure_streak"] == 2
    assert fail2["health"]["state"] == "STALE"
    assert "tab_replacement" in fail2["capture"]

    # After heal_target resets last_reload_mono=None, next tick at t=150 immediately attempts reload -> streak=3 -> P1.
    h.t[0] = 150.0
    fail3 = h.runner.iterate()
    assert fail3["capture"]["state"] == "NO_TIMELINE_RESPONSE"
    assert fail3["health"]["failure_streak"] == 3
    assert fail3["health"]["state"] == "P1"
    assert fail3["p1"]["event"] == "RAISED"
