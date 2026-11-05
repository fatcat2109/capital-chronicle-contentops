"""One secret reader for ContentOps (CC-297): Credential Manager, then the live user environment,
then the process environment.

A key NAME is read, in this order, from:

1. the Windows generic credential ``CapitalChronicle/NAME`` (the blob is UTF-16LE when typed in the
   Windows "Add a generic credential" dialog or written by ``cmdkey``; UTF-8 blobs are read too);
2. the live user environment in the registry (``HKCU\\Environment``), because a long-running
   process (lane runners, the daily app and the Codex children they start) keeps the values it
   started with, which are stale after a key is rotated;
3. the process environment (``os.environ``, or the mapping a caller passes), while keys move.

Rules this module keeps:

- a value is read at the call: nothing is cached, written to disk, copied into a child process's
  environment, logged or printed;
- errors and reprs name the key, never its value;
- presence helpers return booleans and names only.

In a pytest process, or under ``CAPITAL_CHRONICLE_SECRET_STORE=environment-only``, the reader skips
Credential Manager and the registry, so a unit test can never pick up a real key and post with it.
"""
from __future__ import annotations

import os
import sys
from typing import Any, Callable, Iterable, Iterator, Mapping, Optional, Tuple

TARGET_PREFIX = "CapitalChronicle/"
STORE_MODE_ENV = "CAPITAL_CHRONICLE_SECRET_STORE"
ENVIRONMENT_ONLY = "environment-only"
CREDENTIAL_MANAGER_MODE = "credential-manager"

SOURCE_CREDENTIAL_MANAGER = "CREDENTIAL_MANAGER"
SOURCE_USER_ENVIRONMENT = "USER_ENVIRONMENT"          # HKCU\Environment, read live
SOURCE_PROCESS_ENVIRONMENT = "PROCESS_ENVIRONMENT"    # os.environ or the caller's mapping
SOURCE_MISSING = "MISSING"

STORE_FOUND = "FOUND"
STORE_NOT_FOUND = "NOT_FOUND"
STORE_DISABLED = "DISABLED"
STORE_UNAVAILABLE = "UNAVAILABLE"   # not Windows, or advapi32 could not load
STORE_UNREADABLE = "UNREADABLE"     # the blob is neither UTF-16LE nor UTF-8 text

CRED_TYPE_GENERIC = 1
ERROR_NOT_FOUND = 1168
_ERROR_NAMES = {
    5: "ACCESS_DENIED",
    87: "INVALID_PARAMETER",
    1004: "INVALID_FLAGS",
    1168: "NOT_FOUND",
    1312: "NO_SUCH_LOGON_SESSION",
}

# A store reader takes the full target name and returns (status, value or None).
StoreReader = Callable[[str], Tuple[str, Optional[str]]]
StoreLister = Callable[[str], Tuple[str, Tuple[Tuple[str, str], ...]]]
# A user-environment reader takes a variable name and returns its live value or None.
UserEnvReader = Callable[[str], Optional[str]]


class SecretMissingError(KeyError):
    """A required key is in none of the three sources. Names only."""

    def __init__(self, name: str, store_status: str = STORE_NOT_FOUND) -> None:
        super().__init__(name)
        self.name = name
        self.store_status = store_status

    def __str__(self) -> str:
        return (
            f"{self.name} is missing: Windows credential {TARGET_PREFIX}{self.name} "
            f"{self.store_status}, and no user or process environment variable {self.name}"
        )


# --- Windows Credential Manager (ctypes, no new dependency) -------------------------------------

_API: Any = None


