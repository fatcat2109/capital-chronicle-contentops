import pytest
import subprocess
import os
from live_contentops import cli

def test_cli_commands_map_exists():
    assert hasattr(cli, 'COMMANDS')
    assert isinstance(cli.COMMANDS, dict)
    assert len(cli.COMMANDS) >= 35
    
def test_cli_command_status():
    assert "status" in cli.COMMANDS

def test_cli_dispatch_unknown_command():
    res = subprocess.run(
        ["python", "-m", "live_contentops.cli", "not-a-real-command-1234"],
        cwd=os.path.join(os.path.dirname(__file__), '..'),
        capture_output=True,
        text=True
    )
    assert res.returncode == 1
    assert "Unknown command" in res.stdout
    assert "Usage: python -m live_contentops.cli" in res.stdout

def test_cli_dispatch_no_args():
    res = subprocess.run(
        ["python", "-m", "live_contentops.cli"],
        cwd=os.path.join(os.path.dirname(__file__), '..'),
        capture_output=True,
        text=True
    )
    assert res.returncode == 1
    assert "Usage: python -m live_contentops.cli" in res.stdout
