"""
Comprehensive Unit, Resilience, CAS, Lease, Fencing, Artifact Integrity, Replay, Authority Guard,
and Redaction Tests for Durable Operational Store v1 (Wave 02 Final Correction).
"""

import json
import os
import pathlib
import sqlite3
import tempfile
import threading
import pytest

from live_contentops.durable_operational_store_v1 import (
    ContentOpsDurableStore,
    DurableStoreError,
    MigrationError,
    InvalidStateTransitionError,
    CASStateConflictError,
    TransitionValidationError,
    WorkItemNotFoundError,
    StaleFencingTokenError,
    LeaseConflictError,
    DurableStateCorruptionError,
    Wave02AuthorityViolationError,
    ArtifactNotFoundError,
    ArtifactValidationError,
    build_event_envelope,
    canonical_json,
    compute_sha256,
    GENESIS_PREVIOUS_HASH,
)
from live_contentops.production_orchestrator_v1 import (
    CANONICAL_OPERATIONS,
    OPERATION_CONTRACTS,
    RESTART_SAFE,
    ContentOpsDurableContext,
    ContentOpsProductionOrchestrator,
    OperationFailurePersistenceError,
    OperationLifecycleError,
)
import live_contentops.historical_schema_compatibility_v1 as historical_compatibility
from tests.fixtures.historical_wave02_schema_lineage_v1 import create_exact_historical_database


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_contentops_durable_store.sqlite"
    store = ContentOpsDurableStore(db_file, busy_timeout_ms=3000, auto_migrate=True)
    return store


def test_wal_and_foreign_keys_enforcement(temp_db):
    pragmas = temp_db.query_pragmas()
    assert pragmas["journal_mode"] == "WAL"
    assert pragmas["foreign_keys"] == 1
    assert pragmas["busy_timeout_ms"] == 3000


def test_clean_init_and_idempotent_migrations(temp_db):
    version = temp_db.get_current_schema_version()
    assert version == 9
    applied = temp_db.run_migrations()
    assert applied == 0
    assert temp_db.verify_schema_integrity() is True


def test_real_multi_version_migration_upgrade(tmp_path):
    db_file = tmp_path / "test_upgrade.sqlite"
    store = ContentOpsDurableStore(db_file, auto_migrate=True)
    assert store.get_current_schema_version() == 9

    conn = store.get_connection()
    try:
        rows = conn.execute("SELECT version, description FROM schema_migrations ORDER BY version ASC;").fetchall()
        assert len(rows) == 9
        assert rows[0]["version"] == 1
        assert rows[1]["version"] == 2
        assert rows[2]["version"] == 3
        assert rows[3]["version"] == 4
        assert rows[4]["version"] == 5
        assert rows[5]["version"] == 6
        assert rows[6]["version"] == 7
        assert rows[7]["version"] == 8
        assert rows[8]["version"] == 9
    finally:
        conn.close()


def test_applied_migration_checksum_drift_rejection(temp_db):
    # Tamper with schema_migrations recorded checksum
    conn = temp_db.get_connection()
    try:
        conn.execute("UPDATE schema_migrations SET checksum = 'bad_checksum' WHERE version = 1;")
    finally:
        conn.close()

    with pytest.raises(MigrationError, match="Checksum drift"):
        temp_db.verify_applied_migrations()


def test_partial_migration_failure_rollback_and_restore(tmp_path):
    db_file = tmp_path / "test_migration_failure.sqlite"
    store = ContentOpsDurableStore(db_file, auto_migrate=True)
    assert store.get_current_schema_version() == 9

    store.create_work_item(story_id="story_pre_fail", title="Pre Fail Story", target_surface="substack", work_item_id="wi_pre_fail")

    from live_contentops.durable_operational_store_v1 import MIGRATIONS, Migration, SCHEMA_VERSION
    bad_sql = "CREATE TABLE temp_test_table (id INT); INVALID SYNTAX ERROR STATEMENT;"
    MIGRATIONS.append(Migration(SCHEMA_VERSION + 1, "Bad Migration Future", bad_sql, "test_failure.v1"))

    try:
        with pytest.raises(MigrationError):
            store.run_migrations()

        assert store.get_current_schema_version() == SCHEMA_VERSION

        conn = store.get_connection()
        try:
            tbl_check = conn.execute(
                "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='temp_test_table';"
            ).fetchone()[0]
            assert tbl_check == 0

            item = conn.execute("SELECT * FROM work_items WHERE work_item_id = 'wi_pre_fail';").fetchone()
            assert item is not None
            assert item["title"] == "Pre Fail Story"
        finally:
            conn.close()
    finally:
        MIGRATIONS.pop()


def test_historical_post_commit_verification_failure_restores_and_records_redacted_receipt(
    tmp_path, monkeypatch
):
    db_file = tmp_path / "historical_recovery.sqlite"
    fixture = create_exact_historical_database(
        db_file,
        originating_commit="e24a4492e9d72f55c704168d637b7628e49140cd",
    )
    original_migrations = fixture["migration_rows"]
    injected_message = "post-commit verification failure bearer=must-not-persist"
    original_verify = historical_compatibility._verify_upgraded_database

    def fail_after_full_verification(*args, **kwargs):
        original_verify(*args, **kwargs)
        raise RuntimeError(injected_message)

    monkeypatch.setattr(historical_compatibility, "_verify_upgraded_database", fail_after_full_verification)

    with pytest.raises(RuntimeError, match="post-commit verification failure"):
        ContentOpsDurableStore(db_file, auto_migrate=True)

    recovery_paths = list(tmp_path.glob(f"{db_file.name}.recovery.*.sqlite"))
    receipt_paths = list(tmp_path.glob(f"{db_file.name}.migration_failure_*.sqlite"))
    assert len(recovery_paths) == 1
    assert len(receipt_paths) == 1
    restored_hash = compute_sha256(db_file.read_bytes())
    assert compute_sha256(recovery_paths[0].read_bytes()) == restored_hash
    assert not pathlib.Path(f"{db_file}-wal").exists()
    assert not pathlib.Path(f"{db_file}-shm").exists()

    restored = sqlite3.connect(str(db_file))
    restored.row_factory = sqlite3.Row
    try:
        assert restored.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        restored_migrations = tuple(
            dict(row)
            for row in restored.execute(
                "SELECT version,checksum,applied_at,description FROM schema_migrations ORDER BY version"
            ).fetchall()
        )
        assert restored_migrations == original_migrations
        assert restored.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_lineage_metadata'"
        ).fetchone()[0] == 0
    finally:
        restored.close()

    receipt = sqlite3.connect(str(receipt_paths[0]))
    receipt.row_factory = sqlite3.Row
    try:
        assert receipt.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        row = dict(receipt.execute("SELECT * FROM migration_failure_receipts").fetchone())
    finally:
        receipt.close()
    assert row["source_lineage_id"] == "wave02.e24a449.schema_v1.no_genesis"
    assert row["source_database_hash"] == restored_hash
    assert row["failed_version"] == 4
    assert row["error_class"] == "RuntimeError"
    assert row["error_message_hash"] == compute_sha256(injected_message.encode("utf-8"))
    assert row["restore_integrity_status"] == "PASS_SOURCE_HASH_AND_SQLITE_INTEGRITY"
    assert injected_message.encode("utf-8") not in receipt_paths[0].read_bytes()


