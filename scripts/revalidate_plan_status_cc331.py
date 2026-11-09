"""Replay CC-330's copied TOUCH export through its exact Main reader and Publisher consumer.

Reads Main's Git objects only. Reader files and the writable test store live in a temporary
directory. Never opens the production store, invokes a transport or changes a schedule.
"""
from __future__ import annotations

import argparse
import ast
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from live_contentops import plan_status_posts_v1 as posts  # noqa: E402
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore  # noqa: E402


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _reader_snapshot(repository, commit, root):
    files = {}

    def collect(path):
        if path in files:
            return
        raw = subprocess.check_output(["git", "-C", str(repository), "show", commit + ":" + path],
                                      creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        files[path] = raw
        if path.endswith(".py"):
            for node in ast.parse(raw).body:
                if not isinstance(node, ast.ImportFrom):
                    continue
                module = node.module or ""
                if node.level:
                    module = path.rsplit("/", node.level)[0].replace("/", ".") + "." + module
                if module.startswith("tools."):
                    collect(module.replace(".", "/") + ".py")

    collect("tools/product/plan_status_export_v1.py")
    for name in ("CapitalChroniclePlanStatusV1", "CapitalChroniclePlanTransitionsV1"):
        collect("schemas/publication/" + name + ".schema.json")
    for path, raw in files.items():
        destination = root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
    return {path: hashlib.sha256(raw).hexdigest() for path, raw in files.items()}


def revalidate(repository, commit, export_dir):
    export_dir = Path(export_dir).resolve()
    with tempfile.TemporaryDirectory(prefix="cc331-reader-") as directory, ExitStack() as connections:
        class ReplayStore(ContentOpsDurableStore):
            def get_connection(self):
                connection = super().get_connection()
                connections.callback(connection.close)
                return connection

        scratch = Path(directory)
        reader = scratch / "main-reader"
        reader_hashes = _reader_snapshot(repository, commit, reader)
        inputs = {name: _sha(export_dir / name) for name in
                  ("plan-status.public.json", "plan-transitions.public.json")}
        export = posts.read_export(export_dir, main_root=reader)
        rows = posts.rows_from_export(export)
        events = export["transitions"]["transitions"]
        assert len(rows) == len(events) == 5
        compositions = []
        for event, row in zip(events, rows):
            assert row["plan_id"] == event["plan_id"] and row["at_utc"] == event["at_utc"]
            post = posts.compose(row)
            expected = "NOT_POSTED" if event["status"] == "TRIGGERED" else "COMPOSED"
            assert post["status"] == expected
            if expected == "NOT_POSTED":
                assert post["cause"] == "FILL_EVENT_SUPERSEDES_TRIGGER"
            assert "view changed" not in post.get("text", "").lower()
            compositions.append({"plan_id": row["plan_id"], "source_state": event["status"],
                                 "normalized_state": row["to"], "at_utc": row["at_utc"], "post": post})
        fill = next(row for row in rows if row["source_state"] == "FILLED")
        assert fill["plan_id"] == "plan_5eb033547e64c256929ab849"
        assert fill["at_utc"] == "2026-11-06T08:32:25.128000Z"
        assert "filled at Fri 6 Nov, 03:32 ET" in posts.compose(fill)["text"]
        clock = datetime.fromisoformat(export["status"]["generated_at_utc"].replace("Z", "+00:00"))
        clock += timedelta(seconds=1)
        store_path = scratch / "isolated.sqlite3"
        store = ReplayStore(store_path)
        options = dict(now=clock, main_root=reader)
        before = _sha(store_path)
        dry = posts.queue_posts(store, export_dir, dry_run=True, **options)
        assert dry["status"] == "OK" and dry["transitions_read"] == 5
        assert _sha(store_path) == before
        assert store.list_outbox_messages(destination=posts.DESTINATION) == []
        assert [q["key"] for q in dry["would_queue"]] == [fill["key"]]
        first = posts.queue_posts(store, export_dir, **options)
        assert first["queued"] == dry["would_queue"]
        frozen = store.get_outbox_message(fill["key"])["payload"]
        again = posts.queue_posts(store, export_dir, **options)
        assert again["queued"] == [] and again["already_queued"] == [fill["key"]]
        assert store.get_outbox_message(fill["key"])["payload"] == frozen
        assert inputs == {name: _sha(export_dir / name) for name in inputs}
        return {"status": "PASS", "verified_at_utc": datetime.now(timezone.utc).isoformat(),
                "implementation_root": str(ROOT), "implementation_sha256": _sha(posts.__file__),
                "main_commit": commit, "main_reader_sha256": reader_hashes, "export_sha256": inputs,
                "composition": compositions, "replay_clock_utc": clock.isoformat(), "dry_run": dry,
                "dry_run_store_bytes_unchanged": True, "isolated_store_queued": len(first["queued"]),
                "repeat_queued": len(again["queued"]), "frozen_outbox_bytes_unchanged": True,
                "public_transport_calls": 0, "production_store_access": False,
                "main_worktree_mutations": 0, "schedules_changed": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main-repository", type=Path, required=True)
    parser.add_argument("--main-commit", default="ef053ea0d36e372d6cf3053c6c2abfa0d62499a0")
    parser.add_argument("--export-dir", type=Path, default=ROOT / "tests/fixtures/cc331_touch_export")
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args(argv)
    record = json.loads(args.evidence.read_bytes()) if args.evidence.exists() else {}
    result = revalidate(args.main_repository, args.main_commit, args.export_dir)
    if record.get("export_sha256"):
        assert record["export_sha256"] == result["export_sha256"]
    record["acceptance"] = result
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "rows": len(result["composition"]),
                      "dry_run_store_bytes_unchanged": True, "repeat_queued": 0,
                      "evidence": str(args.evidence)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
