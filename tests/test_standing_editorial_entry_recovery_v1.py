"""CC-124: disposable entry replay, no source, model or public calls."""
import json
from pathlib import Path

import pytest

from live_contentops.capital_chronicle_latest_report_consumer_v1 import canonical_bytes, sha256_of
from tests.test_native_newsroom_owner_operation_v1 import entry
from tests.test_publication_coordinator_v1 import _quarantined_derivative_fixture


def isolated_binding(module, tmp_path, store):
    profile = {"schema_version": "contentops.native_desktop_operator_profile.v1",
        "editorial_output_root": str(tmp_path / "articles"),
        "store_path": str(store.db_path), "published_memory_store": str(store.db_path),
        "published_memory_output_root": str(tmp_path / "published"),
        "feed_pointer_path": str(tmp_path / "feed.json")}
    Path(profile["feed_pointer_path"]).write_text("{}")
    return module.resolve_owner_operation(profile, operation_id="same-standing-operation",
        request="Use retained research only; do not ingest any new X input.")


def test_exact_quarantine_reaches_report_only_selection_and_preserves_binding(tmp_path, monkeypatch):
    store, transport, coordinator, ids = _quarantined_derivative_fixture(tmp_path)
    module = entry()
    path, binding = isolated_binding(module, tmp_path, store)
    original = path.read_bytes()
    dispatch = store.get_platform_dispatch(ids["dispatch_id"])
    quarantine = store.get_outbox_message("publication-recovery-quarantine-" + ids["dispatch_id"])
    calls = list(transport.publish_calls)
    seen = []

    class ControlledFeed:
        def __init__(self, tracker, pointer, **kwargs):
            assert kwargs["headline_paths"] == []

        def opportunity(self, **kwargs):
            rolling = kwargs["rolling_input"]
            assert rolling == {"headlines": [], "scope": "REPORT_AND_RETAINED_RESEARCH_ONLY_NO_NEW_X_INTAKE"}
            seen.append(kwargs["cutoff_utc"])
            key = "native-current-input-" + sha256_of(binding["run_id"])
            if not store.get_outbox_message(key):
                store.register_outbox_message(message_id=key,
                    work_item_id="cc-opportunity-" + sha256_of(binding["run_id"]),
                    destination="internal:native-current-input", status="EDITORIAL_INTERNAL",
                    payload=canonical_bytes({"rolling_input": rolling}).decode())
            return {"classification": "CONTROLLED_INPUT_REACHED", "qualified_article_count": 0}

    monkeypatch.setattr(module, "MainReportFeed", ControlledFeed)
    monkeypatch.setattr(module, "load_canonical_published_memory_read_only", lambda **kwargs: ([], {}))
    assert module.operation(binding, report_only=True)["classification"] == "CONTROLLED_INPUT_REACHED"
    # No new flag or binding rewrite is needed after the exact input is frozen.
    assert module.operation(binding)["classification"] == "CONTROLLED_INPUT_REACHED"
    assert seen == [binding["cutoff_utc"]] * 2
    assert path.read_bytes() == original
    registered = store.get_outbox_message("native-operation-binding-" + sha256_of(binding["run_id"]))
    assert json.loads(registered["payload"]) == binding
    assert store.get_platform_dispatch(ids["dispatch_id"]) == dispatch
    assert store.get_outbox_message(quarantine["message_id"]) == quarantine
    assert transport.publish_calls == calls
    assert coordinator.editorial_recovery_dispatch_ids() == []


@pytest.mark.parametrize("fault", ["changed_intent", "changed_authority", "readback_not_owed",
                                    "ATTEMPT_STARTED", "PENDING", "AMBIGUOUS"])
