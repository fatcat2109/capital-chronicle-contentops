import importlib
import pathlib

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.llm_intent_editorial_brief_contract")
    assert callable(module.write_artifacts)
    assert module.TASK_LABEL.startswith("TASK_CONTENTOPS_0174XE_XF_XG")


def _brief(packet, source_message_id):
    return [b for b in packet["editorial_briefs"] if b["source_message_id"] == source_message_id][0]


