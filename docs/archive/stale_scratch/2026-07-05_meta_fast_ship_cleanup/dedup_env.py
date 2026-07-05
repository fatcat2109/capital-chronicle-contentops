from pathlib import Path

def main():
    root = Path(__file__).resolve().parents[1]
    env_path = root / ".env"
    if not env_path.exists():
        return
        
    lines = env_path.read_text(encoding="utf-8").splitlines()
    seen_keys = set()
    new_lines = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue
        if "=" in stripped:
            key, _, _ = stripped.partition("=")
            key = key.strip()
            if key in seen_keys:
                print(f"Skipping duplicate definition of {key}")
                continue
            seen_keys.add(key)
        new_lines.append(line)
        
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print("Deduplicated .env successfully.")

if __name__ == "__main__":
    main()
