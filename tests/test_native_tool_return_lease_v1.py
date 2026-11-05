"""A completed browser return is recordable while another window owns the newsroom."""
from contextlib import contextmanager
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


def test_tool_return_records_under_own_lease_but_fresh_publication_stays_serial(monkeypatch):
    spec = spec_from_file_location("cc124_native_cli", Path(__file__).parents[1] / "scripts/run_native_desktop_editorial.py")
    cli = module_from_spec(spec)
    spec.loader.exec_module(cli)
    events = []

    class Store:
        def acquire_lease(self, key, owner, ttl_seconds):
            events.append(("acquire", key))
            return {"lease_id": "own", "fencing_token": 2}

        def release_lease(self, lease_id, owner, token):
            events.append(("release", lease_id))

    @contextmanager
    def busy_newsroom(store):
        raise RuntimeError("another window owns newsroom")
        yield

    def record(binding, **kwargs):
        assert kwargs["operation_lease"]["lease_id"] == "own"
        events.append(("record", kwargs["command"]))
        return {"classification": "NATIVE_NEO_RETURN_SAVED"}

    monkeypatch.setattr(cli, "validate_binding", lambda *a, **k: None)
    monkeypatch.setattr(cli, "_bound_store", lambda *a: Store())
    monkeypatch.setattr(cli, "_operation", record)
    monkeypatch.setattr("live_contentops.native_finished_publication_v1.newsroom_lease", busy_newsroom)
    binding = {"run_id": "retained-operation", "owner_manual_validation": False}
    assert cli.operation(binding, command="publication-tool-submit")["classification"] == "NATIVE_NEO_RETURN_SAVED"
    assert events == [("acquire", "internal:native-editorial:retained-operation"),
                      ("record", "publication-tool-submit"), ("release", "own")]
    for command in ("publication-tool-begin", "publication-resume", "standing", "advance"):
        with pytest.raises(RuntimeError, match="another window"):
            cli.operation(binding, command=command)
    assert len(events) == 3
