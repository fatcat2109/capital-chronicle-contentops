"""Google Image Search and Downloader for V6 ContentOps news.

Queries Google Images and extracts relevant image URLs.
Uses urllib.request first, falling back to Playwright headless browser.
Saves downloaded files locally inside docs/automation/V6_MEDIA_SYSTEM/downloads/.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import urllib.parse
import urllib.request
import time
from pathlib import Path

DOWNLOAD_DIR = Path("docs/automation/V6_MEDIA_SYSTEM/downloads")
DOWNLOAD_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)
USER_AGENT = DOWNLOAD_USER_AGENT
GOOGLE_SEARCH_USER_AGENTS = (
    # Google often serves a classic/static image table to these clients.
    "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 5 Build/KOT49H) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/34.0.1847.114 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; U; Android 2.3.6; en-us; Nexus S Build/GRK39F) "
    "AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)",
    DOWNLOAD_USER_AGENT,
)
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
BAD_URL_MARKERS = (
    "googlelogo",
    "/logos/",
    "favicon",
    "sprite",
    "profile_images",
    "avatar",
    "icon-editorial",
    "google-meet",
)


def _image_magic(data: bytes) -> bool:
    return (
        data.startswith(b"\xff\xd8\xff")
        or data.startswith(b"\x89PNG\r\n\x1a\n")
        or data.startswith(b"RIFF") and data[8:12] == b"WEBP"
        or data.startswith(b"GIF87a")
        or data.startswith(b"GIF89a")
    )


def clean_search_query(query: str) -> str:
    """Clean the query for clean Google Search parameter formatting."""
    cleaned = re.sub(r'[^a-zA-Z0-9\s-]', ' ', query)
    cleaned = re.sub(r"\bUS\b", "United States", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _normalize_candidate_url(raw_url: str) -> str | None:
    """Normalize a candidate image URL found in HTML/JS payloads."""
    if not raw_url:
        return None
    value = html.unescape(raw_url).strip()
    value = value.replace("\\/", "/")
    if "\\u" in value or "\\x" in value:
        value = value.encode("utf-8", errors="ignore").decode("unicode_escape", errors="ignore")
    unquoted = urllib.parse.unquote(value)
    if unquoted.startswith(("http://", "https://")):
        value = unquoted
    if value.startswith("//"):
        value = f"https:{value}"
    if value.startswith("/imgres?") or value.startswith("https://www.google.com/imgres?"):
        parsed = urllib.parse.urlparse(value if value.startswith("http") else f"https://www.google.com{value}")
        params = urllib.parse.parse_qs(parsed.query)
        imgurl = (params.get("imgurl") or params.get("imgrefurl") or [""])[0]
        if imgurl:
            value = urllib.parse.unquote(imgurl)
    if not value.startswith(("http://", "https://")):
        return None
    parsed = urllib.parse.urlparse(value)
    if not parsed.netloc:
        return None
    lowered = value.lower()
    if any(marker in lowered for marker in BAD_URL_MARKERS):
        return None
    if ("encrypted-tbn" in lowered and "/images?" in lowered) or ("google.com/images?q=tbn:" in lowered):
        return value
    if lowered.split("?", 1)[0].endswith(IMAGE_EXTENSIONS):
        return value
    return None


def _dedupe(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for url in urls:
        key = url.split("#", 1)[0]
        if key in seen:
            continue
        seen.add(key)
        out.append(url)
    return out


def extract_image_candidates_from_html(raw_html: str) -> list[str]:
    """Extract image candidates from classic HTML and escaped JS payloads."""
    text = html.unescape(raw_html)
    patterns = [
        r'''(?:src|data-src|data-iurl|data-ou)=["']([^"']+)["']''',
        r'''"(?:ou|murl|turl)"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"''',
        r'''[?&]imgurl=([^&"'<>\s]+)''',
        r'''https?://[^"'<>\\\s]+?\.(?:jpg|jpeg|png|webp)(?:\?[^"'<>\\\s]*)?''',
        r'''https?://encrypted-tbn\d\.gstatic\.com/images\?q=tbn:[^"'<>\\\s]+''',
        r'''/images\?q=tbn:[^"'&<>\s]+''',
    ]
    direct: list[str] = []
    thumbs: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, text, flags=re.IGNORECASE):
            candidate = match if isinstance(match, str) else match[0]
            if candidate.startswith("/images?"):
                candidate = f"https://www.google.com{candidate}"
            normalized = _normalize_candidate_url(candidate)
            if not normalized:
                continue
            if "encrypted-tbn" in normalized or "google.com/images?q=tbn" in normalized:
                thumbs.append(normalized)
            else:
                direct.append(normalized)
    return _dedupe(direct + thumbs)


def _google_recency_tbs(recency_days: int | None = 365) -> str:
    if not recency_days or recency_days <= 0:
        return ""
    if recency_days <= 1:
        return "qdr:d"
    if recency_days <= 7:
        return "qdr:w"
    if recency_days <= 31:
        return "qdr:m"
    if recency_days <= 365:
        return "qdr:y"
    return ""


def download_image(url: str, output_path: Path) -> bool:
    """Download image payload via HTTP request."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": DOWNLOAD_USER_AGENT,
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            content_type = (response.headers.get("Content-Type") or "").lower()
            payload = response.read()
        if len(payload) < 2048 or not (_image_magic(payload) or content_type.startswith("image/")):
            print(f"[Warning] Rejected non-image or tiny payload from {url}: {content_type or 'missing_content_type'} {len(payload)} bytes")
            return False
        output_path.write_bytes(payload)
        return True
    except Exception as e:
        print(f"[Warning] Failed to download image from {url}: {e}")
        return False


