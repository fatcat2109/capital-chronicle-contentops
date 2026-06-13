import os
from playwright.sync_api import sync_playwright

def run():
    target_dir = r"scratch\v4_recheck_screenshots"
    os.makedirs(target_dir, exist_ok=True)
    
    url = r"file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/institutional_operator_cockpit_v4/index.html"
    
    viewports = [
        (1366, 768),
        (1440, 900),
        (1536, 864),
        (1920, 1080)
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        print(f"Opening {url}")
        page.goto(url)
        page.wait_for_timeout(1000)
        
        for w, h in viewports:
            print(f"Capturing Command Center at {w}x{h}...")
            page.set_viewport_size({"width": w, "height": h})
            page.wait_for_timeout(500)
            out_path = os.path.join(target_dir, f"{w}x{h}_command_center_recheck.png")
            page.screenshot(path=out_path, full_page=True)
            
        browser.close()
        
    print("Recheck screenshots captured.")

if __name__ == "__main__":
    run()
