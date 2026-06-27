# V6 Dynamic Pointer Policy

This policy governs task pointers and handoffs inside the ContentOps V6 workflow. It prevents static files from hardcoding stale task sequences or HEAD states that get updated dynamically during parallel or fast-ship executions.

## 1. Ephemeral Task Pointers
* Files like `next_task_pointer.md` or `new_chat_continuation.md` are useful starting points but are **intentionally ephemeral**.
* Any pointer file may be stale immediately after a task is completed, committed, and pushed.
* Project Sources must avoid claiming any permanent next task as absolute truth.

## 2. Recommended Phrasing
All pointer references in files and generated logs must use soft recommendation language:
* **Allowed**: *"Recommended next task at time of bundle generation..."*
* **Allowed**: *"Recommended next action at time of execution..."*
* **Banned**: *"Authoritative next task"* or *"Next task requirement"*

## 3. Remote Verification Rules
* **GitHub Audit First**: ChatGPT/Antigravity must verify the actual remote HEAD and the latest repository commit logs via GitHub before accepting worker evidence or issuing the next task.
* **HEAD Verification Invariant**: Every Antigravity task prompt must dynamically declare its starting HEAD from fresh remote verification, not from outdated static text files in Project Sources.
* **Resolution of Pointer Conflicts**: If a static pointer file conflicts with remote GitHub history or a newer verified local evidence packet, the **GitHub/audited evidence wins**.
