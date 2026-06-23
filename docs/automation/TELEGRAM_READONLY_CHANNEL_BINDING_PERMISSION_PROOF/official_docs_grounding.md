# Telegram Read-Only Official Docs Grounding

Official docs source: `https://core.telegram.org/bots/api`.

Verified method families:

- `getMe`: read-only bot identity proof.
- `getChat`: read-only target chat/channel metadata lookup.
- `getChatMember`: read-only bot membership and administrator permission lookup.

Request format:

- Telegram Bot API token-path method-name format, kept symbolic here to avoid raw bot URL persistence.

Safety interpretation:

- Only `api.telegram.org` is allowed.
- Only `getMe`, `getChat`, and `getChatMember` are allowed.
- `ChatMemberAdministrator.can_post_messages` is mapped to a redacted proof class only.
- Live write/post/send/publish remains false.
