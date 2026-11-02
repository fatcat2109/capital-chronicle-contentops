"""One offline CC-074 replay with exact historical rows and temporary storage."""

import json
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from tempfile import mkdtemp
from unittest.mock import patch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts import promote_cc074_fomc_for_ops as p
from live_contentops import native_desktop_editorial_v1 as editorial
from live_contentops import native_desktop_workspace_v1 as workspace
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore

ROOT = Path(__file__).resolve().parents[3]
sys.tracebacklimit = 10
operation = p.verify_source()
original_binding = operation["binding"]
original_store = Path(original_binding["store_path"])
original_snapshot = workspace.workspace_snapshot(original_store)
task_root = ROOT / ".task-runtime/cc-074"
folder = Path(mkdtemp(prefix="retained-promotion-", dir=task_root)).resolve()
assert folder.is_relative_to(task_root.resolve())
source = ContentOpsDurableStore(folder / "CONTROLLED_SOURCE_COPY.sqlite3")
item = operation["item"]
source.create_work_item(
    story_id=item["story_id"],
    work_item_id=item["work_item_id"],
    title=item["title"],
    target_surface=item["target_surface"],
)
with source.get_connection() as conn:
    for table, rows in (
        ("outbox_messages", operation["rows"]),
        ("review_records", operation["reviews"]),
    ):
        for row in rows:
            conn.execute(
                "INSERT INTO "
                + table
                + " ("
                + ",".join(row)
                + ") VALUES ("
                + ",".join("?" for _ in row)
                + ")",
                list(row.values()),
            )
source_before = workspace.workspace_snapshot(source.db_path)
manifest = {
    "schema_version": workspace.SCHEMA,
    "paths": [
        {"source": str(original_store), "target": str(source.db_path), "kind": "store"},
        {
            "source": str(p.ORIGINAL_PACKAGE),
            "target": str(p.PACKAGE),
            "kind": "directory",
        },
    ],
}
manifest["manifest_sha256"] = workspace._hash(manifest)
manifest_path = folder / "CONTROLLED_REFERENCE_RELOCATION.json"
manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
target = ContentOpsDurableStore(folder / "CONTROLLED_TARGET_COPY.sqlite3")
control = target.get_operating_control()
target.update_operating_control(
    operating_mode="AUTONOMOUS_DEFAULT",
    expected_state_version=control["state_version"],
    control_source="CONTROLLED_CC074_REPLAY_ONLY",
)
rollout = p._json(ROOT / "config/native_desktop_rollout_v1.json")
live_store_path = rollout["store_path"]
rollout = {
    **rollout,
    "store_path": str(target.db_path),
    "editorial_output_root": str(folder / "output"),
    "published_output_root": str(folder / "published"),
}
assert Path(rollout["store_path"]).resolve() != Path(live_store_path).resolve()
# Preserve original accepted JSON path labels while routing only file I/O to the
# same sealed bytes. No production resolver or accepted artifact is edited.
file_check = editorial._final_visual_file


def exact_label_file(item):
    verified = file_check(item)
    return {**verified, "path": item["path"]}


image_open = Image.open


def fixture_path(file):
    file = Path(file)
    return (
        p.PACKAGE / file.relative_to(p.ORIGINAL_PACKAGE)
        if file.is_relative_to(p.ORIGINAL_PACKAGE)
        else file
    )


def relocated_image_open(file, *args, **kwargs):
    return image_open(
        fixture_path(file) if isinstance(file, (str, Path)) else file, *args, **kwargs
    )


path_open = Path.open


def relocated_path_open(file, mode="r", *args, **kwargs):
    if file.is_relative_to(p.ORIGINAL_PACKAGE):
        assert not any(c in mode for c in "wax+"), (
            "Original artifacts must be read-only"
        )
        file = fixture_path(file)
    return path_open(file, mode, *args, **kwargs)


path_stat = Path.stat


def relocated_path_stat(file, *args, **kwargs):
    if file.is_relative_to(p.ORIGINAL_PACKAGE):
        file = fixture_path(file)
    return path_stat(file, *args, **kwargs)


operation["files"] = [{**f, "target": f["source"]} for f in operation["files"]]
with (
    patch.object(workspace, "DEFAULT_MANIFEST", manifest_path),
    patch.object(editorial, "_final_visual_file", exact_label_file),
    patch.object(Image, "open", relocated_image_open),
    patch.object(Path, "open", relocated_path_open),
    patch.object(Path, "stat", relocated_path_stat),
):
    dry = p.promote(operation, rollout)
    first = p.promote(
        operation, rollout, apply=True, expected_plan_sha256=dry["plan_sha256"]
    )
    assert first["classification"] == "CC074_PROMOTED_NO_DISPATCH", first
    assert first["publication"]["state"] != "INVALIDATED", first["publication"]
    binding = p._json(first["binding_path"])
    p.scheduled_publication_authority(target, binding, rollout)
    accepted = editorial.require_current_final_visual_review(
        target, run_id=binding["run_id"]
    )
    assert accepted == p._json(p.PACKAGE / "piece.json")["final_visual_review"]
    plan, handoff_root = p.NativeReviewedPublication(
        target, binding, native_invocation_id=None
    ).validate()
    final_source = json.loads(
        next(
            r["payload"]
            for r in operation["rows"]
            if r["message_id"] == "cc-editorial-final-" + p.sha256_of(binding["run_id"])
        )
    )
    assert p._json(handoff_root / "article_manifest_v1.json") == final_source["article"]
    before_repeat = target.list_outbox_messages()
    repeat = p.promote(
        operation, rollout, apply=True, expected_plan_sha256=dry["plan_sha256"]
    )
    assert repeat["classification"] == "CC074_PROMOTION_ALREADY_APPLIED"
    assert before_repeat == target.list_outbox_messages()
    assert len(repeat["publication"]["destinations"]) == 9
    assert target.list_platform_dispatches() == []
assert workspace.workspace_snapshot(source.db_path) == source_before
assert workspace.workspace_snapshot(original_store) == original_snapshot
for f in operation["files"]:
    assert sha256(Path(f["source"]).read_bytes()).hexdigest() == f["sha256"]
result = {
    "checked_at_utc": datetime.now(timezone.utc).isoformat(),
    "classification": "EXACT_RETAINED_PACKET_ISOLATED_REPLAY_PASS",
    "scope": "Disposable source/target stores and process-local file I/O relocation only; not production or new visual/model proof",
    "source_outbox_rows": len(operation["rows"]),
    "source_reviews": len(operation["reviews"]),
    "sealed_artifacts_verified": len(operation["files"]),
    "original_source_store_unchanged": True,
    "copied_source_store_unchanged": True,
    "original_binding_and_native_returns_unchanged": True,
    "same_prior_final_visual_acceptance_revalidated": True,
    "new_final_visual_review": False,
    "run_id": binding["run_id"],
    "article_identity": plan["article_identity"],
    "plan_hash": plan["plan_hash"],
    "repeat_outbox_identical": True,
    "canonical_and_derivative_destinations": 9,
    "public_dispatch_rows": 0,
    "model_invocations": 0,
    "source_requests": 0,
    "live_store_apply_calls": 0,
    "live_store_path_excluded_from_replay": live_store_path,
    "fixture_root": str(folder),
    "file_reference_relocation": manifest["paths"][1],
    "next_actor": "Claude Ops",
    "next_action": "Run fresh live dry-run, apply exact reviewed plan, continue sole V1 publisher/readback",
}
destination = ROOT / "docs/publisher/CC-074-live-20261102/promotion-replay.json"
destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
