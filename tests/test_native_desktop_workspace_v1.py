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


def test_desk_export_is_offline_read_only_and_preserves_the_existing_store(tmp_path, monkeypatch, capsys):
    """Real exporter over a controlled projection; neither model nor publication proof."""
    from scripts.run_native_desktop_editorial import main
    from live_contentops import capital_chronicle_report_editorial_workspace_v1 as workspace
    from live_contentops import native_newsroom_learning_v1 as learning
    store = ContentOpsDurableStore(tmp_path / "existing.sqlite3")
    before = workspace_snapshot(store.db_path)
    from hashlib import sha256
    original = tmp_path / "original.png"
    import base64
    original.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j5foAAAAASUVORK5CYII="))
    media = {"asset_id": "controlled-pixel", "path": str(original), "sha256": sha256(original.read_bytes()).hexdigest(),
             "caption": "Controlled engineering pixel; not documentary evidence.", "computed_values": [[4.0]]}
    article = {"run_id": "selected-control", "article_identity": "a" * 64,
        "article": {"title": "Controlled owner export", "dek": "Engineering specimen", "substack_body_markdown": "Exact unchanged copy."},
        "previews": [], "media_assets": [media]}
    projection = {"owner_edition": {"edition_id": "control", "title": "Control", "operation_ids": [article["run_id"]],
        "ready": 1, "held": 0, "missing": 0, "preview_count": 0, "held_candidates": []},
        "native_edition": [article, {**article, "run_id": "unselected", "article_identity": "b" * 64,
            "article": {**article["article"], "title": "Historical control not selected"}}],
        "audience_learning": {}, "foundation_library": {"unrelated": "Do not expose broad history"}}
    monkeypatch.setattr(workspace, "report_workspace_projection", lambda *_args, **_kwargs: projection)
    monkeypatch.setattr(learning, "learning_context", lambda *_args: {"policy": {"sample_count": 0}})
    profile = tmp_path / "profile.json"
    profile.write_text(json.dumps({"store_path": str(store.db_path), "published_memory_store": str(store.db_path),
                                   "editorial_output_root": str(tmp_path / "existing-previews")}))
    assert main(["desk", "--profile", str(profile)]) == 0
    export = tmp_path / "existing-previews/desk/index.html"
    html = export.read_text(encoding="utf-8")
    from html.parser import HTMLParser
    class DataParser(HTMLParser):
        payload = ""
        capture = False
        def handle_starttag(self, tag, attrs):
            if tag == "script":
                self.capture = dict(attrs).get("id") == "owner-review-data"
        def handle_endtag(self, tag):
            if tag == "script":
                self.capture = False
        def handle_data(self, data):
            if self.capture:
                self.payload += data
    parser = DataParser()
    parser.feed(html)
    packet = json.loads(parser.payload)
    data = packet["data"]
    assert data["native_edition"] == [article]
    assert isinstance(data["native_edition"][0]["media_assets"][0]["computed_values"][0][0], float)
    assert "foundation_library" not in data
    assert packet["context"]["original_media_links"][media["sha256"]] == "../../original.png"
    assert "connect-src 'none'" in html and "form-action 'none'" in html
    assert not list(export.parent.glob("*.js"))  # no server, bundle or CDN dependency
    assert workspace_snapshot(store.db_path) == before
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1])["publication_authority"] is False
