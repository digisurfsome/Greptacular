# The Five Durable Verticals of the Agentic Web

**Source:** YouTube video transcript — AI app builder landscape analysis
**Core thesis:** AI commoditizes production. The companies and builders that survive own layers that production cannot replace. There are five such layers.

---

## Section 1: The Collapse of the Build Layer

### What's happening

A dozen+ companies are racing to build platforms where you describe an app and it appears. They are all converging on the same pitch: "Tell us your idea, AI builds it for you." Since the rise of agentic coding tools (OpenClaw, Claude Code, Codex), that pitch has expanded to: "Tell us your idea and we'll build your entire business."

### The players and their scale

| Company | Scale / Position |
|---------|-----------------|
| **Lovable** | $330M raise, $6.6B valuation, $300M+ ARR, 100,000+ new projects created per day |
| **Replit** | ~25M developers on platform |
| **Vercel (V0)** | ~4M users |
| **Bolt, Shipper, Base44** | Smaller players, same core pitch |
| **Long tail** | Dozens more fighting over the same lane |

### Why they're all functionally the same

- Most are thin UI wrappers around the same base models (Claude, ChatGPT, Gemini)
- Some use open-source models (Qwen, etc.) to reduce token costs
- They differentiate on pitch, UI, pricing, minor feature twists (AI advisor, visual editor, etc.)
- Underneath, structurally identical

### The middleware trap

- When your product is a UI layer on top of someone else's intelligence, your moat is as deep as the time it takes to replicate the UI
- With Claude Code and Codex, that replication time is about a week or less
- A better model from any provider can instantly make your wrapper obsolete

### The "train your own model" escape attempt

Several companies are trying to escape by training proprietary models:

| Company | Model training approach |
|---------|----------------------|
| **Cursor** | Training their own model to compete for developer time/tokens |
| **Replit** | Trained code completion models via Databricks, released open-source on Hugging Face, used for inline suggestions where cost efficiency matters |
| **Lovable** | Has $300M+ ARR cash to attempt the same play |
| **Vercel** | Trained a custom autofix model with Fireworks AI for catching code generation errors during streaming; updated ToS to use customer code for training |

### Why model training alone isn't the answer

Training your own model is not what separates survivors from casualties. The companies that make it through the middleware trap share a different trait: **they own something structural that model providers cannot replicate.**

---

## Section 2: The Central Question

> "If building things is essentially going to be free, what is actually worth building a company around?"

### The strategic question for every builder

Whether you're a big company or a solo founder building a side project, you need to answer: **Are there spaces between the model makers and end users that are safe to build in — where the model makers won't just make a better model and take the space?**

### Three examples of structural ownership

| Company | Why it survives | What it owns |
|---------|----------------|--------------|
| **Replit** | Claude can't execute your code. Replit owns the runtime — the actual compute environment where applications live. That's a different value proposition than "we call an API and show you the output." | Runtime / execution environment |
| **Vercel** | Not an AI wrapper with hosting. An infrastructure company that built an AI front door. Hosts production apps for OpenAI, Anthropic, Nike, PayPal. Nobody else has that deployment infrastructure. | Deployment infrastructure |
| **Notion** | Doesn't pretend to want to train a model. Offers a model picker (ChatGPT, Claude, Gemini). Their bet: 100M users have built the largest structured knowledge graph of organizational info on the planet. Every model needs to come to them to access it. | User-generated knowledge graph |

---

## Section 3: The Five Durable Verticals of Value

These are not product categories. They are layers of value that persist regardless of how good models get. No single company can fully own any one of them. The agentic economy makes each more important, not less.

---

### Vertical 1: Trust

#### The problem trust solves

The web is being flooded with millions of AI-generated apps, services, storefronts, and content streams created daily. Most are indistinguishable from each other. Most are garbage. Some are actively malicious. When anyone can generate a professional-looking checkout page in seconds, looking legitimate no longer means being legitimate.

#### What trust companies do

