"""An accepted CC-010 projection survives removal of its old scratch checkout."""
from hashlib import sha256
import json
from types import SimpleNamespace

import pytest

from live_contentops import official_release_history_v1 as history
from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes
from tests.test_official_release_history_v1 import archive, load


def setup(tmp_path, monkeypatch, archive):
    value = load(archive)
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    path = root / "held.json"
    path.write_bytes(canonical_bytes(value))
    config = root / "config/history.json"
    config.write_text(json.dumps({"retained_histories": {"cpi": {"path": "held.json",
        "canonical_sha256": sha256(canonical_bytes(value)).hexdigest(), "accepted_owner": "CONTROLLED_TEST"}}}), encoding="utf-8")
    monkeypatch.setattr(history, "HISTORY_CONFIG_PATH", config)
    return path, value


def test_existing_history_and_its_original_clock_feed_the_writer_after_relocation(tmp_path, monkeypatch, archive):
    _, value = setup(tmp_path, monkeypatch, archive)
    turn = SimpleNamespace(root=tmp_path / "operation", frozen_request=lambda _: None)
    turn.root.mkdir()
    source = {"source_id": "SOURCE_1", "url": "https://www.bls.gov/news.release/cpi.nr0.htm",
        "published_at_utc": "2026-10-14T12:30:00Z"}
    docs = history.enrich_source_pack(turn, source_pack=[source], article_mode="DATA_OR_DOCUMENT_LENS",
        cutoff_utc="2026-11-14T12:00:00Z", archive_root=tmp_path / "removed-scratch")
    assert len(docs) == 5
    assert docs[1]["official_release_history"]["series"] == value["series"][0]
    assert docs[1]["official_release_history"]["cutoff_utc"] == value["cutoff_utc"]
    assert docs[1]["raw_sha256"] == value["dataset_sha256"]


def test_review_history_is_not_dropped_when_its_held_context_exceeds_ten_documents(tmp_path, monkeypatch, archive):
    setup(tmp_path, monkeypatch, archive)
    turn = SimpleNamespace(root=tmp_path / "operation", frozen_request=lambda _: None)
    turn.root.mkdir()
    sources = [{"source_id": f"SOURCE_{i+1}", "document_id": f"context-{i}",
        "url": "https://www.bls.gov/news.release/cpi.nr0.htm", "published_at_utc": "2026-10-14T12:30:00Z"}
        for i in range(8)]
    docs = history.enrich_source_pack(turn, source_pack=sources, article_mode="DATA_OR_DOCUMENT_LENS",
        cutoff_utc="2026-11-14T12:00:00Z", archive_root=tmp_path / "removed-scratch")
    assert len(docs) == 12 and docs[:8] == sources
    assert all(d.get("official_release_history") for d in docs[8:])


@pytest.mark.parametrize("fault,cause", [("changed", "PROJECTION_CHANGED"), ("future", "SCOPE_OR_CLOCK_INVALID")])
def test_changed_values_and_later_history_cannot_replace_event_evidence(tmp_path, monkeypatch, archive, fault, cause):
    path, _ = setup(tmp_path, monkeypatch, archive)
    if fault == "changed":
        value = json.loads(path.read_bytes())
        value["series"][0]["observations"][0]["value"] = 999
        path.write_bytes(canonical_bytes(value))
    source = {"url": "https://www.bls.gov/news.release/cpi.nr0.htm",
        "published_at_utc": "2026-09-01T12:30:00Z" if fault == "future" else "2026-10-14T12:30:00Z"}
    with pytest.raises(ValueError, match=cause):
        history.history_for_source_pack([source], cutoff_utc="2026-11-14T12:00:00Z", archive_root=tmp_path / "removed-scratch")