def _api() -> Any:
    """Load advapi32 once; None off Windows or when it cannot load."""
    global _API
    if _API is not None:
        return _API or None
    if os.name != "nt":
        _API = False
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class CREDENTIALW(ctypes.Structure):
            _fields_ = [
                ("Flags", wintypes.DWORD),
                ("Type", wintypes.DWORD),
                ("TargetName", wintypes.LPWSTR),
                ("Comment", wintypes.LPWSTR),
                ("LastWritten", wintypes.FILETIME),
                ("CredentialBlobSize", wintypes.DWORD),
                ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
                ("Persist", wintypes.DWORD),
                ("AttributeCount", wintypes.DWORD),
                ("Attributes", ctypes.c_void_p),
                ("TargetAlias", wintypes.LPWSTR),
                ("UserName", wintypes.LPWSTR),
            ]

        advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
        cred_read = advapi32.CredReadW
        cred_read.argtypes = [
            wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
            ctypes.POINTER(ctypes.POINTER(CREDENTIALW)),
        ]
        cred_read.restype = wintypes.BOOL
        cred_enumerate = advapi32.CredEnumerateW
        cred_enumerate.argtypes = [
            wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(ctypes.POINTER(ctypes.POINTER(CREDENTIALW))),
        ]
        cred_enumerate.restype = wintypes.BOOL
        cred_free = advapi32.CredFree
        cred_free.argtypes = [ctypes.c_void_p]
        cred_free.restype = None
        _API = (ctypes, wintypes, CREDENTIALW, cred_read, cred_enumerate, cred_free)
    except (OSError, AttributeError):
        _API = False
        return None
    return _API


def _error_status(code: int) -> str:
    return "ERROR_" + _ERROR_NAMES.get(int(code), str(int(code)))


def _decode_blob(blob: bytes) -> Optional[str]:
    """UTF-16LE (Windows dialog, cmdkey) or UTF-8; trailing NULs and edge whitespace dropped."""
    if not blob:
        return ""
    text: Optional[str] = None
    if len(blob) % 2 == 0 and not any(blob[1::2]):
        text = blob.decode("utf-16-le")          # ASCII text stored as UTF-16LE
    else:
        try:
            text = blob.decode("utf-8")
        except UnicodeDecodeError:
            if len(blob) % 2 == 0:
                try:
                    text = blob.decode("utf-16-le")
                except UnicodeDecodeError:
                    text = None
    if text is None:
        return None
    return text.strip("\x00").strip()


def _blob_of(api: Any, credential: Any) -> bytes:
    ctypes = api[0]
    size = int(credential.CredentialBlobSize)
    if not size or not credential.CredentialBlob:
        return b""
    return ctypes.string_at(credential.CredentialBlob, size)


def windows_store_read(target: str) -> Tuple[str, Optional[str]]:
    """Read one generic credential. Returns (status, value); the value never leaves the caller."""
    api = _api()
    if api is None:
        return STORE_UNAVAILABLE, None
    ctypes, _wintypes, CREDENTIALW, cred_read, _enumerate, cred_free = api
    pointer = ctypes.POINTER(CREDENTIALW)()
    if not cred_read(target, CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)):
        code = ctypes.get_last_error()
        return (STORE_NOT_FOUND if code == ERROR_NOT_FOUND else _error_status(code)), None
    try:
        value = _decode_blob(_blob_of(api, pointer.contents))
    finally:
        cred_free(pointer)
    if value is None:
        return STORE_UNREADABLE, None
    return STORE_FOUND, value


def windows_store_list(prefix: str) -> Tuple[str, Tuple[Tuple[str, str], ...]]:
    """All generic credentials under ``prefix`` as (target, value); for leak guards and names."""
    api = _api()
    if api is None:
        return STORE_UNAVAILABLE, ()
    ctypes, wintypes, CREDENTIALW, _read, cred_enumerate, cred_free = api
    count = wintypes.DWORD(0)
    array = ctypes.POINTER(ctypes.POINTER(CREDENTIALW))()
    if not cred_enumerate(prefix + "*", 0, ctypes.byref(count), ctypes.byref(array)):
        code = ctypes.get_last_error()
        return (STORE_NOT_FOUND if code == ERROR_NOT_FOUND else _error_status(code)), ()
    rows = []
    try:
        for index in range(int(count.value)):
            credential = array[index].contents
            if int(credential.Type) != CRED_TYPE_GENERIC:
                continue
            target = str(credential.TargetName or "")
            if not target.startswith(prefix):
                continue
            value = _decode_blob(_blob_of(api, credential))
            rows.append((target, value if value is not None else ""))
    finally:
        cred_free(array)
    return STORE_FOUND, tuple(rows)