@pytest.mark.parametrize(
    ("originating_commit", "expected_lineage_id", "expected_baselines", "expected_genesis"),
    (
        (
            "e24a4492e9d72f55c704168d637b7628e49140cd",
            "wave02.e24a449.schema_v1.no_genesis",
            2,
            0,
        ),
        (
            "3cc531a3d30848f54329d25913018882f6b71bcd",
            "wave02.3cc531a.schema_v2.no_genesis",
            2,
            0,
        ),
        (
            "33225d5e8d79ad229ad93d203e8d2e5018bb2738",
            "wave02.33225d5.schema_v3.envelope_genesis",
            0,
            2,
        ),
        (
            "615a96fb20aa97fd76bb3343e9150daec40d9031",
            "wave02.615a96f.schema_v3.preservation_genesis",
            0,
            2,
        ),
        (
            "03337e8f82478cf578866a5a1749d96acd687d3d",
            "wave02.03337e8.schema_v3.canonical_pre_v4",
            0,
            2,
        ),
    ),
)
def test_exact_historical_lineage_upgrade_preserves_rows_and_replays(
    tmp_path,
    originating_commit,
    expected_lineage_id,
    expected_baselines,
    expected_genesis,
):
    db_file = tmp_path / f"historical_{originating_commit[:7]}.sqlite"
    fixture = create_exact_historical_database(
        db_file,
        originating_commit=originating_commit,
    )

    store = ContentOpsDurableStore(db_file, auto_migrate=True)

    assert store.get_current_schema_version() == 4
    assert not list(tmp_path.glob(f"{db_file.name}.recovery.*.sqlite"))
    assert not list(tmp_path.glob(f"{db_file.name}.migration_failure_*.sqlite"))

    connection = store.get_connection()
    try:
        metadata = dict(connection.execute("SELECT * FROM schema_lineage_metadata").fetchone())
        assert metadata["source_lineage_id"] == expected_lineage_id
        assert metadata["source_schema_fingerprint"] == fixture["schema_fingerprint"]
        assert metadata["compatibility_version"] == 4

        migrations = tuple(
            dict(row)
            for row in connection.execute(
                "SELECT version,checksum,applied_at,description FROM schema_migrations ORDER BY version"
            ).fetchall()
        )
        assert migrations[:-1] == fixture["migration_rows"]
        assert migrations[-1]["version"] == 4

        for expected_projection in fixture["work_item_projections"]:
            actual = dict(
                connection.execute(
                    "SELECT work_item_id,story_id,title,target_surface,current_state,state_version,created_at,updated_at "
                    "FROM work_items WHERE work_item_id=?",
                    (expected_projection["work_item_id"],),
                ).fetchone()
            )
            assert actual == expected_projection

        assert connection.execute(
            "SELECT count(*) FROM legacy_projection_baselines"
        ).fetchone()[0] == expected_baselines
        assert connection.execute(
            "SELECT count(*) FROM transition_events WHERE event_kind='WORK_ITEM_CREATED'"
        ).fetchone()[0] == expected_genesis

        migrated_source_event_ids = {
            payload["legacy_migration"]["source_event_id"]
            for payload in (
                json.loads(row[0])
                for row in connection.execute(
                    "SELECT event_payload_json FROM transition_events "
                    "WHERE event_kind!='LEGACY_PROJECTION_BASELINE'"
                ).fetchall()
            )
        }
        assert migrated_source_event_ids == set(fixture["source_event_ids"])

        artifact_evidence = dict(
            connection.execute(
                "SELECT source_record_hash,migrated_scope FROM legacy_artifact_evidence WHERE artifact_id=?",
                (fixture["artifact_id"],),
            ).fetchone()
        )
        assert len(artifact_evidence["source_record_hash"]) == 64
        assert artifact_evidence["migrated_scope"] in {
            "WORK_ITEM_EXACT",
            "LEGACY_UNSCOPED_QUARANTINED",
        }

        assert connection.execute("SELECT count(*) FROM assignments").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM leases").fetchone()[0] == 1
        assert connection.execute("SELECT count(*) FROM heartbeats").fetchone()[0] == 1
    finally:
        connection.close()

    expected_counts = {
        "wi_historical_alpha": 3 if expected_baselines else 2,
        "wi_historical_beta": 2 if expected_baselines else 1,
    }
    for projection in fixture["work_item_projections"]:
        replay = store.replay_work_item_events(projection["work_item_id"])
        assert replay["verification_status"] == "PASS"
        assert replay["replayed_state"] == projection["current_state"]
        assert replay["replayed_version"] == projection["state_version"]
        assert replay["event_count"] == expected_counts[projection["work_item_id"]]


def test_canonical_json_encoder_is_a_single_shared_object():
    """The migration writer and the replay verifier must share one encoder object.

    Wave 02 previously defined a second ``canonical_json`` inside the store module
    with ``ensure_ascii=False`` while the migration path used the compatibility
    module's ``ensure_ascii=True`` encoder. Both modules imported cleanly, all
    ASCII-only tests passed, and the divergence only surfaced as an unreplayable
    database once any non-ASCII byte entered a payload. Identity is asserted here
    (not merely equal output) so a re-introduced local definition fails immediately
    instead of failing silently on data the suite happens not to exercise.
    """
    assert canonical_json is historical_compatibility.canonical_json
    assert historical_compatibility._canonical_json is historical_compatibility.canonical_json


def test_canonical_json_matches_declared_dependency_manifest_contract():
    """The encoder's behaviour must match the contract string hashed into every database.

    ``DEPENDENCY_MANIFEST["canonical_json"]`` is embedded in the manifest whose SHA-256
    is written to ``schema_lineage_metadata``. If the code drifts from the declared
    string, already-migrated databases assert a guarantee the code no longer honours.
    """
    declared = historical_compatibility.DEPENDENCY_MANIFEST["canonical_json"]
    assert declared == historical_compatibility.CANONICAL_JSON_CONTRACT
    assert declared == "json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False)"

    # sort_keys=True: key insertion order cannot perturb the hash.
    assert canonical_json({"b": 1, "a": 2}) == canonical_json({"a": 2, "b": 1}) == '{"a":2,"b":1}'
    # separators: no incidental whitespace.
    assert canonical_json({"a": [1, 2]}) == '{"a":[1,2]}'
    # ensure_ascii=True: non-ASCII is escaped, never emitted as raw UTF-8.
    assert canonical_json({"t": "caf\u00e9 \u2014 r\u00e9sum\u00e9"}) == '{"t":"caf\\u00e9 \\u2014 r\\u00e9sum\\u00e9"}'
    assert canonical_json({"t": "caf\u00e9"}).isascii()
    # allow_nan=False: non-standard JSON tokens are rejected, not written to the ledger.
    for invalid in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError):
            canonical_json({"v": invalid})


def test_dependency_manifest_hash_is_pinned_against_silent_lineage_drift():
    """Pin the manifest hash recorded in every migrated database.

    Any edit to DEPENDENCY_MANIFEST changes this hash and invalidates the lineage
    metadata of databases already migrated in the field. Changing this constant is
    therefore a deliberate compatibility-version decision, not an incidental edit.
    """
    assert historical_compatibility.DEPENDENCY_MANIFEST_HASH == (
        "6130da750b36fed3183816218717d008a74234efd12dcc92725ab25c0cc12f33"
    )
    assert compute_sha256(historical_compatibility.DEPENDENCY_MANIFEST_JSON) == (
        historical_compatibility.DEPENDENCY_MANIFEST_HASH
    )


def test_dependency_manifest_v2_hash_is_pinned_against_silent_lineage_drift():
    """Pin the V2 manifest hash for the same reason the v1 hash is pinned.

    V2 was previously unpinned, which let a semantic error ship silently: the manifest
    named ``build_event_envelope_v1``, a function that does not exist. Because nothing
    asserted the hash or resolved the path, the bad name was written into the lineage
    metadata of every migrated database without any test failing.
    """
    assert historical_compatibility.DEPENDENCY_MANIFEST_V2_HASH == (
        "39b78e149ad5b703dabdbbccf4892d1ede940052b8614fbd52f0bd3e1c4b11c4"
    )
    assert compute_sha256(historical_compatibility.DEPENDENCY_MANIFEST_V2_JSON) == (
        historical_compatibility.DEPENDENCY_MANIFEST_V2_HASH
    )


def test_current_manifest_dotted_paths_resolve_to_real_attributes():
    """Every dotted path in the *current* manifest must name a symbol that exists.

    Scoped deliberately to V2 and any future current manifest. V1 is frozen legacy (see
    ``test_legacy_manifest_v1_stays_frozen_with_known_inherited_defect``) and is excluded
    on purpose, so this guard must never be widened to include it.

    Guards the class of defect where a manifest advertises a path that cannot be
    imported: unfalsifiable at runtime, yet durably recorded in database lineage
    metadata. V2 previously named ``build_event_envelope_v1``, which does not exist.
    """
    import importlib

    manifest = historical_compatibility.DEPENDENCY_MANIFEST_V2
    checked = 0
    for key, value in manifest.items():
        if not isinstance(value, str) or not value.startswith("live_contentops."):
            continue
        module_path, _, attribute = value.rpartition(".")
        module = importlib.import_module(module_path)
        assert hasattr(module, attribute), (
            f"DEPENDENCY_MANIFEST_V2[{key!r}] names {value!r}, but {attribute!r} "
            f"does not exist in {module_path}"
        )
        checked += 1
    assert checked, "expected at least one dotted path to verify"


def test_legacy_manifest_v1_stays_frozen_with_known_inherited_defect():
    """V1 is a frozen legacy compatibility artifact: recognized, not corrected.

    Databases already migrated in the field carry V1's hash in their lineage metadata, so
    its bytes, dotted-path strings, schema-version label, and pinned hash must not change.

    V1 contains an inherited defect: ``state_rules`` names
    ``durable_operational_store_v1.TRANSITION_GRAPH``, which has never existed (the real
    symbol is ``STATE_TRANSITION_GRAPH``). This predates the Wave 02 work and is recorded
    here as a frozen historical defect, explicitly *not* current runtime authority. Nothing
    resolves this string at runtime; V2 binds the real graph instead. Do not "fix" V1 and
    do not re-pin its hash -- that would invalidate already-migrated databases.
    """
    import live_contentops.durable_operational_store_v1 as durable_store

    assert historical_compatibility.DEPENDENCY_MANIFEST["state_rules"] == (
        "live_contentops.durable_operational_store_v1.TRANSITION_GRAPH"
    )
    assert not hasattr(durable_store, "TRANSITION_GRAPH"), (
        "V1 names a symbol that must remain absent; if it were added, the frozen legacy "
        "manifest would start looking authoritative"
    )
    assert hasattr(durable_store, "STATE_TRANSITION_GRAPH")
    assert historical_compatibility.DEPENDENCY_MANIFEST_HASH == (
        "6130da750b36fed3183816218717d008a74234efd12dcc92725ab25c0cc12f33"
    )


def test_manifest_v2_state_graph_binds_to_real_runtime_graph():
    """V2's inlined graph must agree with the executable graph, set-wise per state.

    V2 inlines the transition graph rather than referencing V1's non-existent symbol, so
    the two could silently drift. Comparison is order-insensitive because successor order
    carries no semantics; only membership does.
    """
    import live_contentops.durable_operational_store_v1 as durable_store

    declared = historical_compatibility.DEPENDENCY_MANIFEST_V2["state_transition_graph"]
    runtime = durable_store.STATE_TRANSITION_GRAPH

    assert set(declared) == set(runtime), "declared and runtime states must match exactly"
    for state, successors in runtime.items():
        assert set(declared[state]) == set(successors), (
            f"state {state!r}: manifest declares {sorted(set(declared[state]))} "
            f"but runtime allows {sorted(set(successors))}"
        )


