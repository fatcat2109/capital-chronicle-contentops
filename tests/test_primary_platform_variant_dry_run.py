import importlib
import pathlib

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_import_has_no_side_effects():
    module = importlib.import_module("live_contentops.primary_platform_variant_dry_run")
    assert module.NEXT_BATCH_PROMPT.endswith("APPROVAL_CHALLENGE_CANDIDATE_CONTRACT_V0")


def _generated():
    from live_contentops import primary_platform_variant_dry_run as p

    briefs = p.load_briefs(REPO_ROOT)
    variants, blocked = p.build_all_variants(briefs)
    packet = p.build_run_packet(briefs, variants, blocked)
    return variants, blocked, packet


