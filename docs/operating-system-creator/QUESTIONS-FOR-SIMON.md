# Questions for Simon Scrapes — Missing Pieces from the Cold Email System

> **Context:** We reverse-engineered all 21 MD files from the free Skool content + the Lead Gen Mastery course. The system is legit and production-tested. But there are gaps — things that aren't documented anywhere in the files. These questions target exactly what's missing.

---

## Critical Gaps (System Won't Work Without These)

### 1. Email Warmup Process
The system mentions buying domains and setting up mailboxes but never documents the warmup process.

**Questions to ask:**
- "What warmup service do you use? Lemwarm, Warmup Inbox, or SmartLead's built-in?"
- "What's your ramp schedule? How many emails/day do you start at, and how fast do you increase?"
- "How many days do you warm up before starting cold sends?"
- "Do you warm up and cold send simultaneously, or stop warmup once you start sending?"

### 2. Bounce Handling & Suppression
The system sends emails but never documents what happens when they bounce.

**Questions to ask:**
- "How do you handle bounces? Manual checking or automated?"
- "Do you maintain a suppression list? Where — in SmartLead or separately?"
- "What bounce rate triggers you to pause a mailbox?"
- "How do you differentiate hard bounces from soft bounces in your system?"

### 3. Domain Health Monitoring
The system uses multiple domains but never documents how you monitor their reputation.

**Questions to ask:**
- "Do you use Google Postmaster Tools to monitor domain reputation?"
- "What metrics trigger you to pause or retire a domain?"
- "How often do you check domain health — daily? Weekly?"
- "Have you automated any of the domain health monitoring, or is it all manual?"

### 4. Reply Classification Beyond Basic
The 3-step outreach doc mentions webhooks for replies, but the classification is basic.

**Questions to ask:**
- "When a reply comes in, how granular is your classification? Just interested/not interested, or more?"
- "Do you auto-route different reply types to different workflows?"
- "How do you handle 'interested but not now' — do they go into a nurture sequence?"

### 5. Compliance / CAN-SPAM
Mentioned once in passing but never operationalized.

**Questions to ask:**
- "How do you handle the physical address requirement for CAN-SPAM?"
- "Do you have an unsubscribe mechanism in your cold emails, or do you rely on the 'first contact' exemption?"
- "Have you had any compliance issues? What happened and how did you handle it?"

---

## Important Gaps (System Works But Fragile Without These)

### 6. The Web Research Problem
The n8n lead research workflow uses Google CSE correctly. But SiteSprint and the pitch generator tell Claude to "research" companies — which means Claude will hallucinate.

**Questions to ask:**
- "In SiteSprint and the pitch generator, how does Claude get real company data? The MD files say 'research the prospect' but Claude can't browse the web."
- "Are you using Google CSE or Perplexity API for all company research, or does Claude sometimes just make it up?"
- "Have you had issues with Claude fabricating company details in the personalized emails?"

### 7. Multi-Client Data Isolation
The multi-client pipeline mentions per-client folders but doesn't fully document how to prevent cross-contamination.

**Questions to ask:**
- "How do you keep client data completely separate in Supabase? Separate tables? Row-level security? Separate projects?"
- "Has client data ever leaked between campaigns?"

### 8. SmartLead Webhook Setup
The 3-step outreach doc references webhooks but doesn't show the full setup.

**Questions to ask:**
- "Can you show the full SmartLead webhook configuration? What URL does it point to?"
- "Are you using n8n to receive webhooks, or a custom endpoint?"
- "What webhook events do you listen for beyond replies?"

---

## Nice-to-Have (Would Make System Better)

### 9. Actual Campaign Performance Data
**Question:** "What reply rates are you actually getting across clients? The 8-10% claim — is that on warm leads or truly cold?"

### 10. Cost Breakdown
**Question:** "What's the total monthly cost to run this for one client? Domains + Google Workspace + SmartLead + APIs + VPS?"

### 11. The Dashboard
**Question:** "The Agentic OS Dashboard you mentioned — does it replace the Telegram notification system, or sit on top of it? What does it actually show?"

### 12. Scaling Playbook
**Question:** "When you onboard a new client, what's the actual timeline? Day 1 you buy domains, day 14 warmup is done, day 15 first send — is that right? What's the full timeline?"

---

## Files We Had vs. Files That Might Be New in Lead Gen Mastery

### We Already Have (from free tier):
- All 21 MD files covering the 15 components
- The PDF (53 pages, formatted version)
- The TXT (full curriculum text)

### What Lead Gen Mastery Might Add (based on the course outline):
| Course Step | What We Already Have | What Might Be New |
|------------|---------------------|-------------------|
| Step 1: Cold Email Infrastructure | `1-stack-replacement.md` | DNS setup walkthrough? |
| Step 2: Picking Your Niche | `4-MOD-client-app-delivery.md` (partial) | ICP definition framework? |
| Step 3: Front-End Cold... | Maybe `3-MOD-auto-site-generator.md`? | Landing page templates? |
| Step 4: Build Your Lead List | `2-MOD-daily-lead-engine.md` | Apollo search strategies? |
| Step 5: Scraping Contacts | `2-MOD-google-maps-scraping.md` | New scraping methods? |
| Step 6: Verify Your List | Multi-client pipeline (MillionVerifier) | Verification thresholds? |
| Step 7: Centralizing System | Maybe Supabase CRM setup | Full CRM schema? |
| Step 8: Launch Campaign | `2-MOD-3-step-outreach-sequence.md` | Campaign launch checklist? |
| Step 9: Pitfalls | Scattered across files | **Probably new — operational lessons** |
| Step 10: Rule of Replies | Basic in outreach doc | **Probably new — reply handling** |
| Step 11: Main Summary | PDF covers this | Condensed version? |
| Close Your Deals section | Not in any MD file | **Definitely new — sales process** |
| Bonus: Sales Call + DM Scripts | Not in any MD file | **Definitely new** |

**The "Close Your Deals" and "Bonus" sections are the most likely to contain genuinely new material** — the free tier was all about building the system, not about actually closing clients.

---

## How to Ask Without Being Annoying

Since there's only ~20 people in the group, you can be direct:

> "Hey Simon, went through all the MD files and built out most of the system. Incredible work. I noticed a few gaps that I'm stuck on — mainly around warmup process, bounce handling, and domain health monitoring. Are those covered somewhere I missed, or are they coming in a future update? Also curious about the web research issue — how does Claude get real company data for SiteSprint without hallucinating?"

That one message covers the 3 biggest gaps without being overwhelming.