def windows_user_env_read(name: str) -> Optional[str]:
    """The live value of one user environment variable (``HKCU\\Environment``), or None."""
    if os.name != "nt":
        return None
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, kind = winreg.QueryValueEx(key, name)
    except (OSError, ImportError):
        return None
    if value is None:
        return None
    text = str(value)
    if kind == winreg.REG_EXPAND_SZ and "%" in text:
        text = winreg.ExpandEnvironmentStrings(text)
    return text


# --- The reader ---------------------------------------------------------------------------------

def store_enabled() -> bool:
    """Whether the default readers (Credential Manager, then HKCU\\Environment) are used.

    Off under ``CAPITAL_CHRONICLE_SECRET_STORE=environment-only``, and off by default in any pytest
    process even when a test clears the environment: a test that removes a key to exercise the
    "missing" path must never read Jim's live key instead and post with it. A test that proves the
    real store sets ``CAPITAL_CHRONICLE_SECRET_STORE=credential-manager`` or passes readers.
    """
    mode = str(os.environ.get(STORE_MODE_ENV) or "").strip().lower()
    if mode == ENVIRONMENT_ONLY:
        return False
    if mode == CREDENTIAL_MANAGER_MODE:
        return True
    return "_pytest" not in sys.modules


def _check_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip() or any(ch in name for ch in "\x00*?"):
        raise ValueError("secret_name_invalid")
    return name.strip()


def _lookup(name: str, env: Optional[Mapping[str, str]], store: Optional[StoreReader],
            user_env: Optional[UserEnvReader]) -> Tuple[str, Optional[str], str]:
    """(source, value, store_status). Explicit readers are used as given; the defaults honour the mode."""
    name = _check_name(name)
    enabled = store_enabled()
    if store is None and not enabled:
        status, value = STORE_DISABLED, None
    else:
        status, value = (store or windows_store_read)(TARGET_PREFIX + name)
    if status == STORE_FOUND and value:
        return SOURCE_CREDENTIAL_MANAGER, value, status
    if user_env is not None or enabled:
        live = (user_env or windows_user_env_read)(name)
        if live is not None and str(live) != "":
            return SOURCE_USER_ENVIRONMENT, str(live), status
    environment = os.environ if env is None else env
    env_value = environment.get(name)
    if env_value is not None and str(env_value) != "":
        return SOURCE_PROCESS_ENVIRONMENT, str(env_value), status
    return SOURCE_MISSING, None, status


def read_secret(name: str, *, env: Optional[Mapping[str, str]] = None, store: Optional[StoreReader] = None,
                user_env: Optional[UserEnvReader] = None) -> Optional[str]:
    """The value of ``name`` (Credential Manager, then HKCU\\Environment, then the process), or None."""
    return _lookup(name, env, store, user_env)[1]


def require_secret(name: str, *, env: Optional[Mapping[str, str]] = None, store: Optional[StoreReader] = None,
                   user_env: Optional[UserEnvReader] = None) -> str:
    """Like read_secret, but a missing key raises SecretMissingError naming the key only."""
    source, value, status = _lookup(name, env, store, user_env)
    if source == SOURCE_MISSING or value is None:
        raise SecretMissingError(_check_name(name), status)
    return value


def first_secret(*names: str, env: Optional[Mapping[str, str]] = None, store: Optional[StoreReader] = None,
                 user_env: Optional[UserEnvReader] = None) -> str:
    """The first non-blank value among ``names`` in order (each name through all sources), else ''."""
    for name in names:
        value = read_secret(name, env=env, store=store, user_env=user_env)
        if value and value.strip():
            return value.strip()
    return ""


def secret_present(name: str, *, env: Optional[Mapping[str, str]] = None, store: Optional[StoreReader] = None,
                   user_env: Optional[UserEnvReader] = None) -> bool:
    value = read_secret(name, env=env, store=store, user_env=user_env)
    return bool(value and value.strip())


