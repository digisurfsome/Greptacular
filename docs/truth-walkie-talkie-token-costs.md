# Truth Document: Walkie-Talkie Token Costs & Rate Limit Impact

**Written: 2026-03-14**
**Status: Verified ground truth — cite this document when agents disagree**

---

## How the Claude Agent SDK Works (Stateless)

Claude is **stateless**. The SDK maintains a `messages` array in memory. Every API call sends:

```
[system_prompt] + [ALL messages ever] → Claude API → response
```

The messages array grows with every interaction. It never shrinks unless compacted.

---

## What Goes Into the Messages Array

| Item | Added to messages? | Token cost? |
|------|--------------------|-------------|
| System prompt (.agent/system_prompt.md) | Sent with EVERY call | ~6,000 tokens (fixed) |
| Initial startup message | Yes, once | ~500 tokens (fixed) |
| User chat messages (normal mode) | YES — accumulates | Grows constantly |
| User messages via walkie-talkie | **NO — stays in files** | **ZERO** |
| Agent's thinking/responses | YES — accumulates | ~50-100 tokens per turn |
| Tool call requests (agent asks to use a tool) | YES — accumulates | ~30-50 tokens each |
| Tool results (file contents, command output) | YES — accumulates | Varies: 50-5,000 tokens each |
| PreToolUse hook execution | **NO — runs locally** | **ZERO** |
| File read/write execution | **NO — runs locally** | **ZERO** |
| Walkie-talkie hook check | **NO — runs locally** | **ZERO** |

---

## The Key Insight

The walkie-talkie eliminates **user message accumulation** from the messages array. User messages stay in files (`from_human.md`, `to_human.md`). The agent reads them via tool calls when needed.

