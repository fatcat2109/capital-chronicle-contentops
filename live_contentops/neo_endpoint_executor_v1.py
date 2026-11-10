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
from urllib.parse import urlsplit
import requests

from live_contentops.native_neo_executor_v1 import NativeNeoExecutor, NativeNeoInputRequired, expected_posts, _post_texts

ENDPOINT_SURFACE = "NEO_ENDPOINT_EXECUTOR"
ENDPOINT_TOOL = "browseros-neo/run"
STEPS = Path(__file__).with_name("neo_endpoint_steps_v1.js")
GROUP = "codex/cc436-automatic-posts"


class NeoEndpointError(RuntimeError):
    pass


class NeoMcpClient:
    def __init__(self, endpoint="http://127.0.0.1:9010/mcp", *, session=None):
        parsed = urlsplit(endpoint)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("NEO_LOCAL_ENDPOINT_REQUIRED")
        self.endpoint = endpoint
        self.http = session or requests.Session()
        self.http.headers.update({"Accept": "application/json, text/event-stream"})
        self.sequence = 0
        self.task_session = None
        self.initialized = False

    def rpc(self, method, params=None):
        self.sequence += 1
        payload = {"jsonrpc": "2.0", "id": self.sequence, "method": method, "params": params or {}}
        try:
            response = self.http.post(self.endpoint, json=payload, timeout=(3, 35))
            response.raise_for_status()
            response.encoding = "utf-8"
            if response.headers.get("Mcp-Session-Id"):
                self.http.headers["Mcp-Session-Id"] = response.headers["Mcp-Session-Id"]
            try:
                value = response.json()
            except ValueError:
                values = [json.loads(line[5:].strip()) for line in response.text.splitlines()
                          if line.startswith("data:") and line[5:].strip()]
                value = next(v for v in values if v.get("id") == self.sequence)
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
        if self.task_session:
            arguments["session"] = self.task_session
        result = self.rpc("tools/call", {"name": name, "arguments": arguments})
        self.task_session = result.get("_meta", {}).get("com.browseros.neo/session") or self.task_session
        if result.get("isError"):
            raise NeoEndpointError("NEO_TOOL_ERROR_" + name.upper())
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

    def run(self, page, phase, **values):
        # JSON is embedded in JS only, never interpolated into a shell command.
        prefix = "const input=" + json.dumps({"phase": phase, **values}) + ";\n"
        code = prefix + f"const page=browser.page({int(page)});\n" + STEPS.read_text(encoding="utf-8")
        result = self.value(self.call("run", {"code": code}))
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise NeoEndpointError("NEO_RUN_FAILED_" + phase.upper())
        return result["value"]

    def snapshot(self, page):
        result = self.value(self.call("run", {"code": f"return await browser.page({int(page)}).snapshot();"}))
        if not result or not result.get("ok"):
            raise NeoEndpointError("NEO_SNAPSHOT_UNAVAILABLE")
        return result["value"]

    @staticmethod
    def text(result):
        return "\n".join(c["text"] for c in result.get("content", []) if c.get("type") == "text")

    def open(self, destination, url):
        if not hasattr(self, "pages"):
            self.pages = {}
            self.call("name_session", {"name": "cc436 automatic posts", "category": "social-media"})
            listing = self.text(self.call("tabs", {"action": "list"}))
            groups = self.text(self.call("tab_groups", {"action": "list"}))
            group = re.search(r'^\[([^]]+)\] "' + re.escape(GROUP) + r'"[^\n]*pages: ([\d, ]+)', groups, re.M)
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
                match = re.search(r'^\[([^]]+)\] "' + re.escape(GROUP) + '"', groups, re.M)
                self.group = match[1] if match else None
        return page

    def wait(self, page, selector):
        self.call("wait", {"page": page, "for": "selector", "value": selector, "timeout": 12000})

    def act(self, page, kind, **values):
        return self.call("act", {"page": page, "kind": kind, "diff": "none", **values})


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
            request["destination"] == "substack_notes" and (
                host == "substack-post-media.s3.amazonaws.com" or host == "substackcdn.com" or host.endswith(".substackcdn.com")))
        if parsed.scheme != "https" or not allowed:
            continue
        try:
            response = session.get(url, timeout=(3, 12), stream=True, allow_redirects=False)
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
                    rms = max(ImageStat.Stat(diff).rms)
                    worst = max(max(ImageStat.Stat(diff.crop((x,y,min(x+32,b.width),min(y+32,b.height)))).rms)
                        for y in range(0,b.height,32) for x in range(0,b.width,32))
                    matched = digest == asset["sha256"] or (rms <= 3.5 and worst <= 7)
                comparisons.append({"source_asset_sha256": asset.get("public_delivery_sha256") or asset["sha256"],
                    "platform_sha256": digest, "public_image_url": url,
                    "public_object_url": observed.get("public_object_url"), "pixels_inspected": True,
                    "source_pixels_match": matched, "comparison_method": "RGB_BLUR075_TILE32_V1",
                    "rms": round(rms, 4), "worst_tile_rms": round(worst, 4)})
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

    def readback(self, request, page, *, posts=None):
        destination = request["destination"]
        url = request.get("public_object_url")
        if url:
            self.client.call("navigate", {"page": page, "url": url})
        else:
            root = "https://x.com/Capitalnicle/with_replies" if destination == "x" else "https://substack.com/@deancapitalchronicle"
            self.client.call("navigate", {"page": page, "url": root})
        selector = 'article[data-testid="tweet"]' if destination == "x" else 'main .FeedProseMirror'
        self.client.wait(page, selector)
        data = self.client.run(page, "readback")
        candidates = data["tweets" if destination == "x" else "notes"]
        texts = posts or expected_posts(request)
        matches = [p for p in candidates if (not url or p["public_object_url"] == url)
            and texts and _post_texts([texts[0]])[0] in _post_texts([p["observed_text"]])[0]]
        if len(matches) != 1:
            return {"status":"READBACK_UNAVAILABLE", "verified":False,
                "reason_code":"NEO_EXACT_PUBLIC_OBJECT_NOT_FOUND", "observed_identity":request["expected_identity"]}
        root = matches[0]
        # Read the exact object, not a truncated profile excerpt.
        if not url:
            self.client.call("navigate", {"page":page,"url":root["public_object_url"]})
            self.client.wait(page, selector)
            data = self.client.run(page,"readback")
            candidates = data["tweets" if destination == "x" else "notes"]
            root = next((r for r in candidates if r["public_object_url"] == root["public_object_url"]), root)
        thread = []
        for text in texts:
            found = [r for r in candidates if _post_texts([text])[0] in _post_texts([r["observed_text"]])[0]]
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
        if card:
            result["observed_link_cards"] = [{"url":link["url"],"card_visible":True,
                "public_object_url":root["public_object_url"]} for link in root.get("links",[]) if link["url"] == card]
        return compare_public_images(request, result, http=getattr(self.client,"image_http",None))

    def perform(self, packet):
        request = packet["request"]
        destination = request["destination"]
        profile = "https://x.com/Capitalnicle" if destination == "x" else "https://substack.com/@deancapitalchronicle"
        page = self.client.open(destination, profile)
        self.client.wait(page, 'a[href="/settings/profile"]' if destination == "x" else 'button')
        identity = self.client.run(page,"identity",destination=destination,expected_identity=request["expected_identity"])
        if request["action"] == "VERIFY_IDENTITY":
            return {"result": {**identity,"status":"SUCCESS"}, "identity":identity}
        if request["action"] == "READBACK":
            return {"result":self.readback(request,page),"identity":identity}
        if not identity["authenticated"]:
            return {"result":{"status":"FAILED_BEFORE_WRITE","definite_no_write":True,
                "stage":"BEFORE_PUBLISH_CLICK","reason_code":"NEO_SIGNED_IN_ACCOUNT_MISMATCH"},"identity":identity}
        parent = request.get("reply_parent")
        if destination == "x":
            self.client.call("navigate",{"page":page,"url": parent["public_object_url"] if parent else "https://x.com/compose/post"})
            self.client.wait(page,'[contenteditable="true"][role="textbox"]')
        else:
            if parent:
                self.client.call("navigate",{"page":page,"url":parent["public_object_url"]})
                self.client.wait(page,'main .FeedProseMirror')
            ref=self._ref(page,"button",{"Comment"} if parent else {"New post"})
            self.client.act(page,"click",ref=ref)
            self.client.wait(page,'[contenteditable="true"][role="textbox"]')
        posts=expected_posts(request)
        for index,text in enumerate(posts):
            if index:
                self.client.act(page,"click",ref=self._ref(page,"button",{"Add post"},last=True))
            ref=self._ref(page,"textbox",{"Post text","Post your reply","What's on your mind?","Write a reply...","Add a comment..."},last=True)
            self.client.act(page,"fill",ref=ref,value=text)
        media=(request.get("content_binding") or {}).get("media_manifest") or []
        if media:
            if destination == "substack_notes":
                self.client.run(page,"expose_note_upload")
            ref=self._ref(page,"button",{"Choose Files","Choose File","CC436 image upload"})
            self.client.call("upload",{"page":page,"ref":ref,"files":[a["path"] for a in media]})
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


