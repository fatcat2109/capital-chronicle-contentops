"""Approval queue placeholder."""
from typing import Dict, Any

_QUEUE = []

def add_to_queue(item: Dict[str, Any]):
    _QUEUE.append(item)

def approve(item_id: str) -> bool:
    return False # No publish execution
