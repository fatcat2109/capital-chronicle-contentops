"""Retained native MAX manuscripts for the five current 10 November plans.

The paragraphs below were authored in this Codex run from Main's exact files.
This is a dated preparation artifact, not a future prose generator.
"""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from live_contentops import plan_analysis_pages_v1 as pages
from live_contentops.plan_status_posts_v1 import read_export

TEXT = {
"EURUSD": {
 "title": "EUR/USD before CPI: the dollar thesis and its weak link",
 "subtitle": "A full account of the conditional euro view: the dollar driver, crowded positioning, price structure and the critic's rates objection.",
 "introduction": "This is the analysis behind the euro plan fixed before the US inflation release. The case was conditional: a weaker dollar could carry the euro higher, provided the breakout base held and inflation did not restore demand for the dollar. The strongest objection was causal: the currency move was clearer than the explanation for it. All levels and chances below belong to that original view; publication of this page does not refresh them.",
 "macro": [
  "The desk identified a US dollar leg rather than an isolated euro move. EUR/USD moved with sterling and the New Zealand dollar while the dollar index weakened. Capital Chronicle's own twenty-day calculation put EUR/USD's correlation with the dollar index at -0.966 and its beta at -1.09. These measures described a close recent relationship; they did not establish that a change in US interest rates caused the move.",
  "The first analyst proposed an oil-led easing of inflation pressure: cheaper energy could reduce inflation concern, weaken the dollar and support the euro. The critic challenged the middle of that chain. The run did not contain a current admitted US ten-year Treasury yield observation supporting falling rates, while the rates context pointed in the opposite direction. The final owner retained the observed dollar weakness and downgraded the claim about its cause. A correlated move is evidence of a common channel, not proof of a particular policy repricing.",
  "The regime remained sensitive to US inflation and the next policy decision. A core inflation surprise could revive the dollar even after the previous session's reversal. The useful test was therefore the inflation figure followed by the joint reaction of EUR/USD and the dollar index, rather than treating the preceding rally as a permanent change of regime."
 ],
 "fundamental": [
  "For a currency pair, the fundamental question is the relative path of policy and growth. The original analysis considered euro-area inflation and a potentially firmer European Central Bank response as possible euro support. It did not establish a fresh, comparable euro versus US rate differential. The final view consequently placed more weight on the demonstrated dollar channel than on a quantified interest-rate advantage for the euro.",
  "That distinction changes the quality of the thesis. A view backed by a measured rate differential can survive some short-term currency noise. This view needed the dollar's decline to persist after the US data. A reversal in US inflation expectations would weaken the argument even if euro-area policy remained relatively firm. The desk did not turn background policy discussion into a confirmed central-bank commitment."
 ],
 "technical": [
  "The pullback entry zone was 1.12010–1.12050. The owner located it at the previous session's breakout base, rather than at an arbitrary distance from the latest price. The distinct breakout zone was 1.12270–1.12300, beyond the nearby resistance at 1.12250. These were two conditional expressions of the same direction: a return to support or evidence that resistance had been cleared.",
  "The pullback's stop was 1.11820; the breakout's separate stop was 1.12140. The common model target was 1.12640, set below the earlier overhead resistance discussed in the run. Different stops mattered because the breakout rested on a different, nearer structure. The target was part of the frozen analytical geometry, not an assurance about a future price or an instruction to a reader.",
  "The volatility context made chasing less attractive. The desk's pricing assessment described a move of 1.38 average true ranges from the earlier close and a one-day volatility-normalised move of 2.18. Its twenty-day mean was 1.11934, fifty-day mean 1.12796 and two-hundred-day mean 1.15026. The euro could have positive short-term momentum while remaining below longer-term reference points. The plan therefore relied on its own support and resistance conditions rather than a blanket claim that every trend measure agreed.",
  "The fourteen-day daily average true range in the run was 0.00581071. This was the desk's volatility calculation, not an observed future range. The owner also preserved the warning that an inflation-release move could cross a stop abruptly; a level that invalidates the idea does not guarantee execution at that level."
 ],
 "geopolitical": [
  "The analytical mechanism was an unwind in energy and haven demand that could weaken the dollar. The run also carried unconfirmed event explanations. Those event details are not reproduced here: the public case rests on the observed currency relationship and the desk's conditional interpretation, not on treating an unverified report as an established geopolitical outcome.",
  "The countermechanism was straightforward. Renewed demand for the dollar, whether from a change in inflation expectations or a reversal in risk appetite, could overwhelm the euro's support. The final owner retained that vulnerability instead of presenting de-escalation, cheaper energy and a weaker dollar as a single proven sequence."
 ],
 "priced_in": [
  "The inflation comparison used the held consensus capture: Investing.com supplied a headline monthly CPI expectation of 0.3%, and the core monthly expectation in the captured consensus record was 0.2%. These are attributed comparison figures from the original run, not a reproduced forecast table or a later update. The plan's adverse event condition was a core reading of 0.3% or more with a renewed dollar bid.",
  "Positioning came from the CFTC commitments report dated 3 November and released 6 November: the retained analysis cited a euro non-commercial net short of 157,791 contracts. The owner viewed a break of nearby resistance as a possible short-covering catalyst. That was an interpretation of a dated positioning figure, not an observation of current dealer orders or a claim that all of those contracts would be bought back.",
  "The desk explicitly called the prior-pricing assessment ambiguous. The run did not establish a fresh, source-bound option-implied move. Realised volatility, distance from moving averages and a crowded position can describe the market's starting point; none can be silently substituted for an options market's expected release move."
 ],
 "scenarios": [
  "Base case — 55% (Capital Chronicle model estimate, uncalibrated): EUR/USD holds above 1.1200 and extends through the 1.1225 high within three sessions. Confirmation requires the dollar weakness to survive the inflation release and the plan's own support conditions to hold. The two entry zones provide the pullback and breakout versions of this case.",
  "Downside alternative — 35% (Capital Chronicle model estimate, uncalibrated): a hot core inflation reading restores the dollar bid and takes EUR/USD below 1.1186. The owner described an analytical reversal condition combining core CPI of at least 0.3%, EUR/USD below 1.11860 and the dollar index above 102.0. The explicit price stops remain 1.11820 for the pullback and 1.12140 for the breakout.",
  "Upside extension and a sideways outcome were not assigned separate point probabilities in the final record. Clearing 1.12250 would support the continuation toward the stated 1.12640 objective; failure to clear resistance could leave the view unresolved. The page does not allocate an invented remainder to either outcome. The stated chances are judgments from this run and are not a calibrated record of success."
 ],
 "desk_process": [
  "The first analyst's base case was 58%, with a 32% main alternative. The critic reduced the base case to about 55% and raised the alternative to about 35%, stressing pre-release position adjustment, the unresolved interest-rate explanation and the risk around the nearer breakout stop. The owner adopted the 55% and 35% judgments and kept the direction conditional.",
  "The committee's evidence combined same-session currency relationships, the desk's correlation and volatility calculations, the dated CFTC figure and the captured inflation consensus. The hourly and shorter-interval observations were already known before the run's cutoff. Their exact file locations, hashes and paragraph-level numeric references are retained with this page. No later observation was used to make the original case look stronger.",
  "The final response to the critic was to separate what the desk could observe from what it could explain. Dollar weakness and the structural levels survived; the assertion that lower US yields caused them did not become a confirmed fact. The page retains that dissent because it identifies the condition under which the attractive chart could still be wrong. The freeze time and fingerprint below identify the exact decision version."
 ]
},
"XAUUSD": {
 "title": "Gold: a support test after a strong run, with the dollar channel uncertain",
 "subtitle": "The original conditional gold plan, its two entry structures and the liquidation risk the critic kept.",
 "introduction": "The gold view combined an accepted prior-session recovery with a less reassuring new-session dip. The desk kept a conditional upward case, but the dollar was no longer confirming the latest move. This page records that original reasoning and its limitations, using only evidence and levels held in the run that produced the plan.",
 "macro": [
  "The previous recovery had moved with a weaker dollar. In the later snapshot, gold fell while the dollar was broadly flat. The desk therefore classified the current transmission as mixed: the earlier dollar channel could explain the preceding advance, but it did not explain the newest decline. Treating those two periods as one uninterrupted macro impulse would overstate the evidence.",
  "Capital Chronicle's calculations described an advance of about 2.3 daily average true ranges from the earlier reference point. A large prior move can leave a market vulnerable even when its original macro argument is intact. The owner consequently required either a return to identified support or a break of the previous high, instead of treating the latest price as an automatic continuation.",
  "The run did not establish a fresh US ten-year yield observation that resolved the gold move. It therefore did not claim a confirmed decline in real yields. The macro question remained whether dollar weakness would resume or whether gold-specific selling would overcome it."
 ],
 "fundamental": [
  "Gold's fundamental channels include its sensitivity to the dollar, the opportunity cost of holding it and demand for a haven. The frozen analysis did not quantify a fresh physical supply-demand balance or establish new fund inflows. The upward case was consequently a conditional interpretation of price structure and the preceding dollar move, rather than a documented change in physical scarcity.",
  "This mattered to the countercase. If the latest dip reflected a reduction in haven demand or a separate liquidation, the earlier currency explanation would offer little protection. The critic specifically retained the possibility that the break of the Asian low was the start of a deeper decline. The final owner did not resolve that uncertainty by inventing a new fundamental catalyst."
 ],
 "technical": [
  "The pullback zone was 4101–4104, above the prior afternoon support identified around 4100.46. The breakout condition was 4150, beyond the previous high of 4148.76. These structures distinguished buying a support retest from following a genuine break of the extreme; the source did not treat a small bounce inside the range as equivalent confirmation.",
  "The plan's invalidation used a completed short-interval close below 4079, beneath the prior low at 4084.40. The run's nearer warning was the loss of the Asian low at 4120.2. The critic's concern was that the pullback version could be exposed while that decline was still developing. The model target and the separate breakout geometry are displayed on the source-bound plan card.",
  "The momentum evidence was mixed across horizons. The prior advance was substantial, but the newest drop had held only briefly and remained inside the preceding hourly range. The desk had not observed a complete twenty-, fifty- and two-hundred-day trend comparison in this shock review. It did not infer those missing comparisons from the positive prior-session return.",
  "The average true range used in the geometry was the desk's own fourteen-period daily calculation. It scaled the extension and the latest move; it was not an option-implied range or a promise that the next session would remain inside it."
 ],
 "geopolitical": [
  "The geopolitical question was how a change in haven demand could affect gold. A reduction in perceived conflict risk could remove support; renewed uncertainty could restore it. These are competing analytical channels. The original run did not admit a verified event that established which channel caused the latest dip, so this page does not reproduce the private event leads or present them as facts.",
  "The owner kept the price test independent of an event narrative. Support had to hold, or the previous high had to break. That design preserved a falsifiable case even when the event explanation remained unresolved."
 ],
 "priced_in": [
  "The desk saw an already extended advance, not an untouched opportunity. Its own volatility assessment put the run at about 2.3 daily average true ranges. A further rise therefore needed renewed confirmation, while an unwind could be amplified by holders who had joined the advance late.",
  "The shock roles did not cite a current CFTC positioning observation, a fresh option-implied move or a new quantified fund-flow measure. The owner could discuss possible pressure on late buyers, but could not turn that interpretation into a measured inventory of current positions. No such series is manufactured here.",
  "The priced-in question was therefore practical: would the market defend the earlier support despite the break of the Asian low? The distinction between prior strength and new acceptance was the reason for retaining both the support retest and the breakout condition."
 ],
 "scenarios": [
  "Base case — about 55% (Capital Chronicle model estimate, uncalibrated): the previous low around 4084.40 holds and gold revisits the 4148 area within six sessions. The pullback zone at 4101–4104 or the separate break at 4150 supplies the required price condition. The owner retained this as a conditional view, not a certainty about the next move.",
  "Downside alternative — about 45% in the first analyst's scenario (Capital Chronicle model estimate, uncalibrated): the loss of 4120.2 extends through 4084.4. A completed short-interval close below 4079 invalidates the recorded plan. The critic preserved this liquidation countercase; the final owner's short rationale restated the approximate 55% base judgment without assigning a new alternative figure.",
  "A distinct upside extension beyond the prior high was not given a separate probability. A break at 4150 is the continuation condition, not an additional chance to be added to the base case. Neither a third probability nor a new target has been inferred from the two stated cases."
 ],
 "desk_process": [
  "The first analyst proposed a support-based upward view with two distinct structures. The critic checked those structures and retained a substantive objection: the dip with a flat dollar could be the beginning of liquidation rather than an attractive retest. The owner kept both the conditional view and the mixed-channel qualification.",
  "The committee cited the prior-session structure, shorter-interval acceptance and the desk's own volatility context. It did not upgrade a coincident news lead into proof. The independent critic-note file is also retained with the source manifest; a missing or unsuccessful return is never represented as another completed agreement.",
  "The page is tied to the original final-decision freeze, not the clock at which this account is published. Exact source files and paragraph-level numeric references remain bound to that version. A later market outcome can test the original view but cannot be inserted into its original rationale."
 ]
},
"USOIL": {
 "title": "WTI: an accepted breakdown, and the squeeze that could undo it",
 "subtitle": "Why the desk kept a conditional downward view after an extended fall, without turning event leads into a supply forecast.",
 "introduction": "The oil plan rested on an accepted breakdown and a sequence of lower highs. Its weakest point was the size of the move already completed: a technically coherent downward case could still be vulnerable to a sharp squeeze. This account preserves the conditions, countercase and evidence limits of the original run.",
 "macro": [
  "The preceding session combined weaker oil with a weaker dollar and a recovery in equities. The desk treated those as related market observations while keeping the cause of the oil move unresolved. A drop in crude can ease inflation pressure and support risk appetite, but the run did not demonstrate a fresh change in monetary policy caused by this particular move.",
  "The desk's own volatility work described a decline of about 2.5 daily average true ranges from the earlier reference point, including about 1.6 average true ranges in the latest full session. That extension was material counterevidence to chasing the move. The owner consequently used a bounce toward resistance or a break of the prior low as distinct conditions.",
  "The shock did not supply a source-bound US ten-year yield explanation that resolved the oil thesis. The plan was price-led, rather than a conclusion that every macro channel independently pointed in the same direction."
 ],
 "fundamental": [
  "Oil's physical balance depends on supply interruptions, producer decisions, inventories and demand. The reviewed run did not establish a new official inventory release or a quantified change in supply that explained this breakdown. The final owner explicitly kept the cause from becoming load-bearing. The downward price case should therefore not be read as a documented forecast of a growing physical surplus.",
  "The same distinction applied to the opposite case. A verified supply interruption could support a squeeze, but the source did not treat an unconfirmed event or trade-data lead as proof of one. The critic's useful contribution was the conditional supply-risk channel and the already extended price move, rather than a new claim about barrels entering or leaving the market."
 ],
 "technical": [
  "The first analyst identified the previous low at 84.237 and lower highs at 86.326 and 86.069. The pullback zone was 85.95–86.05, beneath the nearer lower high. The separate breakout condition was 84.20, below the previous low. These were two ways to test continued weakness without treating every small downward tick as a new signal.",
  "The plan's invalidation was a completed short-interval close above 86.80, beyond the prior lower-high structure. The final model target and exact separate breakout geometry remain on the run-bound plan card. A stop is the level that contradicts the setup; it does not guarantee that a volatile move can be exited at precisely that price.",
  "The previous decline was already large enough to create a positioning hazard. The primary analysis described about a 2.5-average-true-range move and the critic retained the possibility of a squeeze through 86.33. That objection survived the final decision. A coherent sequence of lower highs does not make a stretched market immune to reversal.",
  "The shock review did not establish a complete twenty-, fifty- and two-hundred-day comparison. Its trend evidence was the observed breakdown and the subsequent lower highs, measured against the desk's daily average true range. The analysis did not substitute that short-term structure for a fully measured long-term trend."
 ],
 "geopolitical": [
  "The mechanism is direct: a confirmed threat to supply or transport can lift oil, while a reduction in that risk can remove a premium. The original run contained competing, unadmitted event explanations. Their private details are excluded here. The owner kept the plan on price structure because those explanations had not established a verified direction for the shock.",
  "This left a real asymmetry. Continued weakness could proceed without a new event, while a verified supply action could quickly challenge a stretched short-side view. The critic kept that countermechanism. The page does not call a disputed event confirmed simply because it would fit the chart."
 ],
 "priced_in": [
  "Much of the weakness was already reflected in the desk's volatility-normalised assessment: about 2.5 daily average true ranges from the earlier reference point. The issue was therefore whether the market would accept another break, or instead squeeze above the recent lower highs.",
  "The shock roles did not cite a current CFTC position, a fresh option-implied move or an admitted inventory surprise. Possible pressure on late shorts was a model interpretation of the extended move, not a measured count of today's positions. The run's own evidence limits remain visible in that distinction.",
  "A return above 86.33 would challenge the lower-high sequence; the plan's explicit invalidation was 86.80. The separation between an early warning and the recorded invalidation prevented a vague event narrative from replacing the plan's actual price test."
 ],
 "scenarios": [
  "Base case — about 55% (Capital Chronicle model estimate, uncalibrated): WTI stays below 86.33 and revisits the 84.24 area within six sessions. The pullback zone at 85.95–86.05 and the separate break at 84.20 provide the recorded conditions. This is the first analyst's directional case retained by the owner.",
  "Upside alternative — about 45% in the first analyst's scenario (Capital Chronicle model estimate, uncalibrated): short covering carries the market through 86.33 toward 87.5. The critic kept the squeeze risk because the preceding decline was already extended. A completed short-interval close above 86.80 invalidates the original plan.",
  "A separate accelerated-downside case was not assigned a point probability. A break below the previous low would confirm continuation, but it does not authorise inventing another chance or extending the frozen target. The final owner's concise record repeated the approximate 55% base judgment without supplying a revised alternative probability."
 ],
 "desk_process": [
  "The first analyst built the case from the accepted breakdown and lower highs. The critic accepted the structural explanation while retaining the danger of a stretched move and an abrupt squeeze. The owner kept a conditional downward view and explicitly declined to make the unadmitted event explanation a required premise.",
  "The committee's cited evidence was time-bound: the prior session's low, subsequent resistance and shorter-interval behaviour were known before the decision cutoff. The geometry and options-context files are retained alongside the role outputs. Their presence is recorded accurately; a retained options file does not prove the roles used a fresh implied move.",
  "The decision process is useful because it shows what survived criticism. The price structure survived; a confirmed event cause did not emerge; the squeeze objection remained. The freeze time and fingerprint below identify that original balance of evidence and judgment."
 ]
},
"US500": {
 "title": "S&P 500: a recovery that held, with a narrow base beneath it",
 "subtitle": "The desk's conditional index view, its breakout and retest structures, and the countercase behind the rally.",
 "introduction": "The index plan followed a recovery that held into the next session. The desk retained an upward case only at identified structure: a return to the base or a break above the prior high. The analysis did not claim that a strong chart settled the questions about earnings, valuation or the next macro catalyst.",
 "macro": [
  "The primary analysis identified a risk recovery alongside a weaker dollar and lower oil. Those relationships were supportive of equities, but the current channel remained mixed. The owner did not turn the co-movement into proof that lower US rates had caused the rally or that every part of the macro environment had improved.",
  "The recovery had already brought the index close to the prior high. Capital Chronicle's own assessment described a largely completed round trip from the earlier reference point and a recovery of about 1.7 daily average true ranges from the low. The macro benefit was therefore partly expressed in price before the plan was frozen.",
  "The shock review did not establish a fresh US ten-year yield observation that independently confirmed the index thesis. The relevant test remained acceptance at the base and at the previous extreme, with the dollar and energy channels providing context rather than an unconditional forecast."
 ],
 "fundamental": [
  "For an equity index, earnings, margins, financing conditions and valuation determine how durable a recovery can be. This shock review did not supply a new aggregate earnings revision or a freshly measured valuation multiple. The final plan was therefore a conditional recovery setup, not a quantified claim that the index had become cheap.",
  "The run retained technology-investment and credit sensitivity as possible opposing channels. A market can welcome cheaper energy while remaining vulnerable to a change in financing expectations. Specific unverified leads are not reproduced here, and the source did not establish a confirmed new company event that resolved that fundamental tension.",
  "That limitation affects interpretation. A defended chart base can support the recorded setup, but it cannot by itself verify a stronger earnings outlook. The owner kept the distinction between an observable recovery and the longer-lived fundamental explanation a reader would need for a broader investment thesis."
 ],
 "technical": [
  "The pullback zone was 7500–7506, built around the previous breakout base and the recorded 7500.73 support. The separate breakout condition was 7584, above the prior high of 7581.97. The distance between these structures mattered: a small move inside the existing range was not the same evidence as a break above its extreme.",
  "The plan was invalidated by a completed short-interval close below 7478, beneath that base. Its exact model target and the distinct breakout geometry remain on the run-bound card. These levels describe the original conditional view; they are not changed to fit later prices.",
  "The critic accepted the structure but highlighted the fragility of the retest version. The move back to the base could be the start of a broader reversal rather than an opportunity to resume the rally. That objection was especially relevant because the run described no clear fresh reaction to the latest shock window.",
  "The shock roles did not establish a full twenty-, fifty- and two-hundred-day trend comparison. Their evidence was the prior recovery, the defended base, proximity to the high and the desk's daily volatility calculation. The page preserves that narrower technical scope."
 ],
 "geopolitical": [
  "The analytical channel ran mainly through energy costs and appetite for risk. A durable easing in those pressures could help equities, while renewed uncertainty could reverse that benefit. The run did not admit a verified geopolitical event that proved which mechanism controlled the latest price.",
  "The owner consequently kept the condition observable: the base had to hold or the previous high had to break. This avoided making an unverified event explanation the reason to assume that the recovery would continue."
 ],
 "priced_in": [
  "The previous recovery had already restored much of the earlier decline. The desk's assessment was that the index sat near its prior high after a roughly 1.7-average-true-range rebound from the low. The question was not whether the rebound existed, but how much additional good news was required to extend it.",
  "The shock roles did not cite a current CFTC observation or a fresh source-bound option-implied move. A retained gamma-context file is included in the source manifest, but the primary role said that its gamma row had not been read. This page therefore does not present an unreviewed options level as support for the plan.",
  "The lower boundary was concrete: the model base at 7500–7506, with invalidation below 7478. The upper confirmation was equally concrete: 7584 beyond 7581.97. Those conditions expressed what the desk needed the market to prove rather than treating a broad risk-appetite label as sufficient."
 ],
 "scenarios": [
  "Base case — about 55% (Capital Chronicle model estimate, uncalibrated): the recovery holds above 7500 and revisits the 7578–7582 area. The plan provides a retest zone at 7500–7506 and a separate continuation condition at 7584. The owner retained the base case as conditional.",
  "Downside alternative — about 45% in the first analyst's scenario (Capital Chronicle model estimate, uncalibrated): the recovery fades back below 7500. A completed short-interval close below 7478 invalidates the recorded view. The critic kept the possibility that the apparent retest could be a reversal.",
  "An upside extension beyond the prior high was not assigned a separate probability. The breakout at 7584 is a condition within the upward case, not another probability to add to it. The final owner's concise record repeated the approximate 55% judgment and did not create a separately calibrated three-case distribution."
 ],
 "desk_process": [
  "The first analyst proposed an upward case from the recovery and the two distinct entry structures. The critic accepted those structures while retaining a mixed transmission channel and the danger of fading the rebound. The owner kept a conditional plan rather than presenting the recovery as an unconditional market recommendation.",
  "The committee cited the prior-session low, recovered base, previous high and the desk's volatility context, all held before the decision cutoff. The exact role outputs, geometry, options context and final owner record remain bound by file hash. A file's existence does not establish that every number in it influenced the decision.",
  "The critical contribution was to limit the claim. The desk could show a recovery and test its structure; it could not show a new earnings or valuation regime from this run. The freeze time and fingerprint below identify the original view, including those limits."
 ]
},
"BTCUSD": {
 "title": "Bitcoin: relative weakness after the equity recovery",
 "subtitle": "The lower-high sequence behind the conditional downward case, and why an equity-led squeeze remained a serious countercase.",
 "introduction": "The Bitcoin plan was based on relative weakness and a series of lower highs. The desk did not identify an admitted new fundamental cause. Its case therefore depended on clear price conditions, while the possibility of a broader risk recovery remained the main challenge.",
 "macro": [
  "The key comparison was with equities. The index had recovered toward its prior high while Bitcoin failed to follow through. The desk interpreted that divergence as crypto-specific weakness rather than evidence that all risk assets were moving together. A shared risk-appetite story could not explain the difference on its own.",
  "Capital Chronicle's calculations described a decline of about 2.4 daily average true ranges from the earlier reference point. That extension supported the observation of weakness but also increased the risk of a rebound. The owner kept a conditional downward case instead of treating a large completed decline as proof of an unlimited continuation.",
  "The run did not establish a fresh US ten-year yield, a measured liquidity shock or an independently confirmed macro event that named the cause of Bitcoin's latest move. The critical test was whether equities could extend their recovery and pull Bitcoin back through its lower highs."
 ],
 "fundamental": [
  "For Bitcoin, the relevant fundamental question in this run was flows: who was adding or removing demand, and whether the divergence from equities had a measurable cause. The roles did not cite a new confirmed fund-flow series or a quantified on-chain flow explaining the decline. The owner explicitly kept the cause unnamed.",
  "The page therefore does not relabel price weakness as proven institutional outflow. A relative-performance observation is useful, but it cannot identify the buyer or seller behind a move. The downward case was a structural judgment, while a return of broad risk demand remained a viable opposing mechanism.",
  "That distinction also limits the horizon. The plan can be tested against its own conditions and invalidation, but the run does not establish a lasting deterioration in adoption or a new long-term valuation. A reader should not infer either from the shorter-term setup."
 ],
 "technical": [
  "The lower-high sequence was the primary structure. The run cited hourly highs at 75511.91, 75492.84 and 75354.13. The pullback zone at 75250–75340 lay beneath the latest lower high. The separate breakout condition was 73600, below the prior low at 73653.94.",
  "The recorded invalidation was a completed short-interval close above 75700, beyond the lower-high structure. The plan's model target was 73700. The nearby weekend low at 73328 was a reason to treat further downside as contested terrain, not an empty space into which a target could be extended at will.",
  "The latest acceptance was not decisive. The analysis described a slow drift below the Asian low rather than a large new impulsive break. That distinction explained why the owner required a bounce into resistance or a fresh break of the prior low, rather than presenting the current price as sufficient confirmation.",
  "The review did not establish a full twenty-, fifty- and two-hundred-day trend comparison. Its momentum evidence was the lower-high sequence, relative weakness and the desk's daily volatility assessment. The average true range described the completed move; it was not an option-implied forecast."
 ],
 "geopolitical": [
  "The run did not establish a verified geopolitical event as the cause of this Bitcoin move. The relevant analytical channel was indirect: a change in broad appetite for risk could either reinforce crypto weakness or pull it back toward the equity recovery. The page excludes the private event leads rather than treating them as independent corroboration.",
  "This left price and relative performance as the falsifiable tests. If equities extended and Bitcoin reclaimed the lower highs, the main countercase would gain support even without a new geopolitical explanation. The owner did not require a convenient news story before recognising that risk."
 ],
 "priced_in": [
  "The desk saw an already extended move: about 2.4 daily average true ranges from the earlier reference point. That starting point made the next downside break less attractive to chase and left room for short covering if risk appetite improved.",
  "The shock roles did not cite current CFTC positioning, a fresh option-implied move or a confirmed new flow number. Possible pressure on shorts above the lower highs was the desk's interpretation of structure, not a measured current position count. No proprietary series or unsupported flow estimate is reproduced here.",
  "The competing thresholds were explicit. The downward continuation used 73600 below the prior low; the wider reversal condition was above 75700. The equity recovery mattered because it supplied a plausible force that could carry Bitcoin back through its own resistance rather than allowing the divergence to persist indefinitely."
 ],
 "scenarios": [
  "Base case — about 55% (Capital Chronicle model estimate, uncalibrated): Bitcoin stays below the 75512 area and revisits roughly 73654 within six sessions. The recorded conditions were the bounce zone at 75250–75340 or the distinct break at 73600. The owner kept the view conditional because the run had not established a named cause.",
  "Upside alternative — about 45% in the first analyst's scenario (Capital Chronicle model estimate, uncalibrated): an equity-led recovery and short covering take Bitcoin through 75512. The completed short-interval close above 75700 invalidates the plan. The critic retained the danger of a rebound after the already extended decline.",
  "A separate accelerated-downside case was not assigned its own probability. A break of the prior low would confirm continuation, while the nearby weekend low would still have to be confronted. The page does not invent a third chance or extend the frozen 73700 target to make the case look more attractive."
 ],
 "desk_process": [
  "The first analyst proposed a downward case from the lower highs and failure to join the equity recovery. The critic accepted that structure while preserving three weaknesses: no named cause, an extended decline and the possibility that a stronger equity market could lift Bitcoin. The owner kept the approximate 55% judgment and a conditional plan.",
  "The committee cited the lower-high sequence, the earlier low, the equity comparison and the desk's volatility context. Each was held before the decision cutoff. The original role outputs and exact geometry are bound to this page, while no later price action is used to rewrite what the desk knew then.",
  "The depth of the process lies in the distinction between observation and explanation. Relative weakness was observable; its underlying flow cause was unresolved. The final decision retained the structural test and the countercase instead of filling that gap with an unsupported narrative. The freeze time and fingerprint below identify that version."
 ]
}}


