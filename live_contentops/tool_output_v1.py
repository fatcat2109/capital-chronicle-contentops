"""Keep large tool results and image bytes in files, never in the session (CC-172).

This is an output adapter, not a publication or evidence store. Small ordinary
CLI output keeps its existing format. Large results return a file reference.
"""
from __future__ import annotations

import base64
import builtins
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

MAX_OUTPUT_BYTES = 10 * 1024
_BASE64 = re.compile(r"data:[^;,\s]+;base64,([A-Za-z0-9+/]+={0,2})|([A-Za-z0-9+/]{10240,}={0,2})")


def _save(data: bytes, *, kind: str, output_dir: Path | None):
    root = Path(output_dir) if output_dir else Path(tempfile.gettempdir()) / "CapitalChronicle" / "tool-output"
    root.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(data).hexdigest()
    path = root / (digest + (".bin" if kind == "binary" else ".json" if kind == "json" else ".txt"))
    # Atomic replacement means readers never receive a partially written result.
    with tempfile.NamedTemporaryFile(dir=root, delete=False) as stream:
        stream.write(data)
        temporary = stream.name
    os.replace(temporary, path)
    value = {"path": str(path.resolve()), "size_bytes": len(data), "sha256": digest, "kind": kind}
    if kind == "binary":
        try:
            from PIL import Image
            with Image.open(path) as image:
                value["width"], value["height"] = image.size
        except (OSError, ValueError):
            pass
    return value


def _externalize(value, output_dir):
    if isinstance(value, bytes):
        return _save(value, kind="binary", output_dir=output_dir)
    if isinstance(value, dict):
        return {k: _externalize(v, output_dir) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_externalize(v, output_dir) for v in value]
    if isinstance(value, str):
        # A base64 field is persisted as its original binary, not as a sidecar.
        match = _BASE64.fullmatch(value)
        if match:
            try:
                data = base64.b64decode(match[1] or match[2], validate=True)
            except ValueError:
                return value
            if match[1] or len(data) > MAX_OUTPUT_BYTES or len(value.encode("utf-8")) > MAX_OUTPUT_BYTES:
                return _save(data, kind="binary", output_dir=output_dir)
    return value


def safe_print(*values, sep=" ", end="\n", file=None, flush=False, output_dir=None):
    """print-compatible CLI boundary; emitted payload never exceeds 10 KB.

    Callers can still read the full JSON from the returned path. No truncation
    silently loses a pending native request, article or publication observation.
    """
    rendered = []
    for value in values:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except (ValueError, TypeError):
                parsed = value
            cleaned = _externalize(parsed, output_dir)
            rendered.append(value if cleaned == parsed else json.dumps(cleaned, ensure_ascii=True))
        elif isinstance(value, bytes):
            rendered.append(json.dumps(_externalize(value, output_dir)))
        elif isinstance(value, (dict, list, tuple)):
            rendered.append(json.dumps(_externalize(value, output_dir), ensure_ascii=True))
        else:
            rendered.append(str(value))
    text = sep.join(rendered)
    # Also cover small data URIs embedded in diagnostic prose.
    def replace(match):
        try:
            data = base64.b64decode(match[1] or match[2], validate=True)
        except ValueError:
            return match[0]
        return json.dumps(_save(data, kind="binary", output_dir=output_dir))
    text = _BASE64.sub(replace, text)
    if len((text + end).encode("utf-8")) > MAX_OUTPUT_BYTES:
        try:
            json.loads(text)
            kind = "json"
        except ValueError:
            kind = "text"
        reference = _save(text.encode("utf-8"), kind=kind, output_dir=output_dir)
        text = json.dumps({"classification": "TOOL_OUTPUT_IN_FILE", "output": reference})
        end = "\n"
    builtins.print(text, end=end, file=file, flush=flush)
