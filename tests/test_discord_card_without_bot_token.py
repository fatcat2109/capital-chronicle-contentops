"""Ops Product, 10 Nov 2026: a local refusal (no Discord bot token for a thread) must not darken Discord for the ET day."""
import types


class _Conn:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, *args):
        return types.SimpleNamespace(fetchone=lambda: None)


class _Store:
    def __init__(self):
        self.incidents = []

    def get_read_only_connection(self):
        return _Conn()

    def register_incident(self, **kwargs):
        self.incidents.append(kwargs)


def _coordinator():
    return types.SimpleNamespace(store=_Store(),
                                 _destination_failure_key=lambda destination, instant=None: ("day-key", "2026-11-10"))


def test_local_bot_token_refusal_does_not_trip_the_day_circuit():
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
    fake = _coordinator()
    Coordinator._record_destination_day_failure(fake, {"work_item_id": "w"}, "discord",
        {"safe_error_classification": "DISCORD_CALL_THREAD_BOT_TOKEN_UNAVAILABLE", "status": "DEFINITE_NO_WRITE"})
    assert fake.store.incidents == []


def test_a_platform_failure_still_trips_the_day_circuit():
    from live_contentops.publication_coordinator_v1 import DurablePublicationCoordinator as Coordinator
    fake = _coordinator()
    Coordinator._record_destination_day_failure(fake, {"work_item_id": "w"}, "discord",
        {"safe_error_classification": "HTTPError", "status": "DEFINITE_NO_WRITE"})
    assert [i["incident_id"] for i in fake.store.incidents] == ["day-key"]
