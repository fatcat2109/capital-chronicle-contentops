"""Loopback-only API for the Final Daily App operating console.

The snapshot endpoint is a query-only projection over one explicitly configured canonical
store.  The only mutation exposed here is a compare-and-swap operating-mode update.  The
historical HTTP pipeline launcher remains fail-closed and quarantined.
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Type
from urllib.parse import parse_qs, urlparse

from live_contentops.daily_app_ui_read_model_v1 import (
    DailyAppReadModelError,
    build_daily_app_snapshot,
    update_daily_app_mode,
)
from live_contentops.durable_operational_store_v1 import OperatingModeConflictError
from live_contentops.live_entrypoint_registry_v1 import HTTP_LAUNCH_QUARANTINED

TASKS: dict[str, dict[str, object]] = {}
SERVER_SCHEMA_VERSION = "contentops.daily_app_loopback_api.v1"
MAX_CONTROL_BODY_BYTES = 1024
ALLOWED_ORIGINS = frozenset({
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
})


class PipelineServerHandler(BaseHTTPRequestHandler):
    """Request handler configured by ``make_handler`` with an explicit store path."""

    store_path: Path | None = None

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        # Do not put request query/body data into a durable log by default.
        return

    def _allowed_origin(self) -> str | None:
        origin = self.headers.get("Origin")
        return origin if origin in ALLOWED_ORIGINS else None

    def end_headers(self) -> None:
        origin = self._allowed_origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        if self.headers.get("Origin") not in ALLOWED_ORIGINS:
            self._send_json(403, {"error": "ORIGIN_NOT_ALLOWED"})
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _require_store(self) -> Path:
        if self.store_path is None:
            raise DailyAppReadModelError("canonical durable store is not configured")
        return self.store_path

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        route = parsed_url.path
        if route == "/api/health":
            self._send_json(200, {
                "status": "LOOPBACK_API_HEALTHY",
                "schema_version": SERVER_SCHEMA_VERSION,
                "live_launch_authorized": False,
            })
            return
        if route == "/api/daily-app/snapshot":
            if parsed_url.query:
                self._send_json(400, {"error": "QUERY_PARAMETERS_NOT_SUPPORTED"})
                return
            try:
                snapshot = build_daily_app_snapshot(self._require_store())
            except DailyAppReadModelError as exc:
                self._send_json(503, {"error": "SNAPSHOT_UNAVAILABLE", "detail": str(exc)})
                return
            self._send_json(200, snapshot)
            return
        if route == "/api/pipeline-status":
            task_id = parse_qs(parsed_url.query).get("task_id", [""])[0]
            if not task_id or task_id not in TASKS:
                self._send_json(404, {"error": "Task not found", "task_id": task_id or None})
                return
            self._send_json(200, TASKS[task_id])
            return
        self._send_json(404, {"error": "Route not found", "route": route})

    def _read_control_payload(self) -> dict[str, Any]:
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if content_type != "application/json":
            raise ValueError("CONTENT_TYPE_MUST_BE_APPLICATION_JSON")
        raw_length = self.headers.get("Content-Length")
        if raw_length is None or not raw_length.isdigit():
            raise ValueError("VALID_CONTENT_LENGTH_REQUIRED")
        length = int(raw_length)
        if length <= 0 or length > MAX_CONTROL_BODY_BYTES:
            raise ValueError("CONTROL_BODY_SIZE_INVALID")
        try:
            payload = json.loads(self.rfile.read(length))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("MALFORMED_JSON") from exc
        if not isinstance(payload, dict) or set(payload) != {"operating_mode", "expected_state_version"}:
            raise ValueError("EXACT_CONTROL_FIELDS_REQUIRED")
        if not isinstance(payload["operating_mode"], str):
            raise ValueError("OPERATING_MODE_MUST_BE_STRING")
        if isinstance(payload["expected_state_version"], bool) or not isinstance(payload["expected_state_version"], int):
            raise ValueError("EXPECTED_STATE_VERSION_MUST_BE_INTEGER")
        if payload["expected_state_version"] < 1:
            raise ValueError("EXPECTED_STATE_VERSION_MUST_BE_POSITIVE")
        return payload

    def do_POST(self) -> None:
        route = urlparse(self.path).path
        if route == "/api/run-pipeline":
            self._send_json(423, {
                "status": HTTP_LAUNCH_QUARANTINED,
                "entrypoint_id": "contentops.local_http_run_pipeline.v1",
                "canonical_entrypoint_id": "contentops.production_orchestrator.v1",
                "live_launch_authorized": False,
                "thread_created": False,
                "subprocess_created": False,
                "retryable": False,
            })
            return
        if route != "/api/daily-app/control/mode":
            self._send_json(404, {"error": "Route not found", "route": route})
            return
        if self.headers.get("Origin") not in ALLOWED_ORIGINS:
            self._send_json(403, {"error": "ORIGIN_NOT_ALLOWED"})
            return
        try:
            payload = self._read_control_payload()
            control = update_daily_app_mode(
                self._require_store(),
                expected_state_version=payload["expected_state_version"],
                operating_mode=payload["operating_mode"],
            )
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
            return
        except OperatingModeConflictError:
            self._send_json(409, {"error": "OPERATING_MODE_STATE_VERSION_CONFLICT"})
            return
        except DailyAppReadModelError as exc:
            self._send_json(503, {"error": "CONTROL_UNAVAILABLE", "detail": str(exc)})
            return
        self._send_json(200, {"status": "OPERATING_MODE_UPDATED", "control": control})


def make_handler(store_path: str | Path) -> Type[PipelineServerHandler]:
    """Bind a handler class to one canonical store without exposing the path over HTTP."""
    resolved = Path(store_path).resolve(strict=True)

    class ConfiguredPipelineServerHandler(PipelineServerHandler):
        pass

    ConfiguredPipelineServerHandler.store_path = resolved
    return ConfiguredPipelineServerHandler


def run_server(*, store_path: str | Path, port: int = 5174) -> None:
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, make_handler(store_path))
    print(f"ContentOps Daily App API running on http://127.0.0.1:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        httpd.server_close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the loopback-only ContentOps Daily App API")
    parser.add_argument("--store", required=True, help="Explicit path to the canonical durable SQLite store")
    parser.add_argument("--port", type=int, default=5174)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_server(store_path=args.store, port=args.port)
