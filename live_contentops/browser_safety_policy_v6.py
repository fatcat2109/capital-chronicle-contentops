"""V6 Browser Safety Policy.

Defines rules and safety flags forbidding automated browser sessions from mutating live resources.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"


def get_safety_policy() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "real_substack_navigation_allowed": False,
        "real_browser_profile_allowed": False,
        "cookie_read_allowed": False,
        "local_storage_read_allowed": False,
        "session_storage_read_allowed": False,
        "cdp_token_inspection_allowed": False,
        "account_switching_allowed": False,
        "live_publish_click_allowed": False,
        "live_schedule_click_allowed": False,
        "screenshot_allowed_local_mock_only": True,
        "network_allowed": False,
        "env_read_allowed": False,
        "credentials_hydrated": False,
        "public_url_capture_allowed": False,
        "manual_fallback_available": True
    }


def validate_safety_compliance(
    runtime_state: dict[str, Any]
) -> dict[str, Any]:
    """Ensures runtime execution parameters do not violate the browser safety policy."""
    policy = get_safety_policy()
    blockers = []
    
    # Assert navigation compliance
    if runtime_state.get("real_substack_opened", False):
        blockers.append("real_platform_navigation_detected")
        
    # Assert secret/session lookup compliance
    if runtime_state.get("browser_session_secret_accessed", False):
        blockers.append("browser_secret_access_detected")
        
    # Assert clickable controls compliance
    if runtime_state.get("live_publish_control_enabled", False):
        blockers.append("executable_publish_control_detected")
        
    # Assert public URL compliance
    if runtime_state.get("public_url_captured", False):
        blockers.append("fake_public_result_detected")
        
    # Assert live flags compliance
    if runtime_state.get("dispatch_allowed_now", False) or runtime_state.get("live_write_allowed_now", False):
        blockers.append("unexpected_live_status_claim")
        
    # Standard blockers
    blockers.extend([
        "source_verification_required",
        "publication_blocked_until_source_verification"
    ])
    
    compliance_passed = len(blockers) == 0
    
    return {
        "schema_version": SCHEMA_VERSION,
        "compliance_passed": compliance_passed,
        "blocker_count": len(blockers),
        "blockers": sorted(list(set(blockers)))
    }
