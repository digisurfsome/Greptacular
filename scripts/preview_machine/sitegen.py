#!/usr/bin/env python3
"""
sitegen.py -- mass preview-site generator.

CSV in (from biz_pull.py or site_age.py output) -> one polished preview site
per business -> previews/<slug>/index.html -> CSV out with preview_url column.

  pip install requests
  set ANTHROPIC_API_KEY env var (skip it and use --offline to test free)

RUN:
  python sitegen.py my_list.csv                # full run, Claude API writes copy
  python sitegen.py my_list.csv --offline      # free test run, template copy
  python sitegen.py my_list.csv --copydir copy # use pre-written copy JSONs
                                               # (from copywriter.py, subscription
                                               # billed -- no API key needed)
  python sitegen.py --selftest                 # render one sample, no internet

Then deploy the previews/ folder to Cloudflare Pages (one command):
  npx wrangler pages deploy previews --project-name=previews
"""

import csv, html as html_escape_mod, json, os, re, sys, time
import requests

# ============================================================ CONFIG
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL    = "claude-sonnet-4-6"     # swap to "claude-haiku-4-5" for cheaper copy
NICHE    = "pressure washing"      # used in the copy prompt
BASE_URL = "https://previews.example.com"   # your Cloudflare Pages URL, no trailing /
CAL_LINK = "#quote"                # your GHL calendar link (placeholder ok)
CHAT_SNIPPET = ""                  # paste your GHL chat widget <script> here, or leave ""
USE_LOGOS = True                   # use their logo from the CSV 'logo' column if present
TEMPLATE = "template.html"
OUTDIR   = "previews"
THEMES   = ["theme-hydro", "theme-emerald", "theme-gold"]   # rotates per site
MAX_SITES = 0                      # 0 = all rows; set 25 for a test batch
# Only build sites for these site_audit verdicts. Rows whose verdict is
# anything else (SKIP, BLOCKED, UNREACHABLE, PARKED/EMPTY...) are dropped.
# CSVs without a verdict column (raw biz_pull output) are untouched.
# Override with:  python sitegen.py file.csv --all
KEEP_VERDICTS = {"STRONG TARGET", "WORTH A LOOK"}
# Optional: per-service photo URLs (e.g. Pexels). Leave empty for the built-in
# gradient look. If filled, images download once into previews/assets/.
SERVICE_PHOTOS = []
# ============================================================

API_URL = "https://api.anthropic.com/v1/messages"

PROMPT = """You write website copy for a local {niche} company. Use ONLY the facts given. STRICT RULES:
- NEVER invent statistics, years in business, awards, certifications, customer quotes, or guarantees.
- Mention the city naturally. Confident, premium, plain-spoken tone. No exclamation marks. No cliches like "look no further".
Facts: business name "{business}", city {city}, {state}.{extra}
Return ONLY JSON (no markdown) with EXACTLY these keys:
{{"badge_text": "5-7 word premium positioning badge, title case",
"hero_headline_pre": "first part of headline, 3-6 words",
"hero_accent": "final 1-3 words of the headline (will be highlighted)",
"hero_sub": "1-2 sentences, what they do + where, 25-40 words",
"tagline_short": "4-6 word tagline",
"services_headline": "5-8 words",
"services_sub": "one sentence",
"services": [6 items of {{"name": "2-4 word {niche} service", "desc": "one sentence, 12-20 words"}}],
"step_1": {{"name": "2-4 words", "desc": "one sentence"}},
"step_2": {{"name": "2-4 words", "desc": "one sentence"}},
"step_3": {{"name": "2-4 words", "desc": "one sentence"}},
"about_headline": "6-10 words",
"about_text_1": "2 sentences about the company, local flavor, no invented facts",
"about_text_2": "2 sentences on approach/values, no invented facts",
"checks": ["4 short trust points, 2-4 words each, NO unverifiable claims like 'licensed' -- use things like 'Locally owned', 'Free quotes', 'Satisfaction focused', 'Fast response'"],
"panel_card_title": "4-6 words",
"panel_card_sub": "one short sentence",
"reviews_headline": "5-9 words about serving {city}",
"reviews_sub": "one sentence inviting a call, no invented review quotes",
"cta_headline": "5-9 word call to action",
"cta_sub": "one sentence",
"footer_blurb": "one sentence"}}"""