@pytest.mark.parametrize(
    "originating_commit",
    (
        "e24a4492e9d72f55c704168d637b7628e49140cd",
        "3cc531a3d30848f54329d25913018882f6b71bcd",
        "33225d5e8d79ad229ad93d203e8d2e5018bb2738",
        "615a96fb20aa97fd76bb3343e9150daec40d9031",
        "03337e8f82478cf578866a5a1749d96acd687d3d",
    ),
)
def test_non_ascii_historical_payload_migrates_and_replays(tmp_path, originating_commit):
    """Non-ASCII legacy content must survive migration and remain replayable.

    Real editorial titles routinely contain em dashes and accented characters, but
    every pre-existing lineage fixture was pure ASCII, so the write/verify encoder
    split was invisible to the suite. This exercises the byte path that actually
    broke: migrate a payload containing non-ASCII, then re-verify the hash chain.

    The suffix is passed to the fixture builder rather than applied by a later
    ``UPDATE``. Titles are embedded in event payloads and covered by the event
    hash chain, so patching ``work_items`` alone would produce a database that was
    already corrupt on arrival -- the migration would then be blamed for a defect
    the test itself introduced.
    """
    title_suffix = " \u2014 caf\u00e9 r\u00e9sum\u00e9 \u00fcber \u20ac5"
    non_ascii_title = f"Historical Alpha{title_suffix}"
    db_file = tmp_path / f"historical_nonascii_{originating_commit[:7]}.sqlite"
    fixture = create_exact_historical_database(
        db_file,
        originating_commit=originating_commit,
        title_suffix=title_suffix,
    )

    # Guard the guard: if the suffix ever stops reaching the payload bytes, this test
    # would silently degrade into a duplicate of the plain ASCII migration test.
    assert not non_ascii_title.isascii()
    projected_titles = {
        projection["title"] for projection in fixture["work_item_projections"]
    }
    assert non_ascii_title in projected_titles

    store = ContentOpsDurableStore(db_file, auto_migrate=True)

    assert store.get_current_schema_version() == 4
    # A migration that fails post-commit verification quarantines the database instead
    # of upgrading it; assert no such artifacts were produced.
    assert not list(tmp_path.glob(f"{db_file.name}.recovery.*.sqlite"))
    assert not list(tmp_path.glob(f"{db_file.name}.migration_failure_*.sqlite"))

    connection = store.get_connection()
    try:
        assert connection.execute(
            "SELECT title FROM work_items WHERE work_item_id=?",
            ("wi_historical_alpha",),
        ).fetchone()[0] == non_ascii_title

        payload_rows = connection.execute(
            "SELECT event_payload_json FROM transition_events WHERE work_item_id=?",
            ("wi_historical_alpha",),
        ).fetchall()
        assert payload_rows
        saw_escaped_non_ascii = False
        for (payload_json,) in payload_rows:
            # Stored payload bytes must be the escaped ASCII form the manifest promises.
            assert payload_json.isascii()
            assert canonical_json(json.loads(payload_json)) == payload_json
            if json.loads(payload_json).get("title") == non_ascii_title:
                saw_escaped_non_ascii = True
        assert saw_escaped_non_ascii, "no migrated payload carried the non-ASCII title"
    finally:
        connection.close()

    for projection in fixture["work_item_projections"]:
        replay = store.replay_work_item_events(projection["work_item_id"])
        assert replay["verification_status"] == "PASS"
        assert replay["replayed_state"] == projection["current_state"]
        assert replay["replayed_version"] == projection["state_version"]


def test_historical_unknown_checksum_set_fails_closed_without_migration(tmp_path):
    db_file = tmp_path / "historical_unknown_checksum.sqlite"
    fixture = create_exact_historical_database(
        db_file,
        originating_commit="e24a4492e9d72f55c704168d637b7628e49140cd",
    )
    connection = sqlite3.connect(str(db_file))
    try:
        connection.execute(
            "UPDATE schema_migrations SET checksum=? WHERE version=1",
            ("f" * 64,),
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(ValueError, match="historical_schema_lineage_unknown_checksum_set"):
        ContentOpsDurableStore(db_file, auto_migrate=True)

    connection = sqlite3.connect(str(db_file))
    try:
        assert connection.execute(
            "SELECT checksum FROM schema_migrations WHERE version=1"
        ).fetchone()[0] == "f" * 64
        assert connection.execute(
            "SELECT count(*) FROM work_items"
        ).fetchone()[0] == len(fixture["work_item_projections"])
        assert connection.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_lineage_metadata'"
        ).fetchone()[0] == 0
    finally:
        connection.close()
    assert not list(tmp_path.glob(f"{db_file.name}.recovery.*.sqlite"))


def test_historical_checksum_fingerprint_mismatch_fails_closed_without_migration(tmp_path):
    db_file = tmp_path / "historical_fingerprint_mismatch.sqlite"
    create_exact_historical_database(
        db_file,
        originating_commit="e24a4492e9d72f55c704168d637b7628e49140cd",
    )
    connection = sqlite3.connect(str(db_file))
    try:
        connection.execute("ALTER TABLE metrics ADD COLUMN adversarial_column TEXT")
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(ValueError, match="historical_schema_lineage_checksum_fingerprint_mismatch"):
        ContentOpsDurableStore(db_file, auto_migrate=True)

    connection = sqlite3.connect(str(db_file))
    try:
        assert "adversarial_column" in {
            row[1] for row in connection.execute("PRAGMA table_info(metrics)").fetchall()
        }
        assert connection.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_lineage_metadata'"
        ).fetchone()[0] == 0
    finally:
        connection.close()
    assert not list(tmp_path.glob(f"{db_file.name}.recovery.*.sqlite"))


