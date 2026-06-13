import os
from playwright.sync_api import sync_playwright

def run():
    target_dir = r"scratch\v4_recheck_0174U"
    os.makedirs(target_dir, exist_ok=True)
    
    url = r"file:///A:/Capital%20Chronicle/tools/cc-live-contentops/ui/institutional_operator_cockpit_v4/index.html"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # 1920x1080
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url)
        
        # Command Center
        page.click("text=Command Center")
        page.screenshot(path=os.path.join(target_dir, "1920x1080_command_center.png"), full_page=True)
        
        # Content Studio
        page.click("text=Content Studio")
        page.screenshot(path=os.path.join(target_dir, "1920x1080_content_studio.png"), full_page=True)
        
        # Publish Readiness Tower
        page.click("text=Publish Readiness Tower")
        page.screenshot(path=os.path.join(target_dir, "1920x1080_publish_readiness.png"), full_page=True)
        
        # Evidence Vault
        page.click("text=Evidence Vault")
        page.screenshot(path=os.path.join(target_dir, "1920x1080_evidence_vault.png"), full_page=True)
        
        # Content Calendar
        page.click("text=Content Calendar / Workflow")
        page.screenshot(path=os.path.join(target_dir, "1920x1080_content_calendar.png"), full_page=True)
        
        # Visual Export
        page.click("text=Visual Export / Screenshot-Safe")
        page.screenshot(path=os.path.join(target_dir, "1920x1080_visual_export.png"), full_page=True)
        
        # Settings
        page.click("text=Settings / Safety Policy")
        page.screenshot(path=os.path.join(target_dir, "1920x1080_settings.png"), full_page=True)
        
        # 1440x900
        page.set_viewport_size({"width": 1440, "height": 900})
        
        page.click("text=Command Center")
        page.screenshot(path=os.path.join(target_dir, "1440x900_command_center.png"), full_page=True)
        
        page.click("text=Content Studio")
        page.screenshot(path=os.path.join(target_dir, "1440x900_content_studio.png"), full_page=True)
        
        page.click("text=Publish Readiness Tower")
        page.screenshot(path=os.path.join(target_dir, "1440x900_publish_readiness.png"), full_page=True)
        
        page.click("text=Evidence Vault")
        page.screenshot(path=os.path.join(target_dir, "1440x900_evidence_vault.png"), full_page=True)
        
        page.click("text=Content Calendar / Workflow")
        page.screenshot(path=os.path.join(target_dir, "1440x900_content_calendar.png"), full_page=True)
        
        page.click("text=Visual Export / Screenshot-Safe")
        page.screenshot(path=os.path.join(target_dir, "1440x900_visual_export.png"), full_page=True)
        
        page.click("text=Settings / Safety Policy")
        page.screenshot(path=os.path.join(target_dir, "1440x900_settings.png"), full_page=True)
        
        # 1366x768
        page.set_viewport_size({"width": 1366, "height": 768})
        page.click("text=Command Center")
        page.screenshot(path=os.path.join(target_dir, "1366x768_command_center.png"), full_page=True)
        
        browser.close()

if __name__ == "__main__":
    run()
