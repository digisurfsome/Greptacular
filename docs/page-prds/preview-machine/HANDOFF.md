# HANDOFF: Preview Site Machine → AutoForge Integration

**From:** Claude (claude.ai session, June 2026) — pipeline already debugged and smoke-tested end to end.
**To:** Claude instance in Claude Code working on AutoForge.
**Owner:** Tim. Read this whole doc before touching anything.

---

## 1. What this is (business context)

A mass cold-outreach machine for selling websites to local service businesses (first niche: pressure washing, ~20 niches planned). The play:

1. Scrape every business in a niche+city from DataForSEO (~$0.31 per 1,000 businesses).
2. Audit their existing websites for age/neglect signals (free — direct HTTP fetches).
3. Auto-generate a polished, personalized **static preview website for each business** — their name, phone, city, Google rating, scraped logo, and AI-written copy baked into a premium HTML template.
4. Deploy all previews to one Cloudflare Pages project (free, ~20K sites per project). Each business gets `https://<custom-domain>/<business-slug>/`.
5. Blast the preview links via GSA Website Contact forms. Offer: $197/mo, setup waived for first 5, GHL upsells stacked on top (chatbot, AI receptionist, etc.). Post-sale fulfillment is rebuilt in GHL AI Studio — the static preview is the demo, not the product.

This works today as four files run by hand. **Your job: build it into AutoForge as an orchestrated workflow, and move the AI copywriting off the metered API and onto the subscription (Section 5 — the most important section).**

---

## 2. The pipeline files & run order

All four files live in one folder plus `assets/` (ba1.jpg, ba2.jpg, hero.jpg — before/after photos referenced by the template at `../assets/`).

| Stage | File | What it does | Cost |
|---|---|---|---|
| 1 | `biz_pull.py` | DataForSEO Business Listings pull for category+coordinates. Splits into `<label>_websites_*.csv` (has website) and `<label>_coldcall_*.csv` (no website — phone list). | $0.01/req + $0.0003/row, max $0.31 per 1,000 |
| 2 | `site_age.py` | Fetches each website, detects platform/jQuery age/stale copyright/no viewport/no chat/etc., scores weakness, scrapes their logo URL. Outputs `site_audit.csv` sorted STRONG TARGET first. | Free (0.5s sleep per site — keep it) |
| 3 | `sitegen.py` | Renders one preview site per row into `previews/<slug>/index.html` using `template.html` ({{TOKEN}} replacement). Writes `site_audit_with_previews.csv` with a `preview_url` column for GSA merge. | **API tokens — see Section 5** |
| 4 | deploy | `npx wrangler pages deploy previews --project-name=X` | Free |

Modes that already exist and must keep working:
- `biz_pull.py --findcat <kw>` (category ID lookup), `--selftest`
- `site_age.py --selftest`
- `sitegen.py <csv> --offline` (free template copy, no API — the dress-rehearsal mode), `--selftest`

---

## 3. The CSV contracts (do not break these)

**biz_pull → site_age** (`*_websites_*.csv`):
`business, website, domain, phone, category, rating, reviews, claimed, address, city, state, zip`

**site_age → sitegen** (`site_audit.csv`):
`verdict, score, business, phone, city, state, zip, rating, reviews, address, url, platform, theme, jquery, copyright, mobile, chat, logo, reasons`

Notes:
- `phone` is Excel-safe wrapped (`="(254) 555-0101"`) by biz_pull; it passes through site_age untouched and **sitegen already strips the wrap**. Don't "fix" this.
- `logo` is an absolute URL scraped from their site (og:image → header img with "logo" → apple-touch-icon). sitegen uses it when `USE_LOGOS=True`, falls back to a letter mark.
- `reasons` is human-readable outreach ammo per business ("copyright 2016 (10 yrs stale); no mobile viewport; no live chat"). **This column is the fuel for the planned per-business pitch message (Section 6). Preserve it everywhere.**
- `verdict` values: STRONG TARGET / WORTH A LOOK / SKIP / BLOCKED / UNREACHABLE / PARKED/EMPTY. BLOCKED means a bot wall — the audit could NOT inspect them, so no claims about their site may appear in outreach for those rows. PARKED/EMPTY pitch is "your site is gone," not feature gaps. This logic is already encoded; keep it.

---

## 4. Fixes already applied in this session (do not redo, do not regress)

1. **`site_age.py` metadata carry-through (critical):** originally site_audit.csv dropped business name/phone/city/etc., which killed sitegen ("No business/name column"). `load_urls()` now returns `(url, meta)` pairs and `run()` merges meta into every audit row. The column list in Section 3 is the post-fix contract.
2. **`biz_pull.py` state column:** added from DataForSEO `address_info.region`. Without it sitegen silently hardcoded "TX".
3. **`--findcat`:** a parallel session hardcoded the category list (works fine). The real DataForSEO endpoint exists but is **GET, not POST**: `GET https://api.dataforseo.com/v3/business_data/business_listings/categories` (POSTing returns the 404 that started all this).
4. Smoke-tested end to end with stubbed network: no unfilled `{{TOKENS}}`, phone unwraps, logo renders, city lands in copy.

---

## 5. THE SONNET SITUATION (the reason for this handoff)

