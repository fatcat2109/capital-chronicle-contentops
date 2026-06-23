# Operator Browser Lab Runbook

Task: `TASK_CONTENTOPS_OPERATOR_BROWSER_LAB_AND_SOCIAL_CREDENTIAL_SETUP_WORKBENCH_V0`

## Purpose

Browser Lab gives operator persistent Chrome/CDP profile for manual social account login, official developer portal access, and credential retrieval. It is not runtime posting authority.

## Defaults

- Profile root: `A:\Capital Chronicle\operator-browser-profiles\contentops-social-main`
- Profile override env key: `CONTENTOPS_OPERATOR_BROWSER_PROFILE_ROOT`
- CDP port: `9222`
- CDP override env key: `CONTENTOPS_OPERATOR_BROWSER_CDP_PORT`

Default profile is outside repo. Repo-local override is sensitive and must remain gitignored.

## Commands

```powershell
python -m live_contentops.operator_browser_lab open --platform telegram
python -m live_contentops.operator_browser_lab open --platform x
python -m live_contentops.operator_browser_lab open --platform linkedin
python -m live_contentops.operator_browser_lab open --platform meta
python -m live_contentops.operator_browser_lab open --platform tiktok
python -m live_contentops.operator_browser_lab open --platform youtube
python -m live_contentops.operator_browser_lab open --platform substack
python -m live_contentops.operator_browser_lab open --platform all-docs
```

Use `--dry-run` for command validation without opening browser.

## Allowed

- operator manual login
- official portal browsing
- manual API/OAuth credential retrieval
- local storage in `.env.local` or approved local secret files

## Forbidden

- no posting, publishing, upload, schedule, reply, or DM
- no Telegram `sendMessage` or `sendPhoto`
- no X tweet creation
- no LinkedIn post creation
- no Meta, Instagram, Threads post
- no TikTok upload or publish
- no YouTube upload
- no Substack publish
- no provider LLM API call
- no scraping
- no cookie dump
- no `localStorage` dump
- no `sessionStorage` dump
- no DOM dump
- no screenshot containing token/key/secret
- no OpenClaw runtime integration

## Browser-Assisted Publish Policy

Browser Lab may help with login, API key retrieval, and manual publish setup only. It is not runtime authority.

Future browser-assisted publish requires:

- approved payload hash
- destination/account pre-click compare
- Jim present
- no cookie/session dump
- stop on UI uncertainty
- no generic publish-all
- no autonomous replies/DMs

## OAuth Callback Scaffold

Suggested callback root: `http://127.0.0.1:8765/oauth/{platform}/callback`

- X: `http://127.0.0.1:8765/oauth/x/callback`
- LinkedIn: `http://127.0.0.1:8765/oauth/linkedin/callback`
- Meta: `http://127.0.0.1:8765/oauth/meta/callback`
- TikTok: `http://127.0.0.1:8765/oauth/tiktok/callback`
- YouTube: `http://127.0.0.1:8765/oauth/youtube/callback`

Scaffold must not log authorization codes or tokens. It must require operator confirmation before writing token file and must never commit token files.
