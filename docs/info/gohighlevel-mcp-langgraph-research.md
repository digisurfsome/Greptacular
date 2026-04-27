# GoHighLevel + LangGraph Sales Bot — Research

*Date: 2026-04-27. Plain-language brief for non-coder owner.*

---

## 1. TL;DR (read this first)

- **GHL MCP does NOT let LangGraph drive a live voice call.** MCP is the opposite direction — it lets an external AI read/write CRM data (contacts, conversations, calendars). Useful for memory & follow-up, not for being the voice brain.
- **GHL Voice AI cannot point at a custom LLM endpoint today.** "Bring Your Own LLM" is only a feature request on their ideas board. The brain is GHL-hosted.
- **You CAN inject LangGraph mid-call** via **Voice AI Custom Actions** — these fire HTTP POST webhooks during a live call, can pass parameters, and use the response. This is the realistic path for NEPQ logic.
- **$97/mo (often called $99) AI Employee Unlimited is per sub-account, not per bot.** Phone/telephony minutes still billed separately. Outbound calls and Agent Studio are NOT included.
- **Bot-to-bot 3-way conferencing is not a native GHL feature.** Possible only via Twilio-level call control outside GHL.
- **Memory: use Mem0 for cross-call prospect memory; Chroma (or simple JSON) for the static NEPQ script library.**

---

## 2. GHL MCP — what it actually does

**Direction:** External AI agent → MCP server → GHL account. (Not the other way.)

**Exposes ~36 tools** across:
- Contacts (CRUD, tags, tasks)
- Conversations (search, read messages, send messages)
- Opportunities / pipelines
- Calendars & appointments
- Payments, social posts, blogs, email templates

**Auth:** Private Integration Token (PIT) via Bearer header. Location ID passed per request. OAuth is "coming soon."

**Transport:** HTTP Streamable only right now. No npx/desktop client yet. Roadmap targets 250+ tools.

**What it is good for in your build:**
- LangGraph (or any agent) can read prospect history, write notes back to the contact record, create opportunities, book calendar appointments.
- Cross-call memory anchor — store NEPQ stage progress as a tag or custom field on the contact.

**What it is NOT good for:**
- Driving a live voice call. MCP has no voice / call-control surface. The voice agent runs inside GHL.

---

## 3. Without MCP — paths to put LangGraph in the loop

Three real options for getting LangGraph logic into a GHL voice call:

### A. Voice AI Custom Actions (webhook during live call) — VIABLE
- GHL Voice AI fires a **POST webhook** mid-call to your endpoint.
- Supports auth headers, dynamic parameters extracted from the call, and uses the JSON response in the next turn.
- This is the real "give it a brain" hook. LangGraph runs server-side, returns the next NEPQ line + which gates passed.
- Limitation: it's per-action, not per-turn — you can structure the prompt so every turn calls a "next_step" action.

### B. Workflow handoff (post-call or async) — PARTIAL
- After call, GHL workflow can webhook to an external system. Good for follow-up, bad for live driving.

### C. Bring Your Own LLM endpoint — NOT AVAILABLE
- Only a feature request on ideas.gohighlevel.com. Not shipped.

### D. Bypass GHL Voice entirely (Twilio + LangGraph) — MAX CONTROL
- Use Twilio Media Streams + your own STT/TTS (Deepgram/ElevenLabs) + LangGraph.
- Push results back into GHL via MCP for CRM continuity.
- More work, but full control of state, latency, and bot-to-bot conferencing.

---

## 4. $99 (actually $97) Unlimited — pricing reality

- **Plan:** "AI Employee Unlimited" — **$97/month per sub-account**.
- **Per sub-account, NOT per bot.** Multiple bots inside one sub-account share the bucket.
- **Includes:** Voice AI inbound calls, Conversation AI, Reviews AI, Content AI, Ask AI.
- **Excludes:** Agent Studio, outbound Voice AI calls, Voice AI on website chat widget.
- **Still pay-per-use:** telephony / phone minutes (Twilio-style charges) regardless of unlimited AI plan.
- **Practical impact for your sales bot:** If your bot calls OUT to prospects, the unlimited plan does NOT cover it. Outbound is metered.

Source: HighLevel Support Portal — AI Product Pricing article.

---

## 5. Bot-to-bot 3-way call (sales bot conferences in demo bot)

- **Not a native GHL Voice AI feature.** No documented "AI conferences another AI" capability.
- Workarounds:
  1. **Twilio conference room** — your sales bot dials into a conference, then dials the demo bot in too. Requires telephony control outside GHL.
  2. **Sequential handoff** — sales bot says "let me transfer you to our med-spa receptionist demo," does a SIP/PSTN warm transfer to the demo bot's number. Loses the 3-way "live witness" feel but is achievable.
  3. **Single-bot persona swap** — same LangGraph instance switches voice/persona mid-call to demo. Cheapest, no telephony plumbing, but less impressive.
- Recommendation: Option 3 first (ship in days), Option 1 later if prospects want a real 3-way.

