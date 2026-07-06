import os
import sys
import json
from pathlib import Path

# Add project root to python path so we can import live_contentops
project_root = Path(__file__).parents[1]
sys.path.insert(0, str(project_root))

def load_dotenv():
    env_path = project_root / ".env"
    if not env_path.exists():
        print("No .env file found at project root!")
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, _, val = stripped.partition("=")
            key = key.strip()
            val = val.strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in {"'", '"'}:
                val = val[1:-1]
            # Only set if it has a value and is not dummy placeholder
            if val and "DUMMY_PLACEHOLDER" not in val:
                os.environ[key] = val

load_dotenv()

from live_contentops import telegram_live_adapter_v6 as telegram
from live_contentops import facebook_page_adapter_v6 as facebook
from live_contentops import instagram_adapter_v6 as instagram
from live_contentops import threads_adapter_v6 as threads
from live_contentops import discord_live_adapter_v6 as discord

def run_real_dispatches():
    outcomes = {}

    print("=================== STARTING REAL LIVE DISPATCH RUN ===================")

    # 1. Discord Webhook
    print("\n--- Dispatching to Discord ---")
    discord_post_res = discord.execute_discord_post(
        message="Capital Chronicle Integration Smoke Test - V6 Real Dispatch",
        dry_run=False
    )
    print(f"Discord Post Result: {json.dumps(discord_post_res, indent=2)}")
    outcomes["discord_post"] = discord_post_res

    if discord_post_res.get("status") == "SUCCESS":
        msg_id = discord_post_res["id"]
        # Discord webhook edit
        discord_edit_res = discord.execute_discord_edit(
            message_id=msg_id,
            new_message="Capital Chronicle Integration Smoke Test - V6 Real Dispatch [Verified]",
            dry_run=False
        )
        print(f"Discord Edit Result: {json.dumps(discord_edit_res, indent=2)}")
        outcomes["discord_edit"] = discord_edit_res

    # 2. Telegram Bot API
    print("\n--- Dispatching to Telegram ---")
    tg_post_res = telegram.execute_telegram_post(
        message="Capital Chronicle Integration Smoke Test - V6 Real Dispatch",
        dry_run=False
    )
    print(f"Telegram Post Result: {json.dumps(tg_post_res, indent=2)}")
    outcomes["telegram_post"] = tg_post_res

    if tg_post_res.get("status") == "SUCCESS":
        msg_id = tg_post_res["id"]
        
        # Telegram reply (comment)
        tg_comment_res = telegram.execute_telegram_comment(
            reply_to_message_id=msg_id,
            message="Real-time verification comments auto-responder active.",
            dry_run=False
        )
        print(f"Telegram Reply Result: {json.dumps(tg_comment_res, indent=2)}")
        outcomes["telegram_reply"] = tg_comment_res

        # Telegram edit
        tg_edit_res = telegram.execute_telegram_edit(
            message_id=msg_id,
            new_message="Capital Chronicle Integration Smoke Test - V6 Real Dispatch [Verified]",
            dry_run=False
        )
        print(f"Telegram Edit Result: {json.dumps(tg_edit_res, indent=2)}")
        outcomes["telegram_edit"] = tg_edit_res

    # 3. Facebook Page
    print("\n--- Dispatching to Facebook Page ---")
    fb_post_res = facebook.execute_facebook_post(
        message="Capital Chronicle Integration Smoke Test - V6 Real Dispatch",
        dry_run=False
    )
    print(f"Facebook Post Result: {json.dumps(fb_post_res, indent=2)}")
    outcomes["facebook_post"] = fb_post_res

    if fb_post_res.get("status") == "SUCCESS":
        post_id = fb_post_res["id"]

        # Facebook comment
        fb_comment_res = facebook.execute_facebook_comment(
            post_id=post_id,
            message="Real-time verification comments auto-responder active.",
            dry_run=False
        )
        print(f"Facebook Comment Result: {json.dumps(fb_comment_res, indent=2)}")
        outcomes["facebook_comment"] = fb_comment_res

        # Facebook edit
        fb_edit_res = facebook.execute_facebook_edit(
            post_id=post_id,
            message="Capital Chronicle Integration Smoke Test - V6 Real Dispatch [Verified]",
            dry_run=False
        )
        print(f"Facebook Edit Result: {json.dumps(fb_edit_res, indent=2)}")
        outcomes["facebook_edit"] = fb_edit_res

    # 4. Threads
    print("\n--- Dispatching to Threads ---")
    threads_post_res = threads.execute_threads_post(
        text="Capital Chronicle Integration Smoke Test - V6 Real Dispatch",
        dry_run=False
    )
    print(f"Threads Post Result: {json.dumps(threads_post_res, indent=2)}")
    outcomes["threads_post"] = threads_post_res

    if threads_post_res.get("status") == "SUCCESS":
        post_id = threads_post_res["id"]

        # Threads reply
        threads_reply_res = threads.execute_threads_post(
            text="Real-time verification comments auto-responder active.",
            reply_to_id=post_id,
            dry_run=False
        )
        print(f"Threads Reply Result: {json.dumps(threads_reply_res, indent=2)}")
        outcomes["threads_reply"] = threads_reply_res

    # 5. Instagram Business
    print("\n--- Dispatching to Instagram Business ---")
    ig_post_res = instagram.execute_instagram_post(
        image_url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600",
        caption="Capital Chronicle Integration Smoke Test - V6 Real Dispatch",
        dry_run=False
    )
    print(f"Instagram Post Result: {json.dumps(ig_post_res, indent=2)}")
    outcomes["instagram_post"] = ig_post_res

    if ig_post_res.get("status") == "SUCCESS":
        media_id = ig_post_res["id"]

        # Instagram comment
        ig_comment_res = instagram.execute_instagram_comment(
            media_id=media_id,
            message="Real-time verification comments auto-responder active.",
            dry_run=False
        )
        print(f"Instagram Comment Result: {json.dumps(ig_comment_res, indent=2)}")
        outcomes["instagram_comment"] = ig_comment_res

    print("\n=================== DISPATCH RUN COMPLETED ===================")
    
    # Save outcomes to scratch for auditing
    outcomes_path = project_root / "scratch" / "last_real_dispatch_outcomes.json"
    with open(outcomes_path, "w", encoding="utf-8") as f:
        json.dump(outcomes, f, indent=2)
    print(f"\nSaved outcomes log to {outcomes_path}")

if __name__ == "__main__":
    run_real_dispatches()