They become the verification layer:
- "This app will not steal your credit card — and we back it up"
- "This service actually does what it claims — and we back it up"
- "This content was produced by someone real who can be held accountable"

#### Why trust matters more in the agentic economy

- Noise proliferation is exponential compared to the human web
- AI agents will autonomously transact on your behalf (booking flights, signing up for services, making purchases)
- The trust layer is all that stands between you and a universe of AI-generated scams
- Agents themselves need trust signals to operate: Which payments are safe? Which services are verified? Which APIs won't steal data?
- If an agent cannot verify a service, it won't transact on it, likely won't even use it, and in many cases won't be allowed to

#### Trust becomes a walled garden

Trust providers become the routing layer for responsible web traffic. It won't be one player — a hedge of major players will collectively secure the agentic future.

#### Companies playing in trust

| Company | Trust position |
|---------|---------------|
| **Stripe** | "Powered by Stripe" is no longer a technical feature — it's a trust signal. Over $1 trillion in transactions processed. |
| **Shopify** | Trusted commerce platform |
| **Apple App Store** | Review process = trust verification |
| **Vercel** | Deployment infrastructure implies production-grade trust |

#### Key insight

An LLM cannot replicate trust. Trust is earned through track record, accountability, and real-world consequences — none of which a model can provide.

---

### Vertical 2: Context

#### The problem context solves

AI is a general application tool. To be useful, it needs data specific to your situation:
- Your company's data
- Your customer relationships
- Your medical records
- Your meeting notes from last Tuesday

#### What context companies own

They become the authoritative store for context AND the permissioning layer that governs where context gets served. They own the choke point — every agent, every model, every workflow has to flow through the context layer.

#### The Notion example in depth

- Built custom agents that took off immediately (tens of thousands to hundreds of thousands built by users)
- Agents run autonomously across each individual user's workspace
- The context is what makes the agents valuable — not the AI capability
- Notion didn't recognize that AI is powerful. They recognized that their context is the secret sauce, and any AI brought into it becomes super powerful for users.

#### The structural data play

This is the same structural advantage that makes these companies durable:

| Company | Context domain |
|---------|---------------|
| **Notion** | Organizational knowledge / workspace data |
| **Salesforce** | Customer relationship data |
| **Epic** | Healthcare records |
| **Palantir** | Security / intelligence data |
| **Snowflake / Databricks** | Enterprise data warehousing |
| **Apple / Google** | Local AI + device-level personal context |
| **Google Maps** | Recently launched a context layer for maps — geographic/location context |

#### Why context locks in

- An agent without context is just a chatbot
- An agent with your context can be a dependable junior employee
- That difference is massive and observable right now
- Correct prompting is increasingly about: "Here's my context. Here's where to search for more. Are we good?" — then the agent executes

#### Context as revenue source

When AI agents become the primary way work gets done, the mechanism by which agents get information becomes a source of revenue and dependable competitive advantage.

#### Google's multi-angle position

Google keeps showing up with multiple ways to win:
- Model player (Gemini)
- Foundation player (TPUs)
- Context player (Maps context layer, Search data)
- Ecosystem player
- Devices player (Android, Pixel)

---

### Vertical 3: Distribution

#### The problem distribution solves

You can generate an app in seconds, but who's going to see it?

#### The lesson second-time founders know

> The bottleneck was never about building the thing. It was always about distributing it. "Build it and they will come" is never how it works. You build it, then you round people up, get them to come, and see if they'll pay for it.

#### Why distribution matters more now

When supply is infinite (10x or 100x more software being generated), **curation becomes the scarcest resource in the world.** You must have an edge in distribution to be heard, seen, or get any signal from customers at all.

#### Current distribution monopolies

| Player | Distribution channel |
|--------|---------------------|
| **Google** | Search and discovery |
| **Apple** | App Store |
| **TikTok** | Short-form content discovery |
| **YouTube** | Long-form content discovery |
| **Amazon** | Commerce discovery |
| **Substack** | Written content distribution |

