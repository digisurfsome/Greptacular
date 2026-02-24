"""
SaaS Strategy Engine — Interactive chat-based strategy builder.

Based on Alex Becker's SaaS Transition Thesis, this engine walks users through
a step-by-step process to evaluate their software idea, classify it against
the surviving SaaS categories, and generate a personalized game plan.

Can be run standalone (CLI) or imported as a module for web integration.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

# ─── Categories from Becker's Thesis ────────────────────────────────────────

class SaaSCategory(str, Enum):
    """The surviving SaaS categories from Becker's thesis."""
    API_INFRASTRUCTURE = "api_infrastructure"
    COMPLEX_INFRASTRUCTURE = "complex_infrastructure"
    NETWORK_EFFECT = "network_effect"
    OPEN_FRAMEWORK = "open_framework"
    CUSTOM_SAAS_SERVICE = "custom_saas_service"
    TEMPLATE_MARKETPLACE = "template_marketplace"
    CONNECTOR_PLATFORM = "connector_platform"
    # Dead/dying
    GENERIC_PLATFORM = "generic_platform"
    SIMPLE_TOOL = "simple_tool"
    NO_MOAT_SAAS = "no_moat_saas"


CATEGORY_INFO = {
    SaaSCategory.API_INFRASTRUCTURE: {
        "name": "API / Infrastructure Company",
        "description": "You provide the building blocks other apps plug into. Payment processing, email delivery, SMS, auth, database hosting, etc.",
        "examples": ["Stripe", "Twilio", "SendGrid", "Supabase", "Clerk"],
        "moat": "Infrastructure complexity + ecosystem lock-in + usage-based revenue",
        "risk_level": "Low",
        "revenue_model": "Usage-based pricing",
        "survivability": "Thriving — every app built needs infrastructure",
    },
    SaaSCategory.COMPLEX_INFRASTRUCTURE: {
        "name": "Complex Infrastructure SaaS",
        "description": "Your backend is so complicated that even if someone can code the interface, maintaining accuracy and handling edge cases is hell on earth.",
        "examples": ["Hyros (ad tracking)", "Datadog", "Databricks", "Snowflake"],
        "moat": "Deep domain expertise + data accuracy + maintenance burden too high to DIY",
        "risk_level": "Low",
        "revenue_model": "Subscription + usage-based",
        "survivability": "Thriving — can't be replicated by vibe coding",
    },
    SaaSCategory.NETWORK_EFFECT: {
        "name": "Network Effect Platform",
        "description": "The value isn't the software — it's the people on it. Users attract users. Being on the platform = distribution.",
        "examples": ["School (Hormozi)", "LinkedIn", "Marketplaces"],
        "moat": "Community + distribution + switching cost is leaving the network",
        "risk_level": "Low-Medium",
        "revenue_model": "Subscription + marketplace fees",
        "survivability": "Thriving — network effects can't be vibe coded",
    },
    SaaSCategory.OPEN_FRAMEWORK: {
        "name": "Open-Source Framework / Widely-Used Foundation",
        "description": "You build the foundation everyone builds on. The more people use it, the more valuable the ecosystem becomes.",
        "examples": ["WordPress", "Next.js", "React", "OpenClaw"],
        "moat": "Ecosystem lock-in + community contributions + integration breadth",
        "risk_level": "Medium",
        "revenue_model": "Hosting/premium features + ecosystem revenue + enterprise",
        "survivability": "Thriving — becomes the default foundation",
    },
    SaaSCategory.CUSTOM_SAAS_SERVICE: {
        "name": "Custom SaaS Service / Agency",
        "description": "You master frameworks early, build custom software stacks for businesses, and rent/maintain them. $5K build + $1K/month.",
        "examples": ["Boutique dev agencies", "Verticalized SaaS builders"],
        "moat": "Speed + expertise + playbook + client relationships",
        "risk_level": "Medium",
        "revenue_model": "Upfront build fee + monthly maintenance + affiliate revenue",
        "survivability": "New opportunity — massive demand incoming",
    },
    SaaSCategory.TEMPLATE_MARKETPLACE: {
        "name": "Template / Framework Marketplace",
        "description": "You build and sell high-quality templates that people customize and build on.",
        "examples": ["ThemeForest (legacy)", "Shadcn/ui", "Vercel templates"],
        "moat": "Quality + ecosystem + community contributions",
        "risk_level": "Medium-High",
        "revenue_model": "One-time sales + subscriptions + affiliate on connected services",
        "survivability": "Growing — templates are the new SaaS products",
    },
    SaaSCategory.CONNECTOR_PLATFORM: {
        "name": "Connector / Orchestration Platform",
        "description": "You build the glue that connects templates and mini-apps together. The orchestration layer.",
        "examples": ["Zapier (legacy)", "AutoForge-style builders"],
        "moat": "Integration breadth + reliability + ecosystem",
        "risk_level": "Medium",
        "revenue_model": "Subscription + usage-based + affiliate",
        "survivability": "Thriving — someone needs to bind everything together",
    },
    SaaSCategory.GENERIC_PLATFORM: {
        "name": "Generic Feature Platform (DYING)",
        "description": "You sell a monolithic platform where users only use 1-2 features. The rest is bloat they'll build themselves.",
        "examples": ["Kajabi", "Generic CRMs", "All-in-one platforms"],
        "moat": "Eroding — users will download templates and customize",
        "risk_level": "Critical",
        "revenue_model": "Subscription (declining)",
        "survivability": "DYING — pivot to infrastructure/API or die",
    },
    SaaSCategory.SIMPLE_TOOL: {
        "name": "Simple Tool SaaS (DYING)",
        "description": "A tool that can be one-shot vibe coded. Booking forms, landing page builders, simple dashboards.",
        "examples": ["Calendly (booking only)", "Simple form builders", "Basic landing page tools"],
        "moat": "None — can be built in a single prompt",
        "risk_level": "Critical",
        "revenue_model": "Subscription (dying)",
        "survivability": "DYING — will be replaced by templates",
    },
    SaaSCategory.NO_MOAT_SAAS: {
        "name": "No-Moat SaaS (DYING)",
        "description": "Software with no network effects, no complex infrastructure, no ecosystem. The value is purely the code.",
        "examples": ["Any SaaS where the only value is the feature set"],
        "moat": "None — code is commodity",
        "risk_level": "Critical",
        "revenue_model": "Subscription (dying)",
        "survivability": "DYING — pivot or exit",
    },
}


# ─── Strategy Engine Steps ──────────────────────────────────────────────────

