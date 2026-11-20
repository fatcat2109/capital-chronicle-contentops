"""CC-732 export-to-outbox clocks in the existing minute run log."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json

TARGET_SECONDS = 120
ALARM_SECONDS = 600
PHASE = "PLAN_EXPORT_QUEUE"
FIELD = "plan_export_queue"
DECISION = "CC-732"


def _time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _iso(value):
    return value.isoformat().replace("+00:00", "Z")


def _identity(row):
    return row.get("source_transition_id") or row["key"]


def _ticks(path, *, reverse=False):
    if not path.is_file():
        return
    with path.open("rb") as handle:
        lines = _reverse_lines(handle) if reverse else handle
        for line in lines:
            if b'"plan_export_queue"' not in line:
                continue
            try:
                tick = json.loads(line)
                if tick.get("phase") == PHASE and isinstance(tick.get(FIELD), dict):
                    yield tick
            except (ValueError, TypeError, AttributeError):
                continue


def _reverse_lines(handle):
    offset = handle.seek(0, 2)
    prefix = b""
    while offset:
        size = min(offset, 65536)
        offset -= size
        handle.seek(offset)
        prefix, *lines = (handle.read(size) + prefix).split(b"\n")
        yield from reversed(lines)
    yield prefix


def _latest(folder, now):
    for day in (now, now - timedelta(days=1), now - timedelta(days=2)):
        path = folder / f"runs-{day:%Y%m%d}.jsonl"
        if tick := next(_ticks(path, reverse=True), None):
            return tick[FIELD]
    return {}


def queue_event(observation, checked_at, *, queued_at=None):
    """Compare like clocks. The transition's event time is provenance."""
    elapsed = ((_time(queued_at) if queued_at else checked_at)
               - _time(observation["first_seen_at_utc"])).total_seconds()
    alarm = elapsed > ALARM_SECONDS and not observation.get("alarm_at_utc")
    outcome = {
        **observation, "queued_at_utc": queued_at,
        "gap_seconds": round(elapsed, 3), "target_missed": elapsed > TARGET_SECONDS,
        "alarm": alarm,
    }
    if outcome.get("first_cause") is None and (not queued_at or alarm):
        outcome["first_cause"] = "QUEUE_REGISTRATION_DELAY" if queued_at else "PLAN_QUEUE_NOT_REGISTERED"
    if alarm:
        outcome["alarm_at_utc"] = _iso(checked_at)
    return outcome


class PlanQueueClock:
    def __init__(self, store, folder, write, *, clock=None):
        self.store = store
        self.folder = folder
        self.write = write
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.error = None
        try:
            previous = _latest(folder, self.clock())
        except OSError as exc:
            self.error = type(exc).__name__
            previous = {}
        self.seen = set(previous.get("seen_keys", ()))
        self.initial = not previous.get("observed")
        self.pending = previous.get("pending", {})
        self.current = self.seen
        self.read_export = False
        self.refusals = {}
        if previous.get("stage") == "OBSERVED":
            for row in self.pending.values():
                if not row.get("first_cause") and not store.get_outbox_message(row["key"]):
                    row["first_cause"] = "PREVIOUS_QUEUE_COMPLETION_NOT_RECORDED"

    def observe(self, rows, export_generated_at_utc):
        at = self.clock()
        self.read_export = True
        current = {_identity(row): row for row in rows}
        new_keys = current.keys() - self.seen - self.pending.keys()
        self.current = current.keys()
        self.seen.update(self.current)
        new = []
        for identity in sorted(new_keys):
            row = current[identity]
            if self.initial and _time(row["at_utc"]) < at - timedelta(hours=24):
                continue  # Baseline the old export history on the first instrumented run.
            key = row["key"]
            if self.store.get_outbox_message(key):
                continue
            observation = {"key": key, "plan_id": row["plan_id"], "symbol": row["symbol"],
                           "state": row.get("source_state") or row["to"],
                           "source_transition_id": row.get("source_transition_id"),
                           "source_event_at_utc": row["at_utc"],
                           "first_seen_at_utc": _iso(at), "first_export_at_utc": export_generated_at_utc}
            self.pending[identity] = observation
            new.append(observation)
        self.initial = False
        due = self._reconcile({}, at, only_due=True)
        if new or due:
            self._record(at, "OBSERVED", [*new, *due])

    def finish(self, result):
        at = self.clock()
        events = self._reconcile(result, at)
        if not self.initial or events:
            self._record(at, "COMPLETE", events)

    def refuse(self, row, cause, *, replacement_key=None):
        identity = _identity(row)
        if identity in self.pending:
            self.refusals.setdefault(identity, {"cause": cause, "replacement_key": replacement_key})

    def _reconcile(self, result, at, *, only_due=False):
        skipped = {row["key"]: row for row in result.get("not_posted", [])}
        events = []
        for identity, row in list(self.pending.items()):
            if only_due and (row.get("alarm_at_utc")
                             or (at - _time(row["first_seen_at_utc"])).total_seconds() <= ALARM_SECONDS):
                continue
            key = row["key"]
            refusal = self.refusals.get(identity) or skipped.get(key, {})
            message = self.store.get_outbox_message(key)
            if not message and refusal.get("replacement_key"):
                message = self.store.get_outbox_message(refusal["replacement_key"])
                if message:
                    row["queued_key"] = message["message_id"]
            queued_at = message["created_at"] if message else None
            if not row.get("first_cause"):
                cause = refusal.get("cause") or (result.get("cause") if not queued_at else None)
                if cause is None and self.read_export and identity not in self.current:
                    cause = "ROW_ABSENT_FROM_EXPORT"
                if cause:
                    row["first_cause"] = cause
            event = queue_event(row, at, queued_at=queued_at)
            if queued_at or event["alarm"] or not row.get("alarm_at_utc"):
                events.append(event)
            if queued_at or (event.get("alarm_at_utc") and self.read_export and identity not in self.current):
                del self.pending[identity]
            elif event["alarm"]:
                row.update(alarm_at_utc=event["alarm_at_utc"], first_cause=event["first_cause"])
        return events

    def _record(self, at, stage, events):
        try:
            self.write({"phase": PHASE, "status": stage, FIELD: {
                "stage": stage, "observed": not self.initial, "seen_keys": sorted(self.seen),
                "pending": self.pending, "events": events,
            }}, self.folder, now=at)
        except OSError as exc:
            self.error = type(exc).__name__


def read_queue_events(folder, start, end):
    """Read the report window once. Identity and alarm clock deduplicate overlapping ticks."""
    events = {}
    day = start.date()
    while day <= end.date():
        for tick in _ticks(folder / f"runs-{day:%Y%m%d}.jsonl"):
            if not start < _time(tick["at_utc"]) <= end:
                continue
            for event in tick[FIELD]["events"]:
                if event.get("alarm") or event.get("queued_at_utc"):
                    key = (_identity(event), bool(event["alarm"]))
                    events.setdefault(key, event)
        day += timedelta(days=1)
    return list(events.values())
