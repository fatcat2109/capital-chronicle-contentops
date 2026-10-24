"""Serial exact existing-owner advances: respects the shared Main consumption lease."""
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[4]
for slug in ('policy','tesla-r2','southwest-r2'):
    command=[sys.executable,'-X','utf8',str(ROOT/'bind_media_case.py'),slug]
    if slug=='policy':command.append('--reviewed')
    result=subprocess.run(command,cwd=REPO,text=True,capture_output=True)
    (ROOT/slug/'writer-freeze.stdout.txt').write_text(result.stdout,encoding='utf-8')
    (ROOT/slug/'writer-freeze.stderr.txt').write_text(result.stderr,encoding='utf-8')
    print(result.stdout,flush=True)
    if result.returncode:
        print(result.stderr,flush=True)
        raise SystemExit(result.returncode)
