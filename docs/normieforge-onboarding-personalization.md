# NormieForge — Instant Personalization Strategy

## The Problem With Every Other App

Every app onboarding is the same soulless flow:
1. Create account
2. Pick categories you're interested in
3. Set preferences manually
4. Get generic content for 2 weeks until it "learns" you
5. Delete app on day 3 because it feels like every other app

**Nobody waits 2 weeks.** If it doesn't feel personal in 60 seconds, it's gone.

## The Cheat Code: Social Signal Scraping

When the user signs up with Google, Twitter/X, Instagram, or Facebook,
we get their public profile instantly. From that we can build a
"first impression" personality sketch in seconds.

### What We Scrape (Public Only, With Permission)

**From Twitter/X:**
- Bio (job, interests, identity in 160 chars)
- Recent posts (tone, topics, complaints, wins)
- Who they follow (fitness accounts? finance? parenting? hustle?)
- Posting patterns (morning person? night owl? weekday vs weekend?)

**From Instagram:**
- Bio (similar to Twitter — identity snapshot)
- Public post captions (lifestyle signals, interests, tone)
- Hashtags used (fitness, cooking, travel, kids, business)

**From Google:**
- Name, profile photo
- Connected services give hints (Google Fit = health conscious, etc.)

**From Facebook:**
- Life stage signals (relationship status, kids, job, location)
- Groups (parenting groups, finance groups, hobby groups)
- Public posts (complaints, celebrations, daily life)

### What We Build From It: The Instant Profile

```json
{
  "name": "Sarah",
  "likely_age_range": "30-40",
  "life_stage": "parent_young_kids",
  "personality_tone": "warm_casual_overwhelmed",
  "primary_stressors": ["family_logistics", "money_management", "time"],
  "interests": ["fitness", "cooking_sometimes", "organization"],
  "communication_style": "friendly_direct_emoji_user",
  "likely_first_need": "family_schedule_chaos",
  "energy": "busy_but_trying",
  "humor_level": "moderate_self_deprecating"
}
```

### How This Changes The First 60 Seconds

**Without social scraping (generic):**
> "Welcome to NormieForge! What would you like help with?"
> [Budget] [Meals] [Schedule] [Health] [Other]

Feels like: every other app.

**With social scraping (personalized):**
> "Hey Sarah 👋 Looks like you've got a lot on your plate —
> three kids, a full calendar, and not enough hours.
> Most people in your situation start with getting the
> family schedule under control. Want me to start there?"
>
> [Yes, do that] [Actually, it's more about money] [Something else]

Feels like: this thing already gets me.

### Tone Mapping

The AI adapts its VOICE based on the personality sketch:

**Young professional, hustle energy:**
> "Yo, let's get your money right. I found some leaks
> in your subscriptions — $47/mo you're not using.
> Want me to sort it?"

**Overwhelmed parent, warm tone:**
> "I know mornings are chaos. Here's tomorrow sorted:
> Jake needs his cleats, Emma has a dentist at 3,
> and I've got dinner planned — you just need chicken."

**Older, straightforward, no-nonsense:**
> "Good morning. Your accounts look fine — $2,340 checking,
> $847 remaining this month. Electric bill Friday: covered.
> Nothing needs your attention today."

**Creative/artsy type:**
> "Morning ✨ Budget's looking healthy, you've got $847 of
> breathing room this month. Tonight's recipe is that Thai
> basil chicken you saved — 25 min, and you've got everything."

SAME INFORMATION. Completely different delivery.
The user never sets a "tone preference." It just speaks their language.

### The Depth Layers

**Layer 1: Social scrape (instant — before first interaction)**
- Name, life stage, interests, tone, likely first need
- Enough to nail the first message

**Layer 2: First conversation (minute 1-5)**
- What they type in the hero ("I'm always broke by the 20th")
- Which option they pick when presented with choices
- How they respond to the AI's tone (short answers = get to the point)

**Layer 3: Account connections (minute 5-15)**
- Bank data reveals actual spending patterns
- Calendar reveals actual schedule chaos
- Health app reveals fitness patterns
- Real data replaces social signal guesses

**Layer 4: Behavioral learning (week 1+)**
- When they open the app (morning person? evening?)
- What they tap on first (money? schedule? meals?)
- What they ignore (stop showing things they skip)
- When they screenshot (that's what they're proud of — do more of that)

**Layer 5: Deep personalization (month 1+)**
- Spending patterns by day of week and emotional state
- Which reminders they act on vs dismiss
- Communication style refinement
- Proactive suggestions based on pattern recognition

### Privacy Strategy

This only works if users TRUST it. Key principles:

1. **Ask permission explicitly.** "I can learn about you faster if you
   connect your Twitter — want me to? Or we can start fresh."
   Both options work. Social scrape is a speed boost, not a requirement.

2. **Show what you learned.** After scraping, show the user:
   "Here's what I picked up about you — anything wrong?"
   This builds trust AND lets them correct mistakes.

3. **All local by default.** Brain file lives on THEIR device/account.
   We don't sell data. We don't share it. The AI works for THEM.

4. **Easy wipe.** One button: "Forget everything about me."
   Full brain file deleted. Start fresh.

### Implementation: MVP Version

For MVP, we don't need full social scraping. Just:

1. **Google sign-in** → Get name, profile photo
2. **One smart question** → "In one sentence, what does your typical day look like?"
3. **AI builds first profile** from that single sentence

Even "I'm a mom with two kids and a full-time job" gives us:
- Life stage: parent
- Energy: busy
- Tone: probably wants efficiency, not fluff
- First need: probably time/schedule management
- Communication: probably appreciates brevity

That single sentence + their name = enough to make the first
interaction feel personal. Layer on social scraping in v2.

### The Viral Feedback Loop

1. User gets a perfectly-toned morning briefing
2. It feels so personal they screenshot it
3. They share it: "look what my AI said to me this morning"
4. Friend sees it, but the TONE is what hooks them
   — "wait, it talks to you like THAT?"
5. Friend signs up, connects their Twitter
6. Gets their OWN perfectly-toned first message
7. Screenshots it. Shares it. Repeat.

The personalization IS the virality. Generic briefings don't get
screenshotted. But a briefing that sounds like your best friend
who also happens to be an accountant? That gets shared.

### Competitive Moat

After 3 months, the AI knows:
- Your financial personality (spender? saver? anxious? carefree?)
- Your communication style (emoji? formal? sweary? brief?)
- Your life rhythms (when you're stressed, happy, lazy, motivated)
- Your blind spots (what you always forget, what you overspend on)
- Your values (family first? career first? health first?)

No other product has this. Not ChatGPT (forgets you). Not Mint
(just numbers). Not Alexa (just commands). Not your actual friends
(they don't have your bank data).

This is the moat. It's not the features. It's the RELATIONSHIP.
And relationships don't get cancelled for $9/mo.
