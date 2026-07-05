"""Unit tests for localized cron scheduler and outbox timing reconciliation."""
from __future__ import annotations

import datetime
import os
import tempfile
import pytest

from live_contentops.scheduler_v6 import CronExpression, OutboxScheduler


def test_cron_expression_parsing_and_matching():
    # 1. Match all wildcard
    cron_all = CronExpression("* * * * *")
    dt = datetime.datetime(2026, 7, 5, 12, 0, tzinfo=datetime.timezone.utc)
    assert cron_all.matches(dt)

    # 2. Match step value
    cron_step = CronExpression("*/15 * * * *")
    assert cron_step.matches(dt)  # 12:00 matches % 15 == 0
    dt_14 = datetime.datetime(2026, 7, 5, 12, 14, tzinfo=datetime.timezone.utc)
    assert not cron_step.matches(dt_14)
    dt_30 = datetime.datetime(2026, 7, 5, 12, 30, tzinfo=datetime.timezone.utc)
    assert cron_step.matches(dt_30)

    # 3. Match range value
    cron_range = CronExpression("1-5 * * * *")
    assert cron_range.matches(datetime.datetime(2026, 7, 5, 12, 3, tzinfo=datetime.timezone.utc))
    assert not cron_range.matches(datetime.datetime(2026, 7, 5, 12, 6, tzinfo=datetime.timezone.utc))

    # 4. Match list value
    cron_list = CronExpression("0,30 9 * * *")
    assert cron_list.matches(datetime.datetime(2026, 7, 5, 9, 30, tzinfo=datetime.timezone.utc))
    assert not cron_list.matches(datetime.datetime(2026, 7, 5, 9, 15, tzinfo=datetime.timezone.utc))

    # 5. Match day of week (Monday-Friday: 1-5)
    cron_wday = CronExpression("* * * * 1-5")
    # July 5, 2026 is Sunday (weekday=6 in python, cron wday=0)
    sun = datetime.datetime(2026, 7, 5, 12, 0, tzinfo=datetime.timezone.utc)
    assert not cron_wday.matches(sun)
    # July 6, 2026 is Monday (weekday=0 in python, cron wday=1)
    mon = datetime.datetime(2026, 7, 6, 12, 0, tzinfo=datetime.timezone.utc)
    assert cron_wday.matches(mon)


def test_cron_expression_next_execution():
    cron = CronExpression("*/15 9 * * *")
    start = datetime.datetime(2026, 7, 5, 8, 0, tzinfo=datetime.timezone.utc)
    next_exec = cron.next_execution(start)
    # Should find 9:00 AM on same day
    assert next_exec == datetime.datetime(2026, 7, 5, 9, 0, tzinfo=datetime.timezone.utc)

    start_past = datetime.datetime(2026, 7, 5, 9, 30, tzinfo=datetime.timezone.utc)
    next_exec_past = cron.next_execution(start_past)
    # Should find 9:45 AM
    assert next_exec_past == datetime.datetime(2026, 7, 5, 9, 45, tzinfo=datetime.timezone.utc)


def test_outbox_scheduler_registry_and_reconciliation():
    with tempfile.TemporaryDirectory() as tmpdir:
        reg_file = os.path.join(tmpdir, "scheduled_outbox.json")
        sched = OutboxScheduler(reg_file)

        # 1. Initially empty
        assert len(sched.load_entries()) == 0

        # 2. Add entry (unapproved)
        start_time = datetime.datetime(2026, 7, 5, 8, 0, tzinfo=datetime.timezone.utc)
        entry1 = sched.add_entry(
            platform_id="facebook_page",
            action="post",
            payload={"message": "Hello scheduled!"},
            cron_expression="0 9 * * *",
            approved=False,
            start_time=start_time
        )
        assert entry1.status == "pending"
        assert entry1.approved is False
        assert entry1.next_execution_time == "2026-07-05T09:00:00+00:00"

        # 3. Add approved entry
        entry2 = sched.add_entry(
            platform_id="instagram",
            action="post",
            payload={"caption": "Vibe check"},
            cron_expression="*/30 * * * *",
            approved=True,
            start_time=start_time
        )
        assert entry2.status == "pending"
        assert entry2.approved is True
        assert entry2.next_execution_time == "2026-07-05T08:30:00+00:00"

        # 4. Tick reconciliation before execution time
        tick_time_early = datetime.datetime(2026, 7, 5, 8, 15, tzinfo=datetime.timezone.utc)
        res_early = sched.reconcile_outbox_timing(current_time=tick_time_early, dry_run=True)
        assert res_early["dispatched"] == 0
        assert res_early["skipped"] == 2

        # 5. Tick reconciliation past execution time of approved entry2 (8:30)
        tick_time_due = datetime.datetime(2026, 7, 5, 8, 35, tzinfo=datetime.timezone.utc)
        res_due = sched.reconcile_outbox_timing(current_time=tick_time_due, dry_run=True)
        assert res_due["dispatched"] == 1
        assert res_due["skipped"] == 1  # entry1 skipped as unapproved

        # Reload entries and check states
        entries = sched.load_entries()
        e1 = next(e for e in entries if e.entry_id == entry1.entry_id)
        e2 = next(e for e in entries if e.entry_id == entry2.entry_id)

        assert e1.status == "pending"
        assert e2.status == "dispatched"
        assert e2.last_dispatch_time == tick_time_due.isoformat()
        # Next run should be updated to 9:00
        assert e2.next_execution_time == "2026-07-05T09:00:00+00:00"
        assert len(e2.history) == 1
        assert e2.history[0]["result"]["status"] == "DRY_RUN_PASS"
