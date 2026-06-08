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
    assert data["next_task"] == "TASK_CONTENTOPS_0070_LOCAL_REAL_ARTIFACT_INTAKE_CONTRACT_AND_READINESS_GATE_V0"