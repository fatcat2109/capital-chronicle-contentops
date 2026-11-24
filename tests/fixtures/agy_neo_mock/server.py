"""CC-798 test fixture: a local mock composer that logs every request (no outside access).

Copied from the Ops Advisor's 24 Nov mock; adds a post id and a readback page per post.
Usage: python -I server.py <port> <log.jsonl> <composer.html>
"""
import html, json, sys, time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

LOG = Path(sys.argv[2])
PAGE = Path(sys.argv[3]).read_bytes()
POSTS = {}


class Handler(BaseHTTPRequestHandler):
    def _log(self, body=None):
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"t": time.time(), "method": self.command, "path": self.path, "body": body},
                               ensure_ascii=False) + "\n")

    def _send(self, body, kind="text/html; charset=utf-8"):
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._log()
        if self.path.startswith("/composer"):
            return self._send(PAGE)
        if self.path.startswith("/status/") and self.path[8:] in POSTS:
            text = html.escape(POSTS[self.path[8:]])
            return self._send(("<html><body><p id='author'>@Capitalnicle</p><p id='post-id'>" + self.path[8:]
                               + "</p><pre id='text'>" + text + "</pre></body></html>").encode("utf-8"))
        self._send(b"<html><body>ok</body></html>")

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n).decode("utf-8", "replace")
        self._log(body)
        if self.path == "/post":
            post_id = str(1000 + len(POSTS) + 1)
            POSTS[post_id] = body
            return self._send(json.dumps({"ok": True, "id": post_id}).encode(), "application/json")
        self._send(b'{"ok":true}', "application/json")

    def log_message(self, *a):
        pass


HTTPServer(("127.0.0.1", int(sys.argv[1])), Handler).serve_forever()
