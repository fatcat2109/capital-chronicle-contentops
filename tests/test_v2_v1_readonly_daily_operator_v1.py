from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from video.daily_operator_v1 import read_v1_opportunities, run_daily_operator
from video.unattended_core_factory_v1.creative import hash_value
from video.unattended_core_factory_v1.store import V2JobStore


REPO = Path(__file__).resolve().parents[1]
GOVERNED_PACKET = (
    REPO
    / "video"
    / "unattended_core_factory_v1"
    / "frozen_without_breaking_proof_input_v1.json"
)
HEAD = "a" * 40


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_v1_store(tmp_path: Path, *, now: datetime) -> Path:
    store_path = tmp_path / "v1.sqlite3"
    output = tmp_path / "v1-output" / "fresh"
    output.mkdir(parents=True)
    long_body = "# A qualified article\n\n" + " ".join(f"word{i}" for i in range(950))
    (output / "article_manifest_v1.json").write_text(
        json.dumps(
            {
                "title": "A fresh governed V1 article",
                "substack_body_markdown": long_body,
                "entities_topics": ["rates", "banks", "credit"],
                "evidence_document_ids": ["DOC1", "DOC2", "DOC3"],
            }
        ),
        encoding="utf-8",
    )
    (output / "grounded_support_v1.json").write_text(
        json.dumps(
            {
                "evidence_documents": [
                    {"evidence_document_id": "DOC1", "source_ref": "https://example.test/one"},
                    {"evidence_document_id": "DOC2", "source_ref": "https://example.test/two"},
                    {"evidence_document_id": "DOC3", "source_ref": "https://example.test/three"},
                ]
            }
        ),
        encoding="utf-8",
    )
    (output / "idea_selection_v1.json").write_text(
        json.dumps({"cluster_id": "fresh-story", "entities_topics": ["rates", "banks", "credit"]}),
        encoding="utf-8",
    )

    connection = sqlite3.connect(store_path)
    connection.executescript(
        """
        CREATE TABLE work_items(
            work_item_id TEXT PRIMARY KEY, story_id TEXT, title TEXT
        );
        CREATE TABLE outbox_messages(
            message_id TEXT PRIMARY KEY, work_item_id TEXT, destination TEXT,
            payload TEXT, created_at TEXT
        );
        CREATE TABLE platform_dispatches(
            dispatch_id TEXT PRIMARY KEY, message_id TEXT, platform TEXT, status TEXT,
            dispatched_at TEXT, public_object_id TEXT, public_object_url TEXT,
            public_object_url_hash TEXT
        );
        CREATE TABLE reconciliations(
            reconciliation_id TEXT PRIMARY KEY, work_item_id TEXT, status TEXT,
            reconciled_at TEXT
        );
        CREATE TABLE performance_observations(
            observation_id TEXT PRIMARY KEY, schema_version TEXT, dispatch_id TEXT,
            work_item_id TEXT, platform TEXT, public_object_id TEXT,
            public_object_url_hash TEXT, observation_window TEXT,
            scheduled_for_utc TEXT, collected_at_utc TEXT,
            collector_capability_version TEXT, collection_status TEXT,
            metrics_native_json TEXT, metric_availability_json TEXT,
            source_identity TEXT, observation_hash TEXT, learning_eligible INTEGER
        );
        """
    )
    published = (now - timedelta(hours=8)).isoformat().replace("+00:00", "Z")
    intent = json.dumps(
        {
            "article_identity": "article-fresh-v1",
            "story_identity": "fresh-story",
            "output_dir": str(output),
        }
    )
    connection.execute(
        "INSERT INTO work_items VALUES(?,?,?)",
        ("work-fresh", "fresh-story", "A fresh governed V1 article"),
    )
    connection.execute(
        "INSERT INTO outbox_messages VALUES(?,?,?,?,?)",
        ("message-fresh", "work-fresh", "substack", intent, published),
    )
    connection.execute(
        "INSERT INTO platform_dispatches VALUES(?,?,?,?,?,?,?,?)",
        (
            "dispatch-fresh",
            "message-fresh",
            "substack",
            "DISPATCH_CONFIRMED",
            published,
            "post-fresh",
            "https://capitalchronicle.substack.com/p/fresh-governed-article",
            "b" * 64,
        ),
    )
    connection.execute(
        "INSERT INTO reconciliations VALUES(?,?,?,?)",
        ("reconciliation_dispatch-fresh", "work-fresh", "RECONCILED_CONFIRMED", published),
    )
    connection.execute(
        "INSERT INTO performance_observations VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            "obs-fresh",
            "contentops.performance_observation.v1",
            "dispatch-fresh",
            "work-fresh",
            "substack",
            "post-fresh",
            "b" * 64,
            "T_PLUS_24H",
            published,
            published,
            "test",
            "COLLECTED",
            json.dumps({"shares": 4, "saves": 3}),
            json.dumps({"shares": "AVAILABLE", "saves": "AVAILABLE"}),
            "test.readonly",
            "c" * 64,
            1,
        ),
    )
    connection.commit()
    connection.close()
    return store_path


