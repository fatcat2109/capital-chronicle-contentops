"""V6 Localized Cron Scheduler and Outbox Timing Reconciliation.

Provides cron parsing and scheduled dispatch logic for Fast Ship Mode.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .live_telemetry_v6 import classify_and_record_dispatch

TASK_LABEL = "TASK_CONTENTOPS_V6_SCHEDULER_AND_CRON_RECONCILIATION_V0"
SCHEMA_VERSION = "6.0.0"
DEFAULT_REGISTRY_PATH = Path("docs/automation/V6_SCHEDULER/scheduled_outbox_entries_v6.json")


class CronExpression:
    def __init__(self, expr: str):
        self.expr = expr.strip()
        fields = self.expr.split()
        if len(fields) != 5:
            raise ValueError(f"Invalid cron expression: '{expr}'. Must have exactly 5 fields.")
        
        self.minute_field = fields[0]
        self.hour_field = fields[1]
        self.day_of_month_field = fields[2]
        self.month_field = fields[3]
        self.day_of_week_field = fields[4]

    def _parse_field(self, field_str: str, min_val: int, max_val: int) -> set[int]:
        if field_str == "*":
            return set(range(min_val, max_val + 1))
        
        allowed_vals = set()
        parts = field_str.split(",")
        for part in parts:
            if part.startswith("*/"):
                step = int(part[2:])
                allowed_vals.update(v for v in range(min_val, max_val + 1) if (v - min_val) % step == 0)
            elif "/" in part:
                subparts = part.split("/")
                step = int(subparts[1])
                range_part = subparts[0]
                if range_part == "*":
                    allowed_vals.update(v for v in range(min_val, max_val + 1) if (v - min_val) % step == 0)
                else:
                    r_start, r_end = map(int, range_part.split("-"))
                    allowed_vals.update(v for v in range(r_start, r_end + 1) if (v - r_start) % step == 0)
            elif "-" in part:
                r_start, r_end = map(int, part.split("-"))
                allowed_vals.update(range(r_start, r_end + 1))
            else:
                allowed_vals.add(int(part))
        return allowed_vals

    def matches(self, dt: datetime.datetime) -> bool:
        py_wday = dt.weekday()  # 0=Monday, 6=Sunday
        cron_wday = (py_wday + 1) % 7  # 0=Sunday, 1=Monday, ..., 6=Saturday
        
        try:
            minutes = self._parse_field(self.minute_field, 0, 59)
            hours = self._parse_field(self.hour_field, 0, 23)
            days = self._parse_field(self.day_of_month_field, 1, 31)
            months = self._parse_field(self.month_field, 1, 12)
            
            wdays_raw = self._parse_field(self.day_of_week_field, 0, 7)
            wdays = set(w % 7 for w in wdays_raw)

            dom_restricted = self.day_of_month_field != "*"
            dow_restricted = self.day_of_week_field != "*"
            
            if dom_restricted and dow_restricted:
                dom_matches = dt.day in days
                dow_matches = cron_wday in wdays
                day_matches = dom_matches or dow_matches
            else:
                day_matches = (dt.day in days) if dom_restricted else True
                day_matches = day_matches and ((cron_wday in wdays) if dow_restricted else True)

            return (
                dt.minute in minutes and
                dt.hour in hours and
                day_matches and
                dt.month in months
            )
        except Exception:
            return False

    def next_execution(self, start_dt: datetime.datetime) -> datetime.datetime:
        current = start_dt.replace(second=0, microsecond=0)
        # Check start time itself first, but standard cron usually checks subsequent times.
        # Let's check minutes starting from start_dt + 1 minute to avoid double triggers.
        current += datetime.timedelta(minutes=1)
        max_look_ahead = current + datetime.timedelta(days=366)
        while current < max_look_ahead:
            if self.matches(current):
                return current
            current += datetime.timedelta(minutes=1)
        raise ValueError(f"Could not find next execution time for cron '{self.expr}' within 1 year.")


@dataclass
class ScheduledOutboxEntry:
    entry_id: str
    platform_id: str
    action: str
    payload: dict[str, Any]
    cron_expression: str
    approved: bool = False
    last_dispatch_time: str | None = None
    next_execution_time: str | None = None
    status: str = "pending"  # pending, dispatched, failed
    retry_count: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)


def dispatch_platform_action(
    platform_id: str,
    action: str,
    payload: dict[str, Any],
    dry_run: bool
) -> dict[str, Any]:
    """Helper to dispatch actions to platform adapters, or fallback to mock dispatch."""
    if platform_id == "substack":
        from .substack_browser_adapter_v6 import execute_substack_post, execute_substack_comment, execute_substack_edit
        if action == "post":
            return execute_substack_post(
                title=payload.get("title", ""),
                subtitle=payload.get("subtitle", ""),
                body_markdown=payload.get("body_markdown", payload.get("body", "")),
                dry_run=dry_run
            )
        elif action == "comment":
            return execute_substack_comment(
                post_url_or_slug=payload.get("post_url_or_slug", payload.get("url", "")),
                message=payload.get("message", payload.get("text", "")),
                dry_run=dry_run
            )
        elif action == "edit":
            return execute_substack_edit(
                post_id_or_url=payload.get("post_id_or_url", payload.get("post_id", "")),
                title=payload.get("title", ""),
                subtitle=payload.get("subtitle", ""),
                body_markdown=payload.get("body_markdown", payload.get("body", "")),
                dry_run=dry_run
            )
    elif platform_id == "x":
        from .x_browser_adapter_v6 import execute_x_post, execute_x_comment, execute_x_edit
        if action == "post":
            return execute_x_post(
                text=payload.get("text", payload.get("message", "")),
                image_url=payload.get("image_url"),
                dry_run=dry_run
            )
        elif action == "comment":
            return execute_x_comment(
                tweet_url_or_id=payload.get("tweet_url_or_id", payload.get("tweet_id", "")),
                text=payload.get("text", payload.get("message", "")),
                dry_run=dry_run
            )
        elif action == "edit":
            return execute_x_edit(
                tweet_url_or_id=payload.get("tweet_url_or_id", payload.get("tweet_id", "")),
                new_text=payload.get("new_text", payload.get("text", "")),
                dry_run=dry_run
            )
    elif platform_id == "discord":
        from .discord_live_adapter_v6 import execute_discord_post, execute_discord_comment, execute_discord_edit
        if action == "post":
            return execute_discord_post(
                message=payload.get("message", payload.get("text", "")),
                webhook_url=payload.get("webhook_url"),
                embeds=payload.get("embeds"),
                dry_run=dry_run
            )
        elif action == "comment":
            return execute_discord_comment(
                thread_id_or_url=payload.get("thread_id_or_url", payload.get("thread_id", "")),
                message=payload.get("message", payload.get("text", "")),
                webhook_url=payload.get("webhook_url"),
                dry_run=dry_run
            )
        elif action == "edit":
            return execute_discord_edit(
                message_id=payload.get("message_id", payload.get("id", "")),
                new_message=payload.get("new_message", payload.get("message", payload.get("text", ""))),
                webhook_url=payload.get("webhook_url"),
                dry_run=dry_run
            )
    elif platform_id == "telegram":
        from .telegram_live_adapter_v6 import execute_telegram_post, execute_telegram_comment, execute_telegram_edit
        if action == "post":
            return execute_telegram_post(
                message=payload.get("message", payload.get("text", "")),
                chat_id=payload.get("chat_id"),
                bot_token=payload.get("bot_token"),
                parse_mode=payload.get("parse_mode", "HTML"),
                dry_run=dry_run
            )
        elif action == "comment":
            return execute_telegram_comment(
                reply_to_message_id=payload.get("reply_to_message_id", payload.get("message_id", "")),
                message=payload.get("message", payload.get("text", "")),
                chat_id=payload.get("chat_id"),
                bot_token=payload.get("bot_token"),
                parse_mode=payload.get("parse_mode", "HTML"),
                dry_run=dry_run
            )
        elif action == "edit":
            return execute_telegram_edit(
                message_id=payload.get("message_id", payload.get("id", "")),
                new_message=payload.get("new_message", payload.get("message", payload.get("text", ""))),
                chat_id=payload.get("chat_id"),
                bot_token=payload.get("bot_token"),
                parse_mode=payload.get("parse_mode", "HTML"),
                dry_run=dry_run
            )
    elif platform_id == "facebook_page":
        from .facebook_page_adapter_v6 import execute_facebook_comment, execute_facebook_edit, execute_facebook_post
        if action == "post":
            return execute_facebook_post(
                page_id=payload.get("page_id"),
                access_token=payload.get("access_token"),
                message=payload.get("message", payload.get("text", "")),
                link=payload.get("link"),
                dry_run=dry_run
            )
        elif action == "comment":
            return execute_facebook_comment(
                post_id=payload.get("post_id", payload.get("id", "")),
                access_token=payload.get("access_token"),
                message=payload.get("message", payload.get("text", "")),
                dry_run=dry_run
            )
        elif action == "edit":
            return execute_facebook_edit(
                post_id=payload.get("post_id", payload.get("id", "")),
                access_token=payload.get("access_token"),
                message=payload.get("new_message", payload.get("message", payload.get("text"))),
                link=payload.get("link"),
                dry_run=dry_run
            )
    elif platform_id in {"instagram", "instagram_business"}:
        from .instagram_adapter_v6 import execute_instagram_comment, execute_instagram_edit, execute_instagram_post
        if action == "post":
            return execute_instagram_post(
                ig_id=payload.get("ig_id", payload.get("instagram_business_account_id")),
                access_token=payload.get("access_token"),
                image_url=payload.get("image_url", "https://example.invalid/contentops-dry-run.jpg" if dry_run else ""),
                caption=payload.get("caption", payload.get("message", "")),
                dry_run=dry_run
            )
        elif action == "comment":
            return execute_instagram_comment(
                media_id=payload.get("media_id", payload.get("id", "")),
                access_token=payload.get("access_token"),
                message=payload.get("message", payload.get("text", "")),
                dry_run=dry_run
            )
        elif action == "edit":
            return execute_instagram_edit()
    elif platform_id == "threads":
        from .threads_adapter_v6 import execute_threads_edit, execute_threads_post
        if action in {"post", "comment", "reply"}:
            return execute_threads_post(
                threads_user_id=payload.get("threads_user_id"),
                access_token=payload.get("access_token"),
                text=payload.get("text", payload.get("message", "")),
                media_type=payload.get("media_type"),
                image_url=payload.get("image_url"),
                reply_to_id=payload.get("reply_to_id", payload.get("parent_id") if action in {"comment", "reply"} else None),
                dry_run=dry_run
            )
        elif action == "edit":
            return execute_threads_edit()
    
    # Fallback / Dry run mock dispatch for other platforms
    return {
        "status": "SUCCESS" if not dry_run else "DRY_RUN_PASS",
        "id": f"{platform_id}_mock_id_{hashlib.md5(str(payload).encode('utf-8')).hexdigest()[:8]}",
        "response": {"mocked": True}
    }


class OutboxScheduler:
    def __init__(self, registry_path: Path | str = DEFAULT_REGISTRY_PATH):
        self.registry_path = Path(registry_path)

    def load_entries(self) -> list[ScheduledOutboxEntry]:
        if not self.registry_path.exists():
            return []
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            entries = []
            for item in data.get("entries", []):
                entries.append(ScheduledOutboxEntry(
                    entry_id=item["entry_id"],
                    platform_id=item["platform_id"],
                    action=item["action"],
                    payload=item["payload"],
                    cron_expression=item["cron_expression"],
                    approved=item.get("approved", False),
                    last_dispatch_time=item.get("last_dispatch_time"),
                    next_execution_time=item.get("next_execution_time"),
                    status=item.get("status", "pending"),
                    retry_count=item.get("retry_count", 0),
                    history=item.get("history", [])
                ))
            return entries
        except Exception:
            return []

    def save_entries(self, entries: list[ScheduledOutboxEntry]) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "schema_version": SCHEMA_VERSION,
            "task_label": TASK_LABEL,
            "entries": [asdict(e) for e in entries]
        }
        # Atomic write
        temp_path = self.registry_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        if os.path.exists(self.registry_path):
            os.remove(self.registry_path)
        os.rename(temp_path, self.registry_path)

    def add_entry(
        self,
        platform_id: str,
        action: str,
        payload: dict[str, Any],
        cron_expression: str,
        approved: bool = False,
        start_time: datetime.datetime | None = None
    ) -> ScheduledOutboxEntry:
        if start_time is None:
            start_time = datetime.datetime.now(datetime.timezone.utc)
            
        cron = CronExpression(cron_expression)
        next_run = cron.next_execution(start_dt=start_time)
        
        digest = hashlib.md5(f"{platform_id}:{action}:{cron_expression}:{next_run.isoformat()}".encode("utf-8")).hexdigest()[:12]
        entry_id = f"sched_{platform_id}_{digest}"
        
        entry = ScheduledOutboxEntry(
            entry_id=entry_id,
            platform_id=platform_id,
            action=action,
            payload=payload,
            cron_expression=cron_expression,
            approved=approved,
            next_execution_time=next_run.isoformat(),
            status="pending"
        )
        
        entries = self.load_entries()
        # Prevent duplicates
        for existing in entries:
            if existing.entry_id == entry_id:
                return existing
                
        entries.append(entry)
        self.save_entries(entries)
        return entry

    def reconcile_outbox_timing(
        self,
        current_time: datetime.datetime | None = None,
        dry_run: bool = True
    ) -> dict[str, Any]:
        """Runs a tick check of the scheduler to dispatch any due entries."""
        if current_time is None:
            current_time = datetime.datetime.now(datetime.timezone.utc)
            
        entries = self.load_entries()
        dispatched_count = 0
        failed_count = 0
        skipped_count = 0
        
        for entry in entries:
            if entry.status in ["dispatched", "failed"] or not entry.approved:
                skipped_count += 1
                continue
                
            if not entry.next_execution_time:
                skipped_count += 1
                continue
                
            try:
                next_exec = datetime.datetime.fromisoformat(entry.next_execution_time)
            except Exception:
                skipped_count += 1
                continue
                
            # If current time is past or equal to next execution time
            if current_time >= next_exec:
                # Trigger dispatch!
                result = dispatch_platform_action(
                    platform_id=entry.platform_id,
                    action=entry.action,
                    payload=entry.payload,
                    dry_run=dry_run
                )
                
                # Check outcome status
                status = result.get("status")
                is_success = status in ["SUCCESS", "DRY_RUN_PASS"]
                
                # Record in entry history
                run_record = {
                    "timestamp": current_time.isoformat(),
                    "dry_run": dry_run,
                    "result": result
                }
                entry.history.append(run_record)
                
                if is_success:
                    entry.status = "dispatched"
                    entry.last_dispatch_time = current_time.isoformat()
                    dispatched_count += 1
                else:
                    entry.retry_count += 1
                    if entry.retry_count >= 3:
                        entry.status = "failed"
                    failed_count += 1
                    
                # Recompute next execution time from current run
                cron = CronExpression(entry.cron_expression)
                try:
                    next_run = cron.next_execution(start_dt=current_time)
                    entry.next_execution_time = next_run.isoformat()
                except Exception:
                    entry.next_execution_time = None
            else:
                skipped_count += 1
                
        self.save_entries(entries)
        
        return {
            "timestamp": current_time.isoformat(),
            "dry_run": dry_run,
            "dispatched": dispatched_count,
            "failed": failed_count,
            "skipped": skipped_count
        }
