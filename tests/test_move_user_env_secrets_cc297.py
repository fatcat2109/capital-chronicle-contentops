"""CC-297: tools/secrets/move_user_env_secrets.ps1 on dummy user variables only.

It creates CC297_TEST_DUMMY_VAR_* values in HKCU\\Environment and CapitalChronicle/CC297_TEST_DUMMY_VAR_*
credentials, runs the script in PowerShell 7 and Windows PowerShell 5.1, and removes every dummy.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from live_contentops import secret_store_v1 as reader

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows user environment and Credential Manager only")

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "secrets" / "move_user_env_secrets.ps1"
SHELLS = [
    shell for shell in (
        shutil.which("pwsh") or r"C:\Program Files\PowerShell\7\pwsh.exe",
        r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
    ) if shell and Path(shell).exists()
]


def _user_set(name: str, value: str) -> None:
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)


def _user_has(name: str) -> bool:
    return reader.windows_user_env_read(name) is not None


def _user_delete(name: str) -> None:
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, name)
    except FileNotFoundError:
        pass


def _advapi32():
    import ctypes
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    CREDENTIALW = reader._api()[2]
    advapi32.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIALW), wintypes.DWORD]
    advapi32.CredWriteW.restype = wintypes.BOOL
    advapi32.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    advapi32.CredDeleteW.restype = wintypes.BOOL
    return ctypes, advapi32, CREDENTIALW


def _cred_write(name: str, value: str) -> None:
    """A dummy generic credential stored as the Windows dialog stores it (UTF-16LE)."""
    ctypes, advapi32, CREDENTIALW = _advapi32()
    blob = value.encode("utf-16-le")
    buffer = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
    credential = CREDENTIALW()
    credential.Type = reader.CRED_TYPE_GENERIC
    credential.TargetName = reader.TARGET_PREFIX + name
    credential.UserName = name
    credential.CredentialBlobSize = len(blob)
    credential.CredentialBlob = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
    credential.Persist = 2
    assert advapi32.CredWriteW(ctypes.byref(credential), 0), ctypes.get_last_error()


def _cred_delete(name: str) -> None:
    _ctypes, advapi32, _ = _advapi32()
    advapi32.CredDeleteW(reader.TARGET_PREFIX + name, reader.CRED_TYPE_GENERIC, 0)


def _stored(name: str):
    return reader.windows_store_read(reader.TARGET_PREFIX + name)


def _run(shell: str, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT), *arguments],
        capture_output=True, text=True, timeout=180, stdin=subprocess.DEVNULL,
    )


def _line(output: str, name: str) -> str:
    rows = [row for row in output.splitlines() if f" {name} " in f" {row} " or row.split()[1:2] == [name]]
    return rows[0] if rows else ""


@pytest.mark.parametrize("shell", SHELLS, ids=[Path(shell).stem for shell in SHELLS])
def test_move_delete_conflict_wildcard_and_names_only(shell):
    tag = f"CC297_TEST_DUMMY_VAR_{os.getpid()}_{Path(shell).stem.upper()}"
    names = {case: f"{tag}_{case}" for case in ("A", "B", "C", "D", "E", "W1", "W2")}
    values = {case: f"cc297-dummy-{case.lower()}-{os.getpid()}-not-a-secret" for case in names}
    try:
        for case in ("A", "B", "C", "D", "W1", "W2"):
            _user_set(names[case], values[case])
        _cred_write(names["C"], "cc297-dummy-older-different-value")   # conflict: a different stored value
        _cred_write(names["D"], values["D"])                             # already stored, same value
        result = _run(shell, "-Move", ",".join([names["A"], names["C"], names["D"], names["E"], f"{tag}_W*"]),
                      "-Delete", names["B"])
        output = result.stdout + result.stderr
        for value in values.values():
            assert value not in output                                    # names and states only
        assert "cc297-dummy-older-different-value" not in output
        assert result.returncode == 1, result.returncode                  # the conflict is a FAIL
        assert _line(output, names["A"]).startswith("OK ")
        assert _line(output, names["B"]).startswith("OK ")
        assert _line(output, names["C"]).startswith("FAIL ")
        assert _line(output, names["D"]).startswith("OK ")
        assert _line(output, names["E"]).startswith("SKIP ")
        assert _line(output, names["W1"]).startswith("OK ") and _line(output, names["W2"]).startswith("OK ")
        assert "Moved 4, deleted 1, skipped 1, failed 1." in output
        # Moved: in Credential Manager with the same value (UTF-16LE), gone from the user environment.
        for case in ("A", "W1", "W2"):
            status, stored = _stored(names[case])
            assert status == reader.STORE_FOUND and stored == values[case], case
            assert not _user_has(names[case]), case
        # Deleted: gone, stored nowhere. Already stored: user variable gone, credential unchanged.
        assert not _user_has(names["B"]) and _stored(names["B"])[0] == reader.STORE_NOT_FOUND
        assert not _user_has(names["D"]) and _stored(names["D"]) == (reader.STORE_FOUND, values["D"])
        # Conflict: nothing changed for that name.
        assert _user_has(names["C"])
        assert _stored(names["C"]) == (reader.STORE_FOUND, "cc297-dummy-older-different-value")
        # The reader now finds a moved key in Credential Manager.
        os.environ.pop(names["A"], None)
        assert reader.read_secret(names["A"], store=reader.windows_store_read, user_env=reader.windows_user_env_read) == values["A"]
    finally:
        for name in names.values():
            _user_delete(name)
            _cred_delete(name)


@pytest.mark.parametrize("shell", SHELLS[:1], ids=[Path(shell).stem for shell in SHELLS[:1]])
def test_dry_run_changes_nothing(shell):
    name = f"CC297_TEST_DUMMY_VAR_{os.getpid()}_DRY"
    value = f"cc297-dummy-dry-{os.getpid()}-not-a-secret"
    try:
        _user_set(name, value)
        result = _run(shell, "-Move", name, "-DryRun")
        output = result.stdout + result.stderr
        assert result.returncode == 0, result.returncode
        assert value not in output
        assert _line(output, name).startswith("OK ") and "would move" in _line(output, name)
        assert "Dry run, nothing changed." in output
        assert _user_has(name)
        assert _stored(name)[0] == reader.STORE_NOT_FOUND
        nothing = _run(shell)
        assert nothing.returncode == 2 and "Nothing to do" in nothing.stdout
    finally:
        _user_delete(name)
        _cred_delete(name)
