import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.approval_challenge_candidate_contract")
    assert module.NEXT_BATCH_PROMPT.endswith("APPROVAL_LEDGER_CONTRACT_V0")


def _result():
    from live_contentops import approval_challenge_candidate_contract as c

    return c.write_artifacts(REPO_ROOT)


