import re
from live_contentops import unified_payload_hash_manifest_v6 as hm

def test_canonical_json_hashing_is_deterministic():
    obj1 = {"a": 1, "b": [2, 3], "c": {"d": "test\r\nvalue"}}
    obj2 = {"c": {"d": "test\nvalue"}, "b": [2, 3], "a": 1}
    
    hash1 = hm.get_canonical_json_hash(obj1)
    hash2 = hm.get_canonical_json_hash(obj2)
    
    assert hash1 == hash2
    assert re.match(r"^[0-9a-f]{64}$", hash1)
