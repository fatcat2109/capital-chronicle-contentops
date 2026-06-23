from pathlib import Path

from live_contentops import approval_ledger as ledger
from live_contentops import approval_payload_hash as aph
from live_contentops import approval_validator as validator


def test_no_env_network_or_browser_imports():
    for module_file in (aph.__file__, ledger.__file__, validator.__file__):
        source = Path(module_file).read_text(encoding="utf-8")
        forbidden = (
            "getenv",
            "environ",
            "dotenv",
            "requests",
            "urllib",
            "socket",
            "http.client",
            "subprocess",
            "playwright",
            "selenium",
            "webdriver",
        )
        for token in forbidden:
            assert token not in source, f"Forbidden token '{token}' found in {module_file}"


def test_no_dispatch_action_simulation():
    # Make sure we don't have simulated API dispatcher codes inside the core approval files
    for module_file in (aph.__file__, ledger.__file__, validator.__file__):
        source = Path(module_file).read_text(encoding="utf-8")
        # Assert no dispatching network triggers are present
        assert "requests.post" not in source
        assert "urllib.request" not in source
        assert "socket.connect" not in source