AI makes these gatekeepers more powerful, not less. When the flood is bigger, the gatekeepers who tell people where to go become more critical.

#### The agentic distribution problem

Agent discovery is a massive unsolved problem. If every business has AI agents:
- How do agents discover where to go to do business with one another?
- How do agents discover where to go to do business with humans?

#### The need for an agent-native app store

A new distribution layer is emerging. We need something like an agent-native app store that allows agents to find and use utilities or businesses that are agent-friendly.

#### What makes a business viable for agent transactions

This is described as "one of the most interesting questions of 2026." It's much more than putting up an MCP server. You have to think about:

1. **Transaction speed** — How fast does the transaction work?
2. **Discoverability** — How easy is it for the agent to understand the depth of what you offer?
3. **Selection simplicity** — How quick is it for the agent to make a selection and operate with your API?
4. **Delivery clarity** — How simple is it for the agent to receive the good or service?

The entire mechanism for commerce has to be rethought with agents at the core. Almost no businesses are thinking like this yet.

#### Why this is bullish for content creators

If you establish yourself as a niche authority in AI, people can use you to get useful signal they can't get elsewhere. Authority in distribution = durable advantage.

---

### Vertical 4: Taste

#### What taste means (not ambiguous)

When producing software is free, **what you choose to produce** becomes the entire game.

Taste includes:
- Product decisions
- Design sensibility
- Editorial judgment about what's worth building and what's not
- The ability to look at AI-generated output and know if it's right or wrong
- Accountability for those judgments
- A conviction about what should exist in the world that is not easily derivable from training data
- A point of view on how humans do business with humans

#### The music production analogy

After GarageBand went mainstream (and now with Suno generating AI music in seconds):
- Tools became free. Everyone can make a track. The flood of music is enormous.
- The producers and artists who thrive are NOT the ones with the most expensive studio (production is free)
- They're the ones with **taste** — an idea of what will work with the audience, an ear for how music plays in different settings, a choice to produce something that connects

#### The same thing is happening to software

- The vibe coder who ships an app in minutes hasn't done the hard part yet
- The hard part: **How is what I'm building going to deeply connect with my audience?**

#### Two expressions of taste

1. **Design sense** — how the product looks and feels
2. **Value proposition accuracy** — absolutely nailing the angle that resonates with a felt need

The best products have both. If you have to pick one, you pick value proposition (which is why there are so few design-led companies). But both are powerful engines for companies that achieve product-market fit.

#### Taste on the agentic web = orchestration quality

- Winning agent systems won't necessarily have the best underlying models
- They'll be the ones where a human with deep domain expertise has:
  - Carefully tuned the prompts
  - Designed the workflows
  - Chosen the right tools
  - Made a thousand small editorial decisions about agent behavior
- The result: a curated experience that does powerful work

#### Will auto-research change this?

- Auto-research applied to agentic harnesses may lead to agents that self-evolve
- Agents may be intentionally, automatically evolved by humans supervising the process
- BUT: The human's responsibility to say "this is the direction, this is the goal, this is what good looks like" — that doesn't change
- Regardless of how far above the loop the human sits, they remain accountable for what the agent does and how it participates in the economy
- Taste is not being abdicated even with more powerful tools

---

### Vertical 5: Liability

#### The problem liability solves

Someone has to be on the hook.

- When an AI-generated financial plan loses you money — who's liable?
- When an AI-built medical app gives bad advice — who's liable?
- When an AI-generated contract has a bad clause you litigate and lose over — who's liable?

**"The AI did it" is not going to be an answer that survives court.**

#### Why regulated industries are liability niches

Healthcare, finance, legal, insurance — the professionals in these spaces are selling accountability. That's fundamentally why lawyers stay in business: they sell accountability before the court for how a case is represented.

#### The counterintuitive dynamic

The better AI gets at sounding plausible, the MORE important authentic accountability becomes. The mistakes you can make with a plausible-sounding AI get much more serious, not less.

#### Liability in the agentic economy = governance layer

