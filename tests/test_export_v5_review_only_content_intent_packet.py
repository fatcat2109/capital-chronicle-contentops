"""Unit tests for the V5 static TypeScript review-only content intent exporter.

Part of TASK_CONTENTOPS_0175BM_REVIEW_ONLY_INTENT_PACKET_TO_V5_INTENT_DETAIL_BINDING_V0.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.export_v5_review_only_content_intent_packet import cmd_check, load_packet, render_ts


def test_exporter_check():
    """Verify that the committed TS review-only intent packet is up-to-date and byte-identical."""
    assert cmd_check() == 0


def test_exporter_determinism():
    """Verify that exporting twice yields identical results."""
    packet1 = load_packet()
    packet2 = load_packet()
    
    assert packet1 == packet2
    assert "packet_hash" in packet1
    
    ts1 = render_ts(packet1)
    ts2 = render_ts(packet2)
    assert ts1 == ts2
    assert packet1["packet_hash"] in ts1
