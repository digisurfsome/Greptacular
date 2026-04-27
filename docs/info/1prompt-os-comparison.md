# 1prompt-os Repo Analysis — Adopt, Hybrid, or Learn?

> Companion doc to `gohighlevel-mcp-langgraph-research.md`. Investigates whether to adopt or borrow from the open-source `genokadzin/1prompt-os` GHL appointment-setter project.

## TL;DR

- **Repo:** https://github.com/genokadzin/1prompt-os (MIT)
- **Framing was wrong:** It's primarily SMS/Instagram/Facebook DM auto-reply, not voice. Retell is bolted on as a small outbound task.
- **Stack:** GHL + Supabase + Trigger.dev + n8n + OpenRouter (NOT GHL + n8n + Retell + Supabase as advertised).
- **Verdict: Don't fork. Steal 6 patterns. Add a small Supabase for orchestration state.**
- **Reactivation magic:** Mostly a generic drip sequencer + GHL smart lists. Not proprietary IP.

## Stack — what each component does

| Component | Role |
|---|---|
| GoHighLevel | CRM + inbound webhook source + the channel that sends the SMS/DM reply |
| Supabase | Master DB + Edge Functions; receives GHL webhook, validates client, queues messages, stores everything |
| Trigger.dev | Background job runner; debounce, follow-up timers, workflow execution, outbound-call dispatch |
| n8n | The "brain"; receives grouped messages as query params, pulls history + setter prompt from client Supabase, calls OpenRouter, returns Message_1 / Message_2 |
| OpenRouter | LLM gateway (model-agnostic) |
| Retell | Optional outbound voice via `placeOutboundCall` task; brain there is just `custom_instructions` + `contact_fields` |

End-to-end inbound DM flow:
```
GHL webhook → Supabase Edge Fn → Trigger.dev debounce (wait.until)
   → n8n (history + prompt + OpenRouter) → reply webhook to GHL → SMS/DM sent
```

## Brain-swap feasibility

- **Possible:** n8n is just an HTTP-callable LLM box. Same in/out contract (history + prompt → reply text). LangGraph webhook can replace it.
- **Stays:** Supabase schema, Trigger.dev debounce, follow-up timers, GHL webhook plumbing, React dashboard.
- **Changes:** n8n workflow → LangGraph; OpenRouter → Anthropic.
- **Hidden cost:** Inherit 3 ops surfaces (Trigger.dev, Supabase platform DB, React dashboard) for capabilities a voice-first product only half-uses.

## What their Supabase stores

**Platform DB:** `clients`, `agent_settings`, `message_queue`, `dm_executions`, `followup_timers`, `ai_generation_jobs`.

**Per-client DB:** `leads` (keyed to GHL Contact_ID), `chat_history` (LangChain JSONB), `text_prompts` (setter system prompts).

## Do we need our own DB?

For voice-first GHL Voice AI + LangGraph + Mem0 + Chroma:

| State type | Where it lives in our build |
|---|---|
| Live conversation memory | In-prompt + Mem0 |
| Phrase library | Chroma |
| Contact + appointment state | GHL CRM (via MCP) |
| Per-prospect MP profile | Mem0 |
| **Orchestration state (drip timers, batch claims, sequence resume, idempotency)** | **Small Postgres/Supabase needed** |

Conclusion: yes, we want Supabase, but **only for orchestration state**, not conversation. ~5-8 tables, free tier covers it for a long time.

## The 6 patterns to steal

1. **Drip-batch claim RPC** — atomic claim ("next N leads to call this hour") so 500-lead reactivation lists don't all fire at once.
2. **AI-judged follow-up JSON contract** — `{should_followup, reason, message}` with per-client cancellation rules.
3. **Resume-by-node-index** — outbound sequences survive crashes without double-calling. Critical for voice retries.
4. **Reply-detection auto-cancel** — lead replies (text or voice) → kill the sequence automatically.
5. **Timezone-aware business-hours gating** — never call at 6am local. TCPA-adjacent.
6. **Per-setter prompt table** — A/B test NEPQ personas without code deploys.

## Reactivation use case — the truth

There's no dedicated "DB reactivation" code. What exists:

- `runEngagement.ts` — generic outbound sequencer with drip batching, timezone gating, reply-stop, resume.
- `sendFollowup.ts` — AI decides whether/when to follow up.
- **Lead selection lives upstream in GHL smart lists**, not in the repo.

The "reactivation magic" = **GHL smart list → loop → generic drip sequencer**. Pattern, not proprietary IP.

## Recommendation

**Don't fork. Build clean.** Steal the 6 patterns into our PRD. Add a small Supabase for orchestration state. Use their existence as proof the GHL+webhook architecture is production-grade.

## Pairs with the commission-only real estate play

Same brain, two pitches:
- **Receptionist:** flat $497/mo, inbound coverage. Land local businesses fast.
- **Reactivation:** zero up-front, 10-25% of close commission. High-end real estate agents with stale CRM dumps.

