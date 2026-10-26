"""Real retained producer artifact plus isolated access/permission/read-only controls."""
from copy import deepcopy
from hashlib import sha256
import json
import re
import sqlite3
from types import SimpleNamespace

import pytest

from live_contentops import retained_news_read_v1 as news

IBM = "b39e88587862e50ced7333a61ad27c21546b45690b50a32c2c840799a28d7e13"
CASH = "ibm-dj-cash-improvement-r2"
NOW = "2026-10-26T03:00:00Z"


class TrustedSession:
    """Controlled host adapter, not a client-provided role/verified flag."""
    def __init__(self, **changes):
        self.calls = 0
        self.changes = changes

    def resolve(self, opaque_session, *, read_at_utc):
        self.calls += 1
        assert read_at_utc == NOW
        if opaque_session != "opaque-allowed":
            return None
        return SimpleNamespace(**{**dict(status="ACTIVE", scopes=(news.SCOPE,), record_ids=(IBM,),
            not_before_utc="2026-10-20T00:00:00Z", verified_at_utc="2026-10-26T02:00:00Z",
            expires_at_utc="2026-10-27T00:00:00Z"), **self.changes})


def reader(adapter=None):
    return news.RetainedNewsReader(adapter or TrustedSession(), clock=lambda: NOW)


@pytest.fixture
def actual():
    return json.loads(news.ARTIFACT_PATH.read_bytes())


def test_real_artifact_reads_full_exact_ibm_body_dates_models_and_prepared_state(actual):
    result = reader().read(IBM, "opaque-allowed")
    assert result["status"] == 200
    story = result["body"]["story"]
    retained = json.loads(news.SELECTION_PATH.read_bytes())
    original = next(c for c in retained["native_edition"] if c["article_identity"] == IBM)
    assert story["article"] == {k: v for k, v in original["article"].items() if k in news.ARTICLE_FIELDS}
    assert story["article"]["substack_body_markdown"] == original["article"]["substack_body_markdown"]
    assert story["article"]["display_date"] == "Updated October 25, 2026"
    assert story["clocks"]["analysis_at_utc"] is None
    assert story["clocks"]["evidence_cutoff_utc"] == "2026-10-24T19:43:39.977162Z"
    assert story["clocks"]["current_market_refresh_verified"] is False
    assert story["evidence"][0]["published_at_source"] == "2026-10-21"
    assert story["evidence"][0]["published_at_utc"] is None
    assert story["evidence"][0]["publication_precision"] == "DATE_ONLY"
    assert story["publication"]["state"] == "PREPARED"
    assert story["publication"]["canonical_url"] is None and story["publication"]["publication_at_utc"] is None
    assert all(d["status"] == "NOT_DISPATCHED" for d in story["publication"]["destinations"])
    assert story["epistemic_state"]["primary_reporting_publisher"] == "IBM"
    assert {"role": "write", "stage": "write", "model": "gpt-6.1-sol", "reasoning_effort": "max"} in story["editorial_execution"]["observed_models"]
    assert result["body"]["exported_at_utc"] == actual["exported_at_utc"]
    assert result["headers"]["Cache-Control"].startswith("private, no-store")


def test_real_cash_image_and_table_retain_exact_bytes_rounding_source_and_scope(actual):
    r = reader()
    story = r.read(IBM, "opaque-allowed")["body"]["story"]
    asset = next(a for a in story["media_assets"] if a["asset_id"] == CASH)
    pixels = r.read_asset(IBM, CASH, "opaque-allowed")
    assert pixels["status"] == 200 and pixels["headers"]["Content-Type"] == "image/png"
    assert sha256(pixels["body"]).hexdigest() == "928c7b51662662fd4c49f107da42ef29b51fe8addb3ff0c7b15daf0ee4ce7588"
    assert pixels["body"] == (news.SELECTION_PATH.parent / "ibm/ibm-dj-cash-improvement-r2.png").read_bytes()
    assert (asset["width"], asset["height"]) == (1120, 1760)
    table = r.read_table(IBM, CASH, "opaque-allowed")
    assert table["status"] == 200
    assert table["body"]["columns"] == ["2025", "2026"]
    assert [row["values"] for row in table["body"]["rows"]] == [[9153, 11791], [905, 2805], [-1067, -1200], [7181, 7787]]
    assert "$605 million" in asset["caption"] and "$606 million" in asset["caption"] and "$1 million" in asset["caption"]
    assert "non-GAAP" in asset["support_caption"] and "consolidated IBM" in asset["support_caption"]
    assert asset["source_links"][0]["url"] == "https://newsroom.ibm.com/2026-10-21-IBM-RELEASES-THIRD-QUARTER-RESULTS"
    assert "Software cash conversion" in " ".join(table["body"]["notes"])
    # Original photographs are selected through the fixed existing portable map,
    # not recopied as large originals into the producer artifact.
    photo = next(a for a in story["media_assets"] if a["modality"] == "documentary_photo")
    original_photo = r.read_asset(IBM, photo["asset_id"], "opaque-allowed")
    assert original_photo["status"] == 200
    assert sha256(original_photo["body"]).hexdigest() == photo["sha256"]


