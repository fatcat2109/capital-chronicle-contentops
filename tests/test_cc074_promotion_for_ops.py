"""Offline import/recovery contracts in temporary stores; no publication proof."""

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import (
    canonical_bytes,
    sha256_of,
)
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.native_desktop_editorial_v1 import (
    native_review_revision,
    require_current_final_visual_review,
)
from live_contentops.native_desktop_publication_v1 import (
    scheduled_publication_authority,
)
from live_contentops.native_desktop_workspace_v1 import workspace_snapshot
from scripts import promote_cc074_fomc_for_ops as promotion
from test_native_desktop_publication_v1 import seeded


@pytest.fixture
def controlled(tmp_path, monkeypatch):
    source, binding, _, result, _ = seeded(
        tmp_path / "source", monkeypatch, manual=True
    )
    binding = {
        k: v
        for k, v in binding.items()
        if k not in {"automation_id", "window_id", "slot_ordinal"}
    }
    key = "native-operation-binding-" + sha256_of(binding["run_id"])
    with source.get_connection() as conn:
        conn.execute(
            "UPDATE outbox_messages SET payload=? WHERE message_id=?",
            (canonical_bytes(binding).decode(), key),
        )
    out = Path(binding["output_dir"])
    (out / "binding.json").write_bytes(canonical_bytes(binding))
    rows, reviews, item = promotion._snapshot(
        promotion.ReadOnlyStore(source.db_path), binding["run_id"]
    )
    record = out / "qualified_article_record_v1.json"
    pin = {
        "run_id": binding["run_id"],
        "article_identity": result["article_identity"],
        "package_revision": native_review_revision(result),
        "authority_ref": "CONTROLLED CONTRACT FIXTURE, NEVER REAL PUBLICATION AUTHORITY",
        "source_binding_sha256": sha256(canonical_bytes(binding)).hexdigest(),
        "qualified_record_sha256": sha256(record.read_bytes()).hexdigest(),
    }
    operation = {
        "binding": binding,
        "rows": rows,
        "reviews": reviews,
        "item": item,
        "pin": pin,
        "files": [],
        "qualified_record": str(record),
        "source_check": {"status": "CONTROLLED_NOT_REAL_ARTICLE_ACCEPTANCE"},
    }
    target = ContentOpsDurableStore(
        tmp_path / "target" / "CONTROLLED_NOT_PRODUCTION.sqlite3"
    )
    control = target.get_operating_control()
    target.update_operating_control(
        operating_mode="AUTONOMOUS_DEFAULT",
        expected_state_version=control["state_version"],
        control_source="CONTROLLED_TEST",
    )
    rollout = {
        "schema_version": "contentops.native_desktop_rollout.v1",
        "public_write_authority": True,
        "store_path": str(target.db_path),
        "editorial_output_root": str(tmp_path / "live-output"),
        "published_output_root": str(tmp_path / "published"),
        "live_authority": {
            "scope": "V1_NATIVE_PUBLICATION",
            "thread_id": "CONTROLLED",
            "turn_id": "CONTROLLED",
            "message_id": "CONTROLLED",
            "not_before_utc": "2026-10-20T00:00:00Z",
        },
    }
    return source, target, operation, rollout


def apply(controlled):
    _, _, operation, rollout = controlled
    dry = promotion.promote(operation, rollout)
    return promotion.promote(
        operation, rollout, apply=True, expected_plan_sha256=dry["plan_sha256"]
    )


def test_read_only_plan_does_not_create_files_or_change_either_store(controlled):
    source, target, operation, rollout = controlled
    before = (workspace_snapshot(source.db_path), workspace_snapshot(target.db_path))
    first, second = (
        promotion.promote(operation, rollout),
        promotion.promote(operation, rollout),
    )
    assert first == second
    assert first["classification"] == "CC074_PROMOTION_DRY_RUN"
    assert not Path(first["binding_path"]).parent.exists()
    assert before == (
        workspace_snapshot(source.db_path),
        workspace_snapshot(target.db_path),
    )
    assert target.list_platform_dispatches() == []