def test_real_v1_surface_is_read_only_and_candidate_job_is_idempotent(tmp_path: Path) -> None:
    now = datetime(2026, 8, 18, 15, 0, tzinfo=timezone.utc)
    v1_store = _make_v1_store(tmp_path, now=now)
    before = _sha(v1_store)
    snapshot = read_v1_opportunities(v1_store)
    assert _sha(v1_store) == before
    assert snapshot["read_surface"].startswith("published_corpus_read_model_v1")
    assert snapshot["read_only_proof"]["sqlite_uri_mode"] == "ro"
    assert snapshot["read_only_proof"]["pragma_query_only"] == 1
    assert snapshot["read_only_proof"]["connection_total_changes"] == 0
    assert snapshot["read_only_proof"]["v1_write_count"] == 0
    assert snapshot["article_count"] == 1
    assert len(snapshot["articles"][0]["evidence_refs"]) >= 3

    runtime = tmp_path / "v2-runtime"
    first = run_daily_operator(
        v1_store_path=v1_store,
        runtime_root=runtime,
        operator_run_id="daily_20260818_first",
        implementation_head=HEAD,
        parent_session_label="automation-high-parent",
        parent_task_id="parent-task-1",
        now=now,
    )
    second = run_daily_operator(
        v1_store_path=v1_store,
        runtime_root=runtime,
        operator_run_id="daily_20260818_repeat",
        implementation_head=HEAD,
        parent_session_label="automation-high-parent",
        parent_task_id="parent-task-2",
        now=now + timedelta(minutes=5),
    )
    assert first["result"] == "QUALIFIED_JOB_WAITING_GOVERNED_INPUT"
    assert first["created_job_count"] == 1
    assert second["created_job_count"] == 0
    assert second["candidate_decisions"][0]["idempotent_replay"] is True
    assert _sha(v1_store) == before

    store = V2JobStore(runtime / "v2_daily_operator_shadow.sqlite3")
    assert len(store.jobs()) == 1
    assert len(store.candidate_decisions()) == 1
    job = store.jobs()[0]
    assert job["state"] == "WAITING_GOVERNED_INPUT"
    assert job["run_id"] is None
    assert store.daily_review_queue()["waiting_governed_input_count"] == 1
    assert all(row["public_write_authority"] == 0 for row in store.jobs())
    assert all(row["v1_write_count"] == 0 for row in store.candidate_decisions())
    assert all(row["platform_write_count"] == 0 for row in store.candidate_decisions())


def test_qualified_candidate_activates_only_with_valid_governed_factory_packet(
    tmp_path: Path,
) -> None:
    now = datetime(2026, 8, 18, 15, 0, tzinfo=timezone.utc)
    v1_store = _make_v1_store(tmp_path, now=now)
    runtime = tmp_path / "v2-runtime"
    result = run_daily_operator(
        v1_store_path=v1_store,
        runtime_root=runtime,
        operator_run_id="daily_activation",
        implementation_head=HEAD,
        parent_session_label="automation-high-parent",
        now=now,
    )
    job_id = result["candidate_decisions"][0]["video_job_id"]
    packet = json.loads(GOVERNED_PACKET.read_text(encoding="utf-8"))
    store = V2JobStore(runtime / "v2_daily_operator_shadow.sqlite3")
    activated = store.activate_candidate_job(
        video_job_id=job_id,
        governed_input_packet_path=GOVERNED_PACKET,
        governed_input_packet_hash=hash_value(packet),
    )
    assert activated["state"] == "QUEUED"
    replay = store.activate_candidate_job(
        video_job_id=job_id,
        governed_input_packet_path=GOVERNED_PACKET,
        governed_input_packet_hash=hash_value(packet),
    )
    assert replay["state"] == "QUEUED"
    claimed = store.claim_next(worker_id="high-parent", implementation_head=HEAD)
    assert claimed is not None
    assert claimed["video_job_id"] == job_id
    assert claimed["run_id"]


