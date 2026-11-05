from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/automation/CONTENTOPS_FAST_SHIP_CAPABILITY_POLICY_GENERICITY_AND_READINESS_RECEIPT_REPAIR_V1"
REGISTRY = ROOT / "docs/automation/V6_FINAL_PRODUCT_EXECUTION_PLAN/source_evidence_capability_registry_v2.json"


def _read(name: str) -> dict:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def _logical_hash(value: dict) -> str:
    core = {key: item for key, item in value.items() if key != "logical_hash"}
    encoded = json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _byte_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_blob(path: Path) -> str:
    return subprocess.run(
        ["git", "hash-object", str(path)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_current_story_and_platform_policy_truth_is_preserved():
    records = _read("capability_readiness_records.json")["records"]
    by_story = {}
    for row in records:
        by_story.setdefault(row["story_id"], []).append(row)
    assert len(by_story) == 3
    usgs = next(rows for rows in by_story.values() if rows[0]["story_type"] == "physical_event")
    assert all(row["market_sensitive"] is False for row in usgs)
    assert all(row["market_snapshot_required"] is False for row in usgs)
    for rows in by_story.values():
        substack = next(row for row in rows if row["platform_id"] == "substack_newsletter")
        assert substack["effective_platform_visual_mode"] == "long_form"
        for row in rows:
            if row["platform_id"] != "substack_newsletter":
                assert row["effective_platform_visual_mode"] == "text_only"
                assert row["variant_mode"] == "dry_run"


