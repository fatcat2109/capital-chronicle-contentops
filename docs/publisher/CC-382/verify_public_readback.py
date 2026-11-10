"""Read the actual published CC-338 package; write only CC-382 evidence.

This does not run tests, replay a store, invoke editorial roles or send a post.
The browser markdown must come from the current public canonical via Neo read.
"""
import ast
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
LIVE = Path(r"A:\Capital Chronicle\ContentOps")
BUILDER = HERE.parents[2]
OP = Path(r"A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual\cc338-cpi-preview-20261110-v1")
sys.path.insert(0, str(LIVE))
from live_contentops import public_instruments_v1 as instruments


def load(path):
    return json.loads(path.read_bytes())


def info(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def original_url(url):
    return unquote(url[url.index("https%3A"):]) if "https%3A" in url else url


def normalized(text):
    text = re.sub(r"\[\[SOURCE:[^\]]+\]\]", "", text)
    return re.sub(r"\s+", " ", re.sub(r"[*_#]", "", text)).strip()


now = datetime.now(timezone.utc).isoformat()
markdown_path = Path(sys.argv[1])
markdown = markdown_path.read_text(encoding="utf-8")
public_article = markdown.split("\n#### Discussion about this post", 1)[0]
article = load(OP / "article_manifest_v1.json")
assert article["public_instrument_policy"] == instruments.POLICY
instruments.validate_article(article)
public_projection = {"title": article["title"], "substack_body_markdown": public_article,
                     "public_instrument_policy": article["public_instrument_policy"]}
instruments.validate_article(public_projection)
coverage = {}
for market, (name, symbols) in instruments.INSTRUMENTS.items():
    found = [s for s in symbols if re.search(r"\b" + s + r"\b", public_article)]
    assert found, name
    coverage[name] = found

# Compare the authored instrument paragraphs with the current public copy.
paragraphs = [p for p in article["substack_body_markdown"].split("\n\n")
              if any(re.search(r"\b" + s + r"\b", p) for _, symbols in instruments.INSTRUMENTS.values()
                     for s in symbols if s != "BTC")]
assert paragraphs
assert all(normalized(p) in normalized(public_article) for p in paragraphs)
request = load(OP / "desktop_request_write.json")
assert "CC382_PUBLIC_INSTRUMENTS" in json.dumps(request)

asset_path = OP / "media/tradingview/refresh-1855/asset.json"
asset = load(asset_path)
tree = ast.parse((LIVE / "live_contentops/tradingview_snapshot_v1.py").read_text(encoding="utf-8"))
symbol_map = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == "SYMBOLS" for t in n.targets))
assert asset["tradingview_snapshot"]["tv_symbol"] == symbol_map["XAUUSD"] == "FX_IDC:XAUUSD"
assert info(Path(asset["path"]))["sha256"] == asset["sha256"]
assert info(Path(asset["tradingview_snapshot"]["path"]))["sha256"] == asset["tradingview_snapshot"]["sha256"]
assert asset["caption"] in public_article and asset["alt_text"] in public_article

# Reuse the exact public byte readback, and prove that today's page still uses
# those same original image URLs. Do not confuse an old capture with a fresh one.
prior_path = OP / "canonical-repair-readback-response-fixed.json"
prior = load(prior_path)["result"]
assert prior["content_verified"] and asset["sha256"] in prior["observed_media_sha256"]
current_urls = re.findall(r"\]\((https://substackcdn\.com/[^\s)]+)\)", public_article)
current_originals = [original_url(u) for u in current_urls]
prior_originals = [original_url(u) for u in prior["public_image_urls"]]
assert current_originals == prior_originals
assert len(current_originals) == 5

command = [sys.executable, "scripts/run_native_desktop_editorial.py", "publication-status",
           "--binding", str(OP / "binding.json"), "--rollout", "config/native_desktop_rollout_v1.json"]
observed = subprocess.run(command, cwd=LIVE, capture_output=True, text=True, timeout=45)
assert observed.returncode == 0, observed.stderr[-500:]
status = json.loads(observed.stdout)
if status.get("classification") == "TOOL_OUTPUT_IN_FILE":
    ref = status["output"]
    raw = Path(ref["path"]).read_bytes()
    assert sha256(raw).hexdigest() == ref["sha256"]
    status = json.loads(raw)
publication = status.get("publication", status)
assert publication["canonical_article_real_published"]
assert publication["canonical_url"] == prior["url"]
assert publication["unknown_write_count"] == 0

source_checks = []
for row in load(HERE / "integration.json")["files"]:
    rel = row["path"]
    installed = (LIVE / rel).read_bytes().replace(b"\r\n", b"\n")
    builder = (BUILDER / rel).read_bytes().replace(b"\r\n", b"\n")
    committed = subprocess.check_output(["git", "-C", str(LIVE), "show", "HEAD:" + rel]).replace(b"\r\n", b"\n")
    assert installed == builder == committed, rel
    source_checks.append({"path": rel, "normalized_sha256": sha256(installed).hexdigest(),
                          "installed_matches_builder_and_operating_commit": True})

(HERE / "public-readback-20261110.md").write_text(public_article.rstrip() + "\n", encoding="utf-8")
result = {
    "item": "CC-382", "observed_at_utc": now, "acceptance": "PASS",
    "run_id": request["run_id"], "canonical_url": publication["canonical_url"],
    "public_object_id": "224293572", "published_at_utc": prior["published_at_utc"],
    "article_and_wrap": "CC-124 decision 98: CPI/PPI event preview is that day's wrap; no second wrap.",
    "choice": "Close the existing acceptance on the published CPI preview/wrap; preserve its identity and frozen package.",
    "configured_launch": {"pid": 29484, "model": "gpt-6.1-sol", "effort": "high",
                          "telemetry": "CONFIGURED_NOT_OBSERVED"},
    "public_instrument_policy": article["public_instrument_policy"],
    "instruments_by_market": coverage, "forbidden_public_names": [],
    "installed_article_validator": str(Path(instruments.__file__).resolve()),
    "actual_article_package_validation": "PASS", "current_public_copy_validation": "PASS",
    "authored_instrument_paragraphs_match_current_public_copy": len(paragraphs),
    "request_includes_cc382_guidance": True,
    "chart": {"asset": info(asset_path), "image": info(Path(asset["path"])),
              "feed": asset["tradingview_snapshot"]["tv_symbol"],
              "captured_at_utc": asset["tradingview_snapshot"]["captured_at_utc"],
              "current_public_caption_and_alt_match": True,
              "public_byte_hash_observation_at_utc": prior["observed_at_utc"],
              "prior_byte_readback": info(prior_path),
              "current_original_image_urls_equal_prior_byte_readback": True},
    "current_public_image_original_urls": current_originals,
    "inputs": [info(markdown_path), info(OP / "article_manifest_v1.json"),
               info(OP / "desktop_request_write.json")],
    "publication_status": publication, "source_checks": source_checks,
    "operating_head_before_evidence": git(LIVE, "rev-parse", "HEAD"),
    "tests": "None started during the 10 November 18:30-22:30 GMT+7 blackout; actual published-package checks only.",
    "new_public_writes": 0, "new_editorial_calls": 0, "schedule_changes": 0,
    "limits": "LinkedIn API TLS recovery and CC-338's G05 freeze-file gap remain with their existing items; neither changes this public text/chart acceptance."
}
(HERE / "public-readback-20261110.json").write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
print(json.dumps({"acceptance": result["acceptance"], "markets": coverage,
                  "canonical": publication["canonical_url"], "chart_feed": symbol_map["XAUUSD"],
                  "evidence": str(HERE / "public-readback-20261110.json")}))