def search_google_image_urllib(query: str, recency_days: int | None = 365) -> list[str]:
    """Search Google Images via standard urllib HTTP requests."""
    cleaned = clean_search_query(query)
    encoded = urllib.parse.quote(cleaned)
    tbs = _google_recency_tbs(recency_days)
    tbs_param = f"&tbs={urllib.parse.quote(tbs)}" if tbs else ""
    urls = [
        f"https://www.google.com/search?q={encoded}&tbm=isch&hl=en&safe=active{tbs_param}",
        f"https://www.google.com/search?q={encoded}&udm=2&hl=en&safe=active{tbs_param}",
        f"https://www.google.com/search?q={encoded}&tbm=isch&hl=en&safe=active&gbv=1{tbs_param}",
        f"https://www.google.com/images?q={encoded}&hl=en&safe=active{tbs_param}",
    ]

    candidates: list[str] = []
    for user_agent in GOOGLE_SEARCH_USER_AGENTS:
        for url in urls:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Cookie": "CONSENT=YES+cb",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    page_html = response.read().decode("utf-8", errors="ignore")
                found = extract_image_candidates_from_html(page_html)
                if found:
                    candidates.extend(found)
            except Exception as e:
                print(f"[Warning] Urllib Google Image search failed for {url}: {e}")
    return _dedupe(candidates)


def _commons_queries(query: str) -> list[str]:
    lowered = clean_search_query(query).lower()
    queries: list[str] = []
    if "oil" in lowered or "crude" in lowered or "energy" in lowered:
        queries.extend(["crude oil price chart", "WTI crude oil price chart", "oil prices chart"])
    if "recession" in lowered or "yield" in lowered or "curve" in lowered:
        queries.extend(["yield curve recession graph", "US Treasury interest rates"])
    if "inflation" in lowered:
        queries.append("inflation and oil price chart")
    queries.append(clean_search_query(query))
    return _dedupe(queries)


def search_commons_image_urllib(query: str) -> list[str]:
    """Find topic-related public chart images from Wikimedia Commons as a no-browser fallback."""
    preferred: list[str] = []
    fallback: list[str] = []
    for commons_query in _commons_queries(query):
        params = urllib.parse.urlencode({
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": commons_query,
            "gsrnamespace": "6",
            "gsrlimit": "15",
            "prop": "imageinfo",
            "iiprop": "url|mime|size|extmetadata",
        })
        url = f"https://commons.wikimedia.org/w/api.php?{params}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "CapitalChronicleContentOps/1.0"})
            with urllib.request.urlopen(req, timeout=15) as response:
                payload = json.loads(response.read().decode("utf-8", errors="ignore"))
        except Exception as exc:
            print(f"[Warning] Wikimedia Commons image fallback failed for '{commons_query}': {exc}")
            continue
        pages = payload.get("query", {}).get("pages", {}) if isinstance(payload, dict) else {}
        for page in pages.values():
            info = (page.get("imageinfo") or [{}])[0]
            mime = str(info.get("mime") or "").lower()
            image_url = str(info.get("url") or "")
            if mime not in {"image/jpeg", "image/png", "image/webp"}:
                continue
            normalized = _normalize_candidate_url(image_url)
            if normalized:
                if mime in {"image/jpeg", "image/png"}:
                    preferred.append(normalized)
                else:
                    fallback.append(normalized)
    return _dedupe(preferred + fallback)


