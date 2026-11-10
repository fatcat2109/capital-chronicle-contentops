# CC-395 public bio and About inventory

Read through BrowserOS Neo on 10 November 2026, 08:27–08:44 GMT+7
(01:27–01:44 UTC). No profile, account setting or public object was edited.
Only the item's task tabs were used; no mailbox or signed-in Telegram view was opened.

| Surface | Current wording / observed state | AI label |
|---|---|---|
| [Substack About](https://capitalchronicle.substack.com/about) | Generic template: “Why subscribe?”; “Subscribe to get full access to the newsletter and publication archives.”; “Stay up-to-date”; “Never miss an update—every new post is sent directly to your email inbox. For a spam-free, ad-free reading experience, plus audio and community features, get the Substack app.”; “Join the crew”; “Be part of a community of people who share your interests. Participate in the comments section, or support this work with a subscription.” | None in the visible About copy. |
| [Substack profile](https://substack.com/@capitalchronicle) | Displayed “Jim’s Substack”, handle @capitalchronicle; no description text exposed. | None visible. |
| [Telegram public channel](https://t.me/s/CapitalChronicle) | “Capital Chronicle”, @CapitalChronicle; the public page exposes no channel-description wording. Official Bot API `getChat` independently confirmed the description is empty (`telegram-bio.json`). Posts are separate historical objects. | None; API confirms an empty description. |
| [Discord server profile](https://discord.com/channels/1519310996030750782/1519310996689387673) | Name “Capital Chronicle”; Description field empty in the read-only Server Profile view. The UI identifies it as a Private Server. Welcome-channel topic: “Start here. What Capital Chronicle is, what this Discord is for, and how to participate.” Welcome text transcribed below. | **Flag: “AI-native content operations” in the welcome/about text.** This describes the product; it is not an explicit claim that all desk decisions are AI-run. |
| [Threads](https://www.threads.com/@official.capitalchronicle) | “Capital Chronicle”, official.capitalchronicle. No bio; the page shows “Finish your profile” / “Add bio”. | None visible. |
| [Facebook About](https://www.facebook.com/official.capitalchronicle/about) | “Capital Chronicle”; category “Blogger”; Bio shows the empty “About you” prompt. The Intro route gives the same result. | None visible. |
| [Instagram](https://www.instagram.com/official.capitalchronicle/) | “Capital Chronicle”, official.capitalchronicle; category “Entrepreneur”; no biography text displayed before the Threads link. | None visible. |
| [LinkedIn company](https://www.linkedin.com/company/capitalchronicle/about/?viewAsMember=true) | **“AI-driven macro & market intelligence”**; Industry “Financial Services”; no Overview prose displayed. Opened in member view after the numeric company URL redirected to the admin dashboard. | **Flag: AI-driven tagline.** |
| [YouTube About](https://www.youtube.com/@CapitalChronicleYouTube/about) | @CapitalChronicleYouTube; full description transcribed below. | None in the visible description. |

## Discord welcome/about text

“Welcome to Capital Chronicle. This is a community for serious macro research,
AI-native content operations, source trust, data sufficiency, and build-in-public
product work. Capital Chronicle is not a signal service. Nothing here is financial
advice. We do not provide buy/sell/hold calls, price targets, position sizing,
execution instructions, or guaranteed predictions. The core idea: better public
macro discussion should show sources, uncertainty, missing data, limitations, and
forecast readiness instead of pretending every headline is a trade.”

This is the pinned 24 June welcome message, not a new post. It is recorded and
flagged without editing it. The settings description itself is empty.

## YouTube description

“Welcome to Capital Chronicle, your trusted source for data-driven commentary and
deep insights into global economics and finance. We deliver regular market recaps,
timely updates on key economic data, and expert perspectives on long-term finance
strategies—empowering you to stay ahead in an ever-changing landscape. From policy
shifts and regime changes to evolving investment trends, our comprehensive coverage
translates complex financial concepts into actionable knowledge. Join us for a
richer understanding of global markets, sharpen your decision-making, and gain the
confidence to navigate the future of finance with clarity and purpose. Subscribe
now and start charting your path forward.”

## Prepared account action

Ops Product owns any change under decision 109. At its account-setting confirmation
step with Jim, replace the LinkedIn company tagline with “Macro and market analysis”
and remove the AI-native product wording from the Discord welcome/about presentation.
This inventory authorizes no account-setting change. Telegram's description was independently checked through the authorized channel Bot API and is empty.
