"""
site_age.py  -- find old / weak websites worth replacing.

This bolts onto your existing scrape. Your DataForSEO scrape finds the
businesses and their website URLs; THIS reads those URLs, fetches each site,
and scores how old / neglected / feature-poor it is. The reasons it prints
double as your outreach ammo ("not mobile-friendly, no chat, copyright 2016").

It does NOT use any API or your DataForSEO creds. It just fetches the page
HTML (free) and reads the tells in it.

------------------------------------------------------------------
WHAT IT LOOKS AT (all read straight from the page source):
  - Platform: WordPress / Wix / Squarespace / GoDaddy / Weebly / Shopify
  - WordPress theme name + WordPress version (when leaked)
  - jQuery / Bootstrap version  (old library = old, untouched build)
  - Mobile viewport tag present?  (missing = not mobile-friendly = old)
  - Open Graph tags present?      (missing = older build)
  - Copyright year in footer      (stale year = neglected)
  - HTTPS working?
  - Live chat / chatbot present?  (missing = your upsell hook)
Then it tallies a weakness score and gives a verdict.
------------------------------------------------------------------

HOW TO RUN:
  pip install requests beautifulsoup4
  # Option A: make a file urls.txt with one website per line, then:
  python site_age.py
  # Option B: point it at your scrape CSV (auto-finds a website/url/domain column):
  python site_age.py your_market_teardown.csv
  # Check the detection logic works, no internet needed:
  python site_age.py --selftest

Output: prints each site + writes site_audit.csv (sorted best targets first).
NOTE: you run this on your machine -- it needs to reach the real websites.
"""

import csv
import re
import sys
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
THIS_YEAR = datetime.now().year

CHAT_SIGNATURES = [
    "tawk.to", "intercom", "drift.com", "livechatinc", "livechat.com",
    "tidio", "crisp.chat", "zopim", "zendesk", "olark", "podium",
    "customerchat", "leadconnector", "gohighlevel", "hubspot",
    "messenger/customerchat", "smartsupp",
]
BUILDERS = {
    "wix": ["wixstatic.com", "wix.com", "parastorage.com"],
    "squarespace": ["squarespace.com", "static1.squarespace"],
    "godaddy": ["img1.wsimg.com", "godaddy", "websitebuilder"],
    "weebly": ["weebly.com", "editmysite"],
    "shopify": ["cdn.shopify.com", "myshopify"],
}


def fetch(url):
    """Return (final_url, html, https_ok, status).
    status: 'ok' | 'blocked' (bot wall -- could NOT check, never claim) | 'dead'."""
    if not url.startswith("http"):
        url = "https://" + url
    https_ok = False
    html = None
    final = url
    status = "dead"
    for scheme_url in (url.replace("http://", "https://"),
                       url.replace("https://", "http://")):
        try:
            r = requests.get(scheme_url, headers={"User-Agent": UA},
                             timeout=15, allow_redirects=True)
            if r.status_code < 400:
                html = r.text
                final = r.url
                https_ok = final.startswith("https")
                status = "ok"
                break
            if r.status_code in (401, 403, 406, 429, 503):
                status = "blocked"   # bot wall, not a dead site
        except Exception:
            continue
    return final, html, https_ok, status


PARKED_SIGNS = ["domain is parked", "buy this domain", "domain for sale",
                "this domain may be for sale", "sedoparking", "hugedomains",
                "parked free, courtesy", "domain expired", "renew now"]


