# ContentOps V6 — Live Run Approach & CDP UI Mitigation Guide

This document defines our operational approach for live runs across all 8 platforms and outlines strategies to handle UI drift on platforms that utilize Playwright Browser Automation (CDP).

---

## 1. Live Run Invariants & Platform Tiering

We operate under **Fast Ship Mode**, which bypasses historical dry-run limits and enables direct live dispatches, credential hydration, and browser automation to post, comment, and edit.

### Platform Dispatches Mapping

| Platform | Tier | Integration Method | Post Method | Comment / Interaction | Edit Method |
|---|---|---|---|---|---|
| **Discord** | Tier 1 | Webhooks & Bot API | Direct payload post | Webhook-driven replies | N/A |
| **Telegram** | Tier 1 | Bot API | `sendMessage` endpoint | Channel updates | Telegram Bot API |
| **Facebook Page** | Tier 1 | Meta Graph API | Direct page post | API comment dispatch | API post edit |
| **Threads** | Tier 1 | Threads API | Container publishing | API reply dispatch | Unsupported |
| **Instagram** | Tier 1 | Business Graph API | Media container publishing | API comment dispatch | Unsupported |
| **Substack** | Tier 2 | Playwright CDP | Direct page composition | CDP-assisted comments | CDP-assisted edit |
| **X (Twitter)** | Tier 2 | Playwright CDP | Timeline page navigation | CDP-assisted replies | CDP-assisted edit |
| **LinkedIn** | Tier 2 | Playwright CDP | Profile update page | CDP-assisted comments | CDP-assisted edit |

---

## 2. CDP Browser Automation (Playwright) Mitigation Playbook

Social platforms that do not provide free API endpoints (Substack, X, LinkedIn) are integrated via Playwright browser sessions utilizing the operator's existing profile directory (e.g. Edge profile). 

Because these platforms change their frontend layouts and CSS class names frequently, we must apply **defensive design principles** to prevent dispatches from breaking.

### Common Failure Modes & Solutions

#### A. Selector Conflict (Clicking the wrong element)
* **Problem**: In a direct post page, the button to open/close comments and the blue button to submit a comment might both have the text "Comment". A loose page-wide selector like `button:has-text('Comment')` will match the toggle button first, collapsing the input box instead of submitting the draft.
* **Mitigation**: **Strict Container Scoping**. Never search page-wide for common action words. First, locate the parent form or container (e.g., `form.comments-comment-box__form` or `.comments-comment-box`) and scope child locators inside it:
  ```python
  submit_btn = post_card.locator("form.comments-comment-box__form button:has-text('Comment')").first
  ```

#### B. Text-Box Focus Failures
* **Problem**: Typing commands fail because the wrong text editor (e.g., search box or "Start a post" box) has focus, or because the rich-text editor (e.g., Quill `ql-editor`) is not activated.
* **Mitigation**: Focus explicitly on rich-text attributes before using page keyboard inputs:
  ```python
  editor = container.locator("div.ql-editor, [role='textbox']").first
  editor.focus()
  page.keyboard.type(message)
  ```

#### C. Feed Polling Brittleness
* **Problem**: After posting, the adapter navigates to a profile's feed and reloads the page repeatedly, waiting for the new post to appear in order to copy its URL or ID. Feed algorithms and page caching make feed polling highly unreliable.
* **Mitigation**: **Direct Navigation & Dynamic URNs**. If the target post has a known URN (e.g. `urn:li:activity:7479815873415815169`), navigate directly to the update URL (`https://www.linkedin.com/feed/update/<URN>/`). For X, extract the status ID dynamically from the URL bar immediately after submitting the tweet, bypassing timeline polling.

#### D. Cookie Consent & Modal Obstructions
* **Problem**: Popups or cookie consent modal banners block elements from view, throwing "Element click intercepted" exceptions.
* **Mitigation**: Include preflight consent clicks in the adapter initialization:
  ```python
  accept_btn = page.locator("button:has-text('Accept'), button[id*='cookie']").first
  if accept_btn.is_visible():
      accept_btn.click()
  ```

#### E. DOM Drift Diagnosability
* **Problem**: A script fails silently or returns success because a selector exists but is hidden or enabled-state checks are bypassed.
* **Mitigation**: **Step-by-step Visual Tracing**. Take screenshots before and after every major click/type transition. Save them to a debug directory (e.g. `scratch/`) with sequential names (`step1_navigated.png`, `step2_typed.png`). If an assertion fails, the visual log reveals the exact state of the browser.

---

## 3. Playbook for Operator UI-Drift Recovery

When a platform updates its UI and breaks an adapter:
1. **Run Visual Debug Inspection**: Run the smoke test and inspect the captured screenshots in `scratch/`. Locate the step where the UI drifted.
2. **Extract DOM Structure**: Run a short script to write the HTML layout of the target container to a local text file:
   ```python
   html_content = page.locator(".target-container").evaluate("el => el.outerHTML")
   Path("scratch/dom_dump.html").write_text(html_content, encoding="utf-8")
   ```
3. **Update Fallback Chains**: Update the selector chain in the adapter. Always place specific class names first, and text-based / ARIA-attribute selectors as final fallbacks.
4. **Local Smoke Verification**: Run a focused script to verify the fix locally (e.g. `python scratch/test_linkedin_direct_comment.py`) before pushing code to `master`.