def test_native_xhigh_handoff_receipt_is_distinct_append_only_and_zero_write(
    tmp_path: Path,
) -> None:
    store = V2JobStore(tmp_path / "v2.sqlite3")
    receipt = store.record_native_handoff(
        handoff_id="handoff_shadow_probe_1",
        operator_run_id="daily_shadow_probe_1",
        parent_task_id="parent-high-task",
        child_task_id="fresh-xhigh-child-task",
        child_model="gpt-5.6-sol",
        child_reasoning_effort="xhigh",
        child_worktree=str(tmp_path / "child-worktree"),
        purpose="SHADOW_ISOLATION_PROBE",
        governed_input_hash="d" * 64,
        result_hash="e" * 64,
    )
    assert receipt["child_task_id"] != receipt["parent_task_id"]
    assert receipt["child_reasoning_effort"] == "xhigh"
    assert receipt["cli_invocation_count"] == 0
    assert receipt["sdk_api_invocation_count"] == 0
    assert receipt["nine_router_creative_invocation_count"] == 0
    assert receipt["public_write_authority"] == 0
    assert store.record_native_handoff(
        handoff_id="handoff_shadow_probe_1",
        operator_run_id="daily_shadow_probe_1",
        parent_task_id="parent-high-task",
        child_task_id="fresh-xhigh-child-task",
        child_model="gpt-5.6-sol",
        child_reasoning_effort="xhigh",
        child_worktree=str(tmp_path / "child-worktree"),
        purpose="SHADOW_ISOLATION_PROBE",
        governed_input_hash="d" * 64,
        result_hash="e" * 64,
    )["handoff_id"] == receipt["handoff_id"]


def test_native_staggered_relay_is_append_only_exactly_once_and_zero_write(
    tmp_path: Path,
) -> None:
    store = V2JobStore(tmp_path / "v2.sqlite3")
    store.record_operator_run(
        operator_run_id="daily_relay_probe",
        summary={"result": "NO_GENUINE_QUALIFIED_CANDIDATE_NO_VIDEO"},
        parent_model="gpt-5.6-sol",
        parent_reasoning_effort="high",
        parent_task_id="high-daily-task",
        v1_read_snapshot_hash="a" * 64,
        decision_count=0,
        qualified_count=0,
        created_job_count=0,
        result="NO_GENUINE_QUALIFIED_CANDIDATE_NO_VIDEO",
    )
    packet = json.loads(GOVERNED_PACKET.read_text(encoding="utf-8"))
    governed_hash = hash_value(packet)
    request = store.create_creative_request(
        request_id="creative_req_shadow_probe_v1",
        idempotence_key="shadow_probe_task3_correction_v1",
        operator_run_id="daily_relay_probe",
        purpose="SHADOW_ISOLATION_PROBE",
        governed_input_path=GOVERNED_PACKET,
        governed_input_hash=governed_hash,
        parent_task_id="high-daily-task",
        parent_run_id="high-daily-run",
        parent_thread_id="high-daily-task",
        parent_worktree=str(tmp_path / "high-worktree"),
    )
    assert request["state"] == "READY_FOR_CREATIVE"
    assert request["idempotent_replay"] is False
    replay = store.create_creative_request(
        request_id="creative_req_shadow_probe_v1",
        idempotence_key="shadow_probe_task3_correction_v1",
        operator_run_id="daily_relay_probe",
        purpose="SHADOW_ISOLATION_PROBE",
        governed_input_path=GOVERNED_PACKET,
        governed_input_hash=governed_hash,
        parent_task_id="high-daily-task",
        parent_run_id="high-daily-run",
        parent_thread_id="high-daily-task",
        parent_worktree=str(tmp_path / "high-worktree"),
    )
    assert replay["idempotent_replay"] is True
    assert len(store.creative_relay_requests()) == 1

    claimed = store.claim_creative_request(
        request_id="creative_req_shadow_probe_v1",
        worker_task_id="xhigh-worker-task",
        worker_run_id="xhigh-worker-run",
        worker_thread_id="xhigh-worker-task",
        worker_worktree=str(tmp_path / "xhigh-worktree"),
        worker_model="gpt-5.6-sol",
        worker_reasoning_effort="xhigh",
    )
    assert claimed is not None
    assert claimed["state"] == "CREATIVE_CLAIMED"
    claim_replay = store.claim_creative_request(
        request_id="creative_req_shadow_probe_v1",
        worker_task_id="xhigh-worker-task",
        worker_run_id="xhigh-worker-run",
        worker_thread_id="xhigh-worker-task",
        worker_worktree=str(tmp_path / "xhigh-worktree"),
        worker_model="gpt-5.6-sol",
        worker_reasoning_effort="xhigh",
    )
    assert claim_replay is not None
    assert claim_replay["idempotent_replay"] is True

    creative_artifact = tmp_path / "creative-result.json"
    creative_artifact.write_text(
        json.dumps({"beats": ["evidence", "mechanism", "implication"]}),
        encoding="utf-8",
    )
    creative_hash = _sha(creative_artifact)
    ready = store.record_creative_result(
        request_id="creative_req_shadow_probe_v1",
        worker_task_id="xhigh-worker-task",
        worker_run_id="xhigh-worker-run",
        worker_thread_id="xhigh-worker-task",
        result_path=creative_artifact,
        result_hash=creative_hash,
        output_hashes={"creative_artifact_sha256": creative_hash},
    )
    assert ready["state"] == "CREATIVE_READY"
    assert store.claim_creative_request(
        worker_task_id="second-xhigh-task",
        worker_run_id="second-xhigh-run",
        worker_thread_id="second-xhigh-task",
        worker_worktree=str(tmp_path / "second-xhigh-worktree"),
        worker_model="gpt-5.6-sol",
        worker_reasoning_effort="xhigh",
    ) is None

    terminal = store.finalize_creative_request(
        request_id="creative_req_shadow_probe_v1",
        finalizer_task_id="high-finalizer-task",
        finalizer_run_id="high-finalizer-run",
        finalizer_thread_id="high-finalizer-task",
        finalizer_worktree=str(tmp_path / "finalizer-worktree"),
        finalizer_model="gpt-5.6-sol",
        finalizer_reasoning_effort="high",
        output_hashes={"finalizer_receipt_sha256": "b" * 64},
        terminal_result="SHADOW_ISOLATION_PROBE_RELAY_COMPLETE_NO_CONTENT_OUTCOME",
    )
    assert terminal["state"] == "LOCAL_TERMINAL_RESULT"
    terminal_replay = store.finalize_creative_request(
        request_id="creative_req_shadow_probe_v1",
        finalizer_task_id="high-finalizer-task",
        finalizer_run_id="high-finalizer-run",
        finalizer_thread_id="high-finalizer-task",
        finalizer_worktree=str(tmp_path / "finalizer-worktree"),
        finalizer_model="gpt-5.6-sol",
        finalizer_reasoning_effort="high",
        output_hashes={"finalizer_receipt_sha256": "b" * 64},
        terminal_result="SHADOW_ISOLATION_PROBE_RELAY_COMPLETE_NO_CONTENT_OUTCOME",
    )
    assert terminal_replay["idempotent_replay"] is True
    events = store.creative_relay_events("creative_req_shadow_probe_v1")
    assert [row["state"] for row in events] == [
        "READY_FOR_CREATIVE",
        "CREATIVE_CLAIMED",
        "CREATIVE_READY",
        "HIGH_FINALIZATION",
        "LOCAL_TERMINAL_RESULT",
    ]
    assert all(row["public_write_authority"] == 0 for row in events)
    assert all(row["v1_write_count"] == 0 for row in events)
    assert all(row["platform_write_count"] == 0 for row in events)
    queue = store.daily_review_queue()
    assert queue["creative_relay_request_count"] == 1
    assert queue["local_terminal_result_count"] == 1


