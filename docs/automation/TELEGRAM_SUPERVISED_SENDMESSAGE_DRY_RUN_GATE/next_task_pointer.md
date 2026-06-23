# Next Task Pointer

Next task: supervised operator approval capture for exact Telegram sendMessage payload hash.

Required before live send:

1. Human operator reviews payload hash and redacted destination binding.
2. Approval ledger records current operator approval for exact payload hash.
3. Separate live-write gate re-validates read-only proof, approval, idempotency, kill switch, and audit sink.
4. Live send remains locked until that future task explicitly enables it.
