import hashlib
import json

FORBIDDEN_TERMS = [
    "buy", "sell", "hold", "long", "short", "target", "entry", "exit",
    "signal", "model says", "broker", "order", "execution", "guaranteed"
]

def generate_content_hash(text: str) -> str:
    """Generate deterministic SHA-256 hash for content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def generate_idempotency_key(platform: str, content_hash: str) -> str:
    """Generate deterministic idempotency key."""
    return f"{platform}-{content_hash}"

def validate_queue_item(item: dict) -> dict:
    """Validates a single queue item. Returns dictionary with 'status' and 'reasons'."""
    reasons = []
    status = "VALID"

    # Check safety flags
    if item.get("live_execution_allowed_now") or item.get("network_accessed") or item.get("telegram_api_called") or item.get("live_post_sent"):
        reasons.append("Live/network capability flags must be false")
    if item.get("env_read_performed") or item.get("credential_accessed_by_repo"):
        reasons.append("Env/credential access flags must be false")
    if item.get("scheduling_enabled") or item.get("replies_or_dms_enabled") or item.get("scraping_enabled") or item.get("metrics_fetched"):
        reasons.append("Autonomous/scheduler capability flags must be false")

    # Check targets
    if item.get("public_channel_target") or item.get("public_postable"):
        reasons.append("Public targets and public postable content are forbidden")
    if item.get("real_channel_id_committed") or item.get("target_channel_id_present"):
        reasons.append("Real channel IDs cannot be committed")
    if item.get("publish_ready"):
        reasons.append("publish_ready must be false")

    # Check required checks
    if not all([item.get("approval_required"), item.get("kill_switch_required"), item.get("redaction_required"), item.get("manual_operator_final_check_required")]):
        reasons.append("All manual supervision checks (approval, kill-switch, redaction, final check) are required")

    # Check forbidden language
    text = item.get("post_text", "").lower()
    for term in FORBIDDEN_TERMS:
        if f" {term} " in f" {text} " or text.startswith(f"{term} ") or text.endswith(f" {term}"):
            reasons.append(f"Forbidden financial/signal language found: {term}")

    if reasons:
        status = "BLOCKED"

    return {"status": status, "reasons": reasons}

def process_queue(queue_data: dict) -> dict:
    """Process a queue, mark duplicates, and validate all items."""
    seen_hashes = {}
    processed_items = []
    queue_blocked = False
    all_reasons = []

    for item in queue_data.get("items", []):
        text = item.get("post_text", "")
        chash = generate_content_hash(text)
        ikey = generate_idempotency_key(item.get("platform_id", "unknown"), chash)

        # Ensure hashes match if provided
        if item.get("content_hash") and item["content_hash"] != chash:
            all_reasons.append(f"Item {item.get('queue_item_id')} has invalid content_hash")
            queue_blocked = True

        # Duplicate detection
        if ikey in seen_hashes:
            if item.get("queue_status") != "DUPLICATE":
                all_reasons.append(f"Item {item.get('queue_item_id')} is an unmarked duplicate")
                queue_blocked = True
            elif item.get("duplicate_of_queue_item_id") != seen_hashes[ikey]:
                all_reasons.append(f"Item {item.get('queue_item_id')} references wrong original ID")
                queue_blocked = True
        else:
            seen_hashes[ikey] = item.get("queue_item_id")
            if item.get("queue_status") == "DUPLICATE":
                all_reasons.append(f"Item {item.get('queue_item_id')} marked duplicate but is first occurrence")
                queue_blocked = True

        validation = validate_queue_item(item)
        if validation["status"] == "BLOCKED":
            queue_blocked = True
            all_reasons.extend([f"Item {item.get('queue_item_id')}: {r}" for r in validation["reasons"]])

        processed_items.append(item)

    return {
        "queue_status": "BLOCKED" if queue_blocked else "VALID",
        "items_processed": len(processed_items),
        "reasons": all_reasons
    }
