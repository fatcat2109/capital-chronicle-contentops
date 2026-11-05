"""The live status reader must never offer a retired publication request again."""
import json

import pytest

from live_contentops.native_desktop_publication_v1 import DESTINATION, publication_projection


@pytest.mark.parametrize("status,pending", [("NATIVE_NEO_TOOL_PENDING", True), ("NATIVE_NEO_SUPERSEDED", False)])
def test_publication_status_omits_superseded_tool_request(status, pending):
    rows = [{"message_id":"binding", "work_item_id":"work", "destination":DESTINATION,
        "payload":json.dumps({"run_id":"work", "plan_hash":"plan"})},
        {"message_id":"older-request", "work_item_id":"work", "destination":"internal:native-neo-tool",
            "status":status, "payload":json.dumps({"operation_id":"work",
                "schema_version":"contentops.native_neo_tool_request.v1",
                "request":{"action":"PUBLISH", "destination":"x", "request_sha256":"request"}})}]
    result = publication_projection(rows, [], [], run_id="work")
    assert bool(result["pending_requests"]) is pending
    assert (result["next_operation"] == "publication-tool-begin") is pending
