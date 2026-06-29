"""Unit tests for supervised dispatch contract coordinator."""
from __future__ import annotations

import json
import os
from live_contentops import supervised_dispatch_contract_v6 as coordinator


def test_coordinator_outputs():
    packet = coordinator.make_supervised_dispatch_packet()
    contract = coordinator.make_supervised_dispatch_input_contract()
    template = coordinator.make_supervised_dispatch_blocked_template()
    output = coordinator.make_supervised_dispatch_blocked_output()
    matrix = coordinator.make_supervised_dispatch_gate_matrix()
    checklist = coordinator.make_supervised_dispatch_checklist()

    assert packet["supervised_dispatch_status"] == "SUPERVISED_DISPATCH_BLOCKED_WAITING_FOR_VALID_OUTBOX_AND_AUTHORIZATION"
    assert contract["contract_status"] == "FUTURE_SUPERVISED_DISPATCH_INPUT_CONTRACT_ONLY"
    assert template["dispatch_template_status"] == "BLOCKED_TEMPLATE_ONLY_NOT_DISPATCH"
    assert output["dispatch_output_status"] == "BLOCKED_NO_DISPATCH_ATTEMPT_CREATED"
    assert len(matrix) == 6
    assert checklist["checklist_status"] == "SUPERVISED_DISPATCH_BLOCKED_PENDING_OUTBOX_AUTHORIZATION_AND_KILL_SWITCH"
