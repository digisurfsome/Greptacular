#!/usr/bin/env python3
"""
biz_pull.py -- bulk-pull businesses in a category + area from DataForSEO
Business Listings, and split into TWO lists:

  1) <slug>_websites.csv   -> businesses WITH a website  (feed to site_age.py)
  2) <slug>_coldcall.csv   -> businesses WITHOUT a website (cold-call list)

COST (verified June 2026): $0.01 per request + $0.0003 per row.
  1,000 businesses = $0.31      500 = $0.16
One request returns up to 1,000 rows. The script prints the API-reported
cost after the call so you always know exactly what you spent.

SETUP:
  pip install requests
  set DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD env vars (or edit fallbacks below)

RUN:
  python biz_pull.py                  # pull using CONFIG below
  python biz_pull.py --findcat plumb  # look up valid category ids ("plumb...")
  python biz_pull.py --selftest       # test the splitter logic, no internet

NOTES:
  - location_name is silently IGNORED by this endpoint. Coordinates only.
  - Radius is in KILOMETERS. 40 km ~= 25 miles. Overshooting is fine --
    you still get max 1,000 rows, sorted by relevance to the center point.
  - Category ids are Google's internal ones ("plumber", "hvac_contractor"...).
    Not sure of an id? Run --findcat first. Up to 10 categories per pull.
"""

import base64, csv, json, os, re, sys, time
import requests

# ============================================================ CONFIG
DATAFORSEO_LOGIN    = os.environ.get("DATAFORSEO_LOGIN",    "PUT_LOGIN_HERE")
DATAFORSEO_PASSWORD = os.environ.get("DATAFORSEO_PASSWORD", "PUT_PASSWORD_HERE")

CATEGORIES = ["plumber"]              # up to 10 ids; verify with --findcat
LABEL      = "plumber-temple"         # used in output filenames
COORD      = "31.0982,-97.3428,40"    # lat,lng,radius_km   (40 km ~= 25 mi)
LIMIT      = 1000                     # max rows (1-1000). 1000 = $0.31
COUNTRY    = "US"                     # keeps foreign junk rows out
# ============================================================

API = "https://api.dataforseo.com/v3/business_data/business_listings"


def _post(endpoint, payload):
    tok = base64.b64encode(
        f"{DATAFORSEO_LOGIN}:{DATAFORSEO_PASSWORD}".encode()).decode()
    r = requests.post(f"{API}/{endpoint}",
                      headers={"Authorization": f"Basic {tok}",
                               "Content-Type": "application/json"},
                      data=json.dumps(payload), timeout=90)
    r.raise_for_status()
    return r.json()


def xl_text(v):  # stop Excel mangling phone numbers
    return f'="{v}"' if v else ""


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# ------------------------------------------------ category lookup helper
def _get(endpoint):
    tok = base64.b64encode(
        f"{DATAFORSEO_LOGIN}:{DATAFORSEO_PASSWORD}".encode()).decode()
    r = requests.get(f"{API}/{endpoint}",
                     headers={"Authorization": f"Basic {tok}"}, timeout=90)
    r.raise_for_status()
    return r.json()


def find_categories(keyword):
    # NOTE: this endpoint is GET, not POST (POSTing returns 404)
    data = _get("categories")
    try:
        result = data["tasks"][0]["result"] or []
    except Exception:
        print("Could not read categories response."); return
    # result may be a flat list of strings, a list of dicts, or nested items
    items = []
    for r in result:
        if isinstance(r, str):
            items.append(r)
        elif isinstance(r, dict):
            if isinstance(r.get("items"), list):
                items.extend(r["items"])
            else:
                items.append(r)
    names = []
    for it in items:
        if isinstance(it, str):
            names.append(it)
        elif isinstance(it, dict):
            names.append(it.get("category") or it.get("category_name")
                         or it.get("category_id") or "")
    kw = keyword.lower()
    hits = [n for n in names if n and kw in n.lower()]
    if not hits:
        print(f"No category ids containing '{keyword}'.")
    else:
        print(f"Category ids matching '{keyword}':")
        for h in sorted(set(hits)):
            print(f"  {h}")


# ------------------------------------------------ main pull
def pull():
    payload = [{
        "categories": CATEGORIES,
        "location_coordinate": COORD,
        "filters": [["address_info.country_code", "=", COUNTRY]],
        "limit": LIMIT,
    }]
    est = 0.01 + 0.0003 * LIMIT
    print(f"Pulling up to {LIMIT} businesses | categories={CATEGORIES} "
          f"| coord={COORD}\nEstimated max cost: ${est:.2f}")
    data = _post("search/live", payload)
    task = data["tasks"][0]
    if task.get("status_code") != 20000:
        print(f"API error: {task.get('status_code')} {task.get('status_message')}")
        sys.exit(1)
    cost = data.get("cost") or task.get("cost") or 0
    res = (task.get("result") or [{}])[0] or {}
    items = res.get("items") or []
    total_in_area = res.get("total_count")
    print(f"Got {len(items)} rows (database shows {total_in_area} total in "
          f"this area) | actual cost: ${cost:.4f}")
    return items


