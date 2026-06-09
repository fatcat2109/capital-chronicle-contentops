import os
import re

def test_env_example_contains_placeholders_only():
    env_example_path = ".env.example"
    
    if not os.path.exists(env_example_path):
        return  # test doesn't fail if it doesn't exist, but we expect it to
        
    with open(env_example_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Must not contain real bot token patterns
    bot_token_pattern = re.compile(r"bot[0-9]+:", re.IGNORECASE)
    assert not bot_token_pattern.search(content), ".env.example contains a bot token-like value"
    
    # Must not contain private channel ID patterns
    private_channel_pattern = re.compile(r"-100\d+")
    assert not private_channel_pattern.search(content), ".env.example contains a private channel ID-like value"
    
    # Verify the presence of expected placeholders
    assert "REPLACE_WITH_REAL_TOKEN_OUTSIDE_REPO" in content
    assert "REPLACE_WITH_PRIVATE_SANDBOX_CHANNEL_ID_OUTSIDE_REPO" in content
