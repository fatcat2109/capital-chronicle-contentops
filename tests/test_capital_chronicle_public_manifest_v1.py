"""Main-owned public export fixture plus explicitly resealed lifecycle controls."""

import hashlib
import shutil
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    LatestReportDeliveryTracker,
    canonical_bytes,
    sha256_of,
)
from live_contentops.capital_chronicle_public_manifest_v1 import (
    CONFIG_SCHEMA,
    PublicMainFileSource,
)
from live_contentops.capital_chronicle_report_feed_v1 import MainReportFeed
from live_contentops.capital_chronicle_report_editorial_workspace_v1 import (
    report_workspace_projection,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from tests.test_capital_chronicle_report_editorial_workspace_v1 import controlled_writer

FIXTURE = Path(__file__).parent / "fixtures/main_goal20_public_export_control"
NOW = "2026-10-19T07:00:00Z"


def setup(tmp_path):
    root = tmp_path / "public"
    shutil.copytree(FIXTURE, root)
    pointer = {
        "schema_version": CONFIG_SCHEMA,
        "public_export_root": str(root),
        "export_root_id": "goal20-compatibility-control",
        "producer_repository": "https://github.com/fatcat2109/Headline-Raw-data-json",
    }
    source = PublicMainFileSource(pointer)
    manifest = source.refresh(cutoff_utc=NOW)
    tracker = LatestReportDeliveryTracker(
        ContentOpsDurableStore(tmp_path / "isolated.sqlite3")
    )
    return root, pointer, manifest, tracker


def control_manifest(
    root, template, entries, parent=None, emitted="2026-10-19T06:30:00Z"
):
    """Lifecycle mechanics control, not new Main production or source evidence."""
    body = {
        **template,
        "entries": entries,
        "parent_manifest_sha256": parent,
        "emitted_at_utc": emitted,
    }
    body.pop("manifest_sha256", None)
    body["manifest_sha256"] = sha256_of(body)
    path = "manifests/" + body["manifest_sha256"] + ".json"
    raw = canonical_bytes(body)
    (root / path).write_bytes(raw)
    (root / "latest-manifest.json").write_bytes(
        canonical_bytes(
            {
                "path": path,
                "bytes_sha256": hashlib.sha256(raw).hexdigest(),
                "manifest_sha256": body["manifest_sha256"],
            }
        )
    )
    return body


def test_incremental_parent_history_restart_without_pointer_edit(tmp_path):
    root, pointer, template, tracker = setup(tmp_path)
    first = control_manifest(root, template, template["entries"][:1])
    feed = MainReportFeed(tracker, pointer, headline_paths=[])
    assert feed.poll(cutoff_utc=NOW)["new_events"] == 1
    second = control_manifest(
        root, template, template["entries"], first["manifest_sha256"]
    )
    resumed = MainReportFeed(tracker, pointer, headline_paths=[])
    scan = resumed.poll(cutoff_utc=NOW)
    assert scan["new_events"] == 1 and scan["events"][-1]["state"] == "ADMITTED"
    assert scan["manifest_sha256"] == second["manifest_sha256"]
    assert resumed.pending()[0]["report_version"] == 2
    assert resumed.poll(cutoff_utc=NOW)["new_events"] == 0
    rollback = control_manifest(root, template, template["entries"][:1])
    assert rollback["manifest_sha256"] == first["manifest_sha256"]
    blocked = resumed.poll(cutoff_utc=NOW)
    assert blocked["gaps"][0]["state"] == "MAIN_PUBLIC_MANIFEST_HISTORY_FORK"
    assert resumed.pending()[0]["report_version"] == 2


def test_exact_source_bytes_public_projection_and_local_bad_entry(tmp_path):
    root, pointer, manifest, tracker = setup(tmp_path)
    poisoned = {
        **manifest["entries"][0],
        "envelope": {
            **manifest["entries"][0]["envelope"],
            "path": "../private/account.json",
        },
    }
    control_manifest(root, manifest, [poisoned, *manifest["entries"]])
    feed = MainReportFeed(tracker, pointer, headline_paths=[])
    scan = feed.poll(cutoff_utc=NOW)
    assert len(scan["gaps"]) == 1 and [e["state"] for e in scan["events"]] == [
        "ADMITTED",
        "ADMITTED",
    ]
    source = PublicMainFileSource(pointer)
    with pytest.raises(ValueError, match="OUTSIDE_CONTRACT"):
        source._read("C:/private/account.json")
    target = root / manifest["entries"][1]["public_report"]["path"]
    target.write_bytes(target.read_bytes() + b" ")
    replay = feed.poll(cutoff_utc=NOW)
    assert replay["gaps"] and tracker.receipts()[-1]["report_version"] == 2


def test_public_manifest_urn_draft_withdrawal_no_provider_replay(tmp_path):
    root, pointer, manifest, tracker = setup(tmp_path)
    feed = MainReportFeed(tracker, pointer, headline_paths=[])
    calls = []
    result = feed.opportunity(
        output_dir=tmp_path / "draft",
        cutoff_utc=NOW,
        run_id="public-outbox",
        rolling_input={"headlines": []},
        llm_invoke=controlled_writer(calls),
    )
    r = result["report_workspace_result"]
    assert r["classification"] == "DRAFT_READY" and len(r["previews"]) == 8
    assert r["evidence"][0]["url"].startswith("urn:cc-public-report:")
    event = {
        "event_type": "WITHDRAWAL",
        "asset_id": "XNGUSD",
        "report_sha256": r["source_report_sha256"],
        "reason": "Explicit controlled withdrawal",
        "known_at_cutoff_utc": "2026-10-19T06:40:00Z",
    }
    event["event_id"] = "withdrawal:" + sha256_of(event)
    control_manifest(
        root,
        manifest,
        [*manifest["entries"], event],
        manifest["manifest_sha256"],
        emitted="2026-10-19T06:40:00Z",
    )
    scan = feed.poll(cutoff_utc=NOW)
    assert scan["events"][-1]["state"] == "CLAIMS_WITHDRAWN" and not feed.pending()
    view = report_workspace_projection(tracker.store.list_outbox_messages())
    assert (
        view["latest_report"]["withdrawal_only"]
        and view["article"] is None
        and not view["previews"]
    )
    repeated = feed.opportunity(
        output_dir=tmp_path / "draft",
        cutoff_utc=NOW,
        run_id="public-outbox",
        llm_invoke=lambda **_: (_ for _ in ()).throw(
            AssertionError("duplicate provider")
        ),
    )
    assert (
        repeated["report_workspace_result"]["classification"] == "DRAFT_WITHDRAWN"
        and len(calls) == 2
    )


def test_withdrawal_receipt_survives_crash_before_status_projection(tmp_path, monkeypatch):
    root, pointer, manifest, tracker = setup(tmp_path)
    feed = MainReportFeed(tracker, pointer, headline_paths=[])
    feed.poll(cutoff_utc=NOW)
    report = feed.pending()[0]
    event = {"event_type": "WITHDRAWAL", "asset_id": "XNGUSD", "report_sha256": report["source_report_sha256"],
             "reason": "Controlled interrupted withdrawal", "known_at_cutoff_utc": NOW}
    event["event_id"] = "withdrawal:" + sha256_of(event)
    original = tracker.store.set_outbox_status
    monkeypatch.setattr(tracker.store, "set_outbox_status", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("interrupted status projection")))
    with pytest.raises(RuntimeError, match="interrupted status"):
        feed.apply_withdrawal(event)
    assert not feed.pending()  # durable withdrawal already excludes further editorial work
    monkeypatch.setattr(tracker.store, "set_outbox_status", original)
    resumed = MainReportFeed(tracker, pointer, headline_paths=[])
    assert resumed.apply_withdrawal(event)["state"] == "DUPLICATE_WITHDRAWAL_NOOP"
    assert all(r["delivery_status"] == "CONTENT_WITHDRAWN" for r in tracker.receipts() if r["source_report_sha256"] == event["report_sha256"])


def test_missing_parent_is_named_in_workspace_with_exact_next_action(tmp_path):
    root, pointer, manifest, tracker = setup(tmp_path)
    control_manifest(root, manifest, manifest["entries"][1:])
    feed = MainReportFeed(tracker, pointer, headline_paths=[])
    scan = feed.poll(cutoff_utc=NOW)
    assert scan["events"][0]["state"] == "LINEAGE_PARENT_NOT_RECEIVED"
    view = report_workspace_projection(tracker.store.list_outbox_messages())
    assert view["named_blocker"] == "LINEAGE_PARENT_NOT_RECEIVED"
    assert manifest["entries"][1]["parent_report_sha256"] in view["next_operation"]
    assert not feed.pending()