def test_apply_preserves_native_history_review_identity_and_private_binding(controlled):
    source, target, operation, rollout = controlled
    original = workspace_snapshot(source.db_path)
    result = apply(controlled)
    assert result["classification"] == "CC074_PROMOTED_NO_DISPATCH"
    assert (
        result["prepared"]["article_identity"] == operation["pin"]["article_identity"]
    )
    assert len(result["publication"]["destinations"]) == 9
    binding = json.loads(Path(result["binding_path"]).read_bytes())
    assert binding["run_id"] == operation["binding"]["run_id"]
    assert binding["owner_manual_live"] is True
    assert operation["binding"]["owner_manual_validation"] is True
    assert workspace_snapshot(source.db_path) == original
    assert (
        binding["promoted_from_binding_sha256"]
        == operation["pin"]["source_binding_sha256"]
    )
    scheduled_publication_authority(target, binding, rollout)
    assert (
        require_current_final_visual_review(target, run_id=binding["run_id"])[
            "article_revision"
        ]
        == operation["pin"]["package_revision"]
    )
    for row in operation["rows"]:
        if row["message_id"].startswith("native-operation-binding-"):
            continue
        assert target.get_outbox_message(row["message_id"]) == row
    with target.get_read_only_connection() as conn:
        for row in operation["reviews"]:
            assert (
                dict(
                    conn.execute(
                        "SELECT * FROM review_records WHERE review_id=?",
                        (row["review_id"],),
                    ).fetchone()
                )
                == row
            )
        promoted = conn.execute(
            "SELECT * FROM outbox_messages WHERE destination=?",
            (promotion.PROMOTION_DESTINATION,),
        ).fetchone()
        archived = json.loads(promoted["payload"])
        live_row = conn.execute(
            "SELECT * FROM outbox_messages WHERE message_id=?",
            ("native-operation-binding-" + sha256_of(binding["run_id"]),),
        ).fetchone()
        assert live_row["created_at"] == promoted["created_at"]
        assert live_row["created_at"] != archived["original_binding_row"]["created_at"]
    assert (
        json.loads(archived["original_binding_row"]["payload"]) == operation["binding"]
    )
    assert target.list_platform_dispatches() == []
    assert result["public_write_performed"] is False


def test_second_apply_is_idempotent_and_retains_prepared_plan(controlled):
    _, target, _, _ = controlled
    first = apply(controlled)
    rows = target.list_outbox_messages()
    second = apply(controlled)
    assert second["classification"] == "CC074_PROMOTION_ALREADY_APPLIED"
    assert first["prepared"]["plan_hash"] == second["prepared"]["plan_hash"]
    assert target.list_outbox_messages() == rows
    assert target.list_platform_dispatches() == []


def test_apply_requires_exact_dry_run_hash_before_writes(controlled):
    _, target, operation, rollout = controlled
    before = workspace_snapshot(target.db_path)
    with pytest.raises(ValueError, match="EXACT_DRY_RUN_PLAN_HASH_REQUIRED"):
        promotion.promote(operation, rollout, apply=True, expected_plan_sha256="a" * 64)
    assert workspace_snapshot(target.db_path) == before
    assert not Path(rollout["editorial_output_root"]).exists()


