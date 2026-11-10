"""Ops Product, 10 Nov 2026: one Discord card without a bot token must not darken Discord for the ET day."""
import types


def test_card_asks_for_a_discord_thread_only_with_a_bot_token(monkeypatch):
    from live_contentops import plan_call_cards_v1 as cards, secret_store_v1
    monkeypatch.setattr(secret_store_v1, "read_secret", lambda name: None)
    assert cards._discord_threads_available() is False
    monkeypatch.setattr(secret_store_v1, "read_secret", lambda name: "token" if name == "DISCORD_BOT_TOKEN" else None)
    assert cards._discord_threads_available() is True


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
