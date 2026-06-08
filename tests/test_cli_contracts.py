import subprocess
import json
import sys
from pathlib import Path

def run_cli(cmd):
    cwd = Path(__file__).parent.parent
    return subprocess.run([sys.executable, "-m", "live_contentops.cli", cmd], capture_output=True, text=True, cwd=str(cwd))

def test_cli_contracts_summary():
    res = run_cli("contracts-summary")
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert "contracts" in data

def test_cli_validate_samples():
    res = run_cli("validate-sample-contracts")
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["validation"] == "SUCCESS"
