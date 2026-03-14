# Research Report: AI Caching, Context Management, and Patent Landscape

**Date:** 2026-03-14
**Methodology:** 80+ web searches across 5 parallel research agents covering official documentation, patents, academic papers, open-source projects, and industry blogs.

---

## Table of Contents
1. [Anthropic — Tool Result Offloading & Caching](#topic-1-anthropic--tool-result-offloading--caching)
2. [Google Gemini — 1M Context Architecture](#topic-2-google-gemini--1m-context-architecture)
3. [OpenAI — Context Window Management](#topic-3-openai--context-window-management)
4. [Patent Landscape](#topic-4-patent-landscape)
5. [Prior Art](#topic-5-prior-art)
6. [Cross-Topic Summary & Conclusions](#cross-topic-summary--conclusions)

---

## TOPIC 1: Anthropic — Tool Result Offloading & Caching

### How Prompt Caching Works

Anthropic's prompt caching stores **KV-cache representations** (not raw text) and cryptographic hashes of cached content server-side. It allows subsequent API calls with identical prompt prefixes to skip recomputation.

**What gets cached:**
- Tool definitions in the `tools` array
- System message content blocks
- Text messages (user and assistant turns)
- Images and documents in user turns
- Tool use blocks and tool result blocks in `messages.content`

**What does NOT get cached:**
- Thinking blocks cannot be explicitly marked with `cache_control` (though implicitly cached when passed back)
- Empty text blocks
- Sub-content blocks like citations

**Cache hierarchy (strict order):** `tools` → `system` → `messages`. Changes at any level invalidate that level and everything below. Adding a new MCP tool mid-session invalidates the entire cache.

**Cache matching:** Requires 100% identical content from the start of the prompt up to and including the `cache_control` breakpoint. Even minor formatting changes break the cache.

**TTL options:**
- **5-minute TTL (default):** Cache writes cost 1.25x base input price. Cache reads cost 0.1x base input price.
- **1-hour TTL:** Cache writes cost 2x base input price. Cache reads still 0.1x.

**Minimum token requirements:**
- Claude Opus 4.6/4.5: 4,096 tokens per cache checkpoint
- Claude Sonnet 4.6: 2,048 tokens
- Claude Sonnet 4/3.7, Opus 4.1/4/3: 1,024 tokens

**Sources:**
- [Prompt Caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Prompt Caching Announcement — Anthropic Blog](https://www.anthropic.com/news/prompt-caching)

### Does the Claude Agent SDK Automatically Cache the System Prompt?

**YES.** The official documentation states: "Content that stays the same across turns (system prompt, tool definitions, CLAUDE.md) is automatically prompt cached, which reduces cost and latency for repeated prefixes."

Two approaches exist:
- **Automatic caching:** Add `cache_control: {"type": "ephemeral"}` at the top level. The system automatically places cache breakpoints at the last cacheable block and moves them forward as the conversation grows. Recommended for multi-turn conversations.
- **Explicit breakpoints:** Manually place `cache_control` on specific content blocks.

**Known issue:** The Agent SDK reportedly changed its default cache TTL from 5 minutes to 1 hour, meaning all cache writes now cost 2x instead of 1.25x.

**Sources:**
- [How Prompt Caching Elevates Claude Code Agents — Walturn](https://www.walturn.com/insights/how-prompt-caching-elevates-claude-code-agents)
- [Agent SDK 1-hour cache TTL — GitHub Issue #188](https://github.com/anthropics/claude-agent-sdk-typescript/issues/188)

### Is There a Mechanism to Offload Tool Results to Files or Cache Them Server-Side?

**NO — not in the API.** There is no Anthropic API feature that stores tool results in a separate file store or server-side cache so they don't need to be re-sent. Every API call requires the full messages array. Prompt caching reduces the **compute cost** of reprocessing that content but does **NOT** eliminate the need to send it.

However, two API mechanisms deal with stale tool results:

**A) Context Editing (API-level, beta):**
- The `clear_tool_uses_20250919` strategy clears old tool results server-side **before** the prompt reaches Claude
- Cleared content is replaced with **placeholder text** (not offloaded to disk)
- Configurable: trigger threshold, number of recent tool uses to keep, tool exclusions
- Clearing invalidates prompt cache at the clearing point
- This is "garbage collection," not offloading — the data is gone

**B) Server-Side Compaction (API-level, beta):**
- The `compact_20260112` strategy summarizes the entire conversation when it approaches a token threshold
- Replaces full message history with a `compaction` block containing a summary
- Destructive — original messages are replaced, not stored elsewhere

**Sources:**
- [Context Editing — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/context-editing)
- [Compaction — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/compaction)

### What is "Micro-Compaction" in Claude Code?

**Micro-compaction is a Claude Code CLIENT-SIDE feature** (introduced in v1.0.68), not an Anthropic API feature. It sits between normal operation and full auto-compaction.

**What it does (confirmed):**
- Automatically identifies old tool calls no longer immediately relevant
- Selectively removes outdated tool results while preserving recent context
- Maintains critical project information (current file states, ongoing tasks)
- Triggers automatically when context grows long, before full auto-compaction

**Does it offload to disk?** Evidence is mixed:
- **Decode Claude (third-party)** claims: "When tool outputs get large, Claude Code saves them to disk and keeps only a reference in the model context." Describes "hot tail" (recent results inline) and "cold storage" (older results referenced by path).
- **Anthropic's official documentation** does not describe this mechanism. The closest feature is Context Editing, which replaces results with placeholders.
- **Assessment:** The "cold storage" description likely refers to Claude Code's client-side implementation, not an API feature.

**Sources:**
- [Inside Claude Code's Compaction System — Decode Claude](https://decodeclaude.com/compaction-deep-dive/)
- [What is Micro-Compact — ClaudeLog](https://claudelog.com/faqs/what-is-micro-compact/)

### Are Tool Results Cached Server-Side So They Don't Need Re-Sending?

**NO.** This is the clearest finding:

| Mechanism | What Happens | Tool Results Re-Sent? |
|-----------|-------------|----------------------|
| **Prompt Caching** | Server caches KV representations of prompt prefix | YES — must be sent every time |
| **Context Editing** | Server drops old tool results, replaces with placeholders | YES — you still send them, server strips before processing |
| **Compaction** | Server summarizes entire conversation | NO — but original content is destroyed |

**The critical distinction:** Prompt caching is a **compute optimization**, not a **transfer optimization**. You must send the full messages array every time. The bytes still go over the wire.

---

## TOPIC 2: Google Gemini — 1M Context Architecture

### How Gemini Achieves 1M Token Context

**Confirmed: Sparse Mixture-of-Experts (MoE) Architecture.** The Gemini 1.5 technical report ([arXiv:2403.05530](https://arxiv.org/abs/2403.05530)) confirms Gemini 1.5 Pro is a "sparse mixture-of-expert (MoE) Transformer-based model." MoE activates only a subset of parameters per token, decoupling total model capacity from per-token compute cost.

**The report states** it "incorporates a series of significant architecture changes that enable long-context understanding of inputs up to 10 million tokens without degrading performance" — but **deliberately does not specify what those changes are**. Model size, number of experts, and specific attention modifications are all withheld.

**Near-perfect retrieval:** >99.7% recall on needle-in-a-haystack tasks up to 1M tokens, 99.2% at 10M tokens in research settings.

### Likely But Unconfirmed Techniques

Google has published research on multiple efficient attention approaches but **never confirmed which powers Gemini:**

- **Infini-Attention** ([arXiv:2404.07143](https://arxiv.org/abs/2404.07143)) — Compressive memory storing past KV states instead of discarding them. 114x compression ratio. Published by Google researchers April 2024.
- **Ring Attention** ([arXiv:2310.01889](https://arxiv.org/abs/2310.01889)) — Distributes sequences across devices in a ring topology. Published by UC Berkeley (Liu, Zaharia, Abbeel), not Google. Enables context length proportional to device count.
- **MELODI** ([DeepMind](https://deepmind.google/research/publications/121073/)) — Hierarchical compression for long documents. 8x memory footprint reduction.
- **LongT5** — Transient Global attention combining local sliding-window with global attention.

**Sources:**
- [Gemini 1.5 Technical Report (arXiv)](https://arxiv.org/abs/2403.05530)
- [Google Blog: Introducing Gemini 1.5](https://blog.google/innovation-and-ai/products/google-gemini-next-generation-model-february-2024/)

### Is 1M Context Enabled by Custom TPU Hardware?

**YES, partially — hardware and software are co-designed.**

| Generation | HBM/Chip | HBM Bandwidth | ICI/Chip | Max Pod | Topology |
|-----------|----------|---------------|---------|---------|----------|
| TPU v5e | 16 GB | 819 GB/s | 1,600 Gbps | 256 chips | 2D torus |
| TPU v5p | 95 GB | 2,765 GB/s | 4,800 Gbps | 8,960 chips | 3D torus |
| TPU v6e (Trillium) | 32 GB | 1,600 GB/s | 3,200 Gbps | 256 chips | 2D torus |
| **TPU v7 (Ironwood)** | **192 GB** | **7,400 GB/s** | **9,600 Gbps** | **9,216 chips** | **3D torus** |

**Why this matters:**
1. **HBM capacity determines KV cache size.** A 70B model at 300K tokens needs ~93 GB of KV cache — more than an H100's 80 GB. Ironwood at 192 GB/chip handles much larger caches.
2. **HBM bandwidth determines throughput.** Reading the KV cache at every attention step requires enormous bandwidth.
3. **Inter-chip interconnect (ICI) enables distributed attention.** If attention is distributed (ring attention etc.), ICI determines whether communication overlaps with computation.
4. **Ironwood was explicitly designed for long context** — Google's docs state the architecture was "designed specifically for long-context applications approaching million-token windows."

**However, hardware alone is insufficient.** Standard quadratic attention at 1M tokens requires computing a 1M × 1M attention matrix (1 trillion entries). Algorithmic innovations are essential complements.

**Sources:**
- [Google TPU Architecture Guide — Introl](https://introl.com/blog/google-tpu-architecture-complete-guide-7-generations)
- [Cloud TPU v5p — Google Cloud Blog](https://cloud.google.com/blog/products/ai-machine-learning/introducing-cloud-tpu-v5p-and-ai-hypercomputer)

### Did Google Patent the Long Context Approach?

**Primarily trade secrecy, not patents.**

**What Google HAS patented:**
1. **The Transformer itself** — US10,452,978 ("Attention-Based Sequence Transduction Neural Networks"). Foundational patent from "Attention Is All You Need." 7+ continuation applications. NOT in Google's Open Source Non-Assertion Pledge.
2. **Sparse attention** — US20230022151A1 ("Full Attention with Sparse Computation Cost"). Directly addresses quadratic complexity limitation.
3. **Universal Transformers** — US10,740,433. Adaptive computation time.

**What Google has NOT publicly patented:**
- No specific patent on "1M context window" technique
- No patent on Gemini's MoE configuration
- No patent on whatever attention modification enables the long context

**Protection strategy:**
1. **Trade secrecy** — Technical report deliberately omits specifics
2. **Custom silicon moat** — TPUs not sold commercially; only via Google Cloud
3. **Broad foundational patents** — Transformer patent as legal backstop

**Sources:**
- [Google's Transformer Patents — PI IP LAW](https://piip.co.kr/en/blog/google-transformer-llm-patent-risk-and-strategy)
- [US10,452,978 — Google Patents](https://patents.google.com/patent/US10452978B2/en)
- [US20230022151A1 — Google Patents](https://patents.google.com/patent/US20230022151A1/en)

### Gemini's Context Caching

**Two types:**

**Implicit Caching (automatic, since May 2025):**
- Enabled by default on Gemini 2.5+ models
- No developer action required
- Cache reads cost 10% of base input price (90% savings)
- No storage costs

**Explicit Caching (manual):**
- Developer creates cache object with TTL (default 60 min)
- Storage costs: $1–$4.50 per million tokens per hour
- Warning: A 10M token cache costs $45/hour or $1,080/day

**Sources:**
- [Context Caching — Gemini API](https://ai.google.dev/gemini-api/docs/caching)
- [Gemini 2.5 Implicit Caching — Google Developers Blog](https://developers.googleblog.com/en/gemini-2-5-models-now-support-implicit-caching/)

---

## TOPIC 3: OpenAI — Context Window Management

### Prompt Caching

**Automatic and free** on all models GPT-4o and newer. No code changes required.

- Caches exact prefix match starting at 1,024 tokens, increasing in 128-token increments
- Requests routed to machines based on hash of initial prefix (~256 tokens)
- Up to **80% latency reduction** and **90% input cost reduction**
- **In-memory (default):** 5–10 min inactivity TTL, max 1 hour
- **Extended (24-hour):** Available for GPT-5.x and GPT-4.1. Configured via `prompt_cache_retention` parameter
- **Everything is cacheable:** messages array, tool definitions, images, audio, structured output schemas

**Sources:**
- [OpenAI Prompt Caching Guide](https://developers.openai.com/api/docs/guides/prompt-caching/)
- [OpenAI Prompt Caching 201](https://developers.openai.com/cookbook/examples/prompt_caching_201/)

### Tool Result Handling

Tool results are part of the messages array and part of the cacheable prefix. **No evidence of automatic offloading or summarization of tool results** separately from general context management.

**File Search (Vector Store Offloading)** — OpenAI's mechanism for keeping large document content OUT of the context window:
- Files uploaded to vector stores, automatically chunked, embedded, indexed
- Default: up to 20 chunks injected for GPT-4/o-series models
- Pricing: $0.10/GB/day storage + $2.50 per 1,000 search calls
- **This is effectively file-based offloading** — large documents never enter context directly

**Sources:**
- [OpenAI File Search Guide](https://platform.openai.com/docs/guides/tools-file-search)

### Stateless Problem Solutions

The core API is stateless. OpenAI provides five mechanisms:

| Approach | How It Works | Status |
|----------|-------------|--------|
| **Client-side array chaining** | Developer maintains full history, sends with every request | Active (Chat Completions) |
| **`previous_response_id`** | Server reconstructs conversation chain. Preserves reasoning traces. | Active (Responses API) |
| **Conversation objects** | Server automatically maintains history | Active (Responses API) |
| **Compaction** | `/responses/compact` replaces prior assistant messages, tool calls, tool results with opaque encrypted item. User messages kept verbatim. | Active (since Dec 2025) |
| **Threads** | Automatic server-side truncation | **Deprecated** — shutting down Aug 26, 2026 |

**Key insight about Compaction:** OpenAI's compaction is opaque and encrypted. Developers cannot inspect, debug, or verify what was preserved. It's a black box.

**Sources:**
- [OpenAI Compaction Guide](https://developers.openai.com/api/docs/guides/compaction/)
- [OpenAI Conversation State Guide](https://platform.openai.com/docs/guides/conversation-state)
- [Sean Goedecke — The Responses API](https://www.seangoedecke.com/responses-api/)

### OpenAI Patents

**US 11,886,826 B1** — "Systems and Methods for Language Model-Based Text Insertion" (granted Jan 30, 2024). Covers context-aware text generation/insertion. **NOT about context window management, compression, or caching.**

**No patents found specifically about prompt caching, KV-cache management, context compression, or truncation strategies.**

OpenAI's portfolio: 110 patents globally, 42 granted. Uses defensive patent pledge.

**Sources:**
- [Google Patents — US11886826B1](https://patents.google.com/patent/US11886826B1/en)
- [GreyB — OpenAI Patents Insights](https://insights.greyb.com/openai-patents/)

---

## TOPIC 4: Patent Landscape

### Critical Finding: No Patent Covers the Core Concepts

After 16+ targeted searches across Google Patents, USPTO, Justia, and patent-specific resources:

| Concept | Patent Found? | Closest Match | Notes |
|---------|:------------:|---------------|-------|
| File-based agent communication to reduce token costs | **NO** | None | Widely practiced, no patent identified |
| Offloading conversation history to persistent storage | **NO** | US 7,024,656 (generic agent persistence, pre-LLM) | Prior art in academic papers |
| Agent session chaining through file persistence | **NO** | None | Telephony chaining patents exist but unrelated |
| Reducing LLM API costs through file-based message passing | **NO** | None | Engineering best practice, not patented |
| Context window extension through agent chaining | **NO** | US 12,387,050 (thought caching, different mechanism) | Adjacent but mechanistically different |
| Multi-agent session persistence with shared files | **NO** | US 12,111,859 (C3.AI orchestration, broader scope) | Enterprise orchestration, not file-specific |

### Closest Existing Patents

**US 12,387,050 — "Multi-stage LLM with unlimited context"** (Issued Aug 12, 2025)
- Combines large and small LLMs with a "thought cache." Router directs prompts to large LLM or cached thoughts. Cached thoughts combined with new prompts through smaller LLM.
- **Key distinction:** Operates at model inference level (thought caching between model tiers), NOT at agent/session level through files. Does not cover file-based communication between sessions or reducing API token costs by passing information through files.
- Source: [Justia Patents](https://patents.justia.com/patent/12387050)

**US 12,111,859 B2 — "Enterprise generative artificial intelligence architecture"** (C3.AI, issued Oct 8, 2024)
- Orchestrator managing multiple AI agents with context management across enterprise data sources.
- Does NOT specifically cover file-based communication to reduce token costs.
- Source: [Google Patents](https://patents.google.com/patent/US12111859B2/en)

**US 7,024,656 B1 — "Persistent agents"**
- Object persistence for software agents using persistent stores (filesystem or database).
- Pre-LLM era patent about object-relational mapping. Not specific to LLM context management.
- Source: [Google Patents](https://patents.google.com/patent/US7024656B1/en)

### Important Caveat

Patent applications have an **18-month publication delay**. Applications filed in 2025 or early 2026 may not yet be publicly visible. A professional patent search through USPTO PAIR and WIPO databases would be needed to identify unpublished applications.

---

## TOPIC 5: Prior Art

### File-Based Communication Instead of API Messages

**EXTENSIVE PRIOR ART EXISTS.**

**Blackboard Architecture (1980s — present)**
The pattern of agents reading from and writing to a central shared space dates to the 1980s. Google Research and UMass Amherst published a 2025 paper applying this to LLM multi-agent data science, showing 13%–57% improvements over baselines.
- Source: [arXiv:2510.01285 — LLM-Based Multi-Agent Blackboard System](https://arxiv.org/abs/2510.01285)
- Source: [github.com/claudioed/agent-blackboard](https://github.com/claudioed/agent-blackboard)

**Manus (2024–2025)**
Pioneered treating the file system as "infinite memory." Agents write intermediate results to files, load only summaries into context. Claims 100:1 compression ratios.
- Source: [Manus Blog — Context Engineering](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)

**LangChain Deep Agents (2025)**
When tool responses exceed 20,000 tokens, automatically offloads to filesystem and substitutes with file path reference plus 10-line preview. When context crosses 85% capacity, truncates older tool calls and replaces with file pointers.
- Source: [LangChain Blog — Context Management for Deep Agents](https://blog.langchain.com/context-management-for-deepagents/)

**Fast.io — Shared File Protocols**
Detailed guide on using shared file workspaces as a "blackboard" for agent coordination. Claims 35% processing time reduction vs. streaming through API layers.
- Source: [Fast.io — Agent-to-Agent File Communication Protocols](https://fast.io/resources/agent-to-agent-file-communication-protocols/)

### "Super Agent Chain" — Agents Reading Previous Agents' Files

**The concept exists under different names.** No one uses the exact term "super agent chain."

**Chain-of-Agents (CoA) — Google Research (NeurIPS 2024)**
Worker agents sequentially process different portions of text, each receiving the message from the previous worker. A manager agent synthesizes the final output. 10% improvement over RAG and full-context approaches.
- Source: [arXiv:2406.02818](https://arxiv.org/abs/2406.02818)
- Source: [Google Research Blog — Chain of Agents](https://research.google/blog/chain-of-agents-large-language-models-collaborating-on-long-context-tasks/)

**Git Context Controller (GCC) — arXiv 2025**
Structures agent memory as a persistent file system with COMMIT, BRANCH, MERGE, and CONTEXT operations. Enables cross-session and cross-agent context reuse. 80%+ SWE-Bench resolution rate.
- Source: [arXiv:2508.00031](https://arxiv.org/abs/2508.00031)
- Source: [github.com/swadhinbiswas/contexa](https://github.com/swadhinbiswas/contexa)

**Graph of Agents — arXiv 2025**
Extends Chain-of-Agents to graph topologies for structured context sharing.
- Source: [arXiv:2509.21848](https://arxiv.org/html/2509.21848v1)

### Open-Source Session Chaining Projects

| Project | Mechanism | Source |
|---------|-----------|--------|
| **Claude Code** | JSONL session files; `--continue` / `--resume` flags; auto-compact with summary | [Claude Code Docs](https://code.claude.com/docs/en/how-claude-code-works) |
| **Aider** | `--restore-chat-history`; `.aider.llm.history` logs; git diff injection | [Aider FAQ](https://aider.chat/docs/faq.html) |
| **OpenHands** | Event-sourced state; `LLMSummarizingCondenser` for compression | [OpenHands Docs](https://docs.openhands.dev/sdk/guides/convo-persistence) |
| **Letta (MemGPT)** | Agent File (.af) format; persistent memory blocks across sessions | [github.com/letta-ai/agent-file](https://github.com/letta-ai/agent-file) |
| **Contexa (GCC)** | `.GCC/` directory with markdown + YAML; COMMIT/BRANCH/MERGE operations | [github.com/swadhinbiswas/contexa](https://github.com/swadhinbiswas/contexa) |
| **LangGraph** | Thread-scoped checkpoints persisted to database; long-term memory via files | [LangChain Memory Docs](https://docs.langchain.com/oss/python/langgraph/memory) |
| **AutoGen** | `save_state()` / `load_state()` for JSON serialization | [GitHub Issue #6466](https://github.com/microsoft/autogen/issues/6466) |
| **Session-Handoff Skill** | Structured markdown handoff docs chained via `--continues-from` links | [skills.sh](https://skills.sh/softaworks/agent-toolkit/session-handoff) |

### MemGPT/Letta — The Foundational Prior Art

The most mature prior art for extending context beyond model windows. Treats the context window as "RAM" and external storage as "disk," paging information in and out via tool calls. The LLM itself serves as the memory manager.
- Source: [arXiv:2310.08560 — MemGPT](https://arxiv.org/abs/2310.08560)
- Source: [Letta Docs](https://docs.letta.com/concepts/letta/)

### "Walkie-Talkie" Agent Communication

**NO PRIOR ART FOUND** for file-based "walkie-talkie" communication between AI agents. The term is not used in any published research, blog post, or open-source project for this concept. A GitHub project called "Walkie" exists but uses P2P network sockets, not files.

---

## Cross-Topic Summary & Conclusions

### How the Big 3 Compare on Caching

| Feature | Anthropic | Google | OpenAI |
|---------|-----------|--------|--------|
| **Automatic caching** | Yes (with `cache_control` header) | Yes (implicit since May 2025) | Yes (fully automatic, no changes) |
| **Cache read discount** | 90% (0.1x base) | 90% (Gemini 2.5+) | Up to 90% |
| **Cache write cost** | 1.25x–2x base | Standard input rate | Free |
| **Extended TTL** | 1 hour (2x cost) | Configurable (explicit) | 24 hour (GPT-5.x, 4.1) |
| **Cache storage fees** | None | $1–$4.50/M tokens/hr (explicit) | None |
| **Tool result offloading** | No | No | File Search (vector store) |
| **Compaction** | Yes (beta, lossy) | Not announced | Yes (opaque encrypted) |
| **Context editing** | Yes (beta, clears tool results) | Not announced | Compaction serves this role |

### What IS Known (High Confidence)

1. **No provider truly offloads tool results server-side.** All three cache KV representations to reduce compute, but the full messages array must be sent every time. This is a compute optimization, not a transfer optimization.
2. **Google protects its 1M context approach through trade secrecy and custom silicon**, not primarily through patents. The specific technique is unknown.
3. **Compaction/summarization is destructive everywhere.** Anthropic, OpenAI, and client-side tools like Claude Code all replace original content with summaries. There is no transparent "cold storage with retrieval."
4. **File-based agent communication is widely practiced but unpatented.** Manus, LangChain, Claude Code, and many others use it. No patent covers it.
5. **Session chaining through files is widely practiced but unpatented.** Multiple frameworks implement it. No patent covers it.

### What COULD NOT Be Found (Gaps in Evidence)

1. **No patent exists** covering "communicating with an AI agent through files instead of the API message array to reduce token costs"
2. **No patent exists** covering "chaining multiple AI agent sessions through shared files to extend effective context beyond the model's window"
3. **No one uses the term "super agent chain"** — the concept exists under names like "Chain-of-Agents," "agent relay," and "session handoff chain"
4. **No one uses "walkie-talkie"** as a metaphor for file-based, half-duplex agent communication
5. **The exact attention mechanism in Gemini** is deliberately undisclosed
6. **Whether Claude Code's micro-compaction actually writes to disk** is only claimed by third-party analysis, not Anthropic

### Patent Gap Analysis

The specific combination of these ideas appears to be in a **patent gap**:
- File-based communication between agent sessions to reduce API token costs
- Session chaining through persistent files to extend effective context

**However, prior art is substantial** (Manus 2024, LangChain 2025, MemGPT 2023, Chain-of-Agents 2024, GCC 2025). Any patent application would need to claim something more specific than what is already public.

The closest existing patent (**US 12,387,050** — "Multi-stage LLM with unlimited context") covers thought-caching between model tiers, a **different mechanism** than file-based inter-session communication.

**Caveat:** Patent applications filed after September 2024 may not yet be publicly visible due to the 18-month publication delay.
