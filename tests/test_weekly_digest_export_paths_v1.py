"""The existing weekly exporters deliver to a consumer outside the checkout."""
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest


@pytest.mark.parametrize("kind", ["coverage", "engagement"])
def test_export_reaches_external_consumer_directory_without_writing_store(tmp_path, kind):
    store = tmp_path / "source.sqlite3"
    with sqlite3.connect(store) as connection:
        for table in ("outbox_messages", "platform_dispatches", "reconciliations", "readbacks",
                      "performance_observations"):
            connection.execute(f"CREATE TABLE {table} (placeholder TEXT)")
    original = store.read_bytes()
    consumer = tmp_path / "runtime" / "weekly"
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / f"export_contentops_weekly_{kind}.py"),
         "--store", str(store), "--week-ending", "2026-11-04", "--output-dir", str(consumer)],
        cwd=tmp_path, capture_output=True, text=True, timeout=30, check=True,
    )
    receipt = json.loads(result.stdout)
    value = json.loads((consumer / f"{kind}.json").read_bytes())
    rendered = (consumer / f"{kind}.md").read_text(encoding="utf-8")
    assert Path(receipt["digest"]) == consumer / f"{kind}.md"
    assert value["input_store_read_only"] is True
    assert rendered.strip()
    if kind == "engagement":
        assert len(value["channels"]) == 10
        assert all(row["missing_causes"] for row in value["channels"])
        assert "linkedin_company" in rendered
    else:
        assert value["source_walks"] == 0
        assert value["source_walk_success_rate"] is None
        assert "UNAVAILABLE" in rendered
    assert store.read_bytes() == original
