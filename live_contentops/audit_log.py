"""Audit log placeholder."""
from typing import Dict, Any
from .contracts import AuditEvent

_LOG = []

def log_event(event: AuditEvent):
    _LOG.append(event)