Order: ship receptionist first → build case studies → use receptionist customer base as proof for high-margin reactivation deals.

---

## Multi-Channel Brain — Voice + Chat + SMS All on One Engine

The same LangGraph brain (NEPQ + MP + phrase library + Mem0 keyed by phone) drives three output channels:

```
LangGraph brain
  ├─ Voice (GHL Voice AI)        — live demo + close
  ├─ Web chat (landing page)     — first sell, ~$0.05/session
  └─ SMS / iMessage              — async nurture + handoffs
```

Cross-channel handoff (Mem0 keyed to phone or email):

| From → To | Mechanism |
|---|---|
| Web chat → voice | Chat collects phone, GHL outbound trigger, voice loads chat history |
| SMS → voice | Bot texts a number to call, inbound matches by phone, voice loads SMS thread |
| Voice → SMS | Call ends, GHL workflow fires recap SMS |
| Voice → web chat | Bot SMS's a personalized landing page link, chat resumes from where call ended |

Cost per first-touch engagement:

| Channel | Cost per session |
|---|---|
| Web chat (30 min) | ~$0.05 |
| SMS thread | ~$0.10 |
| Voice (30 min) | ~$0.50 |

Funnel:
```
1k contact-form msgs → 200 page views → 40 chat engagements
     → 12 voice demos → 3 closes/day @ $497 MRR
     = ~$1,491/mo new MRR per day of outreach
```

## A2P 10DLC + TCPA — The Actual Rules

| Activity | A2P needed? | TCPA exposure |
|---|---|---|
| Inbound voice calls | NO | None (they called you) |
| Outbound voice (AI auto-dialer) | NO A2P | YES — needs prior express consent |
| Outbound SMS (US carriers) | YES | YES |
| Inbound SMS replies | Practically yes (deliverability) | None |
| iMessage / Sendblue P2P | NO | TCPA still applies |
| Contact form submissions | N/A | None — they published the form |

**"Spam Likely" caller ID** is separate from A2P: caused by STIR/SHAKEN attestation, outbound volume, complaint rate, short calls. Mitigate with **CNAM registration** (~$5/mo, sets caller ID name to your business). Inbound-only avoids this entirely.

## Sendblue Verdict

YC-backed iMessage-for-business service, real bypass of carrier A2P 10DLC by routing through Apple's iMessage infrastructure. ~$29/mo per dedicated line, real GHL Marketplace integration.

**The trap:** Bypasses **carrier compliance** (A2P), NOT **legal compliance** (TCPA). Per TCPAWorld 2025: "P2P literally does NOTHING to protect a business in a TCPA case." Cold-texting unconsented leads = $500–$1,500/message statutory damages.

**Platform risk:** Apple rate-limits ~50–200 msgs/day/line for "natural pacing." Multiple lines required for scale. No formal Apple blessing — could tighten any quarter.

**How to use it correctly:**
- ✅ Warm/opted-in lead nurture after they've engaged
- ❌ Cold blasts to scraped lists (legal exposure unchanged)
- ❌ Lead-source replacement for the front of the funnel

**Recommended SMS path:** Start with **Sole Prop A2P 10DLC** ($24.50 + $11/mo, 1-3 day approval, uses SSN not EIN, no business license required). Legally clean. Add Sendblue later as an opted-in nurture optimization if volume justifies.

## Recommended Channel Plan

| Stage | Channel | Regulation |
|---|---|---|
| Cold outreach (1k/day) | Contact form submissions | None — public form, they invited it |
| Warm conversion | Custom landing page + chat bot | None — your property |
| Live close | Inbound voice call | None — they call you |
| Post-engagement nurture | Sole Prop A2P SMS or Sendblue (if opted in) | A2P + TCPA cleared by opt-in |
| Outbound voice (later premium tier) | GHL outbound with documented consent | TCPA cleared by opt-in |

## 24–48 Hour Ship Path (No Business License)

| Item | Time | Blocked by license? |
|---|---|---|
| GHL sub-account + Voice AI | 1 hr | No |
| Buy 1 phone number | 5 min | No |
| Inbound voice bot configured | 4–8 hrs | No |
| Custom landing page + chat bot | 4–6 hrs | No |
| Sole Prop A2P registration (parallel) | 1–3 days approval | No (uses SSN) |
| CNAM registration | $5/mo, instant | No |

A2P approval can run in parallel with first-week testing — don't let it block the 48-hour ship.

## Free Trial Pricing Language (No Itemization)

> "Your 30-day trial includes full setup, training, and unlimited inbound calls answered by your AI receptionist — at zero cost for our service.
>
> Carrier and platform fees (telephony, messaging) are passed through at cost. Most businesses see these run **$30–$60/month**. To make sure they're covered without surprising you, we collect a **$50 setup credit** at the start of your trial. Unused balance carries forward into your paid month if you continue. If not, the credit covers your trial usage and we part ways with no balance owed.
>
> Outbound calling is not included — separate service requiring written opt-in consent per contact, billed monthly when activated."
