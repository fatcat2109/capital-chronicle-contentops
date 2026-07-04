# LIVE PILOT OPERATOR PREREQUISITE PACKET

**IMPORTANT: Do not paste any secret values into this document, into git, or into the chat window. No network/API execution is occurring in this packet.**

## Overview
This document specifies what the operator (Jim) must explicitly prepare *outside of this repository* before any future live pilot GO task can be executed. 

## 1. Chosen Pilot Platform
- **Recommended First Platform:** Telegram Private/Staging Channel.
- **Requirement:** Operator must verify the exact platform intended for the V1 pilot.

## 2. Staging Target Capture
- **Requirement:** Operator must create the private staging sandbox (e.g., a Telegram channel) and capture its numeric ID. 
- **Secret Storage:** Store the ID in the offline secret manager. Do NOT commit it.

## 3. Secret Manager Approach
- **Requirement:** Operator must choose an offline secret manager or local secure injection approach (e.g., heavily gitignored explicit `.env.secrets` loaded only at runtime, or a key vault).
- **Rule:** This repository will never track secrets.

## 4. Provider and Platform Credentials
- **Requirement:** Operator must acquire the necessary LLM provider API keys and Platform OAuth/Bot tokens.
- **Decision:** Do this later, not now. Keep them out of `cc-live-contentops`.

## 5. Operator Roles & Accountability
- **Manual Approval Role:** Operator must manually type `publish_now` for every single pilot post.
- **Emergency Stop Role:** Operator must know how to trigger the kill switch.
- **Rollback/Correction:** Operator must define the manual procedure to delete or retract a bad post from the platform natively.

## 6. Content Scope
- **Cadence:** Maximum 1 post per day during the pilot.
- **Allowed:** Summaries of known safe Local Source Bundles.
- **Forbidden:** No financial advice, market calls, position sizing, guaranteed predictions, partisan persuasion, or autonomous replies.

## 7. Pilot Duration and Success/Failure
- **Duration:** 1 week minimum pilot.
- **Success Criteria:** 100% of posts manually approved without violating the allowed scope, zero secrets leaked, zero hallucinated claims, zero unauthorized API calls.
- **Stop Conditions:** A secret leak, a rate limit ban, an unauthorized publish, or an unapproved topic generation immediately halts the pilot.

## Required Explicit GO Language
When all prerequisites are met offline, a future task will require the explicit phrase: 
`"I, the operator, confirm all prerequisites are met offline and authorize the staging dry-run to proceed."`
