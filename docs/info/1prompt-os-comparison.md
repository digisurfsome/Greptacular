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
