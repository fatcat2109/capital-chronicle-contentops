"""A standing article remains in its actual publication day after late reconciliation."""
import json

import pytest

from live_contentops.native_newsroom_volume_v1 import persist_native_day_measurement
from live_contentops.newsroom_production_day_v1 import newsroom_production_day_id


@pytest.mark.parametrize("window", [False, True])
def test_day_projection_uses_actual_publication_for_standing_and_frozen_window_cutoff(tmp_path, monkeypatch, window):
    published_at = "2020-11-05T18:44:51Z"  # 01:44 Bangkok, before the 02:00 boundary.
    cutoff = "2020-11-06T17:57:44Z"
    reference = cutoff if window else published_at
    expected_day = newsroom_production_day_id(reference)

    class Store:
        def list_outbox_messages(self): return []
        def list_platform_dispatches(self): return []
        def list_performance_observations(self): return []

    monkeypatch.setattr("live_contentops.native_finished_publication_v1.confirmed_canonicals",
        lambda store: iter([{"run_id": "retained", "published_at_utc": published_at,
                             "first_readback_utc": "2020-11-06T19:10:00Z"}]))
    monkeypatch.setattr("live_contentops.native_brief_windows_v1.quota_stop_observations", lambda *a, **k: [])
    output = tmp_path / expected_day / "window" / "retained" if window else tmp_path / "manual" / "retained"
    binding = {"run_id": "retained", "owner_manual_live": True, "cutoff_utc": cutoff,
               "output_dir": str(output), "published_memory_output_root": str(tmp_path / "published")}
    if window:
        binding["window_id"] = "window"
    path = persist_native_day_measurement(Store(), binding)
    result = json.loads(open(path, encoding="utf-8").read())
    assert result["newsroom_production_day_id"] == expected_day
    assert expected_day in path
    assert result["native_volume_measurement"]["observed_at_utc"] > published_at