def split_rows(items):
    """Dedupe, then split into (with_website, without_website) row dicts."""
    seen = set()
    with_site, no_site = [], []
    for it in items:
        title = (it.get("title") or "").strip()
        if not title:
            continue
        phone = (it.get("phone") or "").strip()
        domain = (it.get("domain") or "").strip().lower()
        url = (it.get("url") or "").strip()
        # dedupe on domain first, else phone, else name
        key = domain or re.sub(r"\D", "", phone) or title.lower()
        if key in seen:
            continue
        seen.add(key)
        addr = it.get("address_info") or {}
        rating = it.get("rating") or {}
        base = {
            "business": title,
            "phone": phone,
            "category": it.get("category") or "",
            "rating": rating.get("value", ""),
            "reviews": rating.get("votes_count", ""),
            "claimed": "y" if it.get("is_claimed") else "n",
            "address": addr.get("address") or it.get("address") or "",
            "city": addr.get("city") or "",
            "state": addr.get("region") or "",
            "zip": addr.get("zip") or "",
        }
        if domain:
            with_site.append({**base, "website": url or f"https://{domain}",
                              "domain": domain})
        else:
            no_site.append(base)
    return with_site, no_site


def write_outputs(with_site, no_site):
    stamp = time.strftime("%m%d-%H%M%S")
    slug = slugify(LABEL)

    f1 = f"{slug}_websites_{stamp}.csv"
    cols1 = ["business", "website", "domain", "phone", "category", "rating",
             "reviews", "claimed", "address", "city", "state", "zip"]
    with open(f1, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols1, restval="")
        w.writeheader()
        for r in with_site:
            r = dict(r); r["phone"] = xl_text(r["phone"])
            w.writerow({k: r.get(k, "") for k in cols1})

    f2 = f"{slug}_coldcall_{stamp}.csv"
    cols2 = ["business", "phone", "category", "rating", "reviews", "claimed",
             "address", "city", "state", "zip"]
    # least-established first: unclaimed + few reviews = most reachable pitch
    no_site.sort(key=lambda r: (r["claimed"], r["reviews"] or 0))
    with open(f2, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols2, restval="")
        w.writeheader()
        for r in no_site:
            r = dict(r); r["phone"] = xl_text(r["phone"])
            w.writerow({k: r.get(k, "") for k in cols2})

    print(f"\n  WITH website: {len(with_site):>4}  -> {f1}")
    print(f"  NO website:   {len(no_site):>4}  -> {f2}   (cold-call list)")
    print(f"\nNext step:  python site_age.py {f1}")


# ------------------------------------------------ self test
MOCK = [
    {"title": "Old Pipes Plumbing", "phone": "(254) 555-0101",
     "domain": "oldpipes.com", "url": "http://oldpipes.com",
     "category": "Plumber", "rating": {"value": 4.1, "votes_count": 9},
     "is_claimed": True,
     "address_info": {"address": "1 Main St", "city": "Temple", "zip": "76501"}},
    {"title": "No Site Plumbing Co", "phone": "(254) 555-0102", "domain": "",
     "category": "Plumber", "rating": {"value": 5.0, "votes_count": 2},
     "is_claimed": False,
     "address_info": {"address": "2 Oak St", "city": "Temple", "zip": "76501"}},
    {"title": "Old Pipes Plumbing", "phone": "(254) 555-0101",   # duplicate
     "domain": "oldpipes.com", "url": "http://oldpipes.com",
     "category": "Plumber", "rating": {"value": 4.1, "votes_count": 9},
     "is_claimed": True, "address_info": {}},
    {"title": "", "phone": "x", "domain": ""},                    # junk row
]


def selftest():
    ws, ns = split_rows(MOCK)
    ok = (len(ws) == 1 and len(ns) == 1
          and ws[0]["website"] == "http://oldpipes.com"
          and ns[0]["business"] == "No Site Plumbing Co")
    print(f"with_site={len(ws)} no_site={len(ns)} "
          f"(expected 1 and 1, dupe+junk dropped)")
    print("RESULT:", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    elif "--findcat" in sys.argv:
        i = sys.argv.index("--findcat")
        if i + 1 >= len(sys.argv):
            print("Usage: python biz_pull.py --findcat <keyword>"); sys.exit(1)
        find_categories(sys.argv[i + 1])
    else:
        if "PUT_LOGIN_HERE" in DATAFORSEO_LOGIN:
            print("Set DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD env vars "
                  "(or edit the fallbacks at the top of this file).")
            sys.exit(1)
        items = pull()
        ws, ns = split_rows(items)
        write_outputs(ws, ns)
