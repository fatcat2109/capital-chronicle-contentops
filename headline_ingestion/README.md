# Step 1: X List Headlines Ingestion Tool (CDP)

This is the isolated **Step 1: Data Ingestion** tool extracted from Capital Chronicle. It is designed to pull headlines (tweets) from a specific X (formerly Twitter) list into ContentOps using **Chrome DevTools Protocol (CDP)**.

By fetching and archiving up-to-date headlines, this tool enables downstream content generators to leverage current context without spending unnecessary compute resources on repetitive scraping or broad topic selection.

## How It Works

1. **CDP Connection**: The script connects to an already-running Chrome browser session over port `9222`.
2. **List Navigation**: It opens or attaches to a tab with X.com and navigates to the target list (`https://x.com/i/lists/1843870469143048642`).
3. **Response Interception**: Intercepts network calls matching `ListLatestTweetsTimeline` to extract clean JSON tweet structures.
4. **Scrolling & Interception (Phase 1)**: Scroll down systematically to fetch historical tweets.
5. **Streaming/Monitoring (Phase 2)**: Monitor and click the "Show new posts" button or reload periodically to capture fresh updates.
6. **Data Archiving**: Writes the outputs to:
   - `data/capital_chronicle_ALL_DATA.json` (and `.md`) containing all crawled historical headlines.
   - `data/capital_chronicle_YYYY_MM_DD.json` (and `.md`) for daily segmented headlines.
   - `data/intake/headline_sidecars/step1_headline_sidecar_YYYY_MM_DD.jsonl` with structured tags, catalyst classification, and quality warning flags.

## Prerequisites

1. **Python 3.12+**
2. **Google Chrome** (or Chromium) running with remote debugging enabled:
   - **Windows**:
     ```powershell
     & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="C:\Users\bullw\.gemini\antigravity-ide\chrome-profile-ingestion"
     ```
     *(Note: Log in to your X.com account in this browser window before running the script)*

## Setup

Install the required Python package:
```bash
pip install -r requirements.txt
```
*(Optionally run `playwright install` if using standard Playwright browsers, though this tool connects to your existing Chrome instance over CDP).*

## Running the Ingestion Tool

With your Chrome browser running on port `9222` and logged in to X, run:
```bash
python Data_Ingestion.py
```

The script will:
- Attach to the Chrome tab.
- Automatically navigate to the X list.
- Scroll to populate history and monitor for new incoming headlines.
- Log progress in terminal and in `data/ingestion.log`.
