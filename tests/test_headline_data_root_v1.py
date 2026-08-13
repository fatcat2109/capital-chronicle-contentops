from __future__ import annotations

import json
from pathlib import Path

from live_contentops.headline_data_root_v1 import reconcile_headline_data_roots


def _write_sidecar(data_root: Path, name: str, rows: list[dict]) -> None:
    target = data_root / "intake" / "headline_sidecars" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_reconciliation_is_additive_deterministic_and_preserves_sources(tmp_path):
    first = tmp_path / "worktree-a" / "data"
    second = tmp_path / "worktree-b" / "data"
    target = tmp_path / "stable" / "data"
    common_old = {
        "dedup_key": "same", "headline_id": "h1", "headline_text": "old",
        "headline_timestamp": "2026-08-13T08:00:00Z", "captured_at_utc": "2026-08-13T08:01:00Z",
    }
    common_new = {**common_old, "headline_text": "new", "captured_at_utc": "2026-08-13T08:02:00Z"}
    unique = {
        "dedup_key": "unique", "headline_id": "h2", "headline_text": "unique",
        "headline_timestamp": "2026-08-13T09:00:00Z", "captured_at_utc": "2026-08-13T09:01:00Z",
    }
    filename = "step1_headline_sidecar_2026_08_13.jsonl"
    _write_sidecar(first, filename, [common_old])
    _write_sidecar(second, filename, [common_new, unique])
    raw_a = first / "raw_archive" / "headline_cdp" / "a.json"
    raw_b = second / "raw_archive" / "headline_cdp" / "b.json"
    raw_a.parent.mkdir(parents=True); raw_b.parent.mkdir(parents=True)
    raw_a.write_bytes(b'{"a":1}'); raw_b.write_bytes(b'{"b":2}')
    state = first / "state" / "current" / "SourceHealth.json"
    state.parent.mkdir(parents=True); state.write_text('{"status":"HEALTHY"}', encoding="utf-8")
    first_before = (first / "intake" / "headline_sidecars" / filename).read_bytes()
    second_before = (second / "intake" / "headline_sidecars" / filename).read_bytes()

    report = reconcile_headline_data_roots(
        [second, first], canonical_root=target, state_authority_root=first
    )
    merged = [
        json.loads(line) for line in
        (target / "intake" / "headline_sidecars" / filename).read_text(encoding="utf-8").splitlines()
    ]
    assert report["canonical_unique_sidecar_row_count"] == 2
    assert report["deduplicated_row_count"] == 1
    assert {row["headline_text"] for row in merged} == {"new", "unique"}
    assert (target / "raw_archive" / "headline_cdp" / "a.json").read_bytes() == b'{"a":1}'
    assert (target / "raw_archive" / "headline_cdp" / "b.json").read_bytes() == b'{"b":2}'
    assert (first / "intake" / "headline_sidecars" / filename).read_bytes() == first_before
    assert (second / "intake" / "headline_sidecars" / filename).read_bytes() == second_before
    first_result = (target / "intake" / "headline_sidecars" / filename).read_bytes()

    rerun = reconcile_headline_data_roots(
        [first, second], canonical_root=target, state_authority_root=first
    )
    assert (target / "intake" / "headline_sidecars" / filename).read_bytes() == first_result
    assert rerun["canonical_unique_sidecar_row_count"] == 2
