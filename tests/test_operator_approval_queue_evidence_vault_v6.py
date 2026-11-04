from dataclasses import asdict
import json
from pathlib import Path

import pytest

from live_contentops.operator_approval_queue_evidence_vault_v6 import *


def packet_dict():
    return asdict(sample_operator_approval_queue_evidence_vault_packet())


def test_canonical_dashboard_contains_required_queue_evidence_labels_and_no_enabled_controls():
    dashboard_dir = Path("ui/contentops_v5/src")
    app = (dashboard_dir / "App.tsx").read_text(encoding="utf-8-sig").lower()
    fixtures = (dashboard_dir / "fixtures.ts").read_text(encoding="utf-8-sig").lower()
    approval = (dashboard_dir / "views" / "ApprovalQueue.tsx").read_text(encoding="utf-8-sig").lower()
    evidence = (dashboard_dir / "views" / "EvidenceVault.tsx").read_text(encoding="utf-8-sig").lower()
    combined = "\n".join([app, fixtures, approval, evidence])
    assert "operator approval queue" in combined
    assert "evidence vault" in combined
    assert "sample_fixture_only" in combined
    assert "d4a5afd3ecf03b1b93caf5b9dbd204d93eb80237eb8d368c9eea24680fabe44e" in combined
    assert "1cd58fd896f19c77638e62c52f34700c8166bd9644a8d830071d174924ca9172" in combined
    assert "974e8509d7999acad8cdf4855dc874d2d7182e766a51d4d1b4a6d6749126eb32" in combined
    assert "c19e65c51abb0967d25dde12e8c1b5ff2a3fa32ccac3b9e14eb7d73aa30b1b59" in combined
    assert "discord_dry_run_outbox_e59579adf7eb8db3" in combined
    assert "e59579adf7eb8db3839080f3b1b6f6744012d064f1fa58a96abb02bdff73bb80" in combined
    assert "live pilot blocked" in combined
    assert "live blocked" in combined
    assert "dispatch to platform" in combined
    assert "<button>send" not in combined
    assert "<button>dispatch" not in combined
    assert "<button>approve" not in combined


def test_standalone_ui_removed_and_not_canonical():
    assert not Path("ui/operator_approval_queue_evidence_vault/index.html").exists()
    runbook = Path("docs/runbooks/V6_OPERATOR_APPROVAL_QUEUE_EVIDENCE_VAULT_UI_RUNBOOK.md").read_text(encoding="utf-8-sig")
    assert "ui/contentops_v5/" in runbook
    assert "ui/institutional_operator_cockpit_v4/index.html" not in runbook
    assert "ui/operator_approval_queue_evidence_vault/index.html" not in runbook


