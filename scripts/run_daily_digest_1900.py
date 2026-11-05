"""CC-143: the 19:00 GMT+7 daily email digest route, without Codex.

The digest code is unchanged (live_contentops/substack_daily_digest_v1.py). Until
5 Nov the Codex Desktop automation v1-newsroom-brief-us-1900 reached it through
with_due_digest and continued the Neo loop; that route needs Codex quota. This
script is the deterministic half of the replacement route, started by one Claude
Desktop scheduled task:

  preflight  Reads only. Is the digest due (19:00 GMT+7 passed today), is the
             publication path open (no LLM operator pause, AUTONOMOUS_DEFAULT,
             live rollout, feed present), and which exact commands continue it.
  dry-run    Copies the production store into a scratch folder, freezes the
             digest there and drives the existing coordinator to its first
             native Neo request. Writes outside the scratch folder and network
             connections are refused and counted. Publishes nothing.

The live publish/readback loop is the existing CLI (run_native_desktop_editorial.py
digest-resume / digest-tool-begin / digest-tool-submit); this script adds no
publish path, no store and no timer.
"""
from __future__ import annotations

import argparse
import builtins
import contextlib
import io
import json
import os
import socket
import sqlite3
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BANGKOK = timezone(timedelta(hours=7))
DUE_LOCAL = time(19, 0)
DEFAULT_ROLLOUT = ROOT / "config" / "native_desktop_rollout_v1.json"
CLI = "scripts/run_native_desktop_editorial.py"
SURFACE = "CLAUDE_CODE_SESSION"
TOOL = "mcp__browseros-neo__run"


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("EXPLICIT_DIGEST_CLOCK_REQUIRED")
    return parsed.astimezone(timezone.utc)


def due_state(now: datetime) -> dict:
    """The digest for day D is frozen at D 19:00 GMT+7. Before that instant the
    owner returns day D-1's packet, so an early wake must not continue it (the
    4 Nov Codex window entered at 18:59:59.78 and saw only the 3 Nov digest)."""
    if now.tzinfo is None:
        raise ValueError("EXPLICIT_DIGEST_CLOCK_REQUIRED")
    local = now.astimezone(BANGKOK)
    due_at = datetime.combine(local.date(), DUE_LOCAL, BANGKOK)
    if local < due_at:
        return {"state": "NOT_YET_DUE", "due_at_gmt7": due_at.isoformat(),
                "due_at_utc": due_at.astimezone(timezone.utc).isoformat(),
                "digest_id": "cc143-digest-" + local.date().isoformat()}
    return {"state": "DUE", "due_at_gmt7": due_at.isoformat(),
            "due_at_utc": due_at.astimezone(timezone.utc).isoformat(),
            "digest_id": "cc143-digest-" + local.date().isoformat()}


def default_invocation_id(now: datetime) -> str:
    """A truthful run label when the session id is not visible to the agent."""
    return "claude-code-session:cc143-digest-1900:" + now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _ro(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True, timeout=30)
    conn.execute("PRAGMA query_only=ON")
    return conn


def _operating_mode(store_path: Path) -> str:
    with contextlib.closing(_ro(store_path)) as conn:
        row = conn.execute("SELECT operating_mode FROM operating_controls WHERE singleton_id=1").fetchone()
    return row[0] if row else "MISSING"


def _commands(rollout_arg: str, invocation_id: str) -> dict:
    py = f'"{sys.executable}" -B'
    base = f'{py} {CLI} %s --rollout {rollout_arg} --native-invocation-id "{invocation_id}"'
    return {"resume": f'{py} scripts/run_daily_digest_1900.py resume --native-invocation-id "{invocation_id}"',
            "begin": base % "digest-tool-begin" + " --request-sha256 <request_sha256>",
            "submit": base % "digest-tool-submit" + " --request-sha256 <request_sha256> --response <response.json>",
            "observation": {"surface": SURFACE, "tool_name": TOOL, "native_invocation_id": invocation_id,
                            "observation_source": "BROWSEROS_NEO"}}