- AI agents will autonomously execute complex workflows
- They'll file documents, potentially move money, make commitments with your name on them
- Someone needs to: define boundaries, audit actions, and ultimately be liable
- Companies and professionals who position as liability guarantors or accountability makers own the governance layer for the future web

#### Companies playing in liability

| Player | Liability position |
|--------|-------------------|
| **Deloitte, McKinsey** | Repositioning as AI assurance providers |
| **ElevenLabs** | Offering insurance for voice agents |
| **Veeva, Elation** | Regulated SaaS platforms in healthcare |
| **AI safety professionals** | Providing safety and vetting protocols for agents |

This is a patchwork space — scaled consulting firms doing billions alongside small mom-and-pop shops. All in the business of making agents safer to run and handling the liability layer. Expected to grow quickly.

---

## Section 4: The Future Web — All Layers Together

### The layer map

| Layer | Who owns it | Why it's durable |
|-------|------------|-----------------|
| **Bedrock intelligence** | OpenAI, Anthropic, Google | Own the foundational model capability. Enormously valuable but increasingly commoditized relative to each other. Even open-source models will be derivations of these lineages — influence persists regardless. |
| **Wrapper companies** | Lovable, Bolt, Shipper | Don't own anything structurally durable. Most will die. Some get acquired. A few with enough user data/momentum (Lovable is a strong candidate) get a shot at becoming a platform — Lovable's play is to be Shopify 2.0. |
| **Infrastructure** | Vercel, Replit, Stripe, Shopify | Own the trust and execution layers. AI makes them more valuable because more things being built = more trust, verification, and payments needed. They are the picks and shovels of the AI gold rush. |
| **Context owners** | Notion, Salesforce, Snowflake, Databricks | Own data gravity. Agents need context to be useful. Context gets locked inside these platforms. They become the permissioning layer for the agentic economy if they play it right. |
| **Distribution gatekeepers** | Google, Amazon, Apple | Own how humans pay attention on the internet. If they play it right, they also own how agents pay attention. |
| **Human operators** | Founders, professionals, individuals | Provide taste, judgment, accountability — the connective tissue. AI doesn't replace what humans bring. Understanding web structure lets humans be above the loop, providing direction strategically. |

---

## Section 5: The Builder's Decision Framework

### The one question every builder must answer

> "What do I own that still matters if AI gets 10x better?"

### If the answer is "nothing"

- A better model makes your product obsolete
- Change your positioning now
- Assume models will get better (they will)

### If a better model makes your product MORE valuable

- You own a piece of trust, liability, context, distribution, or taste
- You want smarter agents to enable the economy you're building for
- You have something durable to build on
- You don't have to lose sleep over the next Claude release

### The distribution warning

The biggest gap in the current builder ecosystem:

- All the energy around tools like Lovable and Replit has gone into creation
- Almost none has been piped into distribution
- Result: 100,000 to 10,000,000 apps blooming, most never discovered
- No one put thought into whether someone actually wants the product
- **Building an MVP in a day is great. Your actual job is to put it in front of customers, get feedback, and validate that you're building something they want.**
- That is a deeply human activity
- There is no substitute for distribution

---

## Section 6: Summary — The Forcing Function

### The five verticals restated

| # | Vertical | One-line definition | Why AI can't replace it |
|---|----------|-------------------|----------------------|
| 1 | **Trust** | Verification that something is safe, real, and accountable | Earned through track record and real-world consequences |
| 2 | **Context** | Your specific data, relationships, and situation | General models need it but can't generate it |
| 3 | **Distribution** | Getting your product seen by the right people | Curation requires judgment about human attention |
| 4 | **Taste** | Conviction about what should exist that isn't derivable from training data | Requires a point of view on human-to-human value |
| 5 | **Liability** | Accountability when things go wrong | Legal systems require a human on the hook |

### The meta-insight

These five things have always mattered on the web. AI is a forcing function that makes them matter more. AI cannot take their place. That is why they are durable places to build in the agentic economy.
