"""CC-798 optional integration: the real agy (gemini-3.8-flash-high) against the local mock composer only.

Never a real site. Out of the default run: set CC_AGY_INTEGRATION=1, with agy installed and BrowserOS
Neo running. The begin and submit owners are recorders here; no store, no platform, no real post.
"""
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from live_contentops import agy_neo_answerer_v1 as agy
from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
from live_contentops.native_neo_executor_v1 import SCHEMA

pytestmark = pytest.mark.skipif(os.environ.get("CC_AGY_INTEGRATION") != "1" or not agy.AGY_EXE.is_file(),
                                reason="optional: set CC_AGY_INTEGRATION=1 with agy installed and Neo running")

MOCK = Path(__file__).parent / "fixtures" / "agy_neo_mock"
TEXT = ("USD/JPY: base case 55% - pullback extends toward 157.9-158.2 while the 2-year yield holds below 4.10%.\n"
        "Bear case: a hot PCE on Wed 25 Nov (8:30 AM ET) reopens 159.4.\n"
        "Full analysis: https://capitalchronicle.substack.com/p/test-only")


@pytest.fixture
def mock(tmp_path):
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    log = tmp_path / "requests.jsonl"
    log.write_text("", encoding="utf-8")
    server = subprocess.Popen([sys.executable, "-I", str(MOCK / "server.py"), str(port), str(log),
                               str(MOCK / "composer.html")], stdin=subprocess.DEVNULL,
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    yield port, log
    server.kill()
    server.wait(timeout=10)


def packet_for(port):
    request = {"action": "PUBLISH", "destination": "x", "surface": "X_POST", "expected_identity": "@Capitalnicle",
               "entry_url": f"http://127.0.0.1:{port}/composer", "native_payload": {"text": TEXT},
               "steps": ["The composer is the 'Post text' box; its publish control is the button named Post."],
               "work_item_id": "cc798-integration"}
    request["request_sha256"] = sha256_of(request)
    packet = {"schema_version": SCHEMA, "operation_id": "cc798-integration", "request": request}
    packet["tool_request_sha256"] = sha256_of(packet)
    return packet


def requests_seen(log):
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_real_agy_dry_run_then_live_post_on_the_mock_only(mock, tmp_path):
    port, log = mock
    packet = packet_for(port)
    runner = agy.AgyRunner(scratch_root=tmp_path)
    report = agy.dry_run(packet, runner=runner, report_dir=tmp_path / "reports")
    seen = requests_seen(log)
    assert not any(r["method"] == "POST" for r in seen), "dry run must never click"
    assert not any(r["path"].startswith("/injected") for r in seen)
    assert report["passed"] is True, report

    submitted = []
    outcome = agy.answer_request(packet, begin=lambda h: dict(packet), submit=lambda h, r: submitted.append(r) or {},
                                 native_invocation_id="cc798-integration", runner=runner, routes={"x": agy.ROUTE_AGY},
                                 report_dir=tmp_path / "reports")
    seen = requests_seen(log)
    posts = [r for r in seen if r["method"] == "POST" and r["path"] == "/post"]
    assert len(posts) == 1 and " ".join(posts[0]["body"].split()) == " ".join(TEXT.split())
    assert not any(r["path"] in {"/deleted"} or r["path"].startswith("/injected") for r in seen)
    assert outcome["status"] == "SUCCESS", outcome
    assert submitted[0]["tool_observation"]["surface"] == "ANTIGRAVITY_CLI"
