"""CC-512: one bounded AGY call, then one Codex call on timeout/empty output.

Call artifacts stay with the existing role's artifacts. Role-specific source,
copy and image checks still judge the answer; this module grants no acceptance.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import tempfile
import threading
from time import perf_counter

from .agy_editorial_assist_v1 import AGY, MODEL, EFFORT, _run

# The saved answered-call p90 is 64.57s. Censored timeouts are reported separately
# in CC-512's diagnosis; they cannot establish a completed-call percentile.
AGY_TIMEOUT = 65
CODEX_TIMEOUT = 65
CODEX_IMAGE_TIMEOUT = 120
CODEX_MODEL, CODEX_EFFORT = "gpt-6.1-sol", "low"
POLICY = "cc512-light-caller-v1"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def codex_executable():
    found = shutil.which("codex.exe") or shutil.which("codex")
    if not found:
        candidates = list(Path(r"C:\Users\bullw\AppData\Local\OpenAI\Codex\bin").glob("*/codex.exe"))
        found = str(max(candidates, key=lambda p: p.stat().st_mtime)) if candidates else None
    if not found:
        raise ValueError("CODEX_EXECUTABLE_NOT_FOUND")
    return found


def _run_codex(args, *, cwd, timeout, input):
    """A completed JSONL turn is the return, even if CLI teardown holds a pipe.

    The CC-512 native diagnostic observed turn.completed followed by a 65s
    communicate timeout. Never kill another session: this owns only its Popen.
    """
    proc = subprocess.Popen(args, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    lines, output, errors = queue.Queue(), [], []
    def read_stdout():
        try:
            for line in iter(proc.stdout.readline, b""):
                output.append(line)
                lines.put(line)
        finally:
            lines.put(None)
    def read_stderr():
        for line in iter(proc.stderr.readline, b""):
            errors.append(line)
    readers = [threading.Thread(target=read_stdout, daemon=True), threading.Thread(target=read_stderr, daemon=True)]
    for thread in readers:
        thread.start()
    started, completed, expired, failure = perf_counter(), False, False, None
    try:
        proc.stdin.write(input)
        proc.stdin.close()  # One finite request; no interactive stdin survives.
        deadline = started + timeout
        while True:
            left = deadline - perf_counter()
            if left <= 0:
                expired = True
                break
            try:
                line = lines.get(timeout=left)
            except queue.Empty:
                expired = True
                break
            if line is None:
                break
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if event.get("type") == "turn.completed":
                completed = True
                completion_seconds = perf_counter() - started
                break
            if event.get("type") == "turn.failed":
                break
    except Exception as exc:
        failure = exc
    finally:
        try:
            proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True,
                    timeout=5, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            else:
                proc.kill()
            proc.wait(timeout=5)
        for thread in readers:
            thread.join(timeout=2)
        # A descendant may have inherited a pipe after the CLI itself exited.
        # Closing a stream under its blocked reader would reacquire its lock and
        # recreate the hang. Daemon readers release it on EOF/process teardown.
        if not readers[0].is_alive():
            proc.stdout.close()
        if not readers[1].is_alive():
            proc.stderr.close()
    raw, err = b"".join(output), b"".join(errors)
    if failure:
        raise failure
    if expired:
        raise subprocess.TimeoutExpired(args, timeout, output=raw, stderr=err)
    result = subprocess.CompletedProcess(args, 0 if completed else (proc.returncode or 1), raw, err)
    result.turn_completed = completed
    result.completion_seconds = completion_seconds if completed else None
    return result


def _agy_answer(raw, record):
    """Unwrap the supported final envelope, including a blank SUCCESS result."""
    text = raw.decode("utf-8").strip()
    if not text:
        return b""
    try:
        events = [json.loads(line) for line in text.splitlines() if line.strip()]
        final = next((e["result"] for e in reversed(events) if e.get("event") == "result"), None)
    except (ValueError, AttributeError, TypeError):
        events, final = [], None
    if final is None:
        try:
            value = json.loads(text)
        except ValueError:
            return raw  # A nonempty invalid answer belongs to the role's validator.
        final = value if isinstance(value, dict) and "response" in value else None
    tools = set()
    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"name", "tool_name"} and item in ("read_file", "view_file", "view_image"):
                    tools.add(item)
                else:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    for event in events:
        if event.get("event") == "step_update":
            walk(event)
    record["image_tools_observed"] = sorted(tools)
    if final is None:
        return text.encode()
    for key in ("model", "effort", "session_id", "conversation_id", "usage", "duration_seconds", "num_turns"):
        if final.get(key) is not None:
            record["observed_" + key] = final[key]
    if final.get("error") == 'stream input content block type "image" is not supported (only "text")':
        raise ValueError("AGY_IMAGE_INPUT_UNSUPPORTED")
    if final.get("status") != "SUCCESS":
        raise ValueError("AGY_RESULT_UNAVAILABLE")
    if isinstance(final.get("structured_output"), dict):
        return json.dumps(final["structured_output"]).encode()
    response = final.get("response")
    return (response if isinstance(response, str) else "").strip().encode()


def _codex_observations(raw, record):
    messages = []
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "thread.started":
            record["observed_session_id"] = event.get("thread_id")
        if event.get("type") == "turn.completed":
            record["observed_usage"] = event.get("usage")
        item = event.get("item") or {}
        if item.get("type") == "agent_message" and isinstance(item.get("text"), str):
            messages.append(item["text"])
        if item.get("type") in {"command_execution", "mcp_tool_call", "web_search", "tool_call", "function_call",
                "collab_tool_call", "image_generation_call", "local_shell_call", "computer_call"}:
            raise ValueError("CODEX_LIGHT_TOOL_USE_REFUSED")
    return messages[-1].encode() if messages else b""


def call_light(prompt, *, root, timeout_cause, empty_cause, runner=None, image=None, schema=None):
    """Return (answer bytes, record); retain the first cause if both calls fail."""
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if not prompt.startswith("Do not call any tool"):
        prompt = "Do not call any tool. " + prompt
    (root / "prompt.txt").write_text(prompt, encoding="utf-8")
    image = Path(image).resolve() if image is not None else None
    record = {"policy": POLICY, "status": "FAILED", "started_at_utc": _now(),
        "prompt_sha256": sha256(prompt.encode()).hexdigest(), "prompt_bytes": len(prompt.encode()),
        "attempts": [], "answered_by": None, "configuration_status": "CONFIGURED_NOT_OBSERVED"}
    if image is not None:
        record["image_sha256"] = sha256(image.read_bytes()).hexdigest()
        record["image_bytes"] = image.stat().st_size
    schema_path = None
    if schema is not None:
        schema_path = root / "output.schema.json"
        _save(schema_path, schema)
    start, answer = perf_counter(), b""
    for caller in ("antigravity", "codex"):
        run = runner or (_run if caller == "antigravity" else _run_codex)
        limit = AGY_TIMEOUT if caller == "antigravity" else CODEX_IMAGE_TIMEOUT if image is not None else CODEX_TIMEOUT
        attempt = {"caller": caller, "started_at_utc": _now(), "status": "FAILED",
            "configured_model": MODEL if caller == "antigravity" else CODEX_MODEL,
            "configured_effort": EFFORT if caller == "antigravity" else CODEX_EFFORT,
            "configuration_status": "CONFIGURED_NOT_OBSERVED",
            "timeout_seconds": limit}
        raw, err, then, eligible = b"", b"", perf_counter(), False
        try:
            if image is not None and sha256(image.read_bytes()).hexdigest() != record["image_sha256"]:
                raise ValueError("IMAGE_REVIEW_BYTES_CHANGED")
            with tempfile.TemporaryDirectory(prefix="cc512-light-", ignore_cleanup_errors=True) as cwd:
                if caller == "antigravity":
                    args = [AGY, "--model", MODEL, "--effort", EFFORT, "--disable-slash-commands",
                        "--print-timeout", str(AGY_TIMEOUT) + "s", "--input-format", "stream-json",
                        "--output-format", "stream-json", "--print", ""]
                    if image is not None:
                        # AGY 1.5.5 cannot attach images. Retain the already supported
                        # exact-local-PNG read; the same prompt tells Codex to use its attachment.
                        args += ["--mode", "plan", "--add-dir", str(image.parent)]
                    if schema_path:
                        args += ["--json-schema", str(schema_path)]
                    message = {"event": "user", "message": {"role": "user", "content": [{"type": "text", "text": prompt}]}}
                    done = run(args, cwd=cwd, timeout=AGY_TIMEOUT, input=(json.dumps(message) + "\n").encode())
                    raw, err = done.stdout, done.stderr
                    answer = _agy_answer(raw, attempt)
                else:
                    result_path = Path(cwd) / "codex-answer.txt"
                    args = [codex_executable(), "exec", "--model", CODEX_MODEL,
                        "-c", 'model_reasoning_effort="' + CODEX_EFFORT + '"',
                        "--ignore-user-config", "--ephemeral", "--skip-git-repo-check", "--sandbox", "read-only",
                        "-c", 'approval_policy="never"', "-c", 'forced_login_method="chatgpt"',
                        "-c", 'web_search="disabled"', "--disable", "shell_tool", "--disable", "multi_agent",
                        "--disable", "view_image", "--disable", "apps", "--disable", "remote_plugin",
                        "--disable", "hooks", "--json", "--output-last-message", str(result_path)]
                    if image is not None:
                        args += ["--image", str(image)]
                    if schema_path:
                        args += ["--output-schema", str(schema_path)]
                    # communicate() sends this exact prompt then closes stdin (EOF);
                    # there is no interactive input, shell interpolation or size truncation.
                    done = run(args + ["-"], cwd=cwd, timeout=limit, input=prompt.encode())
                    raw, err = done.stdout, done.stderr
                    if getattr(done, "turn_completed", False):
                        attempt["turn_completed_seconds"] = done.completion_seconds
                    final_message = _codex_observations(raw, attempt)
                    # JSONL startup/usage events alone are not an answer. Plain
                    # stdout is accepted for older CLIs and controlled runners.
                    answer = result_path.read_bytes() if result_path.is_file() else final_message
                    if not answer and raw.strip() and not any(b'"type"' in line for line in raw.splitlines()):
                        answer = raw
                    attempt["image_attached"] = image is not None
                attempt["returncode"] = done.returncode
                if done.returncode:
                    raise ValueError(caller.upper() + "_EXIT_" + str(done.returncode))
                if not answer.strip():
                    eligible = True
                    raise ValueError(empty_cause if caller == "antigravity" else "CODEX_LIGHT_EMPTY_RESPONSE")
                if image is not None and sha256(image.read_bytes()).hexdigest() != record["image_sha256"]:
                    raise ValueError("IMAGE_REVIEW_BYTES_CHANGED")
                attempt["status"] = "RETURNED"
        except subprocess.TimeoutExpired as exc:
            raw, err = exc.output or b"", exc.stderr or b""
            eligible = True
            attempt.update(status="TIMEOUT", cause=timeout_cause if caller == "antigravity" else "CODEX_LIGHT_TIMEOUT_" + str(limit) + "S")
        except Exception as exc:
            attempt["cause"] = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
            if isinstance(exc, OSError):
                attempt.update(error_errno=exc.errno, error_winerror=getattr(exc, "winerror", None))
        attempt.update(ended_at_utc=_now(), elapsed_seconds=perf_counter() - then,
            stdout_bytes=len(raw), stderr_bytes=len(err), output_sha256=sha256(raw).hexdigest(), stderr_sha256=sha256(err).hexdigest())
        (root / (caller + "-stdout.txt")).write_bytes(raw)
        (root / (caller + "-stderr.txt")).write_bytes(err)
        record["attempts"].append(attempt)
        if attempt["status"] == "RETURNED":
            record.update(status="RETURNED", answered_by=caller, answer_seconds=attempt["elapsed_seconds"],
                configured_model=attempt["configured_model"], configured_effort=attempt["configured_effort"])
            for key, value in attempt.items():
                if key.startswith("observed_") or key == "image_tools_observed":
                    record[key] = value
            break
        if caller == "antigravity":
            record["cause"] = attempt["cause"]
            if not eligible:
                break
        else:
            record["fallback_cause"] = attempt["cause"]
    record.update(ended_at_utc=_now(), elapsed_seconds=perf_counter() - start, artifact_path=str(root / "light-call.json"))
    if record["status"] == "RETURNED":
        if "cause" in record:
            record["first_cause"] = record.pop("cause")
        (root / "answer.txt").write_bytes(answer)
    _save(root / "light-call.json", record)
    return (answer if record["status"] == "RETURNED" else b""), record


def json_answer(raw):
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.decode("utf-8").strip())
    return json.loads(text)
