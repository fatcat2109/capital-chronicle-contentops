from __future__ import annotations

from live_contentops import destination_performance_observer_v1 as observer


def test_current_binding_missing_is_auth_required_and_never_zero_filled(monkeypatch):
    monkeypatch.setattr(observer, "_meta_token", lambda *_names: "")

    result = observer.collect_current_authorized_destination_metrics(
        destination="facebook_page", public_object_id="exact-post"
    )

    assert result["status"] == "AUTH_REQUIRED"
    assert result["provider_requests"] == 0
    assert result["metrics"] == {}
    assert result["availability"]["likes"] == "AUTH_REQUIRED"
    assert result["public_write_performed"] is False
    assert result["additional_scope_requested"] is False


def test_facebook_exact_object_read_returns_bounded_metrics_and_interactions(monkeypatch):
    requests = []
    monkeypatch.setattr(observer, "_meta_token", lambda *_names: "existing-binding")
    monkeypatch.setattr(
        observer,
        "_get_json",
        lambda url, params: requests.append((url, params)) or {
            "likes": {"summary": {"total_count": 7}},
            "shares": {"count": 2},
            "comments": {
                "summary": {"total_count": 1},
                "data": [{"id": "comment-1", "message": "Useful context"}],
            },
        },
    )

    result = observer.collect_current_authorized_destination_metrics(
        destination="facebook_page", public_object_id="exact-post"
    )

    assert len(requests) == 1
    assert requests[0][0].endswith("/exact-post")
    assert result["status"] == "COLLECTED"
    assert result["provider_requests"] == 1
    assert result["metrics"] == {"likes": 7, "comments": 1, "shares": 2}
    assert result["interactions"] == [
        {
            "interaction_id": "comment-1",
            "text": "Useful context",
            "platform": "facebook_page",
        }
    ]
    assert result["public_write_performed"] is False


def test_current_non_metrics_bindings_are_truthfully_not_exposed():
    for destination in ("telegram", "x", "youtube"):
        result = observer.collect_current_authorized_destination_metrics(
            destination=destination, public_object_id="exact-object"
        )
        assert result["status"] == "NOT_EXPOSED"
        assert result["provider_requests"] == 0
        assert result["metrics"] == {}
        assert result["availability"]["views"] == "NOT_EXPOSED"
        assert result["public_write_performed"] is False
