import json
import subprocess
import sys
from pathlib import Path

def test_cli_status():
    result = subprocess.run([sys.executable, "-m", "live_contentops.cli", "status"], capture_output=True, text=True, cwd=str(Path(__file__).parent.parent))
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["status"] == "local skeleton status"
    assert data["network"] == "disabled"
    assert data["provider_calls"] == "disabled"
    assert data["platform_apis"] == "disabled"
    assert data["scheduler"] == "disabled"
    assert data["publishing"] == "disabled"
    assert data["autonomous_replies"] == "disabled"
    assert data["next_task"] == "TASK_CONTENTOPS_0066_LOCAL_PACKET_REGISTRY_QUERY_AND_OPERATOR_DASHBOARD_SUMMARY_V0"