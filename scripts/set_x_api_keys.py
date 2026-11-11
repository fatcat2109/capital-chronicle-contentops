"""Run by Jim in his own terminal; prompt without echo, store names only in output."""
from __future__ import annotations

import argparse
import ctypes
from getpass import getpass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live_contentops.secret_store_v1 import CRED_TYPE_GENERIC, TARGET_PREFIX, _api

NAMES = ("X_API_KEY", "X_API_KEY_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET")


def store_key(name, value):
    api = _api()
    if api is None:
        raise RuntimeError("WINDOWS_CREDENTIAL_MANAGER_UNAVAILABLE")
    _ctypes, wintypes, credential_type, *_ = api
    raw = value.encode("utf-16-le")
    blob = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
    record = credential_type()
    record.Type = CRED_TYPE_GENERIC
    record.TargetName = TARGET_PREFIX + name
    record.UserName = "Capitalnicle"
    record.Persist = 2  # CRED_PERSIST_LOCAL_MACHINE for this Windows user.
    record.CredentialBlobSize = len(raw)
    record.CredentialBlob = ctypes.cast(blob, ctypes.POINTER(ctypes.c_ubyte))
    write = ctypes.WinDLL("advapi32", use_last_error=True).CredWriteW
    write.argtypes = [ctypes.POINTER(credential_type), wintypes.DWORD]
    write.restype = wintypes.BOOL
    if not write(ctypes.byref(record), 0):
        raise RuntimeError("WINDOWS_CREDENTIAL_WRITE_FAILED")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", choices=NAMES, help="Omit to enter all four keys in one action")
    args = parser.parse_args()
    if not sys.stdin.isatty():
        parser.error("Run this yourself in an interactive terminal; piped secrets are refused")
    for name in (args.name,) if args.name else NAMES:
        value = getpass(name + " (hidden): ")
        if not value.strip():
            raise SystemExit("EMPTY_KEY_NOT_STORED: " + name)
        store_key(name, value.strip())
        value = None
        print("Stored " + TARGET_PREFIX + name)


if __name__ == "__main__":
    main()