def preflight(rollout_path: Path, *, now: datetime | None = None, native_invocation_id: str | None = None) -> dict:
    """Reads only: SELECTs on the production store, the rollout, the pause marker and the feed."""
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.llm_operator_control_v1 import llm_operator_pause_active
    from live_contentops.native_desktop_publication_v1 import live_publication_policy
    from live_contentops.published_content_v1 import DEFAULT_FEED, PRODUCTION_STORE
    from live_contentops.substack_daily_digest_v1 import digest_status, packets

    now = now or datetime.now(timezone.utc)
    result = {"item": "CC-143", "route": "CLAUDE_DESKTOP_TASK_1900", "checked_at_utc": now.isoformat(),
              "public_write_performed": False, **due_state(now)}
    blockers = []
    rollout = json.loads(Path(rollout_path).read_bytes())
    try:
        live_publication_policy(rollout)
    except ValueError as exc:
        blockers.append("ROLLOUT:" + str(exc))
    store_path = Path(rollout.get("store_path", ""))
    if store_path.resolve() != PRODUCTION_STORE.resolve():
        blockers.append("EXACT_PRODUCTION_DIGEST_STORE_REQUIRED")
    if llm_operator_pause_active():
        blockers.append("LLM_OPERATOR_PAUSED")
    if not DEFAULT_FEED.is_file():
        blockers.append("CONFIRMED_PUBLICATION_FEED_MISSING")
    mode = _operating_mode(store_path) if store_path.is_file() else "STORE_MISSING"
    result["operating_mode"] = mode
    if mode != "AUTONOMOUS_DEFAULT":
        blockers.append("PUBLICATION_OPERATING_MODE_BLOCKED:" + mode)
    digests = []
    if store_path.is_file():
        store = ContentOpsDurableStore(store_path, auto_migrate=False)
        for packet in sorted(packets(store), key=lambda p: p["cutoff_utc"]):
            status = digest_status(store, packet)
            digests.append({k: status.get(k) for k in ("digest_id", "state", "web_confirmed", "email_confirmed",
                                                       "public_object_id", "public_object_url")}
                           | {"articles": len(packet.get("articles", []))})
    result["existing_digests"] = digests
    result["todays_digest_exists"] = any(d["digest_id"] == result["digest_id"] for d in digests)
    invocation = native_invocation_id or default_invocation_id(now)
    result["native_invocation_id"] = invocation
    result["commands"] = _commands("config/native_desktop_rollout_v1.json", invocation)
    result["blockers"] = blockers
    if blockers:
        result["route_state"] = "BLOCKED"
    elif result["state"] == "NOT_YET_DUE":
        result["route_state"] = "NOT_YET_DUE"
    else:
        result["route_state"] = "CONTINUE_WITH_RESUME"
    return result


class _Guard:
    """Refuse and count every write outside the scratch root and every network connection."""

    def __init__(self, scratch: Path, protected: list[Path]):
        self.scratch = Path(scratch).resolve()
        self.protected = [Path(p).resolve() for p in protected]
        self.refused_writes: list[str] = []
        self.refused_connections: list[str] = []

    def _inside(self, path) -> bool:
        try:
            Path(path).resolve().relative_to(self.scratch)
            return True
        except (ValueError, TypeError, OSError):
            return False

    def _check_write(self, path):
        if isinstance(path, int) or self._inside(path):
            return
        self.refused_writes.append(str(path))
        raise PermissionError("DRY_RUN_WRITE_OUTSIDE_SCRATCH: " + str(path))

    @contextlib.contextmanager
    def active(self):
        real_open, real_io_open = builtins.open, io.open
        real_mkdir, real_makedirs, real_replace, real_rename = Path.mkdir, os.makedirs, os.replace, os.rename
        real_connect, real_create = socket.socket.connect, socket.create_connection
        real_sqlite = sqlite3.connect
        guard = self

        def g_open(file, mode="r", *a, **k):
            if any(c in mode for c in "wax+"):
                guard._check_write(file)
            return real_open(file, mode, *a, **k)

        def g_io_open(file, mode="r", *a, **k):
            if any(c in mode for c in "wax+"):
                guard._check_write(file)
            return real_io_open(file, mode, *a, **k)

        def g_mkdir(self_path, *a, **k):
            if not self_path.exists():
                guard._check_write(self_path)
            return real_mkdir(self_path, *a, **k)

        def g_makedirs(name, *a, **k):
            if not Path(name).exists():
                guard._check_write(name)
            return real_makedirs(name, *a, **k)

        def g_replace(src, dst, *a, **k):
            guard._check_write(dst)
            return real_replace(src, dst, *a, **k)

        def g_rename(src, dst, *a, **k):
            guard._check_write(dst)
            return real_rename(src, dst, *a, **k)

        def g_connect(sock, address):
            guard.refused_connections.append(repr(address))
            raise ConnectionRefusedError("DRY_RUN_NETWORK_REFUSED")

        def g_create(address, *a, **k):
            guard.refused_connections.append(repr(address))
            raise ConnectionRefusedError("DRY_RUN_NETWORK_REFUSED")

        def g_sqlite(database, *a, **k):
            text = str(database)
            target = text[5:].split("?", 1)[0] if text.startswith("file:") else text
            read_only = text.startswith("file:") and "mode=ro" in text
            if target != ":memory:" and not read_only:
                guard._check_write(target)
            return real_sqlite(database, *a, **k)

        builtins.open, io.open = g_open, g_io_open
        Path.mkdir, os.makedirs, os.replace, os.rename = g_mkdir, g_makedirs, g_replace, g_rename
        socket.socket.connect, socket.create_connection = g_connect, g_create
        sqlite3.connect = g_sqlite
        try:
            yield self
        finally:
            builtins.open, io.open = real_open, real_io_open
            Path.mkdir, os.makedirs, os.replace, os.rename = real_mkdir, real_makedirs, real_replace, real_rename
            socket.socket.connect, socket.create_connection = real_connect, real_create
            sqlite3.connect = real_sqlite


