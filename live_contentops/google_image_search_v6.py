"""Google Image Search and Downloader for V6 ContentOps news.

Queries Google Images and extracts relevant image URLs.
Uses urllib.request first, falling back to Playwright headless browser.
Saves downloaded files locally inside docs/automation/V6_MEDIA_SYSTEM/downloads/.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

DOWNLOAD_DIR = Path("docs/automation/V6_MEDIA_SYSTEM/downloads")
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/100.0.0.0 Safari/537.36"
)


def clean_search_query(query: str) -> str:
    """Clean the query for clean Google Search parameter formatting."""
    return re.sub(r'[^a-zA-Z0-9\s-]', '', query).strip()


def download_image(url: str, output_path: Path) -> bool:
    """Download image payload via HTTP request."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as response:
            output_path.write_bytes(response.read())
        return True
    except Exception as e:
        print(f"[Warning] Failed to download image from {url}: {e}")
        return False


def search_google_image_urllib(query: str) -> list[str]:
    """Search Google Images via standard urllib HTTP requests."""
    cleaned = clean_search_query(query)
    encoded = urllib.parse.quote(cleaned)
    url = f"https://www.google.com/search?q={encoded}&tbm=isch"
    
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8", errors="ignore")
            # Google images classic output regex match for image urls
            img_urls = re.findall(r'src="([^"]+)"', html)
            valid = []
            for u in img_urls:
                if u.startswith("http") and ("gstatic" in u or u.endswith((".jpg", ".jpeg", ".png"))):
                    valid.append(u)
            return valid
    except Exception as e:
        print(f"[Warning] Urllib Google Image search failed: {e}")
        return []


def search_google_image_playwright(query: str) -> list[str]:
    """Search Google Images via headless Playwright browser to bypass blocks."""
    cleaned = clean_search_query(query)
    encoded = urllib.parse.quote(cleaned)
    url = f"https://www.google.com/search?q={encoded}&tbm=isch"
    
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


def execute_google_image_search_and_download(query: str, custom_filename: str | None = None) -> tuple[str | None, str | None]:
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
    img_urls = search_google_image_urllib(query)
    
    # 2. Fall back to Playwright if no images found
    if not img_urls:
        print("[Info] Urllib returned no images. Falling back to Playwright search.")
        img_urls = search_google_image_playwright(query)
        
    if not img_urls:
        print(f"[Warning] No Google Images found for query: '{query}'")
        return None, None
        
    # Attempt downloading matching candidate URLs until one succeeds
    for url in img_urls:
        if download_image(url, output_path):
            print(f"[Info] Successfully downloaded Google Image to: {output_path}")
            try:
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump({"url": url}, f)
            except Exception:
                pass
            return str(output_path), url
            
    return None, None
