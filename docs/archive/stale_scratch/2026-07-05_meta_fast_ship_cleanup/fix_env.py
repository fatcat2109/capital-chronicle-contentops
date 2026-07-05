import sys
from pathlib import Path
from live_contentops.final_environment_format_inventory import REQUIRED_KEYS

def main():
    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    if not env_path.exists():
        print(".env does not exist, creating empty one")
        env_path.write_text("", encoding="utf-8")
    
    # Read the existing keys safely without printing any values or storing secret data in variables
    existing_keys = set()
    content = env_path.read_text(encoding="utf-8")
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, _ = line.partition("=")
            existing_keys.add(key.strip())
            
    # Find missing required keys
    missing_keys = [k for k in REQUIRED_KEYS if k not in existing_keys]
    if missing_keys:
        print(f"Found {len(missing_keys)} missing keys. Appending them with placeholder values...")
        with open(env_path, "a", encoding="utf-8") as f:
            f.write("\n\n# --- Appended missing required keys for V6 validation ---\n")
            for key in missing_keys:
                f.write(f"{key}=DUMMY_PLACEHOLDER_VALUE_V6\n")
        print("Successfully appended missing keys.")
    else:
        print("All required keys are already present in .env.")

if __name__ == "__main__":
    main()
