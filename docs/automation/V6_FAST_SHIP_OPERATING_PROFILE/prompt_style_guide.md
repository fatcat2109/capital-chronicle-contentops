# V6 Prompt Style Guide

This style guide defines the prompt structure for future ContentOps V6 tasks, eliminating repeated disclaimers and focusing on clean, clear execution instructions.

## 1. Line One Task Label
Every task prompt must begin with the active task label on line one, formatted as:
`TASK_CONTENTOPS_V6_[TASK_NAME]_HEAVY_BATCH_V0`

## 2. Standard Prompt Architecture
Every task prompt must include:
1. **Header Metadata**: Repo path, branch, and starting HEAD SHA.
2. **Objective**: A clear description of the batch objective.
3. **Target Files**: Categorized list of files to read, build, and update.
4. **Output Contract**: Expected properties, schemas, and directory formats.
5. **Validation & Verification**: The exact test commands to execute.
6. **Git Instructions**: The specific commit message and push instructions.

## 3. Concise Safety Invariant
Instead of repeating long, ceremonial blocks prohibiting env files, network calls, browser tools, or provider APIs, tasks must use a single, concise safety invariant line:
> **Safety Invariant**: Governance policies are determined by the V6 Fast Ship Operating Profile. Never print or commit raw secrets.

## 4. Omitted Ceremony
Do not repeat long lists of forbidden activities (e.g., "no env", "no provider", "no browser", "no network", "local-only") unless the task is explicitly a security, credentials, or audit-specific task.