SUMMARIES = {
 'EURUSD': ['A shared dollar move, with the rates explanation challenged.', 'Relative policy mattered; no fresh rate differential proved the case.', 'Pullback 1.12010–1.12050; breakout 1.12270–1.12300; objective 1.12640.', 'Haven and energy channels remained interpretations.', 'Captured CPI consensus and dated CFTC positioning framed the risk.', 'Base 55%; downside alternative 35%; no invented third chance.', 'The critic reduced the first analyst\'s confidence; the owner kept the dissent.'],
 'XAUUSD': ['Prior dollar support contrasted with a gold-specific dip.', 'No new measured physical balance or fund-flow catalyst.', 'Support 4101–4104; breakout 4150; invalidation below 4079.', 'Competing haven channels; no verified event cause.', 'An extended advance made renewed confirmation important.', 'Base about 55%; first analyst\'s downside alternative about 45%.', 'The owner kept the critic\'s liquidation countercase.'],
 'USOIL': ['An accepted breakdown, with about 2.5 daily ATR already covered.', 'The case did not establish a new physical surplus.', 'Bounce 85.95–86.05; break 84.20; invalidation above 86.80.', 'Supply-risk transmission remained conditional.', 'The extended decline left room for a squeeze.', 'Base about 55%; first analyst\'s upside alternative about 45%.', 'Price structure survived review; an event cause was not established.'],
 'US500': ['The recovery held, while transmission remained mixed.', 'No new earnings revision or valuation multiple established.', 'Base 7500–7506; breakout 7584; invalidation below 7478.', 'Energy and risk appetite were conditional channels.', 'Much of the recovery was already in price.', 'Base about 55%; first analyst\'s downside alternative about 45%.', 'The owner kept both the structure and the critic\'s reversal risk.'],
 'BTCUSD': ['Bitcoin lagged the equity recovery.', 'No new confirmed flow explained the weakness.', 'Bounce 75250–75340; break 73600; invalidation above 75700.', 'No verified geopolitical cause was established.', 'An extended decline left short-covering risk.', 'Base about 55%; first analyst\'s upside alternative about 45%.', 'The owner kept the structural case and the unnamed-cause limitation.'],
}


