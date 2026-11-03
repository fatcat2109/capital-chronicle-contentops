"""CC-149: detach the article mirror after a confirmed CC-135 append.

The hook never builds, waits for a child, writes an outlet or changes a schedule.
Its failure is destination-local and cannot undo canonical publication or social.
"""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

FEED = Path(r"A:\Capital Chronicle\Runtime\ContentOps\published_content_v1.jsonl")
CONFIG = Path(__file__).resolve().parents[1] / "config/public_preview_mirror_v1.json"


def launch_preview_mirror(feed):
    try:
        if Path(feed).resolve() != FEED.resolve():
            return {"status": "SKIPPED", "cause": "NONPRODUCTION_FEED"}
        config = json.loads(CONFIG.read_bytes())
        if (set(config) != {"schema", "consumer_root", "consumer_module_sha256"}
                or config["schema"] != "contentops.preview_mirror_binding.v1"):
            return {"status": "NOT_STARTED", "cause": "BINDING_INVALID"}
        root = Path(config["consumer_root"])
        if not root.is_absolute():
            return {"status": "NOT_STARTED", "cause": "BINDING_INVALID"}
        module = root / "tools/product/republish_preview_articles_v1.py"
        if sha256(module.read_bytes()).hexdigest() != config["consumer_module_sha256"]:
            return {"status": "NOT_STARTED", "cause": "CONSUMER_SOURCE_CHANGED"}
        pythonw = Path(sys.executable).with_name("pythonw.exe")
        if os.name != "nt" or not pythonw.is_file():
            return {"status": "NOT_STARTED", "cause": "PYTHONW_REQUIRED"}
        child = subprocess.Popen(
            [str(pythonw), "-E", "-m", "tools.product.republish_preview_articles_v1",
             "--execute", "--record", str(FEED)], cwd=root, shell=False,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            close_fds=True, creationflags=(subprocess.DETACHED_PROCESS
                                         | subprocess.CREATE_NEW_PROCESS_GROUP
                                         | subprocess.CREATE_NO_WINDOW),
        )
        return {"status": "STARTED", "pid": child.pid}
    except Exception:
        # Do not print config, paths, environments or subprocess error bodies.
        return {"status": "NOT_STARTED", "cause": "PREVIEW_HOOK_UNAVAILABLE"}
