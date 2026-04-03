# Question Templates for Gap Analysis

> Reusable patterns for generating adaptive gap questions.
> Fill in {placeholders} with app-specific context from raw_input and platform_profile.

## Pattern 1: REQUIRED Gap (Archetype expects it, user didn't mention it)

**Template:**
> "{Archetype} apps typically need {category_name}. {Specific_need_description}. How will yours handle this? ({option_1}, {option_2}, {option_3}, or something else?)"

**Examples:**
- "Marketplace apps need payment processing. How will buyers pay sellers? (Stripe, PayPal, direct bank transfer, or something else?)"
- "SaaS products need subscription billing. Will you offer plan tiers? (free/pro/team, single paid plan, usage-based, or something else?)"
- "Social platforms need content moderation. How will you handle inappropriate posts? (automated filters, user reports + manual review, AI moderation, or something else?)"

## Pattern 2: OPTIONAL Inquiry (Archetype says optional, check if needed)

**Template:**
> "Does your app need {category_name}? For example, {example_relevant_to_their_app}."

**Examples:**
- "Does your app need search? For example, letting users search across all their tasks by keyword or filter by status?"
- "Does your app need integrations? For example, syncing tasks with Google Calendar or importing from Trello?"
- "Does your app need a notification system? For example, email alerts when a due date is approaching?"

## Pattern 3: Sub-Type Specifics (Category identified but details missing)

**Template:**
> "You mentioned {what_user_said}. {Specific_sub_question}? ({option_1}, {option_2}, or {option_3}?)"

**Examples:**
- "You mentioned users can upload photos. What file types and size limits? (JPEG/PNG only up to 5MB, any image type up to 20MB, or also video files?)"
- "You mentioned email login. Will you also support social login? (Google only, Google + GitHub, Google + Apple, or email-only?)"
- "You mentioned a dashboard with charts. What specific metrics? (task completion rates, team productivity, time tracking, or something else?)"

## Pattern 4: Stack-Aware Question (Use platform_profile for context)

**Template:**
> "Since you're using {tech_stack_component}, {stack_specific_question}? ({stack_option_1}, {stack_option_2}?)"

**Stack-specific examples by platform:**

### Supabase
- "Since you're using Supabase, will you use Row Level Security to isolate user data, or handle authorization in your application code?"
- "Since you're using Supabase, will you use Supabase Auth for login, or a separate auth provider?"
- "Since you're using Supabase, will you use Edge Functions for server-side logic, or a separate API server?"

### Firebase
- "Since you're using Firebase, will you use Firestore security rules for authorization, or Cloud Functions middleware?"
- "Since you're using Firebase, will file uploads go to Cloud Storage with Firebase SDK, or a separate storage service?"
- "Since you're using Firebase, will you use Firebase Hosting, or deploy elsewhere?"

### Next.js / Vercel
- "Since you're using Next.js, will data fetching happen server-side (RSC), client-side (SWR/React Query), or a mix?"
- "Since you're deploying to Vercel, will you use Vercel's built-in analytics and edge functions?"

### Flutter / Mobile
- "Since you're building a mobile app, which platforms? (iOS only, Android only, or both?)"
- "Since you're using Flutter, will you use Firebase for the backend, Supabase, or a custom API?"

### Generic (no specific stack)
- "Where do you plan to host this? (Vercel, AWS, self-hosted, or undecided?)"
- "Do you have a preference for the database? (PostgreSQL, MySQL, MongoDB, or whatever fits best?)"

## Pattern 5: Contradiction Clarifier

**Template:**
> "You mentioned '{statement_1}' but also '{statement_2}'. Which takes priority? ({interpretation_1}, {interpretation_2}, or both in different contexts?)"

**Examples:**
- "You mentioned 'it should be simple' but also listed 12 features. Should we prioritize a minimal MVP first, or include all features from the start?"
- "You mentioned 'free for everyone' but also 'team workspaces with billing'. Will there be a free tier alongside a paid team plan, or is the entire app free?"

## Pattern 6: Developer's Choice Confirmation

**Template:**
> "For {category_name}, the standard approach for {archetype} apps is {default_approach}. Works for you, or do you have something different in mind?"

**Examples:**
- "For data storage, the standard approach for CRUD apps is a relational database (PostgreSQL). Works for you, or do you need something different?"
- "For session management, the standard approach is JWT with refresh tokens. Works for you?"

## Grouping Rules

When presenting questions, group by topic area:

1. **Core functionality gaps** — REQUIRED categories missing (highest priority)
2. **Feature questions** — OPTIONAL categories to confirm/deny
3. **Implementation specifics** — Sub-type details for identified categories
4. **Stack-specific** — Platform-tailored questions

Within each group, order from most impactful to least. Lead with the question whose answer affects the most downstream decisions (e.g., monetization model before payment processor details).

## Anti-Patterns (NEVER do these)

- "Tell me more about your app." (too vague)
- "What about authentication?" (too broad — offer specific options)
- "Have you thought about scalability?" (generic, not actionable)
- "What's your budget?" (not a mechanism question)
- "Can you describe the user flow?" (Stage 3's job, not Stage 2)
- Asking about something the user already clearly described in raw_input.
- Asking the same category twice in different questions.
- Asking more than 15 questions regardless of input length.
