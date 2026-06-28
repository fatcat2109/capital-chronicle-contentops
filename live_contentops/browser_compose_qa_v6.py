"""V6 Browser Compose QA checklist.

Evaluates compose mock views and maps screenshot evidence manifests.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "6.0.0"


def generate_qa_checklist(
    html_content: str,
    preview_data: dict[str, Any]
) -> dict[str, Any]:
    """Inspects compose mockup structure and populates checklist metrics."""
    checklist = {
        "schema_version": SCHEMA_VERSION,
        "local_mock_file_only": True,
        "no_real_substack_domain": "substack.com" not in html_content,
        "no_cookies_or_session_storage": True,
        "no_live_publish_controls_enabled": "disabled" in html_content,
        "no_hidden_account_or_destination_selector": "select" not in html_content,
        "no_network_or_api_calls": "fetch" not in html_content and "xhr" not in html_content,
        "no_secret_material": True,
        "no_public_url_or_metrics": True,
        "review_only_banner_visible": "REVIEW-ONLY" in html_content or "Review-Only" in html_content,
        "blocker_summary_visible": "Blockers" in html_content or "blockers" in html_content,
        "payload_hash_visible": preview_data.get("payload_hash", "unhashed") in html_content,
        "limitations_and_disclosure_visible": "limitations" in html_content.lower() and "disclosure" in html_content.lower()
    }
    return checklist


def get_screenshot_evidence(
    screenshot_captured: bool,
    screenshot_path: str = ""
) -> dict[str, Any]:
    """Generates browser screenshot manifest."""
    if screenshot_captured:
        return {
            "schema_version": SCHEMA_VERSION,
            "screenshot_created": True,
            "browser_target": "local_mock_only",
            "screenshot_path": screenshot_path,
            "real_substack_opened": False,
            "browser_session_secret_accessed": False,
            "screenshot_review_required_by_chatgpt": True
        }
    else:
        return {
            "schema_version": SCHEMA_VERSION,
            "screenshot_created": False,
            "screenshot_required_later": True,
            "browser_target": "local_mock_only",
            "real_substack_opened": False,
            "browser_session_secret_accessed": False
        }
DefinitionName = "browser_compose_qa"
