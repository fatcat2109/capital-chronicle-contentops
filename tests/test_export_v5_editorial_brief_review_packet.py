"""Unit tests for the export_v5_editorial_brief_review_packet exporter.

Part of TASK_CONTENTOPS_0175BI_EDITORIAL_BRIEF_REVIEW_PACKET_TO_V5_BRIEF_QUEUE_BINDING_V0.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from tools.export_v5_editorial_brief_review_packet import (
    load_packet,
    render_ts,
    _safety_scan,
    main,
    ARTIFACT,
)


def test_load_packet():
    """Verify that the packet loads successfully with the expected structure."""
    packet = load_packet()
    assert isinstance(packet, dict)
    assert packet["task_label"] == "TASK_CONTENTOPS_0175BH_LIFECYCLE_INTAKE_BRIDGE_TO_EDITORIAL_BRIEF_REVIEW_PACKET_V0"
    assert "candidate_review_items" in packet
    assert len(packet["candidate_review_items"]) > 0


def test_render_ts_and_forbidden_tokens():
    """Verify render_ts and safety scans for forbidden keywords."""
    packet = load_packet()
    rendered = render_ts(packet)
    assert "export const editorialBriefReviewPacket = " in rendered
    assert "as const;" in rendered

    # No forbidden keywords
    hits = _safety_scan(rendered)
    assert not hits, f"Safety scan failed: {hits}"

    # Verify that a forbidden word trigger works
    bad_rendered = rendered + "\n// buy target stock now"
    bad_hits = _safety_scan(bad_rendered)
    assert "buy" in bad_hits


def test_exporter_check_command():
    """Verify that main with '--check' works correctly when artifact matches."""
    # Run check mode - should exit 0 because the file was just written and matches perfectly
    code = main(["--check"])
    assert code == 0