def claude_copy(business, city, state, extra_facts=""):
    extra = f" Additional known facts: {extra_facts}" if extra_facts else ""
    body = {"model": MODEL, "max_tokens": 1400,
            "messages": [{"role": "user", "content": PROMPT.format(
                niche=NICHE, business=business, city=city, state=state, extra=extra)}]}
    r = requests.post(API_URL, timeout=90, json=body,
                      headers={"x-api-key": ANTHROPIC_API_KEY,
                               "anthropic-version": "2023-06-01",
                               "content-type": "application/json"})
    r.raise_for_status()
    txt = "".join(b.get("text", "") for b in r.json().get("content", []))
    txt = re.sub(r"^```(?:json)?|```$", "", txt.strip(), flags=re.M).strip()
    return json.loads(txt)


def offline_copy(business, city, state):
    """Free, deterministic copy for test runs -- decent, not Claude-good."""
    n = NICHE
    return {
        "badge_text": f"{city}'s Premier {n.title()} Team",
        "hero_headline_pre": "A Clean Property,",
        "hero_accent": "Done Right",
        "hero_sub": f"{business} delivers professional {n} for homes and businesses across {city}, {state} — careful work, honest pricing, results you can see from the street.",
        "tagline_short": f"Professional {n.title()}",
        "services_headline": f"Complete {n.title()} Services",
        "services_sub": f"Everything your property needs, handled by one local {city} team.",
        "services": [
            {"name": "House Washing", "desc": "Gentle soft-wash cleaning that lifts dirt, mold, and mildew without damaging your siding."},
            {"name": "Driveway & Concrete", "desc": "Deep surface cleaning that strips years of grime, oil, and stains from concrete."},
            {"name": "Roof Cleaning", "desc": "Low-pressure treatment that safely removes streaks and buildup from shingles."},
            {"name": "Deck & Patio", "desc": "Restores wood and stone outdoor spaces to the way they looked when new."},
            {"name": "Gutter Brightening", "desc": "Exterior gutter cleaning that takes the black streaks off your home's trim lines."},
            {"name": "Commercial Exteriors", "desc": "Storefronts, sidewalks, and building exteriors kept clean for your customers."},
        ],
        "step_1": {"name": "Get a Quote", "desc": "Tell us about your property and get a clear, honest price."},
        "step_2": {"name": "We Get to Work", "desc": "Our crew arrives on time and treats your property like our own."},
        "step_3": {"name": "See the Difference", "desc": "Walk the job with us and see the results up close."},
        "about_headline": f"A local team that takes {city} properties personally",
        "about_text_1": f"{business} is a locally owned {n} company serving {city} and the surrounding area. We built this business on doing careful work and treating every property like it's our own.",
        "about_text_2": "We show up when we say we will, quote honestly, and don't consider a job finished until you're happy with how it looks.",
        "checks": ["Locally owned", "Free quotes", "Fast response", "Satisfaction focused"],
        "panel_card_title": f"Serving {city} and nearby",
        "panel_card_sub": "Residential and commercial properties, one careful job at a time.",
        "reviews_headline": f"Trusted by your neighbors in {city}",
        "reviews_sub": "Call today and find out why local property owners keep our number saved.",
        "cta_headline": "Ready to see your property like new?",
        "cta_sub": "Get a fast, free quote — no pressure, no obligation.",
        "footer_blurb": f"Professional {n} serving {city}, {state} and surrounding communities.",
    }


# ------------------------------------------------ helpers
def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60]


def digits(phone):
    d = re.sub(r"\D", "", phone or "")
    return ("+1" + d[-10:]) if len(d) >= 10 else d


def stars_for(rating):
    try:
        r = round(float(rating))
        return "★" * r + "☆" * (5 - r)
    except (TypeError, ValueError):
        return "★★★★★"