def prepare():
    export = read_export()
    candidates = export['status']['plans']
    # Freeze the five plans selected at this item's entry. A later Main run
    # cannot silently rebind these already-authored original-view accounts.
    selected = {'EURUSD':'plan_a4e853272f83b1cca81ab1d1', 'XAUUSD':'plan_f45a45412d7fb675b4db238d',
                'USOIL':'plan_829c6d5505eb74877d962853', 'US500':'plan_79ec7bb46eb37b474f0f2c04',
                'BTCUSD':'plan_8b7c1dd880206079033b6efe'}
    results = []
    for symbol, text in TEXT.items():
        plan = next(p for p in candidates if p['plan_id'] == selected[symbol])
        run = pages.load_run(plan)
        combined = 'analysis-native.json' in run['documents']
        roles = run['documents']['analysis-native.json'] if combined else {
            'primary_analysis': run['documents']['primary-native.json'],
            'critical_review': run['documents']['critical-native.json'],
            'native_synthesis': run['documents']['owner-native.json']}
        cid = {'XAUUSD':'cand_macro_gold','USOIL':'cand_macro_wti','US500':'cand_macro_spx','BTCUSD':'cand_macro_btcusd','EURUSD':'cand_macro_eurusd'}[symbol]
        def references(role, array, fields):
            index = next(i for i,c in enumerate(roles[role][array]) if c['candidate_id'] == cid)
            filename = 'analysis-native.json' if combined else {'primary_analysis':'primary-native.json','critical_review':'critical-native.json','native_synthesis':'owner-native.json'}[role]
            prefix = '/' + role if combined else ''
            return [{'file':filename, 'pointer':f'{prefix}/{array}/{index}/{field}'} for field in fields if isinstance(roles[role][array][index].get(field), (str,int,float))]
        refs = references('primary_analysis','candidate_evaluations',['directional_thesis','mechanism_and_transmission','invalidation','material_counterevidence','next_observable_or_activation_trigger'])
        refs += references('critical_review','candidate_reviews',['rationale','dissent'])
        refs += references('native_synthesis','candidates',['rationale','invalidation','entry','stop_loss','take_profit','planned_exit_at_utc'])
        refs += [{'file':'final-decision-freeze.json','pointer':'/frozen_at_utc','transform':'ET'}]
        if symbol == 'EURUSD':
            refs += [{'file':'plan-geometry.json','pointer':'/symbols/EURUSD/atr'}]
        sections = {}
        for i,(key,_) in enumerate(pages.SECTIONS):
            sections[key] = {'paragraphs':[{'text':t, 'refs':refs,
                'rights':'CAPITAL_CHRONICLE_ORIGINAL_ANALYSIS', 'source_name':'Capital Chronicle original run analysis'} for t in text[key]],
                'summary':SUMMARIES[symbol][i]}
        manuscript = {k:text[k] for k in ('title','subtitle','introduction')}
        manuscript.update(plan_id=plan['plan_id'], registration_hash=plan['registration_hash'], sections=sections,
            authorship={'surface':'CODEX_EXEC', 'process_id':1960, 'configured_model':'gpt-6.1-sol', 'configured_effort':'max',
                        'evidence_state':'CONFIGURED_NOT_OBSERVED', 'preparation':'deterministic exact-run extraction; no X filtering needed',
                        'writer_and_editor':'same active native Codex run', 'new_editorial_model_calls':0})
        target = ROOT/'docs/publisher/CC-432/manuscripts'/f'{symbol}.json'
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(manuscript,ensure_ascii=False,indent=2),encoding='utf-8')
        folder = Path(r'A:\Capital Chronicle\Runtime\ContentOps\daily_app_outputs\owner-manual')/('plan-analysis-'+plan['plan_id'])
        packet = pages.render(plan,manuscript,output_dir=folder)
        results.append({'symbol':symbol,'plan_id':plan['plan_id'],'run_id':plan['run_id'],'folder':str(folder),
                        'paragraphs':len(packet['numeric_bindings']),'words':len(packet['native_payload']['body_markdown'].split())})
    return results


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(prepare(),indent=1))
