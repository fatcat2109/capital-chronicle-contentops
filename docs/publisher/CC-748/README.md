# CC-748: the manual posting desk

Jim posts four platforms by hand: X, Substack Notes, the LinkedIn company page and the YouTube community post. Their automatic routes stay suspended in `Runtime/ContentOps/control/suspended_routes.json`; this desk does not read or change that file. It hands Jim a ready pack for every piece, so each platform takes him under a minute.

## What it does

Every minute, `scripts/plan_status_posts.py --publish` calls `live_contentops/manual_desk_v1.minute_hook`. The hook runs before the slow reply, page and browser work, because the task stops after five minutes. Any desk error is written to `manual_desk/errors.jsonl` and to the run record under `manual_desk`. It never stops posting.

1. **Packs.** It opens the store read-only (`?mode=ro`, `PRAGMA query_only=ON`). It finds every plan post, plan result, market wrap and article from the last 72 hours that at least one automatic platform received. For each one it builds a pack:
   - one text each for X (a thread of parts of 280 characters or fewer), Substack Notes (10,000), the LinkedIn company page (3,000) and the YouTube community post (1,000);
   - every text starts with the call (the plan's lead line, or the article's headline), then the analysis lines, then the notice and the chart credit, and ends with `Full analysis: <Substack link>`;
   - a text that is too long loses whole optional lines, longest first; the call and the conditional-call sentence are never dropped and no sentence is cut;
   - the words come from what the platform itself received, or, for a platform with no copy of its own, from the Telegram copy. X is always re-threaded from the Telegram copy;
   - the full Substack text, the chart file the live posts used (from the post's `delivery_media_manifest_v1.json`), and the Substack link.
2. **Checks on every text.** `plan_analysis_pages_v1.public_filter` (no sizes, money, accounts or model names) is always enforced. `event_article_guard_v1.check_publication_copy` (decisions 35, 40, 109) and `plan_reader_copy_v1.check_text` (numbers bound to the received copy) are enforced too, with one exception. If the received copy already fails one of those two checks with the same cause, the rule does not fit that piece's format: the measured-odds articles publish results in R under their own owner's check. The pack then records `*_AS_RECEIVED_<cause>` instead of withholding the text. A failing text is withheld with its cause, and the page shows that cause.
3. **The Substack link first.** A pack waits for its confirmed Substack page: a `DISPATCH_CONFIRMED` substack dispatch for `plan-analysis-<plan_id>`, the wrap or the article. After 30 minutes from the first platform post it is released marked "page pending", with no link. Once the page is confirmed, the texts carry the link, and the phone gets a follow-up for the platforms not yet marked Posted.
4. **The local page.** `Runtime/ContentOps/manual_desk/index.html` is a static file: no server and no port. It shows the newest packs first, with copy buttons, the chart (shown and saveable), the composer links and each pack's state: new, partly posted, posted, overdue (6 hours after release with a platform unposted) or waiting for its page. It reloads itself every minute.
5. **The phone.** The same private bot that sends the X reply drafts (CC-464, @CapitalChroniclePublisherBot) pushes each pack once, in the same private chat:
   - the chart;
   - a header with the Substack link and a "Latest packs" button;
   - then each platform text as its own plain message, so one long press copies it. X sends one message per thread part.
   - The first message of each platform has two buttons: "Open X composer", which opens `https://x.com/intent/post?text=...` with part 1 filled in (the others open the Substack Notes, LinkedIn page or YouTube posts page, where Jim pastes), and "Posted on <platform>".
6. **Pull.** Jim sends `/packs` or taps "Latest packs". On the next minute he gets every pack from the last 48 hours that still has platforms not marked Posted, newest first (5 at most), with only those platforms.
7. **Posted.** A Posted tap appends a line to `manual_desk/posted.jsonl`: the piece id, the platform, the time and `public_url: null`. If Jim replies to a platform's message with the post's URL, the line carries that URL; a bare URL attaches to the newest pack missing it. Each line carries the Telegram update id, so a re-read update writes nothing twice.

There is one reader of the bot's updates: `x_reply_bot_v1.process_updates`, which already runs every minute. It now passes desk updates (callbacks starting `dk:`, `/packs`, "latest packs", and post URLs) from Jim's bound private chat only to `manual_desk_v1.accept_update`. Every other chat is ignored as before, and the update offset still advances once. A desk fault there is counted as `DESK_UPDATE_FAILED_<class>` and the reply drafts continue.

## Files (under `Runtime/ContentOps/manual_desk/`)

| File | What it holds |
|---|---|
| `index.html` | the local page |
| `packs.json` | the current packs with their per-platform state (`overdue_packs()` reads it for the evening check) |
| `sent.jsonl` | the phone ledger: a pack version (`<pack>:pending`, `<pack>:linked`, `pull:<update>:<pack>`) is written as SENDING before its first message and is never sent again, even after a crash |
| `posted.jsonl` | Jim's Posted marks |
| `inbox.jsonl` | `/packs` requests waiting for the next minute |
| `desk_state.json` | each pack's first release time (for the 6-hour overdue mark) |
| `errors.jsonl` | desk failures, class names only |

## How Jim uses it

- **On the PC:** open `A:\Capital Chronicle\Runtime\ContentOps\manual_desk\index.html`. For each platform, press Copy, open the composer link, paste, attach the chart, and press Post.
- **On the phone:** long-press the text message, tap "Open X composer" (or the platform's button), press Post, then tap "Posted on ...". To record the post's link, reply to that text message with the URL.
- **Any time:** send `/packs` to get what is still unposted.

## Start-up

No new bot is needed and no `/start`: the binding in `control/x_reply_bot_binding.json` is already bound to Jim's private chat. The desk uses the bot's own `private_chat` check and send path, and never prints the chat id or the token. On its first live minute, the desk pushes only packs first posted in the previous 6 hours, at most 3 a minute, so the phone is not flooded with older pieces; the page still shows 72 hours.

## Tests

`tests/test_manual_desk_cc748.py`: fake store rows and a fake bot, with no network. It covers:
- X parts of 280 characters or fewer, the call first and the link last;
- a withheld private line;
- waiting, then page pending, then the link following;
- the 6-hour overdue mark;
- no re-send after a restart or an interrupted send;
- the Posted tap, the URL reply, `/packs` and "Latest packs" through the one bot reader;
- other chats ignored;
- wrap and article packs;
- a read-only store;
- a desk failure that does not stop the minute job or the reply drafts.
