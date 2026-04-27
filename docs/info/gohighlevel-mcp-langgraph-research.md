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