def test_historical_ambiguous_event_order_restores_source_and_retains_receipts(tmp_path):
    db_file = tmp_path / "historical_ambiguous_order.sqlite"
    create_exact_historical_database(
        db_file,
        originating_commit="e24a4492e9d72f55c704168d637b7628e49140cd",
    )
    connection = sqlite3.connect(str(db_file))
    connection.row_factory = sqlite3.Row
    try:
        source = dict(connection.execute(
            "SELECT * FROM transition_events WHERE event_id='evt_historical_alpha_v3'"
        ).fetchone())
        source["event_id"] = "evt_historical_alpha_v3_duplicate"
        source["transition_key"] = "tr_historical_alpha_v3_duplicate"
        source["state_version"] = 2
        columns = tuple(source)
        connection.execute(
            f"INSERT INTO transition_events ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
            tuple(source[column] for column in columns),
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(ValueError, match="historical_schema_lineage_ambiguous_event_order"):
        ContentOpsDurableStore(db_file, auto_migrate=True)

    recovery_paths = list(tmp_path.glob(f"{db_file.name}.recovery.*.sqlite"))
    receipt_paths = list(tmp_path.glob(f"{db_file.name}.migration_failure_*.sqlite"))
    assert len(recovery_paths) == 1
    assert len(receipt_paths) == 1
    restored_hash = compute_sha256(db_file.read_bytes())
    assert compute_sha256(recovery_paths[0].read_bytes()) == restored_hash
    connection = sqlite3.connect(str(db_file))
    try:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute(
            "SELECT count(*) FROM transition_events WHERE state_version=2"
        ).fetchone()[0] == 3
        assert connection.execute(
            "SELECT count(*) FROM transition_events WHERE event_id='evt_historical_alpha_v3_duplicate'"
        ).fetchone()[0] == 1
        assert connection.execute(
            "SELECT count(*) FROM sqlite_master WHERE type='table' AND name='schema_lineage_metadata'"
        ).fetchone()[0] == 0
    finally:
        connection.close()

    receipt = sqlite3.connect(str(receipt_paths[0]))
    receipt.row_factory = sqlite3.Row
    try:
        row = dict(receipt.execute("SELECT * FROM migration_failure_receipts").fetchone())
    finally:
        receipt.close()
    assert row["source_database_hash"] == restored_hash
    assert row["error_class"] == "ValueError"
    assert row["error_message_hash"] == compute_sha256(
        b"historical_schema_lineage_ambiguous_event_order"
    )
    assert row["restore_integrity_status"] == "PASS_SOURCE_HASH_AND_SQLITE_INTEGRITY"


def test_dependency_manifest_self_consistent_mutation_fails_integrity(temp_db):
    mutated_manifest = json.dumps(
        {"schema_version": "contentops.schema_v4_dependency_manifest.adversarial"},
        sort_keys=True,
        separators=(",", ":"),
    )
    mutated_hash = compute_sha256(mutated_manifest)
    connection = temp_db.get_connection()
    try:
        connection.execute(
            "UPDATE schema_lineage_metadata SET dependency_manifest_json=?,dependency_manifest_hash=? "
            "WHERE singleton_id=1",
            (mutated_manifest, mutated_hash),
        )
    finally:
        connection.close()

    with pytest.raises(DurableStateCorruptionError, match="Dependency manifest binding mismatch"):
        temp_db.verify_schema_integrity()


def test_migrated_unscoped_artifact_is_quarantined_from_active_genesis(tmp_path):
    db_file = tmp_path / "historical_quarantine.sqlite"
    fixture = create_exact_historical_database(
        db_file,
        originating_commit="e24a4492e9d72f55c704168d637b7628e49140cd",
    )
    store = ContentOpsDurableStore(db_file, auto_migrate=True)
    artifact = store.get_artifact(fixture["artifact_id"])
    assert artifact["artifact_scope"] == "LEGACY_UNSCOPED_QUARANTINED"

    with pytest.raises(ArtifactValidationError, match="quarantined from active use"):
        store.create_work_item(
            story_id="story_quarantine_attack",
            title="Quarantine attack",
            target_surface="substack",
            work_item_id="wi_quarantine_attack",
            input_artifact_ids=[fixture["artifact_id"]],
        )

    connection = store.get_connection()
    try:
        assert connection.execute(
            "SELECT count(*) FROM work_items WHERE work_item_id='wi_quarantine_attack'"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT count(*) FROM transition_events WHERE work_item_id='wi_quarantine_attack'"
        ).fetchone()[0] == 0
    finally:
        connection.close()


def test_work_item_exact_artifact_cannot_cross_work_item_identity(temp_db):
    temp_db.create_work_item(
        story_id="story_shared_scope",
        title="Scope owner",
        target_surface="substack",
        work_item_id="wi_scope_owner",
    )
    temp_db.register_artifact(
        artifact_id="art_work_item_exact_owner",
        artifact_type="evidence",
        storage_class="LOCAL",
        schema_version="scope.v1",
        producer_ref="scope-test",
        content_bytes=b"work-item exact evidence",
        story_id="story_shared_scope",
        work_item_id="wi_scope_owner",
        artifact_scope="WORK_ITEM_EXACT",
    )

    with pytest.raises(ArtifactValidationError, match="outside exact work-item scope"):
        temp_db.create_work_item(
            story_id="story_shared_scope",
            title="Cross work-item attack",
            target_surface="substack",
            work_item_id="wi_scope_attacker",
            input_artifact_ids=["art_work_item_exact_owner"],
        )

    connection = temp_db.get_connection()
    try:
        assert connection.execute(
            "SELECT count(*) FROM work_items WHERE work_item_id='wi_scope_attacker'"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT count(*) FROM transition_events WHERE work_item_id='wi_scope_attacker'"
        ).fetchone()[0] == 0
    finally:
        connection.close()


def test_story_exact_artifact_cannot_cross_story_identity(temp_db):
    temp_db.register_artifact(
        artifact_id="art_story_exact_owner",
        artifact_type="evidence",
        storage_class="LOCAL",
        schema_version="scope.v1",
        producer_ref="scope-test",
        content_bytes=b"story exact evidence",
        story_id="story_scope_owner",
        artifact_scope="STORY_EXACT",
    )

    with pytest.raises(ArtifactValidationError, match="outside exact story scope"):
        temp_db.create_work_item(
            story_id="story_scope_attacker",
            title="Cross story attack",
            target_surface="substack",
            work_item_id="wi_story_scope_attacker",
            input_artifact_ids=["art_story_exact_owner"],
        )

    connection = temp_db.get_connection()
    try:
        assert connection.execute(
            "SELECT count(*) FROM work_items WHERE work_item_id='wi_story_scope_attacker'"
        ).fetchone()[0] == 0
        assert connection.execute(
            "SELECT count(*) FROM transition_events WHERE work_item_id='wi_story_scope_attacker'"
        ).fetchone()[0] == 0
    finally:
        connection.close()


def test_atomic_genesis_event_and_work_item_creation(temp_db):
    item = temp_db.create_work_item(story_id="story_gen", title="Genesis Test", target_surface="substack", work_item_id="wi_gen")
    assert item["work_item_id"] == "wi_gen"
    assert item["current_state"] == "DISCOVERED"
    assert item["state_version"] == 1

    conn = temp_db.get_connection()
    try:
        events = conn.execute("SELECT * FROM transition_events WHERE work_item_id = 'wi_gen';").fetchall()
        assert len(events) == 1
        genesis = events[0]
        assert genesis["event_seq"] == 1
        assert genesis["reason_code"] == "WORK_ITEM_INITIALIZATION"
        assert genesis["previous_event_hash"] == GENESIS_PREVIOUS_HASH
        assert genesis["from_state"] == "DISCOVERED"
        assert genesis["to_state"] == "DISCOVERED"
    finally:
        conn.close()


def test_projection_without_genesis_fails(temp_db):
    conn = temp_db.get_connection()
    try:
        conn.execute(
            "INSERT INTO work_items (work_item_id, story_id, title, current_state, state_version, target_surface, created_at, updated_at) "
            "VALUES ('wi_nogen', 'story_nogen', 'No Gen', 'DISCOVERED', 1, 'substack', 'now', 'now');"
        )
    finally:
        conn.close()

    with pytest.raises(DurableStateCorruptionError, match="has no transition events|missing valid genesis event"):
        temp_db.replay_work_item_events("wi_nogen")


def test_artifact_registration_derived_from_bytes_or_verified_receipt(temp_db):
    payload = b"Sample input artifact content for test"
    length = len(payload)
    sha256 = compute_sha256(payload)

    art = temp_db.register_artifact(
        artifact_id="art_101",
        artifact_type="raw_headline_packet",
        storage_class="local_file",
        schema_version="contentops.artifact.v1",
        producer_ref="unit_test_producer",
        content_bytes=payload,
        story_id="story_101",
    )
    assert art["artifact_id"] == "art_101"
    assert art["sha256_hash"] == sha256
    assert art["byte_length"] == length

    with pytest.raises(ArtifactValidationError):
        temp_db.register_artifact(
            artifact_id="art_bad",
            artifact_type="raw_headline_packet",
            storage_class="local_file",
            schema_version="contentops.artifact.v1",
            producer_ref="unit_test_producer",
        )


def test_artifact_update_and_delete_triggers_reject_direct_modification(temp_db):
    temp_db.register_artifact(
        artifact_id="art_trig",
        artifact_type="claim",
        storage_class="memory",
        schema_version="v1",
        producer_ref="test",
        content_bytes=b"test bytes",
    )

    conn = temp_db.get_connection()
    try:
        with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError), match="artifact_references are immutable"):
            conn.execute("UPDATE artifact_references SET storage_class = 'hacked' WHERE artifact_id = 'art_trig';")

        with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError), match="artifact_references are immutable"):
            conn.execute("DELETE FROM artifact_references WHERE artifact_id = 'art_trig';")
    finally:
        conn.close()


def test_complete_event_payload_hash_verification(temp_db):
    temp_db.create_work_item(story_id="story_hash", title="Hash Envelope Test", target_surface="x", work_item_id="wi_hash")
    art = temp_db.register_artifact(
        artifact_id="art_hash_1",
        artifact_type="claim",
        storage_class="memory",
        schema_version="v1",
        producer_ref="test",
        content_bytes=b"input bytes",
        story_id="story_hash",
        work_item_id="wi_hash",
    )

    claim = temp_db.claim_work_item(lease_key="key_hash", work_item_id="wi_hash", owner_ref="worker_hash", ttl_seconds=10)

    t1 = temp_db.transition_state(
        work_item_id="wi_hash",
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="Worker",
        actor_ref="worker_hash",
        reason_code="STEP_1",
        explanation="Step 1 transition",
        lease_key="key_hash",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_hash_1"],
        output_artifact_ids=[],
        correlation_id="corr_1",
    )

    replay = temp_db.replay_work_item_events("wi_hash")
    assert replay["verification_status"] == "PASS"


def _forged_event_insert(
    store,
    *,
    work_item_id,
    event_seq,
    from_state,
    to_state,
    state_version=None,
    previous_event_hash=None,
    reason_code="FORGED_DIRECT_INSERT",
):
    item = store.get_work_item(work_item_id)
    if previous_event_hash is None:
        connection = store.get_connection()
        try:
            previous_event_hash = connection.execute(
                "SELECT event_hash FROM transition_events WHERE work_item_id=? ORDER BY event_seq DESC LIMIT 1",
                (work_item_id,),
            ).fetchone()[0]
        finally:
            connection.close()
    version = event_seq if state_version is None else state_version
    explanation = f"Forged direct event {event_seq}: {from_state} to {to_state}"
    envelope = build_event_envelope(
        event_schema_version="contentops.event_payload.v1",
        event_kind="STATE_TRANSITION",
        event_seq=event_seq,
        work_item_id=work_item_id,
        story_id=item["story_id"],
        title=item["title"],
        target_surface=item["target_surface"],
        state_version=version,
        from_state=from_state,
        to_state=to_state,
        previous_event_hash=previous_event_hash,
        actor_class="ExternalSQLiteOwner",
        actor_ref="direct-write-adversary",
        reason_code=reason_code,
        explanation_hash=compute_sha256(explanation),
        correlation_id=f"corr_direct_{work_item_id}_{event_seq}",
        policy_version="contentops.policy.v1",
        model_version="NOT_APPLICABLE",
        authority_type="NONE",
        authority_ref=None,
        authority_effect="NO_AUTHORITY_GRANTED",
        lease_id=None,
        lease_key=None,
        fencing_token=0,
        input_artifact_ids=[],
        output_artifact_ids=[],
        artifact_snapshots=[],
        timestamp_utc=store._get_now_iso(),
    )
    payload = canonical_json(envelope)
    event_hash = compute_sha256(payload)
    columns = (
        "event_id", "transition_key", "work_item_id", "event_kind", "event_seq",
        "from_state", "to_state", "state_version", "actor_class", "actor_ref",
        "reason_code", "explanation", "explanation_hash", "correlation_id", "policy_version",
        "model_version", "authority_type", "authority_ref", "authority_effect", "lease_id",
        "lease_key", "fencing_token", "input_artifact_ids", "output_artifact_ids",
        "artifact_snapshot_json", "previous_event_hash", "event_payload_json", "event_hash",
        "timestamp_utc",
    )
    values = (
        f"evt_direct_{work_item_id}_{event_seq}_{event_hash[:8]}",
        f"tr_direct_{work_item_id}_{event_seq}_{event_hash[:8]}",
        work_item_id, "STATE_TRANSITION", event_seq, from_state, to_state, version,
        "ExternalSQLiteOwner", "direct-write-adversary", reason_code, explanation,
        compute_sha256(explanation), f"corr_direct_{work_item_id}_{event_seq}",
        "contentops.policy.v1", "NOT_APPLICABLE", "NONE", None, "NO_AUTHORITY_GRANTED",
        None, None, 0, "[]", "[]", "[]", previous_event_hash, payload, event_hash,
        envelope["timestamp_utc"],
    )
    statement = (
        f"INSERT INTO transition_events ({','.join(columns)}) "
        f"VALUES ({','.join('?' for _ in columns)})"
    )
    return statement, values, event_hash


