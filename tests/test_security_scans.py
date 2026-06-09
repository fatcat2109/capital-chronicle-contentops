import os
import re
from pathlib import Path

def test_no_forbidden_imports_or_env_vars():
    root = Path(__file__).parent.parent / "live_contentops"
    forbidden_imports = re.compile(r"import\s+(requests|httpx|urllib|socket|openai|anthropic|tweepy|selenium|playwright|dotenv)")
    forbidden_env = re.compile(r"os\.environ")
    
    for p in root.rglob("*.py"):
        if p.name == "telegram_live_pilot.py":
            continue # Exempt live pilot script from strict no-network local guardrails
        text = p.read_text(encoding="utf-8")
        assert not forbidden_imports.search(text), f"Forbidden import found in {p}"
        assert not forbidden_env.search(text), f"os.environ access found in {p}"
