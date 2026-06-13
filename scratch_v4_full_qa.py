import os
from playwright.sync_api import sync_playwright

def run():
    target_dir = r"scratch\v4_full_qa_screenshots"
    os.makedirs(target_dir, exist_ok=True)
    
    url = r"file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/institutional_operator_cockpit_v4/index.html"
    
    screens = [
        ("command_center", "Command Center"),
        ("content_studio", "Content Studio"),
        ("publish_readiness", "Publish Readiness Tower"),
        ("evidence_vault", "Evidence Vault"),
        ("content_calendar", "Content Calendar / Workflow"),
        ("visual_export", "Visual Export / Screenshot-Safe"),
        ("settings_safety_policy", "Settings / Safety Policy")
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        print(f"Opening {url}")
        page.goto(url)
        page.wait_for_timeout(1000)
        
        # Capture Command Center at 1366x768 and 1920x1080
        page.set_viewport_size({"width": 1366, "height": 768})
        page.screenshot(path=os.path.join(target_dir, "1366x768_command_center.png"), full_page=True)
        
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.screenshot(path=os.path.join(target_dir, "1920x1080_command_center.png"), full_page=True)
        
        # Capture all screens at 1440x900
        page.set_viewport_size({"width": 1440, "height": 900})
        
        for screen_id, label in screens:
            print(f"Capturing 1440x900_{screen_id}.png ...")
            nav_item = page.get_by_role("button", name=label, exact=True)
            if nav_item.count() > 0:
                nav_item.nth(0).click()
            else:
                print(f"Warning: nav item for {screen_id} ('{label}') not found.")
            
            page.wait_for_timeout(500)
            out_path = os.path.join(target_dir, f"1440x900_{screen_id}.png")
            page.screenshot(path=out_path, full_page=True)
            
        browser.close()
        
    print("Full QA screenshots captured.")

if __name__ == "__main__":
    run()
