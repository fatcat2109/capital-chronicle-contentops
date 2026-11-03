"""Reject new base64 image evidence without printing its contents.

Default: staged additions/changes. --base/--head: a bounded commit range.
Historical files outside that change are never rewritten or dumped.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".pdf", ".gz", ".zip"}
IMAGE_HEADERS = {".png": (b"\x89PNG\r\n\x1a\n",), ".jpg": (b"\xff\xd8\xff",),
    ".jpeg": (b"\xff\xd8\xff",), ".gif": (b"GIF87a", b"GIF89a"), ".bmp": (b"BM",)}
IMAGE_TEXT = re.compile(rb"data:image/[a-zA-Z0-9.+-]+;base64,|(?:iVBORw0KGgo|/9j/)[A-Za-z0-9+/=]{96,}")


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def check(root, *, base=None, head="HEAD"):
    args = ["diff", "--name-only", "--diff-filter=ACM", "-z"]
    args += [base, head] if base else ["--cached"]
    failures = []
    for raw in git(root, *args).split(b"\0"):
        if not raw:
            continue
        path = raw.decode("utf-8")
        suffix = Path(path).suffix.lower()
        if suffix in {".b64", ".base64"}:
            failures.append((path, "BASE64_IMAGE_SIDECAR_FORBIDDEN"))
            continue
        if suffix in IMAGE_SUFFIXES - {*IMAGE_HEADERS, ".webp"}:
            continue
        identity = f"{head}:{path}" if base else f":{path}"
        # Stream bounded chunks. Even a giant historical blob never enters stdout
        # or a single in-memory buffer in this guard.
        matched, tail, header = False, b"", b""
        with subprocess.Popen(["git", "-C", str(root), "cat-file", "blob", identity], stdout=subprocess.PIPE) as proc:
            while chunk := proc.stdout.read(65536):
                if not header:
                    header = chunk[:16]
                window = tail + chunk
                matched |= bool(IMAGE_TEXT.search(window))
                tail = window[-256:]
            if proc.wait() != 0:
                raise RuntimeError("GIT_EVIDENCE_BLOB_READ_FAILED:" + path)
        if suffix in IMAGE_HEADERS or suffix == ".webp":
            valid = (header.startswith(b"RIFF") and header[8:12] == b"WEBP") if suffix == ".webp" else header.startswith(IMAGE_HEADERS[suffix])
            if not valid:
                failures.append((path, "BINARY_IMAGE_MAGIC_REQUIRED"))
        elif matched:
            failures.append((path, "EMBEDDED_BASE64_IMAGE_FORBIDDEN"))
    return failures


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--base")
    parser.add_argument("--head", default="HEAD")
    args = parser.parse_args(argv)
    failures = check(args.root, base=args.base, head=args.head)
    for path, cause in failures:
        print(cause + ": " + path)
    if not failures:
        print("PASS_BINARY_EVIDENCE")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
