"""V6 Content Idea Packet.

Represents Jim's initial content ideas, source contexts, and operator input structures.
"""
from __future__ import annotations

import uuid
from typing import Any


def create_content_idea_packet(
    idea_text: str,
    operator_name: str = "Jim",
    source_context: dict[str, Any] | None = None,
    target_audience: str = "general_financial_education"
) -> dict[str, Any]:
    """Constructs a structured Content Idea Packet from operator inputs."""
    return {
        "idea_id": f"idea_{uuid.uuid4().hex[:12]}",
        "operator_name": operator_name,
        "idea_text": idea_text,
        "source_context": source_context or {},
        "target_audience": target_audience,
        "grounding_required": True,
        "schema_version": "6.0.0"
    }