def stat_strip(rating, reviews, city):
    """Real data only. Falls back to safe generics when reviews are absent."""
    s = []
    if rating:
        s.append((str(rating), "Google rating"))
    if reviews:
        s.append((str(reviews), "Google reviews"))
    s += [("Free", "No-obligation quotes"), (city or "Local", "Proudly served")]
    fillers = [("Fast", "Response times"), ("Local", "Owned & operated")]
    while len(s) < 4:
        s.append(fillers[len(s) % 2])
    return s[:4]


def render(tpl, biz, copy, theme):
    name = biz["business"]
    city, state = biz.get("city") or "your area", biz.get("state") or "TX"
    logo_url = (biz.get("logo") or "").strip() if USE_LOGOS else ""
    letter = (name[:1] or "•").upper()
    esc = lambda s: html_escape_mod.escape(str(s), quote=True)
    logo_html = (f'<img class="logo-img" src="{esc(logo_url)}" alt="{esc(name)} logo">'
                 if logo_url.startswith("http")
                 else f'<span class="logo-mark">{esc(letter)}</span>')
    rep = {
        "BUSINESS_NAME": name, "LOGO_LETTER": letter, "LOGO_HTML": logo_html,
        "CITY": city, "STATE": state,
        "PHONE": biz.get("phone") or "", "PHONE_DIGITS": digits(biz.get("phone")),
        "ADDRESS_LINE": biz.get("address") or f"{city}, {state}",
        "THEME_CLASS": theme, "YEAR": time.strftime("%Y"),
        "NICHE_LOWER": NICHE.lower(),
        "CAL_LINK": CAL_LINK, "CHAT_SNIPPET": CHAT_SNIPPET,
        "STARS": stars_for(biz.get("rating")),
        "IMG_CLASS": "has-photo" if SERVICE_PHOTOS else "",
        "BADGE_TEXT": copy["badge_text"],
        "HERO_HEADLINE_PRE": copy["hero_headline_pre"],
        "HERO_ACCENT": copy["hero_accent"], "HERO_SUB": copy["hero_sub"],
        "TAGLINE_SHORT": copy["tagline_short"],
        "SERVICES_HEADLINE": copy["services_headline"],
        "SERVICES_SUB": copy["services_sub"],
        "ABOUT_HEADLINE": copy["about_headline"],
        "ABOUT_TEXT_1": copy["about_text_1"], "ABOUT_TEXT_2": copy["about_text_2"],
        "PANEL_CARD_TITLE": copy["panel_card_title"],
        "PANEL_CARD_SUB": copy["panel_card_sub"],
        "REVIEWS_HEADLINE": copy["reviews_headline"],
        "REVIEWS_SUB": copy["reviews_sub"],
        "CTA_HEADLINE": copy["cta_headline"], "CTA_SUB": copy["cta_sub"],
        "FOOTER_BLURB": copy["footer_blurb"],
    }
    for i in range(6):
        svc = copy["services"][i] if i < len(copy["services"]) else {"name": "", "desc": ""}
        rep[f"SERVICE_{i+1}_NAME"] = svc["name"]
        rep[f"SERVICE_{i+1}_DESC"] = svc["desc"]
        url = SERVICE_PHOTOS[i % len(SERVICE_PHOTOS)] if SERVICE_PHOTOS else ""
        rep[f"SVC_IMG_{i+1}"] = f"background-image:url('{url}')" if url else ""
    for i in (1, 2, 3):
        rep[f"STEP_{i}_NAME"] = copy[f"step_{i}"]["name"]
        rep[f"STEP_{i}_DESC"] = copy[f"step_{i}"]["desc"]
    checks = (copy.get("checks") or [])[:4] + [""] * 4
    for i in (1, 2, 3, 4):
        rep[f"CHECK_{i}"] = checks[i - 1]
    for i, (big, label) in enumerate(stat_strip(biz.get("rating"),
                                                biz.get("reviews"), city), 1):
        rep[f"STAT_{i}_BIG"], rep[f"STAT_{i}_LABEL"] = big, label
    # Escape everything except tokens that are intentionally raw HTML/CSS
    raw_keys = {"LOGO_HTML", "CHAT_SNIPPET", "THEME_CLASS", "CAL_LINK",
                "STARS", "IMG_CLASS"}
    out = tpl
    for k, v in rep.items():
        s = str(v)
        if k not in raw_keys and not k.startswith("SVC_IMG_"):
            s = html_escape_mod.escape(s, quote=True)
        out = out.replace("{{" + k + "}}", s)
    return out