def test_direct_insert_application_boundary_rejects_external_and_store_connections(temp_db):
    temp_db.create_work_item(
        story_id="story_direct_boundary",
        title="Direct boundary",
        target_surface="substack",
        work_item_id="wi_direct_boundary",
    )
    statement, values, _ = _forged_event_insert(
        temp_db,
        work_item_id="wi_direct_boundary",
        event_seq=2,
        from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
    )

    external = sqlite3.connect(str(temp_db.db_path))
    try:
        with pytest.raises(sqlite3.OperationalError, match="no such function: contentops_append_authorized"):
            external.execute(statement, values)
    finally:
        external.close()

    owned = temp_db.get_connection()
    try:
        with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
            owned.execute(statement, values)
        owned.create_function("contentops_append_authorized", 0, lambda: 1)
        with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
            owned.execute(statement, values)
    finally:
        owned.close()

    assert temp_db.replay_work_item_events("wi_direct_boundary") == {
        "work_item_id": "wi_direct_boundary",
        "replayed_state": "DISCOVERED",
        "replayed_version": 1,
        "event_count": 1,
        "last_event_hash": temp_db.get_connection().execute(
            "SELECT event_hash FROM transition_events WHERE work_item_id='wi_direct_boundary'"
        ).fetchone()[0],
        "verification_status": "PASS",
    }


def test_direct_artifact_insert_requires_canonical_registration(temp_db):
    values = (
        "art_direct_attack", "evidence", None, None, "LOCAL", 6,
        compute_sha256(b"attack"), "scope.v1", temp_db._get_now_iso(), "adversary",
        "PUBLIC", "GLOBAL_REUSABLE", None, None, None, None, None, None,
    )
    statement = (
        "INSERT INTO artifact_references "
        "(artifact_id,artifact_type,story_id,work_item_id,storage_class,byte_length,sha256_hash,"
        "schema_version,created_at,producer_ref,sensitivity_class,artifact_scope,receipt_id,"
        "receipt_schema,receipt_source_identity,receipt_object_identity,receipt_verifier_identity,"
        "canonical_receipt_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
    )
    external = sqlite3.connect(str(temp_db.db_path))
    try:
        with pytest.raises(sqlite3.OperationalError, match="no such function: contentops_artifact_insert_authorized"):
            external.execute(statement, values)
    finally:
        external.close()
    owned = temp_db.get_connection()
    try:
        with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
            owned.execute(statement, values)
    finally:
        owned.close()


def test_external_spoofed_udf_illegal_edge_is_detected_by_replay(temp_db):
    temp_db.create_work_item(
        story_id="story_spoof_edge", title="Spoof edge", target_surface="substack",
        work_item_id="wi_spoof_edge",
    )
    statement, values, _ = _forged_event_insert(
        temp_db,
        work_item_id="wi_spoof_edge",
        event_seq=2,
        from_state="DISCOVERED",
        to_state="REVIEW_READY",
    )
    external = sqlite3.connect(str(temp_db.db_path))
    try:
        external.create_function("contentops_append_authorized", 0, lambda: 1)
        external.execute(statement, values)
        external.commit()
    finally:
        external.close()
    with pytest.raises(DurableStateCorruptionError, match="Illegal event state edge"):
        temp_db.replay_work_item_events("wi_spoof_edge")


def test_external_spoofed_udf_state_version_mismatch_is_detected_by_replay(temp_db):
    temp_db.create_work_item(
        story_id="story_spoof_version", title="Spoof version", target_surface="substack",
        work_item_id="wi_spoof_version",
    )
    statement, values, _ = _forged_event_insert(
        temp_db,
        work_item_id="wi_spoof_version",
        event_seq=2,
        state_version=7,
        from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
    )
    external = sqlite3.connect(str(temp_db.db_path))
    try:
        external.create_function("contentops_append_authorized", 0, lambda: 1)
        external.execute(statement, values)
        external.commit()
    finally:
        external.close()
    with pytest.raises(DurableStateCorruptionError, match="Event sequence/state-version mismatch"):
        temp_db.replay_work_item_events("wi_spoof_version")


def test_external_spoofed_udf_protected_state_is_detected_by_replay(temp_db):
    temp_db.create_work_item(
        story_id="story_spoof_protected", title="Spoof protected", target_surface="substack",
        work_item_id="wi_spoof_protected",
    )
    edges = (
        ("DISCOVERED", "EVIDENCE_PENDING"),
        ("EVIDENCE_PENDING", "EVIDENCE_READY"),
        ("EVIDENCE_READY", "ASSIGNMENT_CANDIDATE"),
        ("ASSIGNMENT_CANDIDATE", "ASSIGNED"),
        ("ASSIGNED", "PRODUCTION_IN_PROGRESS"),
        ("PRODUCTION_IN_PROGRESS", "REVIEW_READY"),
        ("REVIEW_READY", "OPERATOR_PENDING"),
        ("OPERATOR_PENDING", "APPROVED_EXACT"),
    )
    connection = temp_db.get_connection()
    try:
        previous_hash = connection.execute(
            "SELECT event_hash FROM transition_events WHERE work_item_id='wi_spoof_protected'"
        ).fetchone()[0]
    finally:
        connection.close()
    external = sqlite3.connect(str(temp_db.db_path))
    try:
        external.create_function("contentops_append_authorized", 0, lambda: 1)
        for event_seq, (from_state, to_state) in enumerate(edges, 2):
            statement, values, previous_hash = _forged_event_insert(
                temp_db,
                work_item_id="wi_spoof_protected",
                event_seq=event_seq,
                from_state=from_state,
                to_state=to_state,
                previous_event_hash=previous_hash,
            )
            external.execute(statement, values)
        external.commit()
    finally:
        external.close()
    with pytest.raises(DurableStateCorruptionError, match="Protected authority state event"):
        temp_db.replay_work_item_events("wi_spoof_protected")


def test_unauthorized_direct_event_insertion_and_update_rejection(temp_db):
    temp_db.create_work_item(story_id="story_tamper", title="Tamper Test", target_surface="x", work_item_id="wi_tamper")
    art = temp_db.register_artifact(
        artifact_id="art_tamper_1",
        artifact_type="claim",
        storage_class="memory",
        schema_version="v1",
        producer_ref="test",
        content_bytes=b"tamper bytes",
        story_id="story_tamper",
        work_item_id="wi_tamper",
    )
    claim = temp_db.claim_work_item(lease_key="key_tamper", work_item_id="wi_tamper", owner_ref="worker_tamper", ttl_seconds=10)

    temp_db.transition_state(
        work_item_id="wi_tamper",
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="Worker",
        actor_ref="worker_tamper",
        reason_code="STEP_1",
        explanation="Step 1 transition",
        lease_key="key_tamper",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_tamper_1"],
        output_artifact_ids=[],
        correlation_id="corr_1",
    )

    conn = temp_db.get_connection()
    try:
        with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError), match="transition_events are append-only"):
            conn.execute(
                "UPDATE transition_events SET reason_code = 'HACKED' WHERE work_item_id = 'wi_tamper' AND event_seq = 2;"
            )
        with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError), match="transition_events are append-only"):
            conn.execute(
                "DELETE FROM transition_events WHERE work_item_id = 'wi_tamper' AND event_seq = 2;"
            )
    finally:
        conn.close()