**Current state:** `sitegen.py → claude_copy()` makes a direct `POST https://api.anthropic.com/v1/messages` call per business (model `claude-sonnet-4-6`, ~1,400 max_tokens) using `ANTHROPIC_API_KEY`. At scale (5,000+ sites per batch, 20 niches), that's recurring metered API spend.

**Goal:** Tim runs AutoForge against his Claude subscription. The copywriting must run **through the subscription, not the API key.** Since you ARE a subscription-billed Claude instance, the move is: **you (or AutoForge's agents) become the copywriter, and sitegen becomes a dumb renderer.**

**Recommended architecture — the copy-cache pattern:**

1. Add a `--copydir <dir>` mode to sitegen: for each row, if `<copydir>/<slug>.json` exists, use it; else fall back to `offline_copy()`. Remove nothing — `--offline` and the API path stay as fallbacks.
2. Build an AutoForge workflow step where the agent (you, on subscription) reads `site_audit.csv` and writes `<slug>.json` per business — batching 10–20 businesses per generation pass to be efficient with context.
3. Orchestration becomes: `biz_pull → site_age → [agent writes copy JSONs] → sitegen --copydir copy/ → wrangler deploy`.

This decouples copywriting from any billing path: subscription agent, API, or offline templates all feed the same renderer.

**The exact copy contract (per business JSON) — reproduce faithfully, keys are template-bound:**

```json
{"badge_text": "5-7 word premium positioning badge, title case",
 "hero_headline_pre": "first part of headline, 3-6 words",
 "hero_accent": "final 1-3 words (highlighted)",
 "hero_sub": "1-2 sentences, what they do + where, 25-40 words",
 "tagline_short": "4-6 words",
 "services_headline": "5-8 words",
 "services_sub": "one sentence",
 "services": [6 x {"name": "2-4 word service", "desc": "one sentence, 12-20 words"}],
 "step_1": {"name": "2-4 words", "desc": "one sentence"},
 "step_2": {"name": "...", "desc": "..."},
 "step_3": {"name": "...", "desc": "..."},
 "about_headline": "6-10 words",
 "about_text_1": "2 sentences, local flavor",
 "about_text_2": "2 sentences, approach/values",
 "checks": ["4 trust points, 2-4 words each"],
 "panel_card_title": "4-6 words",
 "panel_card_sub": "one short sentence",
 "reviews_headline": "5-9 words about serving the city",
 "reviews_sub": "one sentence inviting a call",
 "cta_headline": "5-9 word CTA",
 "cta_sub": "one sentence",
 "footer_blurb": "one sentence"}
```

**Copy rules (these are liability rules, not style preferences — enforce them):**
- Use ONLY known facts: business name, city, state, and real Google rating/review count when present.
- NEVER invent: stats, years in business, awards, certifications, licenses, customer quotes, guarantees.
- `checks` must be unverifiable-claim-free: "Locally owned", "Free quotes", "Fast response", "Satisfaction focused" — never "Licensed & insured".
- Mention the city naturally. Confident, premium, plain-spoken. No exclamation marks. No "look no further" clichés.

**One honest caveat to surface to Tim, not bury:** subscription usage is included but **rate-limited**, not infinite. Generating copy for thousands of sites in one sitting will hit Claude Code session/usage caps on the $100 plan. Design the workflow to batch and resume (the copy-cache pattern makes this natural — JSONs already written are never regenerated), and treat the API path as the overflow valve for genuinely huge runs, where Haiku (`claude-haiku-4-5`) cuts cost ~4x vs Sonnet.

---

## 6. Roadmap context (build extensible, don't build these yet)

- **Pitch column:** a per-business 2–3 sentence outreach message that names the 2 most embarrassing problems from `reasons` and links the preview. Same generation pass as the copy JSON — just one more key (`"pitch"`) written into the output CSV for GSA merge fields `{business}` `{pitch}` `{preview_url}`. Respect BLOCKED/PARKED verdict rules from Section 3.
- **Multi-template:** 3 designs per niche planned. `THEMES` rotation in sitegen becomes a `TEMPLATES` rotation (template path per site). Keep the {{TOKEN}} vocabulary identical across templates.
- **Multi-niche / multi-city:** config-per-run (CATEGORIES, LABEL, COORD, NICHE, BASE_URL). AutoForge should treat a "market" (niche × city) as the unit of work. Dedupe on `domain` across overlapping city radii before outreach.
- **Custom domain:** one Cloudflare Pages project per niche, custom subdomain attached (e.g. `powerwashing.digibranded.ai`). `BASE_URL` in sitegen must match before the real run — it's baked into the outreach CSV.

## 7. Hard constraints — do not change

- Template token set ({{BUSINESS_NAME}}, {{HERO_SUB}}, etc.) — the render contract.
- `../assets/` relative paths in template.html (resolves to `previews/assets/`, which sitegen copies in).
- The 0.5s politeness sleep in site_age.py.
- Excel phone wrap handling.
- The no-invented-claims copy rules.
- All existing CLI modes and selftests must still pass: `biz_pull.py --selftest`, `site_age.py --selftest`, `sitegen.py --selftest`, `sitegen.py <csv> --offline`.
