# Telegram Read-Only Official Docs Grounding

Official docs source: `https://core.telegram.org/bots/api`.

Verified methods and fields:

- `getMe`: read-only bot identity method; no parameters; returns bot `User`.
- `getChat`: read-only chat lookup; requires `chat_id`; returns chat metadata including type.
- `getChatMember`: read-only membership lookup; requires `chat_id` and `user_id`.
- `ChatMemberAdministrator.can_post_messages`: channel posting permission flag for administrators.

Request format summary:

- Telegram Bot API uses token-path method-name request format on `api.telegram.org`.
- This proof stores only symbolic request-format text, never raw URLs.

Safety interpretation:

- Allowed host: `api.telegram.org`.
- Allowed methods: `getMe`, `getChat`, `getChatMember`.
- Allowed parameter names: `chat_id`, `user_id` only in method-specific exact shapes.
- No write/post/send/publish endpoint is called.
- Live write remains locked after read-only proof.
