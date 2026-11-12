"""CC-436: execute existing durable Neo requests over Neo's local MCP endpoint.

This is a transport inside the existing publisher, not a worker or scheduler.
Claims, immutable request hashes and recovery remain NativeNeoExecutor's.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import re
from uuid import uuid4
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import requests

from live_contentops.native_neo_executor_v1 import NativeNeoExecutor, NativeNeoInputRequired, expected_posts
from live_contentops.neo_destination_handoff_v1 import ROOTS

ENDPOINT_SURFACE = "NEO_ENDPOINT_EXECUTOR"
ENDPOINT_TOOL = "browseros-neo/run"
STEPS = Path(__file__).with_name("neo_endpoint_steps_v1.js")
GROUP = "codex/cc436-automatic-posts"
ARTICLE_ROUTES = {"linkedin_company", "youtube"}


class NeoEndpointError(RuntimeError):
    pass


class NeoMcpClient:
    def __init__(self, endpoint="http://127.0.0.1:9010/mcp", *, session=None,
                 task_name="cc436 automatic posts", group_title=GROUP):
        parsed = urlsplit(endpoint)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("NEO_LOCAL_ENDPOINT_REQUIRED")
        self.endpoint = endpoint
        self.task_name=task_name
        self.group_title=group_title
        self.http = session or requests.Session()
        self.http.headers.update({"Accept": "application/json, text/event-stream"})
        self.sequence = 0
        self.task_session = None
        self.initialized = False

    def rpc(self, method, params=None):
        import time
        self.sequence += 1
        payload = {"jsonrpc": "2.0", "id": self.sequence, "method": method, "params": params or {}}
        try:
            response = self.http.post(self.endpoint, json=payload, timeout=(3, 35),stream=True)
            response.raise_for_status()
            response.encoding = "utf-8"
            if response.headers.get("Mcp-Session-Id"):
                self.http.headers["Mcp-Session-Id"] = response.headers["Mcp-Session-Id"]
            try:
                if "text/event-stream" in response.headers.get("Content-Type",""):
                    deadline=time.monotonic()+40
                    value=None
                    # SSE may remain open after the reply, and keepalive frames
                    # prevent a socket read timeout. Stop at our exact JSON-RPC
                    # reply; never wait for the connection itself to close.
                    for line in response.iter_lines(chunk_size=1,decode_unicode=True):
                        if time.monotonic()>deadline:
                            raise NeoEndpointError("NEO_RPC_DEADLINE_EXCEEDED")
                        if line.startswith("data:") and line[5:].strip():
                            candidate=json.loads(line[5:].strip())
                            if candidate.get("id")==self.sequence:
                                value=candidate
                                break
                    if value is None: raise NeoEndpointError("NEO_RPC_REPLY_MISSING")
                else:
                    value=response.json()
            finally:
                response.close()
            if value.get("error"):
                raise NeoEndpointError("NEO_RPC_ERROR")
            return value["result"]
        except (requests.RequestException, ValueError, KeyError, StopIteration) as exc:
            # Never log response bodies, browser content, connection headers or sessions.
            raise NeoEndpointError("NEO_ENDPOINT_" + type(exc).__name__.upper()) from None

    def initialize(self):
        if self.initialized:
            return
        result = self.rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
            "clientInfo": {"name": "codex", "version": "cc436-endpoint-executor"}})
        self.http.headers["MCP-Protocol-Version"] = result["protocolVersion"]
        response = self.http.post(self.endpoint,
            json={"jsonrpc": "2.0", "method": "notifications/initialized"}, timeout=(3, 5))
        response.raise_for_status()
        self.initialized = True

    def call(self, name, arguments):
        self.initialize()
        arguments = dict(arguments)
        if name=="navigate" and arguments.get("page") in getattr(self,"pages",{}).values():
            self.clear_task_draft(arguments["page"])
        if self.task_session:
            arguments["session"] = self.task_session
        result = self.rpc("tools/call", {"name": name, "arguments": arguments})
        self.task_session = result.get("_meta", {}).get("com.browseros.neo/session") or self.task_session
        if result.get("isError"):
            detail=self.text(result).lower()
            classification=next((code for marker,code in (
                ('beforeunload:','BEFOREUNLOAD'),('covered by','CONTROL_COVERED'),
                ('did not retain','FIELD_NORMALIZED_OR_REJECTED'),('stale','STALE_REFERENCE'),
                ('not found','CONTROL_NOT_FOUND'),('not a method','UNSUPPORTED_SDK_METHOD')) if marker in detail),
                'TOOL_ERROR')
            self.last_error={"tool":name,"kind":arguments.get("kind"),"classification":classification}
            # A previous pre-click failure may leave this executor's own draft
            # in its task tab. Accept only its browser beforeunload prompt so
            # the requested navigation can finish; never a file/account dialog.
            page=arguments.get("page")
            if (name=="navigate" and page in getattr(self,"pages",{}).values()
                    and "beforeunload:" in self.text(result)):
                accepted=self.rpc("tools/call",{"name":"act","arguments":{
                    "page":page,"kind":"dialog_accept","diff":"none",
                    **({"session":self.task_session} if self.task_session else {})}})
                if not accepted.get("isError"):
                    return accepted
            raise NeoEndpointError("NEO_" + classification + "_" + name.upper())
        return result

    @staticmethod
    def value(result):
        value = result.get("structuredContent")
        if value is None:
            for item in result.get("content", []):
                if item.get("type") == "text":
                    try:
                        value = json.loads(item["text"])
                        break
                    except ValueError:
                        if "\nreturn: " in item["text"]:
                            try:
                                value = json.JSONDecoder().raw_decode(item["text"].split("\nreturn: ", 1)[1])[0]
                                break
                            except ValueError:
                                pass
                        continue
        return value

    @staticmethod
    def _read_dom_output(path):
        path=Path(path).resolve()
        if "/.browseros/tool-output/" not in path.as_posix().lower() or not path.is_file() or path.stat().st_size>512_000:
            raise NeoEndpointError("NEO_DOM_OUTPUT_PATH_INVALID")
        body=path.read_text(encoding="utf-8")
        if body.startswith("[UNTRUSTED_PAGE_CONTENT "):
            body=body.split("\n",1)[1]
        return json.JSONDecoder().raw_decode(body)[0]

    def run(self, page, phase, **values):
        # JSON is embedded in JS only, never interpolated into a shell command.
        prefix = "const input=" + json.dumps({"phase": phase, **values}) + ";\n"
        code = prefix + f"const page=browser.page({int(page)});\n" + STEPS.read_text(encoding="utf-8")
        result = self.value(self.call("run", {"code": code}))
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise NeoEndpointError("NEO_RUN_FAILED_" + phase.upper())
        value = result.get("value")
        if isinstance(value,dict) and value.get("neo_output_file"):
            # Neo's documented overflow output is local public DOM, not a
            # second browser route. Bound the read and never print its bytes.
            value=self._read_dom_output(value["neo_output_file"])
        if isinstance(value,dict) and isinstance(value.get("pre_click_posts"),dict) and value["pre_click_posts"].get("neo_output_file"):
            value["pre_click_posts"]=self._read_dom_output(value["pre_click_posts"]["neo_output_file"])
        if value is None:
            raise NeoEndpointError("NEO_RUN_RESULT_MISSING_" + phase.upper())
        return value

    def snapshot(self, page):
        result = self.value(self.call("run", {"code": f"return await browser.page({int(page)}).snapshot();"}))
        if not result or not result.get("ok"):
            raise NeoEndpointError("NEO_SNAPSHOT_UNAVAILABLE")
        return result["value"]

    def clear_task_draft(self,page):
        """Discard only this executor's unpublished composer before navigation.

        X holds navigation while a beforeunload prompt is open, so waiting for
        the navigation RPC to fail cannot handle that prompt in time.
        """
        try:
            # The granular tool reports a browser dialog immediately; an SDK
            # script cannot execute in a page while its dialog is blocking it.
            self.call("snapshot",{"page":page})
            snapshot=self.snapshot(page)
        except NeoEndpointError:
            if (getattr(self,"last_error",{}).get("classification")=="BEFOREUNLOAD"):
                self.act(page,"dialog_accept")
            return
        if 'dialog "Crop media"' in snapshot.get("text",""):
            back=next((r for r in snapshot["refs"] if r["role"]=="button" and r["name"]=="Back"),None)
            if not back:
                return
            # Cancel the image editor; never save a crop of a source-bound card.
            self.act(page,"click",ref=back["ref"])
            self.wait(page,'[data-testid="tweetTextarea_0"][contenteditable="true"]')
            snapshot=self.snapshot(page)
        discard=next((r for r in snapshot["refs"] if r["role"]=="button" and r["name"]=="Discard"),None)
        if discard and 'alertdialog "Save post?"' in snapshot.get("text",""):
            self.act(page,"click",ref=discard["ref"])
            return
        composer=("/compose/post" in snapshot.get("url","")
            or 'dialog "New note"' in snapshot.get("text",""))
        if not composer:
            return
        close=next((r for r in snapshot["refs"] if r["role"]=="button" and r["name"] in {"Close","Cancel"}),None)
        if close:
            dirty=("/compose/post" in snapshot.get("url","")
                and any(text.strip() for text in self.run(page,"composer")))
            self.act(page,"focus",ref=close["ref"])
            if self.run(page,"dismiss_focused").get("focused") is not True:
                raise NeoEndpointError("NEO_CLOSE_COMPOSER_FOCUS_NOT_CONFIRMED")
            self.act(page,"press",key="Enter")
            if dirty:
                self.wait(page,'[role="alertdialog"]')
            follow=self.snapshot(page)
            discard=next((r for r in follow["refs"] if r["role"]=="button" and r["name"]=="Discard"),None)
            if discard:
                self.act(page,"click",ref=discard["ref"])

    @staticmethod
    def text(result):
        return "\n".join(c["text"] for c in result.get("content", []) if c.get("type") == "text")

    def open(self, destination, url):
        if not hasattr(self, "pages"):
            self.pages = {}
            self.call("name_session", {"name": self.task_name, "category": "social-media"})
            listing = self.text(self.call("tabs", {"action": "list"}))
            groups = self.text(self.call("tab_groups", {"action": "list"}))
            group = re.search(r'^\[([^]]+)\] "' + re.escape(self.group_title) + r'"[^\n]*pages: ([\d, ]+)', groups, re.M)
            self.group = group[1] if group else None
            # Reuse only this executor's explicitly named group, never another task's tabs.
            if group:
                owned = set(re.findall(r"\d+", group[2]))
                for line in listing.splitlines():
                    match = re.match(r"\[(\d+)\] (https://\S+)", line)
                    if match and match[1] in owned:
                        host = urlsplit(match[2]).hostname
                        if host == "x.com": self.pages.setdefault("x", int(match[1]))
                        if host == "substack.com": self.pages.setdefault("substack_notes", int(match[1]))
                        if host == "www.linkedin.com": self.pages.setdefault("linkedin_company", int(match[1]))
                        if host == "www.youtube.com": self.pages.setdefault("youtube", int(match[1]))
                        if host in {"t.co","capitalchronicle.substack.com"}:
                            self.pages.setdefault("plan-substack" if self.group_title=="codex/cc466-plan-pages" else "link-verification",int(match[1]))
        if destination in self.pages:
            page = self.pages[destination]
            self.call("navigate", {"page": page, "url": url})
        else:
            args = {"action": "new", "url": url}
            if self.group: args["groupId"] = self.group
            result = self.text(self.call("tabs", args))
            match = re.search(r"opened page (\d+)", result)
            if not match: raise NeoEndpointError("NEO_TASK_TAB_NOT_OPENED")
            page = self.pages[destination] = int(match[1])
            if not self.group:
                groups = self.text(self.call("tab_groups", {"action": "list"}))
                match = re.search(r'^\[([^]]+)\] "' + re.escape(self.group_title) + '"', groups, re.M)
                self.group = match[1] if match else None
        return page

    def wait(self, page, selector):
        self.call("wait", {"page": page, "for": "selector", "value": selector, "timeout": 12000})

    def wait_text(self, page, text):
        self.call("wait", {"page": page, "for": "text", "value": text, "timeout": 12000})

    def act(self, page, kind, **values):
        return self.call("act", {"page": page, "kind": kind, "diff": "none", **values})

    def verify_link(self, short_url, canonical):
        if not re.fullmatch(r"https://(?:t\.co/[A-Za-z0-9]+|lnkd\.in/[A-Za-z0-9_-]+)",short_url):
            return False
        cache=getattr(self,"verified_links",{})
        if short_url not in cache:
            page=self.open("link-verification",short_url)
            observed=self.snapshot(page)["url"]
            cache[short_url]=observed.split("?",1)[0].split("#",1)[0]
            self.verified_links=cache
        return cache[short_url] == canonical


def compare_public_images(request, observed, *, http=None):
    """Compare actual public bytes/pixels with the bound source, without printing bytes."""
    from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat
    session = http or requests.Session()
    media = (request.get("content_binding") or {}).get("media_manifest") or []
    observed = dict(observed)
    hashes, comparisons = [], []
    for url in observed.get("public_image_urls") or []:
        parsed = urlsplit(url)
        host = parsed.hostname or ""
        allowed = (request["destination"] == "x" and host == "pbs.twimg.com" and parsed.path.startswith("/media/")) or (
            request["destination"] in {"substack_notes", "substack"} and (
                host == "substack-post-media.s3.amazonaws.com" or host == "substackcdn.com" or host.endswith(".substackcdn.com"))) or (
            request["destination"] == "linkedin_company" and host == "media.licdn.com") or (
            request["destination"] == "youtube" and host == "yt3.ggpht.com")
        if parsed.scheme != "https" or not allowed:
            continue
        try:
            retrieved_url=url
            if request["destination"]=="x":
                # X's displayed small/900x900 variants rescale letters. Its
                # public original is the same observed asset path, at full
                # resolution; PNG often remains byte-identical to our upload.
                query=dict(parse_qsl(parsed.query));query["name"]="orig"
                retrieved_url=urlunsplit((parsed.scheme,parsed.netloc,parsed.path,urlencode(query),""))
            response = session.get(retrieved_url, timeout=(3, 12), stream=True, allow_redirects=False)
            response.raise_for_status()
            if 300 <= response.status_code < 400: continue
            chunks, size = [], 0
            for chunk in response.iter_content(65536):
                size += len(chunk)
                if size > 12_000_000: raise ValueError("PUBLIC_IMAGE_TOO_LARGE")
                chunks.append(chunk)
            data = b"".join(chunks)
            digest = sha256(data).hexdigest()
            hashes.append(digest)
            for asset in media:
                source = Path(asset["path"]).read_bytes()
                if sha256(source).hexdigest() != asset["sha256"]:
                    continue
                with Image.open(BytesIO(data)) as delivered, Image.open(BytesIO(source)) as original:
                    a = ImageOps.exif_transpose(original).convert("RGB")
                    b = ImageOps.exif_transpose(delivered).convert("RGB")
                    if abs(a.width / a.height - b.width / b.height) > .005 or min(b.size) < 200:
                        continue
                    if a.size != b.size: a = a.resize(b.size, Image.Resampling.LANCZOS)
                    diff = ImageChops.difference(a.filter(ImageFilter.GaussianBlur(.75)),
                                                b.filter(ImageFilter.GaussianBlur(.75)))
                    max_luma=ImageChops.difference(a.convert("L"),b.convert("L")).getextrema()[1]
                    rms = max(ImageStat.Stat(diff).rms)
                    worst = max(max(ImageStat.Stat(diff.crop((x,y,min(x+32,b.width),min(y+32,b.height)))).rms)
                        for y in range(0,b.height,32) for x in range(0,b.width,32))
                    matched = digest == asset["sha256"] or (rms <= 3.5 and worst <= 10 and max_luma <= 60)
                comparisons.append({"source_asset_sha256": asset.get("public_delivery_sha256") or asset["sha256"],
                    "platform_sha256": digest, "public_image_url": retrieved_url,"observed_image_url":url,
                    "public_object_url": observed.get("public_object_url"), "pixels_inspected": True,
                    "source_pixels_match": matched, "comparison_method": "RGB_BLUR075_TILE32_LUMA60_V1",
                    "rms": round(rms, 4), "worst_tile_rms": round(worst, 4),"max_luma_delta":max_luma})
        except (OSError, ValueError, requests.RequestException):
            continue
    observed.update(observed_media_sha256=hashes, media_comparisons=comparisons)
    return observed


class NeoBrowserDriver:
    def __init__(self, client):
        self.client = client

    def _ref(self, page, role, names, *, last=False):
        refs = [r for r in self.client.snapshot(page)["refs"] if r["role"] == role and r["name"] in names]
        if not refs: raise NeoEndpointError("NEO_EXPECTED_" + role.upper() + "_MISSING")
        return refs[-1 if last else 0]["ref"]

    def article_guard(self, request, page):
        """Observe objections without clicking a checkpoint or optional verification."""
        snapshot = self.client.snapshot(page)
        text, url = snapshot.get("text", ""), snapshot.get("url", "")
        patterns = (
            r"[^\n]*(?:your account (?:has been|is) (?:temporarily )?(?:restricted|suspended)|"
            r"your channel (?:has been|is) (?:removed|suspended|terminated)|"
            r"verify your identity|confirm your identity|security verification|"
            r"tài khoản của bạn (?:đã bị|bị) (?:hạn chế|tạm ngưng)|xác minh danh tính)[^\n]*",
        )
        wording = next((m.group(0).strip() for p in patterns if (m := re.search(p, text, re.I))), None)
        checkpoint = bool(re.search(r"/(?:checkpoint|challenge|verify)(?:/|\?|$)", url, re.I))
        if not wording and not checkpoint:
            return None
        cause = ("LINKEDIN" if request["destination"] == "linkedin_company" else "YOUTUBE") + "_PLATFORM_RESTRICTION"
        from .neo_destination_handoff_v1 import suspend_route
        suspend_route(request["destination"], cause)
        return {"status": "FAILED_BEFORE_WRITE", "definite_no_write": True,
            "public_write_performed": False, "stage": "BEFORE_PUBLISH_CLICK",
            "reason_code": cause, "platform_wording": wording or text[:1500], "page_url": url}

    def article_readback(self, request, page, *, posts=None):
        if request.get("public_object_url"):
            self.client.call("navigate", {"page": page, "url": request["public_object_url"]})
        refused = self.article_guard(request, page)
        if refused:
            return {**refused, "status": "READBACK_UNAVAILABLE", "verified": False}
        data = self.client.run(page, "article_readback", destination=request["destination"])
        candidates = data["posts"]
        for post in candidates:
            resolutions = []
            for link in post.get("links") or []:
                if (request.get("canonical_url") and request["destination"] == "linkedin_company"
                        and re.fullmatch(r"https://lnkd\.in/[A-Za-z0-9_-]+", str(link.get("url") or ""))
                        and self.client.verify_link(link["url"], request["canonical_url"])):
                    link["expanded_url"] = request["canonical_url"]
                    resolutions.append({"displayed_url": link["url"], "target_url": request["canonical_url"],
                        "target_verified": True, "public_object_url": post["public_object_url"]})
            post["observed_link_resolutions"] = resolutions
        texts = posts or expected_posts(request)
        from .neo_destination_handoff_v1 import _text
        def matches(post):
            if post.get("observed_identity") != request["expected_identity"]:
                return False
            observed = _text(post["observed_text"])
            for link in post.get("links") or []:
                if link.get("expanded_url") == request.get("canonical_url"):
                    observed = observed.replace(_text(link["url"]), _text(link["expanded_url"]))
            return all(_text(text) in observed for text in texts)
        matches_found = [p for p in candidates if matches(p) and (
            not request.get("public_object_url") or p["public_object_url"] == request["public_object_url"])]
        if len(matches_found) != 1:
            return {"status": "READBACK_UNAVAILABLE", "verified": False,
                "reason_code": "NEO_EXACT_PUBLIC_OBJECT_NOT_FOUND", "observed_identity": request["expected_identity"]}
        post = matches_found[0]
        if not request.get("public_object_url"):
            return self.article_readback({**request, "public_object_url": post["public_object_url"]}, page, posts=texts)
        return compare_public_images(request, {**post, "status": "SUCCESS", "content_verified": True,
            "request_sha256": request["request_sha256"]}, http=getattr(self.client, "image_http", None))

    def article_perform(self, packet):
        request = packet["request"]
        destination = request["destination"]
        identity = {"authenticated": False, "observed_identity": None,
            "observed_at_utc": datetime.now(timezone.utc).isoformat()}
        page = self.client.open(destination, ROOTS[destination])
        refused = self.article_guard(request, page)
        if refused:
            return {"result": refused, "identity": identity}
        if request["action"] == "READBACK":
            return {"result": self.article_readback(request, page), "identity": identity}
        identity = self.client.run(page, "article_identity", destination=destination,
            expected_identity=request["expected_identity"])
        if request["action"] == "VERIFY_IDENTITY":
            return {"result": {**identity, "status": "SUCCESS"}, "identity": identity}
        if not identity.get("authenticated"):
            return {"result": {"status": "FAILED_BEFORE_WRITE", "definite_no_write": True,
                "stage": "BEFORE_PUBLISH_CLICK", "reason_code": "NEO_SIGNED_IN_ACCOUNT_MISMATCH"}, "identity": identity}
        try:
            posts = expected_posts(request)
            if len(posts) != 1:
                raise NeoEndpointError("ARTICLE_SINGLE_POST_REQUIRED")
            if destination == "linkedin_company":
                self.client.act(page, "click", ref=self._ref(page, "button", {"Start a post"}))
                self.client.wait(page, '[role="dialog"] [contenteditable="true"]')
                ref = self._ref(page, "textbox", {"Text editor for creating content"}, last=True)
            else:
                ref = self._ref(page, "button", {"Bật mí về video tiếp theo của bạn", "Share an upcoming video", "What's on your mind?"})
                self.client.act(page, "click", ref=ref)
                ready = self.client.run(page, "article_editor")
                if not ready.get("ready"):
                    raise NeoEndpointError("ARTICLE_EDITOR_UNAVAILABLE")
                ref = self._ref(page, "textbox", {"CC454 article text"})
            self.client.act(page, "fill", ref=ref, value=posts[0])
            media = (request.get("content_binding") or {}).get("media_manifest") or []
            if media:
                ready = self.client.run(page, "article_intercept_upload", destination=destination)
                if not ready.get("installed"):
                    raise NeoEndpointError("ARTICLE_FILE_CHOOSER_INTERCEPTION_UNAVAILABLE")
                try:
                    names = {"Add media"} if destination == "linkedin_company" else {"Thêm hình ảnh", "Image", "Add image"}
                    self.client.act(page, "click", ref=self._ref(page, "button", names))
                    ref = self._ref(page, "button", {"CC454 article image"})
                    self.client.call("upload", {"page": page, "ref": ref, "files": [a["path"] for a in media]})
                    if destination == "linkedin_company":
                        self.client.act(page, "click", ref=self._ref(page, "button", {"Next"}))
                        self.client.wait(page, '[role="dialog"] [contenteditable="true"]')
                finally:
                    self.client.run(page, "article_upload_restore")
            refused = self.article_guard(request, page)
            if refused:
                return {"result": refused, "identity": identity}
        except NeoEndpointError as exc:
            return {"result": {"status": "FAILED_BEFORE_WRITE", "definite_no_write": True,
                "stage": "BEFORE_PUBLISH_CLICK", "reason_code": "NEO_COMPOSER_PREPARATION_FAILED",
                "safe_error_classification": str(exc)}, "identity": identity}
        result = self.client.run(page, "article_publish", destination=destination, posts=posts)
        if result["status"] != "CLICKED":
            return {"result": result, "identity": identity}
        readback = self.article_readback(request, page, posts=posts)
        return {"result": {**readback, "status": "SUCCESS" if readback.get("public_object_id") else "UNKNOWN_WRITE",
                "stage": "PUBLISH_CLICK_ATTEMPTED"}, "identity": identity, "readback": readback,
            "pre_click_posts": result["pre_click_posts"], "dispatched_at_utc": result["dispatched_at_utc"]}

    @staticmethod
    def _links(request, post):
        canonical = request.get("canonical_url")
        return [{"displayed_text":link["text"],"short_url":link["url"],"target_url":canonical,
            "target_verified":True,"public_object_url":post["public_object_url"]}
            for link in post.get("links") or []
            if canonical and canonical in {link.get("url"),link.get("expanded_url")}]

    @classmethod
    def _matches(cls, request, text, post):
        from live_contentops.neo_destination_handoff_v1 import _text, _x_reader_text, _note_rendered_text
        observed = post["observed_text"]
        if request["destination"] == "x":
            observed = _x_reader_text(observed,cls._links(request,post),post["public_object_url"],request.get("canonical_url") or "")
            return _text(text) in observed
        card = (request.get("content_binding") or {}).get("expected_link_card_url")
        if card and any(link.get("url")==card and link.get("card_visible") is True for link in post.get("links") or []):
            return _note_rendered_text(text,card,post.get("links") or [],post["public_object_url"]) in _note_rendered_text(
                observed,card,post.get("links") or [],post["public_object_url"])
        return _text(text) in _text(observed)

    def readback(self, request, page, *, posts=None):
        destination = request["destination"]
        url = request.get("public_object_url")
        if url:
            self.client.call("navigate", {"page": page, "url": url})
        else:
            root = ROOTS["x"] + "/with_replies" if destination == "x" else request["entry_url"]
            self.client.call("navigate", {"page": page, "url": root})
        selector = 'article[data-testid="tweet"]' if destination == "x" else 'main .FeedProseMirror'
        self.client.wait(page, selector)
        data = self.client.run(page, "readback", expected_identity=request["expected_identity"])
        candidates = data["tweets" if destination == "x" else "notes"]
        self._resolve_links(request,candidates)
        texts = posts or expected_posts(request)
        from live_contentops.neo_destination_handoff_v1 import _text
        matches = [p for p in candidates if (not url or p["public_object_url"] == url)
            and texts and (self._matches(request,texts[0],p) or (
                not url and _text(texts[0])[:100] in _text(p["observed_text"]))) ]
        if len(matches) != 1:
            return {"status":"READBACK_UNAVAILABLE", "verified":False,
                "reason_code":"NEO_EXACT_PUBLIC_OBJECT_NOT_FOUND", "observed_identity":request["expected_identity"]}
        root = matches[0]
        # Read the exact object, not a truncated profile excerpt.
        if not url:
            self.client.call("navigate", {"page":page,"url":root["public_object_url"]})
            self.client.wait(page, selector)
            data = self.client.run(page,"readback", expected_identity=request["expected_identity"])
            candidates = data["tweets" if destination == "x" else "notes"]
            self._resolve_links(request,candidates)
            if destination == "substack_notes":
                # Replies can link through /profile/<id>-<slug>/note/<id>.
                # Following that public link must reveal the same object under
                # the bound @handle before the alias can establish authorship.
                canonical_prefix="https://substack.com/"+request["expected_identity"]+"/note/"
                root = next((r for r in candidates if r.get("public_object_id") == root.get("public_object_id")
                    and r["public_object_url"].startswith(canonical_prefix)),None)
                if root is None:
                    return {"status":"READBACK_UNAVAILABLE","verified":False,
                        "reason_code":"NEO_NOTE_AUTHOR_NOT_VERIFIED"}
            else:
                root = next((r for r in candidates if r["public_object_url"] == root["public_object_url"]), root)
        if len(texts)>1:
            # X delivers replies after the root. Wait for the expected final
            # post, rather than accepting the root-only loading snapshot.
            self.client.wait_text(page,texts[-1].splitlines()[0][:100])
            data=self.client.run(page,"readback",expected_identity=request["expected_identity"])
            candidates=data["tweets" if destination=="x" else "notes"]
            self._resolve_links(request,candidates)
            root=next((r for r in candidates if r["public_object_url"]==root["public_object_url"]),root)
        thread = []
        for text in texts:
            found = [r for r in candidates if self._matches(request,text,r)]
            if len(found) != 1:
                return {"status":"READBACK_UNAVAILABLE","verified":False,"reason_code":"NEO_THREAD_READBACK_INCOMPLETE"}
            thread.append(found[0])
        result = {**root,"status":"SUCCESS","request_sha256":request["request_sha256"],
            "observed_identity":request["expected_identity"],"observed_text":"\n\n".join(r["observed_text"] for r in thread),
            "content_verified":True,"observed_thread":thread}
        # A reply's parent must actually occur on the exact rendered thread.
        parent = request.get("reply_parent")
        if parent and any(r["public_object_url"] == parent["public_object_url"] for r in candidates):
            result.update(observed_reply_parent_id=parent["public_object_id"],
                          observed_reply_parent_url=parent["public_object_url"])
        card = (request.get("content_binding") or {}).get("expected_link_card_url")
        result["observed_links"] = root.get("links") or []
        result["observed_link_resolutions"] = [link for post in thread for link in self._links(request,post)]
        if card:
            result["observed_link_cards"] = [{"url":link["url"],"card_visible":True,
                "public_object_url":root["public_object_url"]} for link in root.get("links",[])
                if link["url"] == card and link.get("card_visible") is True]
        return compare_public_images(request, result, http=getattr(self.client,"image_http",None))

    def _resolve_links(self, request, candidates):
        canonical=request.get("canonical_url")
        if request["destination"] != "x" or not canonical:
            return
        for post in candidates:
            for link in post.get("links") or []:
                if (canonical not in {link.get("url"),link.get("expanded_url")}
                        and re.fullmatch(r"https://t\.co/[A-Za-z0-9]+",str(link.get("url") or ""))
                        and self.client.verify_link(link["url"],canonical)):
                    link["expanded_url"]=canonical

    def prepare(self, request, page):
        """Prepare exact approved copy/media; this method never publishes."""
        destination = request["destination"]
        parent = request.get("reply_parent")
        if destination == "x":
            self.client.call("navigate",{"page":page,"url": parent["public_object_url"] if parent else "https://x.com/compose/post"})
            editor='[data-testid="tweetTextarea_0"][contenteditable="true"][role="textbox"]'
            self.client.wait(page,editor if parent else '[role="dialog"] '+editor)
        else:
            if parent:
                self.client.call("navigate",{"page":page,"url":parent["public_object_url"]})
                self.client.wait(page,'main .FeedProseMirror')
            ref=self._ref(page,"button",{"Comment"} if parent else {"New post"})
            self.client.act(page,"click",ref=ref)
            self.client.wait(page,'[contenteditable="true"][role="textbox"]')
        posts=expected_posts(request)
        media=(request.get("content_binding") or {}).get("media_manifest") or []
        for index,text in enumerate(posts):
            if index:
                # An uploaded preview can move under this button's click point
                # and open Crop media. Activate the exact observed button by
                # keyboard, after verifying focus, so the source image stays intact.
                self.client.act(page,"focus",ref=self._ref(page,"button",{"Add post"},last=True))
                if self.client.run(page,"add_post_focused").get("focused") is not True:
                    raise NeoEndpointError("NEO_ADD_POST_FOCUS_NOT_CONFIRMED")
                self.client.act(page,"press",key="Enter")
                self.client.wait(page,f'[role="dialog"] [data-testid="tweetTextarea_{index}"][contenteditable="true"][role="textbox"]')
            def editor_refs():
                return [r for r in self.client.snapshot(page)["refs"] if r["role"] == "textbox"
                    and (r["name"].startswith(("Post text", "CC436 post text")) or r["name"] in {
                        "Post your reply","What's on your mind?","Write a reply...","Leave a reply...","Add a comment..."})]
            refs = editor_refs()
            if not refs:
                # X can expose its editable DOM before its AX name appears.
                # Name only the visible editor in this task's composer, then
                # let Neo observe its ref. No text or submit state is changed.
                self.client.run(page,"expose_composer",destination=destination)
                refs=editor_refs()
            if not refs: raise NeoEndpointError("NEO_EXPECTED_COMPOSER_MISSING")
            ref=refs[-1]["ref"]
            try:
                self.client.act(page,"fill",ref=ref,value=text)
            except NeoEndpointError:
                # ProseMirror retains extra paragraph separators, causing
                # Neo's literal fill verification to fail after inserting the
                # whole value. Observe the actual editor; never type it twice.
                actual = self.client.run(page,"composer")
                from live_contentops.native_neo_executor_v1 import _post_texts
                if len(actual) <= index or _post_texts([actual[index]]) != _post_texts([text]):
                    # A new X thread editor may replace its first AX node as
                    # focus arrives. Refill only this task's exact editor using
                    # a newly observed ref. This is pre-click and reversible.
                    refs=editor_refs()
                    if len(refs)<=index:
                        raise
                    if getattr(self.client,"last_error",{}).get("classification")=="CONTROL_COVERED":
                        # X's sticky thread toolbar can cover a composer's
                        # click point. Focus the exact observed editor, then
                        # type through Neo's supported keyboard action.
                        self.client.act(page,"focus",ref=refs[index]["ref"])
                        self.client.act(page,"press",key="Control+a")
                        self.client.act(page,"type",text=text)
                    else:
                        self.client.act(page,"fill",ref=refs[index]["ref"],value=text)
            # The lead card belongs to the first post, including a thread.
            if media and index == 0:
                if destination == "substack_notes":
                    self.client.run(page,"expose_note_upload")
                ref=self._ref(page,"button",{"Choose Files","Choose File","CC436 image upload"})
                self.client.call("upload",{"page":page,"ref":ref,"files":[a["path"] for a in media]})
        return posts

    def perform(self, packet):
        request = packet["request"]
        destination = request["destination"]
        if destination == "substack" and packet.get("operation_id", "").startswith("plan-analysis-"):
            from .plan_substack_neo_v1 import perform
            return perform(self.client, packet)
        if destination in ARTICLE_ROUTES:
            return self.article_perform(packet)
        profile = request["entry_url"] if request["action"] == "READBACK" else ROOTS[destination]
        identity={"authenticated":False,"observed_identity":None,
            "observed_at_utc":datetime.now(timezone.utc).isoformat()}
        try:
            page = self.client.open(destination, profile)
            if request["action"] == "READBACK":
                return {"result":self.readback(request,page),"identity":identity}
            self.client.wait_text(page,"Edit profile")
            identity = self.client.run(page,"identity",destination=destination,expected_identity=request["expected_identity"])
        except NeoEndpointError as exc:
            return {"result":{"status":"READBACK_UNAVAILABLE" if request["action"]=="READBACK" else "FAILED_BEFORE_WRITE",
                "definite_no_write":request["action"]!="READBACK","stage":"BEFORE_PUBLISH_CLICK",
                "reason_code":"NEO_REGISTERED_PROFILE_UNAVAILABLE","safe_error_classification":str(exc)},"identity":identity}
        if request["action"] == "VERIFY_IDENTITY":
            return {"result": {**identity,"status":"SUCCESS"}, "identity":identity}
        if not identity["authenticated"]:
            return {"result":{"status":"FAILED_BEFORE_WRITE","definite_no_write":True,
                "stage":"BEFORE_PUBLISH_CLICK","reason_code":"NEO_SIGNED_IN_ACCOUNT_MISMATCH"},"identity":identity}
        try:
            posts=self.prepare(request,page)
        except NeoEndpointError as exc:
            return {"result":{"status":"FAILED_BEFORE_WRITE","definite_no_write":True,
                "stage":"BEFORE_PUBLISH_CLICK","reason_code":"NEO_COMPOSER_PREPARATION_FAILED",
                "safe_error_classification":str(exc)},"identity":identity}
        parent=request.get("reply_parent")
        result=self.client.run(page,"publish",destination=destination,posts=posts,reply_parent=parent)
        if result["status"] != "CLICKED":
            return {"result":result,"identity":identity}
        readback=self.readback(request,page,posts=posts)
        return {"result":{**readback,"status":"SUCCESS" if readback.get("public_object_id") else "UNKNOWN_WRITE",
            "stage":"PUBLISH_CLICK_ATTEMPTED"},"identity":identity,"readback":readback,
            "pre_click_posts":result["pre_click_posts"],"dispatched_at_utc":result["dispatched_at_utc"]}


@lru_cache(maxsize=1)
def endpoint_client():
    return NeoMcpClient()


def repaired_prewrite_request(store, dispatch, *, executor_revision=None):
    """Identify an exact unsent composer refusal made by older transport code.

    A missing/uncertain return, an attempted click, a known object or the same
    code revision cannot release the existing exactly-once dispatch fence.
    """
    if (dispatch.get("status") != "DEFINITE_NO_WRITE" or dispatch.get("public_object_id")
            or dispatch.get("public_object_url") or dispatch.get("platform") not in {"x","substack_notes"}):
        return None
    message=store.get_outbox_message(dispatch["message_id"])
    if not message:
        return None
    from .capital_chronicle_latest_report_consumer_v1 import sha256_of
    revision=executor_revision or sha256(Path(__file__).read_bytes()+STEPS.read_bytes()).hexdigest()
    found=None
    for row in store.list_outbox_messages(work_item_id=message["work_item_id"],destination="internal:native-neo-tool"):
        packet=json.loads(row["payload"])
        request=packet.get("request") or {}
        if (request.get("action") != "PUBLISH" or request.get("destination") != dispatch["platform"]
                or request.get("dispatch_attempt_identity") != dispatch["dispatch_id"]):
            continue
        key="native-neo-"+sha256_of([packet["operation_id"],request["request_sha256"],"response"])
        response=store.get_outbox_message(key)
        result=json.loads(response["payload"]).get("result",{}) if response else {}
        if (result.get("status") != "FAILED_BEFORE_WRITE" or result.get("definite_no_write") is not True
                or result.get("public_write_performed") is not False or result.get("stage") != "BEFORE_PUBLISH_CLICK"
                or result.get("reason_code") not in {"NEO_COMPOSER_PREPARATION_FAILED","NEO_COMPOSER_PAYLOAD_MISMATCH",
                    "NEO_REGISTERED_PROFILE_UNAVAILABLE"}
                or not result.get("native_tool_return_sha256")
                or (result.get("native_tool_observation") or {}).get("dispatched_at_utc")
                or result.get("neo_executor_revision") == revision):
            return None
        found={"request_sha256":request["request_sha256"],"reason_code":result["reason_code"]}
    return found


class EndpointNeoExecutor(NativeNeoExecutor):
    """The existing sole publisher calls this synchronously; no model is involved."""
    inline_transport = True
    def __init__(self,*args,client=None,automatic_destinations=None,**kwargs):
        # Article-only composition still returns Substack/X actions to its
        # native parent. Keep that parent's id across their begin/submit calls.
        # Standalone fully automatic callers retain the endpoint's own id.
        if automatic_destinations is None:
            kwargs["native_invocation_id"] = "neo-endpoint:" + uuid4().hex
        super().__init__(*args,**kwargs)
        self.client=client or (NeoMcpClient(task_name="cc466 plan pages",group_title="codex/cc466-plan-pages")
            if self.operation_id.startswith("plan-analysis-") else endpoint_client())
        self.automatic_destinations = (set(automatic_destinations) if automatic_destinations is not None
            else {"x", "substack_notes", *ARTICLE_ROUTES})
        self.executor_revision=sha256(Path(__file__).read_bytes()+STEPS.read_bytes()
            +Path(__file__).with_name("plan_substack_neo_v1.py").read_bytes()).hexdigest()

    def repaired_prewrite_request(self, dispatch):
        return repaired_prewrite_request(self.store,dispatch,executor_revision=self.executor_revision)

    def fresh_publish_request(self, request):
        """A repaired transport can supersede its proven pre-click refusal once.

        Keep every old request/return. An unchanged transport or any attempted
        click keeps its original outcome and cannot obtain a fresh write claim.
        """
        from .capital_chronicle_latest_report_consumer_v1 import sha256_of
        refreshed = dict(request)
        while True:
            previous = self._get(sha256_of(refreshed), "response") or {}
            result = previous.get("result") or {}
            if (result.get("status") != "FAILED_BEFORE_WRITE" or result.get("definite_no_write") is not True
                    or result.get("public_write_performed") is not False
                    or result.get("stage") != "BEFORE_PUBLISH_CLICK"
                    or (result.get("native_tool_observation") or {}).get("dispatched_at_utc")
                    or not result.get("native_tool_return_sha256")
                    or result.get("neo_executor_revision") == self.executor_revision):
                break
            refreshed["supersedes_prewrite_no_write_sha256"] = sha256_of(previous)
        return refreshed if refreshed != request else None

    def __call__(self,request):
        try:
            return super().__call__(request)
        except NativeNeoInputRequired as waiting:
            plan_page = request.get("destination") == "substack" and self.operation_id.startswith("plan-analysis-")
            if (request.get("destination") not in self.automatic_destinations and not plan_page) or request.get("action") == "EDIT_EXISTING":
                raise
            pending=waiting
        # Connect before claiming: an unavailable endpoint has made no public attempt.
        try:
            self.client.initialize()
        except (NeoEndpointError,requests.RequestException):
            # No action claim exists. Preserve the same pending request for the
            # next existing minute tick instead of settling a transient outage.
            pending.request["endpoint_cause"]="NEO_ENDPOINT_UNAVAILABLE"
            raise pending
        request_hash=request["request_sha256"]
        try:
            packet=self.begin(request_hash)
        except ValueError as exc:
            # Another worker owns a write claim. It can only be read back.
            if self._get(request_hash,"started"):
                return {"status":"UNKNOWN_WRITE","retry_permitted":False,
                    "reason_code":"NATIVE_NEO_CLAIMED_ACTION_WITHOUT_RETURN"}
            # begin() has not returned and no native action claim exists. No
            # browser action has run; preserve the actual local validation cause.
            cause=str(exc)
            if not re.fullmatch(r"[A-Z][A-Z0-9_]{2,150}",cause):
                cause="LOCAL_VALIDATION_ERROR"
            return {"status":"FAILED_BEFORE_WRITE","definite_no_write":True,
                "public_write_performed":False,"stage":"BEFORE_PUBLISH_CLICK",
                "reason_code":cause,"request_sha256":request_hash,
                "observed_identity":request["expected_identity"],"identity_observed":False}
        try:
            observed=NeoBrowserDriver(self.client).perform(packet)
            result={"request_sha256":request_hash,**observed["result"],"neo_executor_revision":self.executor_revision}
            observation={"tool_name":ENDPOINT_TOOL,"surface":ENDPOINT_SURFACE,
                "native_invocation_id":self.native_invocation_id,
                "observation_source":"BROWSEROS_NEO_LOCAL_MCP_ENDPOINT",
                "observed_at_utc":datetime.now(timezone.utc).isoformat()}
            if observed.get("dispatched_at_utc"):
                observation["dispatched_at_utc"]=observed["dispatched_at_utc"]
            response={"tool_request_sha256":packet["tool_request_sha256"],"tool_observation":observation,
                "result":result,"composed":{"identity":observed["identity"],
                    "pre_click_posts":observed.get("pre_click_posts"),"readback":observed.get("readback")}}
            self.submit(request_hash,response)
            return super().__call__(request)
        except (NeoEndpointError,OSError,ValueError,KeyError,requests.RequestException):
            # No repeat after a claimed action, including a lost click/return.
            return {"status":"UNKNOWN_WRITE" if request["action"] == "PUBLISH" else "READBACK_UNAVAILABLE",
                "retry_permitted":False,"reason_code":"NEO_ENDPOINT_OBSERVATION_INCOMPLETE",
                "request_sha256":request_hash}


def resume_stored_requests(store, *, limit=2, budget_seconds=20, client=None, output_root=None):
    """The same minute run drains already-issued status/link steps after fresh work.

    An API-complete legacy parent may be PUBLISHED while its Neo step is still
    pending. Consume its exact saved bytes; never rebuild that package to make
    it eligible. Repeated old readback epochs collapse to one destination here.
    """
    import time
    from live_contentops import plan_status_posts_v1 as posts
    from live_contentops.capital_chronicle_latest_report_consumer_v1 import sha256_of
    from live_contentops.native_neo_executor_v1 import DESTINATION, SCHEMA, bind_native_neo_coordinator
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator
    chosen={}
    for row in store.list_outbox_messages(destination=DESTINATION):
        packet=json.loads(row["payload"])
        request=packet.get("request") or {}
        if (row["status"]=="NATIVE_NEO_SUPERSEDED" or packet.get("schema_version")!=SCHEMA
                or request.get("destination") not in {"x","substack_notes"}
                or request.get("action") not in {"PUBLISH","READBACK"}):
            continue
        operation=packet["operation_id"]
        source=store.get_outbox_message(operation)
        if not source or source["destination"] not in {posts.DESTINATION,"internal:plan-analysis-page"}:
            continue
        source_payload=json.loads(source["payload"])
        source_payload.setdefault("key", operation)
        if source["destination"] == posts.DESTINATION:
            from .plan_call_cards_v1 import SETTLED_POST, settled_destinations, settle_pending
            if source["status"] in {SETTLED_POST, posts.STALE, posts.SUPERSEDED}:
                continue
            # Legacy API-complete rows used PUBLISHED before their browser
            # copies reconciled. Their old readbacks obey the same late limit.
            if source_payload.get("at_utc") and posts._age_minutes(source_payload,
                    datetime.now(timezone.utc)) > posts.LATE_STATE_HOURS * 60:
                closed = settle_pending(store, source, source_payload, now=datetime.now(timezone.utc))
                if closed:
                    continue
            if request["destination"] in settled_destinations(store, source_payload):
                continue
        if source["destination"]=="internal:plan-analysis-page" and source_payload.get("link_id")!=operation:
            continue
        if source["destination"] == "internal:plan-analysis-page":
            from .plan_analysis_pages_v1 import settle_late_link
            if settle_late_link(store, source_payload):
                continue
        response_key="native-neo-"+sha256_of([operation,request["request_sha256"],"response"])
        if store.get_outbox_message(response_key):
            continue
        key=(operation,request["destination"])
        prior=chosen.get(key)
        if not prior or request["action"]=="READBACK" or prior[0]["request"]["action"]!="READBACK":
            chosen[key]=(packet,source_payload)
    started=time.monotonic()
    outcomes=[]
    processed=0
    for (operation,destination),(packet,source) in sorted(chosen.items(), key=lambda item:
            item[1][1].get("at_utc") or item[1][0].get("created_at") or "", reverse=True):
        if processed>=limit or time.monotonic()-started>=budget_seconds:
            break
        request=packet["request"]
        request_hash=request["request_sha256"]
        coordinator,executor=bind_native_neo_coordinator(store,operation_id=operation,
            output_dir=Path(output_root or (source.get("plan") or {}).get("output_dir") or posts.POST_ROOT)/operation/"native-neo",
            native_invocation_id="minute-stored-requests",
            allow_publish=True,automatic=True,endpoint_client=client)
        messages=store.list_outbox_messages(work_item_id=request["work_item_id"],destination=destination)
        message=next((m for m in messages if json.loads(m["payload"]).get("plan_hash")),None)
        if not message:
            continue
        intent=json.loads(coordinator._effective_message(message)["payload"])
        ids=DurablePublicationCoordinator._ids(request["work_item_id"],intent["plan_hash"],destination)
        dispatch=store.get_platform_dispatch(ids["dispatch_id"])
        if not dispatch:
            continue
        if dispatch["status"] == "DISPATCH_CONFIRMED":
            reconciliation = next((r for r in store.get_reconciliations_for_work_item(request["work_item_id"])
                if r["reconciliation_id"] == ids["reconciliation_id"]), {})
            if reconciliation.get("status") == "RECONCILED_CONFIRMED":
                # The exact object already consumed this intent. Retained old
                # account requests cannot take slots from new minute work.
                continue
        if (dispatch["status"]=="DEFINITE_NO_WRITE" and not dispatch.get("public_object_id")
                and not dispatch.get("public_object_url")):
            # A settled no-write has nothing to read back. Repeated old read
            # requests must not spend the bounded drain slots every minute.
            continue
        coordinator.recovery_scope={"work_item_id":request["work_item_id"],"exact_work_item_only":True}
        coordinator.allow_prior_confirmed_distribution=True
        try:
            # Keep begin_x's existing current-state/freshness rule at the
            # actual write boundary; readback is available after expiry.
            unclaimed_write=request["action"]=="PUBLISH" and executor._get(request_hash,"started") is None
            if unclaimed_write and source.get("at_utc"):
                now=datetime.now(timezone.utc)
                if posts._age_minutes(source,now)>posts._x_freshness_limit(source,now):
                    outcomes.append({"operation_id":operation,"destination":destination,
                        "request_sha256":request_hash,"status":"PLAN_STATUS_X_STALE_NOT_POSTED"})
                    continue
            if unclaimed_write:
                from live_contentops.event_article_guard_v1 import public_execution_copy_forbidden
                if any(public_execution_copy_forbidden(text) for text in expected_posts(request)):
                    outcomes.append({"operation_id":operation,"destination":destination,
                        "request_sha256":request_hash,"status":"PRIVATE_OR_EXECUTION_COPY_FORBIDDEN"})
                    continue
            processed+=1
            result=executor(request)
            if request["action"]=="PUBLISH" and result.get("status")=="SUCCESS":
                outcome=coordinator.reconcile_completed_native_publish(ids["dispatch_id"],request_hash=request_hash)
            else:
                outcome=coordinator.readback_existing_dispatch(ids["dispatch_id"])
            outcomes.append({"operation_id":operation,"destination":destination,"request_sha256":request_hash,
                "status":outcome.get("reconciliation_status") or outcome.get("status"),
                "cause":result.get("reason_code")})
        except NativeNeoInputRequired:
            outcomes.append({"operation_id":operation,"destination":destination,"request_sha256":request_hash,
                "status":"NATIVE_NEO_TOOL_PENDING","cause":"NEO_ENDPOINT_UNAVAILABLE"})
        except (ValueError,OSError,NeoEndpointError) as exc:
            outcomes.append({"operation_id":operation,"destination":destination,"request_sha256":request_hash,
                "status":"NOT_COMPLETED","cause":str(exc)[:160]})
    return {"status":"OK","requests":outcomes}