def test_all_actual_selected_members_and_allowlist_preserve_safe_original_fields(actual):
    previous = json.loads(news.SELECTION_PATH.read_bytes())
    assert actual["owner_edition"]["operation_ids"] == previous["owner_edition"]["operation_ids"]
    for item in actual["native_edition"]:
        source = next(c for c in previous["native_edition"] if c["article_identity"] == item["article_identity"])
        assert item["availability"] == "AVAILABLE"
        assert item["article"] == {k: v for k, v in source["article"].items() if k in news.ARTICLE_FIELDS}
        assert [a["sha256"] for a in item["media_assets"]] == [a["sha256"] for a in source["media_assets"]]
    serialized = json.dumps(actual)
    assert not re.search(r"[AC]:[/\\]|file://|canonical_content_text|support_excerpt|policy_capture_sha256|invocation_id|private_question|account_balance", serialized)
    assert "pending-publication-" not in serialized
    # The renderer uses the same React owner reader, with safe embedded media only.
    html = news.ARTIFACT_PATH.with_name("reader.html").read_text(encoding="utf-8")
    data = json.loads(re.search(r'<script id="owner-review-data" type="application/json">(.*?)</script>', html, re.S).group(1))["data"]
    ibm = next(c for c in data["native_edition"] if c["article_identity"] == IBM)
    assert ibm["article"]["substack_body_markdown"] == actual["native_edition"][0]["article"]["substack_body_markdown"]
    assert next(a for a in ibm["media_assets"] if a["asset_id"] == CASH)["reader_table"]["columns"] == ["2025", "2026"]


@pytest.mark.parametrize("changes", [{"scopes": ("owner:read",)}, {"record_ids": ("a" * 64,)},
    {"expires_at_utc": "2026-10-26T02:30:00Z"}, {"status": "REVOKED"}, {"scopes": [news.SCOPE]}])
def test_wrong_scope_record_expired_or_revoked_session_denies_article_image_and_table(changes, monkeypatch):
    monkeypatch.setattr(news, "_artifact", lambda: pytest.fail("Denied request must not open artifact"))
    r = reader(TrustedSession(**changes))
    for result in (r.read(IBM, "opaque-allowed"), r.read_asset(IBM, CASH, "opaque-allowed"), r.read_table(IBM, CASH, "opaque-allowed")):
        assert result["status"] == 403 and result["body"] == {"state": "ACCESS_DENIED"}


def test_request_dictionary_and_adapter_failure_cannot_grant_or_leak():
    class BrokenAdapter:
        def resolve(self, *_args, **_kwargs):
            raise RuntimeError("C:/private/session-secret")
    assert reader().read(IBM, {"verified": True, "scope": news.SCOPE})["status"] == 403
    result = reader(BrokenAdapter()).read(IBM, "opaque-allowed")
    assert result["body"] == {"state": "ACCESS_DENIED"}


@pytest.mark.parametrize("selection", ["../selected-edition.json", "file:///C:/private", "https://example.org/a", "..%2Fsecret", "A:\\secret", "a" * 63])
def test_article_path_or_url_traversal_never_reaches_filesystem(selection, monkeypatch):
    monkeypatch.setattr(news, "_artifact", lambda: pytest.fail("Unsupported selector must not load artifact"))
    assert reader().read(selection, "opaque-allowed")["status"] == 400


@pytest.mark.parametrize("selection", ["../ibm.png", "file:///secret", "cash%2Fprivate", "C:\\secret", "https://example.org"])
def test_asset_and_table_selectors_accept_only_bound_ids(selection):
    r = reader()
    assert r.read_asset(IBM, selection, "opaque-allowed")["status"] == 400
    assert r.read_table(IBM, selection, "opaque-allowed")["status"] == 400
    assert r.read_asset(IBM, "documentary_meta", "opaque-allowed")["status"] == 404


