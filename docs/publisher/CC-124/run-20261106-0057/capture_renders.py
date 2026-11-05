"""Save Neo's real preview screenshots as binary files, never session text."""
import base64
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import sys

from PIL import Image
sys.path.insert(0, r"A:\Capital Chronicle\ContentOps")
from live_contentops.browser_rendered_source_recovery_v1 import BrowserOSNeoMcpTransport

RUN = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc124-bitcoin-rates-20261106-h")
ROOT = RUN / "render-review"
OUT = ROOT / "captures"
OUT.mkdir(exist_ok=True)
targets = json.loads((ROOT / "targets.json").read_bytes())
client = BrowserOSNeoMcpTransport(timeout_seconds=40)

def call(name, arguments):
    identity = client._next_id
    client._next_id += 1
    response, _ = client._request({"jsonrpc": "2.0", "id": identity, "method": "tools/call",
        "params": {"name": name, "arguments": arguments}})
    result = response["result"]
    if result.get("isError"):
        error = " ".join(c.get("text", "") for c in result.get("content", []) if c.get("type") == "text")
        raise RuntimeError(error[:1000])
    return result

def run(code):
    result = call("run", {"code": code, "timeout": 30000})
    structured = result["structuredContent"]
    if not structured.get("ok"):
        raise RuntimeError(str(structured.get("error"))[:1000])
    return structured["value"]

renders = []
try:
    client.initialize()
    call("browser_target", {"action": "set_window", "windowId": 1698400956})
    # First inventory, then one tab in this task's existing group and window.
    call("tabs", {"action": "list"})
    new = call("tabs", {"action": "new", "groupId": "B4B5A1D184A4CA126657D42B40A5CB38",
        "url": (ROOT / "review-desktop.html").as_uri()})
    opened = next(c["text"] for c in new["content"] if c.get("type") == "text" and c.get("text", "").startswith("opened page "))
    page = int(re.search(r"opened page (\d+)", opened)[1])
    (ROOT / "capture-page.json").write_text(json.dumps({"page_id": page,
        "group_id": "B4B5A1D184A4CA126657D42B40A5CB38", "window_id": 1698400956}), encoding="utf-8")
    for viewport in ("desktop", "mobile"):
        html = ROOT / ("review-" + viewport + ".html")
        if viewport == "mobile":
            call("navigate", {"page": page, "url": html.as_uri()})
        for destination, variant in sorted(targets["variants"].items()):
            channel = "canonical" if destination == "substack" else destination
            code = f"""const p=browser.page({page});
const snap=await p.snapshot({{mode:'interactive'}});
const line=snap.text.split('\\n').find(l=>l.includes('Choose reading view'));
if(!line)throw new Error('Reading-view control absent');
const ref=line.match(/\\[ref=(e\\d+)\\]/)[1];
await p.selectOption(ref,{json.dumps(channel)});
const ready=await p.waitForSelector('article[data-reading-view="{channel}"]');
if(!ready.matched)throw new Error('Reading view did not settle');
return await p.evaluateInPage(async()=>{{const a=document.querySelector('article[data-reading-view="{channel}"]');
await Promise.all(Array.from(a.querySelectorAll('img')).map(i=>i.decode()));
const r=a.getBoundingClientRect();return {{x:r.x+scrollX,y:r.y+scrollY,width:r.width,height:r.height,
pageWidth:Math.max(innerWidth,document.documentElement.scrollWidth)}};}});"""
            observed = run(code)
            geometry = observed["value"]
            screenshot = call("screenshot", {"page": page, "format": "png", "fullPage": True})
            block = next(c for c in screenshot["content"] if c.get("type") == "image")
            raw = base64.b64decode(block["data"], validate=True)
            identifier = "cc124-bitcoin-" + destination + "-" + viewport
            original = OUT / (identifier + "-page.png")
            original.write_bytes(raw)
            pixels = Image.open(io.BytesIO(raw))
            scale = pixels.width / geometry["pageWidth"]
            box = tuple(round(v * scale) for v in (geometry["x"], geometry["y"],
                geometry["x"] + geometry["width"], geometry["y"] + geometry["height"]))
            path = OUT / (identifier + ".png")
            pixels.crop(box).save(path)
            width, height = Image.open(path).size
            render = {"destination": destination, "viewport": viewport, "path": str(path),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "width": width, "height": height,
                "captured_at_utc": datetime.now(timezone.utc).isoformat(), "render_id": identifier,
                "variant_sha256": variant, "render_source": {"path": str(html),
                    "sha256": hashlib.sha256(html.read_bytes()).hexdigest()},
                "capture_method": "BrowserOS Neo screenshot; exact article bounds cropped from retained original browser pixels",
                "original_page_capture": {"path": str(original), "sha256": hashlib.sha256(raw).hexdigest()}}
            renders.append(render)
            (ROOT / "render-manifest.json").write_text(json.dumps({"renders": renders}, indent=2) + "\n", encoding="utf-8")
            print(json.dumps({"destination": destination, "viewport": viewport, "path": str(path),
                "width": width, "height": height, "sha256": render["sha256"]}), flush=True)
finally:
    client.close()
