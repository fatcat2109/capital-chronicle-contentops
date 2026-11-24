"""CC-785 hotfix (24 Nov 2026; Jim: 7.6 minutes for the Nvidia headlines is far too serious). Under memory pressure the
locked Chrome missed single 3 s probes while alive; the runner then counted it dead and waited 30 minutes."""
from __future__ import annotations

from live_contentops import x_list_feed_v1 as feed
from test_x_list_feed_cc258 import FakeBootstrap, _runner


class FlakyProbeBootstrap(FakeBootstrap):
    def __init__(self, misses, **kwargs):
        super().__init__(alive=True, **kwargs)
        self.misses, self.probes = misses, 0

    def probe_cdp(self, port, **kwargs):
        self.probes += 1
        return {"cdp_alive": self.probes > self.misses}


def test_a_slow_browser_that_misses_two_probes_is_still_ready_and_never_relaunched(tmp_path):
    bootstrap = FlakyProbeBootstrap(misses=2)
    runner = _runner(tmp_path, bootstrap, lambda: 0.0)
    state = runner._browser_ready()
    assert state["ready"] is True and bootstrap.probes == 3 and bootstrap.launches == 0


def test_a_browser_that_misses_every_probe_waits_two_minutes_not_thirty(tmp_path):
    assert feed.RELAUNCH_AFTER_SECONDS == 120.0
    ticks = iter([0.0, 100.0, 130.0])
    bootstrap = FakeBootstrap()
    runner = _runner(tmp_path, bootstrap, lambda: next(ticks))
    runner.iterate()
    assert bootstrap.launches == 1
    waiting = runner.iterate()
    assert waiting["capture"]["state"] == "BROWSER_NOT_READY" and bootstrap.launches == 1
    runner.iterate()
    assert bootstrap.launches == 2