def test_local_missing_artifact_is_honest_and_denied_session_still_denied(tmp_path, monkeypatch):
    monkeypatch.setattr(news, "ARTIFACT_PATH", tmp_path / "missing.json")
    assert reader().read(IBM, "opaque-allowed")["body"] == {"state": "LOCAL_CONTENT_MISSING"}
    assert reader().read_asset(IBM, CASH, "opaque-allowed")["body"] == {"state": "LOCAL_CONTENT_MISSING"}
    assert reader().read(IBM, "not-allowed")["body"] == {"state": "ACCESS_DENIED"}


def test_original_photo_missing_does_not_substitute_or_block_the_embedded_cash_chart(tmp_path, monkeypatch):
    monkeypatch.setattr(news, "SELECTION_PATH", tmp_path / "absent-portable-map.json")
    r = reader()
    assert r.read(IBM, "opaque-allowed")["status"] == 200
    assert r.read_asset(IBM, "documentary_ibm", "opaque-allowed")["body"] == {"state": "LOCAL_CONTENT_MISSING"}
    assert r.read_asset(IBM, CASH, "opaque-allowed")["status"] == 200


def test_corrupt_original_chart_bytes_do_not_get_served(actual, tmp_path, monkeypatch):
    asset = next(a for a in actual["native_edition"][0]["media_assets"] if a["asset_id"] == CASH)
    asset["content_base64"] = "dGFtcGVyZWQ="
    path = tmp_path / "selected-edition.json"
    path.write_text(json.dumps(actual), encoding="utf-8")
    monkeypatch.setattr(news, "ARTIFACT_PATH", path)
    assert reader().read_asset(IBM, CASH, "opaque-allowed")["body"] == {"state": "CONTENT_INTEGRITY"}


def test_changed_media_use_permission_cannot_leak_article_or_asset(actual, tmp_path, monkeypatch):
    actual["native_edition"][0]["media_assets"][0]["rights_status"] = "RESTRICTED"
    path = tmp_path / "selected-edition.json"
    path.write_text(json.dumps(actual), encoding="utf-8")
    monkeypatch.setattr(news, "ARTIFACT_PATH", path)
    assert reader().read(IBM, "opaque-allowed")["body"] == {"state": "CONTENT_INTEGRITY"}
    assert reader().read_asset(IBM, CASH, "opaque-allowed")["body"] == {"state": "CONTENT_INTEGRITY"}
    assert reader().read_table(IBM, CASH, "opaque-allowed")["body"] == {"state": "CONTENT_INTEGRITY"}


