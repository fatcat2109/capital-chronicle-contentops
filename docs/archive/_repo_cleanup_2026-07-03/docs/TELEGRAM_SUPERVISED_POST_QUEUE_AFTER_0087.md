# Telegram Supervised Post Queue (After 0087)

## Purpose
This document outlines the local deterministic queue framework designed to structure future Telegram post workflows safely. It implements strict idempotency, duplicate detection, and robust safety blockades preventing any live actions.

## Requirements

* **Idempotency**: All items require a `content_hash` (SHA-256) and an `idempotency_key`. 
* **Duplicate Detection**: Duplicates across a queue run are identified by their `idempotency_key`. Duplicates MUST be marked with `queue_status: "DUPLICATE"` and must specify the original `duplicate_of_queue_item_id`.
* **Safety Enforcements**: 
  * No real channel IDs committed.
  * No public targets allowed.
  * All `live`, `network`, `env_read`, `scheduler`, and `autonomous` flags must be False.
  * Any payload containing forbidden financial execution language (e.g. "buy", "sell") is immediately blocked.