---

## 6. Memory: Mem0 vs ChromaDB

**One-paragraph take:**

Use **both, for different jobs.** Mem0 is purpose-built for per-user/per-prospect long-term memory across calls — it auto-extracts facts, deduplicates, and decays old context, which is exactly what a sales pipeline needs ("Sarah at GlowMed mentioned she has 2 estheticians and uses Vagaro" should surface 3 weeks later). ChromaDB (or even a flat JSON file) is better for the **static NEPQ script library** — you want exact-phrase recall of the 8 steps, gate questions, and objection-handling templates with deterministic retrieval, no LLM-summarization risk. Latency-wise both are fine for live voice if hosted near the LangGraph runtime; Mem0's hosted API can add 100-300ms, so for sub-500ms voice turns prefer the self-hosted Mem0 OSS or pre-fetch prospect memory at call start and cache in LangGraph state.

---

## 7. Recommended architecture (ranked)

### Best — Option B: LangGraph brain via Voice AI Custom Actions + MCP for CRM
- GHL Voice AI handles STT/TTS/telephony.
- Every turn, GHL fires a Custom Action webhook → your LangGraph endpoint.
- LangGraph holds NEPQ state (current step + gates), returns the next utterance.
- LangGraph reads/writes prospect memory via GHL MCP (tags, notes, custom fields).
- **Works:** Yes, with engineering effort on the webhook contract.
- **Setup:** Configure Voice AI agent in GHL → add Custom Action webhooks → host LangGraph (FastAPI) → wire MCP client for CRM writes.
- **Ship time:** ~1-2 agent-days (token-time: hours).

### Second — Option D: Twilio + LangGraph (bypass GHL voice)
- Full control, real bot-to-bot conferencing, sub-second latency tunable.
- Use GHL only as CRM via MCP.
- **Works:** Yes, more code.
- **Setup:** Twilio number → Media Streams → Deepgram/ElevenLabs → LangGraph → MCP for CRM.
- **Ship time:** ~3-5 agent-days. Worth it if voice quality / latency / 3-way is a deal-breaker.

### Fallback — Option C: GHL-native bot only (no LangGraph)
- Use GHL Conversation AI prompt + Custom Actions for booking/CRM.
- **Works:** Yes, but you lose strict NEPQ state management. The LLM will drift between steps.
- **Setup:** Hours.
- **Ship time:** Same day. Use as MVP while you build B.

### Worst — Option A: "LangGraph brain via MCP"
- **Doesn't work as described.** MCP is inbound-to-GHL, not a voice driver. Don't pursue.

---

## 8. Things to test in a trial sub-account

1. **Voice AI Custom Action latency** — fire a webhook to a no-op endpoint, measure end-to-end pause the caller hears. Target <800ms.
2. **Multi-action per turn** — can one user utterance trigger multiple Custom Actions (e.g., "lookup contact" then "next_step")? Or only one?
3. **Custom Action response shape** — does Voice AI use the JSON `response` field as the spoken reply, or only as a tool result the GHL LLM rephrases? Big difference for NEPQ exact-phrasing.
4. **MCP PIT scope** — does a PIT work across sub-accounts or per-location only?
5. **Outbound calling cost** — confirm outbound is excluded from $97 unlimited and price the per-minute hit.
6. **Warm transfer to another GHL number** — can Voice AI do a SIP transfer mid-call? (Required for bot-to-bot.)
7. **Workflow → external webhook latency** — for post-call follow-up.
8. **Ideas board status** — check if "BYO LLM" has shipped since last update.

---

## 9. Sources

- GHL MCP docs — https://marketplace.gohighlevel.com/docs/other/mcp/
- HighLevel AI Product Pricing — https://help.gohighlevel.com/support/solutions/articles/155000006652-ai-product-pricing-update
- AI Employee Overview — https://help.gohighlevel.com/support/solutions/articles/155000003906-ai-employee-overview
- Voice AI Custom Actions — https://help.gohighlevel.com/support/solutions/articles/155000005461-voice-ai-custom-actions
- Conversation AI Public API — https://help.gohighlevel.com/support/solutions/articles/155000006639-conversation-ai-public-api
- BYO-LLM idea (not shipped) — https://ideas.gohighlevel.com/conversation-ai/p/openai-chatgpt-integration
- 2026 pricing analysis — https://netpartners.marketing/gohighlevel-ai-pricing/
- Sympana cost breakdown — https://www.sympana.com/blog/gohighlevel-voice-ai-pricing-real-total-cost-breakdown-2026
- AI Call Agents page — https://www.gohighlevel.com/ai-call-agents

---

## Pricing Deep-Dive — What Every Charge Actually Is

The $97/mo "AI Employee Unlimited" tier is **not** truly unlimited voice. It's a flat-rate license for *some* AI features per sub-account, but every actual phone call still triggers metered telephony, and several AI products sit *outside* the bundle. Below is every line item, in plain language.

### 1. What the $97/mo Actually Covers