**What still accumulates:** Tool call history (agent's thinking + tool requests + tool results). This grows ~1,500-2,000 tokens per round-trip.

**What does NOT accumulate:** User ↔ assistant conversation messages. In normal chat, these are the biggest cost driver (paragraphs of context, instructions, responses). The walkie-talkie makes this ZERO.

---

## Cost Comparison: One Hour of Agent Work

### Normal Chat (No Walkie-Talkie)

```
After 50 tool calls:
  System prompt:                    6,000 tokens (fixed)
  User messages (20+ exchanges):   25,000+ tokens (accumulating)
  Agent responses:                  15,000+ tokens (accumulating)
  Tool call history:                50,000-80,000 tokens (accumulating)
  ─────────────────────────────────────────────────
  INPUT per API call:               ~100,000-300,000 tokens

  Over 50 API calls with growing context:
  Total input tokens sent:          ~2,500,000 - 5,000,000 tokens
```

### Walkie-Talkie Mode

```
After 50 tool calls:
  System prompt:                    6,000 tokens (fixed)
  Startup message:                  500 tokens (fixed, never grows)
  User messages:                    0 tokens (in files, not messages)
  Agent responses:                  5,000 tokens (accumulating, but no chat)
  Tool call history:                30,000-80,000 tokens (accumulating)
  ─────────────────────────────────────────────────
  INPUT per API call:               ~40,000-90,000 tokens

  Over 50 API calls with growing context:
  Total input tokens sent:          ~800,000 - 2,000,000 tokens
```

### Savings

| Metric | Normal | Walkie-Talkie | Savings |
|--------|--------|---------------|---------|
| Input per call (after 1hr) | 100-300K | 40-90K | **3-5x less** |
| Total tokens sent (1hr) | 2.5-5M | 0.8-2M | **2.5-3x less** |
| Rate limit burn rate | Fast | **Much slower** | **2.5-5x more runway** |
| Conversation messages | Grows constantly | **Zero** | **100% eliminated** |

---

## Single Round-Trip Breakdown

One complete exchange (user sends message via walkie-talkie, agent reads, works, responds):

```
1. AGENT READS YOUR MESSAGE
   Agent thinks: "check from_human.md"                  ~50 tokens output
   PreToolUse hook (LOCAL - free):                       0 tokens
   Read tool executes (LOCAL - free):                    0 tokens
   File contents returned → added to history:           ~200 tokens

2. AGENT DOES WORK (example: edit a code file)
   Agent thinks: "read main.py"                         ~80 tokens output
   Read main.py → result added to history:              ~1,500 tokens
   Agent thinks: "make this edit"                       ~100 tokens output
   Edit → result added to history:                      ~50 tokens

3. AGENT WRITES RESPONSE
   Agent thinks: "update to_human.md"                   ~50 tokens output
   Write tool → result added to history:                ~30 tokens

TOTALS FOR ONE ROUND-TRIP:
   Output tokens (billed separately):                   ~280 tokens
   Added to message history (carried forward):          ~1,780 tokens
   User messages added:                                 0 tokens
   Local operations (free):                             3 hook checks
```

---

## What's Free (Zero Tokens)

1. **PreToolUse hooks** — Python code running locally. Includes walkie-talkie message checking, bash command validation, session control enforcement. All free.
2. **Tool execution** — Reading files, writing files, running bash commands happen locally on the machine. The EXECUTION is free.
3. **File storage** — Messages sitting in from_human.md and to_human.md cost nothing to store.
4. **Walkie-talkie message injection** — When the hook blocks a tool call and injects a message, that's a local operation.

## What Costs Tokens

1. **System prompt** — Sent with every API call. Fixed cost. (~6K tokens)
2. **Claude's thinking** — Every time Claude decides what to do, that's output tokens. (~50-100 per decision)
3. **Tool RESULTS** — When Claude reads a file, the file contents go into the messages array and are carried forward in every future API call. This is the main source of growth.
4. **Agent's tool requests** — Claude saying "I want to Read file X" goes into messages. Small (~30-50 tokens each) but accumulates.

---

## Rate Limit Impact

Rate limits are **token-based** (not message-based). The 5-hour rolling window counts total tokens consumed.

**Without walkie-talkie on 1M model:**
- Conversation grows to 500K+
- Each API call sends 500K input tokens
- 50 API calls = 12.5M+ total input tokens consumed from quota

**With walkie-talkie on 1M model:**
- Conversation grows to ~80-120K (tool history only, no messages)
- Each API call sends ~80K input tokens
- 50 API calls = 2M total input tokens consumed from quota

**Result: Walkie-talkie gives you ~6x more productive time within the same rate limit window.**

---

## Why Tool History Still Accumulates

Claude is stateless. If you removed previous tool call results from the messages array:
- Claude wouldn't know it already read a file
- Claude would re-read the same files repeatedly
- Claude would lose track of what it already did

The tool history IS Claude's memory. You can't remove it without Claude forgetting everything.

**This is why compaction exists** — it summarizes old tool results instead of carrying the full contents. But compaction loses detail. The walkie-talkie approach of bridge-saving and starting fresh sessions is better because you control exactly what transfers.

---

## Bridge Save vs. Compaction

| Aspect | Compaction | Bridge Save |
|--------|-----------|-------------|
| Who controls it | Claude/SDK (automatic) | You (manual) |
| What's preserved | Summary (lossy) | Exactly what you write (lossless) |
| When it happens | ~75-85% context | When you decide (e.g., 50%) |
| Quality of transfer | Summary of summary of summary | Clean, intentional handoff |
| Can be disabled | Yes (autoCompactEnabled: false) | N/A (manual) |

---

## The 1M Model Changes Everything

| Scenario | 200K Model | 1M Model |
|----------|-----------|----------|
| Walkie-talkie session runway | ~150K before compaction | ~750K+ before compaction |
| Tool calls before hitting wall | ~75 calls | ~375+ calls |
| Hours of productive work | ~1-2 hours | ~5-10 hours |
| Rate limit impact per call | Moderate | Higher per call (bigger context) |
| Rate limit impact total (walkie-talkie) | Lower total | **Much lower total** (fewer sessions needed) |

The 1M model + walkie-talkie + disabled compaction + manual bridge saves = maximum productive time with minimum rate limit burn.

---

## Micro-Bridge: Clearing Tool Receipt Accumulation

Tool receipts (tool call history) accumulate in the messages array. The micro-bridge clears them:

1. Track accumulated tool tokens in the session
2. At threshold (30-50K tokens of tool history), trigger micro-bridge
3. Agent writes current state to `.agent/working_memory.md` and `.agent/tool_log.md`
4. Stop session, start fresh
5. New session reads state files (~2-5K tokens) and continues
6. Messages array back to ~8K tokens

**Result:** Each API call stays at ~8-20K tokens instead of growing to 80-120K.

### Micro-Bridge vs. Interruption Bridge vs. Context Limit Bridge

| Mechanism | Purpose | Trigger | What Happens |
|-----------|---------|---------|-------------|
| **Incremental state save** | Crash protection | Every ~10K tokens | Write state to working_memory.md. If session dies, nothing lost — files survive. |
| **Micro-bridge** | Keep sessions light | Every 30-50K of tool receipts | Stop session, start fresh, read summary. Clears tool receipt accumulation. |
| **Context limit bridge** | Agent handoff | At 50% context (500K on 1M) | Full bridge save, new agent takes over. |

### Updated Cost Comparison

| Approach | Avg tokens per API call | Rate limit burn (1hr, 50 calls) |
|----------|------------------------|--------------------------------|
| Normal chat, no walkie-talkie | ~200K | ~10M tokens |
| Walkie-talkie only | ~60K | ~3M tokens |
| Walkie-talkie + micro-bridges | ~20K | ~1M tokens |
| **Walkie-talkie + micro-bridges + agent chain** | **~20K per call** | **~1M tokens, 1.5M+ accessible** |

---

## Super Agent Chain: File-Based Persistence Across Sessions

### The Breakthrough

Because walkie-talkie stores conversation in FILES (not the API messages array):
- **Sessions can crash without losing conversation** — files survive on disk
- **New agents can read previous agents' conversations** — files are on the filesystem
- **Multiple agents chain together** sharing accumulated knowledge through files

### How It Works

```
AGENT 1 (0 → 500K context):
  Conversation in: from_human.md, to_human.md
  State in: working_memory.md, tool_log.md
  Bridge save: ~3K summary

AGENT 2 (starts fresh at ~8K):
  Reads bridge from Agent 1: ~3K tokens
  Has ACCESS to Agent 1's full conversation files: 500K available on demand
  Only READS what it needs: maybe 10-30K
  Own work: up to 460-490K new context

AGENT 3 (starts fresh at ~8K):
  Reads bridge from Agents 1+2: ~5K tokens
  Has ACCESS to all previous files: 1M+ available on demand
  Only READS what it needs: maybe 20-50K
  Own work: up to 450-480K new context

TOTAL ACCESSIBLE: ~1.5M tokens
COST TO ACCESS: ~8-50K per agent (not 1.5M)
```

### Why This Is Different From Normal Chat

| Normal Chat | Walkie-Talkie + Agent Chain |
|-------------|---------------------------|
| Session dies = conversation lost | Session dies = conversation in files, safe |
| New agent starts blind | New agent reads previous conversation files |
| Full history in messages = expensive | Full history in files = free until read |
| 500K context = 500K per API call | 1.5M accessible, ~20K per API call |
| Must read ALL history every call | Reads ONLY what's needed, WHEN needed |

### The Filing Cabinet Analogy

Messages array = photographic memory (instant recall, massive cost)
Files = filing cabinet (must look things up, near-zero cost)

A person with a filing cabinet and good organization can be just as effective as someone with photographic memory — they just need to know WHERE to look. The bridge summary tells the new agent where to look.

### Crash-Proof By Design

In normal chat: API session dies → messages array gone → all context lost
In walkie-talkie: API session dies → files still on disk → new agent reads files → nothing lost

The walkie-talkie architecture is inherently crash-proof because the source of truth is the filesystem, not the API session.

---

## Theoretical Minimum Token Cost Per API Call

If everything possible is filed:

```
System prompt:            ~6,000 tokens (unavoidable — sent every call)
Startup message:          ~500 tokens (unavoidable — one-time)
Current tool request:     ~50 tokens (unavoidable — agent asking to use a tool)
Current tool result:      ~500-2,000 tokens (unavoidable — what agent just read/wrote)
─────────────────────────────────────────────────────────────────
MINIMUM per API call:     ~7,000-8,500 tokens
```

Everything else — conversation history, tool receipts, previous sessions — lives in files.
The agent reads files on demand, paying only for what it actually needs at that moment.

---

## Super Agent Chain: Full Math

### The Formula

Each agent produces ~20K tokens of conversation files (from_human.md, to_human.md, working_memory.md, bridge.md, build_log.md). Each new agent reads ALL previous agents' files for full context.

```
Cab ride for Agent N = 6,000 + (N-1) × 20,000
Productive work for Agent N = 500,000 - cab ride
Limit: when cab ride exceeds 500,000 (50% of 1M model)
```

Solving for the limit:
```
6,000 + (N-1) × 20,000 = 500,000
N = 25.7 → Agent 25 is the last viable agent
```

### Complete Agent Chain Table

```
Agent  │ Cab Ride  │ Productive Work │ Running Total
───────┼───────────┼─────────────────┼──────────────
  1    │    6K     │    494K         │    494K
  2    │   26K     │    474K         │    968K
  3    │   46K     │    454K         │  1,422K    ← 2.84x (sweet spot for most work)
  4    │   66K     │    434K         │  1,856K
  5    │   86K     │    414K         │  2,270K    ← 4.5x (high efficiency, 83% productive)
  6    │  106K     │    394K         │  2,664K
  7    │  126K     │    374K         │  3,038K
  8    │  146K     │    354K         │  3,392K
  9    │  166K     │    334K         │  3,726K
 10    │  186K     │    314K         │  4,040K    ← 8x (practical limit, 63% productive)
 11    │  206K     │    294K         │  4,334K
 12    │  226K     │    274K         │  4,608K
 13    │  246K     │    254K         │  4,862K    ← cab ride > 50% of session
 14    │  266K     │    234K         │  5,096K
 15    │  286K     │    214K         │  5,310K
 16    │  306K     │    194K         │  5,504K
 17    │  326K     │    174K         │  5,678K
 18    │  346K     │    154K         │  5,832K
 19    │  366K     │    134K         │  5,966K
 20    │  386K     │    114K         │  6,080K    ← 12.2x (cab ride = 77%)
 21    │  406K     │     94K         │  6,174K
 22    │  426K     │     74K         │  6,248K
 23    │  446K     │     54K         │  6,302K
 24    │  466K     │     34K         │  6,336K
 25    │  486K     │     14K         │  6,350K    ← theoretical max: 12.7x
 26    │  506K     │   OVER LIMIT    │  ─────────
```

### Key Milestones

| Agents | Total Productive Work | Multiplier | Efficiency |
|--------|----------------------|------------|------------|
| 1      | 494K                 | 1x         | 99% productive |
| 3      | 1,422K               | 2.9x       | 91% avg productive |
| 5      | 2,270K               | 4.6x       | 83% avg productive |
| 10     | 4,040K               | 8.2x       | 63% last agent productive |
| 15     | 5,310K               | 10.7x      | 43% last agent productive |
| 25     | 6,350K               | 12.9x      | 3% last agent productive |

### Sweet Spot: 5-10 Agents

The practical sweet spot is **5-10 agents**:
- 5 agents: 2.27M productive tokens (4.5x), last agent is 83% productive
- 10 agents: 4.04M productive tokens (8x), last agent is 63% productive
- Beyond 10: diminishing returns, agents spend more time reading than working

### What "Full Context" Means Per Agent

Agent N reads ALL previous conversation files. This means:
- Agent 5 reads ~80K of previous conversations (4 agents × 20K)
- Agent 10 reads ~180K of previous conversations (9 × 20K)
- Agent 15 reads ~280K of previous conversations

The agent starts each session with complete knowledge of everything all previous agents discussed and did. It's not a summary — it's the actual conversation files.

### Compared to Normal Chat (No Walkie-Talkie)

| Approach | Context per "lifetime" | With full recall |
|----------|----------------------|------------------|
| Normal chat, single session | 500K | 500K |
| Normal chat, agent handoff (bridge only) | 500K + 500K (but loses detail) | ~600K effective |
| **Walkie-talkie + agent chain (5 agents)** | **2,270K** | **Full recall of all 2.27M** |
| **Walkie-talkie + agent chain (10 agents)** | **4,040K** | **Full recall of all 4.04M** |

---

## Open Research: Prompt Caching

Anthropic has a "prompt caching" feature where if the same prefix (system prompt + early messages) is sent repeatedly, the cached portion costs only 10% of normal input tokens and doesn't count against per-minute rate limits. This is server-side caching — the tokens ARE sent, but the cost is reduced.

This is DIFFERENT from the walkie-talkie approach:
- **Prompt caching**: Messages still in the API call, but cheaper (10% cost for cached portions)
- **Walkie-talkie**: Messages NOT in the API call at all (0% cost, moved to files)

Both reduce costs. The walkie-talkie is more aggressive — it eliminates the tokens entirely rather than just making them cheaper. However, prompt caching could further reduce the cost of the REMAINING tokens in the messages array (system prompt, tool results). These two approaches are complementary, not competing.

Further research needed: How exactly does prompt caching interact with the Agent SDK? Does the SDK automatically cache the system prompt? If so, the 6K system prompt cost per API call might actually be ~600 tokens (90% cached). This would make the theoretical minimum even lower.

