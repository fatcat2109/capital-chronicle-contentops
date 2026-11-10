"""CC-404: OTS evidence beside exact retained public bytes, with separate clocks.

The existing event attach and minute-run consumers call this bounded helper.
It is neither a publisher nor a scheduler. Only hashes reach public calendars.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\event-public-records")
CLIENT_PYTHON = Path(r"A:\Capital Chronicle\Runtime\ContentOps\tools\opentimestamps-client\Scripts\python.exe")
SHIM = Path(__file__).resolve().parents[1] / "scripts" / "opentimestamps_client.py"
CALENDARS = ("https://alice.btc.calendar.opentimestamps.org",
             "https://bob.btc.calendar.opentimestamps.org",
             "https://finney.calendar.eternitywall.com")
RECHECK_HOURS = 6


def _utc(value):
    at = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if at.tzinfo is None:
        raise ValueError("OTS_CLOCK_TIMEZONE_REQUIRED")
    return at.astimezone(timezone.utc)


def _save(path, value):
    data = json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2).encode() + b"\n"
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
    os.replace(temporary, path)


def _retain(path, raw):
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError:
        if path.read_bytes() != raw:
            raise ValueError("EVENT_RETAINED_BYTES_IMMUTABLE")


@contextmanager
def _lock(folder):
    # OS-owned lock releases on crash. The file itself is not a lease or state.
    with (folder / ".ots.lock").open("a+b") as stream:
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            if stream.read(1) == b"":
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def run_client(arguments, *, python=CLIENT_PYTHON):
    result = subprocess.run([str(python), "-B", str(SHIM), *map(str, arguments)],
        capture_output=True, text=True, encoding="utf-8", timeout=20,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return {"returncode": result.returncode, "stdout": result.stdout[-3000:],
            "stderr": result.stderr[-3000:]}


def inspect(source, proof, *, runner=run_client):
    result = runner(["inspect", str(source), str(proof)])
    if result["returncode"]:
        detail = (result["stderr"].strip().splitlines() or ["CLIENT_INSPECTION_FAILED"])[-1]
        raise ValueError("OTS_PROOF_INVALID:" + detail[:160])
    summary = json.loads(result["stdout"])
    if summary.get("file_sha256") != sha256(Path(source).read_bytes()).hexdigest() or summary.get("file_matches") is not True:
        raise ValueError("OTS_PROOF_FILE_DIGEST_MISMATCH")
    return {**summary, "proof_path": str(proof), "proof_sha256": sha256(Path(proof).read_bytes()).hexdigest(),
            "proof_bytes": Path(proof).stat().st_size}


def retain_and_stamp(spec, *, event_id, frozen_at_utc, event_time_utc,
                     root=ROOT, now=None, runner=run_client, upgrade=False):
    """Idempotent submission; upgrades work on a copy and retain the first proof.

    A calendar receipt is pending, never an independently verified freeze time.
    No local clock is substituted for a Bitcoin block's time.
    """
    injected_now = now
    now = now or datetime.now(timezone.utc)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", event_id):
        raise ValueError("EVENT_ID_PATH_INVALID")
    raw = Path(spec["path"]).read_bytes()
    digest = sha256(raw).hexdigest()
    if digest != spec["sha256"] or len(raw) > 2_000_000:
        raise ValueError("FROZEN_PUBLIC_RECORD_BYTES_MISMATCH")
    folder = Path(root) / event_id / digest
    folder.mkdir(parents=True, exist_ok=True)
    with _lock(folder):
        target = folder / "frozen-public.json"
        _retain(target, raw)
        proof = target.with_suffix(".json.ots")
        metadata = folder / "timestamp.json"
        state = json.loads(metadata.read_bytes()) if metadata.is_file() else {
            "schema_version": "contentops.event_timestamp.v1", "event_id": event_id,
            "path": str(target), "sha256": digest, "frozen_at_utc": frozen_at_utc,
            "event_time_utc": event_time_utc, "first_attempt_at_utc": now.isoformat(),
            "submitted_at_utc": None, "bitcoin_verified": False}
        if any(state[k] != v for k, v in (("sha256", digest), ("frozen_at_utc", frozen_at_utc),
                                         ("event_time_utc", event_time_utc))):
            raise ValueError("EVENT_TIMESTAMP_BINDING_CHANGED")
        due = not state.get("next_attempt_at_utc") or now >= _utc(state["next_attempt_at_utc"])
        command = None
        try:
            if not proof.is_file() and due:
                command = ["--no-bitcoin", "--no-cache", "stamp", "--timeout", "5", "-m", "2"]
                for calendar in CALENDARS:
                    command.extend(["-c", calendar])
                result = runner([*command, str(target)])
                state["last_client_result"] = result
                if proof.is_file():
                    state.update(inspect(target, proof, runner=runner))
                    observed = injected_now or datetime.now(timezone.utc)
                    state["submitted_at_utc"] = state["submitted_at_utc"] or observed.isoformat()
                    _retain(folder / "initial.ots", proof.read_bytes())
                else:
                    state.update(status="STAMP_FAILED", cause="OTS_CALENDAR_SUBMISSION_FAILED")
            elif proof.is_file():
                state.update(inspect(target, proof, runner=runner))
                if upgrade and due and not state.get("bitcoin_attestations"):
                    command = ["--no-bitcoin", "--no-cache", "upgrade", "--timeout", "5"]
                    # OTS upgrade writes .bak; an isolated copy avoids clobbering
                    # that history or leaving the last valid public proof absent.
                    with tempfile.TemporaryDirectory(dir=folder) as temporary:
                        candidate = Path(temporary) / proof.name
                        candidate.write_bytes(proof.read_bytes())
                        state["last_client_result"] = runner([*command, str(candidate)])
                        upgraded = inspect(target, candidate, runner=runner)
                        if upgraded["proof_sha256"] != state["proof_sha256"]:
                            _retain(folder / (state["proof_sha256"] + ".ots"), proof.read_bytes())
                            os.replace(candidate, proof)
                        state.update(inspect(target, proof, runner=runner))
            if command:
                state["last_attempt_at_utc"] = now.isoformat()
                state["next_attempt_at_utc"] = (now + timedelta(hours=RECHECK_HOURS)).isoformat()
            submitted = state.get("submitted_at_utc")
            state["submission_before_release"] = bool(submitted and _utc(submitted) < _utc(event_time_utc))
            state["bitcoin_verified"] = False
            state["verification_note"] = "Verify the upgraded proof with ots and opentimestamps.org; calendar acceptance is not Bitcoin confirmation."
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            state.update(status="STAMP_ERROR", cause=type(exc).__name__ + ":" + str(exc)[:200],
                         next_attempt_at_utc=(now + timedelta(hours=RECHECK_HOURS)).isoformat())
        _save(metadata, state)
        return state


def maintain_timestamps(*, root=ROOT, now=None, runner=run_client):
    """At most one due proof per existing minute run; no new job or wait loop."""
    now = now or datetime.now(timezone.utc)
    for path in sorted(Path(root).glob("*/*/timestamp.json")):
        state = json.loads(path.read_bytes())
        if state.get("bitcoin_attestations"):
            continue
        if state.get("next_attempt_at_utc") and now < _utc(state["next_attempt_at_utc"]):
            continue
        return retain_and_stamp(state, event_id=state["event_id"], frozen_at_utc=state["frozen_at_utc"],
            event_time_utc=state["event_time_utc"], root=root, now=now, runner=runner, upgrade=True)
    return {"status": "NO_TIMESTAMP_DUE"}
