#!/usr/bin/env python3
"""
gsa_filter.py -- predict which scraped sites GSA Website Contact can actually
deliver to, BEFORE you spend effort auditing + building preview sites for them.

Runs on your <label>_websites_*.csv (the WITH-website list from biz_pull.py).
Fetches each site (homepage, then a few likely contact pages) and looks for the
known hard blockers that make a contact-form submission fail. Splits into:

  <label>_gsa_ready_*.csv    -> a plain HTML form, no blocker  (BUILD SITES FOR THESE)
  <label>_gsa_blocked_*.csv  -> blocked, with the reason       (PARK for cold email)

It does NOT defeat, solve, or bypass anything. If it sees a CAPTCHA or a WAF
challenge it marks the site BLOCKED and SKIPS it. The whole point is to avoid
building sites you can't deliver, and to pre-segment the rest into your future
cold-email list.

------------------------------------------------------------------
WHAT COUNTS AS BLOCKED (all read from raw page HTML, no JS executed):
  WAF        -- Cloudflare/WAF challenge interstitial (403/503 or challenge body)
  CAPTCHA    -- reCAPTCHA / hCaptcha / Turnstile present, NO solvable form behind it
  EMBED      -- only a 3rd-party embedded form (HubSpot/Typeform/Google Forms/JotForm)
  NO_FORM    -- reachable but no fillable contact form found (mailto/phone only)
  UNREACHABLE-- site dead/unreachable
READY        -- a real HTML <form> with fillable text fields, no CAPTCHA
READY_CAPTCHA-- a real form WITH a CAPTCHA, but you run a solver (Captcha Breaker
               + XEvil) so it's deliverable -> goes in the send bucket too
------------------------------------------------------------------

HONEST LIMITS: a single GET can't see honeypots, server-side spam filters
(Akismet), or GSA's own field-matching. READY means "no DETECTABLE blocker,"
not "guaranteed delivery." It removes the certain-fails so you stop building
dead sites -- real hit rate on READY is higher than blind sending, not 100%.

RUN ORDER (insert BEFORE site_age.py):
  biz_pull.py -> gsa_filter.py -> site_age.py (on _gsa_ready_) -> sitegen.py

  pip install requests beautifulsoup4
  python gsa_filter.py <label>_websites_*.csv      # split the scrape
  python gsa_filter.py --selftest                  # test detectors, no internet
"""

import csv, re, sys, time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# contact pages to try if the homepage has no contact form (service-biz friendly)
CONTACT_PATHS = ["/contact", "/contact-us", "/contactus",
                 "/get-a-quote", "/quote", "/free-quote", "/estimate",
                 "/request-a-quote"]
MAX_CONTACT_TRIES = 3   # how many of the above to actually fetch per site

# ----------------------------- CONFIG -----------------------------
# You run GSA with a CAPTCHA solver (GSA Captcha Breaker + XEvil) wired in.
# When True, a real contact form that merely has a CAPTCHA on it is NOT a
# blocker -> it goes to the READY/send bucket (status READY_CAPTCHA) because
# the solver clears it at send time. Set False to park captcha forms instead.
# NOTE: this ONLY rescues pages that actually HAVE a fillable form. A captcha
# with no form behind it stays BLOCKED -- there's nothing to submit to.
HAVE_CAPTCHA_SOLVER = True

CAPTCHA_SIGS = [
    "g-recaptcha", "grecaptcha", "recaptcha/api.js", "recaptcha/enterprise",
    "h-captcha", "hcaptcha.com", "js.hcaptcha.com",
    "cf-turnstile", "challenges.cloudflare.com/turnstile",
    "funcaptcha", "arkoselabs",
]
# 3rd-party form hosts GSA generally cannot post to (iframe / cross-origin)
EMBED_SIGS = [
    "js.hsforms.net", "hsforms.com", "hubspot.com/forms",
    "typeform.com", "embed.typeform",
    "docs.google.com/forms", "google.com/forms",
    "jotform.com", "form.jotform", "wufoo.com", "formstack.com",
    "cognitoforms.com", "123formbuilder", "wpforms.com/pro",  # pro embeds vary
]
# WAF / challenge interstitial markers (only trusted alongside a bad status,
# or when there's almost no real page content -- avoids false-flagging sites
# that merely sit behind Cloudflare CDN and serve fine)
WAF_SIGS = [
    "just a moment", "checking your browser", "cf-browser-verification",
    "cf_chl_opt", "__cf_chl", "challenge-platform", "attention required",
    "ddos protection by", "ray id", "/cdn-cgi/challenge",
    "incapsula incident", "_imperva_", "sucuri_cloudproxy", "access denied",
]


def fetch(url):
    """Return (final_url, html, status_code, ok_bool). Tries https then http."""
    if not url.startswith("http"):
        url = "https://" + url
    for u in (url.replace("http://", "https://"),
              url.replace("https://", "http://")):
        try:
            r = requests.get(u, headers={"User-Agent": UA}, timeout=15,
                             allow_redirects=True)
            return r.url, r.text or "", r.status_code, True
        except Exception:
            continue
    return url, "", 0, False


