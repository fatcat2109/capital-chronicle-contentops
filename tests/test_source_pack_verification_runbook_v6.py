"""Test source pack verification runbook module."""
from __future__ import annotations

from live_contentops import source_pack_verification_runbook_v6 as rb


def test_get_verification_runbook_content():
    content = rb.get_verification_runbook_content()
    assert "Source Pack Verification Runbook" in content
    assert "retrieved data excerpt" in content
    assert "SHA256" in content
