# NormieForge — Metaprogram Personalization Engine

## Core Concept

Metaprograms are unconscious cognitive patterns that determine how people
process information, make decisions, and communicate. Everyone has them.
Nobody knows what they're called. But everyone FEELS when something
matches their pattern — it just "clicks."

NormieForge detects 3 metaprograms from social scraping or 3 quick taps.
That gives us 8 distinct communication profiles. The AI speaks the user's
cognitive language from message one.

## The 3 Core Metaprograms We Detect

### 1. Motivation Direction: Toward vs Away From

**What it is:** Are you motivated by moving TOWARD goals or AWAY FROM pain?

**Detection from language:**

| Away From signals | Toward signals |
|---|---|
| "stop wasting money" | "build my savings" |
| "tired of being disorganized" | "get my life together" |
| "can't keep doing this" | "ready to level up" |
| "avoid late fees" | "stay ahead of bills" |
| "I need to quit..." | "I want to start..." |
| "sick of..." | "excited about..." |
| "prevent / protect / avoid" | "achieve / create / build" |

**How we use it:**

Away From user morning briefing:
> "No fires today. Electric bill is covered. Nothing overdue.
> You dodged a $35 late fee — I paid it yesterday."

Toward user morning briefing:
> "Good morning! You're $200 ahead of your savings target.
> 8-day streak. Keep it going."

### 2. Frame of Reference: Internal vs External

**What it is:** Do you trust your own judgment or look to others for validation?

**Detection from language:**

| External signals | Internal signals |
|---|---|
| "what do you guys think?" | "I've decided to..." |
| "any recommendations?" | "I figured it out" |
| shares polls and surveys | shares opinions and takes |
| "is this normal?" | "this is what works for me" |
| "everyone says..." | "I believe..." |
| asks for reviews before buying | buys based on gut feeling |

**How we use it:**

External user:
> "87% of people with your spending pattern start with cutting
> subscriptions. The average savings is $89/mo. Want me to scan yours?"

Internal user:
> "Here's your spending breakdown. Three categories stand out.
> Take a look and tell me where you want to start."

### 3. Work Style: Options vs Procedures

**What it is:** Do you want choices and flexibility, or step-by-step instructions?

**Detection from language:**

| Procedures signals | Options signals |
|---|---|
| "just tell me what to do" | "what are my options?" |
| follows recipes exactly | improvises in the kitchen |
| likes lists and steps | likes browsing and exploring |
| "what's the right way?" | "what's the best way?" |
| completes one thing at a time | juggles multiple things |
| uses words like "correct, proper" | uses words like "flexible, depends" |

**How we use it:**

Procedures user:
> "Here's your morning plan:
> 1. ✅ Bills — all covered this week
> 2. 🍽️ Dinner tonight — Thai basil chicken (recipe below)
> 3. 📋 Tomorrow — Jake needs cleats for practice
> I'll handle each one in order."

Options user:
> "A few things on your radar today:
> • Dinner — I've got 3 ideas (Thai chicken, pasta, or leftovers)
> • Jake needs cleats tomorrow — Amazon, Target, or that store on Main?
> • Budget's flexible this week — splurge or save? Your call."

## The 8 Communication Profiles

| # | Toward/Away | Internal/External | Options/Procedures | Voice |
|---|---|---|---|---|
| 1 | Toward | Internal | Options | Empowering, choices, "your call" |
| 2 | Toward | Internal | Procedures | Structured wins, "here's the plan" |
| 3 | Toward | External | Options | Social proof + choices |
| 4 | Toward | External | Procedures | "Here's what winners do, step by step" |
| 5 | Away From | Internal | Options | Risk data + "you decide" |
| 6 | Away From | Internal | Procedures | "Here's how to stay safe, step by step" |
| 7 | Away From | External | Options | "Most people avoid this by..." + choices |
| 8 | Away From | External | Procedures | "Experts say do these 3 things to avoid..." |

## Detection Priority

### Best: Social scrape (0 questions needed)
Scan last 20 tweets / captions / posts. Usually get all 3 metaprograms
from language patterns alone. User never knows it happened.

NLP pattern matching on their text:
- Toward/Away: look for motivation language (toward/away word clusters)
- Internal/External: look for decision language (self-trust vs social-proof)
- Options/Procedures: look for structure preference (lists vs open-ended)

### Good: 3-tap questionnaire (feels like a fun quiz)
If no social data available, ask 3 natural questions:

**Q1 (Toward/Away):** "What would make tomorrow better?"
- "Get ahead on my goals" → Toward
- "Stop feeling overwhelmed" → Away From

**Q2 (Internal/External):** "When you need to make a decision, you usually..."
- "Research what others recommend" → External
- "Go with my gut" → Internal

**Q3 (Options/Procedures):** "When you're learning something new..."
- "Give me the steps" → Procedures
- "Let me explore" → Options

### Fallback: First message analysis
If no scrape AND they skip the quiz, analyze their hero input:
- "I want to stop wasting money" → Away From + (need more data)
- "I'm always broke by the 20th" → Away From + External (comparing to norm)

Even 1 metaprogram detected is better than 0. Default the others to
the statistical middle and refine over the first few interactions.

## Refinement Over Time

The initial detection is the STARTING POINT. Every interaction refines:

- They ignore the social proof line → probably more Internal than we thought
- They always pick "just do it" over choices → shift toward Procedures
- They respond more to "you're saving $X" than "you avoided $X" → shift Toward

The brain file tracks these shifts. By week 2, the profile is dialed.

## Why This Is Unbeatable

1. **Nobody else is doing this.** ChatGPT talks to everyone the same way.
   Every app has one voice. NormieForge has 8 voices and picks the right one.

2. **Users can't articulate why it works.** They just say "it gets me."
   They don't know about metaprograms. They just feel understood.
   That feeling = retention. That feeling = word of mouth.

3. **It compounds.** More interactions = more accurate profile = better
   communication = more engagement = more data = even better profile.
   The flywheel never stops.

4. **It's the moat.** A competitor can copy features. They can't copy
   3 months of learned communication calibration for each user.

## Implementation Notes

### MVP (v0.1)
- Detect Toward/Away from hero input text (keyword matching)
- 3-tap quiz as backup
- 2 voice templates (Toward + Away From) — just this one axis is enough to feel personal

### v0.2
- Add social scrape (Twitter API, public Instagram)
- All 3 metaprograms detected
- 8 voice templates

### v0.3
- AI-generated voice blending (not just 8 templates, but a spectrum)
- Real-time refinement from interaction patterns
- Metaprogram shift detection ("you've become more proactive this month!")

### v1.0
- Full metaprogram suite (could add 2-3 more: big picture/detail, proactive/reactive, sameness/difference)
- Voice becomes truly unique per user — no templates, pure AI calibration
- The AI literally speaks differently to every single user
