"""Exercise the installed event-attach and minute-run consumers with bounded OTS I/O."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

import pytest

from live_contentops import event_timestamp_v1 as ots
from tests.test_event_public_record_v1 import frozen_file, FROZEN, RELEASE, EVENT

NOW = datetime(2026, 11, 5, 10, tzinfo=timezone.utc)
INSPECT = ots.inspect
RETAIN = ots.retain_and_stamp


class Client:
    def __init__(self):
        self.calls = []
        self.upgrade_bytes = b"complete proof"
        self.error = None

    def __call__(self, args):
        self.calls.append(args)
        if args[0] == "inspect":
            source, proof = map(Path, args[1:])
            if proof.read_bytes() == b"corrupt":
                return {"returncode": 1, "stdout": "", "stderr": "BadMagicError"}
            data = {"file_sha256": sha256(source.read_bytes()).hexdigest(), "file_matches": True,
                "calendars": [ots.CALENDARS[0]], "bitcoin_verified": False,
                "bitcoin_attestations": [{"height": 1, "merkle_root": "a" * 64}]
                    if proof.read_bytes() == b"complete proof" else [],
                "status": "BITCOIN_ATTESTATION_PRESENT" if proof.read_bytes() == b"complete proof" else "CALENDAR_PENDING"}
            return {"returncode": 0, "stdout": json.dumps(data), "stderr": ""}
        if self.error:
            raise self.error
        if "stamp" in args:
            Path(args[-1] + ".ots").write_bytes(b"pending proof")
        elif "upgrade" in args:
            Path(args[-1]).write_bytes(self.upgrade_bytes)
        return {"returncode": 0, "stdout": "", "stderr": "controlled calendar return"}


def stamp(tmp_path, client=None, **kw):
    spec, _ = frozen_file(tmp_path)
    client = client or Client()
    value = ots.retain_and_stamp(spec, event_id=EVENT, frozen_at_utc=FROZEN, event_time_utc=RELEASE,
        root=tmp_path / "retained", now=kw.pop("now", NOW), runner=client, **kw)
    return value, spec, client


def test_exact_bytes_pending_not_confirmation_and_idempotent_submission(tmp_path):
    value, spec, client = stamp(tmp_path)
    assert value["status"] == "CALENDAR_PENDING" and value["bitcoin_verified"] is False
    assert value["submission_before_release"] is True
    assert Path(value["path"]).read_bytes() == Path(spec["path"]).read_bytes()
    assert Path(value["path"]).read_bytes().startswith(b"\xef\xbb\xbf")
    first = value["submitted_at_utc"]
    value, _, _ = stamp(tmp_path, client, now=NOW + timedelta(minutes=1))
    assert value["submitted_at_utc"] == first
    assert sum("stamp" in c for c in client.calls) == 1
    assert "--no-bitcoin" in client.calls[0] and "--wait" not in client.calls[0]


def test_upgrade_keeps_original_and_never_claims_bitcoin_verification(tmp_path):
    value, spec, client = stamp(tmp_path)
    proof = Path(value["proof_path"])
    value = ots.maintain_timestamps(root=tmp_path / "retained", now=NOW + timedelta(hours=7), runner=client)
    assert value["status"] == "BITCOIN_ATTESTATION_PRESENT"
    assert value["bitcoin_verified"] is False
    assert proof.read_bytes() == b"complete proof"
    assert (proof.parent / "initial.ots").read_bytes() == b"pending proof"
    assert (proof.parent / (sha256(b"pending proof").hexdigest() + ".ots")).read_bytes() == b"pending proof"
    assert value["sha256"] == spec["sha256"]
    assert ots.maintain_timestamps(root=tmp_path / "retained", now=NOW + timedelta(hours=14), runner=client)["status"] == "NO_TIMESTAMP_DUE"


@pytest.mark.parametrize("failure", ["corrupt", "timeout"])
def test_failed_upgrade_preserves_valid_public_proof(tmp_path, failure):
    value, _, client = stamp(tmp_path)
    if failure == "corrupt":
        client.upgrade_bytes = b"corrupt"
    else:
        client.error = subprocess.TimeoutExpired("ots", 20)
    result = ots.maintain_timestamps(root=tmp_path / "retained", now=NOW + timedelta(hours=7), runner=client)
    assert result["status"] == "STAMP_ERROR"
    assert Path(value["proof_path"]).read_bytes() == b"pending proof"


def test_late_historical_submission_never_proves_pre_release_time(tmp_path):
    value, _, _ = stamp(tmp_path, now=NOW + timedelta(days=3))
    assert value["submission_before_release"] is False
    assert value["frozen_at_utc"] == FROZEN
    assert value["submitted_at_utc"] != FROZEN


def test_wrong_hash_is_rejected_before_network(tmp_path):
    spec, _ = frozen_file(tmp_path)
    client = Client()
    with pytest.raises(ValueError, match="BYTES_MISMATCH"):
        ots.retain_and_stamp({**spec, "sha256": "f" * 64}, event_id=EVENT,
            frozen_at_utc=FROZEN, event_time_utc=RELEASE, root=tmp_path / "r", runner=client)
    assert not client.calls


def test_preview_and_review_transport_attach_original_file_and_exact_proof(tmp_path, monkeypatch):
    from live_contentops import event_public_record_v1 as records
    from tests.test_event_public_record_v1 import article, source
    value, spec, client = stamp(tmp_path)
    monkeypatch.setattr(ots, "inspect", lambda source, proof: INSPECT(source, proof, runner=client))
    # Keep the helper used by the transport on the same isolated evidence root.
    monkeypatch.setattr(ots, "ROOT", tmp_path / "retained")
    for kind in ("EVENT_PREVIEW", "EVENT_REVIEW"):
        copy = article(spec, kind=kind)
        copy["event_pack_stage"] = "preview" if kind == "EVENT_PREVIEW" else "review"
        copy["frozen_public_record"] = records.validate_article_record(copy, [source(spec)])
        assets = records.attachments_for_article(copy, media_dir=tmp_path / kind / "media")
        assert len(assets) == 2
        assert all(Path(a["path"]).is_relative_to(tmp_path / kind / "media") for a in assets)
        assert Path(assets[0]["path"]).read_bytes() == Path(spec["path"]).read_bytes()
        assert assets[1]["sha256"] == value["proof_sha256"]
        assert not records.attachment_readback_matches(assets, [], "https://example.com/p/event")


def test_issued_article_keeps_its_proof_after_local_upgrade(tmp_path, monkeypatch):
    from live_contentops import event_public_record_v1 as records
    from tests.test_event_public_record_v1 import article, source
    value, spec, client = stamp(tmp_path)
    monkeypatch.setattr(ots, "inspect", lambda s, p, **kw: INSPECT(s, p, runner=client))
    monkeypatch.setattr(ots, "ROOT", tmp_path / "retained")
    copy = article(spec)
    copy["event_pack_stage"] = "preview"
    copy["frozen_public_record"] = records.validate_article_record(copy, [source(spec)])
    before = records.attachments_for_article(copy, media_dir=tmp_path / "media")
    RETAIN(spec, event_id=EVENT, frozen_at_utc=FROZEN, event_time_utc=RELEASE, root=tmp_path / "retained",
        now=NOW+timedelta(hours=7), runner=client, upgrade=True)
    after = records.attachments_for_article(copy, media_dir=tmp_path / "media")
    assert before == after
    assert after[1]["sha256"] == value["proof_sha256"]
    assert Path(after[1]["path"]).read_bytes() == b"pending proof"


def test_historical_unstamped_preview_keeps_its_original_upload_contract(tmp_path, monkeypatch):
    from live_contentops import event_public_record_v1 as records
    from tests.test_event_public_record_v1 import article, source
    _, spec, _ = stamp(tmp_path)
    monkeypatch.setattr(ots, "ROOT", tmp_path / "retained")
    copy = article(spec)
    copy["frozen_public_record"] = records.validate_article_record(copy, [source(spec)])
    assert records.attachments_for_article(copy, media_dir=tmp_path / "media") == []


def test_attach_freeze_consumer_stamps_before_saving_existing_packet(tmp_path, monkeypatch, capsys):
    from scripts import event_public_record as cli
    from tests.test_pre_event_preview_v1 import prepare
    from tests.test_capital_chronicle_report_feed_v1 import feed
    f = feed(tmp_path)
    prepare(f.tracker.store, tmp_path)
    spec, _ = frozen_file(tmp_path)
    client = Client()
    monkeypatch.setattr(ots, "retain_and_stamp", lambda spec, **kw: RETAIN(spec, **kw, runner=client))
    from live_contentops import event_pack_v1 as packs
    monkeypatch.setattr(packs, "freeze_ledger", lambda p: p)
    assert cli.main(["--store", str(f.tracker.store.db_path), "--attach-freeze", EVENT,
        "--freeze-file", spec["path"], "--freeze-sha256", spec["sha256"],
        "--timestamp-root", str(tmp_path / "retained")]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["timestamp"]["status"] == "CALENDAR_PENDING"
    assert result["sha256"] == spec["sha256"]
    from live_contentops.contentops_editorial_desk_v1 import STORY_PREPARATION
    row = f.tracker.store.list_outbox_messages(destination=STORY_PREPARATION)[-1]
    assert json.loads(row["payload"])["frozen_public_record"] == spec


@pytest.mark.parametrize("dry_run", [False, True])
def test_existing_minute_entry_maintains_proofs_without_changing_dry_run(tmp_path, monkeypatch, capsys, dry_run):
    from scripts import plan_status_posts as cli
    from live_contentops import plan_status_posts_v1 as posts
    from tests.test_capital_chronicle_report_feed_v1 import feed
    f = feed(tmp_path)
    calls = []
    monkeypatch.setattr(cli, "queue_posts", lambda *a, **k: {"status": "OK"})
    monkeypatch.setattr(posts, "record_run", lambda *a, **k: tmp_path / "run.json")
    monkeypatch.setattr(ots, "maintain_timestamps", lambda: calls.append(True) or {"status": "CALENDAR_PENDING"})
    assert cli.main(["--store", str(f.tracker.store.db_path), *(["--dry-run"] if dry_run else [])]) == 0
    result = json.loads(capsys.readouterr().out)
    assert bool(calls) is not dry_run
    assert ("event_timestamp" in result) is not dry_run
