"""Kill switch mechanism."""
from . import config

def is_halted() -> bool:
    return config.KILL_SWITCH_DEFAULT

def status() -> str:
    if is_halted():
        return "all live actions blocked"
    return "active"