def detect(html):
    """Pull every signal out of the raw HTML. Returns a dict."""
    low = html.lower()
    soup = BeautifulSoup(html, "html.parser")
    out = {}

    # parked / dead-shell page -- nothing below can be trusted as a claim
    visible_text = soup.get_text(" ", strip=True)
    out["parked"] = (any(s in low for s in PARKED_SIGNS)
                     or len(visible_text) < 120)

    # platform
    if "wp-content" in low or "wp-includes" in low or "/wp-json" in low:
        out["platform"] = "WordPress"
    else:
        out["platform"] = "custom/unknown"
        for name, sigs in BUILDERS.items():
            if any(s in low for s in sigs):
                out["platform"] = name
                break

    # wordpress theme
    m = re.search(r"wp-content/themes/([^/'\"?]+)", html, re.I)
    out["theme"] = m.group(1) if m else ""

    # wordpress version (generator meta) -- attribute-order agnostic
    out["wp_version"] = ""
    gen = soup.find("meta", attrs={"name": re.compile(r"^generator$", re.I)})
    if gen:
        m = re.search(r"wordpress\s*([\d.]+)", gen.get("content", ""), re.I)
        if m:
            out["wp_version"] = m.group(1)

    # jquery version -- WordPress's ?ver= style first (most reliable), then filename style
    m = (re.search(r"jquery(?:\.min)?\.js\?ver=(\d+\.\d+(?:\.\d+)?)", low)
         or re.search(r"jquery[._/-]?(\d+\.\d+(?:\.\d+)?)", low))
    out["jquery"] = m.group(1) if m else ""

    # bootstrap version
    m = re.search(r"bootstrap[.\-/]?(\d+\.\d+(?:\.\d+)?)", low)
    out["bootstrap"] = m.group(1) if m else ""

    # mobile viewport
    out["has_viewport"] = bool(soup.find("meta", attrs={"name": "viewport"}))

    # open graph -- via parser, survives unquoted/single-quoted/uppercase attrs
    out["has_og"] = bool(soup.find("meta",
                         attrs={"property": re.compile(r"^og:", re.I)}))

    # copyright year (most recent 4-digit year near a copyright mark)
    years = re.findall(
        r"(?:\u00a9|&copy;|&#169;|\(c\)|copyright)[^\d]{0,15}(20\d{2})", low)
    out["copyright_year"] = max((int(y) for y in years), default=0)

    # chat widget
    out["has_chat"] = any(sig in low for sig in CHAT_SIGNATURES)

    # logo URL — og:image, then a header <img> with 'logo' in src/class/alt,
    # then apple-touch-icon. Returns absolute URL or "".
    logo = ""
    og = soup.find("meta", attrs={"property": re.compile(r"^og:image$", re.I)})
    if og and og.get("content"):
        logo = og["content"].strip()
    if not logo:
        for img in soup.find_all("img", src=True):
            blob = (img.get("src", "") + " " + img.get("alt", "") + " " +
                    " ".join(img.get("class", []))).lower()
            if "logo" in blob:
                logo = img["src"].strip(); break
    if not logo:
        ic = soup.find("link", rel=re.compile(r"apple-touch-icon", re.I))
        if ic and ic.get("href"):
            logo = ic["href"].strip()
    out["logo"] = logo

    return out


def score(sig, https_ok):
    """Tally weakness points (higher = better target) + human reasons."""
    pts = 0
    reasons = []

    if not sig["has_viewport"]:
        pts += 2; reasons.append("no mobile viewport (not mobile-friendly)")
    if sig["jquery"] and sig["jquery"][0] in ("1", "2"):
        pts += 2; reasons.append(f"old jQuery {sig['jquery']} (pre-2016 build)")
    if sig["bootstrap"] and sig["bootstrap"][0] in ("2", "3"):
        pts += 1; reasons.append(f"old Bootstrap {sig['bootstrap']}")
    if not sig["has_og"]:
        pts += 1; reasons.append("no Open Graph tags (older build)")
    if sig["copyright_year"]:
        stale = THIS_YEAR - sig["copyright_year"]
        if stale >= 6:
            pts += 3; reasons.append(f"copyright {sig['copyright_year']} ({stale} yrs stale)")
        elif stale >= 3:
            pts += 2; reasons.append(f"copyright {sig['copyright_year']} ({stale} yrs stale)")
    if sig["wp_version"] and sig["wp_version"][0] in ("3", "4"):
        pts += 1; reasons.append(f"old WordPress {sig['wp_version']}")
    if sig["platform"] in BUILDERS:
        pts += 1; reasons.append(f"cheap builder ({sig['platform']})")
    if not https_ok:
        pts += 2; reasons.append("no working HTTPS (insecure/neglected)")
    if not sig["has_chat"]:
        pts += 1; reasons.append("no live chat / chatbot (your upsell hook)")

    if pts >= 5:
        verdict = "STRONG TARGET"
    elif pts >= 3:
        verdict = "WORTH A LOOK"
    else:
        verdict = "SKIP"
    return pts, verdict, reasons


