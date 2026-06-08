"""Adapter base placeholder."""
from typing import Dict, Any
from ..contracts import AdapterDryRunResult

class LiveCapabilityDisabled(Exception):
    pass

class BaseAdapter:
    def dry_run(self, payload: Dict[str, Any]) -> AdapterDryRunResult:
        return AdapterDryRunResult(
            run_id="test",
            platform="base",
            payload=payload,
            validation_status="success"
        )
        
    def publish(self, payload: Dict[str, Any]):
        raise LiveCapabilityDisabled("Live publishing is currently disabled by configuration.")
        
    def send(self, payload: Dict[str, Any]):
        raise LiveCapabilityDisabled("Sending live data is disabled.")