@pytest.mark.parametrize(
    "failure", ["private_store", "absent_store", "authority", "mode", "pause"]
)
def test_live_owner_controls_are_not_bypassed(controlled, monkeypatch, failure):
    source, target, operation, rollout = controlled
    rollout = deepcopy(rollout)
    if failure == "private_store":
        rollout["store_path"] = str(source.db_path)
    elif failure == "absent_store":
        rollout["store_path"] = str(
            target.db_path.parent / "MUST_NOT_BE_CREATED.sqlite3"
        )
    elif failure == "authority":
        rollout["public_write_authority"] = False
    elif failure == "mode":
        control = target.get_operating_control()
        target.update_operating_control(
            operating_mode="SHADOW_ONLY",
            expected_state_version=control["state_version"],
            control_source="CONTROLLED_TEST",
        )
    elif failure == "pause":

        def paused():
            raise ValueError("LLM_OPERATOR_PAUSED")

        monkeypatch.setattr(
            "live_contentops.llm_operator_control_v1.assert_llm_operator_execution_enabled",
            paused,
        )
    before = workspace_snapshot(target.db_path)
    with pytest.raises(ValueError):
        promotion.promote(operation, rollout)
    assert workspace_snapshot(target.db_path) == before
    assert not Path(rollout["editorial_output_root"]).exists()
    if failure == "absent_store":
        assert not Path(rollout["store_path"]).exists()


def test_active_work_is_refused_without_stealing_lease(controlled):
    _, target, operation, rollout = controlled
    lease = target.acquire_lease(
        "internal:native-editorial:other-run",
        "CONTROLLED_OTHER_WORKER",
        ttl_seconds=900,
    )
    with pytest.raises(ValueError, match="TARGET_HAS_ACTIVE_WORK"):
        promotion.promote(operation, rollout)
    with target.get_read_only_connection() as conn:
        assert (
            dict(
                conn.execute(
                    "SELECT * FROM leases WHERE lease_id=?", (lease["lease_id"],)
                ).fetchone()
            )
            == lease
        )


def add_dispatch(store, status, *, work="unrelated-controlled-work"):
    store.create_work_item(
        story_id=work,
        title="CONTROLLED dispatch",
        target_surface="TEST",
        work_item_id=work,
    )
    store.register_outbox_message(
        message_id="CONTROLLED-message",
        work_item_id=work,
        destination="TEST",
        payload='{"controlled":true}',
        status="PENDING",
    )
    with store.get_connection() as conn:
        conn.execute(
            "INSERT INTO platform_dispatches VALUES (?,?,?,?,?,?,?,?)",
            (
                "CONTROLLED-dispatch",
                "CONTROLLED-message",
                "substack",
                status,
                "2026-11-02T00:00:00Z",
                None,
                None,
                None,
            ),
        )


@pytest.mark.parametrize("status", ["UNKNOWN_WRITE", "DISPATCH_ATTEMPT_STARTED"])
def test_existing_uncertain_write_requires_recovery_before_import(controlled, status):
    _, target, operation, rollout = controlled
    add_dispatch(target, status)
    before = workspace_snapshot(target.db_path)
    with pytest.raises(ValueError, match="EXISTING_PUBLICATION_RECOVERY_REQUIRED"):
        promotion.promote(operation, rollout)
    assert workspace_snapshot(target.db_path) == before


def test_apply_after_a_dispatch_only_observes_existing_publication(
    controlled, monkeypatch
):
    _, target, operation, _ = controlled
    apply(controlled)
    add_dispatch(target, "CONFIRMED", work=operation["binding"]["run_id"])
    monkeypatch.setattr(
        promotion,
        "prepare_native_publication",
        lambda *a: pytest.fail("Must not prepare after dispatch"),
    )
    result = apply(controlled)
    assert result["classification"] == "CC074_PROMOTION_ALREADY_APPLIED"
    assert result["prepared"] is None
    assert result["next_operation"] == "publication-status"
    assert len(target.list_platform_dispatches()) == 1


def test_copy_import_is_atomic_and_can_resume_after_failure(controlled):
    _, target, operation, _ = controlled
    with target.get_connection() as conn:
        conn.execute(
            "CREATE TRIGGER controlled_import_failure BEFORE INSERT ON review_records "
            "BEGIN SELECT RAISE(ABORT, 'CONTROLLED_IMPORT_FAILURE'); END"
        )
    with pytest.raises(Exception, match="CONTROLLED_IMPORT_FAILURE"):
        apply(controlled)
    with target.get_read_only_connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM outbox_messages").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM review_records").fetchone()[0] == 0
    with target.get_connection() as conn:
        conn.execute("DROP TRIGGER controlled_import_failure")
    result = apply(controlled)
    assert result["classification"] == "CC074_PROMOTED_NO_DISPATCH"
    assert target.get_outbox_message(operation["rows"][0]["message_id"])


