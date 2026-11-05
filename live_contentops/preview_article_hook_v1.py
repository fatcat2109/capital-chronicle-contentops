"""CC-149: detach the article mirror after a confirmed CC-135 append.

The hook never builds, waits for a child, writes an outlet or changes a schedule.
Its failure is destination-local and cannot undo canonical publication or social.
"""
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

FEED = Path(r"A:\Capital Chronicle\Runtime\ContentOps\published_content_v1.jsonl")
CONFIG = Path(__file__).resolve().parents[1] / "config/public_preview_mirror_v1.json"


def _open_worker_log(path):
    """The worker log, opened so every worker's output lands at its end (CC-248, 5 Nov).

    A detached worker writes through the handle it inherits. A write handle keeps the offset it
    had at launch, so on 5 Nov the worker queued at 02:28Z wrote its UNCHANGED result over the
    PUBLISHED result of the worker started at 00:34Z, from the same byte. A Windows handle with
    FILE_APPEND_DATA and no FILE_WRITE_DATA can only add to the end of the file.
    """
    if os.name != "nt":
        return open(path, "ab")  # POSIX O_APPEND already appends in the child.

    def append_only(name, flags):
        import _winapi
        import msvcrt
        handle = _winapi.CreateFile(
            str(name),
            0x0004 | 0x0080 | 0x00100000,  # FILE_APPEND_DATA | FILE_READ_ATTRIBUTES | SYNCHRONIZE
            0x0001 | 0x0002 | 0x0004,      # share read, write and delete
            0, 4, 0x80, 0)                 # no security attributes, OPEN_ALWAYS, normal file
        return msvcrt.open_osfhandle(handle, os.O_APPEND)

    return open(path, "ab", opener=append_only)


def launch_preview_mirror(feed):
    try:
        if Path(feed).resolve() != FEED.resolve():
            return {"status": "SKIPPED", "cause": "NONPRODUCTION_FEED"}
        config = json.loads(CONFIG.read_bytes())
        required = {"schema", "consumer_root", "consumer_module_sha256"}
        if (not required <= set(config) <= required | {"worker_python"}
                or config["schema"] != "contentops.preview_mirror_binding.v1"):
            return {"status": "NOT_STARTED", "cause": "BINDING_INVALID"}
        root = Path(config["consumer_root"])
        if not root.is_absolute():
            return {"status": "NOT_STARTED", "cause": "BINDING_INVALID"}
        module = root / "tools/product/republish_preview_articles_v1.py"
        actual_hash = sha256(module.read_bytes()).hexdigest()
        # CC-254 review: a changed public-write worker is executable code drift,
        # not a model/effort label. Review and rebind it before it can publish.
        if actual_hash != config["consumer_module_sha256"]:
            return {"status": "NOT_STARTED", "cause": "CONSUMER_SOURCE_CHANGED",
                    "consumer_module_sha256": actual_hash}
        dependencies = root / "ui/node_modules"
        if not dependencies.is_dir():
            return {"status": "NOT_STARTED", "cause": "CONSUMER_NODE_DEPENDENCIES_MISSING"}
        if dependencies.resolve() != dependencies.absolute():
            return {"status": "NOT_STARTED", "cause": "CONSUMER_NODE_DEPENDENCIES_SHARED"}
        pythonw = Path(sys.executable).with_name("pythonw.exe")
        if os.name != "nt" or not pythonw.is_file():
            return {"status": "NOT_STARTED", "cause": "PYTHONW_REQUIRED"}
        # Probe the appending interpreter with the child's -E flag and cwd.
        # A missing dependency must be a named result, not a silent child exit.
        def has_jsonschema(python):
            probe = subprocess.run([str(python), "-E", "-c", "import jsonschema"],
                                   cwd=root, shell=False, capture_output=True, timeout=10,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
            return probe.returncode == 0

        fallback = None
        if not has_jsonschema(sys.executable):
            # The ContentOps runtime venv has no jsonschema (Ops Product, 5 Nov: install nothing
            # there). Use the runbook's system Python instead: the configured one, else `python`
            # on PATH. Each candidate is checked (python and pythonw present, jsonschema imports);
            # Store aliases never run.
            seen = {str(Path(sys.executable).resolve()).casefold()}
            for candidate in (config.get("worker_python"), shutil.which("python")):
                if not candidate:
                    continue
                python = Path(candidate)
                key = str(python.resolve()).casefold()
                if key in seen or "\\windowsapps\\" in key:
                    continue
                seen.add(key)
                if (python.is_file() and python.with_name("pythonw.exe").is_file()
                        and has_jsonschema(python)):
                    fallback = python
                    break
            if fallback is None:
                return {"status": "NOT_STARTED", "cause": "CONSUMER_PYTHON_DEPENDENCY_MISSING:jsonschema"}
            pythonw = fallback.with_name("pythonw.exe")
        with _open_worker_log(FEED.with_name("preview_article_worker.log")) as log:
            child = subprocess.Popen(
            [str(pythonw), "-E", "-m", "tools.product.republish_preview_articles_v1",
             "--execute", "--record", str(FEED)], cwd=root, shell=False,
            stdin=subprocess.DEVNULL, stdout=log, stderr=log,
            close_fds=True, creationflags=(subprocess.DETACHED_PROCESS
                                         | subprocess.CREATE_NEW_PROCESS_GROUP
                                         | subprocess.CREATE_NO_WINDOW),
            )
        return {"status": "STARTED", "pid": child.pid,
                "consumer_module_sha256": actual_hash,
                "configured_consumer_module_sha256": config["consumer_module_sha256"],
                **({"worker_python_fallback": str(fallback)} if fallback else {})}
    except Exception:
        # Do not print config, paths, environments or subprocess error bodies.
        return {"status": "NOT_STARTED", "cause": "PREVIEW_HOOK_UNAVAILABLE"}