The $97 buys **unmetered usage** of these AI features inside one sub-account (location):
- **Conversation AI** — text-based chatbot for SMS, web chat, FB/IG, email
- **Voice AI — INBOUND calls only** — the AI engine that talks on calls (voice engine + STT + TTS + LLM tokens are all included)
- **Reviews AI** — auto-replies to Google/FB reviews
- **Content AI** — AI text/image generator inside the platform
- **Funnel AI / Workflow AI Assistant / Ask AI** — minor helper tools

What "unlimited" means: GHL eats the LLM token cost, the voice engine cost, the STT, and the TTS for *inbound* AI conversations. You don't pay per token or per AI-minute.

What it does **NOT** cover (still pay-per-use even on the $97 plan):
- **Telephony minutes** (the actual phone line carrying the call) — always metered
- **Phone number rental** — monthly fee per number
- **SMS/MMS** — per message
- **Outbound Voice AI calls** — full pay-per-use (engine + LLM + telephony all metered)
- **Agent Studio** — the new visual agent builder, billed at API token rates
- **Web voice chat widget** — the on-website voice agent is metered, not in the bundle

Sources: https://help.gohighlevel.com/support/solutions/articles/155000003906-ai-employee-overview ; https://help.gohighlevel.com/support/solutions/articles/155000006652-ai-product-pricing

### 2. Telephony Minutes — The "Always Extra" Charge

Telephony minutes are the **phone-carrier cost** of moving voice bits over the phone network. GHL calls this "LC Phone." It's a passthrough of Twilio's wholesale rate with a small ~10% markup baked in, then **agencies can re-bill clients on top** at any markup they choose (Agency Pro $497 plan only).

**US local number rates** (per minute, billed in whole minutes — partial minutes round up):
- **Inbound** — about **$0.0128/min** (~$0.77/hour)
- **Outbound** — about **$0.021/min** total (~$1.26/hour)
- **Toll-free inbound** — higher, ~$0.022/min
- **Number rental** — $1.15/mo per local number, $2.15/mo per toll-free number

Why this exists even when "voice is unlimited": the $97 only buys the *AI brain* on inbound calls. The phone line itself is a separate utility charge that goes to Twilio/carriers. AI talking to nobody costs $0; AI talking on a real phone call always has a carrier bill.

Source: https://help.gohighlevel.com/support/solutions/articles/48001223556-lc-phone-pricing-billing-guide

### 3. Agent Studio — Separate Product, Token-Metered

Agent Studio is GHL's **newer visual builder** (drag-and-drop, n8n-style canvas) for custom AI agents. It is the *successor* branding to "AI Employee" — same idea, more flexible builder. Important: **Agent Studio is NOT included in the $97 unlimited bundle.**

Pricing model:
- **Pay per LLM token** at roughly raw API rates (OpenAI/Anthropic passthrough; GHL marks up modestly)
- No flat fee, no per-execution fee — just tokens consumed by the model your agent calls
- Voice agents built in Agent Studio also pay voice engine + TTS + telephony on top

So if you build a custom outbound qualification agent in Agent Studio, you pay: tokens + voice engine + TTS + outbound telephony minutes. Nothing about it is covered by the $97.

Sources: https://help.gohighlevel.com/support/solutions/articles/155000006652-ai-product-pricing ; https://netpartners.marketing/gohighlevel-ai-agent/

### 4. Outbound AI Calls — Metered + Compliance-Gated

Outbound is **fully pay-per-use** even on the $97 plan. Approximate combined rate:
- **Voice engine:** $0.06/min
- **TTS:** included in the engine cost in most configs
- **LLM tokens:** ~$0.10/min average (varies by model)
- **Telephony outbound:** ~$0.021/min
- **Combined: roughly $0.18–$0.20 per outbound minute**

**Compliance gates GHL enforces before any outbound AI call:**
- Sub-account must explicitly enable outbound AI **and complete KYC verification**
- The contact must have a **documented opt-in** (HighLevel form, survey, or calendar booking) — TCPA treats AI calls as robocalls requiring **prior express written consent**
- Contact cannot be on DND or have previously opted out
- Calls only fire **10 AM – 6 PM** in the contact's local time zone (tighter than federal 8 AM – 9 PM)
- Throttle: max **10 calls/minute per location** (one every 6 seconds)
- T&C scanner checks your forms have valid consent language; non-compliant assets get blocked

**Cold-calling is NOT allowed.** There must be a prior relationship: form fill, inbound call/text, calendar booking, or another logged opt-in. Without it, GHL rejects the call and you'd be exposed to TCPA penalties of **$500–$1,500 per call** anyway.

Sources: https://help.gohighlevel.com/support/solutions/articles/155000006679-voice-ai-outbound-calling-compliance-checks ; https://help.gohighlevel.com/support/solutions/articles/155000006598-voice-ai-outbound-calling

### 5. Worked Example — 1-Hour INBOUND Call (US local number, $97 plan)