class EngineStep(str, Enum):
    """Steps in the strategy walkthrough."""
    WELCOME = "welcome"
    IDEA_CAPTURE = "idea_capture"
    CATEGORY_ASSESSMENT = "category_assessment"
    MOAT_ANALYSIS = "moat_analysis"
    REVENUE_MODEL = "revenue_model"
    AUDIENCE_STRATEGY = "audience_strategy"
    COMPETITIVE_POSITION = "competitive_position"
    TIMELINE_PLANNING = "timeline_planning"
    RISK_ASSESSMENT = "risk_assessment"
    GAME_PLAN_GENERATION = "game_plan_generation"
    COMPLETE = "complete"


STEP_SEQUENCE = [
    EngineStep.WELCOME,
    EngineStep.IDEA_CAPTURE,
    EngineStep.CATEGORY_ASSESSMENT,
    EngineStep.MOAT_ANALYSIS,
    EngineStep.REVENUE_MODEL,
    EngineStep.AUDIENCE_STRATEGY,
    EngineStep.COMPETITIVE_POSITION,
    EngineStep.TIMELINE_PLANNING,
    EngineStep.RISK_ASSESSMENT,
    EngineStep.GAME_PLAN_GENERATION,
    EngineStep.COMPLETE,
]


# ─── Data Models ────────────────────────────────────────────────────────────

@dataclass
class IdeaProfile:
    """User's software idea profile built through the conversation."""
    raw_description: str = ""
    name: str = ""
    one_liner: str = ""
    target_audience: str = ""
    problem_solved: str = ""
    existing_alternatives: list[str] = field(default_factory=list)
    primary_categories: list[SaaSCategory] = field(default_factory=list)
    secondary_categories: list[SaaSCategory] = field(default_factory=list)
    danger_categories: list[SaaSCategory] = field(default_factory=list)
    infrastructure_components: list[str] = field(default_factory=list)
    interface_components: list[str] = field(default_factory=list)
    api_dependencies: list[str] = field(default_factory=list)
    network_effects: list[str] = field(default_factory=list)
    moat_factors: list[str] = field(default_factory=list)
    revenue_streams: list[str] = field(default_factory=list)
    revenue_model: str = ""
    audience_channels: list[str] = field(default_factory=list)
    competitive_advantages: list[str] = field(default_factory=list)
    risks: list[dict] = field(default_factory=list)
    timeline_preference: str = ""  # "aggressive", "steady", "conservative"


@dataclass
class GamePlan:
    """Generated game plan with timelines."""
    week_1_2: list[str] = field(default_factory=list)
    days_15_30: list[str] = field(default_factory=list)
    month_2_3: list[str] = field(default_factory=list)
    month_3_6: list[str] = field(default_factory=list)
    month_6_12: list[str] = field(default_factory=list)
    category_verdict: str = ""
    pivot_recommendations: list[str] = field(default_factory=list)
    positioning_statement: str = ""
    risk_summary: list[dict] = field(default_factory=list)