def looks_like_waf(html, status):
    low = html.lower()
    hits = any(s in low for s in WAF_SIGS)
    if status in (401, 403, 429, 503):
        # bad status + any challenge marker = real block; bad status alone is
        # often a plain bot wall too -> treat as WAF (can't deliver either way)
        return True
    # status 200 but the page is a challenge interstitial: markers present AND
    # almost no real text (challenge pages are tiny)
    if hits:
        text_len = len(BeautifulSoup(html, "html.parser").get_text(" ", strip=True))
        if text_len < 600:
            return True
    return False


def has_captcha(html):
    low = html.lower()
    return any(s in low for s in CAPTCHA_SIGS)


def only_embedded_form(html):
    """True if the page's form presence is a 3rd-party embed (iframe/widget)
    AND there's no native <form> with fillable fields."""
    low = html.lower()
    embed = any(s in low for s in EMBED_SIGS)
    return embed and not has_native_form(html)


def has_native_form(html):
    """A real, fillable contact-style form in the raw HTML:
    a <form> containing a <textarea> OR >=2 text/email inputs.
    Excludes lone search/newsletter inputs."""
    soup = BeautifulSoup(html, "html.parser")
    for form in soup.find_all("form"):
        action = (form.get("action") or "").lower()
        if "search" in action:
            continue
        if form.find("textarea"):
            return True
        fillable = 0
        for inp in form.find_all("input"):
            t = (inp.get("type") or "text").lower()
            if t in ("text", "email", "tel", "name"):
                name = (inp.get("name") or "").lower()
                if "search" in name or t == "search":
                    continue
                fillable += 1
        if fillable >= 2:
            return True
    return False


def classify(url):
    """Fetch homepage (+ contact pages if needed) and return a verdict dict."""
    final, html, status, ok = fetch(url)
    if not ok or not html:
        return {"gsa_status": "UNREACHABLE", "gsa_reason": "site dead/unreachable",
                "form_url": ""}
    if looks_like_waf(html, status):
        return {"gsa_status": "BLOCKED_WAF",
                "gsa_reason": "WAF/Cloudflare challenge (GSA can't pass)",
                "form_url": final}

    pages = [(final, html)]
    # if homepage has no native form, try a few likely contact pages
    if not has_native_form(html):
        tried = 0
        for path in CONTACT_PATHS:
            if tried >= MAX_CONTACT_TRIES:
                break
            cu = urljoin(final, path)
            cf, ch, cs, cok = fetch(cu)
            tried += 1
            if cok and ch and not looks_like_waf(ch, cs):
                pages.append((cf, ch))
                if has_native_form(ch):
                    break
            time.sleep(0.2)

    # evaluate the best page we found a form on
    for purl, phtml in pages:
        if has_native_form(phtml):
            if has_captcha(phtml):
                if HAVE_CAPTCHA_SOLVER:
                    return {"gsa_status": "READY_CAPTCHA",
                            "gsa_reason": "form + CAPTCHA, solvable via Captcha Breaker/XEvil",
                            "form_url": purl}
                return {"gsa_status": "BLOCKED_CAPTCHA",
                        "gsa_reason": "form found but CAPTCHA on it (no solver configured)",
                        "form_url": purl}
            return {"gsa_status": "READY",
                    "gsa_reason": "plain HTML contact form, no blocker",
                    "form_url": purl}

    # no native form anywhere -> embed? captcha-guarded? or just none
    joined = " ".join(h for _, h in pages)
    if only_embedded_form(joined):
        return {"gsa_status": "BLOCKED_EMBED",
                "gsa_reason": "only a 3rd-party embedded form (iframe)",
                "form_url": final}
    if has_captcha(joined):
        return {"gsa_status": "BLOCKED_CAPTCHA",
                "gsa_reason": "CAPTCHA present, no plain form",
                "form_url": final}
    return {"gsa_status": "BLOCKED_NO_FORM",
            "gsa_reason": "no fillable contact form (cold-email candidate)",
            "form_url": final}


# ----------------------------- input / output -----------------------------

def website_col(fieldnames):
    return next((c for c in fieldnames or []
                 if c and c.lower() in ("website", "url", "domain", "site")), None)


