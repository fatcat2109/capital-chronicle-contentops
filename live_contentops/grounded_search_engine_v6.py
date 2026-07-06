"""Grounded search engine for financial, economic, and geopolitical news.

Leverages free APIs from GDELT Project and Yahoo Finance to fetch live context.
Stores results in a local JSON cache to prevent redundant queries.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.request
from pathlib import Path
from typing import Any

CACHE_DIR = Path("docs/automation/V6_AI_RESEARCH_GROUNDING/search_cache")
CACHE_EXPIRATION_SECONDS = 3600  # 1 hour cache limit


def clean_query(query: str) -> str:
    """Clean query string for API parameters."""
    return re.sub(r'[^a-zA-Z0-9\s-]', '', query).strip()


def query_gdelt(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Query GDELT DOC API v2 for geopolitical and international news."""
    cleaned = clean_query(query)
    encoded_query = urllib.parse.quote(cleaned)
    url = f"https://api.gdeltproject.org/api/v2/doc/doc?query={encoded_query}&mode=artlist&format=json"
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            articles = data.get("articles", [])
            results = []
            for art in articles[:limit]:
                results.append({
                    "title": art.get("title", "Untitled Article"),
                    "publisher": art.get("source", "GDELT Project"),
                    "url": art.get("url", ""),
                    "date": art.get("seendate", ""),
                    "summary": art.get("title", "")
                })
            return results
    except Exception as e:
        print(f"[Warning] GDELT search failed: {e}")
        return []


def query_yahoo_finance(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Query Yahoo Finance Search API for stock and macroeconomic news."""
    cleaned = clean_query(query)
    encoded_query = urllib.parse.quote(cleaned)
    url = f"https://query1.finance.yahoo.com/v1/finance/search?q={encoded_query}"
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            news = data.get("news", [])
            results = []
            for item in news[:limit]:
                results.append({
                    "title": item.get("title", "Untitled Financial Article"),
                    "publisher": item.get("publisher", "Yahoo Finance"),
                    "url": item.get("link", ""),
                    "date": str(item.get("providerPublishTime", "")),
                    "summary": item.get("title", "")
                })
            return results
    except Exception as e:
        print(f"[Warning] Yahoo Finance search failed: {e}")
        return []


def execute_grounded_search(query: str, limit_per_source: int = 5) -> list[dict[str, Any]]:
    """Orchestrate GDELT and Yahoo Finance queries, checking cache first."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    query_hash = hashlib.sha256(query.lower().strip().encode("utf-8")).hexdigest()
    cache_file = CACHE_DIR / f"{query_hash}.json"
    
    # Check cache validity
    if cache_file.exists():
        stat = cache_file.stat()
        if time.time() - stat.st_mtime < CACHE_EXPIRATION_SECONDS:
            try:
                cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
                print(f"[Info] Loaded {len(cached_data)} search results from cache.")
                return cached_data
            except Exception:
                pass
                
    print(f"[Info] Executing live grounded search for query: '{query}'")
    
    # Run concurrent-like searches from both sources
    gdelt_news = query_gdelt(query, limit=limit_per_source)
    yahoo_news = query_yahoo_finance(query, limit=limit_per_source)
    
    all_articles = gdelt_news + yahoo_news
    sources = []
    
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    
    for art in all_articles:
        title = art["title"]
        url = art["url"]
        publisher = art["publisher"]
        
        # Unique source ID based on URL
        source_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        
        sources.append({
            "source_id": f"src_{source_hash}",
            "title": title,
            "publisher_or_origin": publisher,
            "url_or_local_reference": url,
            "source_type": "reputable_news_context",
            "retrieved_at": timestamp,
            "freshness_label": "recent",
            "claim_summary": f"News report from {publisher}: {title}",
            "allowed_usage": "advisory_only",
            "limitations": [f"Grounded live search from query: {query}"],
            "citation_required": True,
            "synthetic_fixture": False
        })
        
    # Save to cache
    try:
        cache_file.write_text(json.dumps(sources, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except Exception as e:
        print(f"[Warning] Failed to write cache: {e}")
        
    return sources
