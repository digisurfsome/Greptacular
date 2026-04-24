# MP3 Generator — System Context Preamble

**Purpose:** Paste this block at the top of the MP3 Generator intake before feeding to the PRD-making pipeline. This is the agent-OS context the pipeline currently can't derive on its own. Once the full build_mode system is built (Phase 2+), this gets replaced by auto-filled variables. For now: manual context injection.

---

## System Context (for Stage 00-10 reasoning)

### Why this exists

This tool exists as part of a lead-generation system for selling AI-powered phone answering bots to small-business owners. The operator (the owner of this Greptacular project) is launching a B2B sales motion: he builds realistic voice-AI demos that answer phones for plumbers, HVAC companies, garage door repair, appliance repair, and locksmiths. To sell these, he needs a high-signal outreach hook.

The hook: **personalized audio demos delivered via landing page.** Each prospect (a small-business owner) gets a page containing an MP3 that sounds like a natural sales-voicemail referencing their exact business problem — detected by a prior module that actually called their number. The MP3 says things like "Hey Mike, I called Mike's Plumbing at 2:14 PM on Tuesday, rang 8 times, nobody picked up. For a plumber, that's a missed emergency job. Here's what we can do about it..."

**MP3 Generator's role:** turn database rows (populated by upstream modules) into these personalized audio files, save them to cheap cloud storage, write URLs back to the database. It is the CONTENT PRODUCTION step of the lead-gen pipeline.

### Who operates it

The operator is the system owner (a single user, not a coder). They run batches from a dashboard or CLI. No end-users log into this system. It is internal tooling.

### Who the target end-user is (for script tone calibration)

The **business owner who RECEIVES the outreach.** Typically:
- Male, 35-60 years old
- Owns a small trades business (plumbing, HVAC, garage door, appliance repair, locksmith)
- 1-10 employees
- Technical but not sophisticated with AI
- Phone is their #1 lead source
- Loses jobs to competitors because calls go unanswered or to broken voicemail
- Skeptical of sales pitches, so the MP3 must sound human and genuinely helpful, not robotic or salesy

Script tone must match this persona. Not corporate. Not pushy. Conversational. Peer-to-peer. Like one business owner talking to another.

### Larger system this fits into (5-module project, internal codename: CallPitch)

This MP3 Generator is **Module 3 of 5** in a multi-module lead-gen application:

| # | Module | What it does | Relationship to MP3 Gen |
|---|---|---|---|
| 1 | Scraper | Pulls 100 businesses/niche/city from SerpAPI + Playwright. Enriches with website signals, reviews, phone, competitor data. | **Upstream.** Populates the base business rows MP3 Gen reads. |
| 2 | Detection Bot | Calls each business's phone. Records 20 sec. Runs STT + Claude classifier. Flags if voicemail is generic / AI bot is broken / phone rings no answer / etc. | **Upstream.** Populates `detection_result` and `detection_transcript` columns MP3 Gen reads. |
| **3** | **MP3 Generator (this module)** | **Turns the detection + business data into personalized audio files via Kokoro TTS + ffmpeg + Cloudflare R2.** | **THIS MODULE.** |
| 4 | Landing Page | Astro site with dynamic routes per business slug. Embeds the MP3. Shows competitor ranks. 3 CTA buttons with UTM tracking. | **Downstream.** Reads `mp3_url` from DB and serves it to prospects. |
| 5 | Outreach Engines | Email blaster, contact-form blaster, Instagram DM Jarvis. Sends personalized page links to prospects. | **Downstream.** Reads landing page URLs, sends messages, tracks replies. |

**Data flow left-to-right:** Scraper fills → Detection fills more → MP3 Gen fills more → Landing Page reads all → Outreach sends links.

### Why this matters for stage 00-10 decisions

The MP3 Generator is NOT a standalone app. It is a **module** with these properties:

- **Headless.** No end-user UI. At most a minimal operator control panel (run batch / show last runs / show failures). Prospects never see this service directly — they only see the MP3 URL it produces.
- **Batch-oriented.** Runs overnight via cron. Processes N rows per run. Not real-time. Not request-response.
- **Shared database.** Reads from columns written by Modules 1 and 2. Writes to its own columns. Does NOT own the full `businesses` table.
- **Shared infrastructure.** Postgres, Cloudflare R2, logging, failure tracking, authentication are ALL shared with sibling modules. This module does not create its own auth or its own DB or its own logging format.
- **Reusable across apps.** This same MP3 Generator should be usable in a different app (e.g., different vertical, different sales motion) without code changes — just different script templates + different upstream data shape.

