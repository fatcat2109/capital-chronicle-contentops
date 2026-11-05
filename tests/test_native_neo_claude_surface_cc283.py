"""CC-283: a Claude Code surface may run the BrowserOS Neo step, under its own true label.

Controlled protocol checks only; these fixtures do not prove a browser action.
"""
from datetime import datetime, timezone

import pytest

from live_contentops.native_neo_executor_v1 import CLAUDE_CODE_SURFACE, SURFACE_TOOLS, TOOL
from live_contentops.neo_destination_handoff_v1 import NeoDestinationHandoff
from test_native_neo_executor_v1 import pending_readback, setup

CLAUDE_TOOL = "mcp__browseros-neo__run"


def _submission(packet, *, surface=CLAUDE_CODE_SURFACE, tool=CLAUDE_TOOL, **changes):
    observation = {"tool_name": tool, "native_invocation_id": "controlled-test", "surface": surface,
                   "observation_source": "CONTROLLED_TEST_NOT_BROWSER_PROOF",
                   "observed_at_utc": datetime.now(timezone.utc).isoformat()}
    for key, value in changes.items():
        if value is None:
            observation.pop(key)
        else:
            observation[key] = value
    request = packet["request"]
    return {"tool_request_sha256": packet["tool_request_sha256"], "tool_observation": observation,
            "result": {"request_sha256": request["request_sha256"], "status": "SUCCESS"}}


def test_claude_code_surface_is_accepted_and_recorded_under_its_own_label(tmp_path):
    store, executor = setup(tmp_path)
    packet, _, _ = pending_readback(NeoDestinationHandoff(native_executor=executor), "x")
    request_hash = packet["request"]["request_sha256"]
    assert packet["required_tool"] == TOOL  # the stored request is unchanged by CC-283
    executor.begin(request_hash)
    executor.submit(request_hash, _submission(packet))
    stored = executor._get(request_hash, "response")["result"]["native_tool_observation"]
    assert stored["surface"] == "CLAUDE_CODE_SESSION" and stored["tool_name"] == CLAUDE_TOOL
    assert "CODEX" not in stored["surface"]
    assert SURFACE_TOOLS["CODEX_EXEC"] == TOOL and SURFACE_TOOLS[CLAUDE_CODE_SURFACE] == CLAUDE_TOOL


@pytest.mark.parametrize("surface, tool", [
    (CLAUDE_CODE_SURFACE, TOOL),                # Claude's step named with Codex's tool: a relabel
    ("CODEX_EXEC", CLAUDE_TOOL),                # Codex's step named with Claude's tool
    ("CLAUDE_AS_CODEX", CLAUDE_TOOL),           # any other label
    (None, CLAUDE_TOOL),
])
def test_a_surface_and_tool_that_do_not_belong_together_are_refused(tmp_path, surface, tool):
    store, executor = setup(tmp_path)
    packet, _, _ = pending_readback(NeoDestinationHandoff(native_executor=executor), "x")
    request_hash = packet["request"]["request_sha256"]
    executor.begin(request_hash)
    submission = _submission(packet, tool=tool)
    if surface is None:
        submission["tool_observation"].pop("surface")
    else:
        submission["tool_observation"]["surface"] = surface
    with pytest.raises(ValueError, match="NATIVE_NEO_ACTUAL_TOOL_OBSERVATION_REQUIRED"):
        executor.submit(request_hash, submission)
    assert executor._get(request_hash, "response") is None


@pytest.mark.parametrize("missing", ["native_invocation_id", "observation_source", "observed_at_utc"])
def test_a_claude_step_without_invocation_evidence_is_refused(tmp_path, missing):
    store, executor = setup(tmp_path)
    packet, _, _ = pending_readback(NeoDestinationHandoff(native_executor=executor), "x")
    request_hash = packet["request"]["request_sha256"]
    executor.begin(request_hash)
    # An observation without its invocation id or from another invocation does not bind to the claim.
    refused = "NATIVE_NEO_(ACTUAL_TOOL_OBSERVATION|TOOL_RETURN_BINDING)_REQUIRED"
    with pytest.raises(ValueError, match=refused):
        executor.submit(request_hash, _submission(packet, **{missing: None}))
    with pytest.raises(ValueError, match=refused):
        executor.submit(request_hash, _submission(packet, native_invocation_id="another-session"))
    assert executor._get(request_hash, "response") is None
