"""Tests for V5 local canonical draft preview adapter codegen."""
from __future__ import annotations

import json
from pathlib import Path
from live_contentops.local_canonical_draft_preview_v5_adapter_codegen_v6 import (
    ADAPTER_PATH,
    generate_or_check_adapter,
)


def test_adapter_codegen_reproducible_and_in_sync() -> None:
    res = generate_or_check_adapter(verify_only=True)
    assert res["adapter_in_sync"] is True
    assert res["packet_hash_matches"] is True
