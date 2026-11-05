"""CC-297: one secret reader (Credential Manager, then the live user environment, then the process).

Every value here is a dummy. The real-store tests write and delete only CapitalChronicle/CC297_TEST_DUMMY_*
credentials and CC297_TEST_DUMMY_VAR_* user variables.
"""
from __future__ import annotations

import os
import sys

import pytest

from live_contentops import secret_store_v1 as reader

DUMMY = "cc297-dummy-value-not-a-secret-7f3a"


def fake_store(values: dict[str, str], status_when_missing: str = reader.STORE_NOT_FOUND):
    calls: list[str] = []

    def read(target: str):
        calls.append(target)
        name = target[len(reader.TARGET_PREFIX):]
        if name in values:
            return reader.STORE_FOUND, values[name]
        return status_when_missing, None

    read.calls = calls  # type: ignore[attr-defined]
    return read


def fake_user_env(values: dict[str, str]):
    return lambda name: values.get(name)


# --- order ---------------------------------------------------------------------------------------

def test_credential_manager_wins_over_user_and_process_environment():
    value = reader.read_secret(
        "THREADS_USER_ACCESS_TOKEN",
        env={"THREADS_USER_ACCESS_TOKEN": "process-old"},
        store=fake_store({"THREADS_USER_ACCESS_TOKEN": "store-new"}),
        user_env=fake_user_env({"THREADS_USER_ACCESS_TOKEN": "user-rotated"}),
    )
    assert value == "store-new"


def test_live_user_environment_wins_over_a_stale_process_value():
    # A long-running process keeps the value it started with; the registry holds the rotated one.
    store = fake_store({})
    value = reader.read_secret(
        "THREADS_APP_SECRET",
        env={"THREADS_APP_SECRET": "process-old"},
        store=store,
        user_env=fake_user_env({"THREADS_APP_SECRET": "user-rotated"}),
    )
    assert value == "user-rotated"
    assert store.calls == ["CapitalChronicle/THREADS_APP_SECRET"]
    assert reader.secret_source(
        "THREADS_APP_SECRET", env={"THREADS_APP_SECRET": "x"}, store=store,
        user_env=fake_user_env({"THREADS_APP_SECRET": "y"}),
    )["source"] == reader.SOURCE_USER_ENVIRONMENT


def test_process_environment_is_the_last_source():
    value = reader.read_secret(
        "TELEGRAM_BOT_TOKEN", env={"TELEGRAM_BOT_TOKEN": "process-only"},
        store=fake_store({}), user_env=fake_user_env({}),
    )
    assert value == "process-only"
    state = reader.secret_source(
        "TELEGRAM_BOT_TOKEN", env={"TELEGRAM_BOT_TOKEN": "process-only"},
        store=fake_store({}), user_env=fake_user_env({}),
    )
    assert state == {"name": "TELEGRAM_BOT_TOKEN", "source": reader.SOURCE_PROCESS_ENVIRONMENT,
                     "credential_manager": reader.STORE_NOT_FOUND}


def test_blank_values_fall_through_to_the_next_source():
    value = reader.read_secret(
        "META_ACCESS_TOKEN", env={"META_ACCESS_TOKEN": "process"},
        store=fake_store({"META_ACCESS_TOKEN": ""}), user_env=fake_user_env({"META_ACCESS_TOKEN": ""}),
    )
    assert value == "process"


def test_a_store_error_falls_back_and_is_named():
    store = fake_store({}, status_when_missing="ERROR_NO_SUCH_LOGON_SESSION")
    assert reader.read_secret("CLOUDINARY_API_SECRET", env={"CLOUDINARY_API_SECRET": "p"},
                              store=store, user_env=fake_user_env({})) == "p"
    with pytest.raises(reader.SecretMissingError) as caught:
        reader.require_secret("CLOUDINARY_API_SECRET", env={}, store=store, user_env=fake_user_env({}))
    assert "ERROR_NO_SUCH_LOGON_SESSION" in str(caught.value)


def test_first_secret_keeps_each_names_precedence():
    # THREADS_USER_ACCESS_TOKEN (process) is preferred over the legacy THREADS_ACCESS_TOKEN (store).
    value = reader.first_secret(
        "THREADS_USER_ACCESS_TOKEN", "THREADS_ACCESS_TOKEN",
        env={"THREADS_USER_ACCESS_TOKEN": "  primary  "},
        store=fake_store({"THREADS_ACCESS_TOKEN": "legacy"}), user_env=fake_user_env({}),
    )
    assert value == "primary"
    assert reader.first_secret("A_TOKEN", "B_TOKEN", env={}, store=fake_store({}), user_env=fake_user_env({})) == ""


