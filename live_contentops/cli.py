"""CLI entrypoint."""
import sys
import json
from . import status

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        s = status.get_status()
        print(json.dumps(s, indent=2))
        return 0
    else:
        print("Usage: python -m live_contentops.cli status")
        return 1

if __name__ == "__main__":
    sys.exit(main())
