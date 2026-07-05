import subprocess
import os

def run_cmd(cmd):
    print(f"Running: {cmd}")
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.stdout: print(res.stdout.strip())
    if res.stderr: print(res.stderr.strip())
    return res.returncode

run_cmd("git status --short -- ui/institutional_operator_cockpit_v2")
run_cmd("git status --short -- ui/institutional_shell")
run_cmd("git status --short -- docs/design_references")
run_cmd("python -m pytest -q tests/test_institutional_operator_cockpit_v2.py")

# scan ui/institutional_operator_cockpit_v2 for remote dependencies
target_dir = r"ui/institutional_operator_cockpit_v2"
forbidden = ["http://", "https://", "cdn.", "fonts.googleapis", "fonts.gstatic", "tailwindcss", "material-symbols", "fetch(", "XMLHttpRequest", "WebSocket", "EventSource"]

found_forbidden = False
for root, _, files in os.walk(target_dir):
    for f in files:
        if not f.endswith((".html", ".js", ".css")): continue
        path = os.path.join(root, f)
        with open(path, 'r', encoding='utf-8', errors='ignore') as file:
            for i, line in enumerate(file):
                for patt in forbidden:
                    if patt.lower() in line.lower():
                        print(f"FORBIDDEN '{patt}' found in {path}:{i+1}: {line.strip()[:100]}")
                        found_forbidden = True

if found_forbidden:
    print("Pre-QA Scan: BLOCKED - Forbidden patterns found.")
else:
    print("Pre-QA Scan: PASS")