# ------------------------------------------------ CSV handling
def read_rows(path, keep_all=False):
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        rdr = csv.DictReader(f)
        cols = {c.lower(): c for c in (rdr.fieldnames or [])}
        def col(*names):
            return next((cols[n] for n in names if n in cols), None)
        c_name = col("business", "name", "title")
        if not c_name:
            print(f"No business/name column. Columns: {rdr.fieldnames}"); sys.exit(1)
        c_phone, c_city = col("phone"), col("city")
        c_state, c_rate = col("state", "region"), col("rating", "rate")
        c_rev, c_addr = col("reviews", "review_count"), col("address")
        c_logo = col("logo")
        c_verdict = col("verdict")
        skipped = 0
        rows = []
        for r in rdr:
            name = (r.get(c_name) or "").strip()
            if not name:
                continue
            if c_verdict and not keep_all:
                v = (r.get(c_verdict) or "").strip().upper()
                if v and v not in KEEP_VERDICTS:
                    skipped += 1
                    continue
            phone = (r.get(c_phone) or "").strip() if c_phone else ""
            phone = phone.replace('="', "").replace('"', "")   # undo Excel-safe wrap
            rows.append({"business": name, "phone": phone,
                         "city": (r.get(c_city) or "").strip() if c_city else "",
                         "state": (r.get(c_state) or "").strip() if c_state else "",
                         "rating": (r.get(c_rate) or "").strip() if c_rate else "",
                         "reviews": (r.get(c_rev) or "").strip() if c_rev else "",
                         "address": (r.get(c_addr) or "").strip() if c_addr else "",
                         "logo": (r.get(c_logo) or "").strip() if c_logo else "",
                         "_raw": r})
        if skipped:
            print(f"Filtered out {skipped} row(s) with verdict outside "
                  f"{sorted(KEEP_VERDICTS)} -- no money or sites wasted on SKIPs. "
                  f"(Use --all to build everything.)")
        return rows, rdr.fieldnames


def write_csv(path, rows, fieldnames):
    out = path.rsplit(".", 1)[0] + "_with_previews.csv"
    cols = list(fieldnames) + [c for c in ("preview_url",) if c not in fieldnames]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore", restval="")
        w.writeheader()
        for r in rows:
            d = dict(r["_raw"]); d["preview_url"] = r.get("preview_url", "")
            w.writerow(d)
    return out


