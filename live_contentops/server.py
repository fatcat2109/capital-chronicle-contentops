import json
import os
import subprocess
import sys
import uuid
import threading
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer

# Global in-memory task registry
TASKS = {}
MAX_RETAINED_TASKS = 25
PIPELINE_COMMAND = [sys.executable, "-u", "-m", "live_contentops.live_production_pipeline_runner_v6", "--live-run", "--dispatch-live"]
DISPATCH_AUDIT_PATH = os.path.join("docs", "automation", "V6_PLATFORM_NATIVE_VARIANTS", "latest_dispatch_audit.json")
# Any pipeline_status not in this set is treated as a failed/blocked live launch.
LIVE_SUCCESS_STATUSES = {"DISPATCH_COMPLETE"}


def _utc_now():
    import time
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_dispatch_audit(run_id):
    """Read the committed audit packet and return the true dispatch outcome.

    The process return code alone is not trusted: a blocked launch must not be
    reported as success. We only trust the audit if it matches this run_id.
    """
    try:
        with open(DISPATCH_AUDIT_PATH, "r", encoding="utf-8") as f:
            audit = json.load(f)
    except (OSError, ValueError):
        return None
    if run_id and audit.get("run_id") and audit.get("run_id") != run_id:
        return None  # stale audit from a different run
    return {
        "run_id": audit.get("run_id"),
        "pipeline_status": audit.get("pipeline_status"),
        "dispatch_live": bool(audit.get("dispatch_live")),
        "dispatch_summary": audit.get("dispatch_summary"),
        "dispatch_blockers": audit.get("dispatch_blockers", []),
    }


def _run_id_from_stdout(stdout):
    """Extract run_id from the runner's [FinalStatus] line if present."""
    for line in reversed(stdout.splitlines()):
        marker = "[FinalStatus] "
        if marker in line:
            try:
                return json.loads(line.split(marker, 1)[1]).get("run_id")
            except ValueError:
                return None
    return None


def _trim_tasks():
    while len(TASKS) > MAX_RETAINED_TASKS:
        oldest = min(TASKS, key=lambda key: TASKS[key].get("started_at", ""))
        del TASKS[oldest]

def run_pipeline_thread(task_id):
    TASKS[task_id] = {
        "task_id": task_id,
        "status": "RUNNING",
        "started_at": _utc_now(),
        "completed_at": None,
        "returncode": None,
        "command": " ".join(PIPELINE_COMMAND),
        "stdout": "",
        "stderr": "",
        "error": None,
        "dispatch_audit_path": "docs/automation/V6_PLATFORM_NATIVE_VARIANTS/latest_dispatch_audit.json",
    }
    
    try:
        print(f"[Server] Task {task_id} started: executing live pipeline...")
        # Stream stdout and stderr in real-time
        process = subprocess.Popen(
            PIPELINE_COMMAND,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Helper to read stdout stream without blocking
        def read_stdout(proc, tid):
            for line in proc.stdout:
                TASKS[tid]["stdout"] += line
                print(f"[Server {tid}] {line.strip()}")
                
        # Helper to read stderr stream without blocking
        def read_stderr(proc, tid):
            for line in proc.stderr:
                TASKS[tid]["stderr"] += line
                print(f"[Server {tid} ERROR] {line.strip()}")

        t1 = threading.Thread(target=read_stdout, args=(process, task_id))
        t2 = threading.Thread(target=read_stderr, args=(process, task_id))
        t1.start()
        t2.start()
        
        # Wait for the subprocess to complete
        process.wait()
        t1.join()
        t2.join()
        
        TASKS[task_id]["returncode"] = process.returncode
        TASKS[task_id]["completed_at"] = _utc_now()

        # Trust the audit packet over the process return code so a blocked or
        # partial live launch can never be surfaced to the dashboard as success.
        run_id = _run_id_from_stdout(TASKS[task_id]["stdout"])
        audit = _read_dispatch_audit(run_id)
        if audit:
            TASKS[task_id].update({
                "run_id": audit.get("run_id"),
                "pipeline_status": audit.get("pipeline_status"),
                "dispatch_live": audit.get("dispatch_live"),
                "dispatch_summary": audit.get("dispatch_summary"),
                "dispatch_blockers": audit.get("dispatch_blockers", []),
            })

        pipeline_status = (audit or {}).get("pipeline_status")
        live_ok = pipeline_status in LIVE_SUCCESS_STATUSES if audit else (process.returncode == 0)
        if live_ok and process.returncode == 0:
            TASKS[task_id]["status"] = "SUCCESS"
            print(f"[Server] Task {task_id} completed successfully.")
        else:
            TASKS[task_id]["status"] = "FAILED"
            TASKS[task_id]["error"] = (
                f"Live launch not clean: pipeline_status={pipeline_status or 'unknown'} returncode={process.returncode}"
            )
            print(f"[Server] Task {task_id} did not achieve a clean live launch: {TASKS[task_id]['error']}")
            
    except Exception as e:
        TASKS[task_id]["status"] = "FAILED"
        TASKS[task_id]["completed_at"] = _utc_now()
        TASKS[task_id]["returncode"] = -1
        TASKS[task_id]["error"] = str(e)
        print(f"[Server] Task {task_id} encountered exception: {e}")

class PipelineServerHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def _send_json(self, status, payload):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode('utf-8'))

    def do_GET(self):
        parsed_url = urlparse(self.path)
        route = parsed_url.path
        
        if route == '/api/pipeline-status':
            qs = parse_qs(parsed_url.query)
            task_id = qs.get("task_id", [""])[0]
            
            if not task_id or task_id not in TASKS:
                self._send_json(404, {"error": "Task not found", "task_id": task_id or None})
                return

            self._send_json(200, TASKS[task_id])
        else:
            self._send_json(404, {"error": "Route not found", "route": route})

    def do_POST(self):
        parsed_url = urlparse(self.path)
        route = parsed_url.path
        
        if route == '/api/run-pipeline':
            task_id = str(uuid.uuid4())
            thread = threading.Thread(target=run_pipeline_thread, args=(task_id,))
            thread.daemon = True
            thread.start()
            _trim_tasks()

            response = {
                "status": "RUNNING",
                "task_id": task_id,
                "dispatch_audit_path": "docs/automation/V6_PLATFORM_NATIVE_VARIANTS/latest_dispatch_audit.json",
            }
            self._send_json(200, response)
        else:
            self._send_json(404, {"error": "Route not found", "route": route})

def run_server(port=5174):
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, PipelineServerHandler)
    print(f"Pipeline HTTP Server running on http://127.0.0.1:{port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
