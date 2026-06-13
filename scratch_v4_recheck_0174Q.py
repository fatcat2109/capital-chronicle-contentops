import os
from playwright.sync_api import sync_playwright

def run():
    target_dir = r"scratch\v4_recheck_0174Q"
    os.makedirs(target_dir, exist_ok=True)
    
    url = r"file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/institutional_operator_cockpit_v4/index.html"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        print(f"Opening {url}")
        page.goto(url)
        page.wait_for_timeout(1000)
        
        # 1440x900 screens
        page.set_viewport_size({"width": 1440, "height": 900})
        
        # Sparse screen (Settings)
        nav_item = page.get_by_role("button", name="Settings / Safety Policy", exact=True)
        if nav_item.count() > 0: nav_item.nth(0).click()
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(target_dir, "1440x900_settings.png"), full_page=True)
        
        # Publish Readiness
        nav_item = page.get_by_role("button", name="Publish Readiness Tower", exact=True)
        if nav_item.count() > 0: nav_item.nth(0).click()
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(target_dir, "1440x900_publish_readiness.png"), full_page=True)
        
        browser.close()
        
    print("Recheck 0174Q screenshots captured.")

if __name__ == "__main__":
    run()
