from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_simple_dashboard_launcher_delegates_to_canonical_zero_write_runtime():
    cmd = (ROOT / "Start_ContentOps_Simple_Run_Dashboard.cmd").read_text(encoding="utf-8")
    script = (ROOT / "scripts" / "Start-ContentOpsSimpleRunDashboard.ps1").read_text(
        encoding="utf-8"
    )

    assert "Start-ContentOpsSimpleRunDashboard.ps1" in cmd
    assert "Start-ContentOpsDailyApp.ps1" in script
    assert "--no-open-browser" in script
    assert "?view=simple" in script
    assert "127.0.0.1" in script
    assert "Start-Process $dashboardUrl" in script
    assert "publish" not in script.casefold()
    assert "credential" not in script.casefold()
    assert "token" not in script.casefold()
    assert "cookie" not in script.casefold()


def test_simple_dashboard_launcher_has_bounded_current_ui_ports_only():
    script = (ROOT / "scripts" / "Start-ContentOpsSimpleRunDashboard.ps1").read_text(
        encoding="utf-8"
    )

    assert "@(4173, 5173)" in script
    assert "Invoke-WebRequest" in script
    assert "-TimeoutSec 2" in script
    assert "SIMPLE_RUN_DASHBOARD_NOT_READY" in script
