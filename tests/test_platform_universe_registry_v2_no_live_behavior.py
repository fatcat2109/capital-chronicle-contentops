from pathlib import Path
import re

from live_contentops import platform_universe_registry_v2 as registry
from live_contentops import primary_payload_classes_contract as payload_contract


def test_no_env_or_network_imports():
    for module_file in (registry.__file__, payload_contract.__file__):
        source = Path(module_file).read_text(encoding="utf-8")
        forbidden = (
            "getenv",
            "environ",
            "dotenv",
            "requests",
            "urllib",
            "socket",
            "http.client",
            "subprocess",
            "playwright",
            "selenium",
            "webdriver",
        )
        for token in forbidden:
            assert token not in source, f"Forbidden token '{token}' found in {module_file}"


def test_no_secret_shaped_materials_in_registry():
    packet = registry.platform_universe_registry_v2_packet()
    registry.assert_no_secret_shaped_material(packet)


def test_approval_hash_input_fields_exclusion():
    # approval hash input fields must only refer to content fields, never credentials, cookies, tokens, or sessions.
    forbidden_inputs = re.compile(
        r"(?i)(token|key|secret|cookie|session|password|auth|credential|env|header)"
    )
    for p in payload_contract.PAYLOAD_CLASSES:
        for field in p.approval_hash_input_fields:
            assert not forbidden_inputs.search(field), (
                f"Payload class {p.payload_class_id} includes sensitive field '{field}' in approval_hash_input_fields"
            )
