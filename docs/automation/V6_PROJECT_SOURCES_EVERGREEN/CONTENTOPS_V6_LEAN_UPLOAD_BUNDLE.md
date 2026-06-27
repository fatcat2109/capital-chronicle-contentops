# V6 Lean Upload Bundle

This document provides operator instructions for uploading files to ChatGPT Project Sources. Keeping Project Sources lean (targeting 10–13 total files) prevents token exhaustion and context pollution.

## 1. What to Keep (Evergreen Authority)
* Always retain the strategic documents: the V6 Master Plan and the V6 25-Task Execution Plan. Do not delete them.
* Keep the execution posture documents (Fast Ship Operating Profile, Prompt Style Guide, Task Classification Matrix, Live/Env Scope Contract).
* Keep the evergreen files (Authority Index, Minimal Handoff, Dynamic Pointer Policy, Lean Upload Bundle, Retention Matrix).

## 2. What to Replace or Remove
* Replace generated handoff docs (e.g. current state summaries, new chat continuations) only when a Project Sources refresh task explicitly updates and regenerates them.
* Do not keep old implementation reports (such as `implementation_report.md` from previous tasks) in Project Sources.
* Do not keep old upload manifests or file lists after an upload is complete.
* Do not keep ingestion database maps, schemas, or recon notes in the upload bundle unless the next active task is explicitly an ingestion or artifact connector task.

## 3. Strict Safety Invariant
* **Never upload `.env` or configuration files containing secrets.**
* Never upload browser profiles, caches, cookies, local storage sessions, temporary terminal log outputs, or raw webhook/API credentials.
* Never upload screenshots or confirmation images containing visible auth headers, keys, or credentials.