def test_allowed_read_does_not_refresh_source_or_create_a_store(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("No database, refresh, model or runtime operation belongs to artifact reading")
    monkeypatch.setattr(sqlite3, "connect", forbidden)
    import live_contentops.durable_operational_store_v1 as durable
    import live_contentops.contentops_source_research_v1 as sources
    import live_contentops.native_desktop_editorial_v1 as native
    monkeypatch.setattr(durable, "ContentOpsDurableStore", forbidden)
    monkeypatch.setattr(sources, "RetainedSourceResearch", forbidden)
    monkeypatch.setattr(native, "NativeDesktopTurn", forbidden)
    r = reader()
    assert r.read(IBM, "opaque-allowed")["status"] == 200
    assert r.read_asset(IBM, CASH, "opaque-allowed")["status"] == 200
    assert r.read_table(IBM, CASH, "opaque-allowed")["status"] == 200


def test_access_rechecked_after_initial_read_and_before_each_asset_or_table():
    adapter = TrustedSession()
    r = reader(adapter)
    assert r.read(IBM, "opaque-allowed")["status"] == 200
    adapter.changes["status"] = "REVOKED"
    assert r.read_asset(IBM, CASH, "opaque-allowed")["status"] == 403
    assert r.read_table(IBM, CASH, "opaque-allowed")["status"] == 403
    assert adapter.calls == 3


def test_denied_source_never_exports_body_or_asset_table_and_has_no_public_rights_promotion(actual, monkeypatch, tmp_path):
    # The controlled specimen reuses the real story, but withdraws its permission.
    workspace = {"owner_edition": deepcopy(actual["owner_edition"]), "native_edition": deepcopy(actual["native_edition"])}
    item = workspace["native_edition"][0]
    item["evidence"][0]["source_reuse_constraints"]["INTERNAL_ANALYSIS_ALLOWED"] = False
    # Each other member is intentionally unrequested, not fabricated ready output.
    workspace["owner_edition"]["operation_ids"] = [item["run_id"]]
    safe = news.build_news_projection(workspace, exported_at_utc=NOW)
    entry = safe["native_edition"][0]
    assert entry["availability"] == "CONTENT_RESTRICTED"
    assert not any(k in entry for k in ("article", "media_assets", "evidence", "reader_table"))
    path = tmp_path / "selected-edition.json"
    path.write_text(json.dumps(safe), encoding="utf-8")
    monkeypatch.setattr(news, "ARTIFACT_PATH", path)
    for r in (reader().read(IBM, "opaque-allowed"), reader().read_asset(IBM, CASH, "opaque-allowed"), reader().read_table(IBM, CASH, "opaque-allowed")):
        assert r["body"] == {"state": "CONTENT_RESTRICTED"}


@pytest.mark.parametrize("location", ["story", "source", "media", "table", "nested_article_metadata"])
def test_artifact_private_field_injection_fails_closed(actual, tmp_path, monkeypatch, location):
    item = actual["native_edition"][0]
    target = {"story": item, "source": item["evidence"][0], "media": item["media_assets"][0],
              "table": next(a["reader_table"] for a in item["media_assets"] if a.get("reader_table")),
              "nested_article_metadata": item["article"]}[location]
    if location == "nested_article_metadata":
        target["topics"] = [{"private_question": "C:/private/account-secret"}]
    else:
        target["private_question"] = "C:/private/account-secret"
    path = tmp_path / "selected-edition.json"
    path.write_text(json.dumps(actual), encoding="utf-8")
    monkeypatch.setattr(news, "ARTIFACT_PATH", path)
    assert reader().read(IBM, "opaque-allowed")["body"] == {"state": "CONTENT_INTEGRITY"}


def test_export_reads_existing_owner_query_only_without_store_constructor(tmp_path, monkeypatch):
    # Tests never point at the operating owner or production SQLite.
    db = tmp_path / "isolated.sqlite3"
    tables = ("outbox_messages", "review_records", "platform_dispatches", "reconciliations", "destination_readiness")
    with sqlite3.connect(db) as conn:
        for name in tables:
            conn.execute("CREATE TABLE " + name + " (value TEXT)")
    original_bytes = db.read_bytes()
    profile = tmp_path / "profile.json"
    profile.write_text(json.dumps({"store_path": str(db)}))
    selected = tmp_path / "selection.json"
    selected.write_text(json.dumps({"owner_edition": {"edition_id": "controlled", "title": "Controlled missing member", "operation_ids": ["missing-member"]}}))
    import live_contentops.capital_chronicle_report_editorial_workspace_v1 as workspace
    import live_contentops.durable_operational_store_v1 as durable
    monkeypatch.setattr(workspace, "report_workspace_projection", lambda *_a, **_k: {"native_edition": []})
    monkeypatch.setattr(durable, "ContentOpsDurableStore", lambda *_a, **_k: pytest.fail("No constructor/migration"))
    monkeypatch.setattr(news, "PROFILE_PATH", profile)
    monkeypatch.setattr(news, "SELECTION_PATH", selected)
    monkeypatch.setattr(news, "ARTIFACT_PATH", tmp_path / "out/selected-edition.json")
    statements = []
    original_connect = sqlite3.connect
    def traced(database_uri, **kwargs):
        assert database_uri.endswith("?mode=ro") and kwargs["uri"] is True
        conn = original_connect(database_uri, **kwargs)
        conn.set_trace_callback(statements.append)
        return conn
    monkeypatch.setattr(sqlite3, "connect", traced)
    result = news.export_selected_news()
    assert result["available"] == 0
    assert json.loads(news.ARTIFACT_PATH.read_bytes())["native_edition"][0]["availability"] == "LOCAL_CONTENT_MISSING"
    assert db.read_bytes() == original_bytes
    assert all(s.startswith(("PRAGMA query_only", "BEGIN", "SELECT", "COMMIT", "ROLLBACK")) for s in statements)


def test_cli_rejects_alternate_profile_path_and_accepts_exact_real_article(capsys):
    from scripts.run_native_desktop_editorial import main
    with pytest.raises(SystemExit):
        main(["news-read", "--article-id", IBM, "--profile", "C:/private/alternate.json"])
    with pytest.raises(SystemExit):
        main(["news-read", "--article-id", IBM, "--workspace-root", "C:/private"])
    assert main(["news-read", "--article-id", IBM]) == 0
    output = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert output["status"] == 200 and output["body"]["story"]["article_identity"] == IBM
