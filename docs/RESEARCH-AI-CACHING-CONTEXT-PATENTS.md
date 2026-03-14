# Research Report: AI Caching, Context Management, and Patent Landscape

**Date:** 2026-03-14
**Methodology:** 150+ web searches across 10 parallel research agents (5 initial + 5 gap-fill) covering official documentation, patents, academic papers, open-source projects, and industry blogs. All three major providers (Anthropic, Google, OpenAI) researched for every topic.

---

## Table of Contents
1. [Tool Result Offloading & Caching (All Providers)](#topic-1-tool-result-offloading--caching)
2. [Large Context Window Architecture (All Providers)](#topic-2-large-context-window-architecture)
3. [Context Window Management (All Providers)](#topic-3-context-window-management)
4. [Patent Landscape (All Providers)](#topic-4-patent-landscape)
5. [Prior Art — File-Based Agent Communication](#topic-5-prior-art)
6. [Master Comparison Tables & Conclusions](#master-comparison-tables--conclusions)

---

## TOPIC 1: Tool Result Offloading & Caching

### Anthropic

**How prompt caching works:**
Stores **KV-cache representations** (not raw text) and cryptographic hashes server-side. Subsequent API calls with identical prompt prefixes skip recomputation.

**What gets cached:** Tool definitions, system messages, text messages (user/assistant), images, documents, tool use/result blocks.

**What does NOT get cached:** Thinking blocks (can't be explicitly marked), empty text blocks, citation sub-blocks.

**Cache hierarchy:** `tools` → `system` → `messages`. Changes at any level invalidate that level and below. Adding a new MCP tool mid-session invalidates the entire cache.

**TTL & pricing:**
- 5-min TTL (default): writes 1.25x, reads 0.1x base input
- 1-hour TTL: writes 2x, reads 0.1x base input
- Min tokens: 4,096 (Opus 4.6/4.5), 2,048 (Sonnet 4.6), 1,024 (Sonnet 4/3.7)

**SDK auto-caching:** YES. "Content that stays the same across turns (system prompt, tool definitions, CLAUDE.md) is automatically prompt cached." Known issue: SDK default TTL changed from 5min to 1hr (2x write cost). ([GitHub Issue #188](https://github.com/anthropics/claude-agent-sdk-typescript/issues/188))

**Tool result offloading:** NO. Every API call requires the full messages array. Prompt caching reduces compute cost but NOT transfer cost.

**Context editing (beta):** `clear_tool_uses_20250919` clears old tool results server-side, replacing with placeholder text. Data is destroyed, not offloaded. Performance: 29% improvement alone, 39% with memory tool. ([Anthropic Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents))

**Compaction (beta):** `compact_20260112` summarizes entire conversation. Destructive — originals replaced.

**Micro-compaction (Claude Code client-side):** Introduced v1.0.68. Selectively removes outdated tool results. Third-party claims disk offloading with path references ("hot tail" / "cold storage") but Anthropic docs don't confirm this.

**Sources:**
- [Prompt Caching — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Context Editing — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/context-editing)
- [Compaction — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [Decode Claude — Compaction Deep Dive](https://decodeclaude.com/compaction-deep-dive/)

---

### Google Gemini

**Two caching mechanisms:**

**Implicit Caching (automatic, since May 2025):**
- Enabled by default on Gemini 2.5+ models, no code changes
- 90% discount on cached reads (Gemini 2.5+), 75% (Gemini 2.0)
- No storage costs
- Response includes `cachedContentTokenCount` for verification

**Explicit Caching (developer-controlled):**
- Create named cache objects via API with configurable TTL
- Min cache size: 4,096 tokens
- Storage billed by TTL × token count ($1–$4.50/M tokens/hr)
- Warning: 10M token cache = $1,080/day

**What gets cached:** System instructions, documents, media files. Tool definitions count if in stable prefix.

**Tool result offloading:** NO. Tool results (`FunctionResponse` parts) sit in the `contents` array and consume tokens every turn. No mechanism to externalize dynamic tool outputs.

**ADK system prompt caching:** YES, but requires explicit configuration via `ContextCacheConfig`:
- `static_instruction` parameter enforces immutability for system prompts
- `ContextCacheConfig` set at App level: `min_tokens`, `ttl_seconds` (default 1800), `cache_intervals` (default 10)
- Context window divided into "stable prefixes" and "variable suffixes"
- Most architecturally clean approach of the three providers

**ADK compaction:** `EventsCompactionConfig` summarizes older conversation events:
- Turn-based triggers (every N invocations), NOT token-threshold
- Configurable overlap to prevent info loss at boundaries
- Claims 60-80% token reduction
- Token-based triggers are an open feature request ([GitHub #4146](https://github.com/google/adk-python/issues/4146))

**Growing context strategy:** "Big window + developer responsibility." Gemini does NOT auto-truncate at API level — exceeding the window returns a 400 error (which still consumes rate limit quota).

**Sources:**
- [Gemini API Context Caching](https://ai.google.dev/gemini-api/docs/caching)
- [ADK Context Caching Docs](https://google.github.io/adk-docs/context/caching/)
- [ADK Context Compression](https://google.github.io/adk-docs/context/compaction/)
- [Vertex AI Context Caching](https://cloud.google.com/blog/products/ai-machine-learning/vertex-ai-context-caching)

---

### OpenAI

**Prompt caching:** Fully automatic, free, no code changes on all models GPT-4o+.

- Caches exact prefix starting at 1,024 tokens (128-token increments)
- Requests routed by prefix hash (~256 tokens)
- Up to 80% latency reduction, 50% input cost reduction (NOT 90% — less than Anthropic/Google)
- Cache writes are FREE (no surcharge, unlike Anthropic)
- Default TTL: 5-10 min. **Extended 24-hour TTL** on GPT-5.x and GPT-4.1 via `prompt_cache_retention` (offloads KV tensors to GPU-local SSDs — longest TTL of any provider)
- Hit reliability is probabilistic (~50%), unlike Anthropic's deterministic matching
- Optional `prompt_cache_key` parameter influences routing for shared prefixes

**Tool result offloading:** NO dedicated mechanism. Tool results sit in messages array.

**File Search (vector store) as quasi-offloading:**
- Documents in vector stores, chunked/embedded/indexed server-side
- Only relevant chunks enter context (default 20 for GPT-4/o-series)
- Pricing: $0.10/GB/day + $2.50/1K searches
- This IS effectively document offloading, but NOT for dynamic tool outputs

**Compaction:** `/responses/compact` endpoint (since Dec 2025):
- Replaces prior assistant messages, tool calls, tool results with **opaque encrypted item**
- User messages kept verbatim
- Trigger: `compact_threshold` in `context_management`
- NOT human-readable — encrypted black box
- GPT-5.1-Codex-Max: compaction is a **natively trained capability**, not just summarization. Model prunes its own context while preserving critical state. Sessions span millions of tokens across multiple windows (24+ hour sessions observed).

**SDK auto-caching:** The Agents SDK adds no caching layer — relies on API-level automatic caching. `ModelSettings` exposes `prompt_cache_retention` for extended TTL. MCP `cache_tools_list=True` caches tool schemas locally.

**Sources:**
- [OpenAI Prompt Caching Guide](https://developers.openai.com/api/docs/guides/prompt-caching/)
- [OpenAI Compaction Guide](https://developers.openai.com/api/docs/guides/compaction/)
- [OpenAI File Search Guide](https://platform.openai.com/docs/guides/tools-file-search)
- [PromptHub Caching Comparison](https://www.prompthub.us/blog/prompt-caching-with-openai-anthropic-and-google-models)

---

### Caching Comparison Table

| Feature | Anthropic | Google Gemini | OpenAI |
|---------|-----------|---------------|--------|
| **Activation** | Manual `cache_control` breakpoints | Implicit (auto) + Explicit (named) | Fully automatic |
| **Cache read discount** | 90% | 90% (2.5+) / 75% (2.0) | 50% |
| **Cache write cost** | 1.25x–2x | Free (implicit) / storage-based | Free |
| **Max TTL** | 1 hour | Configurable (no max) | **24 hours** (GPT-5.x) |
| **Hit reliability** | Deterministic (100%) | Automatic | Probabilistic (~50%) |
| **Min cache tokens** | 1,024–4,096 | 4,096 | 1,024 |
| **Storage fees** | None | $1–$4.50/M tokens/hr | None |
| **Tool result offloading** | No | No | File Search (documents only) |
| **Server-side compaction** | Yes (beta, LLM summary) | ADK only (turn-based) | Yes (encrypted blob) |
| **Context editing** | Yes (clear tool uses/thinking) | No API equivalent | Compaction serves this role |
| **SDK auto-caching** | Yes (with header) | Yes (if configured) | Yes (automatic) |

**Key trade-off:** Anthropic saves most per hit (90%) but charges for writes and requires engineering. OpenAI is zero-effort but saves less (50%). Google is in between — automatic with deep savings but storage costs for explicit caches.

---

## TOPIC 2: Large Context Window Architecture

### Google Gemini — 1M+

**Architecture:** Sparse Mixture-of-Experts (MoE) Transformer. The [technical report](https://arxiv.org/abs/2403.05530) confirms this but deliberately withholds specifics (model size, expert count, attention modifications).

**Likely techniques (published but unconfirmed for Gemini):**
- **Infini-Attention** ([arXiv:2404.07143](https://arxiv.org/abs/2404.07143)) — Compressive memory, 114x compression ratio
- **Ring Attention** ([arXiv:2310.01889](https://arxiv.org/abs/2310.01889)) — Distributes across devices in ring topology (UC Berkeley)
- **MELODI** — Hierarchical compression, 8x memory reduction (DeepMind)

**Hardware — TPU co-design:**

| Generation | HBM/Chip | HBM BW | ICI/Chip | Max Pod |
|-----------|----------|--------|---------|---------|
| TPU v5p | 95 GB | 2,765 GB/s | 4,800 Gbps | 8,960 chips |
| **TPU v7 (Ironwood)** | **192 GB** | **7,400 GB/s** | **9,600 Gbps** | **9,216 chips** |

Ironwood "designed specifically for long-context applications approaching million-token windows." 3.2 bytes/FLOP ratio chosen to prevent memory bottleneck.

**Protection strategy:** Trade secrecy (withheld details) + custom silicon moat (TPUs not sold commercially).

**Retrieval quality at 1M:** >99.7% on single-needle NIAH. But **26.3% on MRCR v2 (8-needle)** — multi-hop retrieval degrades severely.

**Tiered pricing:** Higher rates for inputs >200K tokens, confirming long context is genuinely more expensive internally.

**Sources:**
- [Gemini 1.5 Technical Report](https://arxiv.org/abs/2403.05530)
- [Google TPU Architecture Guide](https://introl.com/blog/google-tpu-architecture-complete-guide-7-generations)

---

### OpenAI — 1M (GPT-4.1, GPT-5.4)

**Timeline:**
- GPT-4.1 (April 2025): First OpenAI model at 1,047,576 tokens
- GPT-5.4 (March 2026): 272K standard, up to 1.05M (2x input pricing above 272K)

**Technical approach (revealed via open-source GPT-OSS):**
- **Attention sinks:** Learnable sink token absorbs disproportionate attention on first tokens, preventing sliding-window degradation
- **Alternating dense/banded window attention:** Some layers use full attention, others use local sliding window (descends from 2019 Sparse Transformer)
- **Scaled RoPE:** Additional training stage extends positional encodings beyond initial training length
- **Flex Attention:** Customizable score modifiers with auto-generated Triton kernels

**Compaction as beyond-window strategy:** GPT-5.1-Codex-Max (Nov 2025) introduced natively trained compaction — the model prunes its own interaction history while preserving critical state. NOT just summarization — a trained capability. Enables 24+ hour sessions spanning millions of tokens across multiple windows.

**Hardware:**
- NVIDIA H100/Blackwell (primary)
- Custom "Titan" chip with Broadcom (3nm, HBM3E/HBM4) — inference-only, delayed to H2 2026
- AMD MI300X (~10% AMD stake, Dec 2025)
- Cerebras: 750 MW inference compute through 2028

**Retrieval quality at 1M:** 100% on simple NIAH but only 56.72% on LongMemEval. Benchmarks vs reality gap is significant.

**Sources:**
- [Introducing GPT-4.1 — OpenAI](https://openai.com/index/gpt-4-1/)
- [GPT-OSS Technical Analysis](https://trickle.so/blog/inside-gpt-4-1-technical-analysis)
- [GPT-5.1-Codex-Max — OpenAI](https://openai.com/index/gpt-5-1-codex-max/)
- [Zep — GPT-4.1 Long Context Analysis](https://blog.getzep.com/gpt-4-1-and-o4-mini-is-openai-overselling-long-context/)

---

### Anthropic Claude — 200K → 1M

**Timeline:**
- March 2024: Claude 3 launched at 200K (architecturally capable of 1M+)
- August 2025: 1M preview on Bedrock (beta header, tier 4 only, premium pricing)
- **March 13, 2026: 1M GA** for Opus 4.6 and Sonnet 4.6. **No long-context pricing premium** — flat rate across entire 1M window

**Pricing advantage:** Opus 4.6 at $5/$25 per million tokens (input/output). No surcharge beyond 200K, unlike Gemini and GPT-5.4.

**Hardware — multi-cloud, multi-chip (most diversified of any lab):**
- Google Cloud TPUs: Up to 1M TPUs (Oct 2025 deal, tens of billions). ~600K rented, ~400K Ironwood purchased outright
- AWS Trainium (Project Rainier): Custom supercomputer
- NVIDIA GPUs: Continued significant use
- Three-chip, two-cloud strategy provides resilience (AWS outage did not impact Claude)

**No published architecture paper** for long-context techniques. Dario Amodei (July 2024): "There's no reason we can't make the context length 100 million words today" — suggesting constraint is economic, not technical.

**Retrieval quality at 1M:** Claude Opus 4.6 scores **76% on MRCR v2 (8-needle)** — highest among all frontier models. vs Gemini 3 Pro at 26.3% and Opus 4.5 at 18.5%.

**Beyond-window strategy:** Application-layer compaction (Claude Code), multi-agent architectures, context engineering. NOT natively trained compaction like OpenAI.

**Sources:**
- [Anthropic Context Windows Docs](https://platform.claude.com/docs/en/build-with-claude/context-windows)
- [Claude 1M GA — Beri.net](https://www.beri.net/article/claude-1m-context-window-ga-enterprise-2026)
- [Anthropic TPU Expansion](https://www.anthropic.com/news/expanding-our-use-of-google-cloud-tpus-and-services)
- [Long-Context Retrieval Rankings](https://awesomeagents.ai/capabilities/long-context-retrieval/)
- [Context Rot Research — Chroma](https://research.trychroma.com/context-rot)

---

### Context Window Comparison Table

| Dimension | Anthropic | Google Gemini | OpenAI |
|-----------|-----------|---------------|--------|
| **Max context** | 1M (GA March 2026) | 1M+ (2.5 Pro/Flash) | 1.05M (GPT-4.1, GPT-5.4) |
| **First 1M GA** | March 13, 2026 | Mid 2024 | April 2025 (GPT-4.1) |
| **Long-context premium** | **None (flat rate)** | Yes (>200K) | Yes (GPT-5.4: 2x >272K) |
| **MRCR v2 at 1M (8-needle)** | **76%** (Opus 4.6) | 26.3% (Gemini 3 Pro) | ~70% (GPT-5.2 Thinking) |
| **Architecture** | Undisclosed | Sparse MoE (details withheld) | Attention sinks + alternating dense/window |
| **Primary hardware** | TPUs + Trainium + NVIDIA | TPUs (custom) | NVIDIA H100/Blackwell |
| **Custom chip** | None (multi-vendor) | TPU v7 Ironwood | Titan (delayed H2 2026) |
| **Beyond-window strategy** | App-layer compaction + multi-agent | Developer-managed | Natively trained compaction |
| **Protection** | No published research | Trade secrecy + custom silicon | Sparse Transformer (2019) + GPT-OSS |

---

## TOPIC 3: Context Window Management

### Anthropic

**Base API:** Fully stateless. Client sends full `messages` array every call. Strict alternating user/assistant turns enforced.

**Session management (Agent SDK):** Session IDs stored as local JSONL files at `~/.claude/projects/<encoded-cwd>/*.jsonl`. `resume=<session_id>` continues with full context. Sessions can be forked. NO server-side state — sessions are client-local files.

**No `previous_response_id` equivalent.** No Assistants/Threads API. Philosophical choice: modular approach via MCP (model-agnostic) + Agent SDK + prompt caching instead of monolithic managed state.

**Compaction (API beta, `compact-2026-01-12`):**
- Configurable `trigger_tokens` threshold
- LLM generates summary, replaces prior messages with `compaction` block
- Custom `instructions` for summarization prompt
- Extra sampling step billed separately
- Available on Opus 4.6, Sonnet 4.6

**Context editing (API beta):**
- `clear_tool_uses_20250919` — drops old tool results, keeps N most recent
- `clear_thinking_20251015` — clears extended thinking from earlier turns
- Performance: 29% improvement alone, 39% with memory tool

**Claude Code context management (most sophisticated of any coding agent):**
- Auto-compaction at ~80-95% capacity
- Manual `/compact` (best at ~60% utilization for quality)
- Micro-compaction: selectively removes outdated tool results
- CLAUDE.md survives compaction (re-read from disk)
- Subagents: fresh independent context windows
- Session Memory: background continuous summary writing
- PreCompact hooks: git diff safety net
- `/context` command shows what's consuming space

**Sources:**
- [Messages API Reference](https://docs.claude.com/en/api/messages)
- [Agent SDK Sessions](https://platform.claude.com/docs/en/agent-sdk/sessions)
- [Compaction — Claude API Docs](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [Claude Code Context Management — SitePoint](https://www.sitepoint.com/claude-code-context-management/)
- [Session Memory Compaction Cookbook](https://platform.claude.com/cookbook/misc-session-memory-compaction)

---

### Google Gemini

**Base API:** Stateless (`generateContent`). SDK provides `ChatSession` wrapper that tracks history locally.

**Interactions API (beta, Feb 2026):** Server-side state via `previous_interaction_id` — closest analog to OpenAI's `previous_response_id`. Only conversation history preserved; tool definitions and system instructions must be re-sent each call. Storage: 55 days (paid), 1 day (free).

**ADK three-tier architecture:**
- **Session:** Container for conversation events, state, metadata. Backends: InMemory, Database (PostgreSQL/MySQL/SQLite), VertexAI
- **State:** Key-value store with scoping prefixes: `temp:` (per-invocation), no prefix (session lifetime), `app:`/`user:` (cross-session)
- **Memory:** Long-term knowledge via `add_session_to_memory()` / `search_memory()`. Backends: InMemory (keyword) or VertexAiMemoryBankService (RAG/embeddings)
- **Artifacts:** Named, versioned binary data. Only references go into context, not full data

**ADK compaction:** `EventsCompactionConfig` — sliding-window event summarization. Turn-based triggers only (every N invocations). Claims 60-80% token reduction. Custom summarizer model configurable.

**No API-level truncation:** Exceeding the context window returns 400 error (still consumes rate limit quota). No auto-truncation at API level.

**Sources:**
- [Interactions API](https://ai.google.dev/gemini-api/docs/interactions)
- [ADK Sessions](https://google.github.io/adk-docs/sessions/)
- [ADK Memory](https://google.github.io/adk-docs/sessions/memory/)
- [ADK Context Compression](https://google.github.io/adk-docs/context/compaction/)

---

### OpenAI

**Base API:** Stateless (Chat Completions). Five state management mechanisms:

| Approach | How It Works | Status |
|----------|-------------|--------|
| Client-side array | Developer manages full history | Active |
| `previous_response_id` | Server reconstructs chain, preserves reasoning traces | Active |
| Conversation objects | Server auto-maintains history | Active |
| **Compaction** | `/responses/compact` — opaque encrypted blob. User messages kept. | Active (Dec 2025) |
| Threads | Auto server-side truncation | **Deprecated** — dies Aug 2026 |

**Compaction details:** Encrypted, not human-readable. Proven at scale: 5M tokens, 150 tool calls (Triple Whale case study). GPT-5.1-Codex-Max: natively trained, not just summarization. Tension: compaction breaks prompt cache prefixes.

**Codex CLI auto-compaction:** `auto_compact_limit` triggers `/responses/compact`. Achieves linear-time model sampling despite quadratic request growth.

**Agents SDK session backends:** In-memory (default), SQLite, AsyncSQLite, Redis, SQLAlchemy, Dapr (30+ cloud backends), OpenAI-hosted. Short-term: Last-N sliding window or compaction. Long-term cross-session: requires explicit `RunContextWrapper` implementation.

**Sources:**
- [OpenAI Compaction Guide](https://developers.openai.com/api/docs/guides/compaction/)
- [Conversation State Guide](https://platform.openai.com/docs/guides/conversation-state)
- [Responses API — Sean Goedecke](https://www.seangoedecke.com/responses-api/)
- [Codex Agent Loop — OpenAI](https://openai.com/index/unrolling-the-codex-agent-loop/)
- [Agents SDK Sessions](https://openai.github.io/openai-agents-python/sessions/)

---

### Context Management Comparison Table

| Feature | Anthropic | Google Gemini | OpenAI |
|---------|-----------|---------------|--------|
| **Base API** | Stateless (Messages) | Stateless (generateContent) | Stateless (Chat Completions) |
| **Server-side state** | No (client-side JSONL) | Yes — Interactions API (beta) | Yes — Responses API |
| **State chaining** | `resume=<session_id>` (local) | `previous_interaction_id` | `previous_response_id` |
| **Managed threads** | No (MCP + SDK) | No (ADK sessions client-managed) | Yes (Assistants, deprecated) |
| **Compaction** | LLM summary (beta) | ADK turn-based summarization | Encrypted opaque blob |
| **Context editing** | Clear tool uses / thinking (beta) | No API equivalent | Compaction serves this |
| **Overflow behavior** | Compaction or error | 400 error (API) | Truncation or error |
| **Long-term memory** | CLAUDE.md + MEMORY.md | ADK Memory (RAG-based) | Assistants file storage |
| **Agent framework** | Agent SDK (sessions, subagents) | ADK (sessions, state, memory) | Agents SDK (pluggable backends) |

---

## TOPIC 4: Patent Landscape

### Anthropic Patents

**Portfolio:** ~61 patents across 18 families in 8 jurisdictions. **60 of 61 were acquired** (primarily from IBM), only ~5 originally filed by Anthropic.

**Original filings (all focused on computer use / GUI automation):**
- **US 12,387,036 B1** — First US patent. 234 pages. "Magnitude-invariant image-text agentic interface automation." Core computer use technology.
- **US 12,437,238** — Training data generation for agent interface automation. Inventors include David Luan (former Adept CEO).
- **US 2025/0299023** — Prompt construction for multimodal interface workflows.

**Most-cited acquired patent:** US11,361,571B1 ("Term extraction in highly technical domains") — acquired from IBM.

**What Anthropic has NOT patented:**
- Prompt caching / cache_control mechanism
- Context editing or compaction
- Tool result handling / tool use protocol
- Agent SDK architecture or session management
- Multi-session agents or agent chaining
- MCP (Model Context Protocol)

**Strategy:** Acquisition-heavy defensive portfolio + narrow original filings on computer use. No defensive patent pledge published. No litigation history.

**Sources:**
- [Lumenci — Anthropic Patent Portfolio](https://lumenci.com/patent-portfolio/anthropic/)
- [Justia — Anthropic Patents](https://patents.justia.com/assignee/anthropic-pbc)
- [The Best Practice Podcast — Anthropic's Agentic AI Patent](https://thebestpractice.podigee.io/35-the-secret-behind-anthropic-s-agentic-ai-patent-claude-adept-amazon)

---

### Google Patents

**What Google HAS patented:**
1. **The Transformer** — US10,452,978 ("Attention-Based Sequence Transduction Neural Networks"). 7+ continuations. NOT in Open Source Non-Assertion Pledge.
2. **Sparse attention** — US20230022151A1 ("Full Attention with Sparse Computation Cost"). Directly addresses quadratic limitation.
3. **Universal Transformers** — US10,740,433. Adaptive computation time.
4. **Merged linear layers** — App #20250190798 (Dec 2024). Inference efficiency.

**What Google has NOT patented:** No specific patent on 1M context technique, Gemini's MoE configuration, or the attention modification enabling long context.

**Protection strategy:** Trade secrecy (withheld architecture details) + custom silicon moat (TPUs not commercially available) + broad foundational patents. 1,837 AI-related applications globally (~50% more than Microsoft).

**Sources:**
- [Google Transformer Patents — PI IP LAW](https://piip.co.kr/en/blog/google-transformer-llm-patent-risk-and-strategy)
- [US10,452,978 — Google Patents](https://patents.google.com/patent/US10452978B2/en)
- [US20230022151A1 — Google Patents](https://patents.google.com/patent/US20230022151A1/en)

---

### OpenAI Patents

**Portfolio:** ~110 patents globally, 42 granted, 93%+ active. Filed under OpenAI Opco LLC. Accelerated prosecution: 11-month average (industry: 24 months). Primarily US-only (96 of 110).

**Key granted patents:**

| Patent | Title | Area |
|--------|-------|------|
| US 11,886,826 B1 | Language Model-based Text Insertion | Text generation |
| US 11,922,144 B1 | Schema-based Integration of External APIs | API/tool integration |
| US 11,922,550 B1 | Hierarchical Text-conditional Image Generation | DALL-E |
| US 12,079,587 B1 | Multi-task Automatic Speech Recognition | Whisper |
| **US 12,405,822 B1** | **Multi-Agent Interactions Using a Shared Workspace** | **Multi-agent orchestration** |
| **US 12,406,207 B2** | **Generating Customized AI Models** | **Custom GPTs / RAG pipeline** |

**US 12,405,822 is significant:** Covers shared digital workspace as command ledger where agents can view state, post commands, or **yield** (abstain when another agent is better suited). Broad claims covering general multi-agent coordination protocols. **Anyone building multi-agent systems should review this patent.**

**US 12,406,207 covers RAG broadly:** Chunking documents, embedding, storing in vector databases, retrieving for augmented generation.

**What OpenAI has NOT patented:**
- Context compression / compaction
- Assistants/Threads architecture
- Prompt caching mechanism
- Streaming protocols
- Conversation threading

**Defensive patent pledge:** Published Oct 2024 — "only use our patents defensively." BUT: legally non-binding website statement, unilaterally revocable, does not travel with asset sales, and the "harm" exception is broad enough to cover competitors. ([MBHB analysis](https://www.mbhb.com/intelligence/snippets/openais-patent-licensing-promise-is-not-what-it-seems/))

**Sources:**
- [Originality.AI — OpenAI Patent List](https://originality.ai/blog/openai-patent-list)
- [GreyB — OpenAI Patents](https://insights.greyb.com/openai-patents/)
- [BESTPATENT — Two New OpenAI Patents](https://bestpatent.eu/two-new-openai-patents-you-should-know-about/)
- [OpenAI — Our Approach to Patents](https://openai.com/approach-to-patents/)

---

### Third-Party Patents (Adjacent)

| Patent | Title | Relevance |
|--------|-------|-----------|
| **US 12,387,050** | Multi-stage LLM with unlimited context | Thought caching between model tiers. **Different mechanism** than file-based communication. |
| **US 12,111,859 B2** (C3.AI) | Enterprise generative AI architecture | Multi-agent orchestration. Does NOT cover file-based token cost reduction. |
| US 7,024,656 B1 | Persistent agents | Pre-LLM object persistence. Not specific to LLM context. |

---

### THE BIG FINDING: No Patent Covers the Core Concepts

| Concept | Anthropic | Google | OpenAI | Any Company |
|---------|:---------:|:------:|:------:|:-----------:|
| File-based agent communication to reduce token costs | NO | NO | NO | **NO** |
| Offloading conversation history to persistent storage | NO | NO | NO | **NO** |
| Agent session chaining through file persistence | NO | NO | NO | **NO** |
| Reducing LLM API costs via file-based message passing | NO | NO | NO | **NO** |
| Context window extension through agent chaining | NO | NO | NO | **NO** (closest: US 12,387,050) |
| Prompt caching mechanism | NO | NO | NO | **NO** |
| Context compaction/compression | NO | NO | NO | **NO** |

**All three companies protect these capabilities as trade secrets, not patents.**

**Caveat:** 18-month patent publication delay means applications filed after Sept 2024 may not yet be visible. Professional USPTO PAIR/WIPO search needed for unpublished applications.

---

## TOPIC 5: Prior Art

### File-Based Agent Communication

**EXTENSIVE PRIOR ART EXISTS:**

- **Blackboard Architecture (1980s+)** — Agents read/write to shared space. Google Research 2025 paper applied to LLM agents ([arXiv:2510.01285](https://arxiv.org/abs/2510.01285))
- **Manus (2024-2025)** — File system as "infinite memory," 100:1 compression ([Manus Blog](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus))
- **LangChain Deep Agents (2025)** — Auto-offloads tool results >20K tokens to filesystem with path references ([LangChain Blog](https://blog.langchain.com/context-management-for-deepagents/))
- **Fast.io** — Shared file workspaces, 35% processing time reduction ([Fast.io](https://fast.io/resources/agent-to-agent-file-communication-protocols/))

### Session Chaining Concepts

- **Chain-of-Agents (CoA)** — Google Research, NeurIPS 2024. Sequential agents passing context. ([arXiv:2406.02818](https://arxiv.org/abs/2406.02818))
- **Git Context Controller (GCC)** — COMMIT/BRANCH/MERGE for agent memory, 80%+ SWE-Bench ([arXiv:2508.00031](https://arxiv.org/abs/2508.00031))
- **Graph of Agents** — Extends CoA to graph topologies ([arXiv:2509.21848](https://arxiv.org/html/2509.21848v1))
- **MemGPT/Letta (2023)** — Context as "RAM," external storage as "disk" ([arXiv:2310.08560](https://arxiv.org/abs/2310.08560))

### Company-Specific Implementations

**Anthropic — Claude Code:**
- JSONL session files at `~/.claude/projects/<encoded-path>/`
- Three-tier CLAUDE.md hierarchy (Global > Project > Local)
- Auto-generated MEMORY.md (200-line limit, topic files)
- Session Memory: background continuous summarization
- `--continue` / `--resume <id>` for session chaining
- `compact_boundary` records link parent/child sessions
- Published "Effective Context Engineering" blog (Sep 2025)

**OpenAI — Codex CLI:**
- JSONL rollout files at `~/.codex/sessions/YYYY/MM/DD/`
- AGENTS.md hierarchy (AGENTS.override.md > AGENTS.md, root-to-CWD walk)
- 32 KiB size limit for instruction files
- `codex resume` / `codex resume --last` / `codex resume <id>`
- SQLite-backed state for resumable runtime
- Published multiple cookbook resources on context engineering

**Google — ADK / Gemini CLI:**
- GEMINI.md files (Gemini CLI only, not ADK framework)
- ADK: pluggable session backends (InMemory, SQLite, Vertex AI, GCS)
- Three-tier architecture: Session + State + Memory
- `user:` / `app:` state prefixes for cross-session persistence
- Published "Context-Aware Multi-Agent Framework" blog (Dec 2025)

### Cross-Company Convergence

All three have independently converged on the same pattern:
1. Markdown instruction file loaded at session start (CLAUDE.md / AGENTS.md / GEMINI.md)
2. Structured session logs (JSONL) with resume capability
3. Compaction/summarization for long-running tasks
4. Some form of persistent memory across sessions

### What Has NO Prior Art

- **"Walkie-talkie"** as a metaphor for file-based agent communication — term not used anywhere
- **"Super agent chain"** as a named concept — underlying mechanism well-established under other names

**Sources:**
- [Claude Code Session Continuation](https://blog.fsck.com/releases/2026/02/22/claude-code-session-continuation/)
- [Codex CLI Reference](https://developers.openai.com/codex/cli/reference)
- [Gemini CLI Configuration](https://google-gemini.github.io/gemini-cli/docs/get-started/configuration.html)
- [Anthropic Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Google Developers Blog — Multi-Agent Framework](https://developers.googleblog.com/architecting-efficient-context-aware-multi-agent-framework-for-production/)

---

## Master Comparison Tables & Conclusions

### Complete Provider Comparison

| Capability | Anthropic Claude | Google Gemini | OpenAI |
|---|---|---|---|
| **Max context** | 1M (GA Mar 2026) | 1M+ (2.5 Pro/Flash) | 1.05M (GPT-4.1/5.4) |
| **Long-ctx premium** | **None (flat)** | Yes (>200K) | Yes (>272K) |
| **MRCR v2 1M** | **76%** | 26.3% | ~70% |
| **Caching type** | Manual breakpoints | Auto + Explicit | Fully automatic |
| **Cache read savings** | 90% | 90% | 50% |
| **Cache write cost** | 1.25x–2x | Free | Free |
| **Max cache TTL** | 1 hour | Configurable | **24 hours** |
| **Server-side state** | No | Yes (Interactions beta) | Yes (Responses API) |
| **Compaction** | LLM summary (beta) | ADK turn-based | Encrypted blob |
| **Tool result offload** | No | No | File Search only |
| **Agent framework** | Agent SDK | ADK | Agents SDK |
| **Instruction file** | CLAUDE.md (3-tier) | GEMINI.md (CLI) | AGENTS.md (2-tier) |
| **Session format** | JSONL (local) | Pluggable backends | JSONL rollouts + backends |
| **Patents (total)** | ~61 (60 acquired) | 1,837+ AI-related | ~110 (42 granted) |
| **Patents on caching/context** | None | Sparse attention only | None |
| **Defensive pledge** | None | Open Source pledge (partial) | Published (non-binding) |
| **Hardware** | TPU + Trainium + NVIDIA | TPU (custom) | NVIDIA + Titan (delayed) |

### Key Conclusions

1. **No provider truly offloads tool results server-side.** All cache KV representations for compute savings, but the full messages array must be sent every time. This is a compute optimization, not a transfer optimization.

2. **No company has patented prompt caching, context compaction, or tool result handling.** These are all protected as trade secrets. The patent landscape for file-based agent communication is entirely empty.

3. **All three companies converged on the same file-based context pattern** (instruction file + session logs + compaction) independently, confirming it as a natural engineering solution.

4. **Context quality matters more than context size.** Claude Opus 4.6 at 1M scores 76% on multi-hop retrieval vs Gemini 3 Pro at 26.3% — nearly 3x better despite similar window sizes.

5. **The "file-based communication to reduce token costs" concept has extensive prior art** but no patent coverage. Manus (2024), LangChain (2025), MemGPT (2023), Chain-of-Agents (2024), and GCC (2025) all describe variants.

6. **OpenAI's multi-agent shared workspace patent (US 12,405,822) is the broadest threat** to the multi-agent ecosystem. Its "yielding" mechanism and shared command ledger claims are broadly written.

7. **Google protects via hardware moat + trade secrecy.** The specific technique enabling 1M context is unknown. TPUs are not commercially available.

8. **Anthropic's patent portfolio is almost entirely acquired.** Original filings cover only computer use (GUI automation), not the API/SDK/agent infrastructure.

### Patent Gap Summary

The following concepts appear to exist in a **patent gap** — widely practiced but unpatented:

| Concept | Status |
|---------|--------|
| File-based agent communication to reduce API token costs | **UNPATENTED** — extensive prior art |
| Session chaining through persistent files | **UNPATENTED** — extensive prior art |
| Prompt caching / KV-cache management | **UNPATENTED** by any provider |
| Context compaction / compression | **UNPATENTED** by any provider |
| Tool result offloading to external storage | **UNPATENTED** — no one does it |
| Markdown instruction files for agents | **UNPATENTED** — convergent evolution |
| "Walkie-talkie" file-based agent communication | **NO PRIOR ART** — term unused |
| "Super agent chain" concept | **NO PRIOR ART for the name** — mechanism well-established |
