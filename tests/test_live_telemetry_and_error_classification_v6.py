"""Unit tests for live telemetry collection and diagnostic error classification."""
from __future__ import annotations

import os
import tempfile
import pytest

from live_contentops import live_telemetry_v6 as lt
from live_contentops.platform_error_classifier import PlatformErrorSafetyError


def test_telemetry_event_model():
    event = lt.TelemetryEvent(
        platform_id="threads",
        action="post",
        success=True,
        latency_ms=450.5,
        payload_size_bytes=100,
        response_summary="Success",
    )
    data = event.to_dict()
    assert data["platform_id"] == "threads"
    assert data["success"] is True
    assert data["latency_ms"] == 450.5
    assert "event_id" in data
    assert "timestamp" in data


def test_telemetry_registry_atomic_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_file = os.path.join(tmpdir, "telemetry.jsonl")
        registry = lt.TelemetryRegistry(temp_file)

        # 1. Empty registry checks
        assert len(registry.get_events()) == 0
        summary = registry.get_summary()
        assert summary["total_dispatches"] == 0
        assert summary["success_count"] == 0

        # 2. Record success event
        ev1 = lt.TelemetryEvent(
            platform_id="facebook_page",
            action="post",
            success=True,
            latency_ms=150.0,
            payload_size_bytes=50,
            response_summary="Created post 123",
        )
        registry.record_event(ev1)
        assert len(registry.get_events()) == 1

        # 3. Record failure event
        ev2 = lt.TelemetryEvent(
            platform_id="facebook_page",
            action="comment",
            success=False,
            latency_ms=200.0,
            error_class="permission_missing",
            severity="blocker",
            payload_size_bytes=30,
            response_summary="Forbidden",
        )
        registry.record_event(ev2)
        assert len(registry.get_events()) == 2

        # 4. Record another platform event
        ev3 = lt.TelemetryEvent(
            platform_id="instagram",
            action="post",
            success=False,
            latency_ms=300.0,
            error_class="media_requirement_missing",
            severity="blocker",
            payload_size_bytes=80,
            response_summary="Bad format",
        )
        registry.record_event(ev3)

        # 5. Check summary calculations
        sum_data = registry.get_summary()
        assert sum_data["total_dispatches"] == 3
        assert sum_data["success_count"] == 1
        assert sum_data["failure_count"] == 2
        assert sum_data["avg_latency_ms"] == 216.66666666666666

        fb_stats = sum_data["platforms"]["facebook_page"]
        assert fb_stats["total"] == 2
        assert fb_stats["success"] == 1
        assert fb_stats["failure"] == 1
        assert fb_stats["avg_latency_ms"] == 175.0
        assert fb_stats["error_classes"]["permission_missing"] == 1

        ig_stats = sum_data["platforms"]["instagram"]
        assert ig_stats["total"] == 1
        assert ig_stats["success"] == 0
        assert ig_stats["failure"] == 1
        assert ig_stats["avg_latency_ms"] == 300.0
        assert ig_stats["error_classes"]["media_requirement_missing"] == 1


def test_classify_and_record_meta_permission_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_file = os.path.join(tmpdir, "telemetry.jsonl")

        adapter_res = {
            "status": "FAILED",
            "error_code": 400,
            "error_response": {
                "error": {
                    "message": "Requires instagram_content_publish permission to manage the object",
                    "type": "OAuthException",
                    "code": 10,
                }
            },
        }

        event = lt.classify_and_record_dispatch(
            platform_id="instagram",
            action="post",
            adapter_result=adapter_res,
            latency_ms=125.0,
            payload_size_bytes=100,
            registry_file=temp_file,
        )

        assert event.success is False
        assert event.error_class == "permission_missing"
        assert event.severity == "blocker"
        assert "instagram_content_publish" in event.response_summary


def test_classify_and_record_meta_media_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_file = os.path.join(tmpdir, "telemetry.jsonl")

        adapter_res = {
            "status": "FAILED_STEP_1",
            "error_code": 400,
            "error_response": {
                "error": {
                    "message": "Only photo or video can be accepted as media type.",
                    "type": "OAuthException",
                    "code": 9004,
                }
            },
        }

        event = lt.classify_and_record_dispatch(
            platform_id="instagram",
            action="post",
            adapter_result=adapter_res,
            latency_ms=150.0,
            payload_size_bytes=120,
            registry_file=temp_file,
        )

        assert event.success is False
        assert event.error_class == "media_requirement_missing"
        assert event.severity == "blocker"


def test_sanitize_and_safety_checks():
    # 1. Test secret sanitization helper
    raw_error = "OAuthException: token 1234567890:ABCdef123XYZ456_abc_def, jwt=eyJhbGciOi.eyJzdWIiOi.signature"
    clean = lt.sanitize_summary(raw_error)
    assert "1234567890:ABCdef123XYZ456_abc_def" not in clean
    assert "eyJhbGciOi" not in clean
    assert "<redacted_bot_token>" in clean
    assert "<redacted_jwt>" in clean

    # 2. Assert telemetry event fails if raw secrets are supplied directly to registry bypass
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_file = os.path.join(tmpdir, "telemetry.jsonl")
        registry = lt.TelemetryRegistry(temp_file)

        unsafe_ev = lt.TelemetryEvent(
            platform_id="x",
            action="post",
            success=False,
            response_summary="raw_response containing token=123456:ABCdef123XYZ456_abc_def_ghi_jkl"
        )
        # Directly recording should throw error due to security key check
        with pytest.raises(PlatformErrorSafetyError):
            registry.record_event(unsafe_ev)