def test_concurrent_claims_only_one_winner(temp_db):
    temp_db.create_work_item(story_id="story_conc", title="Concurrent Test", target_surface="x", work_item_id="wi_conc")

    results = []

    def attempt_claim(worker_name):
        try:
            res = temp_db.claim_work_item(lease_key="key_conc", work_item_id="wi_conc", owner_ref=worker_name, ttl_seconds=5)
            results.append((worker_name, res))
        except Exception as exc:
            results.append((worker_name, exc))

    t1 = threading.Thread(target=attempt_claim, args=("Worker_1",))
    t2 = threading.Thread(target=attempt_claim, args=("Worker_2",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    successes = [r for r in results if isinstance(r[1], dict)]
    failures = [r for r in results if isinstance(r[1], Exception)]
    assert len(successes) == 1
    assert len(failures) == 1
    assert isinstance(failures[0][1], LeaseConflictError)


def test_lease_expiry_and_stale_fencing_token_rejection(temp_db):
    temp_db.create_work_item(story_id="story_fence", title="Fencing Test", target_surface="substack", work_item_id="wi_fence")
    art = temp_db.register_artifact(
        artifact_id="art_in_1",
        artifact_type="input_claim",
        storage_class="memory",
        schema_version="v1",
        producer_ref="test",
        content_bytes=b"fence bytes",
        story_id="story_fence",
        work_item_id="wi_fence",
    )

    claim_A = temp_db.claim_work_item(lease_key="key_fence", work_item_id="wi_fence", owner_ref="worker_A", ttl_seconds=1)
    assert claim_A["fencing_token"] == 1

    temp_db.release_lease(claim_A["lease_id"], "worker_A", 1)

    claim_B = temp_db.claim_work_item(lease_key="key_fence", work_item_id="wi_fence", owner_ref="worker_B", ttl_seconds=10)
    assert claim_B["fencing_token"] == 2

    with pytest.raises(StaleFencingTokenError):
        temp_db.transition_state(
            work_item_id="wi_fence",
            expected_from_state="DISCOVERED",
            to_state="EVIDENCE_PENDING",
            expected_state_version=1,
            actor_class="WorkerA",
            actor_ref="worker_A",
            reason_code="STALE_TRY",
            explanation="Stale worker A transition",
            lease_key="key_fence",
            fencing_token=1,
            input_artifact_ids=["art_in_1"],
            output_artifact_ids=[],
            correlation_id="corr_A",
        )

    trans_B = temp_db.transition_state(
        work_item_id="wi_fence",
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="WorkerB",
        actor_ref="worker_B",
        reason_code="VALID_TRY",
        explanation="Valid worker B transition",
        lease_key="key_fence",
        fencing_token=2,
        input_artifact_ids=["art_in_1"],
        output_artifact_ids=[],
        correlation_id="corr_B",
    )
    assert trans_B["current_state"] == "EVIDENCE_PENDING"


def test_heartbeat_freshness_and_stale_disposition(temp_db):
    lease = temp_db.acquire_lease("l_hb", "worker_live", 60)
    temp_db.upsert_heartbeat(worker_id="worker_live", lease_id=lease["lease_id"])
    fresh = temp_db.query_fresh_heartbeats(ttl_seconds=60)
    assert len(fresh) == 1
    assert fresh[0]["worker_id"] == "worker_live"

    conn = temp_db.get_connection()
    try:
        conn.execute("UPDATE heartbeats SET last_seen_at = '2000-01-01T00:00:00+00:00' WHERE worker_id = 'worker_live';")
    finally:
        conn.close()

    stale = temp_db.dispose_stale_heartbeats(ttl_seconds=60)
    assert "worker_live" in stale

    fresh_after = temp_db.query_fresh_heartbeats(ttl_seconds=60)
    assert len(fresh_after) == 0


def test_wave02_authority_fail_closed_guard(temp_db):
    temp_db.create_work_item(story_id="story_auth", title="Auth Guard Test", target_surface="substack", work_item_id="wi_auth")
    art = temp_db.register_artifact(
        artifact_id="art_auth_1",
        artifact_type="claim",
        storage_class="memory",
        schema_version="v1",
        producer_ref="test",
        content_bytes=b"auth bytes",
        story_id="story_auth",
        work_item_id="wi_auth",
    )
    claim = temp_db.claim_work_item(lease_key="key_auth", work_item_id="wi_auth", owner_ref="worker_auth", ttl_seconds=10)

    states = ["EVIDENCE_PENDING", "EVIDENCE_READY", "ASSIGNMENT_CANDIDATE", "ASSIGNED", "PRODUCTION_IN_PROGRESS", "REVIEW_READY", "OPERATOR_PENDING"]
    current_state = "DISCOVERED"
    version = 1

    for next_st in states:
        temp_db.transition_state(
            work_item_id="wi_auth",
            expected_from_state=current_state,
            to_state=next_st,
            expected_state_version=version,
            actor_class="Worker",
            actor_ref="worker_auth",
            reason_code="REASON",
            explanation="test",
            lease_key="key_auth",
            fencing_token=claim["fencing_token"],
            input_artifact_ids=["art_auth_1"],
            output_artifact_ids=[],
            correlation_id="corr",
        )
        current_state = next_st
        version += 1

    with pytest.raises(Wave02AuthorityViolationError):
        temp_db.transition_state(
            work_item_id="wi_auth",
            expected_from_state="OPERATOR_PENDING",
            to_state="APPROVED_EXACT",
            expected_state_version=version,
            actor_class="Worker",
            actor_ref="worker_auth",
            reason_code="APPROVE",
            explanation="test",
            lease_key="key_auth",
            fencing_token=claim["fencing_token"],
            input_artifact_ids=["art_auth_1"],
            output_artifact_ids=[],
            correlation_id="corr",
        )


def test_adversarial_redacted_evidence_export(temp_db):
    temp_db.create_work_item(story_id="story_secret", title="Secret Story Title", target_surface="substack", work_item_id="wi_secret")
    temp_db.register_artifact(
        artifact_id="art_secret_1",
        artifact_type="secret_claim",
        storage_class="memory",
        schema_version="v1",
        producer_ref="test",
        content_bytes=b"secret bytes",
        story_id="story_secret",
        work_item_id="wi_secret",
    )
    claim = temp_db.claim_work_item(lease_key="key_secret", work_item_id="wi_secret", owner_ref="secret_agent_007", ttl_seconds=10)

    temp_db.transition_state(
        work_item_id="wi_secret",
        expected_from_state="DISCOVERED",
        to_state="EVIDENCE_PENDING",
        expected_state_version=1,
        actor_class="Worker",
        actor_ref="secret_agent_007",
        reason_code="REASON_SECRET",
        explanation="Secret explanation containing password=my_secret_password and bearer_token=abc123xyz",
        lease_key="key_secret",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_secret_1"],
        output_artifact_ids=[],
        correlation_id="corr_secret",
    )

    export1 = temp_db.export_redacted_store_evidence()
    export2 = temp_db.export_redacted_store_evidence()
    assert json.dumps(export1, sort_keys=True) == json.dumps(export2, sort_keys=True)

    export_json = json.dumps(export1)
    assert "my_secret_password" not in export_json
    assert "abc123xyz" not in export_json
    assert "secret_agent_007" not in export_json
    assert "Secret Story Title" not in export_json


def test_orchestrator_store_integration_with_durable_context(temp_db, tmp_path):
    orchestrator = ContentOpsProductionOrchestrator(store=temp_db)

    with pytest.raises(ValueError, match="durable_context_required_when_store_active"):
        orchestrator.execute("prepare_text_image_release_candidate", run_id="test_run_101", output_dir=tmp_path)

    temp_db.create_work_item(story_id="treasury_20260714", title="Orchestrator Story", target_surface="eight_platform_all", work_item_id="wi_orch_101")
    art = temp_db.register_artifact(
        artifact_id="art_orch_1",
        artifact_type="rc_input",
        storage_class="local_file",
        schema_version="v1",
        producer_ref="test_orch",
        content_bytes=b"orch input bytes",
        story_id="treasury_20260714",
        work_item_id="wi_orch_101",
    )

    claim = temp_db.claim_work_item(lease_key="key_orch", work_item_id="wi_orch_101", owner_ref="orch_worker", ttl_seconds=10)

    ctx = ContentOpsDurableContext(
        story_id="treasury_20260714",
        work_item_id="wi_orch_101",
        title="Orchestrator Story",
        correlation_id="corr_orch_101",
        actor_ref="orch_worker",
        lease_key="key_orch",
        fencing_token=claim["fencing_token"],
        input_artifact_ids=["art_orch_1"],
    )

    orchestrator._dispatcher = lambda operation, **kwargs: {
        "outputs": [
            {"name": "release.json", "output_form": "STRUCTURED_JSON", "value": {"operation": operation, "run_id": kwargs["run_id"]}},
            {"name": "release.txt", "output_form": "UTF8_TEXT", "value": "local durable release"},
        ]
    }
    result = orchestrator.execute(
        "prepare_text_image_release_candidate",
        run_id="test_run_101",
        output_dir=tmp_path,
        durable_context=ctx,
    )
    assert len(result["outputs"]) == 2
    assert temp_db.get_work_item("wi_orch_101")["current_state"] == "EVIDENCE_READY"
    replay = temp_db.replay_work_item_events("wi_orch_101")
    assert replay["verification_status"] == "PASS"
    with temp_db.get_connection() as conn:
        output_ids = json.loads(conn.execute(
            "SELECT output_artifact_ids FROM transition_events WHERE work_item_id=? ORDER BY event_seq DESC LIMIT 1",
            ("wi_orch_101",),
        ).fetchone()[0])
    assert len(output_ids) == 3
    assert any(temp_db.get_artifact(artifact_id)["artifact_type"] == "OPERATION_OUTPUT_MANIFEST" for artifact_id in output_ids)


def _orchestrator_context_and_claim(store, *, suffix):
    work_item_id = f"wi_orch_{suffix}"
    story_id = f"story_orch_{suffix}"
    actor = f"worker_{suffix}"
    lease_key = f"lease_key_{suffix}"
    store.create_work_item(story_id=story_id, title=f"Story {suffix}", target_surface="eight_platform_all", work_item_id=work_item_id)
    claim = store.claim_work_item(lease_key=lease_key, work_item_id=work_item_id, owner_ref=actor, ttl_seconds=30)
    return ContentOpsDurableContext(
        story_id=story_id, work_item_id=work_item_id, title=f"Story {suffix}", correlation_id=f"corr_{suffix}",
        actor_ref=actor, lease_key=lease_key, fencing_token=claim["fencing_token"],
    )


def test_orchestrator_contract_registry_covers_every_operation():
    assert set(OPERATION_CONTRACTS) == set(CANONICAL_OPERATIONS)
    assert OPERATION_CONTRACTS["prepare_text_image_release_candidate"].restart_mode == RESTART_SAFE
    assert OPERATION_CONTRACTS["module_cli"].durable_supported is False


def test_orchestrator_missing_output_blocks_truthfully(temp_db):
    ctx = _orchestrator_context_and_claim(temp_db, suffix="missing_output")
    orchestrator = ContentOpsProductionOrchestrator(store=temp_db)
    orchestrator._dispatcher = lambda operation, **kwargs: None
    with pytest.raises(OperationLifecycleError, match="operation_output_required"):
        orchestrator.execute("prepare_text_image_release_candidate", durable_context=ctx)
    assert temp_db.get_work_item(ctx.work_item_id)["current_state"] == "EVIDENCE_BLOCKED"
    assert temp_db.replay_work_item_events(ctx.work_item_id)["verification_status"] == "PASS"
    with temp_db.get_connection() as conn:
        blocked = conn.execute(
            "SELECT reason_code,explanation FROM transition_events WHERE work_item_id=? ORDER BY event_seq DESC LIMIT 1",
            (ctx.work_item_id,),
        ).fetchone()
    assert blocked["reason_code"] == "ORCHESTRATOR_OUTPUT_CONTRACT_BLOCKED"
    assert "operation_output_required" in blocked["explanation"]


def test_orchestrator_dispatcher_failure_preserves_original_exception(temp_db):
    ctx = _orchestrator_context_and_claim(temp_db, suffix="dispatcher_failure")
    orchestrator = ContentOpsProductionOrchestrator(store=temp_db)
    expected = RuntimeError("local stub failure must remain original")

    def fail(operation, **kwargs):
        raise expected

    orchestrator._dispatcher = fail
    with pytest.raises(RuntimeError) as caught:
        orchestrator.execute("prepare_text_image_release_candidate", durable_context=ctx)
    assert caught.value is expected
    assert temp_db.get_work_item(ctx.work_item_id)["current_state"] == "EVIDENCE_BLOCKED"


def test_orchestrator_output_identity_is_exact_work_item_scoped(temp_db):
    contexts = [
        _orchestrator_context_and_claim(temp_db, suffix="scoped_output_a"),
        _orchestrator_context_and_claim(temp_db, suffix="scoped_output_b"),
    ]
    identical_result = {
        "outputs": [
            {"name": "release.json", "output_form": "STRUCTURED_JSON", "value": {"status": "ready"}},
            {"name": "release.txt", "output_form": "UTF8_TEXT", "value": "identical bytes"},
        ]
    }
    output_sets = []
    for context in contexts:
        orchestrator = ContentOpsProductionOrchestrator(store=temp_db)
        orchestrator._dispatcher = lambda operation, **kwargs: identical_result
        assert orchestrator.execute(
            "prepare_text_image_release_candidate", durable_context=context
        ) == identical_result
        with temp_db.get_connection() as connection:
            output_ids = json.loads(connection.execute(
                "SELECT output_artifact_ids FROM transition_events WHERE work_item_id=? ORDER BY event_seq DESC LIMIT 1",
                (context.work_item_id,),
            ).fetchone()[0])
        assert len(output_ids) == 3
        for artifact_id in output_ids:
            artifact = temp_db.get_artifact(artifact_id)
            assert artifact["artifact_scope"] == "WORK_ITEM_EXACT"
            assert artifact["story_id"] == context.story_id
            assert artifact["work_item_id"] == context.work_item_id
        output_sets.append(set(output_ids))
    assert output_sets[0].isdisjoint(output_sets[1])
    assert all(temp_db.replay_work_item_events(context.work_item_id)["verification_status"] == "PASS" for context in contexts)


def test_orchestrator_composite_failure_preserves_operation_and_persistence_errors(temp_db):
    context = _orchestrator_context_and_claim(temp_db, suffix="composite_failure")
    orchestrator = ContentOpsProductionOrchestrator(store=temp_db)
    operation_error = RuntimeError("dispatcher failed before durable receipt")
    persistence_error = RuntimeError("blocked-state persistence failed")

    def fail_dispatch(operation, **kwargs):
        raise operation_error

    original_transition = temp_db.transition_state

    def fail_only_blocked_transition(**kwargs):
        if kwargs.get("to_state") == "EVIDENCE_BLOCKED":
            raise persistence_error
        return original_transition(**kwargs)

    orchestrator._dispatcher = fail_dispatch
    temp_db.transition_state = fail_only_blocked_transition
    with pytest.raises(OperationFailurePersistenceError) as caught:
        orchestrator.execute("prepare_text_image_release_candidate", durable_context=context)
    assert caught.value.operation_error is operation_error
    assert caught.value.persistence_error is persistence_error
    assert caught.value.restart_disposition == "RESUME_RESTART_SAFE"
    assert caught.value.__cause__ is operation_error
    assert temp_db.get_work_item(context.work_item_id)["current_state"] == "EVIDENCE_PENDING"
    assert temp_db.replay_work_item_events(context.work_item_id)["verification_status"] == "PASS"


def test_orchestrator_pending_restart_requires_explicit_decision(temp_db):
    ctx = _orchestrator_context_and_claim(temp_db, suffix="restart")
    temp_db.transition_state(
        work_item_id=ctx.work_item_id, expected_from_state="DISCOVERED", to_state="EVIDENCE_PENDING", expected_state_version=1,
        actor_class="ContentOpsProductionOrchestrator", actor_ref=ctx.actor_ref, reason_code="LOCAL_PENDING_FIXTURE",
        explanation="Create an explicit restart fixture", lease_key=ctx.lease_key, fencing_token=ctx.fencing_token,
        input_artifact_ids=[], output_artifact_ids=[], correlation_id=ctx.correlation_id,
    )
    orchestrator = ContentOpsProductionOrchestrator(store=temp_db)
    orchestrator._dispatcher = lambda operation, **kwargs: b"restart-safe-output"
    with pytest.raises(ValueError, match="explicit_resume_decision_required:RESUME_RESTART_SAFE"):
        orchestrator.execute("prepare_text_image_release_candidate", durable_context=ctx)
    assert temp_db.get_work_item(ctx.work_item_id)["current_state"] == "EVIDENCE_PENDING"
    ctx.attempt_decision = "RESUME_RESTART_SAFE"
    assert orchestrator.execute("prepare_text_image_release_candidate", durable_context=ctx) == b"restart-safe-output"
    assert temp_db.get_work_item(ctx.work_item_id)["current_state"] == "EVIDENCE_READY"


def test_orchestrator_rejects_nondeterministic_structured_output(temp_db):
    ctx = _orchestrator_context_and_claim(temp_db, suffix="unsupported")
    orchestrator = ContentOpsProductionOrchestrator(store=temp_db)
    orchestrator._dispatcher = lambda operation, **kwargs: {"unsupported": object()}
    with pytest.raises(OperationLifecycleError, match="operation_output_unsupported_json_type:object"):
        orchestrator.execute("prepare_text_image_release_candidate", durable_context=ctx)
    assert temp_db.get_work_item(ctx.work_item_id)["current_state"] == "EVIDENCE_BLOCKED"


def test_orchestrator_context_mismatch_rejection(temp_db):
    orchestrator = ContentOpsProductionOrchestrator(store=temp_db)
    temp_db.create_work_item(story_id="story_real", title="Real Title", target_surface="eight_platform_all", work_item_id="wi_mismatch")
    claim = temp_db.claim_work_item(lease_key="key_mis", work_item_id="wi_mismatch", owner_ref="w_mis", ttl_seconds=10)

    ctx_bad = ContentOpsDurableContext(
        story_id="wrong_story",
        work_item_id="wi_mismatch",
        title="Real Title",
        correlation_id="corr_mis",
        actor_ref="w_mis",
        lease_key="key_mis",
        fencing_token=claim["fencing_token"],
    )

    with pytest.raises(ValueError, match="story_id_mismatch"):
        orchestrator.execute("prepare_text_image_release_candidate", durable_context=ctx_bad)


def test_gitignore_database_family_patterns():
    gitignore_path = pathlib.Path(__file__).resolve().parent.parent / ".gitignore"
    text = gitignore_path.read_text(encoding="utf-8")
    assert "*.sqlite" in text
    assert "*.db" in text


def test_lossless_migration_v1_v2_v3_preserves_all_rows(tmp_path):
    db_file = tmp_path / "legacy_test.sqlite"
    store = ContentOpsDurableStore(db_file, auto_migrate=False)
    assert store.run_migrations(target_version=1) == 1

    conn = sqlite3.connect(str(db_file))
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("INSERT INTO work_items VALUES ('wi_legacy', 'story_legacy', 'Legacy Title', 'DISCOVERED', 1, 'eight_platform_all', '2026-08-01T00:00:00Z', '2026-08-01T00:00:00Z');")
        conn.execute(
            "INSERT INTO transition_events (event_id, transition_key, work_item_id, from_state, to_state, state_version, actor_class, actor_ref, reason_code, explanation, artifact_hash_set, correlation_id, timestamp_utc, authority_granted) "
            "VALUES ('evt_legacy_1', 'tr_legacy_1', 'wi_legacy', 'DISCOVERED', 'DISCOVERED', 1, 'LegacyActor', 'legacy_ref', 'WORK_ITEM_INITIALIZATION', 'Legacy explanation', '[]', 'corr_leg', '2026-08-01T00:00:00Z', 0);"
        )
        conn.execute("COMMIT")
    finally:
        conn.close()

    assert store.run_migrations(target_version=2) == 1
    assert store.get_current_schema_version() == 2
    assert store.run_migrations() == 7
    assert store.get_current_schema_version() == 9
    assert store.verify_schema_integrity() is True
    assert [proof["status"] for proof in store.migration_proofs] == [
        "PASS_LOSSLESS_MIGRATION",
        "PASS_LOSSLESS_MIGRATION",
        "PASS_LOSSLESS_MIGRATION",
        "PASS_LOSSLESS_MIGRATION",
        "PASS_LOSSLESS_MIGRATION",
        "PASS_LOSSLESS_MIGRATION",
        "PASS_LOSSLESS_MIGRATION",
        "PASS_LOSSLESS_MIGRATION",
        "PASS_LOSSLESS_MIGRATION",
    ]

    replayed = store.replay_work_item_events("wi_legacy")
    assert replayed["verification_status"] == "PASS"
    assert replayed["event_count"] == 1


def test_fake_clock_lease_expiry_and_reclaim(tmp_path):
    from datetime import datetime, timezone, timedelta
    curr_time = [datetime(2026, 8, 4, 12, 0, 0, tzinfo=timezone.utc)]
    def fake_now():
        return curr_time[0]

    db_file = tmp_path / "fake_clock_test.sqlite"
    store = ContentOpsDurableStore(db_file, now_fn=fake_now)
    store.create_work_item(story_id="s1", title="Title 1", target_surface="surf1", work_item_id="wi_clock_1")

    lease1 = store.claim_work_item(lease_key="key_clock", work_item_id="wi_clock_1", owner_ref="worker_1", ttl_seconds=30)
    assert lease1["status"] == "ACTIVE"

    curr_time[0] += timedelta(seconds=60)

    stale_ids = store.recover_stale_leases()
    assert lease1["lease_id"] in stale_ids

    lease2 = store.claim_work_item(lease_key="key_clock", work_item_id="wi_clock_1", owner_ref="worker_2", ttl_seconds=30)
    assert lease2["owner_ref"] == "worker_2"
    assert lease2["fencing_token"] == lease1["fencing_token"] + 1


def test_event_column_payload_mismatch_rejection(temp_db):
    temp_db.create_work_item(story_id="s_tamper", title="Tamper Title", target_surface="surf", work_item_id="wi_tamper")
    conn = temp_db.get_connection()
    conn.execute("DROP TRIGGER trg_transition_events_no_update;")
    conn.execute("UPDATE transition_events SET state_version = 99 WHERE work_item_id = 'wi_tamper';")
    conn.execute("""
    CREATE TRIGGER trg_transition_events_no_update
    BEFORE UPDATE ON transition_events
    BEGIN
        SELECT RAISE(ABORT, 'transition_events are append-only: UPDATE forbidden');
    END;
    """)
    conn.close()

    with pytest.raises(DurableStateCorruptionError, match="column mismatch"):
        temp_db.replay_work_item_events("wi_tamper")


def test_artifact_verified_receipt_contract_validation(temp_db):
    payload = b"independently resolved immutable receipt payload"
    digest = compute_sha256(payload)
    receipt = {
        "schema_version": "contentops.artifact_receipt.v1",
        "receipt_id": "rcpt_1001",
        "source_identity": "repo_origin",
        "object_identity": "path/to/blob.bin",
        "sha256_hash": digest,
        "blob_hash": digest,
        "byte_length": len(payload),
        "verifier_ref": "unit_test_verifier",
    }

    def resolve_unit_test_receipt(candidate):
        return {
            "content_bytes": payload,
            "source_identity": candidate["source_identity"],
            "object_identity": candidate["object_identity"],
            "object_hash": digest,
            "immutable": True,
        }

    temp_db.register_receipt_resolver("unit_test_verifier", resolve_unit_test_receipt)
    art = temp_db.register_artifact(
        artifact_id="art_rcpt_1",
        artifact_type="receipt_type",
        storage_class="LOCAL",
        schema_version="v1",
        producer_ref="producer_1",
        verified_receipt=receipt,
    )
    assert art["sha256_hash"] == digest
    assert art["byte_length"] == len(payload)
    assert art["receipt_verifier_identity"] == "unit_test_verifier"

    invalid_receipt = dict(receipt)
    del invalid_receipt["verifier_ref"]
    with pytest.raises(ArtifactValidationError, match="missing required contract identity"):
        temp_db.register_artifact(
            artifact_id="art_rcpt_bad",
            artifact_type="receipt_type",
            storage_class="LOCAL",
            schema_version="v1",
            producer_ref="producer_1",
            verified_receipt=invalid_receipt,
        )


def test_backup_lifecycle_successful_path_deletes_backup_only_after_post_commit_checks(tmp_path):
    db_file = tmp_path / "backup_success.sqlite"
    store = ContentOpsDurableStore(db_file, auto_migrate=False)
    store.run_migrations(target_version=1)

    # Perform migration to current canonical schema.
    applied = store.run_migrations()
    assert applied == 8
    assert store.get_current_schema_version() == 9
    # Ensure backup files were unlinked after all post-commit checks passed
    bak_files = list(tmp_path.glob("*.bak.*"))
    assert len(bak_files) == 0


def test_backup_lifecycle_failure_after_commit_restores_database_and_retains_backup(tmp_path):
    db_file = tmp_path / "backup_failure_post_commit.sqlite"
    store = ContentOpsDurableStore(db_file, auto_migrate=False)
    store.run_migrations(target_version=3)

    # Monkeypatch verify_schema_integrity to fail AFTER migration v4 commits
    original_verify = store.verify_schema_integrity
    call_count = [0]

    def failing_verify():
        call_count[0] += 1
        if call_count[0] >= 1:
            raise DurableStateCorruptionError("Simulated post-commit verification failure")
        return original_verify()

    store.verify_schema_integrity = failing_verify

    with pytest.raises(MigrationError, match="Simulated post-commit verification failure"):
        store.run_migrations(target_version=4)

    # Source database must be restored to v3
    assert store.get_current_schema_version() == 3
    # Pre-migration backup file must be retained on disk
    bak_files = list(tmp_path.glob("*.bak.*"))
    assert len(bak_files) >= 1


def test_external_sqlite_writer_adversarial_threat_model_suite(temp_db):
    """Adversarial suite measuring external writer threats and store boundary invariants."""
    temp_db.create_work_item(
        story_id="story_adv_1", title="Adversarial Threat", target_surface="substack",
        work_item_id="wi_adv_1",
    )

    # 1. Spoofed append UDF
    statement, values, _ = _forged_event_insert(
        temp_db, work_item_id="wi_adv_1", event_seq=2, from_state="DISCOVERED", to_state="EVIDENCE_PENDING",
    )
    ext_conn = sqlite3.connect(str(temp_db.db_path))
    try:
        ext_conn.create_function("contentops_append_authorized", 0, lambda: 1)
        ext_conn.execute(statement, values)
        ext_conn.commit()
    finally:
        ext_conn.close()

    # 6. Replay detects materialized projection mismatch when external writer inserts event without updating work_items table
    with pytest.raises(DurableStateCorruptionError, match="Materialized projection mismatch"):
        temp_db.replay_work_item_events("wi_adv_1")

    # 4. Spoofed artifact insert UDF & 5. Forged GLOBAL_REUSABLE artifact
    art_values = (
        "art_forged_global", "claim", None, None, "memory", 12,
        compute_sha256(b"forged bytes"), "v1", temp_db._get_now_iso(), "external_writer",
        "PUBLIC", "GLOBAL_REUSABLE", None, None, None, None, None, None,
    )
    art_stmt = (
        "INSERT INTO artifact_references (artifact_id,artifact_type,story_id,work_item_id,storage_class,"
        "byte_length,sha256_hash,schema_version,created_at,producer_ref,sensitivity_class,artifact_scope,"
        "receipt_id,receipt_schema,receipt_source_identity,receipt_object_identity,receipt_verifier_identity,"
        "canonical_receipt_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
    )
    ext_conn2 = sqlite3.connect(str(temp_db.db_path))
    try:
        ext_conn2.create_function("contentops_artifact_insert_authorized", 0, lambda: 1)
        ext_conn2.execute(art_stmt, art_values)
        ext_conn2.commit()
    finally:
        ext_conn2.close()

    # 7. Artifact lookup
    fetched_art = temp_db.get_artifact("art_forged_global")
    assert fetched_art["artifact_scope"] == "GLOBAL_REUSABLE"

    # External writer updates work_items table projection so replay can proceed
    ext_conn3 = sqlite3.connect(str(temp_db.db_path))
    try:
        ext_conn3.execute(
            "UPDATE work_items SET current_state='EVIDENCE_PENDING', state_version=2 WHERE work_item_id='wi_adv_1'"
        )
        ext_conn3.commit()
    finally:
        ext_conn3.close()

    # 8. Store replay passes for hash-valid, projection-matched external write
    assert temp_db.replay_work_item_events("wi_adv_1")["verification_status"] == "PASS"
