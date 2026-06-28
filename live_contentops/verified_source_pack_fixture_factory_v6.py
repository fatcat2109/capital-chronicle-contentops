"""V6 Verified Source Pack Fixture Factory.

Generates complete, synthetically compliant verified source packs exclusively for test-only positive path unit tests.
Does not use placeholder/fake keywords in committed runtime files.
"""
from __future__ import annotations

from typing import Any


def make_test_only_positive_verified_source_pack() -> dict[str, Any]:
    """Generates a minimal positive-path capability summary for runtime without real-looking source details."""
    return {
        "test_only": True,
        "runtime_truth": False,
        "operator_verified_by": "TEST_ONLY_OPERATOR_NOT_REAL_VERIFICATION",
        "verified_source_pack_status": "TEST_ONLY_VERIFIED_FIXTURE",
        "source_pack_draft_status": "TEST_ONLY_VERIFIED_FIXTURE",
        "allowed_for_article_use": False,
        "draft_generation_allowed": False,
        "source_pack_complete": False,
        "source_entries": []
    }