def test_stale_source_history_is_refused_before_import(controlled):
    source, target, operation, _ = controlled
    row = next(
        r
        for r in operation["rows"]
        if r["message_id"].startswith("cc-editorial-final-")
    )
    with source.get_connection() as conn:
        conn.execute(
            "UPDATE outbox_messages SET created_at='CONTROLLED_CHANGED' WHERE message_id=?",
            (row["message_id"],),
        )
    with pytest.raises(ValueError, match="SOURCE_CHANGED_BEFORE_IMPORT"):
        apply(controlled)
    assert target.list_outbox_messages() == []


def test_existing_same_article_in_another_run_is_not_duplicated(controlled):
    _, target, operation, rollout = controlled
    target.create_work_item(
        story_id="CONTROLLED_OTHER_RUN",
        title="CONTROLLED other run",
        target_surface="TEST",
        work_item_id="CONTROLLED_OTHER_RUN",
    )
    target.register_outbox_message(
        message_id="CONTROLLED_other_article",
        work_item_id="CONTROLLED_OTHER_RUN",
        destination="internal:cc-report-simple-result",
        payload=json.dumps({"article_identity": operation["pin"]["article_identity"]}),
        status="EDITORIAL_INTERNAL",
    )
    before = workspace_snapshot(target.db_path)
    with pytest.raises(ValueError, match="ARTICLE_IDENTITY_ALREADY_REGISTERED"):
        promotion.promote(operation, rollout)
    assert workspace_snapshot(target.db_path) == before


def test_promotion_record_cannot_be_repurposed_after_import(controlled):
    _, target, operation, rollout = controlled
    apply(controlled)
    with target.get_connection() as conn:
        conn.execute(
            "UPDATE outbox_messages SET destination='CONTROLLED_WRONG_OWNER' WHERE destination=?",
            (promotion.PROMOTION_DESTINATION,),
        )
    with pytest.raises(ValueError, match="PROMOTION_CONFLICT"):
        promotion.promote(operation, rollout)


def test_conflicting_live_file_is_never_overwritten(controlled):
    _, target, operation, rollout = controlled
    out = (
        Path(rollout["editorial_output_root"])
        / "owner-manual"
        / operation["binding"]["run_id"]
    )
    out.mkdir(parents=True)
    (out / "binding.json").write_bytes(b"CONTROLLED unrelated work")
    before = workspace_snapshot(target.db_path)
    with pytest.raises(ValueError, match="LIVE_ARTIFACT_CONFLICT"):
        apply(controlled)
    assert (out / "binding.json").read_bytes() == b"CONTROLLED unrelated work"
    assert workspace_snapshot(target.db_path) == before


def test_changed_manifest_or_seals_cannot_admit_another_private_example(
    tmp_path, monkeypatch
):
    bad = tmp_path / "changed-manifest.json"
    bad.write_bytes(b"{}")
    monkeypatch.setattr(promotion, "MANIFEST", bad)
    with pytest.raises(ValueError, match="PROMOTION_MANIFEST_CHANGED"):
        promotion.verify_source()
    monkeypatch.undo()
    (tmp_path / "artifact-sha256.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="ACCEPTED_SEALS_CHANGED"):
        promotion.verify_source(package_root=tmp_path)


def test_original_file_materialization_is_create_only(tmp_path):
    file = tmp_path / "accepted" / "artifact.png"
    promotion._write_exact(file, b"CONTROLLED accepted bytes")
    promotion._write_exact(file, b"CONTROLLED accepted bytes")
    with pytest.raises(ValueError, match="EXISTING_ARTIFACT_CONFLICT"):
        promotion._write_exact(file, b"CONTROLLED conflicting bytes")
    assert file.read_bytes() == b"CONTROLLED accepted bytes"
