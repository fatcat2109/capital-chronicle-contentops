"""For Ops: import the exact accepted CC-074 packet, then prepare the existing publisher.

The default is read-only. --apply requires the hash of a fresh dry-run plan. This
does not publish, acquire sources, invoke models, change controls or schedules.
The private operation and its original binding/returns/review remain unchanged.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    canonical_bytes,
    sha256_of,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import (
    native_review_revision,
    require_current_final_visual_review,
    validate_release_media,
    validated_native_review,
)
from live_contentops.native_desktop_publication_v1 import (
    NativeReviewedPublication,
    live_publication_policy,
    prepare_native_publication,
    scheduled_publication_authority,
)
from live_contentops.native_desktop_workspace_v1 import resolve_workspace_path
from live_contentops.retrospective_piece_v1 import validate_retrospective_piece

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "docs/publisher/CC-074-private-20261101"
MANIFEST = ROOT / "docs/publisher/CC-074-live-20261102/promotion-manifest.json"
MANIFEST_SHA256 = "3297d335b23d7ac64bfd403a301b276f64307bfde52545ebbf635802a202a185"
ORIGINAL_PACKAGE = Path(
    r"A:\Capital Chronicle\Worktrees\ContentOps\codex-publisher-backlog"
    r"\docs\publisher\CC-074-private-20261101"
)
SOURCE_BINDING = Path(
    r"A:\Capital Chronicle\Worktrees\ContentOps\codex-publisher-backlog"
    r"\.task-runtime\cc-074\private-20261101\articles"
    r"\cc074-retro-fomc-20261028-v1\binding.json"
)
PROMOTION_DESTINATION = "internal:native-retrospective-promotion"


class ReadOnlyStore(ContentOpsDurableStore):
    """Use existing readers while refusing writes, migrations and WAL-mode changes."""

    def __init__(self, path):
        path = resolve_workspace_path(path)
        if not path.is_file():
            raise ValueError("CC074_EXISTING_STORE_REQUIRED:" + str(path))
        super().__init__(path, auto_migrate=False)
        self.verify_schema_integrity()

    def get_connection(self):
        return self.get_read_only_connection()


def _digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def _json(path):
    return json.loads(Path(path).read_bytes())


def _relocate(value, root):
    """Read-only validation view; never serialize relocated historical records."""
    if isinstance(value, dict):
        return {k: _relocate(v, root) for k, v in value.items()}
    if isinstance(value, list):
        return [_relocate(v, root) for v in value]
    if isinstance(value, str) and value.startswith(str(ORIGINAL_PACKAGE) + "\\"):
        return str(root / Path(value[len(str(ORIGINAL_PACKAGE)) + 1 :]))
    return value


def _snapshot(store, run_id):
    work = "cc-opportunity-" + sha256_of(run_id)
    with store.get_read_only_connection() as conn:
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("CC074_STORE_INTEGRITY_FAILED")
        if conn.execute("PRAGMA foreign_key_check").fetchone():
            raise ValueError("CC074_STORE_FOREIGN_KEY_FAILED")
        rows = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM outbox_messages WHERE work_item_id=? ORDER BY rowid",
                (work,),
            )
        ]
        reviews = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM review_records WHERE work_item_id=? ORDER BY rowid",
                (work,),
            )
        ]
        item = conn.execute(
            "SELECT * FROM work_items WHERE work_item_id=?", (work,)
        ).fetchone()
        dispatch = conn.execute(
            "SELECT 1 FROM platform_dispatches d JOIN outbox_messages o USING(message_id) "
            "WHERE o.work_item_id IN (?,?) LIMIT 1",
            (work, run_id),
        ).fetchone()
        active = conn.execute(
            "SELECT 1 FROM leases WHERE status='ACTIVE' AND expires_at>? LIMIT 1",
            (datetime.now(timezone.utc).isoformat(),),
        ).fetchone()
    if not item or dispatch or active:
        raise ValueError("CC074_SOURCE_MUST_BE_IDLE_UNDISPATCHED_OPERATION")
    if any(
        r["status"] != "EDITORIAL_INTERNAL"
        or not r["destination"].startswith("internal:")
        for r in rows
    ):
        raise ValueError("CC074_SOURCE_PUBLIC_OUTBOX_EXCLUDED")
    return rows, reviews, dict(item)


def verify_source(*, package_root=PACKAGE, binding_path=SOURCE_BINDING):
    """Pin the one granted FOMC packet; no arbitrary private-example promotion."""
    if _digest(MANIFEST) != MANIFEST_SHA256:
        raise ValueError("CC074_PROMOTION_MANIFEST_CHANGED")
    pin = _json(MANIFEST)
    root, binding_path = Path(package_root).resolve(), Path(binding_path).resolve()
    if _digest(root / "artifact-sha256.json") != pin["retained_seals_sha256"]:
        raise ValueError("CC074_ACCEPTED_SEALS_CHANGED")
    artifacts = _json(root / "artifact-sha256.json")["artifacts"]
    if len(artifacts) != 207:
        raise ValueError("CC074_EXACT_ACCEPTED_PACKAGE_REQUIRED")
    files = []
    original = resolve_workspace_path(ORIGINAL_PACKAGE)
    for artifact in artifacts:
        relative = Path(artifact["path"])
        source, target = (root / relative).resolve(), (original / relative).resolve()
        if (
            relative.is_absolute()
            or not source.is_relative_to(root)
            or not target.is_relative_to(original)
        ):
            raise ValueError("CC074_SEALED_PATH_OUTSIDE_PACKAGE")
        if (
            _digest(source) != artifact["sha256"]
            or source.stat().st_size != artifact["bytes"]
        ):
            raise ValueError("CC074_SEALED_BYTES_CHANGED:" + str(relative))
        if target.exists() and (
            not target.is_file() or _digest(target) != artifact["sha256"]
        ):
            raise ValueError("CC074_EXISTING_ARTIFACT_CONFLICT:" + str(target))
        files.append(
            {"source": str(source), "target": str(target), "sha256": artifact["sha256"]}
        )
    if _digest(binding_path) != pin["source_binding_sha256"]:
        raise ValueError("CC074_ORIGINAL_BINDING_CHANGED")
    binding = _json(binding_path)
    if (
        binding.get("owner_manual_validation") is not True
        or binding.get("run_id") != pin["run_id"]
        or resolve_workspace_path(binding["output_dir"]) != binding_path.parent
    ):
        raise ValueError("CC074_EXACT_PRIVATE_OPERATION_REQUIRED")
    source = ReadOnlyStore(binding["store_path"])
    rows, reviews, item = _snapshot(source, binding["run_id"])
    if {r["message_id"]: sha256_of(r) for r in rows} != pin["source_outbox_rows"] or {
        r["review_id"]: sha256_of(r) for r in reviews
    } != pin["source_reviews"]:
        raise ValueError("CC074_ACCEPTED_NATIVE_HISTORY_CHANGED")
    by_id = {r["message_id"]: r for r in rows}
    registered = by_id["native-operation-binding-" + sha256_of(binding["run_id"])]
    if json.loads(registered["payload"]) != binding:
        raise ValueError("CC074_EXACT_SOURCE_BINDING_REQUIRED")
    result = json.loads(
        by_id["cc-editorial-final-" + sha256_of(binding["run_id"])]["payload"]
    )
    if (
        result["article_identity"] != pin["article_identity"]
        or native_review_revision(result) != pin["package_revision"]
    ):
        raise ValueError("CC074_ACCEPTED_ARTICLE_REVISION_CHANGED")
    record = binding_path.parent / "qualified_article_record_v1.json"
    if _digest(record) != pin["qualified_record_sha256"]:
        raise ValueError("CC074_QUALIFIED_RECORD_CHANGED")
    piece = _relocate(_json(root / "piece.json"), root)
    check = validate_retrospective_piece(
        piece,
        documents=_relocate(_json(root / "chart-source-documents.json"), root),
        chart_assets=_relocate(_json(root / "chart-assets.json"), root),
        article_text=(root / "article.md").read_text(encoding="utf-8"),
    )
    final = _json(
        root
        / ("native/desktop_request_" + piece["final_visual_review"]["stage"] + ".json")
    )
    for name, digest in final["governed_input"]["binding"]["renderer_sha256"].items():
        if _digest(ROOT / name) != digest:
            raise ValueError("CC074_RENDERER_CHANGED_REVIEW_REQUIRED:" + name)
    return {
        "pin": pin,
        "binding": binding,
        "rows": rows,
        "reviews": reviews,
        "item": item,
        "files": files,
        "qualified_record": str(record),
        "source_check": check,
    }


def _target_guards(conn, operation, binding, promotion, *, own_lease=None):
    if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise ValueError("CC074_TARGET_INTEGRITY_FAILED")
    if conn.execute("PRAGMA foreign_key_check").fetchone():
        raise ValueError("CC074_TARGET_FOREIGN_KEY_FAILED")
    if conn.execute(
        "SELECT 1 FROM leases WHERE status='ACTIVE' AND expires_at>? "
        "AND lease_id!=? LIMIT 1",
        (datetime.now(timezone.utc).isoformat(), own_lease or ""),
    ).fetchone():
        raise ValueError("CC074_TARGET_HAS_ACTIVE_WORK")
    if (
        conn.execute(
            "SELECT 1 FROM platform_dispatches WHERE "
            "UPPER(status) LIKE '%UNKNOWN%' OR UPPER(status) LIKE '%AMBIG%' OR "
            "UPPER(status) LIKE '%STARTED%' OR UPPER(status) LIKE '%PENDING%' OR "
            "UPPER(status) LIKE '%SENDING%' LIMIT 1"
        ).fetchone()
        or conn.execute(
            "SELECT 1 FROM reconciliations WHERE status IN ('PENDING','STARTED','UNKNOWN_WRITE') "
            "LIMIT 1"
        ).fetchone()
    ):
        raise ValueError("CC074_EXISTING_PUBLICATION_RECOVERY_REQUIRED")
    work = operation["item"]["work_item_id"]
    existing = conn.execute(
        "SELECT * FROM outbox_messages WHERE message_id=?", (promotion["message_id"],)
    ).fetchone()
    if existing and any(existing[k] != v for k, v in promotion.items()):
        raise ValueError("CC074_PROMOTION_CONFLICT")
    allowed = {r["message_id"] for r in operation["rows"]}
    for row in conn.execute("SELECT * FROM outbox_messages"):
        value = json.loads(row["payload"])
        if (
            isinstance(value, dict)
            and value.get("article_identity") == operation["pin"]["article_identity"]
            and row["work_item_id"] not in {work, binding["run_id"]}
        ):
            raise ValueError("CC074_ARTICLE_IDENTITY_ALREADY_REGISTERED")
        if row["work_item_id"] not in {work, binding["run_id"]}:
            continue
        if not existing:
            raise ValueError("CC074_TARGET_RUN_ALREADY_EXISTS")
        if row["message_id"] in allowed:
            expected = next(
                r
                for r in _import_rows(
                    operation, binding, promoted_at_utc=existing["created_at"]
                )
                if r["message_id"] == row["message_id"]
            )
            if dict(row) != expected:
                raise ValueError("CC074_IMPORTED_HISTORY_CHANGED")
    for row in operation["reviews"]:
        prior = conn.execute(
            "SELECT * FROM review_records WHERE review_id=?", (row["review_id"],)
        ).fetchone()
        if prior and dict(prior) != row:
            raise ValueError("CC074_IMPORTED_REVIEW_CONFLICT")
    return bool(existing)


def _import_rows(operation, binding, *, promoted_at_utc=None):
    key = "native-operation-binding-" + sha256_of(binding["run_id"])
    return [
        {
            **row,
            "payload": canonical_bytes(binding).decode(),
            "created_at": promoted_at_utc or row["created_at"],
        }
        if row["message_id"] == key
        else row
        for row in operation["rows"]
    ]


def promotion_plan(operation, rollout):
    live_publication_policy(rollout, cutoff_utc=operation["binding"]["cutoff_utc"])
    source = operation["binding"]
    store_path = resolve_workspace_path(rollout["store_path"])
    if store_path in {
        resolve_workspace_path(source[k])
        for k in ("store_path", "published_memory_store")
    }:
        raise ValueError("CC074_PROMOTION_REQUIRES_DISTINCT_LIVE_STORE")
    out = (
        resolve_workspace_path(rollout["editorial_output_root"])
        / "owner-manual"
        / source["run_id"]
    )
    if out == resolve_workspace_path(source["output_dir"]):
        raise ValueError("CC074_PROMOTION_REQUIRES_DISTINCT_LIVE_OUTPUT")
    binding = {
        **source,
        "store_path": str(store_path),
        "output_dir": str(out),
        "published_memory_store": str(store_path),
        "published_memory_output_root": rollout["published_output_root"],
        "owner_manual_validation": False,
        "owner_manual_live": True,
        "live_authority_sha256": sha256_of(rollout["live_authority"]),
        "retrospective_authority_ref": operation["pin"]["authority_ref"],
        "promoted_from_binding_sha256": operation["pin"]["source_binding_sha256"],
    }
    original = next(
        r
        for r in operation["rows"]
        if r["message_id"] == "native-operation-binding-" + sha256_of(source["run_id"])
    )
    payload = {
        "schema_version": "contentops.retained_packet_promotion.v1",
        "source_manifest": operation["pin"],
        "original_binding_row": original,
        "live_binding": binding,
        "source_check": operation["source_check"],
        "public_write_performed": False,
    }
    promotion = {
        "message_id": "native-retrospective-promotion-" + sha256_of(source["run_id"]),
        "work_item_id": operation["item"]["work_item_id"],
        "destination": PROMOTION_DESTINATION,
        "payload": canonical_bytes(payload).decode(),
        "status": "EDITORIAL_INTERNAL",
    }
    target = ReadOnlyStore(store_path)
    from live_contentops.llm_operator_control_v1 import (
        assert_llm_operator_execution_enabled,
    )

    assert_llm_operator_execution_enabled()
    if target.get_operating_control()["operating_mode"] != "AUTONOMOUS_DEFAULT":
        raise ValueError("PUBLICATION_OPERATING_MODE_BLOCKED")
    with target.get_read_only_connection() as conn:
        repeated = _target_guards(conn, operation, binding, promotion)
    for filename, raw in (
        ("binding.json", canonical_bytes(binding)),
        (
            "qualified_article_record_v1.json",
            Path(operation["qualified_record"]).read_bytes(),
        ),
    ):
        path = out / filename
        if path.exists() and path.read_bytes() != raw:
            raise ValueError("CC074_LIVE_ARTIFACT_CONFLICT:" + str(path))
    plan = {
        "binding": binding,
        "promotion": promotion,
        "restore_files": operation["files"],
        "qualified_record_sha256": operation["pin"]["qualified_record_sha256"],
        "rollout_sha256": sha256_of(rollout),
    }
    return plan, repeated


def _write_exact(path, raw):
    """Create missing files only; never overwrite another worker's bytes."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError:
        if path.read_bytes() != raw:
            raise ValueError("CC074_EXISTING_ARTIFACT_CONFLICT:" + str(path)) from None