### Build mode for this run

**`build_mode = module`** (once Phase 2 build-mode system ships)

For this initial Phase 1 test run: treat as `standalone-app` BUT with the above system context injected. This is a compromise — we want the pipeline to focus on the mechanism (Kokoro TTS + ffmpeg + R2 + DB) and NOT try to build surrounding boilerplate / auth / dashboard that the `module-host` will provide later.

Explicitly: **do NOT scope in** authentication, user management, dashboard UI, deploy infrastructure, or boilerplate. Those are the module-host's job, not this module's.

Explicitly: **DO scope in** the CLI tool, the Kokoro service wrapper, ffmpeg pipeline, R2 upload, DB write layer, failure retry logic, logging, and the script template engine.

### Upstream contract (what MP3 Gen reads)

From shared `businesses` table (populated by Modules 1 and 2):

| Column | Source | Required? |
|---|---|---|
| `id` | Scraper | Required |
| `biz_name` | Scraper | Required |
| `niche` | Scraper | Required |
| `city` | Scraper | Required |
| `owner_first_name` | Scraper | Optional (fallback to generic script) |
| `google_rating` | Scraper | Optional (used in script) |
| `review_count` | Scraper | Optional (used in script) |
| `competitor_count_nearby` | Scraper | Optional (used in script) |
| `years_in_business` | Scraper | Optional (used in script) |
| `detection_result` | Detection Bot | Required (drives script template selection) |
| `detection_transcript` | Detection Bot | Required (quoted in script) |
| `detection_called_at` | Detection Bot | Required (script references when call happened) |

Filter: `detection_result IS NOT NULL AND mp3_url IS NULL`

### Downstream contract (what MP3 Gen writes)

To shared `businesses` table:

| Column | Type | Description |
|---|---|---|
| `mp3_url` | text | Public R2 URL |
| `mp3_generated_at` | timestamp | When created |
| `mp3_script_version` | text | Which template was used |
| `mp3_script_text` | text | Full filled-in script (for transcript display on landing page) |
| `mp3_voice_used` | text | Kokoro voice ID |
| `mp3_duration_seconds` | int | Audio length |
| `mp3_offer_type` | text | Which offer this MP3 pitches |
| `mp3_generation_attempts` | int | Retry count |

To new sibling table `mp3_history` (owned by this module):

| Column | Description |
|---|---|
| All mp3_* fields above | Historical record of every MP3 ever made per business |
| `biz_id` | FK to businesses |
| `created_at` | Timestamp |

To shared `module_failures` table (owned by host, written to by all modules):

| Column | Description |
|---|---|
| `module_name` | "mp3-generator" |
| `row_id` | biz_id that failed |
| `error` | error string |
| `timestamp` | when it failed |

To `logs/mp3-generator/YYYY-MM-DD.jsonl` (JSON-line format, not plain text).

### Triggers (how MP3 Gen gets invoked)

- **Cron:** `0 2 * * *` (2 AM daily, after Detection Bot finishes ~1 AM)
- **CLI:** `python -m mp3_generator [--niche X --city Y --limit N --dry-run ...]`
- **Event (future):** subscribe to `detection.completed` for real-time processing (not in v1)

### External services this module uses

- **Kokoro TTS** — self-hosted on same host machine, FastAPI wrapper on `localhost:8881`, NOT publicly exposed.
- **ffmpeg** — local binary for WAV → MP3 conversion (64kbps mono).
- **Cloudflare R2** — object storage with custom domain `mp3s.yourdomain.com`. Zero egress fees.
- **Postgres** — shared DB.

### Legal / compliance baseline

- No TCPA exposure. This module produces files. Does not make calls or send anything.
- No CAN-SPAM exposure. No email sent from this module.
- Kokoro voices are synthetic, commercial-use licensed. Safe.

### Missing details owner will provide (flagged gaps)

Coder should treat these as inputs from the operator, not invent:
- Actual script template copy (tone sample to be written by owner)
- Niche facts JSON structure (1 example from owner, rest copied)
- Telegram alert webhook credentials + message format
- Priority sort rule (high-priority rows processed first — rule TBD)
- Final list of which 5 niches for v1

### Success criteria (how to know this module is done)

- Runs 500 MP3s overnight without manual intervention
- Failure rate < 2%
- Audio quality passes a manual listen-test on 5 random MP3s per niche
- Conforms to Standard Module Contract (§4 of master architecture doc)
- Ships with test harness that runs smoke test on mock data without upstream modules

---

## Now follows the main PRD body

[Paste the existing 18-section PRD-3 document here, unchanged.]
