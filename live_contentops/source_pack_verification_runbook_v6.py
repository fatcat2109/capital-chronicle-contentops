"""V6 Source Pack Verification Runbook.

Establishes offline operational guidelines for operator source pack verification tasks.
"""
from __future__ import annotations


def get_verification_runbook_content() -> str:
    """Returns runbook guidelines."""
    return """# Source Pack Verification Runbook

Operational instructions for research and evidence capture tasks.

## Steps
1. Load outstanding checklist items from operator_research_checklist.json.
2. Complete manual source searches to retrieve data.
3. Enter official URLs and SHA256 hashes into the entry template along with retrieved data excerpt text.
4. Sign with operator_verified_by signature.
"""