class EndpointNeoExecutor(NativeNeoExecutor):
    """The existing sole publisher calls this synchronously; no model is involved."""
    inline_transport = True
    def __init__(self,*args,client=None,**kwargs):
        kwargs["native_invocation_id"] = "neo-endpoint:" + uuid4().hex
        super().__init__(*args,**kwargs)
        self.client=client or endpoint_client()

    def __call__(self,request):
        try:
            return super().__call__(request)
        except NativeNeoInputRequired:
            if request.get("destination") not in {"x","substack_notes"} or request.get("action") == "EDIT_EXISTING":
                raise
        # Connect before claiming: an unavailable endpoint has made no public attempt.
        try:
            self.client.initialize()
        except (NeoEndpointError,requests.RequestException):
            return {"status":"FAILED_BEFORE_WRITE","definite_no_write":True,
                "request_sha256":request["request_sha256"],"observed_identity":request["expected_identity"],
                "reason_code":"NEO_ENDPOINT_UNAVAILABLE","public_write_performed":False}
        request_hash=request["request_sha256"]
        try:
            packet=self.begin(request_hash)
        except ValueError:
            # Another worker owns a write claim. It can only be read back.
            if self._get(request_hash,"started"):
                return {"status":"UNKNOWN_WRITE","retry_permitted":False,
                    "reason_code":"NATIVE_NEO_CLAIMED_ACTION_WITHOUT_RETURN"}
            raise
        try:
            observed=NeoBrowserDriver(self.client).perform(packet)
            result={"request_sha256":request_hash,**observed["result"]}
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