# --- missing keys fail by name, nothing is printed ----------------------------------------------

def test_missing_key_fails_by_name_without_any_value(capfd):
    env = {"OTHER_TOKEN": DUMMY}
    with pytest.raises(reader.SecretMissingError) as caught:
        reader.require_secret("THREADS_USER_ACCESS_TOKEN", env=env, store=fake_store({"OTHER": DUMMY}),
                              user_env=fake_user_env({"OTHER": DUMMY}))
    error = caught.value
    assert isinstance(error, KeyError)
    assert error.name == "THREADS_USER_ACCESS_TOKEN"
    assert "THREADS_USER_ACCESS_TOKEN" in str(error)
    assert "CapitalChronicle/THREADS_USER_ACCESS_TOKEN" in str(error)
    assert DUMMY not in str(error) and DUMMY not in repr(error)
    out, err = capfd.readouterr()
    assert out == "" and err == ""


def test_reading_prints_and_logs_nothing(capfd, caplog):
    store = fake_store({"THREADS_USER_ACCESS_TOKEN": DUMMY})
    users = fake_user_env({"TELEGRAM_BOT_TOKEN": DUMMY})
    view = reader.secret_environment({"DISCORD_WEBHOOK_URL": DUMMY}, store=store, user_env=users)
    with caplog.at_level("DEBUG"):
        assert reader.read_secret("THREADS_USER_ACCESS_TOKEN", env={}, store=store, user_env=users) == DUMMY
        assert reader.secret_present("TELEGRAM_BOT_TOKEN", env={}, store=store, user_env=users)
        assert reader.secret_source("DISCORD_WEBHOOK_URL", env={"DISCORD_WEBHOOK_URL": DUMMY}, store=store,
                                    user_env=users)["source"] == reader.SOURCE_PROCESS_ENVIRONMENT
        assert view.get("DISCORD_WEBHOOK_URL") == DUMMY and "TELEGRAM_BOT_TOKEN" in view
        assert view.get("NOPE_TOKEN", "default") == "default"
        assert reader.require_secret("THREADS_USER_ACCESS_TOKEN", env={}, store=store, user_env=users) == DUMMY
    out, err = capfd.readouterr()
    assert out == "" and err == ""
    assert caplog.records == []
    assert DUMMY not in repr(view)
    assert DUMMY not in str(reader.secret_source("THREADS_USER_ACCESS_TOKEN", env={}, store=store, user_env=users))


def test_the_view_can_never_be_copied_into_a_child_environment():
    view = reader.secret_environment({"A_TOKEN": DUMMY}, store=fake_store({}), user_env=fake_user_env({}))
    with pytest.raises(TypeError):
        dict(view)  # type: ignore[call-overload]
    with pytest.raises(TypeError):
        list(view)
    with pytest.raises(KeyError):
        view["MISSING_TOKEN"]
    assert view["A_TOKEN"] == DUMMY


def test_invalid_names_are_refused():
    for bad in ("", "  ", "A*", "A?B", "A\x00B"):
        with pytest.raises(ValueError):
            reader.read_secret(bad, env={}, store=fake_store({}), user_env=fake_user_env({}))


# --- blob decoding (the Windows dialog stores UTF-16LE) ------------------------------------------

def test_blob_decoding():
    assert reader._decode_blob(DUMMY.encode("utf-16-le")) == DUMMY
    assert reader._decode_blob(DUMMY.encode("utf-8")) == DUMMY
    assert reader._decode_blob((DUMMY + "\x00").encode("utf-16-le")) == DUMMY
    assert reader._decode_blob(("  " + DUMMY + "\r\n").encode("utf-16-le")) == DUMMY
    assert reader._decode_blob("é-token".encode("utf-16-le")) == "é-token"
    assert reader._decode_blob(b"") == ""
    assert reader._decode_blob(b"\xff\xfe\xfd") is None


# --- tests never read the real store or the live user environment by default --------------------

def test_default_readers_are_off_in_tests_even_when_the_environment_is_cleared(monkeypatch):
    monkeypatch.delenv(reader.STORE_MODE_ENV, raising=False)
    assert "_pytest" in sys.modules
    assert reader.store_enabled() is False
    monkeypatch.setenv(reader.STORE_MODE_ENV, reader.ENVIRONMENT_ONLY)
    assert reader.store_enabled() is False
    monkeypatch.setenv(reader.STORE_MODE_ENV, reader.CREDENTIAL_MANAGER_MODE)
    assert reader.store_enabled() is True


