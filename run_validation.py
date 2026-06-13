import subprocess

commands = [
    ["python", "-m", "pytest", "-q"],
    ["node", "--check", "ui/institutional_shell/app.js"],
    ["git", "diff", "--check"],
    ["python", "-m", "live_contentops.cli", "status"],
    ["python", "-m", "live_contentops.cli", "pre-alpha-institutional-antigravity-browser-qa-strategy-summary"],
    ["python", "-m", "live_contentops.cli", "pre-alpha-institutional-pre-antigravity-static-qa-hardening-summary"],
    ["python", "-m", "live_contentops.cli", "pre-alpha-institutional-visual-export-screenshot-safe-mode-screen-summary"],
    ["python", "-m", "live_contentops.cli", "pre-alpha-institutional-content-calendar-workflow-board-screen-summary"],
    ["python", "-m", "live_contentops.cli", "pre-alpha-institutional-evidence-vault-audit-timeline-screen-summary"],
    ["python", "-m", "live_contentops.cli", "pre-alpha-institutional-publish-readiness-tower-screen-summary"],
    ["python", "-m", "live_contentops.cli", "pre-alpha-institutional-content-studio-screen-summary"],
    ["python", "-m", "live_contentops.cli", "pre-alpha-institutional-command-center-screen-summary"],
    ["python", "-m", "live_contentops.cli", "pre-alpha-institutional-shell-prototype-summary"]
]

for cmd in commands:
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FAILED: {' '.join(cmd)}")
        print(result.stdout)
        print(result.stderr)
    else:
        print(f"SUCCESS: {' '.join(cmd)}")
        
print("Validation complete.")