def test_native_staggered_relay_rejects_non_xhigh_worker(tmp_path: Path) -> None:
    store = V2JobStore(tmp_path / "v2.sqlite3")
    store.record_operator_run(
        operator_run_id="daily_relay_model_gate",
        summary={},
        parent_model="gpt-5.6-sol",
        parent_reasoning_effort="high",
        parent_task_id="parent",
        v1_read_snapshot_hash="c" * 64,
        decision_count=0,
        qualified_count=0,
        created_job_count=0,
        result="NO_GENUINE_QUALIFIED_CANDIDATE_NO_VIDEO",
    )
    packet = json.loads(GOVERNED_PACKET.read_text(encoding="utf-8"))
    store.create_creative_request(
        request_id="creative_req_model_gate",
        idempotence_key="creative_req_model_gate",
        operator_run_id="daily_relay_model_gate",
        purpose="SHADOW_ISOLATION_PROBE",
        governed_input_path=GOVERNED_PACKET,
        governed_input_hash=hash_value(packet),
        parent_task_id="parent",
        parent_run_id="parent-run",
        parent_thread_id="parent",
        parent_worktree=str(tmp_path / "parent-worktree"),
    )
    try:
        store.claim_creative_request(
            worker_task_id="worker",
            worker_run_id="worker-run",
            worker_thread_id="worker",
            worker_worktree=str(tmp_path / "worker-worktree"),
            worker_model="gpt-5.6-sol",
            worker_reasoning_effort="high",
        )
    except Exception as exc:
        assert str(exc) == "creative_worker_model_or_reasoning_mismatch"
    else:
        raise AssertionError("HIGH worker must not satisfy the XHIGH creative relay")


def test_daily_operator_has_no_forbidden_creative_execution_path() -> None:
    for relative in (
        "video/daily_operator_v1.py",
        "scripts/run_v2_daily_operator_shadow_v1.py",
    ):
        source = (REPO / relative).read_text(encoding="utf-8").casefold()
        assert "codex exec" not in source
        assert "routed_v2_creative_invocation" not in source
        assert "nine_router_llm" not in source
        assert "publication_coordinator" not in source
        assert "destination_transport" not in source
