# Example Captures

Realistic Stage 1 captures at different detail levels. Each shows raw user input and the resulting `stage_1` output.

---

## Example 1: Minimal Input (2-3 sentences)

**User says:**
> I want a recipe app where people can save recipes and search by ingredient.

**stage_1 output:**

```json
{
  "raw_input": "I want a recipe app where people can save recipes and search by ingredient.",
  "input_format": "typed",
  "captured_at": "2026-04-03T11:00:00Z",
  "word_count": 14,
  "char_count": 71,
  "explicit_corrections": []
}
```

**Confidence: 52/100** — Fails minimum viability (14 words < 20). Prompt user for more detail. If user declines, trigger escape hatch.

**After prompting, user adds:**
> It should have categories like breakfast, lunch, dinner. Users can rate recipes and leave comments. Maybe a meal planner for the week.

**Updated stage_1:**

```json
{
  "raw_input": "I want a recipe app where people can save recipes and search by ingredient.\n\nIt should have categories like breakfast, lunch, dinner. Users can rate recipes and leave comments. Maybe a meal planner for the week.",
  "input_format": "typed",
  "captured_at": "2026-04-03T11:01:30Z",
  "word_count": 41,
  "char_count": 213,
  "explicit_corrections": []
}
```

**Confidence: 74/100** — Flag (low specificity and completeness). Proceeds with warning.

---

## Example 2: Average Input (5-8 sentences)

**User says:**
> I'm thinking of a fitness tracking app for personal trainers. They can create workout plans for their clients, track progress over time, and see charts of improvement. Clients get a separate view where they log their workouts and see what's assigned. I want Google login for both trainers and clients. It should work on mobile since people use it at the gym. Something like Trainerize but less expensive and more customizable.

**stage_1 output:**

```json
{
  "raw_input": "I'm thinking of a fitness tracking app for personal trainers. They can create workout plans for their clients, track progress over time, and see charts of improvement. Clients get a separate view where they log their workouts and see what's assigned. I want Google login for both trainers and clients. It should work on mobile since people use it at the gym. Something like Trainerize but less expensive and more customizable.",
  "input_format": "typed",
  "captured_at": "2026-04-03T11:05:00Z",
  "word_count": 82,
  "char_count": 460,
  "explicit_corrections": []
}
```

**Confidence: 88/100** — Flag (handoff_readiness slightly low — trainer/client permissions not fully described). Proceeds with warning.

---

## Example 3: Verbose Input (40+ sentences)

**User says:**
> OK so I've been thinking about this for a while. I want to build a freelancer management platform. Think of it like a mix between Upwork and Notion. Freelancers sign up, create a profile with their skills, hourly rate, portfolio links. Companies post gigs — not full job listings, more like project briefs. So a company says "I need a landing page designed" and freelancers can bid on it. But here's the thing — I don't want it to be a race to the bottom on pricing like Fiverr. I want quality matching. So maybe there's a rating system based on completed work, and the platform suggests matches based on skills and past work quality. Companies can also create teams of freelancers they work with regularly, like a favorites list. Payments should be handled through the platform — escrow style. Company pays upfront, money is held, released when work is approved. Disputes go to mediation. I want Stripe for payments. Users sign up with email. Actually wait, also Google and LinkedIn since it's a professional platform. The dashboard for companies shows active projects, pending invoices, team performance. Freelancers see their pipeline, earnings chart, upcoming deadlines. There should be a messaging system between freelancers and companies, with file sharing. Not real-time chat necessarily — more like threaded conversations per project. Notifications for new messages, project updates, payment received. I want it to feel professional, not startup-y. Clean design, maybe a blue and white color scheme. Oh and I forgot — there should be a public profile page for freelancers that they can share as a portfolio link. And companies should have a public page too showing their posted gigs. SEO matters for these pages.

**stage_1 output:**

```json
{
  "raw_input": "OK so I've been thinking about this for a while. I want to build a freelancer management platform. Think of it like a mix between Upwork and Notion. Freelancers sign up, create a profile with their skills, hourly rate, portfolio links. Companies post gigs — not full job listings, more like project briefs. So a company says \"I need a landing page designed\" and freelancers can bid on it. But here's the thing — I don't want it to be a race to the bottom on pricing like Fiverr. I want quality matching. So maybe there's a rating system based on completed work, and the platform suggests matches based on skills and past work quality. Companies can also create teams of freelancers they work with regularly, like a favorites list. Payments should be handled through the platform — escrow style. Company pays upfront, money is held, released when work is approved. Disputes go to mediation. I want Stripe for payments. Users sign up with email. Actually wait, also Google and LinkedIn since it's a professional platform. The dashboard for companies shows active projects, pending invoices, team performance. Freelancers see their pipeline, earnings chart, upcoming deadlines. There should be a messaging system between freelancers and companies, with file sharing. Not real-time chat necessarily — more like threaded conversations per project. Notifications for new messages, project updates, payment received. I want it to feel professional, not startup-y. Clean design, maybe a blue and white color scheme. Oh and I forgot — there should be a public profile page for freelancers that they can share as a portfolio link. And companies should have a public page too showing their posted gigs. SEO matters for these pages.",
  "input_format": "typed",
  "captured_at": "2026-04-03T11:10:00Z",
  "word_count": 271,
  "char_count": 1534,
  "explicit_corrections": [
    {
      "original": "email login only",
      "correction": "email AND Google AND LinkedIn login",
      "context": "User initially said email, then added Google and LinkedIn since it's a professional platform"
    }
  ]
}
```

**Confidence: 96/100** — Pass. Rich detail, multiple features, target users, comparisons, technical preferences, and contextual detail.

---

## Example 4: Voice Transcript (with filler words and self-corrections)

**User says (transcribed from voice):**
> um ok so like I want to make this app right where uh people can like track their habits you know like drinking water exercising reading whatever um and it shows you like streaks so if you do it every day your streak goes up and if you miss a day it resets well actually maybe not resets completely like maybe it just you know shows a gap and you can still see your overall progress um I think it should be really simple like not a lot of buttons just open it check off what you did today see your streaks maybe some stats like how many times you exercised this month um I don't know about login maybe just use the phone no wait it should sync between devices so yeah login with Apple or Google I guess um and like maybe there's a social thing where you can share your streaks with friends but that's not the main thing the main thing is just tracking your own habits simply

**stage_1 output:**

```json
{
  "raw_input": "um ok so like I want to make this app right where uh people can like track their habits you know like drinking water exercising reading whatever um and it shows you like streaks so if you do it every day your streak goes up and if you miss a day it resets well actually maybe not resets completely like maybe it just you know shows a gap and you can still see your overall progress um I think it should be really simple like not a lot of buttons just open it check off what you did today see your streaks maybe some stats like how many times you exercised this month um I don't know about login maybe just use the phone no wait it should sync between devices so yeah login with Apple or Google I guess um and like maybe there's a social thing where you can share your streaks with friends but that's not the main thing the main thing is just tracking your own habits simply",
  "input_format": "voice_transcript",
  "captured_at": "2026-04-03T11:15:00Z",
  "word_count": 170,
  "char_count": 837,
  "explicit_corrections": [
    {
      "original": "streak resets when you miss a day",
      "correction": "streak shows a gap but overall progress still visible",
      "context": "User reconsidered full reset as too punishing"
    },
    {
      "original": "no login, just use the phone",
      "correction": "login with Apple or Google for device sync",
      "context": "User realized syncing between devices requires login"
    }
  ]
}
```

**Confidence: 90/100** — Pass. Filler words preserved, corrections detected, app concept clear despite informal language.