# ------------------------------------------------ copy cache (--copydir)
def load_cached_copy(copydir, slug, business, manifest):
    """Copy-cache lookup: <copydir>/<slug>.json by our slug, else by the
    copywriter's slug via manifest.json (business name -> slug). Returns the
    copy dict or None. Never calls the API."""
    path = os.path.join(copydir, slug + ".json")
    if not os.path.exists(path):
        alt = (manifest or {}).get(business)
        if alt:
            path = os.path.join(copydir, alt + ".json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def load_manifest(copydir):
    mpath = os.path.join(copydir, "manifest.json")
    if os.path.exists(mpath):
        with open(mpath, encoding="utf-8") as f:
            return json.load(f)
    return {}


# ------------------------------------------------ main
def main(csv_path, offline=False, copydir=None, keep_all=False):
    if copydir and not os.path.isdir(copydir):
        print(f"--copydir {copydir} is not a directory. Run copywriter.py first.")
        sys.exit(1)
    if not offline and not copydir and not ANTHROPIC_API_KEY:
        print("Set ANTHROPIC_API_KEY, or run with --offline for a free test, "
              "or --copydir <dir> to use copywriter.py output.")
        sys.exit(1)
    tpl = open(TEMPLATE, encoding="utf-8").read()
    tpl = tpl.replace("Instant Power Washing Quote",
                      f"Instant {NICHE.title()} Quote")
    rows, fieldnames = read_rows(csv_path, keep_all=keep_all)
    if MAX_SITES:
        rows = rows[:MAX_SITES]
    os.makedirs(OUTDIR, exist_ok=True)
    import shutil
    if os.path.isdir("assets"):
        shutil.copytree("assets", os.path.join(OUTDIR, "assets"),
                        dirs_exist_ok=True)
    manifest = load_manifest(copydir) if copydir else {}
    src = "offline copy" if offline else (f"copy cache {copydir}/" if copydir else MODEL)
    print(f"Generating {len(rows)} preview sites -> {OUTDIR}/ ({src})")
    cache_misses = 0
    for i, biz in enumerate(rows, 1):
        slug = slugify(biz["business"]) or f"site-{i}"
        if copydir:
            # cached JSON from copywriter.py; fall back to offline copy,
            # NEVER the API in this mode
            copy = load_cached_copy(copydir, slug, biz["business"], manifest)
            if copy is None:
                cache_misses += 1
                print(f"  [{i}] {slug}: no cached copy -- using offline copy")
                copy = offline_copy(biz["business"], biz["city"] or "your area",
                                    biz["state"] or "TX")
        else:
            try:
                copy = (offline_copy(biz["business"], biz["city"] or "your area",
                                     biz["state"] or "TX")
                        if offline else
                        claude_copy(biz["business"], biz["city"] or "the area",
                                    biz["state"] or "TX",
                                    f"Google rating {biz['rating']} from {biz['reviews']} reviews"
                                    if biz.get("rating") else ""))
            except Exception as e:
                print(f"  [{i}] {slug}: copy failed ({e}) -- using offline copy")
                copy = offline_copy(biz["business"], biz["city"] or "your area",
                                    biz["state"] or "TX")
        html = render(tpl, biz, copy, THEMES[(i - 1) % len(THEMES)])
        os.makedirs(os.path.join(OUTDIR, slug), exist_ok=True)
        with open(os.path.join(OUTDIR, slug, "index.html"), "w",
                  encoding="utf-8") as f:
            f.write(html)
        biz["preview_url"] = f"{BASE_URL}/{slug}/"
        print(f"  [{i}/{len(rows)}] {biz['preview_url']}")
        if not offline and not copydir:
            time.sleep(0.4)
    out = write_csv(csv_path, rows, fieldnames)
    if copydir and cache_misses:
        print(f"\nNOTE: {cache_misses} site(s) had no cached copy (offline copy used). "
              f"Run copywriter.py again to fill the cache, then re-run sitegen.")
    print(f"\nDone. Sites in ./{OUTDIR}/   URLs written to {out}")
    print(f"Deploy:  npx wrangler pages deploy {OUTDIR} --project-name=previews")


def selftest():
    tpl = open(TEMPLATE, encoding="utf-8").read()
    biz = {"business": "Temple Pressure Pros", "phone": "(254) 555-0184",
           "city": "Temple", "state": "TX", "rating": "4.8", "reviews": "47",
           "address": "Temple, TX"}
    html = render(tpl, biz, offline_copy(biz["business"], biz["city"],
                                         biz["state"]), "theme-hydro")
    left = re.findall(r"\{\{[A-Z0-9_]+\}\}", html)
    # write into a subfolder so the ../assets/ image paths resolve the same
    # way they do for real preview sites (previews/<slug>/index.html)
    os.makedirs(os.path.join(OUTDIR, "sample"), exist_ok=True)
    with open(os.path.join(OUTDIR, "sample", "index.html"), "w",
              encoding="utf-8") as f:
        f.write(html)
    print(f"Rendered {OUTDIR}/sample/index.html | unfilled tokens: {left or 'none'}")
    print("RESULT:", "PASS" if not left else "FAIL")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        args = sys.argv[1:]
        copydir = None
        if "--copydir" in args:
            idx = args.index("--copydir")
            if idx + 1 >= len(args) or args[idx + 1].startswith("--"):
                print("--copydir needs a directory, e.g. --copydir copy"); sys.exit(1)
            copydir = args[idx + 1]
            del args[idx:idx + 2]
        files = [a for a in args if not a.startswith("--")]
        if not files:
            print(__doc__); sys.exit(1)
        main(files[0], offline="--offline" in args, copydir=copydir,
             keep_all="--all" in args)
