import pytest
import os
from unittest.mock import patch

from live_contentops.telegram_live_pilot import execute_telegram_pilot, LivePilotBlockedException

def test_live_pilot_blocks_public_channel():
    with pytest.raises(LivePilotBlockedException) as exc:
        execute_telegram_pilot("@CapitalChronicle", "test msg")
    assert "Live pilot explicitly forbids targeting public channels" in str(exc.value)

@patch.dict(os.environ, {}, clear=True)
def test_live_pilot_blocks_missing_token():
    with pytest.raises(LivePilotBlockedException) as exc:
        execute_telegram_pilot("-100123456789", "test msg")
    assert "TELEGRAM_BOT_TOKEN is missing from the environment" in str(exc.value)

@patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "fake_token"})
@patch("urllib.request.urlopen")
def test_live_pilot_executes_with_correct_parameters(mock_urlopen):
    class MockResponse:
        def read(self):
            return b'{"ok": true, "result": {"message_id": 1}}'
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_urlopen.return_value = MockResponse()

    result = execute_telegram_pilot("-100123456789", "test msg")
    
    assert result["status"] == "SUCCESS"
    assert result["live_action_taken"] is True
    assert result["audit"]["event_type"] == "POLICY_EVALUATED"
    assert result["telegram_response"]["ok"] is True