@dataclass
class StrategySession:
    """Complete session state for save/resume."""
    id: str = ""
    created_at: str = ""
    updated_at: str = ""
    current_step: EngineStep = EngineStep.WELCOME
    step_index: int = 0
    idea: IdeaProfile = field(default_factory=IdeaProfile)
    game_plan: Optional[GamePlan] = None
    conversation_log: list[dict] = field(default_factory=list)
    completed: bool = False

    def to_json(self) -> str:
        data = asdict(self)
        data["current_step"] = self.current_step.value
        data["idea"]["primary_categories"] = [c.value for c in self.idea.primary_categories]
        data["idea"]["secondary_categories"] = [c.value for c in self.idea.secondary_categories]
        data["idea"]["danger_categories"] = [c.value for c in self.idea.danger_categories]
        return json.dumps(data, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "StrategySession":
        data = json.loads(json_str)
        data["current_step"] = EngineStep(data["current_step"])
        idea_data = data.get("idea", {})
        idea_data["primary_categories"] = [SaaSCategory(c) for c in idea_data.get("primary_categories", [])]
        idea_data["secondary_categories"] = [SaaSCategory(c) for c in idea_data.get("secondary_categories", [])]
        idea_data["danger_categories"] = [SaaSCategory(c) for c in idea_data.get("danger_categories", [])]
        data["idea"] = IdeaProfile(**idea_data)
        if data.get("game_plan"):
            data["game_plan"] = GamePlan(**data["game_plan"])
        return cls(**{k: v for k, v in data.items() if k != "conversation_log" or True})


# ─── Step Prompts & Logic ───────────────────────────────────────────────────

def get_step_prompt(step: EngineStep, session: StrategySession) -> dict:
    """Returns the engine's message and options for a given step."""

    if step == EngineStep.WELCOME:
        return {
            "message": """
# The SaaS Strategy Engine

Welcome. This engine is based on Alex Becker's SaaS Transition Thesis — a framework for understanding where software is heading and how to position yourself to profit from the shift.

**The core thesis:** Traditional SaaS (monolithic platforms with one-size-fits-all features) is dying. What replaces it is more profitable for those who position correctly.

**What we'll do together:**
1. Capture your software idea or current business
2. Classify it against the surviving SaaS categories
3. Analyze your moat (or lack of one)
4. Design your revenue architecture
5. Build your audience strategy
6. Assess competitive positioning
7. Generate a phased game plan (Week 1 → Month 12)

**This takes about 10-15 minutes.** You'll walk away with a concrete strategy document.

Ready to start?
""".strip(),
            "options": ["Let's go", "Tell me more about the thesis first"],
            "input_type": "choice",
        }

    elif step == EngineStep.IDEA_CAPTURE:
        return {
            "message": """
# Step 1: Capture Your Idea

Tell me about what you're building or want to build. Don't overthink it — brain dump. I need to understand:

- **What is it?** (software tool, platform, service, framework?)
- **Who is it for?** (developers, businesses, consumers, specific niche?)
- **What problem does it solve?**
- **What exists today that's similar?** (competitors, alternatives, workarounds)

Just describe it naturally. Stream of consciousness is fine. The messier the better — that's what this engine is built for.
""".strip(),
            "options": [],
            "input_type": "freeform",
        }

    elif step == EngineStep.CATEGORY_ASSESSMENT:
        cats = session.idea.primary_categories
        cat_details = []
        for c in cats:
            info = CATEGORY_INFO[c]
            cat_details.append(f"**{info['name']}**\n- {info['description']}\n- Survivability: {info['survivability']}\n- Risk: {info['risk_level']}")

        danger_details = []
        for c in session.idea.danger_categories:
            info = CATEGORY_INFO[c]
            danger_details.append(f"**{info['name']}**\n- {info['description']}\n- WARNING: {info['survivability']}")

        msg = f"""
# Step 2: Category Assessment

Based on your description, here's how your idea maps to the SaaS survival categories:

## Primary Categories (Where You Fit)
{"---".join(cat_details) if cat_details else "No strong category match yet — we need to shape this."}

"""
        if danger_details:
            msg += f"""## Danger Zones (Parts That Are at Risk)
{"---".join(danger_details)}

"""
        msg += """
## The Key Question

Looking at this classification — does this feel right? And more importantly:

**Which category do you WANT to be in?** Sometimes the pivot isn't about changing your product, it's about changing which layer you emphasize.

For example:
- A booking tool (dying) can pivot to a booking API/infrastructure (thriving)
- A generic CRM (dying) can pivot to a customizable CRM framework (thriving)
- Any tool can add network effects through community

What's your reaction? Do you want to:
1. Double down on your strongest category
2. Pivot toward a stronger category
3. Layer multiple categories (hybrid approach)
"""
        return {
            "message": msg.strip(),
            "options": [
                "Double down on strongest category",
                "I want to pivot toward a stronger category",
                "Hybrid approach — layer multiple categories",
                "Let me explain more about what I'm building",
            ],
            "input_type": "choice_with_comment",
        }

    elif step == EngineStep.MOAT_ANALYSIS:
        return {
            "message": f"""
# Step 3: Moat Analysis

Let's get real about your defensibility. In the new SaaS landscape, there are only a few moats that actually work:

## The Moat Checklist

Rate each (1-5 or just tell me which apply):

**Infrastructure Moat** — Is your backend so complex that replicating it is "hell on earth"?
- Data accuracy requirements? Scale challenges? Domain-specific complexity?

**Network Effect Moat** — Does your product get more valuable as more people use it?
- Community? Marketplace dynamics? Data network effects?

**Ecosystem Moat** — Are other products built on top of yours?
- Plugins? Integrations? Templates? API consumers?

**Switching Cost Moat** — How painful is it to leave?
- Data lock-in? Workflow dependencies? Team training?

**Speed/Expertise Moat** — Can you ship faster and better than anyone else in this niche?
- Domain knowledge? Proprietary playbooks? Tool advantage?

**Current moat factors identified:** {', '.join(session.idea.moat_factors) if session.idea.moat_factors else 'None yet — that is what we are building.'}

Which moats do you have or can you build? Be honest — weak moats get exposed fast in this transition.
""".strip(),
            "options": [],
            "input_type": "freeform",
        }

    elif step == EngineStep.REVENUE_MODEL:
        return {
            "message": f"""
# Step 4: Revenue Architecture

In the new SaaS landscape, the revenue model matters more than ever. Here are the models that work:

## Revenue Models Ranked by Resilience

1. **Usage-Based API Pricing** — Pay per call/event/compute
   - Most resilient. Scales with customer success.
   - Example: Stripe takes a % of every transaction.

2. **Infrastructure Subscription** — Monthly/annual for backend access
   - Strong if the infrastructure is genuinely hard to replicate.
   - Example: Supabase, Datadog.

3. **Affiliate/Referral Revenue** — Earn when your users connect to other services
   - Passive. Scales with template/framework distribution.
   - Example: Frameworks with embedded referral codes.

4. **Custom Build + Maintenance Retainer** — $5K build + $1K/month
   - Direct cash flow. Funds product development.
   - Example: Custom SaaS agency model.

5. **Freemium + Pro Tier** — Free core, paid advanced features
   - Works if free tier drives adoption and pro tier is genuinely valuable.
   - Example: Most developer tools.

6. **Marketplace Commission** — Cut of template/component sales
   - Requires critical mass of contributors.
   - Example: Template marketplaces.

**Your current API dependencies:** {', '.join(session.idea.api_dependencies) if session.idea.api_dependencies else 'Not identified yet'}

Which revenue model(s) fit your product? You can layer multiple — in fact, you should.
""".strip(),
            "options": [
                "Usage-based API pricing",
                "Infrastructure subscription",
                "Freemium + Pro tier",
                "Custom build + maintenance retainer",
            ],
            "input_type": "choice_with_comment",
        }

    elif step == EngineStep.AUDIENCE_STRATEGY:
        return {
            "message": """
# Step 5: Audience Strategy

Even the best product dies without an audience. In the current wave, there's a massive opportunity:

## The Audience Wave

```
Base44/Bolt/Lovable ads (millions in ad spend)
    → People discover "I can build software!"
    → They hit the ceiling fast
    → They search for real tools
    → They find YOU (if you're positioned right)
```

## Audience Channels — Which Apply to You?

**Content/SEO Plays:**
- "SaaS is dead" content (HOT topic right now)
- Build-in-public documentation
- Tutorial content from your own building process
- Comparison content (your tool vs. alternatives)

**Product-Led Growth:**
- Free tools that capture email lists
- Open-source components that drive awareness
- "Built with [Your Tool]" showcases
- Interactive tools (idea classifiers, strategy builders — like this one)

**Community:**
- Discord/forum for builders using your tools
- Template marketplace with community contributions
- Partnerships with complementary tool builders

**Direct Outreach:**
- Agency model clients = case studies = content
- Speaking/podcasting in the builder ecosystem
- Strategic partnerships with infrastructure providers

Which channels feel most natural for you? Where's your energy?
""".strip(),
            "options": [
                "Content/SEO — I can create content",
                "Product-led growth — let the tools speak",
                "Community building — I want to gather builders",
                "Agency/direct — I want to work with clients first",
            ],
            "input_type": "choice_with_comment",
        }

    elif step == EngineStep.COMPETITIVE_POSITION:
        return {
            "message": f"""
# Step 6: Competitive Positioning

Let's figure out where you sit in the landscape.

## The Layer Model

```
Layer 0: Infrastructure APIs (Stripe, Supabase, AWS)     → MOST VALUABLE
Layer 1: Meta-tools (tools that build tools)              → HIGH VALUE
Layer 2: Templates and frameworks                         → GROWING VALUE
Layer 3: End products (CRMs, booking tools, etc.)         → COMMODITY
```

**Based on what you've described, you're primarily at Layer {"?" if not session.idea.primary_categories else "0-1" if SaaSCategory.API_INFRASTRUCTURE in session.idea.primary_categories else "1-2" if SaaSCategory.CONNECTOR_PLATFORM in session.idea.primary_categories or SaaSCategory.OPEN_FRAMEWORK in session.idea.primary_categories else "2-3"}.**

## Key Questions

1. **Who are your direct competitors?** (Name them if you can)
2. **What do you do that they can't or won't?**
3. **If someone vibe-coded a competitor in a weekend, what would they be missing?**
4. **What gets BETTER about your product as more people use it?**

Tell me about your competitive landscape.
""".strip(),
            "options": [],
            "input_type": "freeform",
        }

    elif step == EngineStep.TIMELINE_PLANNING:
        return {
            "message": """
# Step 7: Timeline & Pace

The window for early positioning is NOW through mid-2027. How aggressively do you want to move?

## Pace Options

**Aggressive (Recommended if you can)**
- Ship something this week — even if imperfect
- Multiple releases per month
- Build in public from day one
- Take agency clients while building product
- Goal: market presence in 30 days

**Steady**
- Ship v1 in 2-4 weeks
- Monthly release cadence
- Build audience alongside product
- Agency work after v1 ships
- Goal: market presence in 60-90 days

**Conservative**
- Polish before shipping (4-8 weeks to v1)
- Quarterly major releases
- Audience building after product is solid
- Agency work after proven product
- Goal: market presence in 3-6 months

**The tradeoff:** Speed vs. polish. In a wave like this, speed usually wins. The first mover with a decent product beats the late mover with a perfect product.

What pace matches your situation?
""".strip(),
            "options": [
                "Aggressive — ship fast, iterate faster",
                "Steady — balance speed and quality",
                "Conservative — I want to get it right",
            ],
            "input_type": "choice_with_comment",
        }

    elif step == EngineStep.RISK_ASSESSMENT:
        return {
            "message": """
# Step 8: Risk Assessment

Let's be honest about what could go wrong. Every strategy has risks.

## Common Risks in This Transition

1. **Becker is wrong** — Traditional SaaS persists, transition doesn't happen
   - Mitigation: Your tools are useful regardless of the model

2. **You ship too slow** — Market moves faster than you
   - Mitigation: Ship imperfect, iterate based on feedback

3. **Big players build your thing** — Vercel, Supabase, etc. enter your space
   - Mitigation: Niche focus, community moat, first-mover advantage

4. **Template economy commoditizes** — Race to the bottom on templates
   - Mitigation: Win on ecosystem, not individual templates

5. **Agency model doesn't scale** — Gets stuck in service work
   - Mitigation: Productize the playbook, use agency for R&D funding

6. **Audience building is slow** — Content takes time to compound
   - Mitigation: Free tools as lead magnets, product-led growth

## Your Specific Risks

What worries YOU most about this strategy? What could derail you?
- Time constraints?
- Capital constraints?
- Technical limitations?
- Market timing?
- Something else?

Be real. We'll address each one in the game plan.
""".strip(),
            "options": [],
            "input_type": "freeform",
        }

    elif step == EngineStep.GAME_PLAN_GENERATION:
        return {
            "message": """
# Step 9: Generating Your Game Plan

Based on everything you've shared, I'm assembling your personalized strategy. This includes:

- Category verdict and positioning
- Phased timeline (Week 1 → Month 12)
- Revenue architecture
- Audience playbook
- Risk mitigations
- Pivot recommendations (if applicable)

Generating now...
""".strip(),
            "options": [],
            "input_type": "none",
        }

    elif step == EngineStep.COMPLETE:
        return {
            "message": "Game plan generated. See below.",
            "options": [],
            "input_type": "none",
        }

    return {"message": "Unknown step.", "options": [], "input_type": "none"}


# ─── Category Classification Logic ─────────────────────────────────────────

# Keywords/signals that map to categories
CATEGORY_SIGNALS = {
    SaaSCategory.API_INFRASTRUCTURE: [
        "api", "infrastructure", "backend", "sdk", "payment", "processing",
        "delivery", "hosting", "database", "auth", "authentication",
        "building block", "plug into", "usage-based", "per call", "per request",
        "developer tool", "dev tool", "platform api",
    ],
    SaaSCategory.COMPLEX_INFRASTRUCTURE: [
        "tracking", "attribution", "analytics", "monitoring", "data pipeline",
        "machine learning", "ai model", "accuracy", "edge cases", "compliance",
        "security", "complex backend", "data processing", "real-time data",
    ],
    SaaSCategory.NETWORK_EFFECT: [
        "community", "marketplace", "social", "network", "users attract users",
        "platform", "two-sided", "matching", "discovery", "distribution",
        "collaborative", "shared", "members",
    ],
    SaaSCategory.OPEN_FRAMEWORK: [
        "open source", "open-source", "framework", "library", "template",
        "foundation", "build on top", "ecosystem", "plugin", "extension",
        "widely used", "standard", "convention",
    ],
    SaaSCategory.CUSTOM_SAAS_SERVICE: [
        "agency", "custom", "client", "consulting", "build for",
        "maintain for", "manage for", "white label", "retainer",
        "per client", "done for you",
    ],
    SaaSCategory.TEMPLATE_MARKETPLACE: [
        "template", "theme", "starter", "boilerplate", "marketplace",
        "sell templates", "component library", "ui kit",
    ],
    SaaSCategory.CONNECTOR_PLATFORM: [
        "connect", "integrate", "orchestrate", "bind together",
        "automation", "workflow", "glue", "bridge", "sync",
        "multi-tool", "all-in-one orchestr",
    ],
    SaaSCategory.GENERIC_PLATFORM: [
        "all-in-one", "everything platform", "complete solution",
        "full suite", "does everything",
    ],
    SaaSCategory.SIMPLE_TOOL: [
        "simple tool", "basic", "one feature", "single purpose",
        "form builder", "landing page builder", "booking tool",
        "calculator", "converter",
    ],
    SaaSCategory.NO_MOAT_SAAS: [
        "no switching cost", "easy to replicate", "commodity",
        "just features", "anyone can build",
    ],
}

DYING_CATEGORIES = {
    SaaSCategory.GENERIC_PLATFORM,
    SaaSCategory.SIMPLE_TOOL,
    SaaSCategory.NO_MOAT_SAAS,
}


def classify_idea(description: str) -> tuple[list[SaaSCategory], list[SaaSCategory], list[SaaSCategory]]:
    """Classify an idea description into primary, secondary, and danger categories.

    Returns (primary, secondary, danger) category lists.
    """
    description_lower = description.lower()
    scores: dict[SaaSCategory, int] = {}

    for category, signals in CATEGORY_SIGNALS.items():
        score = 0
        for signal in signals:
            if signal in description_lower:
                score += 1
        if score > 0:
            scores[category] = score

    if not scores:
        return [], [], []

    sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    max_score = sorted_cats[0][1]

    primary = []
    secondary = []
    danger = []

    for cat, score in sorted_cats:
        if cat in DYING_CATEGORIES:
            danger.append(cat)
        elif score >= max_score * 0.7:
            primary.append(cat)
        else:
            secondary.append(cat)

    return primary, secondary, danger


def extract_api_dependencies(description: str) -> list[str]:
    """Extract likely API/infrastructure dependencies from description."""
    known_services = [
        "stripe", "supabase", "vercel", "aws", "twilio", "sendgrid",
        "clerk", "auth0", "firebase", "cloudflare", "planetscale",
        "redis", "postgresql", "postgres", "mongodb", "openai",
        "anthropic", "claude", "github", "docker", "kubernetes",
    ]
    desc_lower = description.lower()
    found = [s for s in known_services if s in desc_lower]
    return found


def identify_infrastructure_vs_interface(description: str) -> tuple[list[str], list[str]]:
    """Separate infrastructure components from interface components."""
    infra_signals = [
        "database", "api", "backend", "server", "auth", "payment",
        "processing", "storage", "queue", "cache", "search index",
        "data pipeline", "webhook", "cron", "scheduler",
    ]
    interface_signals = [
        "dashboard", "form", "ui", "frontend", "landing page",
        "booking page", "widget", "component", "layout", "theme",
        "template", "design", "responsive", "mobile view",
    ]
    desc_lower = description.lower()
    infra = [s for s in infra_signals if s in desc_lower]
    interface = [s for s in interface_signals if s in desc_lower]
    return infra, interface


# ─── Game Plan Generation ───────────────────────────────────────────────────

def generate_game_plan(session: StrategySession) -> GamePlan:
    """Generate a phased game plan based on session data."""
    idea = session.idea
    plan = GamePlan()
    pace = idea.timeline_preference or "aggressive"

    # Category verdict
    if idea.primary_categories:
        primary_names = [CATEGORY_INFO[c]["name"] for c in idea.primary_categories]
        plan.category_verdict = f"Primary positioning: {', '.join(primary_names)}."
        if idea.danger_categories:
            danger_names = [CATEGORY_INFO[c]["name"] for c in idea.danger_categories]
            plan.category_verdict += f" WARNING: Elements in dying categories ({', '.join(danger_names)}) — pivot these toward infrastructure/API."
    else:
        plan.category_verdict = "Category unclear — needs sharper positioning. Consider: what part of your product is INFRASTRUCTURE vs INTERFACE?"

    # Positioning statement
    if idea.target_audience and idea.problem_solved:
        plan.positioning_statement = f"For {idea.target_audience} who need {idea.problem_solved} — built on infrastructure they can't replicate, with an interface they can customize."
    else:
        plan.positioning_statement = "Define your audience and problem clearly. Strong positioning = [Audience] + [Problem] + [Why your infrastructure layer is the moat]."

    # Pivot recommendations
    for danger_cat in idea.danger_categories:
        if danger_cat == SaaSCategory.GENERIC_PLATFORM:
            plan.pivot_recommendations.append("PIVOT: Break your monolithic platform into mini-apps with open APIs. Let users build their own interface, keep the infrastructure.")
        elif danger_cat == SaaSCategory.SIMPLE_TOOL:
            plan.pivot_recommendations.append("PIVOT: Your simple tool will be commoditized. Either add complex infrastructure underneath, build network effects, or open-source it as a template with affiliate revenue.")
        elif danger_cat == SaaSCategory.NO_MOAT_SAAS:
            plan.pivot_recommendations.append("PIVOT: You need a moat. Options: (1) Build network effects, (2) Go deep on infrastructure complexity, (3) Open-source and become a framework, (4) Pivot to custom SaaS service model.")

    # Phased timeline
    if pace == "aggressive":
        plan.week_1_2 = [
            "Ship an MVP or free tool this week — even a strategy tool or template",
            "Set up email capture on everything you ship",
            "Write or record 2-3 pieces of content about the SaaS transition",
            "Identify 5 communities where your audience hangs out",
            "Start engaging in SaaS transition conversations online",
            "Set up affiliate accounts with infrastructure providers (Supabase, Vercel, Stripe)",
        ]
        plan.days_15_30 = [
            "Release 2-3 free tools or templates (email list magnets)",
            "Launch your core product in beta (even if rough)",
            "Create an interactive tool with virality potential",
            "Take on 1-2 agency clients if applicable",
            "Establish build-in-public content cadence",
            "Start building template library (first 3 templates)",
        ]
        plan.month_2_3 = [
            "Ship core product publicly with freemium model",
            "Release first wave of templates with embedded affiliate codes",
            "Scale content to weekly cadence minimum",
            "3-5 agency clients generating case studies",
            "Launch community (Discord or equivalent)",
            "First revenue milestone: $1K-5K/month from combined streams",
        ]
        plan.month_3_6 = [
            "Launch template marketplace (community contributions)",
            "Build connector/orchestration features",
            "Release API access to your engines",
            "Scale agency to 10+ clients",
            "Expand template library to 20+ templates",
            "Revenue target: $5K-15K/month",
        ]
        plan.month_6_12 = [
            "Ecosystem is self-sustaining — templates, community, affiliate revenue",
            "Your tools are becoming the default for new builders",
            "Agency model is a cash machine funding product development",
            "API revenue from other platforms integrating your tools",
            "Revenue target: $15K-50K/month from combined streams",
            "Evaluate: raise funding or stay bootstrapped?",
        ]
    elif pace == "steady":
        plan.week_1_2 = [
            "Finalize your MVP scope — what's the minimum viable product?",
            "Set up project infrastructure (repo, CI, hosting)",
            "Start content planning — outline 10 pieces",
            "Research competitor landscape thoroughly",
            "Set up email list and landing page",
        ]
        plan.days_15_30 = [
            "Ship MVP (beta) to early adopters",
            "Publish first 3-5 pieces of content",
            "Gather feedback from 10 beta users",
            "Iterate on core product based on feedback",
            "Identify first potential agency clients",
        ]
        plan.month_2_3 = [
            "Public launch with freemium model",
            "Weekly content cadence established",
            "First 2-3 agency clients",
            "First templates released",
            "Community seeded (invite-only initially)",
            "First revenue: $500-2K/month",
        ]
        plan.month_3_6 = [
            "Template library growing (10+ templates)",
            "Agency model validated with 5+ clients",
            "Content generating organic traffic",
            "Affiliate revenue starting to compound",
            "Revenue target: $3K-8K/month",
        ]
        plan.month_6_12 = [
            "Mature product with clear market position",
            "Self-sustaining content and community",
            "Template marketplace with community contributions",
            "Revenue target: $8K-25K/month",
            "Consider: API access, partnerships, expansion",
        ]
    else:  # conservative
        plan.week_1_2 = [
            "Deep market research and competitive analysis",
            "Define detailed product spec",
            "Set up development environment and architecture",
            "Begin building core product",
        ]
        plan.days_15_30 = [
            "Continue core product development",
            "Internal testing and QA",
            "Draft content strategy",
            "Identify beta test group",
        ]
        plan.month_2_3 = [
            "Private beta with select users",
            "Iterate based on beta feedback",
            "Begin content creation",
            "First agency conversations",
            "Revenue: pre-revenue, building toward launch",
        ]
        plan.month_3_6 = [
            "Public launch (polished v1)",
            "Content engine starts",
            "First agency clients",
            "First templates released",
            "Revenue target: $1K-5K/month",
        ]
        plan.month_6_12 = [
            "Growing product with established user base",
            "Template library building",
            "Agency model scaling",
            "Revenue target: $5K-15K/month",
        ]

    # Risk summary
    plan.risk_summary = [
        {"risk": "Market timing", "level": "Medium", "mitigation": "Ship fast. Being early with a decent product beats being late with a perfect one."},
        {"risk": "Commoditization", "level": "High", "mitigation": "Win on ecosystem, not individual products. Build network effects."},
        {"risk": "Competition from big players", "level": "Medium", "mitigation": "Niche focus + community moat + first-mover advantage."},
    ]
    for risk in idea.risks:
        plan.risk_summary.append(risk)

    return plan


# ─── Game Plan Formatting ───────────────────────────────────────────────────

def format_game_plan(session: StrategySession) -> str:
    """Format the game plan as a readable markdown document."""
    idea = session.idea
    plan = session.game_plan
    if not plan:
        return "No game plan generated yet."

    doc = f"""
# YOUR SAAS STRATEGY GAME PLAN

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Product:** {idea.name or idea.one_liner or 'Your Software Product'}
**Target Audience:** {idea.target_audience or 'To be defined'}
**Pace:** {idea.timeline_preference or 'Aggressive'} (recommended)

---

## CATEGORY VERDICT

{plan.category_verdict}

## POSITIONING

> {plan.positioning_statement}

"""

    if plan.pivot_recommendations:
        doc += "## PIVOT RECOMMENDATIONS\n\n"
        for rec in plan.pivot_recommendations:
            doc += f"- {rec}\n"
        doc += "\n"

    # Primary categories detail
    if idea.primary_categories:
        doc += "## YOUR CATEGORIES (DETAILED)\n\n"
        for cat in idea.primary_categories:
            info = CATEGORY_INFO[cat]
            doc += f"### {info['name']}\n"
            doc += f"- **What it means:** {info['description']}\n"
            doc += f"- **Survivability:** {info['survivability']}\n"
            doc += f"- **Revenue model:** {info['revenue_model']}\n"
            doc += f"- **Moat:** {info['moat']}\n"
            doc += f"- **Examples:** {', '.join(info['examples'])}\n\n"

    # Revenue architecture
    doc += "## REVENUE ARCHITECTURE\n\n"
    if idea.revenue_streams:
        for stream in idea.revenue_streams:
            doc += f"- {stream}\n"
    else:
        doc += "- Define your primary revenue stream\n"
        doc += "- Layer affiliate revenue on infrastructure connections\n"
        doc += "- Consider agency model for early cash flow\n"
    doc += "\n"

    # Moat factors
    doc += "## MOAT FACTORS\n\n"
    if idea.moat_factors:
        for moat in idea.moat_factors:
            doc += f"- {moat}\n"
    else:
        doc += "- Build infrastructure complexity (hard to replicate)\n"
        doc += "- Create network effects (community, marketplace)\n"
        doc += "- Establish ecosystem (templates, plugins, integrations)\n"
    doc += "\n"

    # Phased timeline
    doc += "---\n\n## PHASED TIMELINE\n\n"

    phases = [
        ("Week 1-2: Foundation Sprint", plan.week_1_2),
        ("Days 15-30: Acceleration", plan.days_15_30),
        ("Month 2-3: Product Shipping", plan.month_2_3),
        ("Month 3-6: Scale & Ecosystem", plan.month_3_6),
        ("Month 6-12: Infrastructure Lock-In", plan.month_6_12),
    ]
    for phase_name, items in phases:
        doc += f"### {phase_name}\n"
        for item in items:
            doc += f"- [ ] {item}\n"
        doc += "\n"

    # Risk summary
    doc += "---\n\n## RISK ASSESSMENT\n\n"
    doc += "| Risk | Level | Mitigation |\n|------|-------|------------|\n"
    for risk in plan.risk_summary:
        doc += f"| {risk.get('risk', 'Unknown')} | {risk.get('level', '?')} | {risk.get('mitigation', '')} |\n"
    doc += "\n"

    # Audience channels
    if idea.audience_channels:
        doc += "## AUDIENCE CHANNELS\n\n"
        for channel in idea.audience_channels:
            doc += f"- {channel}\n"
        doc += "\n"

    doc += """---

## NEXT STEPS

1. **This week:** Ship the first thing from Phase 1. Doesn't matter if it's rough.
2. **Today:** Set up email capture. Every visitor should have a way to stay connected.
3. **Right now:** Pick the ONE most important task from Week 1-2 and start it.

**Remember:** You're not building SaaS. You're building the factory that builds the factories. And the factories are about to be in very high demand.

---

*Generated by the SaaS Strategy Engine — based on Alex Becker's SaaS Transition Thesis*
"""
    return doc.strip()


# ─── Main Engine Class ──────────────────────────────────────────────────────

class StrategyEngine:
    """Interactive strategy engine that walks users through the SaaS transition framework."""

    def __init__(self):
        self.session = StrategySession(
            id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )

    def get_current_prompt(self) -> dict:
        """Get the prompt for the current step."""
        return get_step_prompt(self.session.current_step, self.session)

    def process_input(self, user_input: str) -> dict:
        """Process user input for the current step and advance.

        Returns the next step's prompt (or game plan if complete).
        """
        step = self.session.current_step

        # Log the interaction
        self.session.conversation_log.append({
            "step": step.value,
            "user_input": user_input,
            "timestamp": datetime.now().isoformat(),
        })

        # Process based on current step
        if step == EngineStep.WELCOME:
            if "more" in user_input.lower() or "thesis" in user_input.lower():
                return {
                    "message": self._get_thesis_summary(),
                    "options": ["Got it, let's start"],
                    "input_type": "choice",
                    "advance": False,
                }
            self._advance()
            return self.get_current_prompt()

        elif step == EngineStep.IDEA_CAPTURE:
            self._process_idea_capture(user_input)
            self._advance()
            return self.get_current_prompt()

        elif step == EngineStep.CATEGORY_ASSESSMENT:
            self._process_category_choice(user_input)
            self._advance()
            return self.get_current_prompt()

        elif step == EngineStep.MOAT_ANALYSIS:
            self._process_moat_input(user_input)
            self._advance()
            return self.get_current_prompt()

        elif step == EngineStep.REVENUE_MODEL:
            self._process_revenue_choice(user_input)
            self._advance()
            return self.get_current_prompt()

        elif step == EngineStep.AUDIENCE_STRATEGY:
            self._process_audience_choice(user_input)
            self._advance()
            return self.get_current_prompt()

        elif step == EngineStep.COMPETITIVE_POSITION:
            self._process_competitive_input(user_input)
            self._advance()
            return self.get_current_prompt()

        elif step == EngineStep.TIMELINE_PLANNING:
            self._process_timeline_choice(user_input)
            self._advance()
            # Generate game plan
            self.session.game_plan = generate_game_plan(self.session)
            return self.get_current_prompt()

        elif step == EngineStep.RISK_ASSESSMENT:
            self._process_risk_input(user_input)
            # Regenerate game plan with risks
            self.session.game_plan = generate_game_plan(self.session)
            self._advance()
            self._advance()  # Skip GAME_PLAN_GENERATION to COMPLETE
            self.session.completed = True
            return {
                "message": format_game_plan(self.session),
                "options": ["Save this game plan", "Start over", "Refine a section"],
                "input_type": "choice",
                "complete": True,
            }

        return self.get_current_prompt()

    def _advance(self):
        """Move to the next step."""
        idx = self.session.step_index + 1
        if idx < len(STEP_SEQUENCE):
            self.session.step_index = idx
            self.session.current_step = STEP_SEQUENCE[idx]
            self.session.updated_at = datetime.now().isoformat()

    def _process_idea_capture(self, description: str):
        """Process the idea description and classify it."""
        self.session.idea.raw_description = description

        # Extract first sentence as name/one-liner
        sentences = re.split(r'[.!?\n]', description)
        if sentences:
            self.session.idea.one_liner = sentences[0].strip()[:200]

        # Classify
        primary, secondary, danger = classify_idea(description)
        self.session.idea.primary_categories = primary
        self.session.idea.secondary_categories = secondary
        self.session.idea.danger_categories = danger

        # Extract API dependencies
        self.session.idea.api_dependencies = extract_api_dependencies(description)

        # Separate infra vs interface
        infra, interface = identify_infrastructure_vs_interface(description)
        self.session.idea.infrastructure_components = infra
        self.session.idea.interface_components = interface

    def _process_category_choice(self, choice: str):
        """Process category strategy choice."""
        choice_lower = choice.lower()
        if "pivot" in choice_lower:
            # Suggest moving toward infrastructure/API
            if SaaSCategory.API_INFRASTRUCTURE not in self.session.idea.primary_categories:
                self.session.idea.secondary_categories.append(SaaSCategory.API_INFRASTRUCTURE)
        elif "hybrid" in choice_lower:
            # Keep everything, emphasize layering
            pass
        # User might add more detail in comments
        if len(choice) > 100:
            # Probably includes detailed comments
            more_primary, more_secondary, more_danger = classify_idea(choice)
            for c in more_primary:
                if c not in self.session.idea.primary_categories:
                    self.session.idea.primary_categories.append(c)

    def _process_moat_input(self, moat_text: str):
        """Extract moat factors from user input."""
        moat_keywords = {
            "infrastructure": "Infrastructure complexity moat",
            "data": "Data/accuracy moat",
            "network": "Network effect moat",
            "community": "Community/network moat",
            "ecosystem": "Ecosystem/integration moat",
            "switching": "Switching cost moat",
            "speed": "Speed/expertise moat",
            "expertise": "Domain expertise moat",
            "template": "Template ecosystem moat",
            "open source": "Open-source community moat",
        }
        text_lower = moat_text.lower()
        for keyword, moat_name in moat_keywords.items():
            if keyword in text_lower:
                if moat_name not in self.session.idea.moat_factors:
                    self.session.idea.moat_factors.append(moat_name)

        # Store raw input for context
        if not self.session.idea.moat_factors:
            self.session.idea.moat_factors.append(f"User assessment: {moat_text[:200]}")

    def _process_revenue_choice(self, choice: str):
        """Process revenue model selection."""
        revenue_map = {
            "usage": "Usage-based API pricing",
            "api pricing": "Usage-based API pricing",
            "infrastructure sub": "Infrastructure subscription",
            "subscription": "Infrastructure subscription",
            "freemium": "Freemium + Pro tier",
            "pro tier": "Freemium + Pro tier",
            "agency": "Custom build + maintenance retainer ($5K build + $1K/month)",
            "retainer": "Custom build + maintenance retainer ($5K build + $1K/month)",
            "custom build": "Custom build + maintenance retainer ($5K build + $1K/month)",
            "affiliate": "Affiliate/referral revenue on infrastructure connections",
            "marketplace": "Marketplace commission on templates/components",
        }
        choice_lower = choice.lower()
        for keyword, stream in revenue_map.items():
            if keyword in choice_lower and stream not in self.session.idea.revenue_streams:
                self.session.idea.revenue_streams.append(stream)

        # Always suggest affiliate as a layer
        affiliate = "Affiliate/referral revenue on infrastructure connections"
        if affiliate not in self.session.idea.revenue_streams:
            self.session.idea.revenue_streams.append(affiliate)

        self.session.idea.revenue_model = ", ".join(self.session.idea.revenue_streams)

    def _process_audience_choice(self, choice: str):
        """Process audience strategy choice."""
        channel_map = {
            "content": ["SEO/blog content about SaaS transition", "Build-in-public documentation", "Tutorial content from building process"],
            "seo": ["SEO/blog content about SaaS transition", "Build-in-public documentation"],
            "product": ["Free tools as lead magnets", "Open-source components for awareness", "'Built with' showcases"],
            "community": ["Discord/forum for builders", "Template marketplace with community contributions", "Partnerships with complementary tools"],
            "agency": ["Agency clients as case studies", "Direct outreach to businesses", "Strategic partnerships"],
            "direct": ["Agency clients as case studies", "Direct outreach to businesses"],
        }
        choice_lower = choice.lower()
        for keyword, channels in channel_map.items():
            if keyword in choice_lower:
                for ch in channels:
                    if ch not in self.session.idea.audience_channels:
                        self.session.idea.audience_channels.append(ch)

    def _process_competitive_input(self, comp_text: str):
        """Process competitive landscape input."""
        if comp_text.strip():
            self.session.idea.competitive_advantages.append(comp_text[:500])

    def _process_timeline_choice(self, choice: str):
        """Process timeline/pace selection."""
        choice_lower = choice.lower()
        if "aggressive" in choice_lower or "fast" in choice_lower:
            self.session.idea.timeline_preference = "aggressive"
        elif "conservative" in choice_lower or "right" in choice_lower:
            self.session.idea.timeline_preference = "conservative"
        else:
            self.session.idea.timeline_preference = "steady"

    def _process_risk_input(self, risk_text: str):
        """Process risk concerns from user."""
        risk_keywords = {
            "time": {"risk": "Time constraints", "level": "High", "mitigation": "Ruthless prioritization. Ship the minimum viable version of everything. Perfect later."},
            "money": {"risk": "Capital constraints", "level": "Medium", "mitigation": "Start with free tools + agency revenue. Bootstrap before raising."},
            "capital": {"risk": "Capital constraints", "level": "Medium", "mitigation": "Start with free tools + agency revenue. Bootstrap before raising."},
            "technical": {"risk": "Technical limitations", "level": "Medium", "mitigation": "Use your own tools (AutoForge) to build faster. Leverage AI assistance."},
            "competition": {"risk": "Competition", "level": "Medium", "mitigation": "Speed + niche focus + community moat. Be first, be specific, be helpful."},
            "timing": {"risk": "Market timing", "level": "Medium", "mitigation": "The wave is NOW. Ship fast to catch it. Being early > being perfect."},
            "audience": {"risk": "Audience building is slow", "level": "Medium", "mitigation": "Free tools as lead magnets. Product-led growth compounds faster than content alone."},
            "burnout": {"risk": "Burnout / sustainability", "level": "Medium", "mitigation": "Set sustainable pace. Agency revenue provides stability while building."},
        }
        text_lower = risk_text.lower()
        for keyword, risk in risk_keywords.items():
            if keyword in text_lower:
                self.session.idea.risks.append(risk)

        if not self.session.idea.risks:
            self.session.idea.risks.append({
                "risk": f"User concern: {risk_text[:100]}",
                "level": "Medium",
                "mitigation": "Address this in the first sprint. Don't let it become a blocker.",
            })

    def _get_thesis_summary(self) -> str:
        return """
## The SaaS Transition Thesis (Quick Summary)

**Source:** Alex Becker — operator generating $100K+/day across multiple SaaS companies

**Core claim:** Traditional SaaS (monolithic platforms) is dying. The new model is:

1. **Software becomes free** — people download templates and customize with AI
2. **Infrastructure stays paid** — APIs, data processing, complex backends
3. **The money shifts** from selling interfaces to selling infrastructure

**What's dying:**
- Generic platforms where users only use 1-2 features
- Simple tools that can be vibe-coded in one shot
- SaaS with no network effects or infrastructure moat

**What's thriving:**
- API/infrastructure companies (Stripe, Supabase, Twilio)
- Complex infrastructure SaaS (Hyros, Datadog)
- Network effect platforms (School, marketplaces)
- Open-source frameworks everyone builds on
- Custom SaaS services ($5K build + $1K/month)

**Timeline:** This transition completes within 2 years. The window for early positioning is NOW.

Ready to assess your idea against this framework?
""".strip()

    def save_session(self, filepath: str):
        """Save session to JSON file."""
        with open(filepath, 'w') as f:
            f.write(self.session.to_json())

    @classmethod
    def load_session(cls, filepath: str) -> "StrategyEngine":
        """Load a session from JSON file."""
        engine = cls()
        with open(filepath, 'r') as f:
            engine.session = StrategySession.from_json(f.read())
        return engine


# ─── CLI Runner ─────────────────────────────────────────────────────────────

def run_cli():
    """Run the strategy engine as an interactive CLI."""
    engine = StrategyEngine()

    print("\n" + "=" * 60)
    print("  SaaS STRATEGY ENGINE")
    print("  Based on Alex Becker's SaaS Transition Thesis")
    print("=" * 60 + "\n")

    prompt = engine.get_current_prompt()

    while True:
        # Display the message
        print(prompt["message"])
        print()

        # Display options if any
        if prompt.get("options"):
            for i, opt in enumerate(prompt["options"], 1):
                print(f"  [{i}] {opt}")
            print()

        # Check if complete
        if prompt.get("complete"):
            print("\n--- STRATEGY COMPLETE ---\n")
            save = input("Save game plan to file? (y/n): ").strip().lower()
            if save == 'y':
                filename = f"game_plan_{engine.session.id}.md"
                with open(filename, 'w') as f:
                    f.write(format_game_plan(engine.session))
                print(f"Saved to {filename}")

                session_file = f"strategy_session_{engine.session.id}.json"
                engine.save_session(session_file)
                print(f"Session saved to {session_file}")
            break

        # Get input
        input_type = prompt.get("input_type", "freeform")
        if input_type == "none":
            # Auto-advance (e.g., game plan generation step)
            prompt = engine.process_input("")
            continue

        user_input = input("\n> ").strip()
        if not user_input:
            continue

        # Handle numbered choices
        if prompt.get("options") and user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(prompt["options"]):
                user_input = prompt["options"][idx]

        # Handle quit
        if user_input.lower() in ('quit', 'exit', 'q'):
            save = input("Save session before quitting? (y/n): ").strip().lower()
            if save == 'y':
                session_file = f"strategy_session_{engine.session.id}.json"
                engine.save_session(session_file)
                print(f"Session saved to {session_file}")
            break

        # Process and get next prompt
        prompt = engine.process_input(user_input)


if __name__ == "__main__":
    run_cli()
