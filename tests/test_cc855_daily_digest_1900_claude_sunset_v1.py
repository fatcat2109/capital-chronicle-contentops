"""CC-855 ContentOps Blocker C1 offline hermetic tests: 19:00 digest Claude sunset migration.

Zero live browser, zero network, zero writes to A:\\, zero Claude/agy CLI invocations,
zero-byte delta on daily_app_outputs/tradingview_snapshot_outcomes_v1.jsonl.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import importlib.util
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace
import xml.etree.ElementTree as ET

import pytest

from live_contentops import daily_digest_neo_v1 as digest_neo
from live_contentops import day_readback_v1 as day_readback
from live_contentops import llm_operator_control_v1 as llm_control
from live_contentops import native_desktop_publication_v1 as pub_policy
from live_contentops import published_content_v1 as published
from live_contentops.durable_operational_store_v1 import ContentOpsDurableStore
from live_contentops.event_article_guard_v1 import PUBLIC_NOTICE
from live_contentops.native_neo_executor_v1 import SURFACE_TOOLS

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "run_daily_digest_1900.py"
TASK_XML = REPO_ROOT / "config" / "task_scheduler" / "CapitalChronicle_ContentOps_Daily_Digest_1900_CC855.xml"

_spec = importlib.util.spec_from_file_location("run_daily_digest_1900_cc855", SCRIPT)
route = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(route)


def _utc(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def _seal_feed_row(raw: dict) -> dict:
    row = {
        "schema_version": published.SCHEMA,
        "type": "ARTICLE",
        "event_id": None,
        "conditional_calls": [],
        "rights_class": "CC_OWN_ANALYSIS",
        "visibility": "public",
        "disclaimer": PUBLIC_NOTICE,
        "conflicts_notice": None,
        **raw,
    }
    row.pop("content_sha256", None)
    row["content_sha256"] = sha256(published.canonical(row)).hexdigest()
    return row


def _setup_isolated_env(tmp_path: Path, monkeypatch, *, articles: list[dict] | None = None):
    """Create an isolated SQLite store, confirmed feed, and rollout with zero live A:\\ access."""
    store_path = tmp_path / "contentops_daily_app_v1.sqlite3"
    output_root = tmp_path / "daily_app_outputs"
    output_root.mkdir(parents=True, exist_ok=True)
    control_root = tmp_path / "control"
    control_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(llm_control, "RUNTIME_CONTROL_ROOT", control_root)

    store = ContentOpsDurableStore(store_path)
    control = store.get_operating_control()
    store.update_operating_control(
        operating_mode="AUTONOMOUS_DEFAULT",
        expected_state_version=control["state_version"],
        control_source="TEST_CC855",
    )

    feed_path = tmp_path / "published_content_v1.jsonl"
    feed_path.touch()
    rows = articles if articles is not None else [
        {
            "content_id": "substack:226100001",
            "title": "Gold steady after US payrolls",
            "standfirst": "Bullion held near 4,100 after the payroll report left rate odds balanced.",
            "published_at_utc": "2026-12-05T09:30:00Z",
            "recorded_at_utc": "2026-12-05T09:35:00Z",
            "outlets": [
                {"name": "substack", "url": "https://capitalchronicle.substack.com/p/gold-steady-after-us-payrolls"},
            ],
        }
    ]
    for r in rows:
        published.append_record(feed_path, _seal_feed_row(r))

    rollout_path = tmp_path / "native_desktop_rollout_v1.json"
    rollout = {
        "schema_version": "contentops.native_desktop_rollout.v1",
        "owner": "NATIVE_CODEX_DESKTOP",
        "store_path": str(store_path),
        "editorial_output_root": str(output_root),
        "published_output_root": str(output_root),
        "public_write_authority": True,
        "target_status": "AUTHORIZED_LIVE_TRANSITION",
    }
    rollout_path.write_text(json.dumps(rollout), encoding="utf-8")

    monkeypatch.setattr(published, "PRODUCTION_STORE", store_path)
    monkeypatch.setattr(published, "DEFAULT_FEED", feed_path)
    monkeypatch.setattr(pub_policy, "live_publication_policy", lambda cfg, **kw: None)
    return store, store_path, feed_path, output_root, rollout_path


class _FakeDigestNeoClient:
    """In-memory BrowserOS Neo MCP client for hermetic Substack DAILY_EMAIL_DIGEST tests."""

    def __init__(
        self,
        *,
        email_initially_checked: bool = True,
        email_stays_unchecked: bool = False,
        trigger_email_code: bool = False,
        email_recipients: int | None = 5,
        card_path_provider=None,
    ):
        self.initialized = False
        self.email_checked = email_initially_checked
        self.email_stays_unchecked = email_stays_unchecked
        self.trigger_email_code = trigger_email_code
        self.email_recipients = email_recipients
        self.card_path_provider = card_path_provider
        self.pages: dict[str, int] = {}
        self.next_page = 100
        self.publish_clicks = 0
        self.calls: list[tuple[str, str]] = []
        self.pasted_html: str | None = None
        self.uploaded_files: list[str] = []
        self.draft_title: str = ""
        self.draft_subtitle: str = ""
        self.published_id = "226900123"
        self.published_url = "https://capitalchronicle.substack.com/p/capital-chronicle-daily-digest-december-5"
        self.image_url = "https://substack-post-media.s3.amazonaws.com/public/images/cc855-card_1600x900.png"
        self.image_http = self._make_image_http()

    def _make_image_http(self):
        client = self

        class _FakeResp:
            status_code = 200

            def raise_for_status(self):
                return None

            def iter_content(self, size):
                path = Path(client.uploaded_files[-1]) if client.uploaded_files else client.card_path_provider()
                return iter([path.read_bytes()])

            def close(self):
                return None

        class _FakeSession:
            def get(self, url, **kwargs):
                assert url == client.image_url
                return _FakeResp()

        return _FakeSession()

    def initialize(self):
        self.initialized = True

    def open(self, destination, url):
        self.calls.append(("open", f"{destination}:{url}"))
        if destination not in self.pages:
            self.next_page += 1
            self.pages[destination] = self.next_page
        return self.pages[destination]

    def wait(self, page, selector):
        self.calls.append(("wait", selector))

    def wait_text(self, page, text):
        self.calls.append(("wait_text", text))

    def snapshot(self, page):
        if self.trigger_email_code and self.publish_clicks > 0:
            return {
                "url": f"https://capitalchronicle.substack.com/publish/post/{self.published_id}",
                "text": 'dialog "Check your email"\nEnter the 6-digit code',
                "refs": [],
            }
        return {
            "url": f"https://capitalchronicle.substack.com/publish/posts/detail/{self.published_id}/share-center",
            "text": f"Copy link {self.published_url}",
            "refs": [
                {"role": "button", "name": "Create", "ref": "r1"},
                {"role": "menuitem", "name": "Article", "ref": "r2"},
                {"role": "textbox", "name": "title", "ref": "r3"},
                {"role": "textbox", "name": "Add a subtitle…", "ref": "r4"},
                {"role": "button", "name": "Insert image", "ref": "r5"},
                {"role": "menuitem", "name": "Image", "ref": "r6"},
                {"role": "button", "name": "CC466 editor upload", "ref": "r7"},
                {"role": "button", "name": "Continue", "ref": "r8"},
                {"role": "checkbox", "name": "Send via email and the Substack app", "ref": "r9"},
                {"role": "button", "name": "Send to everyone now", "ref": "r10"},
            ],
        }

    def act(self, page, kind, **values):
        self.calls.append(("act", f"{kind}:{values.get('ref')}"))
        if kind == "fill" and values.get("ref") == "r3":
            self.draft_title = values["value"]
        elif kind == "fill" and values.get("ref") == "r4":
            self.draft_subtitle = values["value"]
        elif kind == "click" and values.get("ref") == "r9" and not self.email_stays_unchecked:
            self.email_checked = not self.email_checked
        return {"ok": True}

    def call(self, name, arguments):
        self.calls.append(("call", name))
        if name == "upload":
            self.uploaded_files.extend(arguments["files"])
            return {"ok": True}
        if name == "run":
            code = arguments["code"]
            prefix_line = code.splitlines()[0]
            payload = json.loads(prefix_line.removeprefix("const input=").rstrip(";"))
            phase = payload["phase"]
            self.calls.append(("digest_js", phase))
            if phase == "digest_substack_delivery_controls":
                return {
                    "structuredContent": {
                        "ok": True,
                        "value": {
                            "email_found": True,
                            "email_send_enabled": self.email_checked,
                            "schedule_enabled": False,
                            "web_only_button_present": False,
                            "publish_button_name": "Send to everyone now",
                            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                        },
                    }
                }
            if phase == "digest_substack_publish_email":
                if not self.email_checked:
                    return {
                        "structuredContent": {
                            "ok": True,
                            "value": {
                                "status": "FAILED_BEFORE_WRITE",
                                "definite_no_write": True,
                                "public_write_performed": False,
                                "stage": "BEFORE_PUBLISH_CLICK",
                                "reason_code": "DIGEST_EMAIL_SEND_NOT_CONFIRMED",
                            },
                        }
                    }
                self.publish_clicks += 1
                return {
                    "structuredContent": {
                        "ok": True,
                        "value": {
                            "status": "CLICKED",
                            "button_name": "Send to everyone now",
                            "dispatched_at_utc": datetime.now(timezone.utc).isoformat(),
                            "email_send_enabled": True,
                            "web_publish_enabled": True,
                        },
                    }
                }
            if phase == "digest_substack_readback_links":
                return {
                    "structuredContent": {
                        "ok": True,
                        "value": {
                            "observed_links": [
                                {
                                    "text": "Gold steady after US payrolls",
                                    "url": "https://capitalchronicle.substack.com/p/gold-steady-after-us-payrolls",
                                }
                            ],
                            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                        },
                    }
                }
            if phase == "digest_substack_email_stats":
                if self.email_recipients:
                    return {
                        "structuredContent": {
                            "ok": True,
                            "value": {
                                "dashboard_url": f"https://capitalchronicle.substack.com/publish/posts/detail/{self.published_id}",
                                "shown": f"Recipients {self.email_recipients}; Open rate 20%; 1 open",
                                "recipients": self.email_recipients,
                                "opens": 1,
                                "open_rate_percent": 20.0,
                                "email_delivery_confirmed": True,
                                "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                            },
                        }
                    }
                return {
                    "structuredContent": {
                        "ok": True,
                        "value": {
                            "dashboard_url": f"https://capitalchronicle.substack.com/publish/posts/detail/{self.published_id}",
                            "shown": "Data still processing; Recipients -",
                            "recipients": None,
                            "opens": None,
                            "open_rate_percent": None,
                            "email_delivery_confirmed": False,
                            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                        },
                    }
                }
        raise AssertionError(f"Unexpected call({name!r})")

    @staticmethod
    def value(result):
        return result.get("structuredContent")

    def run(self, page, phase, **values):
        self.calls.append(("run", phase))
        if phase == "plan_substack_identity":
            return {
                "authenticated": True,
                "observed_identity": "capitalchronicle.substack.com",
                "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        if phase == "plan_substack_intercept":
            return {"installed": True}
        if phase == "plan_substack_uploaded":
            return {"src": self.image_url}
        if phase == "plan_substack_clear":
            return {"sent": True}
        if phase == "plan_substack_paste":
            self.pasted_html = values["html"]
            return {"sent": True}
        if phase == "plan_substack_check":
            return {"verified": True, "spacing_only_mismatch": False, "pre_click_body": values["expected_text"]}
        if phase == "plan_substack_front":
            return {"front": True}
        if phase == "plan_substack_published":
            return {
                "public_object_id": self.published_id,
                "public_object_url": self.published_url,
                "share_center_reached_utc": datetime.now(timezone.utc).isoformat(),
            }
        if phase == "plan_substack_code_handoff":
            return {
                "draft_id": self.published_id,
                "page_id": page,
                "page_url": f"https://capitalchronicle.substack.com/publish/post/{self.published_id}",
            }
        if phase == "plan_substack_readback":
            body_text = (
                "Gold steady after US payrolls\n\n"
                "Bullion held near 4,100 after the payroll report left rate odds balanced.\n\n"
                + PUBLIC_NOTICE
            )
            caption = "Capital Chronicle daily digest, December 5, 2026 (ET)"
            alt = caption + ": Gold steady after US payrolls"
            return {
                "status": "SUCCESS",
                "observed_identity": "capitalchronicle.substack.com",
                "public_object_url": self.published_url,
                "observed_text": f"{self.draft_title}\n{self.draft_subtitle}\n{body_text}\n{caption}",
                "article_text": f"{body_text}\n{caption}",
                "published_at_utc": "2026-12-05T12:16:00Z",
                "public_image_urls": [self.image_url],
                "media": [{"alt_text": alt, "caption": caption}],
                "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            }
        raise AssertionError(f"Unexpected phase: {phase}")


def test_c5_profiles_and_claude_agy_fail_closed():
    stamp = "20261205T121500Z"
    for name, profile in route.ROUTE_PROFILES.items():
        resolved = route.resolve_profile(name)
        assert SURFACE_TOOLS[resolved["surface"]] == resolved["tool_name"]
        assert resolved["tool_name"] != "mcp__browseros-neo__run"  # Hyphenated Claude tool forbidden on non-Claude surfaces.
        assert "CLAUDE" not in str(resolved["surface"]).upper()
        assert "CLAUDE" not in str(resolved["route"]).upper()
        assert "AGY" not in str(resolved["surface"]).upper()
        assert route._extract_scheduled_stamp(str(resolved["invocation_prefix"]) + stamp) == stamp
    # Legacy Claude prefix stays recognized strictly for read-only _empty_digest_readback replay.
    assert route._extract_scheduled_stamp("claude-code-session:cc143-digest-1900:" + stamp) == stamp
    assert route.DEFAULT_DRIVER == "python-neo"
    assert route.SURFACE == "NEO_ENDPOINT_EXECUTOR"
    assert route.TOOL == SURFACE_TOOLS[route.SURFACE] == "browseros-neo/run"
    cmds = route._commands("config/native_desktop_rollout_v1.json", route.default_invocation_id(_utc("2026-12-05T12:15:00Z")))
    assert "scripts/run_day_readback.py --run-dir" in cmds["day_readback"]

    for retired in ("claude", "claude-cli", "claude-desktop", "claude-legacy"):
        with pytest.raises(ValueError, match="CLAUDE_ROUTE_RETIRED_CC855"):
            route.resolve_profile(retired)
    for blocked in ("agy", "antigravity", "antigravity-cli"):
        with pytest.raises(ValueError, match="AGY_BLOCKED_TERMS_OF_SERVICE_20261124"):
            route.resolve_profile(blocked)


def test_digest_neo_public_copy_guard_and_delivery_invariants():
    good = {
        "title": "Capital Chronicle daily digest — December 5, 2026 (ET)",
        "subtitle": "Gold steady after US payrolls",
        "body_markdown": (
            "**[Gold steady after US payrolls](https://capitalchronicle.substack.com/p/gold-steady-after-us-payrolls)**\n\n"
            "Bullion held steady after the 08:30 EST payroll release.\n\n"
            + PUBLIC_NOTICE
        ),
    }
    digest_neo.validate_digest_public_copy(good)

    html = digest_neo.digest_body_html(
        good["body_markdown"],
        figure_html='<figure><img src="https://img.test/a.png" alt="a"><figcaption>c</figcaption></figure>',
        placement_after="lead",
    )
    assert html.startswith('<p><strong><a href="https://capitalchronicle.substack.com/p/gold-steady-after-us-payrolls">')
    assert html.index("</p><figure>") > 0  # Image placed right after lead paragraph.

    # Escaped brackets in markdown title round-trip cleanly.
    escaped = "**[US \\[CPI\\] preview](https://capitalchronicle.substack.com/p/cpi)**"
    assert digest_neo.digest_body_text(escaped) == "US [CPI] preview"
    assert ">US [CPI] preview</a>" in digest_neo.digest_body_html(escaped)

    # CC-691 & public filter rejections:
    with pytest.raises(ValueError, match="PUBLIC_TIMEZONE_ET_REQUIRED"):
        digest_neo.validate_digest_public_copy({**good, "body_markdown": good["body_markdown"] + "\n19:15 GMT+7"})
    with pytest.raises(ValueError, match="PLAN_ANALYSIS_DESK_AI_LABEL_FORBIDDEN"):
        digest_neo.validate_digest_public_copy({**good, "body_markdown": good["body_markdown"] + "\nWritten by Claude."})
    with pytest.raises(ValueError, match="PUBLIC_PLAN_TARGET_PRESENT"):
        digest_neo.validate_digest_public_copy({**good, "body_markdown": good["body_markdown"] + "\nTake-profit at 4,250."})
    with pytest.raises(ValueError, match="DIGEST_PUBLIC_NOTICE_MISSING"):
        digest_neo.validate_digest_public_copy({**good, "body_markdown": "Headline without notice."})
    with pytest.raises(ValueError, match="PREVIEW_HOST_LINK_FORBIDDEN"):
        digest_neo.validate_digest_public_copy({
            **good,
            "body_markdown": good["body_markdown"] + "\nhttps://fatcat2109.github.io/capital-chronicle-preview/",
        })
    with pytest.raises(ValueError, match="DIGEST_FORBIDDEN_DRAFT_LINK"):
        digest_neo.validate_digest_public_copy({
            **good,
            "body_markdown": good["body_markdown"] + "\nhttps://capitalchronicle.substack.com/publish/post/123",
        })

    # Separation from WEB_ONLY plan pages:
    with pytest.raises(ValueError, match="DIGEST_SUBSTACK_EXACT_OPERATION_REQUIRED"):
        digest_neo.perform_digest_action(
            _FakeDigestNeoClient(),
            {"operation_id": "plan-analysis-plan_123", "request": {"destination": "substack", "action": "PUBLISH"}},
        )
    web_only_res = digest_neo.perform_digest_action(
        _FakeDigestNeoClient(),
        {
            "operation_id": "cc143-digest-2026-12-05",
            "request": {
                "destination": "substack",
                "action": "PUBLISH",
                "substack_delivery_policy": {"mode": "WEB_ONLY", "email_send_enabled": False, "web_publish_enabled": True},
            },
        },
    )
    assert web_only_res["result"]["status"] == "FAILED_BEFORE_WRITE"
    assert web_only_res["result"]["reason_code"] == "DIGEST_SUBSTACK_EMAIL_DELIVERY_POLICY_REQUIRED"


def test_unattended_python_neo_run_confirms_digest_and_writes_day_readback(tmp_path, monkeypatch):
    store, _, _, output_root, rollout_path = _setup_isolated_env(tmp_path, monkeypatch)
    fake_client = _FakeDigestNeoClient(email_initially_checked=False, email_recipients=5)
    post_sunset = _utc("2026-12-05T12:15:00Z")  # 19:15 GMT+7, post Fri 04 Dec Claude sunset

    result = route.run_digest_1900(
        rollout_path,
        driver="python-neo",
        now=post_sunset,
        lock_path=tmp_path / "digest.lock",
        stop_path=tmp_path / "digest.stop",
        endpoint_client=fake_client,
        stored_only_readback=True,
    )
    assert result["route"] == "WINDOWS_SCHEDULER_PYTHON_NEO_1900"
    assert result["surface"] == "NEO_ENDPOINT_EXECUTOR"
    assert result["tool_name"] == "browseros-neo/run"
    assert result["route_state"] == "CONFIRMED"
    assert result["email_delivery_confirmed"] is True
    assert result["public_write_performed"] is True
    assert result["public_object_id"] == fake_client.published_id
    assert result["public_object_url"] == fake_client.published_url
    assert [r["action"] for r in result["requests_handled"]] == ["VERIFY_IDENTITY", "PUBLISH", "READBACK"]
    assert fake_client.publish_clicks == 1
    assert fake_client.email_checked is True  # Auto-toggled email send ON and verified before click!

    run_dir = Path(result["run_dir"])
    assert (run_dir / "01-preflight.json").is_file()
    assert (run_dir / "result.json").is_file()
    assert result["day_readback"]["state"] == "READBACK_WRITTEN"
    assert (run_dir / "day_readback.json").is_file()
    assert (run_dir / "day_readback.md").is_file()
    assert (run_dir / "decision_checks.json").is_file()

    # Verify day_readback parsed our observation's Substack post stats (Recipients 5, 1 open, 20%).
    readback_doc = json.loads((run_dir / "day_readback.json").read_bytes())
    assert readback_doc["digest"]["state"] == "CONFIRMED"
    assert readback_doc["digest"]["recipients"] == 5
    assert readback_doc["digest"]["opens"] == 1
    assert readback_doc["digest"]["open_rate_percent"] == 20
    assert readback_doc["digest"]["email_confirmed"] is True

    # Re-running same day is idempotent: zero additional browser clicks or writes.
    fake_client_2 = _FakeDigestNeoClient()
    second = route.run_digest_1900(
        rollout_path,
        driver="python-neo",
        now=post_sunset + timedelta(minutes=5),
        lock_path=tmp_path / "digest.lock",
        stop_path=tmp_path / "digest.stop",
        endpoint_client=fake_client_2,
        stored_only_readback=True,
    )
    assert second["route_state"] == "CONFIRMED"
    assert second["requests_handled"] == []
    assert second["public_write_performed"] is False
    assert fake_client_2.publish_clicks == 0


def test_python_neo_refuses_publish_when_email_send_checkbox_cannot_be_confirmed(tmp_path, monkeypatch):
    _, _, _, _, rollout_path = _setup_isolated_env(tmp_path, monkeypatch)
    fake_client = _FakeDigestNeoClient(email_initially_checked=False, email_stays_unchecked=True)

    result = route.run_digest_1900(
        rollout_path,
        driver="python-neo",
        now=_utc("2026-12-05T12:15:00Z"),
        lock_path=tmp_path / "digest.lock",
        stop_path=tmp_path / "digest.stop",
        endpoint_client=fake_client,
        stored_only_readback=True,
    )
    assert result["route_state"] == "FAILED_BEFORE_WRITE"
    assert result["first_blocking_cause"] == "DIGEST_EMAIL_SEND_NOT_CONFIRMED"
    assert result["public_write_performed"] is False
    assert fake_client.publish_clicks == 0
    assert result["day_readback"]["state"] == "READBACK_WRITTEN"


def test_python_neo_records_pending_jim_email_code_without_retry_or_gmail(tmp_path, monkeypatch):
    _, _, _, _, rollout_path = _setup_isolated_env(tmp_path, monkeypatch)
    fake_client = _FakeDigestNeoClient(trigger_email_code=True)

    result = route.run_digest_1900(
        rollout_path,
        driver="python-neo",
        now=_utc("2026-12-05T12:15:00Z"),
        lock_path=tmp_path / "digest.lock",
        stop_path=tmp_path / "digest.stop",
        endpoint_client=fake_client,
        stored_only_readback=True,
    )
    assert result["route_state"] == "PENDING_JIM_EMAIL_CODE"
    assert result["jim_email_code_pending"] is True
    assert result["public_write_performed"] is False
    assert fake_client.publish_clicks == 1
    assert not any("mail.google.com" in arg for _, arg in fake_client.calls)
    assert result["day_readback"]["state"] == "READBACK_WRITTEN"


def test_empty_day_early_wake_stop_sentinel_pause_and_lock_guards(tmp_path, monkeypatch):
    _, _, _, output_root, rollout_path = _setup_isolated_env(tmp_path, monkeypatch, articles=[])
    lock_path = tmp_path / "digest.lock"
    stop_path = tmp_path / "digest.stop"

    # 1) Early wake (18:59 GMT+7) stops cleanly without creating route-1900 folder.
    early = route.run_digest_1900(
        rollout_path, now=_utc("2026-12-05T11:59:00Z"), lock_path=lock_path, stop_path=stop_path,
        stored_only_readback=True,
    )
    assert early["route_state"] == "NOT_YET_DUE" and not early["public_write_performed"]
    assert not (output_root / "owner-manual" / "route-1900").exists()

    # 2) Empty due day writes result.json + evening day_readback with 0 browser calls.
    class _FailIfCalledClient:
        def initialize(self):
            pytest.fail("browser should not be contacted on NO_CONFIRMED_ARTICLES")

    empty = route.run_digest_1900(
        rollout_path, now=_utc("2026-12-05T12:15:00Z"), lock_path=lock_path, stop_path=stop_path,
        endpoint_client=_FailIfCalledClient(), stored_only_readback=True,
    )
    assert empty["route_state"] == "NO_CONFIRMED_ARTICLES" and not empty["public_write_performed"]
    assert empty["day_readback"]["state"] == "READBACK_WRITTEN"

    # 2b) _empty_digest_readback accepts BOTH new non-Claude prefix AND legacy Claude prefix.
    for stamp, prefix in (
        ("20261205T121600Z", "windows-scheduler-neo:cc143-digest-1900:"),
        ("20261205T121700Z", "codex-exec-astra:cc143-digest-1900:"),
        ("20261205T121800Z", "claude-code-session:cc143-digest-1900:"),
    ):
        rdir = output_root / "owner-manual" / "route-1900" / stamp
        rdir.mkdir(parents=True, exist_ok=True)
        res_empty = route.resume(rollout_path, prefix + stamp, now=_utc("2026-12-05T12:18:00Z"))
        assert res_empty["route_state"] == "NO_CONFIRMED_ARTICLES"
        assert res_empty["day_readback"]["state"] == "READBACK_WRITTEN"
        assert (rdir / "day_readback.json").is_file() and (rdir / "day_readback.md").is_file()

    # 3) Persistent LLM operator pause blocks cleanly before any digest action.
    llm_control.activate_llm_operator_pause()
    paused = route.run_digest_1900(
        rollout_path, now=_utc("2026-12-05T12:20:00Z"), lock_path=lock_path, stop_path=stop_path,
        endpoint_client=_FailIfCalledClient(), stored_only_readback=True,
    )
    assert paused["route_state"] == "BLOCKED"
    assert "LLM_OPERATOR_PAUSED" in paused["blockers"]
    llm_control.resume_llm_operator_execution()

    # 4) .stop sentinel exits cleanly before acquiring lock or reading store.
    stop_path.write_text("stopped\n", encoding="utf-8")
    stopped = route.run_digest_1900(
        rollout_path, now=_utc("2026-12-05T12:25:00Z"), lock_path=lock_path, stop_path=stop_path,
    )
    assert stopped["route_state"] == "STOP_SENTINEL_ACTIVE"
    stop_path.unlink()

    # 5) Held OS lock prevents concurrent duplicate run.
    with route._single_instance_lock(lock_path) as first_acquired:
        assert first_acquired is True
        contended = route.run_digest_1900(
            rollout_path, now=_utc("2026-12-05T12:30:00Z"), lock_path=lock_path, stop_path=stop_path,
        )
        assert contended["route_state"] == "LOCK_HELD" and contended["public_write_performed"] is False


def test_codex_astra_driver_serializes_codex_launch_slot_and_strips_api_keys(tmp_path, monkeypatch):
    _, _, _, _, rollout_path = _setup_isolated_env(tmp_path, monkeypatch)
    slot_file = tmp_path / "codex-launch-slot.txt"

    # Refuse touching the live slot file during pytest when no override is passed.
    monkeypatch.delenv(route.CODEX_LAUNCH_SLOT_ENV, raising=False)
    with pytest.raises(RuntimeError, match="REFUSING_LIVE_CODEX_SLOT_IN_TEST"):
        route.acquire_codex_launch_slot(key="test-key")

    # Pre-seed slot 30 seconds before current clock -> must sleep >= 60 seconds (90s gap).
    t0 = _utc("2026-12-05T12:14:30Z")
    slot_file.write_bytes(route.format_codex_slot_line(t0, "other-lane", "daily_pass"))
    slept: list[float] = []
    clock_state = [_utc("2026-12-05T12:15:00Z")]

    def fake_sleep(sec):
        slept.append(sec)
        clock_state[0] = clock_state[0] + timedelta(seconds=sec)

    monkeypatch.setenv("OPENAI_API_KEY", "sk-must-be-stripped")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-must-be-stripped")
    captured: dict = {}

    def fake_codex(args, *, cwd, env, input, timeout):
        captured["args"] = args
        captured["env"] = env
        captured["prompt"] = input.decode("utf-8")
        return SimpleNamespace(returncode=0, stdout=b'{"type":"turn.completed"}\n', stderr=b"")

    res = route.run_digest_1900(
        rollout_path,
        driver="codex-astra",
        now=clock_state[0],
        lock_path=tmp_path / "digest.lock",
        stop_path=tmp_path / "digest.stop",
        codex_runner=fake_codex,
        codex_slot_file=slot_file,
        codex_min_gap_seconds=90.0,
        codex_now_utc=lambda: clock_state[0],
        stored_only_readback=True,
        sleep=fake_sleep,
    )
    assert res["route"] == "WINDOWS_SCHEDULER_CODEX_ASTRA_1900"
    assert res["surface"] == "CODEX_EXEC"
    assert res["tool_name"] == "mcp__browseros_neo__run"
    assert res["codex_astra"]["configured_model"] == "gpt-6.2-astra"
    assert res["codex_astra"]["configured_reasoning_effort"] == "max"
    assert slept and slept[0] == pytest.approx(60.0)
    assert "--model" in captured["args"] and "gpt-6.2-astra" in captured["args"]
    assert 'model_reasoning_effort="max"' in captured["args"]
    assert "OPENAI_API_KEY" not in captured["env"]
    assert "ANTHROPIC_API_KEY" not in captured["env"]
    assert "claude" not in " ".join(captured["args"]).lower()
    assert "agy" not in " ".join(captured["args"]).lower()
    assert 'surface="CODEX_EXEC"' in captured["prompt"]
    assert slot_file.read_text(encoding="ascii").startswith("2026-12-05T12:16:00.000Z ")
    assert res["day_readback"]["state"] == "READBACK_WRITTEN"


def test_cc548_single_catch_up_pass_confirms_prior_and_todays_digest(tmp_path, monkeypatch):
    from live_contentops.substack_daily_digest_v1 import prepare_daily_digest

    articles = [
        {
            "schema_version": "contentops.published_content.v1",
            "content_id": "substack:226100001",
            "title": "Euro holds range after ECB minutes",
            "standfirst": "EUR/USD stayed near 1.0800 after the policy summary offered no surprise.",
            "published_at_utc": "2026-12-04T09:00:00Z",
            "recorded_at_utc": "2026-12-04T09:05:00Z",
            "outlets": [{"name": "substack", "url": "https://capitalchronicle.substack.com/p/euro-holds-range"}],
        },
        {
            "schema_version": "contentops.published_content.v1",
            "content_id": "substack:226100002",
            "title": "Gold steady after US payrolls",
            "standfirst": "Bullion held near 4,100 after the payroll report left rate odds balanced.",
            "published_at_utc": "2026-12-05T09:30:00Z",
            "recorded_at_utc": "2026-12-05T09:35:00Z",
            "outlets": [{"name": "substack", "url": "https://capitalchronicle.substack.com/p/gold-steady-after-us-payrolls"}],
        },
    ]
    store, _, feed_path, _, rollout_path = _setup_isolated_env(tmp_path, monkeypatch, articles=articles)
    # Pre-freeze yesterday's unsent digest (2026-12-04) so today's 19:15 run triggers 1 catch-up pass!
    prior_prep = prepare_daily_digest(store, feed_path, now=_utc("2026-12-04T12:15:00Z"))
    assert prior_prep["digest_id"] == "cc143-digest-2026-12-04"

    class _TwoPassFakeClient(_FakeDigestNeoClient):
        def __init__(self):
            super().__init__(email_initially_checked=True, email_recipients=5)
            self.pass_idx = 0

        def call(self, name, arguments):
            if name == "run":
                prefix_line = arguments["code"].splitlines()[0]
                payload = json.loads(prefix_line.removeprefix("const input=").rstrip(";"))
                if payload.get("phase") == "digest_substack_readback_links":
                    link = (
                        {"text": "Euro holds range after ECB minutes", "url": "https://capitalchronicle.substack.com/p/euro-holds-range"}
                        if self.pass_idx == 1
                        else {"text": "Gold steady after US payrolls", "url": "https://capitalchronicle.substack.com/p/gold-steady-after-us-payrolls"}
                    )
                    return {
                        "structuredContent": {
                            "ok": True,
                            "value": {"observed_links": [link], "observed_at_utc": datetime.now(timezone.utc).isoformat()},
                        }
                    }
            return super().call(name, arguments)

        def run(self, page, phase, **values):
            if phase == "plan_substack_published":
                self.pass_idx += 1
                self.published_id = f"22690020{self.pass_idx}"
                self.published_url = f"https://capitalchronicle.substack.com/p/capital-chronicle-daily-digest-pass-{self.pass_idx}"
            if phase == "plan_substack_readback":
                if self.pass_idx == 1:
                    body_text = (
                        "Euro holds range after ECB minutes\n\n"
                        "EUR/USD stayed near 1.0800 after the policy summary offered no surprise.\n\n"
                        + PUBLIC_NOTICE
                    )
                    caption = "Capital Chronicle daily digest, December 4, 2026 (ET)"
                    alt = caption + ": Euro holds range after ECB minutes"
                else:
                    body_text = (
                        "Gold steady after US payrolls\n\n"
                        "Bullion held near 4,100 after the payroll report left rate odds balanced.\n\n"
                        + PUBLIC_NOTICE
                    )
                    caption = "Capital Chronicle daily digest, December 5, 2026 (ET)"
                    alt = caption + ": Gold steady after US payrolls"
                return {
                    "status": "SUCCESS",
                    "observed_identity": "capitalchronicle.substack.com",
                    "public_object_url": self.published_url,
                    "observed_text": f"{self.draft_title}\n{self.draft_subtitle}\n{body_text}\n{caption}",
                    "article_text": f"{body_text}\n{caption}",
                    "published_at_utc": "2026-12-05T12:16:00Z",
                    "public_image_urls": [self.image_url],
                    "media": [{"alt_text": alt, "caption": caption}],
                    "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                }
            return super().run(page, phase, **values)

    fake_client = _TwoPassFakeClient()
    res = route.run_digest_1900(
        rollout_path,
        driver="python-neo",
        now=_utc("2026-12-05T12:15:00Z"),
        lock_path=tmp_path / "digest.lock",
        stop_path=tmp_path / "digest.stop",
        endpoint_client=fake_client,
        stored_only_readback=True,
    )
    assert len(res["passes"]) == 2
    assert res["passes"][0]["digest_id"] == "cc143-digest-2026-12-04"
    assert res["passes"][0]["route_state"] == "CONFIRMED"
    assert res["passes"][0]["catch_up_pass"] == "triggered"
    assert res["passes"][1]["digest_id"] == "cc143-digest-2026-12-05"
    assert res["passes"][1]["route_state"] == "CONFIRMED"
    assert res["passes"][1]["catch_up_pass"] == "completed_second_pass"
    assert fake_client.publish_clicks == 2
    assert res["day_readback"]["state"] == "READBACK_WRITTEN"


def test_task_scheduler_xml_is_disabled_matches_renderer_and_passes_com_validation():
    raw = TASK_XML.read_bytes()
    assert raw.count(b"\r") == 0 and not raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8")
    assert text.startswith('<?xml version="1.0"?>\n')
    assert text == digest_neo.render_digest_task_xml()

    ns = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
    root = ET.fromstring(text)
    assert root.findtext("t:RegistrationInfo/t:URI", namespaces=ns) == r"\CapitalChronicle-ContentOpsDailyDigest1900-V1"
    assert root.findtext("t:Principals/t:Principal/t:UserId", namespaces=ns) == "JP"
    assert root.findtext("t:Principals/t:Principal/t:LogonType", namespaces=ns) == "InteractiveToken"
    assert root.findtext("t:Settings/t:Enabled", namespaces=ns) == "false"
    assert root.findtext("t:Settings/t:MultipleInstancesPolicy", namespaces=ns) == "IgnoreNew"
    assert root.findtext("t:Triggers/t:CalendarTrigger/t:StartBoundary", namespaces=ns) == "2026-12-01T19:15:00+07:00"
    args_text = root.findtext("t:Actions/t:Exec/t:Arguments", namespaces=ns) or ""
    assert "run_daily_digest_1900.py" in args_text and "--driver python-neo" in args_text
    assert "claude" not in args_text.lower() and "agy" not in args_text.lower()

    if os.name == "nt":
        # Read-only in-memory Task Scheduler COM XML parser validation (0 live Task Scheduler mutations).
        ps = (
            "$raw = Get-Content -LiteralPath '" + str(TASK_XML).replace("'", "''") + "' -Raw -Encoding UTF8; "
            "$svc = New-Object -ComObject 'Schedule.Service'; "
            "$def = $svc.NewTask(0); "
            "$def.XmlText = $raw; "
            "if ($def.Settings.Enabled) { throw 'ENABLED_MUST_BE_FALSE' }; "
            "if ($def.Principal.UserId -ne 'JP') { throw 'USERID_MISMATCH' }; "
            "if ($def.Principal.LogonType -ne 3) { throw 'LOGONTYPE_MISMATCH' }; "
            "Write-Output ('COM_OK triggers=' + $def.Triggers.Count)"
        )
        done = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, check=True)
        assert "COM_OK triggers=1" in done.stdout


def test_repo_tradingview_snapshot_outcomes_zero_byte_delta():
    # Regression guard: CC-855 digest tests never create or mutate repo-level tradingview_snapshot_outcomes_v1.jsonl.
    outcomes = REPO_ROOT / "daily_app_outputs" / "tradingview_snapshot_outcomes_v1.jsonl"
    assert not outcomes.exists()