def analyze(url):
    final, html, https_ok, status = fetch(url)
    if not html:
        if status == "blocked":
            # Bot wall: we could NOT inspect them. Never put claims in outreach.
            return {"url": url, "verdict": "BLOCKED", "score": "",
                    "platform": "", "reasons": "bot wall -- could not check"}
        return {"url": url, "verdict": "UNREACHABLE", "score": "",
                "platform": "", "reasons": "site dead/unreachable (that IS the pitch: "
                "they rank with no working website)"}
    sig = detect(html)
    logo = sig.get("logo", "")
    if logo and not logo.startswith("http"):
        from urllib.parse import urljoin
        logo = urljoin(final, logo)
    if sig["parked"]:
        # Parked/empty shell: 'no viewport / no OG' claims would be embarrassing.
        return {"url": final, "verdict": "PARKED/EMPTY", "score": "",
                "platform": sig["platform"],
                "reasons": "parked or near-empty page -- pitch is 'your website is "
                "gone', not feature gaps"}
    pts, verdict, reasons = score(sig, https_ok)
    return {
        "url": final, "verdict": verdict, "score": pts,
        "platform": sig["platform"],
        "theme": sig["theme"], "jquery": sig["jquery"],
        "copyright": sig["copyright_year"] or "",
        "mobile": "y" if sig["has_viewport"] else "n",
        "chat": "y" if sig["has_chat"] else "n",
        "logo": logo,
        "reasons": "; ".join(reasons),
    }


# ----------------------------- input handling -----------------------------

def load_urls(arg):
    """Return list of (url, meta) pairs. meta carries business name/phone/etc
    from the input CSV through to site_audit.csv so sitegen.py can use it."""
    META_COLS = ("business", "name", "title", "phone", "city", "state",
                 "zip", "rating", "reviews", "address", "category", "claimed")
    if arg and arg.lower().endswith(".csv"):
        pairs = []
        with open(arg, newline="", encoding="utf-8", errors="ignore") as f:
            rdr = csv.DictReader(f)
            col = next((c for c in rdr.fieldnames or []
                        if c and c.lower() in ("website", "url", "domain", "site")), None)
            if not col:
                print(f"No website/url/domain column in {arg}. Columns: {rdr.fieldnames}")
                sys.exit(1)
            for row in rdr:
                v = (row.get(col) or "").strip()
                if v and v.lower() not in ("none", "n/a", ""):
                    meta = {}
                    for c in rdr.fieldnames or []:
                        lc = (c or "").lower()
                        if lc in META_COLS:
                            key = "business" if lc in ("name", "title") else lc
                            meta[key] = (row.get(c) or "").strip()
                    pairs.append((v, meta))
        return pairs
    # else try urls.txt
    try:
        with open("urls.txt", encoding="utf-8") as f:
            return [(ln.strip(), {}) for ln in f if ln.strip()]
    except FileNotFoundError:
        print("No CSV arg and no urls.txt found. Make urls.txt (one website per "
              "line) or pass a CSV.  Or run:  python site_age.py --selftest")
        sys.exit(1)


def run(pairs):
    rows = []
    for i, (u, meta) in enumerate(pairs, 1):
        res = analyze(u)
        res.update(meta)            # business, phone, city, state, rating...
        rows.append(res)
        label = meta.get("business") or res["url"]
        print(f"[{i}/{len(pairs)}] {res['verdict']:<13} "
              f"score={res['score']!s:<3} {label}")
        if res.get("reasons"):
            print(f"        -> {res['reasons']}")
        time.sleep(0.5)   # be polite; also keeps WAFs calmer
    order = {"STRONG TARGET": 0, "WORTH A LOOK": 1, "UNREACHABLE": 2,
             "PARKED/EMPTY": 3, "SKIP": 4, "BLOCKED": 5}
    rows.sort(key=lambda r: (order.get(r["verdict"], 9), -(r["score"] or 0)))
    cols = ["verdict", "score", "business", "phone", "city", "state", "zip",
            "rating", "reviews", "address", "url", "platform", "theme",
            "jquery", "copyright", "mobile", "chat", "logo", "reasons"]
    with open("site_audit.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore",
                           restval="")
        w.writeheader()
        w.writerows(rows)
    strong = sum(1 for r in rows if r["verdict"] == "STRONG TARGET")
    print(f"\nDone. {strong}/{len(rows)} are STRONG TARGETs. -> site_audit.csv")


