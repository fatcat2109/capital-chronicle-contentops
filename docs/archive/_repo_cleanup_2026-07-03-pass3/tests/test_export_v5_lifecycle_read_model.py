"""Unit tests for the V5 static TypeScript lifecycle read model exporter.

Part of TASK_CONTENTOPS_0175BF_OPERATOR_REVIEW_READ_MODEL_TO_V5_QUEUE_BINDING_V0.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.export_v5_lifecycle_read_model import cmd_check, _build_expected, render_ts
from live_contentops.content_lifecycle_engine import build_contract_packet


def test_exporter_check():
    """Verify that the committed TS read model is up-to-date and byte-identical."""
    assert cmd_check() == 0


def test_exporter_determinism():
    """Verify that exporting twice yields identical results and matches source packet hash."""
    packet1 = build_contract_packet()
    packet2 = build_contract_packet()
    
    assert packet1 == packet2
    assert "packet_hash" in packet1
    
    ts1 = render_ts(packet1)
    ts2 = render_ts(packet2)
    assert ts1 == ts2
    assert packet1["packet_hash"] in ts1