def test_unresolved_recovery_is_visible_without_blocking_editorial_preparation(tmp_path, monkeypatch, fault):
    store, transport, coordinator, ids = _quarantined_derivative_fixture(tmp_path)
    module = entry()
    _, binding = isolated_binding(module, tmp_path, store)
    if fault in {"ATTEMPT_STARTED", "PENDING", "AMBIGUOUS"}:
        store.set_dispatch_status(ids["dispatch_id"], fault)
    else:
        message_id = (ids["message_id"] if fault == "changed_intent" else
                      "publication-recovery-quarantine-" + ids["dispatch_id"])
        row = store.get_outbox_message(message_id)
        value = json.loads(row["payload"])
        value.update({"changed": True} if fault == "changed_intent" else
                     {"authority_ref": "unrelated"} if fault == "changed_authority" else
                     {"readback_owed": False})
        with store.get_connection() as conn:
            conn.execute("UPDATE outbox_messages SET payload=? WHERE message_id=?",
                         (canonical_bytes(value).decode(), message_id))
    before = store.get_platform_dispatch(ids["dispatch_id"])
    calls = list(transport.publish_calls)
    class ControlledFeed:
        def __init__(self, *args, **kwargs):
            pass

        def opportunity(self, **kwargs):
            return {"classification": "CONTROLLED_INPUT_REACHED", "qualified_article_count": 0}

    monkeypatch.setattr(module, "MainReportFeed", ControlledFeed)
    monkeypatch.setattr(module, "load_canonical_published_memory_read_only", lambda **kwargs: ([], {}))
    result = module.operation(binding, report_only=True)
    assert result["classification"] == "CONTROLLED_INPUT_REACHED"
    assert result["pending_publication_recovery_dispatch_ids"] == [ids["dispatch_id"]]
    assert coordinator.editorial_recovery_dispatch_ids() == [ids["dispatch_id"]]
    assert store.get_platform_dispatch(ids["dispatch_id"]) == before
    assert transport.publish_calls == calls


def test_report_only_refuses_existing_frozen_x_without_rewriting_it(tmp_path, monkeypatch):
    store, _, _, _ = _quarantined_derivative_fixture(tmp_path)
    module = entry()
    path, binding = isolated_binding(module, tmp_path, store)
    original = path.read_bytes()
    work = "cc-opportunity-" + sha256_of(binding["run_id"])
    store.create_work_item(story_id=work, work_item_id=work, title="Fixture", target_surface="CONTENTOPS_EDITORIAL_ONLY")
    key = "native-current-input-" + sha256_of(binding["run_id"])
    frozen = canonical_bytes({"rolling_input": {"headlines": [{"id": "existing-x"}]}}).decode()
    store.register_outbox_message(message_id=key, work_item_id=work,
        destination="internal:native-current-input", status="EDITORIAL_INTERNAL", payload=frozen)
    monkeypatch.setattr(module, "load_canonical_published_memory_read_only", lambda **kwargs: ([], {}))
    monkeypatch.setattr(module, "MainReportFeed", lambda *a, **kw: pytest.fail("feed must not run"))
    with pytest.raises(ValueError, match="REPORT_ONLY_FROZEN_OR_BOUND_INPUT_CONFLICT"):
        module.operation(binding, report_only=True)
    assert store.get_outbox_message(key)["payload"] == frozen
    assert path.read_bytes() == original


def test_standing_cli_forwards_report_only_to_binding_and_operation(tmp_path, monkeypatch):
    import live_contentops.native_finished_publication_v1 as finished
    module = entry()
    profile = tmp_path / "profile.json"
    profile.write_text("{}")
    seen = []

    def resolver(*args, **kwargs):
        seen.append(kwargs["report_only"])
        return tmp_path / "binding.json", {}

    def operation(binding, **kwargs):
        seen.append(kwargs["report_only"])
        return {"classification": "CONTROLLED"}

    monkeypatch.setattr(finished, "standing_binding", resolver)
    monkeypatch.setattr(module, "operation", operation)
    assert module.main(["standing", "--profile", str(profile), "--rollout", str(profile),
                        "--operation-id", "same", "--report-only"]) == 0
    assert seen == [True, True]