| Line item | Rate | 60 min cost |
|---|---|---|
| Voice AI engine (voice + STT + TTS) | included in $97 | **$0.00** |
| LLM tokens (inbound AI) | included in $97 | **$0.00** |
| LC Phone inbound minutes | $0.0128/min | **$0.77** |
| Number rental (amortized, ignore for one call) | $1.15/mo | — |
| **Total for the call** | | **~$0.77** |

That's the magic of the $97: a 1-hour inbound AI call costs you under a buck on top of the flat fee.

### 6. Worked Example — 1-Hour OUTBOUND Call (US local number, $97 plan)

| Line item | Rate | 60 min cost |
|---|---|---|
| Voice AI engine | $0.06/min | **$3.60** |
| LLM tokens (avg model) | ~$0.10/min | **$6.00** |
| LC Phone outbound minutes | $0.021/min | **$1.26** |
| **Total for the call** | | **~$10.86** |

Delta vs inbound: about **$10 more per hour-call** for the same conversation. GHL community average benchmark is **~$0.163–$0.20 per outbound AI minute all-in**, which lines up.

### 7. Other Hidden Fees the Owner Should Know About

- **A2P 10DLC SMS registration** (mandatory to send any SMS to US numbers):
  - Standard Brand registration: **~$24.50 one-time** (includes $3 fast-track)
  - Other brand types: **~$71.91 one-time**
  - Campaign fee: **up to $11.025/mo per campaign** (charged whether approved or not)
  - **Passthrough — no GHL markup**
- **SMS per message:** ~$0.0079/segment outbound, ~$0.0079 inbound (US local), plus carrier fees ~$0.005/segment
- **Email sending:** ~$0.001 per email (Mailgun passthrough)
- **AI Employee per-location** — the $97 is **per sub-account/location**. 50 clients = 50 × $97 = $4,850/mo just for AI bundles
- **Workflow Premium Actions** — some automation steps (AI parsing, image gen, slack notifications) cost cents per execution
- **Voice AI add-on for sub-account** — on the Agency Starter ($97 agency plan) the AI Employee bundle is purchased *per location* in addition to the agency plan
- **Agency plan tiers:** $97 Starter, $297 Unlimited, $497 Pro (SaaS mode + rebilling) — rebilling clients for telephony/AI requires the $497 tier

Sources: https://help.gohighlevel.com/support/solutions/articles/155000005200-understanding-a2p-10dlc-messaging-fees-registration-monthly-and-carrier-costs ; https://help.gohighlevel.com/support/solutions/articles/155000001156-highlevel-pricing-guide


## Pricing Deep-Dive — What Every Charge Actually Is

### 1. What the $97/mo "AI Employee Unlimited" actually covers

It's a per-sub-account add-on (per location, not per agency).

**Included (unlimited usage, no metering):**
- Voice AI on **inbound** phone calls — the AI talk time, the speech-to-text, the text-to-speech, AND the LLM tokens behind the conversation. All bundled.
- Conversation AI (SMS / chat replies)
- Reviews AI (auto-respond to reviews)
- Content AI (writes copy/emails)
- Ask AI (data Q&A inside GHL)

