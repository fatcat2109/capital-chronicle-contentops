import os
from live_contentops import config

def test_config_defaults():
    assert config.ENVIRONMENT == "local"
    assert config.NETWORK_ENABLED is False
    assert config.PROVIDER_CALLS_ENABLED is False
    assert config.PLATFORM_APIS_ENABLED is False
    assert config.SCHEDULER_ENABLED is False
    assert config.PUBLISHING_ENABLED is False
    assert config.AUTONOMOUS_REPLIES_ENABLED is False
    assert config.REQUIRE_HUMAN_APPROVAL is True
    assert config.KILL_SWITCH_DEFAULT is True