def secret_source(name: str, *, env: Optional[Mapping[str, str]] = None, store: Optional[StoreReader] = None,
                  user_env: Optional[UserEnvReader] = None) -> dict[str, str]:
    """Where ``name`` would be read from, names and states only (no value, length or digest)."""
    source, _value, status = _lookup(name, env, store, user_env)
    return {"name": _check_name(name), "source": source, "credential_manager": status}


class SecretEnvironment:
    """A read view for code written against an env mapping: ``get``, ``[]`` and ``in`` read each
    name from Credential Manager, then the live user environment, then the process environment.

    It is deliberately not iterable: it can never be copied into a dict or passed as a child
    process's environment (use ``os.environ`` for that).
    """

    __slots__ = ("_env", "_store", "_user_env")

    def __init__(self, env: Optional[Mapping[str, str]] = None, store: Optional[StoreReader] = None,
                 user_env: Optional[UserEnvReader] = None) -> None:
        self._env = env
        self._store = store
        self._user_env = user_env

    def _read(self, name: str) -> Optional[str]:
        return read_secret(name, env=self._env, store=self._store, user_env=self._user_env)

    def get(self, name: str, default: Any = None) -> Any:
        value = self._read(name)
        return default if value is None else value

    def __getitem__(self, name: str) -> str:
        value = self._read(name)
        if value is None:
            raise KeyError(name)
        return value

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and self._read(name) is not None

    def __iter__(self) -> Iterator[str]:
        raise TypeError("SecretEnvironment is not iterable: read names with get(); child processes use os.environ")

    def __len__(self) -> int:
        raise TypeError("SecretEnvironment has no length: read names with get()")

    def __repr__(self) -> str:
        return "SecretEnvironment(credential_manager_then_user_then_process_environment)"


def secret_environment(env: Optional[Mapping[str, str]] = None, store: Optional[StoreReader] = None,
                       user_env: Optional[UserEnvReader] = None) -> SecretEnvironment:
    return SecretEnvironment(env, store, user_env)


def stored_secret_names(*, lister: Optional[StoreLister] = None) -> list[str]:
    """Names held under ``CapitalChronicle/`` in Credential Manager (names only)."""
    if lister is None and not store_enabled():
        return []
    status, rows = (lister or windows_store_list)(TARGET_PREFIX)
    if status != STORE_FOUND:
        return []
    return sorted({target[len(TARGET_PREFIX):] for target, _value in rows if target[len(TARGET_PREFIX):]})


def leaked_secret_names(text: str, *, env: Optional[Mapping[str, str]] = None,
                        env_names: Iterable[str] = (), minimum_length: int = 12,
                        lister: Optional[StoreLister] = None,
                        user_env: Optional[UserEnvReader] = None) -> list[str]:
    """Names whose stored value, or (for ``env_names``) live user or process value, occurs in ``text``.

    For output leak guards: the values stay in this function; only names come back.
    """
    found: set[str] = set()
    if text:
        enabled = store_enabled()
        rows: Tuple[Tuple[str, str], ...] = ()
        if lister is not None or enabled:
            status, rows = (lister or windows_store_list)(TARGET_PREFIX)
            if status != STORE_FOUND:
                rows = ()
        for target, value in rows:
            if value and len(value) >= minimum_length and value in text:
                found.add(target[len(TARGET_PREFIX):])
        environment = os.environ if env is None else env
        live_reader = user_env or (windows_user_env_read if enabled else None)
        for name in env_names:
            candidates = [environment.get(name)]
            if live_reader is not None:
                candidates.append(live_reader(name))
            for value in candidates:
                if value and len(str(value)) >= minimum_length and str(value) in text:
                    found.add(name)
    return sorted(found)


if __name__ == "__main__":  # pragma: no cover - names and states only
    for argument in sys.argv[1:]:
        state = secret_source(argument)
        print(f"{state['name']}: {state['source']} (credential manager {state['credential_manager']})")
