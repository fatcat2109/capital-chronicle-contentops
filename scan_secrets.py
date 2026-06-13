import os
import re

FORBIDDEN_PATTERNS = [
    (r'[0-9]{9}:[a-zA-Z0-9_-]{35}', "Telegram token-like patterns"),
    (r'[-+]?[0-9]{9,}', "raw chat ID values"),
    (r'(?i)(AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36}|xox[baprs]-[0-9]{10,13}-[a-zA-Z0-9]{24}|AIza[0-9A-Za-z_-]{35})', "private key/AWS/GitHub/Slack/Google secret patterns"),
    (r'\.env', ".env path strings"),
    (r'https?://[^\s\"\']+', "raw request URL"),
    (r'raw platform response', "raw platform response"),
    (r'(?i)credential(_|\s)?value', "credential value"),
    (r'api\.telegram\.org', "api.telegram.org"),
    (r'sendMessage\(', "sendMessage as executable call"),
    (r'getMe\(', "getMe as executable call"),
    (r'live_publish', "live_publish"),
    (r'auto_publish', "auto_publish"),
    (r'schedule_post', "schedule_post"),
    (r'platform_api_call', "platform_api_call"),
    (r'scrape_metrics', "scrape_metrics"),
    (r'one_button_publish_all', "one_button_publish_all"),
    (r'public_ready\s*(:|=)\s*true', "public_ready true"),
    (r'\.(png|jpg|jpeg|gif|svg|webp)', "screenshot image file references"),
    (r'(?i)(\.gemini|antigravity-ide|brain)', "Antigravity/Gemini local brain paths")
]

ALLOWED_CONTEXTS = [
    "policy", "evidence", "forbidden", "disabled", "caveat", "no-go", "checklist", "schema", "placeholder"
]

def scan_file(filepath):
    results = []
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            for pattern, name in FORBIDDEN_PATTERNS:
                if re.search(pattern, line):
                    # Check if it's in a safe context
                    is_safe = False
                    lower_line = line.lower()
                    for ctx in ALLOWED_CONTEXTS:
                        if ctx in lower_line:
                            is_safe = True
                            break
                    classification = "SAFE (Allowed Context)" if is_safe else "UNSAFE"
                    results.append(f"{classification} - File: {filepath}:{i+1} | Pattern: {name} | Match: {line.strip()[:100]}")
    return results

def main():
    bundle_dir = "project_sources_bundle_AFTER_0169"
    all_results = []
    for root, _, files in os.walk(bundle_dir):
        for file in files:
            filepath = os.path.join(root, file)
            all_results.extend(scan_file(filepath))
            
    docs_dir = "docs"
    for file in os.listdir(docs_dir):
        if "AFTER_0169" in file:
            all_results.extend(scan_file(os.path.join(docs_dir, file)))
            
    print("SECRET SCAN RESULTS:")
    if not all_results:
        print("CLEAN. No forbidden patterns found.")
    else:
        for r in all_results:
            print(r)

if __name__ == "__main__":
    main()