def promote(operation, rollout, *, apply=False, expected_plan_sha256=None):
    plan, repeated = promotion_plan(operation, rollout)
    digest = sha256_of(plan)
    binding, promotion = plan["binding"], plan["promotion"]
    report = {
        "classification": "CC074_PROMOTION_DRY_RUN",
        "plan_sha256": digest,
        "run_id": binding["run_id"],
        "article_identity": operation["pin"]["article_identity"],
        "binding_path": str(Path(binding["output_dir"]) / "binding.json"),
        "retained_artifact_root": str(resolve_workspace_path(ORIGINAL_PACKAGE)),
        "sealed_artifacts": len(operation["files"]),
        "missing_retained_artifacts": sum(
            not Path(f["target"]).exists() for f in operation["files"]
        ),
        "imported_outbox_rows": len(operation["rows"]),
        "already_imported": repeated,
        "model_invocations": 0,
        "source_requests": 0,
        "public_write_performed": False,
        "next_operation": "Ops reviews dry-run and applies its exact plan hash",
    }
    if not apply:
        return report
    if expected_plan_sha256 != digest:
        raise ValueError("CC074_EXACT_DRY_RUN_PLAN_HASH_REQUIRED")
    # Recover existing uncertain writes before any materialization or preparation.
    # All source/target conflicts have been checked before the first apply write.
    for file in operation["files"]:
        raw = Path(file["source"]).read_bytes()
        if sha256(raw).hexdigest() != file["sha256"]:
            raise ValueError("CC074_SEALED_BYTES_CHANGED_BEFORE_APPLY")
        _write_exact(file["target"], raw)
    source = ReadOnlyStore(operation["binding"]["store_path"])
    validated_native_review(source, run_id=binding["run_id"])
    require_current_final_visual_review(source, run_id=binding["run_id"])
    result, _, _ = validated_native_review(source, run_id=binding["run_id"])
    validate_release_media(result)
    store = ContentOpsDurableStore(binding["store_path"], auto_migrate=False)
    owner = "cc074-ops-promotion-" + uuid4().hex
    lease = store.acquire_lease(
        "internal:native-editorial:" + binding["run_id"], owner, ttl_seconds=900
    )
    try:
        with store.get_read_only_connection() as conn:
            _target_guards(
                conn, operation, binding, promotion, own_lease=lease["lease_id"]
            )
        # Source history is rechecked immediately before importing; never copy a
        # running editorial worker, a completed public attempt, or changed history.
        if _snapshot(source, binding["run_id"])[:2] != (
            operation["rows"],
            operation["reviews"],
        ):
            raise ValueError("CC074_SOURCE_CHANGED_BEFORE_IMPORT")
        _write_exact(
            Path(binding["output_dir"]) / "binding.json", canonical_bytes(binding)
        )
        _write_exact(
            Path(binding["output_dir"]) / "qualified_article_record_v1.json",
            Path(operation["qualified_record"]).read_bytes(),
        )
        item = operation["item"]
        store.create_work_item(
            story_id=item["story_id"],
            work_item_id=item["work_item_id"],
            title=item["title"],
            target_surface=item["target_surface"],
        )
        with store.get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                repeated = _target_guards(
                    conn, operation, binding, promotion, own_lease=lease["lease_id"]
                )
                if not repeated:
                    promoted_at_utc = store._get_now_iso()
                    for row in _import_rows(
                        operation, binding, promoted_at_utc=promoted_at_utc
                    ):
                        columns = list(row)
                        conn.execute(
                            "INSERT INTO outbox_messages ("
                            + ",".join(columns)
                            + ") VALUES ("
                            + ",".join("?" for _ in columns)
                            + ")",
                            list(row.values()),
                        )
                    for row in operation["reviews"]:
                        columns = list(row)
                        conn.execute(
                            "INSERT INTO review_records ("
                            + ",".join(columns)
                            + ") VALUES ("
                            + ",".join("?" for _ in columns)
                            + ")",
                            list(row.values()),
                        )
                    conn.execute(
                        "INSERT INTO outbox_messages (message_id,work_item_id,destination,payload,status,created_at) VALUES (?,?,?,?,?,?)",
                        (*promotion.values(), promoted_at_utc),
                    )
                conn.execute("COMMIT")
            except BaseException:
                conn.execute("ROLLBACK")
                raise
        scheduled_publication_authority(store, binding, rollout)
        state = NativeReviewedPublication(
            store, binding, native_invocation_id=None
        ).projection()
        # A rerun after any dispatch is observation only. UNKNOWN_WRITE was
        # refused above; only the existing publisher can reconcile it.
        with store.get_read_only_connection() as conn:
            dispatched = conn.execute(
                "SELECT 1 FROM platform_dispatches d JOIN outbox_messages o USING(message_id) WHERE o.work_item_id=? LIMIT 1",
                (binding["run_id"],),
            ).fetchone()
        prepared = None if dispatched else prepare_native_publication(store, binding)
        if prepared:
            state = NativeReviewedPublication(
                store, binding, native_invocation_id=None
            ).projection()
        return {
            **report,
            "classification": "CC074_PROMOTION_ALREADY_APPLIED"
            if repeated
            else "CC074_PROMOTED_NO_DISPATCH",
            "prepared": prepared,
            "publication": state,
            "next_operation": "publication-status"
            if dispatched
            else "publication-resume with the actual active native invocation id",
        }
    finally:
        store.release_lease(lease["lease_id"], owner, lease["fencing_token"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rollout", type=Path, default=ROOT / "config/native_desktop_rollout_v1.json"
    )
    parser.add_argument("--package-root", type=Path, default=PACKAGE)
    parser.add_argument("--source-binding", type=Path, default=SOURCE_BINDING)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="For Ops only: import and prepare; never dispatch",
    )
    parser.add_argument("--expected-plan-sha256")
    args = parser.parse_args(argv)
    try:
        rollout = _json(args.rollout)
        live_root = Path(r"A:\Capital Chronicle\Runtime\ContentOps")
        for name, expected in (
            ("store_path", live_root / "contentops_daily_app_v1.sqlite3"),
            ("editorial_output_root", live_root / "daily_app_outputs"),
            ("published_output_root", live_root / "daily_app_outputs"),
        ):
            if resolve_workspace_path(rollout[name]) != expected.resolve():
                raise ValueError("CC074_EXISTING_LIVE_OWNER_PATHS_REQUIRED:" + name)
        operation = verify_source(
            package_root=args.package_root, binding_path=args.source_binding
        )
        result = promote(
            operation,
            rollout,
            apply=args.apply,
            expected_plan_sha256=args.expected_plan_sha256,
        )
    except (ValueError, OSError, sqlite3.Error, KeyError) as error:
        print(
            json.dumps(
                {
                    "classification": "CC074_PROMOTION_BLOCKED",
                    "blocker": str(error),
                    "public_write_performed": False,
                },
                indent=2,
            )
        )
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
