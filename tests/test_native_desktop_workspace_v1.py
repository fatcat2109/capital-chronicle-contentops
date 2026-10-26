"""Manual relocation preserves exact canonical rows and sealed path bindings."""
import json
from pathlib import Path

import pytest

from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_workspace_v1 import relocate_owner_workspace, resolve_workspace_path, workspace_snapshot


def test_manual_relocation_preserves_pending_rows_and_redirects_old_store(tmp_path, monkeypatch):
    from live_contentops import native_desktop_workspace_v1 as module
    old = tmp_path / "Temp" / "manual" / "state.sqlite3"
    store = ContentOpsDurableStore(old)
    store.create_work_item(story_id="pending", work_item_id="pending", title="Pending writer", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    payload = json.dumps({"request_sha256": "a" * 64, "output_dir": str(old.parent)})
    store.register_outbox_message(message_id="pending-request", work_item_id="pending", destination="internal:native-desktop-editorial", payload=payload)
    profile = tmp_path / "profile.json"
    profile.write_text(json.dumps({"scope": "OWNER_MANUAL_EDITORIAL_ONLY_EXISTING_REVIEWED_WORKSPACE_NOT_PRODUCTION", "store_path": str(old)}))
    before = workspace_snapshot(old)
    # No artifact directory containing the database should be an operating alias.
    manifest = relocate_owner_workspace(profile, tmp_path / "durable")
    target = Path(manifest["one_operating_store"])
    monkeypatch.setattr(module, "DEFAULT_MANIFEST", target.parent / "relocation.json")
    assert workspace_snapshot(target) == before == workspace_snapshot(old)
    assert resolve_workspace_path(old) == target
    reopened = ContentOpsDurableStore(old, auto_migrate=False)
    assert reopened.db_path == target
    assert reopened.get_outbox_message("pending-request")["payload"] == payload
    reopened.create_work_item(story_id="new", work_item_id="new", title="New work", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    assert workspace_snapshot(old) == before
    assert workspace_snapshot(target) != before
    data = json.loads((target.parent / "relocation.json").read_bytes())
    data["paths"][0]["target"] = str(tmp_path / "other.sqlite3")
    (target.parent / "relocation.json").write_text(json.dumps(data))
    with pytest.raises(ValueError, match="METADATA_CHANGED"):
        ContentOpsDurableStore(old)


def test_relocation_does_not_move_an_active_writer(tmp_path):
    old = tmp_path / "Temp" / "state.sqlite3"
    store = ContentOpsDurableStore(old)
    store.acquire_lease("native-editorial", "writer", ttl_seconds=60)
    profile = tmp_path / "profile.json"
    profile.write_text(json.dumps({"scope": "OWNER_MANUAL_EDITORIAL_ONLY_EXISTING_REVIEWED_WORKSPACE_NOT_PRODUCTION", "store_path": str(old)}))
    with pytest.raises(ValueError, match="ACTIVE_WRITER_LEASE"):
        relocate_owner_workspace(profile, tmp_path / "durable")
    assert not (tmp_path / "durable").exists()