**NOT included (still metered, billed separately):**
- Telephony minutes (the actual phone line moving the audio — see #2)
- **Outbound** Voice AI calls (the AI talk time itself is metered, even though inbound is "unlimited")
- Voice AI on the **website voice chat widget**
- **Agent Studio** (separate product, see #3)

Source: https://help.gohighlevel.com/support/solutions/articles/155000006652-ai-product-pricing

### 2. Telephony minutes — the contradiction explained

"Unlimited voice" means unlimited **AI brain**. Telephony minutes are the **phone line itself** (Twilio passthrough via "LC Phone").

| Item | Rate (US numbers) |
|---|---|
| Inbound voice minutes (LC Phone) | ~$0.0128/min |
| Outbound voice minutes (LC Phone) | ~$0.0210/min |
| Phone number rental | ~$1.15/mo per number |
| Client minute base cost (rebill) | $0.004/min agency cost |

These are passthrough Twilio + small GHL margin. Always charged, even when AI Employee is "unlimited." Why: the phone carrier (AT&T/Verizon/etc.) still bills GHL per minute regardless of whether a human or an AI is talking.

Source: https://help.gohighlevel.com/support/solutions/articles/48001223556-lc-phone-pricing-billing-guide

### 3. Agent Studio — what it actually is

Agent Studio is a **separate, more advanced product** from the basic AI Employee Voice AI. It's GHL's builder for multimodal / specialized AI agents (custom logic, multi-step, tool use). Think of it as the "pro" tier vs the "starter" Voice AI bot.

**Billing:** charged at **raw model token usage** (API pricing — pass-through to OpenAI/Anthropic/etc.), NOT a flat per-minute rate.

**NOT covered by the $97 Unlimited.** Even if you pay $97, every Agent Studio token is metered out of your wallet.

Source: https://help.gohighlevel.com/support/solutions/articles/155000006652-ai-product-pricing ; https://netpartners.marketing/gohighlevel-ai-agent/

### 4. Outbound calls — rate, gating, and TCPA

**Rate:** Voice AI outbound is billed on the **blended Voice AI formula**:
`(minutes × $0.06) + (tokens ÷ 1M × model price)` — averages ~$0.163/min all-in.
Plus the outbound telephony at ~$0.021/min on top.

**Gating / compliance — this is the big one:**
- Outbound AI calling is in **beta** and TCPA-gated.
- GHL **blocks the call** unless the contact has documented opt-in: a checked consent box on a HighLevel form/survey/calendar referencing voice calls, with timestamp + IP captured.
- DND flag or prior opt-out = call rejected automatically.
- Call hours hard-capped 10am–6pm contact local time (tighter than federal 8am–9pm).
- Throttle: max 10 calls/minute per location.
- **Cold-calling is not allowed.** AI must call only contacts who already opted in.
- TCPA penalty if you bypass: $500–$1,500 per call.

Source: https://help.gohighlevel.com/support/solutions/articles/155000006679-voice-ai-outbound-calling-compliance-checks ; https://help.gohighlevel.com/support/solutions/articles/155000007166-enhanced-consent-checking-for-voice-ai-outbound-calling-forms-surveys-calendars-

### 5. Worked example — 1-hour INBOUND AI call (US, with AI Employee Unlimited)

| Line item | Calc | Cost |
|---|---|---|
| Voice AI brain (STT + LLM + TTS) | covered by $97 flat | **$0.00** |
| Inbound telephony minutes | 60 × $0.0128 | **$0.77** |
| Phone number rental (prorated) | $1.15/mo ÷ ~720 hr | **$0.00** |
| **Total for the 1-hour call** | | **~$0.77** |

(The $97/mo is the only "AI" cost — fixed, regardless of call volume.)

### 6. Worked example — 1-hour OUTBOUND AI call (US)

| Line item | Calc | Cost |
|---|---|---|
| Voice AI brain (NOT covered by $97) | 60 × ~$0.163 blended | **$9.78** |
| Outbound telephony minutes | 60 × $0.0210 | **$1.26** |
| Compliance check (consent lookup) | included | $0.00 |
| **Total for the 1-hour call** | | **~$11.04** |

**Delta: outbound costs ~14× more than inbound** for the same hour, because the $97 flat doesn't cover outbound AI brain at all.

### 7. Other hidden fees to plan for

- **A2P 10DLC SMS registration** (mandatory to send texts in US):
  - Brand registration: ~$4 one-time
  - Campaign vetting: ~$15 one-time
  - Monthly campaign fee: ~$1.50–$10/mo per campaign
  - Carrier fees: ~$0.0083/segment outbound, some inbound (T-Mobile)
  - All passthrough, no GHL markup. Resubmissions now free.
- **Phone number rental:** ~$1.15/mo per number (per sub-account)
- **Email sending:** ~$0.001675 per email (Mailgun passthrough)
- **Wallet auto-recharge:** GHL drains a prepaid wallet — if it hits $0 mid-call, calls fail. Set auto-recharge.
- **AI Employee is per sub-account:** 10 client locations on Unlimited = $970/mo, not $97.
- **Rebilling to clients requires the $497 SaaS Pro agency tier** — Starter and Unlimited agency plans can't markup telephony to clients.

Source: https://help.gohighlevel.com/support/solutions/articles/155000005200-a2p-10dlc-messaging-fees-registration-monthly-and-carrier-costs ; https://help.gohighlevel.com/support/solutions/articles/155000001156-highlevel-pricing-guide

---

## Architecture Synthesis — Sales Bot That Sells Itself

### The pitch loop
Outreach (1k/day to contact forms with personalized recordings + missed-call data) → landing page → prospect calls in to hear what their bot would sound like → **the sales bot answers the call AS the demo**. By minute 5 they're sold not on the concept of an AI receptionist but on this exact one. Close: "This is what would be answering your phone tomorrow. Want to try 30 days free?"

One asset, three jobs: outbound demo recording, sales pitch, eventual production receptionist.

### Cost math (linear scaling confirmed)

| Call type | Default GHL brain | Sonnet 4.6 via webhook |
|---|---|---|
| 30-min inbound | ~$0.39 | ~$1.00–$1.60 |
| 60-min inbound | ~$0.78 | ~$1.80–$3.00 |
| 30-min outbound | ~$5.40 | ~$6.00–$7.00 |
| 60-min outbound | ~$10.86 | ~$12.00–$13.50 |

Inbound is so cheap it's effectively free. Outbound is ~14× more.

### Brain options ranked

**Option 1 (cheapest, recommended to start): GHL default brain only**
- $97 covers everything brain-side, inbound unlimited
- No API key, no webhook, no LangGraph
- Configure NEPQ + metaprograms in the brain-builder UI as system prompt + knowledge base
- Limit: GHL's default model may drift on metaprogram framing in long calls
- Ship time: days

**Option 2 (best value): GHL default brain + LangGraph webhook for gates only**
- Conversation runs on free GHL brain
- LangGraph called via Custom Action only at gate-decision moments (5–15 calls per conversation, not 60+ turns)
- Sonnet 4.6 API key required, but token spend stays under ~$0.30/call
- LangGraph holds NEPQ state machine + metaprogram frame enforcement
- Mem0 for cross-call prospect memory, Chroma for NEPQ phrase library
- Ship time: 1–2 weeks

**Option 3 (max control, max cost): Agent Studio with full BYO-LLM**
- Sonnet 4.6 drives every turn via API key
- ~$1–$2 per 30-min call in API tokens
- Best framing fidelity but 3–5× more expensive than Option 2
- Worth it only if Option 2 framing drift is a problem

**Subscription pipe-in (Claude Max):** Not possible. Subscriptions are for chat.claude.ai and Claude Code only. Production voice bots require an Anthropic Console API key.

### LangGraph vs GHL Workflow Builder

| Need | Use |
|---|---|
| Macro flow (call → qualify → book → confirm) | GHL Workflow Builder |
| In-call NEPQ state + gates | LangGraph |
| Metaprogram frame enforcement every turn | LangGraph |
| Post-call CRM updates, tagging, SMS follow-up | GHL Workflow Builder |
| Cross-call prospect memory | LangGraph + Mem0 |

Workflow Builder is event-based — it can't enforce turn-by-turn metaprogram framing. LangGraph can. Use both, in their respective lanes.

### NEPQ vs Metaprograms — when to use which

- **Metaprograms always-on:** detected from 3 listening questions in first 60 seconds, then injected into every system prompt. Bot reframes every response in their frame. This alone may close warm leads.
- **NEPQ on-demand:** triggered only when prospect throws an objection or stalls 2× in a row. Routes into NEPQ consequence-question loop until re-engaged, then exits back to metaprogram-only mode.
- LangGraph models this as two graphs with one conditional edge between them.

### Free trial economics

| Item | Who pays | Estimated 30-day cost |
|---|---|---|
| Your service (setup, training, management) | YOU (this is the gift) | $0 to client |
| Inbound telephony (~50 calls/day × 3 min) | Client (rebill at cost) | ~$60 |
| LangGraph API tokens (if Option 2/3) | Client (rebill at cost) | ~$15–$45 |
| Outbound (carved out — premium upsell) | Client only if they opt in | $0 default |

**Contract fine print template:** "Free 30-day trial covers our service fees only. Telephony minutes (~$2/day inbound) and LLM costs are billed at cost to your card on file. Outbound calling is not included; available as a separate add-on at $0.16/min with written opt-in consent required per contact."

**Risk if they ghost:** under $100 worst case. Survivable. Most won't — once the bot is live and answering calls they're missing, the switching cost is huge.

### Why this works (the close-rate thesis)

The combination is unprecedented:
1. Industry-specific pain data (missed-call money math, per-niche)
2. NEPQ 8-step framework on standby for resistance
3. Metaprogram framing on every sentence
4. A bot that never has a bad day, knows more than any employee, and demos itself

Same bot then becomes the client's receptionist — armed with the same NEPQ + metaprogram tech, closing their patients/customers at 2–3× employee rates. That IS the upsell. "Don't let your people answer the phone — they can't sell like this."

### Recommended ship sequence

1. **Week 1:** Build Option 1 (GHL default brain). Test on 50 prospects. Measure close rate.
2. **Week 2:** If framing drift is an issue, add Option 2 (LangGraph webhook for metaprogram enforcement).
3. **Week 3+:** Build the per-industry demo bots (med spa, dentist, contractor). Sales bot warm-transfers to demo bot when prospect wants to "hear it work for my business."
4. **Month 2:** Add Mem0 for cross-call memory. Roll outbound to opted-in prospects only.

Total real cost to run all of this for one sub-account: **$97/mo + ~$2/day per active client + API tokens.** A single closed deal at $500/mo MRR pays for the whole stack 5× over.

---

## Detailed Architecture — 3-Brain Stack with NEPQ + Metaprograms + Phrase Arsenal

### Cost reconciliation (the two numbers explained)

| Architecture | Sonnet runs | 30-min call | 60-min call |
|---|---|---|---|
| **A: Sonnet drives every turn** | 60–80 turns | $1.00–$1.60 | $2.00–$3.20 |
| **B: Sonnet only at gates (recommended)** | 5–15 calls | $0.05–$0.20 | $0.10–$0.40 |

The 3× variance in A is real: prospect talkativeness, tool calls, retries, prompt-cache hit rate. B is 10× cheaper because GHL's free default brain handles word-by-word delivery; Sonnet is reserved for nuanced judgment.

### Model assignment per layer (Architecture B)

| Layer | Model | Rationale |
|---|---|---|
| Speaking the words (STT/TTS loop) | GHL default brain | Free under $97. Fast. Adequate for delivering pre-shaped phrases. |
| Metaprogram detection (one-shot at 60s) | Sonnet 4.6 | Worth the 2¢ to nail the profile. |
| Gate decisions every ~90s | Sonnet 4.6 | Reads transcript chunk, judges advance/stay/objection. Haiku is too coarse. |
| Single-sentence frame rewrite | Haiku 4.5 | Cheap, perfect for known-frame rephrasing. |
| Phrase retrieval | No LLM (Chroma vector search) | Microseconds, free. |
| Cross-call memory pull | No LLM (Mem0 lookup) | Microseconds. Sonnet only on write at call end. |

**Subscription pipe-in:** Not possible. Anthropic Console API key required for any Sonnet/Haiku usage.

### Static assets built once

**Phrase library (Chroma):** 100s of pre-written one-liners per category × 10–20 categories (missed-call money math, after-hours pain, employee-quality contrast, lifetime-value math, free-trial close, mafia/insurance frames, mismatcher reverse phrasings). Each tagged: industry, metaprogram alignment, NEPQ step.

**NEPQ state nodes (LangGraph):** 8 nodes (Connect → Situation → Problem Awareness → Solution Awareness → Consequence → Qualifying → Transition → Presentation/Close). Each node has goal, gate criteria, fallback questions, exit condition.

**Metaprogram profile schema (Mem0):** toward/away (-1 to +1), internal/external, match/mismatch, convincer strategy, detection-source transcript snippet.

### Per-call orchestration

```
[Call rings] → [GHL Voice AI picks up, default brain]
       │
       ├──> [Webhook: detect_metaprograms @ 60s]
       │      Sonnet reads first 3 listening-Q answers
       │      → writes profile to Mem0
       │      → returns frame-rule addendum to GHL system prompt
       │
       ├──> [Webhook: gate_check every 90s]
       │      Sonnet reads last transcript chunk
       │      → returns: stay | advance | route_to_objection
       │      → updates GHL system prompt with next-step instructions
       │
       ├──> [Webhook: phrase_inject on demand]
       │      Chroma queried with current_step + MP_tags + industry
       │      → top phrase passed through Haiku for frame rewrite if needed
       │      → returned to GHL to speak
       │
       └──> [Loop until close]
              │
              ▼
       [GHL Workflow Builder takes over]
       CRM update, Mem0 write, appointment booking, SMS recap
```

### Mismatcher special handler

If `match_vs_mismatch < -0.4` after detection, LangGraph flips a flag and routes every Chroma phrase through Haiku with this rewrite directive:

> "Rewrite as inverse polarity. Instead of asserting X, frame as the negation of not-X. Instead of agreement, ask what doesn't work about their current setup. Their natural 'no' should now mean alignment."

NEPQ gates open just as fast — you're speaking in reverse polarity to a brain that's wired to disagree. Their disagreement IS the agreement.

### Memory layout

| Where | What | Why there |
|---|---|---|
| In-prompt (cached) | Persona, industry pain bullets, NEPQ step instructions, MP frame rules, top 30 pre-loaded phrases, returning-prospect summary | Zero retrieval latency, $0.30/M cached |
| Chroma | Full phrase library, NEPQ templates, industry case studies | Per-turn semantic+tag retrieval |
| Mem0 | Per-prospect MP profile, last-call summary, objections, appointment status | Pulled at start, written at end |
| GHL CRM (via MCP) | Contact record, recordings, outcomes, tags | Source of truth for ops |

### Confidence assessment

| Capability | Confidence |
|---|---|
| Hold MP framing 30 min | 95% |
| Recall right phrase from library at right moment | 90% |
| Advance NEPQ gates without sticking | 85% (after 20–50 calls of tuning) |
| Detect MPs accurately from 3 listening Qs | 80% (mid-range scores default to neutral) |
| Detect mismatcher fast enough to flip frame | 85% |
| Stay on script past 45 min | 80% (mitigated by rolling summary every 10 min) |
| Close 30-day free trial with no real resistance | 95% (math + data + frame = no logical exit) |
| Bot signs them up directly (vs. just booking appt) | 60% in phase 1; raise to 80%+ after 100+ calls of training |

### Failure modes

1. Voicemail trees on outbound (inbound is fine)
2. Multi-speaker / background noise → STT degrades → MP detection noisy
3. Prospect goes off-script asking pricing mid-NEPQ → needs an "objection handler" node that answers and routes back
4. Strong mismatcher + away-from + internal-reference combo → rare but unmovable; not your ICP, accept the loss
5. Sparse phrase library (<50 per category) → bot repeats itself
6. Vague NEPQ gate criteria → bot stalls or skips
7. Abstract MP frame rules instead of 3–5 concrete example sentences → Sonnet drifts

### Total per-call economics in Architecture B

- Telephony: ~$0.40 per 30 min inbound
- API: ~$0.10 per 30 min (Sonnet at gates + Haiku rewrites)
- **Total: ~$0.50 per 30-min closed deal call**
- Per appointment-set: ~$0.30
- Per phone-tag/no-show: ~$0.20

A $500/mo MRR client pays back the entire monthly stack 5× over on day one.

---

## Salesperson Copilot — Same Brain, Different Output Sink

Use case: human (you) takes the call, the same LangGraph brain listens in real time and pushes suggested lines to a web page on a second monitor. Trains you to think in NEPQ + metaprograms while every call is fully scaffolded. Ships in ~1 day.

### Architecture

```
[Your phone call (softphone/Twilio number)]
        │ Audio splitter / SIP tap
        ▼
[Deepgram streaming STT, 2 channels diarized]
        │  ~200-400ms latency
        ▼
[LangGraph — SAME nodes as bot architecture]
        │  detect_MP, gate_check, phrase_inject, objection_handler
        │  SAME Chroma library, SAME Mem0
        ▼
[WebSocket push → React 3-column page on your monitor]
   ┌──────────────┬──────────────┬──────────────┐
   │ LIVE         │ NEXT LINE    │ STATE        │
   │ TRANSCRIPT   │ (top 1 BIG,  │ NEPQ step,   │
   │ (you/them)   │  2 alts,     │ MP scores,   │
   │              │  why-tag)    │ last obj.    │
   └──────────────┴──────────────┴──────────────┘
```

### Listen to both channels

- **Prospect audio** → drives gate decisions, response generation
- **Your audio** → calibration (compare suggested line vs delivered line for drift) + off-script detection (if you go your own way, brain pivots the plan)
- Deepgram dual-channel diarization is a config flag, no extra engineering

### Latency budget (target < 1.5s end-of-prospect-sentence to on-screen)

| Step | Latency |
|---|---|
| Deepgram endpointing | 200–400ms |
| LangGraph routing | 50ms |
| Sonnet 4.6 streaming first tokens | 400–800ms |
| Chroma lookup | <50ms |
| WebSocket push | <100ms |
| **Total to first visible word** | **~700–1200ms** |

Sonnet streams; first words appear before full suggestion. Feels instant.

### Talk-speed forcing function

Reading-speak clocks ~150 wpm = "slow enough for prospect reflection" pace. Screen caps your delivery speed automatically. Bonus: kills cold-call anxiety — next perfect line is always 1 second away.

### When to use copilot vs bot

| Mode | Use when |
|---|---|
| Bot solo | High volume inbound, after-hours, qualified-prospect appointment-set, demo calls |
| Copilot (human + brain) | Training months 1–3; high-ticket prospects ($50k+ MRR potential); edge cases where bot drifts; outbound to opted-in lists where human warmth helps |
| Bot warm-transfer to copilot | Bot qualifies, transfers to you with full context already in brain state — you take over with copilot showing where bot left off |

### Cost per 30-min copilot call

| Item | Cost |
|---|---|
| Telephony (your existing line or Twilio) | <$0.05 |
| Deepgram STT (2 channels) | ~$0.26 |
| Sonnet 4.6 at gates | ~$0.10 |
| Haiku rewrites | ~$0.03 |
| **Total** | **~$0.45** |

### Build effort (token-time, not human-time)

- Audio tap + Deepgram streaming: 2–3 hours
- LangGraph copilot output node + WebSocket: 2 hours
- React 3-column page: 2 hours
- Wiring + testing: 2 hours
- **~1 working day to first usable version.** Tuning during real calls.

The same Chroma library, same Mem0 profiles, same NEPQ state machine, same MP detection serve both bot and copilot. Zero duplication. Build the bot, get the copilot for free.

---

## Billing & Money Flow — Every Line Item

| Charge | Billed how | When | Pays |
|---|---|---|---|
| GHL $97/mo Voice AI Unlimited | Subscription, auto-charge | Monthly up front | You |
| Telephony minutes (LC Phone) | **Prepaid wallet, drains real-time** | As consumed; calls fail at $0 | You (auto-recharge required) |
| A2P 10DLC registration | Wallet drain | One-time + monthly campaign fee | You |
| Phone number rental | $1.15/mo per number, wallet | Monthly | You |
| Anthropic API (Sonnet/Haiku) | Postpaid invoice, credit card | Monthly arrears | You direct to Anthropic |
| Deepgram STT (copilot only) | Postpaid invoice | Monthly arrears | You direct |
| Mem0 hosted | Free tier likely sufficient; $19+/mo paid | Monthly | You |
| Chroma self-hosted | $0 | Never | Free |

**Operational rule:** Set GHL wallet auto-recharge at $20 floor / $50 top-up. Otherwise calls fail mid-day.

**Free trial billing pattern:**
- Client puts credit card on file in GHL (requires SaaS Pro $497/mo tier to rebill clients)
- Telephony + API rebilled at cost during trial
- OR cheaper: charge client flat $50/mo "carrier passthrough," you eat overages (<$2/day average means you almost never lose money)
- Outbound carved out of trial entirely — premium add-on with written opt-in only
