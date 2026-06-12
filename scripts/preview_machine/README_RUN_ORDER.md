# RUN ORDER — Preview Site Machine

All pipeline files live in this folder (`scripts/preview_machine/`), plus an
`assets/` folder for images.

## Files
- `biz_pull.py`    — finds businesses (DataForSEO)  **(not in repo yet — keep your local copy here)**
- `gsa_filter.py`  — splits the scrape into GSA-deliverable vs blocked sites
- `site_age.py`    — scores their old websites + pulls logo
- `copywriter.py`  — writes copy JSONs via your Claude SUBSCRIPTION (no API key)
- `sitegen.py`     — builds a preview site per business from the copy cache
- `template.html`  — the site design
- `assets/`        — ba1.jpg, ba2.jpg (your before/afters), optional hero.jpg

## One-time setup
1. Put ba1.jpg + ba2.jpg (and optional hero.jpg) in `assets/`.
2. Set keys in your terminal (Windows shown; Mac/Linux use `export`):
   set DATAFORSEO_LOGIN=your_login
   set DATAFORSEO_PASSWORD=your_password
   (ANTHROPIC_API_KEY only needed for the API overflow path — the normal
   copy step uses your Claude subscription via `claude login`.)
3. pip install requests beautifulsoup4

## THE RUN (in order)

# 1. find the category id for your niche
python biz_pull.py --findcat pressure

# 2. edit biz_pull.py CONFIG: paste the category id, set LABEL + COORD, then:
python biz_pull.py
#   -> makes <label>_websites_*.csv  AND  <label>_coldcall_*.csv  (~$0.31)

# 3. keep only sites GSA can actually deliver to (free)
python gsa_filter.py <label>_websites_*.csv
#   -> <label>_gsa_ready_*.csv (BUILD THESE)  +  <label>_gsa_blocked_*.csv (cold email later)

# 4. score the websites (free) — adds the logo column sitegen uses
python site_age.py <label>_gsa_ready_*.csv
#   -> makes site_audit.csv (STRONG TARGETs on top, with logo + reasons)

# 5. FREE dress rehearsal — builds all sites with placeholder copy, no cost
python sitegen.py site_audit.csv --offline
#   -> open a few files in previews/<slug>/index.html to check

# 6. write the real copy on your SUBSCRIPTION (no API spend, resumable)
python copywriter.py site_audit.csv --outdir copy
#   -> copy/<slug>.json per business. If you hit a rate limit, just re-run
#      later — finished businesses are skipped automatically.

# 7. edit sitegen.py CONFIG: set NICHE, BASE_URL (your cloudflare project name),
#    CAL_LINK (GHL calendar), CHAT_SNIPPET (GHL chat <script>), MAX_SITES=25 to test
python sitegen.py site_audit.csv --copydir copy
#   -> renders from the copy cache, writes previews/ + site_audit_with_previews.csv
#   (the old API path still works:  python sitegen.py site_audit.csv  — overflow
#    valve for huge runs; swap MODEL to claude-haiku-4-5 there for ~4x cheaper)

# 8. put them online (one-time login first)
npx wrangler login
npx wrangler pages deploy previews --project-name=YOUR-PROJECT-NAME

# Every preview URL is now live and listed in site_audit_with_previews.csv
# -> load that CSV into GSA; message merges {business} + {preview_url} + reasons