def test_default_lookup_skips_store_and_registry_when_disabled(monkeypatch):
    def boom(*_args):
        raise AssertionError("must not be called")

    monkeypatch.setattr(reader, "windows_store_read", boom)
    monkeypatch.setattr(reader, "windows_user_env_read", boom)
    monkeypatch.setattr(reader, "windows_store_list", boom)
    monkeypatch.setenv("CC297_TEST_PROCESS_ONLY_TOKEN", "process")
    assert reader.read_secret("CC297_TEST_PROCESS_ONLY_TOKEN") == "process"
    assert reader.secret_source("CC297_TEST_PROCESS_ONLY_TOKEN")["credential_manager"] == reader.STORE_DISABLED
    assert reader.stored_secret_names() == []
    assert reader.leaked_secret_names("text") == []


# --- leak guard helpers return names only --------------------------------------------------------

def test_leaked_secret_names_returns_names_only():
    lister = lambda prefix: (reader.STORE_FOUND, ((prefix + "THREADS_APP_SECRET", DUMMY), (prefix + "SHORT", "abc")))
    text = f"summary ... {DUMMY} ... abc"
    assert reader.leaked_secret_names(text, env={}, lister=lister) == ["THREADS_APP_SECRET"]
    assert reader.leaked_secret_names(
        "x " + DUMMY, env={}, env_names=["ROTATED_TOKEN"], lister=lambda p: (reader.STORE_NOT_FOUND, ()),
        user_env=fake_user_env({"ROTATED_TOKEN": DUMMY}),
    ) == ["ROTATED_TOKEN"]
    assert reader.stored_secret_names(lister=lister) == ["SHORT", "THREADS_APP_SECRET"]


# --- the real Windows stores, with dummies only ---------------------------------------------------

windows_only = pytest.mark.skipif(os.name != "nt", reason="Windows Credential Manager and HKCU only")


def _cred_write(target: str, user: str, blob: bytes) -> None:
    import ctypes
    from ctypes import wintypes

    api = reader._api()
    assert api is not None
    CREDENTIALW = api[2]
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi32.CredWriteW.argtypes = [ctypes.POINTER(CREDENTIALW), wintypes.DWORD]
    advapi32.CredWriteW.restype = wintypes.BOOL
    buffer = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
    credential = CREDENTIALW()
    credential.Type = reader.CRED_TYPE_GENERIC
    credential.TargetName = target
    credential.UserName = user
    credential.CredentialBlobSize = len(blob)
    credential.CredentialBlob = ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))
    credential.Persist = 2
    assert advapi32.CredWriteW(ctypes.byref(credential), 0), ctypes.get_last_error()


def _cred_delete(target: str) -> None:
    import ctypes
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi32.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    advapi32.CredDeleteW.restype = wintypes.BOOL
    advapi32.CredDeleteW(target, reader.CRED_TYPE_GENERIC, 0)


@windows_only
def test_real_credential_manager_dummy_round_trip(monkeypatch, capfd):
    name = f"CC297_TEST_DUMMY_{os.getpid()}"
    target = reader.TARGET_PREFIX + name
    monkeypatch.setenv(reader.STORE_MODE_ENV, reader.CREDENTIAL_MANAGER_MODE)
    monkeypatch.setenv(name, "process-stale-dummy")
    _cred_write(target, name, DUMMY.encode("utf-16-le"))   # as the Windows dialog stores it
    try:
        assert reader.windows_store_read(target) == (reader.STORE_FOUND, DUMMY)
        assert reader.read_secret(name) == DUMMY
        assert reader.secret_source(name)["source"] == reader.SOURCE_CREDENTIAL_MANAGER
        assert name in reader.stored_secret_names()
        assert name in reader.leaked_secret_names(f"out {DUMMY} out")
    finally:
        _cred_delete(target)
    assert reader.windows_store_read(target) == (reader.STORE_NOT_FOUND, None)
    assert reader.read_secret(name) == "process-stale-dummy"
    out, err = capfd.readouterr()
    assert DUMMY not in out + err


@windows_only
def test_real_user_environment_dummy_is_read_live(monkeypatch):
    import winreg

    name = f"CC297_TEST_DUMMY_VAR_{os.getpid()}"
    monkeypatch.setenv(reader.STORE_MODE_ENV, reader.CREDENTIAL_MANAGER_MODE)
    monkeypatch.setenv(name, "process-stale-dummy")
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, DUMMY)
    try:
        assert reader.windows_user_env_read(name) == DUMMY
        assert reader.read_secret(name) == DUMMY
        assert reader.secret_source(name)["source"] == reader.SOURCE_USER_ENVIRONMENT
    finally:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, name)
    assert reader.windows_user_env_read(name) is None
    assert reader.read_secret(name) == "process-stale-dummy"
