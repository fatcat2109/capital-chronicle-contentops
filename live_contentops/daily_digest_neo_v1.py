"""CC-855 / CC-143: deterministic Substack DAILY_EMAIL_DIGEST Neo executor and task XML.

Pure orchestration over the existing NeoMcpClient (NEO_ENDPOINT_EXECUTOR / browseros-neo/run).
No direct network libraries, no environment reads, no LLM calls, no Claude or agy CLI.
Strict separation from plan_substack_neo_v1 (which enforces WEB_ONLY): this module accepts
ONLY cc143-digest-YYYY-MM-DD operations and enforces email_send_enabled=True + web_publish_enabled=True
before any publish click, preserving CC-691 public copy checks and Decision 52/54 email-code safety.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import time as time_mod
from typing import Any, Mapping
from xml.sax.saxutils import escape as xml_escape

from live_contentops.event_article_guard_v1 import PUBLIC_NOTICE
from live_contentops.neo_destination_handoff_v1 import _public_url, _substack_rendered_text, _text
from live_contentops.plan_analysis_pages_v1 import public_filter
from live_contentops.preview_link_guard_v1 import REASON as PREVIEW_LINK_REASON, find_forbidden_link
from live_contentops.public_decision_checks_v1 import plan_target_present
from live_contentops.public_time_v1 import require_public_time

DIGEST_OPERATION_RE = re.compile(r"^cc143-digest-\d{4}-\d{2}-\d{2}\Z")
DIGEST_STEPS = Path(__file__).with_name("daily_digest_neo_steps_v1.js")
DEFAULT_TASK_NAME = "CapitalChronicle-ContentOpsDailyDigest1900-V1"
DEFAULT_TASK_USER_ID = "JP"
DEFAULT_REPO_ROOT = Path(r"A:\Capital Chronicle\ContentOps")
DEFAULT_PYTHONW = Path(r"C:\Users\bullw\AppData\Local\Programs\Python\Python313\pythonw.exe")
DEFAULT_EMAIL_STATS_POLL_TIMEOUT_SECONDS = 1500.0
DEFAULT_EMAIL_STATS_POLL_INTERVAL_SECONDS = 120.0

# Markdown link with escaped brackets from substack_daily_digest_v1._link_title().
_MD_BOLD_LINK_RE = re.compile(r"\*\*\[((?:\\.|[^\]])+)\]\((https://[^\s<>()]+)\)\*\*")
_MD_LINK_RE = re.compile(r"\[((?:\\.|[^\]])+)\]\((https://[^\s<>()]+)\)")
_MD_BOLD_RE = re.compile(r"\*\*([^*\n]+)\*\*")


def supports_digest_operation(operation_id: str) -> bool:
    return isinstance(operation_id, str) and DIGEST_OPERATION_RE.fullmatch(operation_id) is not None


def _unescape_link_label(text: str) -> str:
    return text.replace("\\[", "[").replace("\\]", "]").replace("\\\\", "\\")


def _inline_html(text: str) -> str:
    """Render bold markdown links, plain HTTPS links, and bold spans to Substack editor HTML."""
    parts: list[str] = []
    pos = 0
    combined = re.compile(
        r"\*\*\[(?P<blabel>(?:\\.|[^\]])+)\]\((?P<burl>https://[^\s<>()]+)\)\*\*"
        r"|\[(?P<label>(?:\\.|[^\]])+)\]\((?P<url>https://[^\s<>()]+)\)"
        r"|\*\*(?P<bold>[^*\n]+)\*\*"
    )
    for match in combined.finditer(text):
        parts.append(escape(text[pos:match.start()]))
        if match.group("burl") is not None:
            label = escape(_unescape_link_label(match.group("blabel")))
            url = escape(match.group("burl"), quote=True)
            parts.append(f'<strong><a href="{url}">{label}</a></strong>')
        elif match.group("url") is not None:
            label = escape(_unescape_link_label(match.group("label")))
            url = escape(match.group("url"), quote=True)
            parts.append(f'<a href="{url}">{label}</a>')
        else:
            parts.append(f'<strong>{escape(match.group("bold"))}</strong>')
        pos = match.end()
    parts.append(escape(text[pos:]))
    return "".join(parts)


def digest_body_html(markdown_text: str, *, figure_html: str | None = None, placement_after: str = "lead") -> str:
    """Convert CC-143 digest markdown to Substack ProseMirror HTML with figure placed after lead."""
    paragraphs: list[str] = []
    for block in str(markdown_text or "").split("\n\n"):
        for line in block.splitlines():
            stripped = line.strip()
            if stripped:
                paragraphs.append("<p>" + _inline_html(stripped) + "</p>")
    if figure_html:
        if placement_after in {"lead", "introduction"} and paragraphs:
            paragraphs.insert(1, figure_html)
        else:
            paragraphs.append(figure_html)
    return "".join(paragraphs)


def digest_body_text(markdown_text: str) -> str:
    """Expected visible body text after Substack renders markdown links and bold spans."""
    text = _MD_BOLD_LINK_RE.sub(lambda m: _unescape_link_label(m.group(1)), str(markdown_text or ""))
    text = _MD_LINK_RE.sub(lambda m: _unescape_link_label(m.group(1)), text)
    text = _MD_BOLD_RE.sub(lambda m: m.group(1), text)
    return _substack_rendered_text(text)


def validate_digest_public_copy(native_payload: Mapping[str, Any]) -> None:
    """Enforce ContentOps public filters and CC-691 golden contracts before any browser write."""
    if not isinstance(native_payload, Mapping):
        raise ValueError("DIGEST_NATIVE_PAYLOAD_REQUIRED")
    title = str(native_payload.get("title") or "").strip()
    subtitle = str(native_payload.get("subtitle") or "").strip()
    body = str(native_payload.get("body_markdown") or "").strip()
    if not title or not body:
        raise ValueError("DIGEST_PUBLIC_COPY_INCOMPLETE")
    require_public_time({"title": title, "subtitle": subtitle, "body_markdown": body})
    if find_forbidden_link({"title": title, "subtitle": subtitle, "body_markdown": body}):
        raise ValueError(PREVIEW_LINK_REASON)
    if re.search(r"/publish/posts?/", "\n".join((title, subtitle, body)), re.I):
        raise ValueError("DIGEST_FORBIDDEN_DRAFT_LINK")
    if PUBLIC_NOTICE not in body:
        raise ValueError("DIGEST_PUBLIC_NOTICE_MISSING")
    combined = "\n".join(part for part in (title, subtitle, body) if part)
    public_filter(combined)
    if plan_target_present(combined):
        raise ValueError("PUBLIC_PLAN_TARGET_PRESENT")


def _run_digest_step(client: Any, page: int, phase: str, **values: Any) -> dict[str, Any]:
    """Execute one bounded JS helper from daily_digest_neo_steps_v1.js via NeoMcpClient."""
    from live_contentops.neo_endpoint_executor_v1 import NeoEndpointError

    prefix = "const input=" + json.dumps({"phase": phase, **values}) + ";\n"
    code = prefix + f"const page=browser.page({int(page)});\n" + DIGEST_STEPS.read_text(encoding="utf-8")
    result = client.value(client.call("run", {"code": code}))
    if not isinstance(result, dict) or result.get("ok") is not True:
        raise NeoEndpointError("NEO_RUN_FAILED_" + phase.upper())
    value = result.get("value")
    if isinstance(value, dict) and value.get("neo_output_file") and hasattr(client, "_read_dom_output"):
        value = client._read_dom_output(value["neo_output_file"])
    if not isinstance(value, dict):
        raise NeoEndpointError("NEO_RUN_RESULT_MISSING_" + phase.upper())
    return value


def _ref(client: Any, page: int, role: str, names: set[str] | str) -> str:
    allowed = {names} if isinstance(names, str) else set(names)
    values = [r for r in client.snapshot(page)["refs"] if r["role"] == role and r["name"] in allowed]
    if not values:
        raise ValueError("DIGEST_SUBSTACK_CONTROL_MISSING:" + sorted(allowed)[0])
    return values[-1]["ref"]


def _wait_or_code(client: Any, page: int, text: str) -> dict[str, Any]:
    from live_contentops.neo_endpoint_executor_v1 import NeoEndpointError

    try:
        client.wait_text(page, text)
    except (NeoEndpointError, ValueError):
        observed = client.snapshot(page)
        if "Check your email" in observed.get("text", ""):
            return observed
        raise
    return client.snapshot(page)


def _pending_code(client: Any, page: int, dispatched_at_utc: str, identity: Mapping[str, Any]) -> dict[str, Any]:
    screen = client.run(page, "plan_substack_code_handoff")
    return {
        "result": {
            "status": "PENDING_JIM_EMAIL_CODE",
            **screen,
            "observed_identity": identity.get("observed_identity"),
            "public_write_performed": False,
            "email_code_request_observed": True,
        },
        "identity": dict(identity),
        "dispatched_at_utc": dispatched_at_utc,
        "observation": {
            "action": "PUBLISH",
            "status": "PENDING_JIM_EMAIL_CODE",
            "screen": screen,
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        },
    }


def _verify_media_manifest(media: list[Mapping[str, Any]]) -> None:
    if len(media) > 1:
        raise ValueError("DIGEST_SUBSTACK_ONE_BOUND_CARD_REQUIRED")
    for asset in media:
        path = Path(str(asset.get("path") or ""))
        expected = asset.get("sha256")
        if not expected or not path.is_file() or sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("DIGEST_MEDIA_ASSET_BYTES_CHANGED")


def _perform_readback(
    client: Any,
    request: Mapping[str, Any],
    *,
    observation_path: Path | None = None,
    email_stats_poll_timeout_seconds: float = DEFAULT_EMAIL_STATS_POLL_TIMEOUT_SECONDS,
    email_stats_poll_interval_seconds: float = DEFAULT_EMAIL_STATS_POLL_INTERVAL_SECONDS,
    sleep=time_mod.sleep,
    monotonic=time_mod.monotonic,
) -> dict[str, Any]:
    from live_contentops.neo_endpoint_executor_v1 import NeoEndpointError, compare_public_images

    public_url = request.get("public_object_url")
    public_id = request.get("public_object_id")
    screen = request.get("pending_owner_screen")
    if screen:
        # Decision 54: inspect ONLY the retained code tab without navigating, reloading, or closing it.
        published = client.run(int(screen["page_id"]), "plan_substack_published")
        object_id, url = published.get("public_object_id"), published.get("public_object_url")
        if object_id != screen.get("draft_id") or not _public_url("substack", url, object_id):
            return {
                "result": {
                    "status": "READBACK_UNAVAILABLE",
                    "verified": False,
                    "reason_code": "SUBSTACK_CODE_TAB_SHARE_CENTER_REQUIRED",
                },
                "identity": {},
                "observation": {
                    "action": "READBACK",
                    "status": "READBACK_UNAVAILABLE",
                    "reason_code": "SUBSTACK_CODE_TAB_SHARE_CENTER_REQUIRED",
                    "pending_owner_screen": dict(screen),
                    "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                },
            }
        public_id = str(object_id)
        public_url = str(url)
    if not public_url:
        return {
            "result": {
                "status": "READBACK_UNAVAILABLE",
                "verified": False,
                "reason_code": "DIGEST_EXACT_PUBLIC_URL_REQUIRED",
            },
            "identity": {},
            "observation": {"action": "READBACK", "reason_code": "DIGEST_EXACT_PUBLIC_URL_REQUIRED"},
        }
    target_request = {**request, "public_object_id": public_id, "public_object_url": public_url}
    page = client.open("digest-substack-public", public_url)
    client.wait_text(page, request["native_payload"]["title"])
    raw_page = client.run(page, "plan_substack_readback")
    links_info = _run_digest_step(client, page, "digest_substack_readback_links")
    if raw_page.get("public_object_url") == public_url and public_id:
        raw_page["public_object_id"] = public_id
        raw_page["object_id_basis"] = "EXACT_CANONICAL_URL_BOUND_TO_OBSERVED_SHARE_CENTER_ID"
    observed = compare_public_images(target_request, raw_page, http=getattr(client, "image_http", None))
    media = (request.get("content_binding") or {}).get("media_manifest") or []
    actual_media = raw_page.get("media") or []
    captions = [a.get("caption", "") for a in media]
    comparison = _substack_rendered_text(raw_page.get("observed_text", ""))
    article_text = _substack_rendered_text(raw_page.get("article_text", ""))
    for caption in captions:
        comparison = _text(comparison.replace(_text(caption), " "))
        article_text = _text(article_text.replace(_text(caption), " "))
    alt_present = (len(media) == len(actual_media)
                   and all(a.get("alt_text") == b.get("alt_text") for a, b in zip(media, actual_media)))
    caption_present = (len(media) == len(actual_media)
                       and all(_text(a.get("caption")) == _text(b.get("caption")) for a, b in zip(media, actual_media)))
    expected_segments = (request.get("content_binding") or {}).get("expected_text_segments") or []
    segments_ok = all(
        digest_body_text(seg) in comparison or _substack_rendered_text(seg) in comparison
        for seg in expected_segments
    )
    body_ok = article_text == digest_body_text(request["native_payload"]["body_markdown"])
    observed["content_verified"] = bool(segments_ok and body_ok and alt_present and caption_present)
    observed["observed_links"] = links_info.get("observed_links") or []
    observed["public_alt_text_present"] = bool(alt_present) if media else True
    observed["public_caption_present"] = bool(caption_present) if media else True
    if raw_page.get("published_at_utc"):
        observed["observed_published_at_utc"] = raw_page["published_at_utc"]

    # Read Substack's own post stats page with DOM wait + bounded poll (never Gmail or any mailbox).
    email_block: dict[str, Any] = {
        "dashboard_url": None,
        "reads": [],
        "email_delivery_confirmed": False,
        "basis": "Substack post stats not yet observed; no mailbox read.",
    }
    if public_id:
        stats_url = f"https://capitalchronicle.substack.com/publish/posts/detail/{public_id}"
        reads: list[dict[str, Any]] = []
        stats: dict[str, Any] = {}
        confirmed = False
        timeout = max(0.0, float(email_stats_poll_timeout_seconds))
        interval = max(0.0, float(email_stats_poll_interval_seconds))
        elapsed = 0.0
        started_mono = monotonic()
        while True:
            stats_page = client.open("digest-substack-stats", stats_url)
            try:
                client.wait_text(stats_page, "Recipients")
            except (NeoEndpointError, ValueError):
                pass
            stats = _run_digest_step(client, stats_page, "digest_substack_email_stats")
            reads.append({"at_utc": stats.get("observed_at_utc"), "shown": stats.get("shown", "")})
            confirmed = bool(stats.get("email_delivery_confirmed"))
            if confirmed:
                break
            elapsed = max(elapsed, monotonic() - started_mono)
            remaining = timeout - elapsed
            if remaining <= 0 or interval <= 0:
                break
            step_wait = min(interval, remaining)
            sleep(step_wait)
            elapsed += step_wait
        email_block = {
            "dashboard_url": stats.get("dashboard_url") or stats_url,
            "reads": reads,
            "recipients": stats.get("recipients"),
            "opens": stats.get("opens"),
            "open_rate_percent": stats.get("open_rate_percent"),
            "email_delivery_confirmed": confirmed,
            "basis": (
                f"Substack post stats for post {public_id} show {stats.get('recipients')} recipients. No mailbox read."
                if confirmed
                else f"Substack post stats for post {public_id} have not yet confirmed recipients after {len(reads)} read(s). No mailbox read."
            ),
        }
        observed["email_delivery_confirmed"] = confirmed
        if confirmed and observation_path is not None:
            observed["email_delivery_evidence_ref"] = f"{observation_path.as_posix()}#email"
        elif confirmed:
            observed["email_delivery_evidence_ref"] = stats_url
    else:
        observed["email_delivery_confirmed"] = False

    if observation_path is not None:
        observed["observation_ref"] = observation_path.as_posix()

    observation_doc = {
        "action": "READBACK",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "tool_name": "browseros-neo/run",
        "public_page": {
            "url": raw_page.get("public_object_url") or public_url,
            "post_id": public_id,
            "published_at_utc": raw_page.get("published_at_utc"),
            "public_image_urls": raw_page.get("public_image_urls") or [],
            "links": observed["observed_links"],
            "content_verified": observed["content_verified"],
        },
        "email": email_block,
    }
    return {"result": observed, "identity": {}, "observation": observation_doc}


def perform_digest_action(
    client: Any,
    packet: Mapping[str, Any],
    *,
    observation_path: Path | None = None,
    email_stats_poll_timeout_seconds: float = DEFAULT_EMAIL_STATS_POLL_TIMEOUT_SECONDS,
    email_stats_poll_interval_seconds: float = DEFAULT_EMAIL_STATS_POLL_INTERVAL_SECONDS,
    sleep=time_mod.sleep,
    monotonic=time_mod.monotonic,
) -> dict[str, Any]:
    """Execute one claimed CC-143 Substack digest action (VERIFY_IDENTITY / PUBLISH / READBACK)."""
    from live_contentops.neo_endpoint_executor_v1 import NeoEndpointError

    state: dict[str, Any] = {"identity": {}, "dispatched_at_utc": None}
    request = packet.get("request") or {}
    action = request.get("action")
    operation_id = packet.get("operation_id", "")
    if not supports_digest_operation(operation_id) or request.get("destination") != "substack":
        raise ValueError("DIGEST_SUBSTACK_EXACT_OPERATION_REQUIRED")

    try:
        if action == "READBACK":
            return _perform_readback(
                client,
                request,
                observation_path=observation_path,
                email_stats_poll_timeout_seconds=email_stats_poll_timeout_seconds,
                email_stats_poll_interval_seconds=email_stats_poll_interval_seconds,
                sleep=sleep,
                monotonic=monotonic,
            )

        page = client.open("digest-substack", "https://capitalchronicle.substack.com/publish/posts")
        client.wait(page, 'nav[aria-label="Publisher dashboard"]')
        identity = client.run(page, "plan_substack_identity")
        state["identity"] = identity
        if action == "VERIFY_IDENTITY":
            obs = {
                "action": "VERIFY_IDENTITY",
                "identity": identity,
                "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            }
            res = {**identity, "status": "SUCCESS"}
            if observation_path is not None:
                res["observation_ref"] = observation_path.as_posix()
            return {"result": res, "identity": identity, "observation": obs}

        if action != "PUBLISH":
            raise ValueError("DIGEST_SUBSTACK_UNSUPPORTED_ACTION:" + str(action))

        policy = request.get("substack_delivery_policy") or {}
        if (policy.get("mode") != "DAILY_EMAIL_DIGEST"
                or policy.get("email_send_enabled") is not True
                or policy.get("web_publish_enabled") is not True):
            raise ValueError("DIGEST_SUBSTACK_EMAIL_DELIVERY_POLICY_REQUIRED")

        if not identity.get("authenticated") or identity.get("observed_identity") != request.get("expected_identity"):
            return {
                "result": {
                    "status": "FAILED_BEFORE_WRITE",
                    "definite_no_write": True,
                    "public_write_performed": False,
                    "stage": "BEFORE_PUBLISH_CLICK",
                    "reason_code": "NEO_SIGNED_IN_ACCOUNT_MISMATCH",
                },
                "identity": identity,
                "dispatched_at_utc": None,
                "observation": {"action": "PUBLISH", "identity": identity, "reason_code": "NEO_SIGNED_IN_ACCOUNT_MISMATCH"},
            }

        payload = request["native_payload"]
        validate_digest_public_copy(payload)
        media = (request.get("content_binding") or {}).get("media_manifest") or []
        _verify_media_manifest(media)

        step_clocks: dict[str, str | None] = {
            "draft_ready_utc": None,
            "images_uploaded_utc": None,
            "publish_clicked_utc": None,
            "email_setting_confirmed_utc": None,
            "share_center_reached_utc": None,
        }

        client.act(page, "click", ref=_ref(client, page, "button", "Create"))
        client.wait_text(page, "Article")
        client.act(page, "click", ref=_ref(client, page, "menuitem", "Article"))
        client.wait(page, ".ProseMirror")
        client.act(page, "fill", ref=_ref(client, page, "textbox", "title"), value=payload["title"])
        client.act(page, "fill", ref=_ref(client, page, "textbox", "Add a subtitle…"), value=payload.get("subtitle", ""))

        figure_html = None
        if media:
            asset = media[0]
            client.run(page, "plan_substack_intercept")
            client.act(page, "click", ref=_ref(client, page, "button", "Insert image"))
            client.wait_text(page, "Gallery")
            client.act(page, "click", ref=_ref(client, page, "menuitem", "Image"))
            client.wait(page, '[aria-label="CC466 editor upload"]')
            client.call("upload", {"page": page, "ref": _ref(client, page, "button", "CC466 editor upload"),
                                   "files": [asset["path"]]})
            client.wait(page, ".ProseMirror img")
            original_src = client.run(page, "plan_substack_uploaded")["src"]
            step_clocks["images_uploaded_utc"] = datetime.now(timezone.utc).isoformat()
            figure_html = (
                '<figure><img src="' + escape(str(original_src), quote=True)
                + '" alt="' + escape(str(asset.get("alt_text", "")), quote=True)
                + '"><figcaption>' + escape(str(asset.get("caption", ""))) + "</figcaption></figure>"
            )

        html = digest_body_html(
            payload["body_markdown"],
            figure_html=figure_html,
            placement_after=str(media[0].get("placement_after", "lead")) if media else "lead",
        )
        client.run(page, "plan_substack_clear")
        client.wait(page, ".ProseMirror:not(:has(img))")
        client.run(page, "plan_substack_paste", html=html)
        client.wait(page, ".ProseMirror p")
        if media:
            client.wait(page, ".ProseMirror img")

        check = client.run(page, "plan_substack_check",
                           expected_text=digest_body_text(payload["body_markdown"]), media=media)
        if check.get("verified") is not True:
            raise ValueError("DIGEST_SUBSTACK_EXACT_DRAFT_MISMATCH")
        step_clocks["draft_ready_utc"] = datetime.now(timezone.utc).isoformat()

        client.run(page, "plan_substack_front")
        client.wait_text(page, "Saved")
        client.act(page, "click", ref=_ref(client, page, "button", "Continue"))
        client.wait_text(page, "Send via email and the Substack app")

        controls = _run_digest_step(client, page, "digest_substack_delivery_controls")
        if not controls.get("email_found"):
            return {
                "result": {
                    "status": "FAILED_BEFORE_WRITE",
                    "definite_no_write": True,
                    "public_write_performed": False,
                    "stage": "BEFORE_PUBLISH_CLICK",
                    "reason_code": "DIGEST_EMAIL_CONTROL_MISSING",
                },
                "identity": identity,
                "dispatched_at_utc": None,
                "observation": {"action": "PUBLISH", "controls": controls, "step_clocks": step_clocks},
            }
        if not controls.get("email_send_enabled"):
            client.act(page, "click", ref=_ref(client, page, "checkbox", "Send via email and the Substack app"))
            controls = _run_digest_step(client, page, "digest_substack_delivery_controls")
        if controls.get("email_send_enabled") is not True or controls.get("schedule_enabled") is True:
            return {
                "result": {
                    "status": "FAILED_BEFORE_WRITE",
                    "definite_no_write": True,
                    "public_write_performed": False,
                    "stage": "BEFORE_PUBLISH_CLICK",
                    "reason_code": (
                        "DIGEST_SCHEDULE_TOGGLE_ENABLED"
                        if controls.get("schedule_enabled")
                        else "DIGEST_EMAIL_SEND_NOT_CONFIRMED"
                    ),
                },
                "identity": identity,
                "dispatched_at_utc": None,
                "observation": {"action": "PUBLISH", "controls": controls, "step_clocks": step_clocks},
            }
        step_clocks["email_setting_confirmed_utc"] = datetime.now(timezone.utc).isoformat()

        # Mark click boundary right before the single publish click.
        state["dispatched_at_utc"] = datetime.now(timezone.utc).isoformat()
        published = _run_digest_step(client, page, "digest_substack_publish_email")
        if published.get("status") != "CLICKED":
            if published.get("definite_no_write") is True:
                state["dispatched_at_utc"] = None
            return {
                "result": published,
                "identity": identity,
                "dispatched_at_utc": state["dispatched_at_utc"],
                "observation": {"action": "PUBLISH", "controls": controls, "published": published, "step_clocks": step_clocks},
            }
        state["dispatched_at_utc"] = published["dispatched_at_utc"]
        step_clocks["publish_clicked_utc"] = published["dispatched_at_utc"]

        follow = _wait_or_code(client, page, "Copy link")
        if "Check your email" in follow.get("text", ""):
            return _pending_code(client, page, state["dispatched_at_utc"], identity)

        public = client.run(page, "plan_substack_published")
        if (not public.get("public_object_id")
                or not _public_url("substack", public.get("public_object_url"), public.get("public_object_id"))):
            return {
                "result": {"status": "UNKNOWN_WRITE", "stage": "PUBLISH_CLICK_ATTEMPTED"},
                "identity": identity,
                "dispatched_at_utc": state["dispatched_at_utc"],
                "observation": {"action": "PUBLISH", "controls": controls, "public": public, "step_clocks": step_clocks},
            }
        step_clocks["share_center_reached_utc"] = public.get("share_center_reached_utc") or datetime.now(timezone.utc).isoformat()
        evidence_ref = (
            observation_path.as_posix()
            if observation_path is not None
            else "Neo verified email-send ON and web publish ON; same tab reached share-center."
        )
        result_doc: dict[str, Any] = {
            **public,
            "status": "SUCCESS",
            "observed_identity": "capitalchronicle.substack.com",
            "stage": "PUBLISH_CLICK_ATTEMPTED",
            "delivery_observation": {
                "email_send_enabled": True,
                "web_publish_enabled": True,
                "evidence_ref": evidence_ref,
            },
            "email_code_request_observed": False,
            "public_alt_text_present": True,
            "public_caption_present": True,
            "step_clocks": step_clocks,
        }
        if observation_path is not None:
            result_doc["observation_ref"] = observation_path.as_posix()
        return {
            "result": result_doc,
            "identity": identity,
            "dispatched_at_utc": state["dispatched_at_utc"],
            "observation": {
                "action": "PUBLISH",
                "controls": controls,
                "published": published,
                "public": public,
                "step_clocks": step_clocks,
                "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            },
        }
    except (NeoEndpointError, ValueError, KeyError, OSError) as exc:
        attempted = state["dispatched_at_utc"] is not None
        is_read = action == "READBACK"
        return {
            "result": {
                "status": "READBACK_UNAVAILABLE" if is_read else "UNKNOWN_WRITE" if attempted else "FAILED_BEFORE_WRITE",
                "definite_no_write": not attempted,
                "public_write_performed": False if not attempted else None,
                "stage": "PUBLISH_CLICK_ATTEMPTED" if attempted else "BEFORE_PUBLISH_CLICK",
                "reason_code": str(exc)[:160],
            },
            "identity": state["identity"],
            "dispatched_at_utc": state["dispatched_at_utc"],
            "observation": {
                "action": action,
                "error_type": type(exc).__name__,
                "reason_code": str(exc)[:160],
                "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            },
        }


def render_digest_task_xml(
    *,
    task_name: str = DEFAULT_TASK_NAME,
    repo_root: Path = DEFAULT_REPO_ROOT,
    pythonw: Path = DEFAULT_PYTHONW,
    user_id: str = DEFAULT_TASK_USER_ID,
    driver: str = "python-neo",
    start_boundary: str = "2026-12-01T19:15:00+07:00",
    enabled: bool = False,
) -> str:
    """Render the disabled-by-default Windows Task Scheduler XML for the 19:15 GMT+7 daily digest."""
    if driver not in {"python-neo", "codex-astra"}:
        raise ValueError("DIGEST_TASK_DRIVER_INVALID:" + str(driver))
    script_path = Path(repo_root) / "scripts" / "run_daily_digest_1900.py"
    arguments = f'-B "{script_path}" run --rollout config/native_desktop_rollout_v1.json --driver {driver}'
    enabled_str = "true" if enabled else "false"
    uri = "\\" + task_name.lstrip("\\")
    return (
        '<?xml version="1.0"?>\n'
        '<Task version="1.3" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">\n'
        '  <RegistrationInfo>\n'
        f'    <Description>{xml_escape("CC-855 / CC-143 / CC-690: Daily 19:15 GMT+7 Capital Chronicle Substack email digest and evening readback runner (zero Claude Desktop / zero agy dependency; OS-lock guarded). Disabled until Ops installs.")}</Description>\n'
        f'    <URI>{xml_escape(uri)}</URI>\n'
        '  </RegistrationInfo>\n'
        '  <Triggers>\n'
        '    <CalendarTrigger>\n'
        f'      <StartBoundary>{xml_escape(start_boundary)}</StartBoundary>\n'
        '      <Enabled>true</Enabled>\n'
        '      <ScheduleByDay>\n'
        '        <DaysInterval>1</DaysInterval>\n'
        '      </ScheduleByDay>\n'
        '    </CalendarTrigger>\n'
        '  </Triggers>\n'
        '  <Principals>\n'
        '    <Principal id="Author">\n'
        f'      <UserId>{xml_escape(user_id)}</UserId>\n'
        '      <LogonType>InteractiveToken</LogonType>\n'
        '      <RunLevel>LeastPrivilege</RunLevel>\n'
        '    </Principal>\n'
        '  </Principals>\n'
        '  <Settings>\n'
        '    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>\n'
        '    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>\n'
        '    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>\n'
        '    <AllowHardTerminate>true</AllowHardTerminate>\n'
        '    <StartWhenAvailable>true</StartWhenAvailable>\n'
        '    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>\n'
        '    <IdleSettings>\n'
        '      <Duration>PT10M</Duration>\n'
        '      <WaitTimeout>PT1H</WaitTimeout>\n'
        '      <StopOnIdleEnd>false</StopOnIdleEnd>\n'
        '      <RestartOnIdle>false</RestartOnIdle>\n'
        '    </IdleSettings>\n'
        '    <AllowStartOnDemand>true</AllowStartOnDemand>\n'
        f'    <Enabled>{enabled_str}</Enabled>\n'
        '    <Hidden>true</Hidden>\n'
        '    <RunOnlyIfIdle>false</RunOnlyIfIdle>\n'
        '    <WakeToRun>false</WakeToRun>\n'
        '    <ExecutionTimeLimit>PT40M</ExecutionTimeLimit>\n'
        '    <Priority>7</Priority>\n'
        '    <UseUnifiedSchedulingEngine>true</UseUnifiedSchedulingEngine>\n'
        '  </Settings>\n'
        '  <Actions Context="Author">\n'
        '    <Exec>\n'
        f'      <Command>{xml_escape(str(pythonw))}</Command>\n'
        f'      <Arguments>{xml_escape(arguments, {chr(34): "&quot;"})}</Arguments>\n'
        f'      <WorkingDirectory>{xml_escape(str(repo_root))}</WorkingDirectory>\n'
        '    </Exec>\n'
        '  </Actions>\n'
        '</Task>\n'
    )
