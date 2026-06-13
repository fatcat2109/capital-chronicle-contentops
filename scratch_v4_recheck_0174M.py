import os
from playwright.sync_api import sync_playwright

def run():
    target_dir = r"scratch\v4_recheck_0174M"
    os.makedirs(target_dir, exist_ok=True)
    
    url = r"file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/institutional_operator_cockpit_v4/index.html"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        print(f"Opening {url}")
        page.goto(url)
        page.wait_for_timeout(1000)
        
        # 1366x768 Command Center
        page.set_viewport_size({"width": 1366, "height": 768})
        page.screenshot(path=os.path.join(target_dir, "1366x768_command_center.png"), full_page=True)
        
        # 1440x900 screens
        page.set_viewport_size({"width": 1440, "height": 900})
        
        # Command Center
        page.screenshot(path=os.path.join(target_dir, "1440x900_command_center.png"), full_page=True)
        
        # Content Studio
        nav_item = page.get_by_role("button", name="Content Studio", exact=True)
        if nav_item.count() > 0: nav_item.nth(0).click()
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(target_dir, "1440x900_content_studio.png"), full_page=True)
        
        # Publish Readiness
        nav_item = page.get_by_role("button", name="Publish Readiness Tower", exact=True)
        if nav_item.count() > 0: nav_item.nth(0).click()
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(target_dir, "1440x900_publish_readiness.png"), full_page=True)
        
        # Evidence Vault
        nav_item = page.get_by_role("button", name="Evidence Vault", exact=True)
        if nav_item.count() > 0: nav_item.nth(0).click()
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(target_dir, "1440x900_evidence_vault.png"), full_page=True)
        
        # Settings
        nav_item = page.get_by_role("button", name="Settings / Safety Policy", exact=True)
        if nav_item.count() > 0: nav_item.nth(0).click()
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(target_dir, "1440x900_settings.png"), full_page=True)
        
        browser.close()
        
    print("Recheck 0174M screenshots captured.")

if __name__ == "__main__":
    run()
