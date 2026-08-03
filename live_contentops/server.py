"""Read-only local ContentOps health/status server.

Wave 01 quarantines unauthenticated HTTP live launch. This module intentionally
contains no subprocess or thread launch path.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from live_contentops.live_entrypoint_registry_v1 import HTTP_LAUNCH_QUARANTINED

TASKS: dict[str, dict[str, object]] = {}
SERVER_SCHEMA_VERSION = "contentops.read_only_server.v1"


class PipelineServerHandler(BaseHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:5173")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        route = parsed_url.path
        if route == "/api/health":
            self._send_json(200, {
                "status": "READ_ONLY_HEALTHY",
                "schema_version": SERVER_SCHEMA_VERSION,
                "live_launch_authorized": False,
            })
            return
        if route == "/api/pipeline-status":
            task_id = parse_qs(parsed_url.query).get("task_id", [""])[0]
            if not task_id or task_id not in TASKS:
                self._send_json(404, {"error": "Task not found", "task_id": task_id or None})
                return
            self._send_json(200, TASKS[task_id])
            return
        self._send_json(404, {"error": "Route not found", "route": route})

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
        self._send_json(404, {"error": "Route not found", "route": route})


def run_server(port: int = 5174) -> None:
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, PipelineServerHandler)
    print(f"Read-only ContentOps status server running on http://127.0.0.1:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