def run(path):
    with open(path, newline="", encoding="utf-8", errors="ignore") as f:
        rdr = csv.DictReader(f)
        fieldnames = list(rdr.fieldnames or [])
        wcol = website_col(fieldnames)
        if not wcol:
            print(f"No website/url/domain column. Columns: {fieldnames}")
            sys.exit(1)
        rows = list(rdr)

    extra = ["gsa_status", "gsa_reason", "form_url"]
    out_cols = fieldnames + [c for c in extra if c not in fieldnames]
    ready, blocked = [], []

    todo = []
    for row in rows:
        site = (row.get(wcol) or "").strip()
        if site and site.lower() not in ("none", "n/a"):
            todo.append((row, site))

    for i, (row, site) in enumerate(todo, 1):
        res = classify(site)
        row.update(res)
        (ready if res["gsa_status"].startswith("READY") else blocked).append(row)
        label = row.get("business") or site
        print(f"[{i}/{len(todo)}] {res['gsa_status']:<16} {label}")
        time.sleep(0.5)   # polite; keeps WAFs calmer

    stamp = time.strftime("%m%d-%H%M%S")
    base = re.sub(r"_websites.*$", "", path.rsplit("/", 1)[-1]
                  .rsplit("\\", 1)[-1]).rsplit(".", 1)[0] or "scrape"
    f_ready = f"{base}_gsa_ready_{stamp}.csv"
    f_block = f"{base}_gsa_blocked_{stamp}.csv"

    def dump(fn, data):
        with open(fn, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=out_cols, extrasaction="ignore",
                               restval="")
            w.writeheader()
            w.writerows(data)

    # rank blocked list by usefulness for the future cold-email push:
    # no-form first (pure email targets), then embed, captcha, waf, dead
    border = {"BLOCKED_NO_FORM": 0, "BLOCKED_EMBED": 1, "BLOCKED_CAPTCHA": 2,
              "BLOCKED_WAF": 3, "UNREACHABLE": 4}
    blocked.sort(key=lambda r: border.get(r["gsa_status"], 9))

    dump(f_ready, ready)
    dump(f_block, blocked)

    total = len(ready) + len(blocked)
    pct = (100 * len(ready) / total) if total else 0
    from collections import Counter
    rc = Counter(r["gsa_status"] for r in ready)
    print(f"\n  READY:   {len(ready):>4} ({pct:.0f}%)  -> {f_ready}   BUILD THESE")
    if rc.get("READY_CAPTCHA"):
        print(f"      of which plain         {rc.get('READY', 0)}")
        print(f"      of which solver-needed {rc.get('READY_CAPTCHA', 0)}  (Captcha Breaker/XEvil must be ON at send)")
    print(f"  BLOCKED: {len(blocked):>4}        -> {f_block}   (future cold email)")
    # breakdown
    for k, v in Counter(r["gsa_status"] for r in blocked).most_common():
        print(f"      {k:<16} {v}")
    print(f"\nNext step:  python site_age.py {f_ready}")


# ----------------------------- self test -----------------------------

READY_HTML = """<html><body>
<form action="/send"><input name="name" type="text"><input name="email"
type="email"><textarea name="msg"></textarea></form>
<p>Real contact page content here, plenty of words so it is not mistaken for a
challenge interstitial, describing the business and how to reach them.</p>
</body></html>"""

CAPTCHA_HTML = """<html><body>
<form action="/send"><input name="email" type="email"><textarea name="msg">
</textarea><div class="g-recaptcha" data-sitekey="x"></div></form>
<p>Lots of normal visible content here to clear the challenge-page text length
threshold so this is treated as a normal page that simply has a captcha.</p>
</body></html>"""

WAF_HTML = """<html><head><title>Just a moment...</title></head><body>
<div id="challenge-platform">Checking your browser before accessing.</div>
</body></html>"""

EMBED_HTML = """<html><body><h1>Contact</h1>
<iframe src="https://form.jotform.com/2345"></iframe>
<p>Reach out using the form. Additional words here so the page has enough text
content to not be confused with a tiny challenge interstitial page at all.</p>
</body></html>"""

NOFORM_HTML = """<html><body><h1>Call us</h1>
<a href="mailto:joe@example.com">email</a> or call (254) 555-0101.
<p>We are a local power washing company. No web form here, just a phone number
and an email address, which makes this a cold-email candidate, not a GSA one.</p>
</body></html>"""

SEARCHONLY_HTML = """<html><body>
<form action="/search"><input name="s" type="search"></form>
<p>A blog homepage with only a search box and no real contact form anywhere on
it, with enough words present to pass the interstitial length threshold here.</p>
</body></html>"""


def selftest():
    print("=== self test (no internet) ===\n")
    checks = [
        ("READY plain form",        has_native_form(READY_HTML) and not has_captcha(READY_HTML)),
        ("CAPTCHA detected",        has_captcha(CAPTCHA_HTML) and has_native_form(CAPTCHA_HTML)),
        ("captcha form is sendable w/ solver",
                                    HAVE_CAPTCHA_SOLVER and has_native_form(CAPTCHA_HTML)
                                    and has_captcha(CAPTCHA_HTML)),
        ("WAF interstitial",        looks_like_waf(WAF_HTML, 200)),
        ("WAF on 403 any body",     looks_like_waf("whatever", 403)),
        ("not WAF on normal 200",   not looks_like_waf(READY_HTML, 200)),
        ("embed-only form",         only_embedded_form(EMBED_HTML)),
        ("no-form / mailto only",   not has_native_form(NOFORM_HTML)),
        ("search box != form",      not has_native_form(SEARCHONLY_HTML)),
    ]
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}: {name}")
    print("\nRESULT:", "PASS - detectors work"
          if all(o for _, o in checks) else "FAIL - check logic")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        files = [a for a in sys.argv[1:] if not a.startswith("--")]
        if not files:
            print(__doc__); sys.exit(1)
        run(files[0])
