from __future__ import annotations

import pytest

from live_contentops.source_route_health_v1 import (
    SourceRouteHealthState,
    load_source_route_health_snapshot_read_only,
    persist_source_route_health_snapshot,
)


def test_routing_only_snapshot_round_trips_atomically(tmp_path):
    state = SourceRouteHealthState()
    state.observe_failure(
        "https://www.bloomberg.com/news/articles/exact-current-story", 403
    )
    path = tmp_path / "source_route_health_v1.json"

    persisted = persist_source_route_health_snapshot(path, state.snapshot())

    loaded = load_source_route_health_snapshot_read_only(persisted)
    assert loaded["routing_only"] is True
    assert loaded["routes"][0]["last_failure_class"] == "HTTP_403"
    assert loaded["sourceability_or_health_grants_factual_authority"] is False
    assert not list(tmp_path.glob(".*.tmp"))


def test_persistence_rejects_authority_inflation(tmp_path):
    value = SourceRouteHealthState().snapshot()
    value["sourceability_or_health_grants_factual_authority"] = True

    with pytest.raises(ValueError, match="source_route_health_snapshot_invalid"):
        persist_source_route_health_snapshot(
            tmp_path / "source_route_health_v1.json", value
        )
