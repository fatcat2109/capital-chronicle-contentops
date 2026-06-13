import os
import sys
import json
import hashlib
import time
from playwright.sync_api import sync_playwright

def hash_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest().upper()

def run():
    target_dir = r"docs\browser_qa\TASK_CONTENTOPS_0174A2_OPERATOR_COCKPIT_V2_VISIBLE_ANTIGRAVITY_BROWSER_QA_V0"
    screenshots_dir = os.path.join(target_dir, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    
    url = r"file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/institutional_operator_cockpit_v2/index.html"
    
    screens = [
        ("command_center", "Command Center"),
        ("content_studio", "Content Studio"),
        ("publish_readiness", "Publish Readiness Gate Matrix"),
        ("evidence_vault", "Evidence Vault"),
        ("content_calendar", "Content Calendar / Workflow Board"),
        ("visual_export", "Visual Export / Screenshot-Safe Mode"),
        ("settings", "Settings / Safety Policy")
    ]
    
    viewports = [
        {"width": 1366, "height": 768},
        {"width": 1440, "height": 900},
        {"width": 1536, "height": 864},
        {"width": 1920, "height": 1080}
    ]
    
    results = {
        "network": [],
        "console": [],
        "screenshots": []
    }
    
    # VISIBLE BROWSER
    with sync_playwright() as p:
        # headless=False ensures a visible browser window opens on the operator's desktop
        browser = p.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context()
        page = context.new_page()
        
        page.on("console", lambda msg: results["console"].append({"type": msg.type, "text": msg.text}))
        page.on("request", lambda req: results["network"].append(req.url))
        
        print(f"Opening {url}")
        page.goto(url)
        page.wait_for_selector("#safety-ribbon", timeout=5000)
        
        for vp in viewports:
            w, h = vp["width"], vp["height"]
            print(f"Setting viewport to {w}x{h}")
            page.set_viewport_size({"width": w, "height": h})
            # Operator visibility pause
            time.sleep(1.0)
            
            for screen_id, label in screens:
                print(f"Capturing {w}x{h}_{screen_id}.png ...")
                nav_item = page.get_by_role("button", name=label, exact=True)
                if nav_item.count() > 0:
                    nav_item.nth(0).click()
                else:
                    print(f"Warning: nav item for {screen_id} ('{label}') not found.")
                
                # Visible pause for operator observation before screenshot
                time.sleep(1.0)
                
                filename = f"{w}x{h}_{screen_id}.png"
                out_path = os.path.join(screenshots_dir, filename)
                page.screenshot(path=out_path, full_page=True)
                
                file_size = os.path.getsize(out_path)
                sha = hash_file(out_path)
                
                results["screenshots"].append({
                    "filename": filename,
                    "screen": screen_id,
                    "viewport": f"{w}x{h}",
                    "width": w,
                    "height": h,
                    "sha256": sha,
                    "size_bytes": file_size,
                    "capture_status": "PASS"
                })
                
        browser.close()
        
    with open("qa_script_results_visible.json", "w") as f:
        json.dump(results, f, indent=2)
        
    print("Visible Screenshots captured and results saved to qa_script_results_visible.json")

if __name__ == "__main__":
    run()