def _first_pending(continued: dict) -> dict:
    """The owner raises the first request, or lists unclaimed ones after a resume."""
    if continued.get("native_tool_request"):
        return continued["native_tool_request"]
    for row in continued.get("pending_requests") or []:
        if not row.get("action_claimed"):
            return row
    publication = continued.get("publication") or {}
    for section in (publication.get("recovery_preflight") or {}, publication):
        for value in (section.get("per_destination") or {}).values():
            if isinstance(value, dict) and value.get("native_tool_request"):
                return value["native_tool_request"]
    return {}


def _fingerprint(store_path: Path) -> dict:
    stat = store_path.stat()
    with contextlib.closing(_ro(store_path)) as conn:
        counts = {t: conn.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                  for t in ("outbox_messages", "platform_dispatches", "work_items")}
        digest_rows = conn.execute("SELECT count(*) FROM outbox_messages WHERE destination=?",
                                   ("internal:substack-daily-digest",)).fetchone()[0]
    return {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns, "rows": counts, "digest_packets": digest_rows}


def dry_run(rollout_path: Path, scratch: Path, *, now: datetime | None = None,
            native_invocation_id: str = "cc143-route-dry-run", simulate_identity: bool = False) -> dict:
    """Freeze and continue the digest on a copied store; nothing shared is written."""
    from live_contentops.published_content_v1 import DEFAULT_FEED, PRODUCTION_STORE

    now = now or datetime.now(timezone.utc)
    scratch = Path(scratch)
    scratch.mkdir(parents=True, exist_ok=False)  # a fresh folder per run
    rollout = json.loads(Path(rollout_path).read_bytes())
    production = Path(rollout["store_path"])
    if production.resolve() != PRODUCTION_STORE.resolve():
        raise ValueError("EXACT_PRODUCTION_DIGEST_STORE_REQUIRED")
    copy = scratch / "contentops_daily_app_v1.sqlite3"
    before = _fingerprint(production)
    with contextlib.closing(_ro(production)) as source, contextlib.closing(sqlite3.connect(copy)) as target:
        source.backup(target)
    copied = _fingerprint(copy)
    feed_stat = DEFAULT_FEED.stat()
    result = {"item": "CC-143", "mode": "DRY_RUN_COPIED_STORE", "clock_utc": now.isoformat(),
              "clock_is_simulated": abs((datetime.now(timezone.utc) - now).total_seconds()) > 120,
              "scratch": str(scratch), "copied_store": str(copy), "production_before": before,
              "copy_at_start": copied, **due_state(now)}
    guard = _Guard(scratch, [production])
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.native_neo_executor_v1 import NativeNeoInputRequired
    from live_contentops.substack_daily_digest_v1 import continue_daily_digest, digest_status, prepare_daily_digest
    with guard.active():
        store = ContentOpsDurableStore(copy, auto_migrate=False)
        prepared = prepare_daily_digest(store, DEFAULT_FEED, now=now)
        packet = prepared.get("packet")
        result["prepare"] = {k: v for k, v in prepared.items() if k != "packet"}
        if packet:
            result["digest"] = {"digest_id": packet["digest_id"], "cutoff_utc": packet["cutoff_utc"],
                "title": packet["native_payload"]["title"], "subtitle": packet["native_payload"]["subtitle"],
                "articles": [{k: a[k] for k in ("title", "url", "published_at_utc")} for a in packet["articles"]],
                "media": [{k: m[k] for k in ("asset_id", "path", "sha256")} for m in packet["media_assets"]]}
            local_rollout = {**rollout, "store_path": str(copy), "editorial_output_root": str(scratch / "outputs")}
            try:
                continued = continue_daily_digest(store, packet,
                    output_dir=scratch / "outputs" / "owner-manual" / packet["digest_id"] / "native-tools",
                    invocation_id=native_invocation_id, rollout=local_rollout, command="resume")
            except NativeNeoInputRequired as pending:  # defensive; the owner normally catches it
                continued = {"state": "NATIVE_NEO_TOOL_PENDING", "native_tool_request": pending.request}
            request = _first_pending(continued)
            inner = request.get("request", {})
            result["continue"] = {"state": continued.get("state"), "web_confirmed": continued.get("web_confirmed"),
                "email_confirmed": continued.get("email_confirmed"),
                "first_native_request": {"action": inner.get("action"), "destination": inner.get("destination"),
                    "surface": inner.get("surface"), "expected_identity": inner.get("expected_identity"),
                    "request_sha256": inner.get("request_sha256"), "required_tool": request.get("required_tool"),
                    "public_write_authorized": request.get("public_write_authorized"),
                    "request_path": request.get("request_path")} if request else None,
                "pending_requests": len(continued.get("pending_requests", []))}
            if simulate_identity and request and inner.get("action") == "VERIFY_IDENTITY":
                # Prove the Claude surface passes the owner's begin/submit binding, on the copy
                # only, then stop at the next request without beginning it.
                args = dict(output_dir=scratch / "outputs" / "owner-manual" / packet["digest_id"] / "native-tools",
                            invocation_id=native_invocation_id, rollout=local_rollout)
                continue_daily_digest(store, packet, command="begin", request_hash=inner["request_sha256"], **args)
                response = {"tool_request_sha256": request["tool_request_sha256"],
                    "tool_observation": {"surface": SURFACE, "tool_name": TOOL,
                        "native_invocation_id": native_invocation_id,
                        "observation_source": "DRY_RUN_SIMULATED_NOT_BROWSER",
                        "observed_at_utc": datetime.now(timezone.utc).isoformat()},
                    "result": {"request_sha256": inner["request_sha256"], "status": "SUCCESS",
                        "authenticated": True, "observed_identity": inner.get("expected_identity"),
                        "observation_ref": "DRY_RUN_SIMULATED_NOT_BROWSER"}}
                submitted = continue_daily_digest(store, packet, command="submit",
                    request_hash=inner["request_sha256"], response=response, **args)
                following = continue_daily_digest(store, packet, command="resume", **args)
                nxt = _first_pending(following)
                nxt_inner = nxt.get("request", {})
                result["simulated_identity"] = {"submitted": submitted, "next_state": following.get("state"),
                    "publication_status": (following.get("publication") or {}).get("canonical_publication_status"),
                    "next_native_request": {"action": nxt_inner.get("action"), "destination": nxt_inner.get("destination"),
                        "public_write_authorized": nxt.get("public_write_authorized"),
                        "substack_delivery_policy": nxt_inner.get("substack_delivery_policy"),
                        "request_sha256": nxt_inner.get("request_sha256"),
                        "request_path": nxt.get("request_path")} if nxt else None,
                    "next_request_begun": False}
            result["copy_status_after"] = digest_status(store, packet)
    result["production_after"] = _fingerprint(production)
    result["production_unchanged"] = result["production_after"] == before
    result["feed_unchanged"] = DEFAULT_FEED.stat().st_mtime_ns == feed_stat.st_mtime_ns
    result["refused_writes_outside_scratch"] = guard.refused_writes
    result["refused_network_connections"] = guard.refused_connections
    result["public_write_performed"] = False
    return result