# ----------------------------- self test -----------------------------

OLD_HTML = """<html><head>
<meta name="generator" content="WordPress 4.9.8">
<link href="/wp-content/themes/twentytwelve/style.css">
<script src="/js/jquery-1.11.3.min.js"></script>
</head><body><footer>&copy; 2015 Joe's Plumbing</footer></body></html>"""

MODERN_HTML = """<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta property="og:title" content="Acme">
<script src="https://cdn.jsdelivr.net/jquery-3.7.1.min.js"></script>
<script src="https://widget.tawk.to/abc"></script>
</head><body><footer>&copy; 2026 Acme Co</footer></body></html>"""


def selftest():
    print("=== self test (no internet) ===\n")
    s1 = detect(OLD_HTML); p1, v1, r1 = score(s1, https_ok=False)
    print(f"OLD site  -> {v1} (score {p1})")
    print(f"  platform={s1['platform']} theme={s1['theme']} "
          f"jquery={s1['jquery']} wp={s1['wp_version']} "
          f"copyright={s1['copyright_year']} mobile={s1['has_viewport']} chat={s1['has_chat']}")
    print(f"  reasons: {'; '.join(r1)}\n")
    s2 = detect(MODERN_HTML); p2, v2, r2 = score(s2, https_ok=True)
    print(f"MODERN site -> {v2} (score {p2})")
    print(f"  platform={s2['platform']} jquery={s2['jquery']} "
          f"copyright={s2['copyright_year']} mobile={s2['has_viewport']} chat={s2['has_chat']}")
    print(f"  reasons: {'; '.join(r2) or '(none)'}\n")

    # regression checks for real-world HTML the old regexes missed
    wp_ver = detect('<script src="/wp-includes/js/jquery/jquery.min.js?ver=1.12.4">'
                    '</script><p>real visible content here, long enough to not look '
                    'parked, describing plumbing services in detail for the test.</p>')
    rev_gen = detect('<meta content="WordPress 4.7" name="generator"><p>real visible '
                     'content here, long enough to not look parked, more words words '
                     'words to pass the emptiness threshold for this unit test.</p>')
    unq_og = detect('<meta property=og:title content=x><p>real visible content here, '
                    'long enough to not look parked, more filler text for threshold '
                    'purposes so the parked detector stays quiet during the test.</p>')
    ent_cr = detect('<footer>&#169; 2014 Acme</footer><p>real visible content here, '
                    'long enough to not look parked, additional sentences of filler '
                    'so this sample passes the minimum visible text threshold.</p>')
    parked = detect('<html><body>This domain is parked free, courtesy of '
                    'GoDaddy.com</body></html>')
    checks = [
        ("WP ?ver= jquery", wp_ver["jquery"] == "1.12.4"),
        ("reversed generator meta", rev_gen["wp_version"] == "4.7"),
        ("unquoted OG tag", unq_og["has_og"]),
        ("&#169; copyright", ent_cr["copyright_year"] == 2014),
        ("parked detection", parked["parked"]),
    ]
    for name, passed in checks:
        print(f"  {'PASS' if passed else 'FAIL'}: {name}")
    ok = (v1 == "STRONG TARGET" and v2 == "SKIP"
          and all(p for _, p in checks))
    print("\nRESULT:", "PASS - detectors work" if ok else "FAIL - check logic")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        selftest()
    else:
        run(load_urls(sys.argv[1] if len(sys.argv) > 1 else None))