def search_google_image_playwright(query: str, recency_days: int | None = 365) -> list[str]:
    """Search Google Images via headless Playwright browser to bypass blocks."""
    cleaned = clean_search_query(query)
    encoded = urllib.parse.quote(cleaned)
    tbs = _google_recency_tbs(recency_days)
    tbs_param = f"&tbs={urllib.parse.quote(tbs)}" if tbs else ""
    url = f"https://www.google.com/search?q={encoded}&tbm=isch{tbs_param}"
    
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[Warning] Playwright library not installed. Bypassing Playwright search.")
        return []
        
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=USER_AGENT)
            page.goto(url)
            try:
                # Wait for standard Google Images containers to resolve
                page.wait_for_selector("img", timeout=5000)
            except Exception:
                pass
                
            imgs = page.query_selector_all("img")
            valid = []
            for img in imgs:
                src = img.get_attribute("src")
                if src and src.startswith("http"):
                    # Ignore common Google icons, search buttons, or tracking pixels
                    if "gstatic" in src or ("google" not in src and not src.endswith(".gif")):
                        valid.append(src)
            browser.close()
            return valid
    except Exception as e:
        print(f"[Warning] Playwright Google Image search failed: {e}")
        return []


def execute_google_image_search_and_download(query: str, custom_filename: str | None = None, recency_days: int | None = 365) -> tuple[str | None, str | None]:
    """Search Google Images, retrieve the first valid match, and download it."""
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    query_hash = hashlib.sha256(query.lower().strip().encode("utf-8")).hexdigest()[:12]
    filename = custom_filename or f"img_{query_hash}.jpg"
    output_path = DOWNLOAD_DIR / filename
    meta_path = output_path.with_suffix(".json")
    
    # Check if we already have a cached download
    if output_path.exists() and output_path.stat().st_size > 100:
        url = None
        if meta_path.exists():
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    url = json.load(f).get("url")
            except Exception:
                pass
        print(f"[Info] Found cached Google Image for query '{query}': {output_path}")
        return str(output_path), url
        
    print(f"[Info] Executing Google Image search for query: '{query}'")
    
    # 1. Try standard urllib search
    img_urls = search_google_image_urllib(query, recency_days=recency_days)
    
    # 2. Fall back to Playwright if no images found
    if not img_urls:
        print("[Info] Urllib returned no images. Falling back to Playwright search.")
        img_urls = search_google_image_playwright(query, recency_days=recency_days)

    # 3. Final browserless public-source fallback. This still returns a real,
    # sourceable macro/news chart instead of a branded placeholder card.
    if not img_urls:
        print("[Info] Google/Playwright returned no images. Falling back to Wikimedia Commons chart search.")
        img_urls = search_commons_image_urllib(query)
        
    if not img_urls:
        print(f"[Warning] No Google Images found for query: '{query}'")
        return None, None
        
    # Attempt downloading matching candidate URLs until one succeeds
    for url in img_urls:
        parsed_suffix = Path(urllib.parse.urlparse(url).path).suffix.lower()
        candidate_path = output_path.with_suffix(parsed_suffix) if parsed_suffix in IMAGE_EXTENSIONS else output_path
        candidate_meta_path = candidate_path.with_suffix(".json")
        if download_image(url, candidate_path):
            print(f"[Info] Successfully downloaded Google Image to: {candidate_path}")
            parsed = urllib.parse.urlparse(url)
            source_domain = parsed.netloc.lower().removeprefix("www.")
            image_search_metadata = {
                "url": url,
                "image_url": url,
                "source_page_url": url,
                "source_url": url,
                "source_domain": source_domain,
                "query": query,
                "source_label": source_domain,
                "canonical_source_label": source_domain,
                "recency_days": recency_days,
                "time_filter": _google_recency_tbs(recency_days) or "none",
                "retrieval_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "retrieval_method": "google_image_or_public_fallback",
                "rights_status": "operator_review_required_search_image",
                "provenance_status": "search_discovered_requires_source_page_rights_review",
                "operator_review_required": True,
                "why_selected": "Search-discovered candidate downloaded for editorial review; not auto-approved without source-page rights and relevance review.",
                "media_class": "operator_review_required",
            }
            try:
                with open(candidate_meta_path, "w", encoding="utf-8") as f:
                    json.dump(image_search_metadata, f, indent=2, sort_keys=True)
            except Exception:
                pass
            return str(candidate_path), url
            
    return None, None