def summarize_continuation(continued: dict) -> dict:
    """One flat view of the owner's return: the state and the next unclaimed native request."""
    request = _first_pending(continued)
    inner = request.get("request", {}) if request else {}
    return {"state": continued.get("state"), "digest_id": continued.get("digest_id"),
            "confirmed": continued.get("confirmed"), "web_confirmed": continued.get("web_confirmed"),
            "email_confirmed": continued.get("email_confirmed"),
            "public_object_id": continued.get("public_object_id"),
            "public_object_url": continued.get("public_object_url"),
            "next_request": {"action": inner.get("action"), "destination": inner.get("destination"),
                             "request_sha256": inner.get("request_sha256"),
                             "tool_request_sha256": request.get("tool_request_sha256"),
                             "public_write_authorized": request.get("public_write_authorized")} if request else None}


def resume(rollout_path: Path, native_invocation_id: str, *, now: datetime | None = None) -> dict:
    """The CLI's digest-resume through the same owners, guarded against an early wake.
    It never begins a request: only digest-tool-begin claims, and only the agent acts."""
    from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
    from live_contentops.native_desktop_publication_v1 import live_publication_policy
    from live_contentops.published_content_v1 import DEFAULT_FEED, PRODUCTION_STORE
    from live_contentops.substack_daily_digest_v1 import continue_daily_digest, prepare_daily_digest

    now = now or datetime.now(timezone.utc)
    due = due_state(now)
    if due["state"] == "NOT_YET_DUE":
        return {"item": "CC-143", "route_state": "NOT_YET_DUE", **due, "public_write_performed": False}
    rollout = json.loads(Path(rollout_path).read_bytes())
    live_publication_policy(rollout)
    if Path(rollout["store_path"]).resolve() != PRODUCTION_STORE.resolve():
        raise ValueError("EXACT_PRODUCTION_DIGEST_STORE_REQUIRED")
    store = ContentOpsDurableStore(rollout["store_path"], auto_migrate=False)
    prepared = prepare_daily_digest(store, DEFAULT_FEED)
    packet = prepared.get("packet")
    if not packet:
        return {"item": "CC-143", "route_state": prepared.get("state"), **due,
                "prepare": prepared, "public_write_performed": False}
    continued = continue_daily_digest(store, packet,
        output_dir=Path(rollout["editorial_output_root"]) / "owner-manual" / packet["digest_id"] / "native-tools",
        invocation_id=native_invocation_id, rollout=rollout, command="resume")
    summary = summarize_continuation({"digest_id": packet["digest_id"], **continued})
    if summary["confirmed"]:
        route_state = "CONFIRMED"
    elif summary["next_request"]:
        route_state = "NATIVE_REQUEST_READY"
    elif summary["web_confirmed"]:
        route_state = "WEB_CONFIRMED_EMAIL_READBACK_REQUIRED"
    else:
        route_state = summary["state"] or "NO_NEXT_REQUEST"
    return {"item": "CC-143", "route_state": route_state, **due, **summary,
            "articles": len(packet.get("articles", [])), "native_invocation_id": native_invocation_id,
            "public_write_performed": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("preflight", "resume", "dry-run"))
    parser.add_argument("--rollout", type=Path, default=DEFAULT_ROLLOUT)
    parser.add_argument("--now", help="UTC ISO clock; dry-run simulation only")
    parser.add_argument("--native-invocation-id")
    parser.add_argument("--scratch", type=Path, help="dry-run: a new folder on C: for the copied store")
    parser.add_argument("--output", type=Path, help="also write the JSON result here")
    parser.add_argument("--simulate-identity", action="store_true",
                        help="dry-run: on the copy, answer the read-only identity request with a labelled simulated return and stop at the next request")
    args = parser.parse_args(argv)
    try:
        if args.command == "preflight":
            if args.now:
                parser.error("preflight uses the real clock")
            result = preflight(args.rollout, native_invocation_id=args.native_invocation_id)
        elif args.command == "resume":
            if args.now or not args.native_invocation_id:
                parser.error("resume uses the real clock and needs the preflight's --native-invocation-id")
            result = resume(args.rollout, args.native_invocation_id)
        else:
            if not args.scratch:
                parser.error("dry-run requires --scratch")
            result = dry_run(args.rollout, args.scratch, now=_utc(args.now) if args.now else None,
                             native_invocation_id=args.native_invocation_id or "cc143-route-dry-run",
                             simulate_identity=args.simulate_identity)
    except (ValueError, OSError, KeyError, sqlite3.Error) as exc:
        result = {"item": "CC-143", "route_state": "FAILED", "cause": f"{type(exc).__name__}: {exc}",
                  "public_write_performed": False}
        print(json.dumps(result, ensure_ascii=True))
        return 2
    text = json.dumps(result, indent=2, ensure_ascii=True, default=str)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
