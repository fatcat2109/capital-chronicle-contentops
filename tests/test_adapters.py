import pytest
from live_contentops.adapters.base import BaseAdapter, LiveCapabilityDisabled

def test_adapter_base_dry_run():
    adapter = BaseAdapter()
    result = adapter.dry_run({"test": "data"})
    assert result.validation_status == "success"

def test_adapter_base_publish_disabled():
    adapter = BaseAdapter()
    with pytest.raises(LiveCapabilityDisabled):
        adapter.publish({"test": "data"})
        
def test_adapter_base_send_disabled():
    adapter = BaseAdapter()
    with pytest.raises(LiveCapabilityDisabled):
        adapter.send({"test": "data"})
