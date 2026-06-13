# GSA Website Contact — Technical Reference (All-In-One)

> **Status: AUTHORITATIVE. Verified against official GSA documentation, June 2026.**
> This file supersedes any earlier "Bible" or agent notes that claimed custom
> per-URL personalization is impossible. **It is possible. It is the documented,
> intended feature.** If another doc contradicts this one, this one wins until
> a newer verification replaces it.
>
> Every claim below is tagged:
> - ✅ **CONFIRMED** — stated in official GSA docs/product page (sourced at bottom).
> - ⚠️ **VERIFY-ON-USE** — almost certainly true, but confirm with a 10-minute live test the first time.

---

## 0. The One-Sentence Answer

**GSA Website Contact lets you import a CSV where every row is a target URL plus
as many custom columns as you want, and you reference each column in your message
body as `%ColumnName%`. Each form submission is rendered with that row's own data.**
That means fully personalized, per-business messages — exactly the original plan.

The earlier claim that "you can only use one placeholder" was **wrong**.
The claim that "you can make up your own columns" was **right**.

---

## 1. What GSA Website Contact Is

A Windows desktop app that automatically finds the contact form on a website and
submits a message through it. You give it a list of target sites and a message
template; it fills and submits each site's contact form. It is the contact-form
equivalent of cold email, except it posts through the site's own "Contact Us" form.

- Product page: https://www.gsa-online.de/product/web_contact/
- It is a separate product from **GSA Search Engine Ranker (SER)**, but the two
  **share the same macro/spin engine**, so SER's macro guide applies here too.

---

## 2. The Two Ways To Load Targets (this is what caused the confusion)

There are **two different import paths**, and the earlier agent documented only
the first one and wrongly assumed it was the only one.

| Method | What you import | Custom per-URL data? | Use it? |
|--------|-----------------|----------------------|---------|
| **Plain URL list (TXT)** | One URL per line, nothing else | ❌ No | No — too generic |
| **CSV import** | URL **+ any custom columns** | ✅ **Yes** | ✅ **This is the one we use** |

**We use CSV import.** It is the documented path for custom data. ✅ CONFIRMED.

---

## 3. The CSV Format (exact, copy this)

✅ CONFIRMED — this is the literal example from the official docs:

```
"FirstName","LastName","Website","Rating"
"John","Doe","www.gsa-online.de","8"
"Jean","Doe","www.proxy-scraper.de","9"
```

Rules:

1. **Every value AND every header is wrapped in double quotes**, comma-separated.
   ✅ CONFIRMED. If you save a plain CSV from Excel without quotes, **GSA will not
   recognize the data.** This is the single most common failure. Force-quote everything.
2. **The header row names your columns.** Headers do **NOT** include `%` signs —
   you add the `%` only when you reference them in the message. ✅ CONFIRMED.
3. **One column holds the target URL** (named `Website` in the official example).
   Name it clearly: `Website` or `URL`. ⚠️ VERIFY-ON-USE that GSA picks the right
   column as the URL on import (it recognizes it during the import step).
4. **Column names are yours to invent.** `FirstName`, `Rating`, `missing_citations`,
   `competitor_1`, `preview_url` — whatever you want. ✅ CONFIRMED.
5. UTF-8, one row per target.

> **Excel gotcha:** Excel's default "Save as CSV" does NOT quote values. Either
> build the CSV in code (Python `csv` writer with `quoting=csv.QUOTE_ALL`) or use
> the known Excel macro that force-quotes. Our pipeline scripts should write with
> `QUOTE_ALL` so this is handled automatically.

---

## 4. The Macro Syntax (the thing everyone was arguing about)

✅ CONFIRMED — official docs, verbatim intent:

> "you can use macros like `%FirstName%`, `%LastName%`, `%Website%` and `%Rating%`"
> "Note that the CSV headers should NOT have the % around the headers, just use
> them for the macros."

**Rule: a CSV column named `Foo` becomes the macro `%Foo%` in your message.**
Case should match the header. Each row substitutes its own value.

So if your CSV is:

```
"Website","business_name","missing_citation","preview_url","review_count"
"www.joesplumbing.com","Joe's Plumbing","Yelp + BBB","https://previews.pages.dev/joes-plumbing","12"
```

Your message body can be:

```
Hi %business_name% team — noticed you're not listed on %missing_citation%,
which is where a lot of your %review_count%-review competitors are getting found.
I built a free preview of a faster site for you: %preview_url%
```

Each submission renders with that row's values. ✅ This is the whole plan, confirmed working.

### 4a. Built-in macros (always available, no CSV needed)

✅ CONFIRMED from the macro guide / product docs:

| Macro | Meaning |
|-------|---------|
| `%url%` | The **target site's own URL** (the site being submitted to) |
| `%domain%` | Domain of the target site |
| `%url_domain%` | Domain of the URL you submit (e.g. `gsa-online.de`) |
| `%url_path%` | Path portion of the target URL |
| `%subdomain%`, `%host%` | Parts of the target URL |
| `%title%` | The target page's title |
| `%keyword%`, `%keyword1%`… | Random / indexed keyword from the project |
| `%facebook%`, `%twitter%`, `%instagram%` | Social links found on the target |

> **Critical distinction:** `%url%` / `%domain%` describe the **site you're
> contacting** (their site). Your **custom columns** (`%preview_url%`,
> `%business_name%`) are **your imported data**. They are different things.
> The preview-site link you want to send is a **custom column**, e.g. `%preview_url%` —
> it is NOT `%url%`.

### 4b. File-based macros (advanced, for spinning shared content)

✅ CONFIRMED from the macro guide. These read from files on disk, not the CSV:

- `%spinfile-<file>%` — random line from a file, reused consistently within one submission.
- `%spinfile2-<file>%` — random line, fresh pick each call.
- `%file-<file>%` / `#file[<file>]` — dump an entire file's contents.
- `%columnspinfile-<file>-<column>%` — pick a random line, take column N (comma-separated).
  Using the same file with a different column keeps the **same row** (so name +
  address stay matched). Example: `%columnspinfile-address_data.dat-1% - %columnspinfile-address_data.dat-3%`.
- `%spinfolder-<folder>%`, `%spinfilename-<folder>%`, etc. — folder-based variants.

These are for **shared** rotating content (e.g. a pool of intro lines), not for
per-URL data. For per-URL personalization, use **CSV columns** (Section 4).

### 4c. Spin syntax

✅ CONFIRMED. Standard nested spin works: `{Hi|Hey|Hello} %business_name%`.
Combine spin + macros freely to make every message unique and reduce spam-filter
fingerprinting. The product page explicitly markets "macros and spin syntax… to
create more personal and unique messages."

---

## 5. Hard Limitations (what we genuinely CANNOT do)

✅ CONFIRMED from the official FAQ — quote: *"Contact-Forms are not designed to
hold fancy HTML code, hyperlinks or images. All you can add in a contact form is
plain, simple text."*

Therefore:

1. **Plain text only.** No HTML, no clickable anchor tags, no images, no styling.
2. **Links go in as raw text.** `%preview_url%` renders as `https://previews.pages.dev/joes-plumbing`
   — a bare URL the recipient can copy/click in most inboxes/CRMs, but **not** a
   styled "Click here" hyperlink. **This is fine for our plan** — the link still
   lands; it just isn't dressed up. Make the URL short and clean so it reads well as text.
3. **After import you will NOT see the custom columns as columns in the GSA site
   list.** ✅ CONFIRMED. The data is attached to each URL and shows on **mouse-over
   hover**. This is normal and expected — it is **not** a bug and **not** a sign
   the import failed. Verify by hovering a URL after import.
4. **No rich tracking inside the form text.** If you need click tracking, bake it
   into the URL itself (e.g. a unique slug per business, which we already generate),
   not into HTML.
5. GSA must actually **find and post** to a real form. Sites with no native form,
   3rd-party embeds (HubSpot/Typeform/JotForm iframes), or hard WAF/CAPTCHA walls
   may fail — which is exactly what `gsa_filter.py` pre-screens for.

---

## 6. CAPTCHA / Deliverability

- GSA integrates with **GSA Captcha Breaker** + **XEvil** to solve CAPTCHAs at
  submit time. Our pipeline assumes the solver is ON (`HAVE_CAPTCHA_SOLVER = True`
  in `gsa_filter.py`), so a form that merely has a CAPTCHA is still a send target.
- A CAPTCHA with **no fillable form behind it** is unsendable — there's nothing to submit.
- WAF/Cloudflare challenge pages, dead sites, and embed-only forms are **blocked**
  and routed to the cold-email bucket by `gsa_filter.py`.
- "READY" from our filter means "no *detectable* blocker," not "guaranteed delivery."
  Real-world hit rate on READY is higher than blind sending, not 100%.

---

## 7. How This Plugs Into Our Pipeline

Our existing scraper pipeline (see `README_RUN_ORDER.md`) already produces the
right shape of data. GSA Website Contact is the **final send stage**.

```
biz_pull.py        → find businesses (DataForSEO) → *_websites.csv (+ *_coldcall.csv)
gsa_filter.py      → keep only sites GSA can deliver to → *_gsa_ready.csv
site_age.py        → score weak sites + pull logo + generate audit "reasons"
sitegen.py         → build a preview site per business (Claude copy)
                     deploy to Cloudflare Pages → site_audit_with_previews.csv
─────────────────────────────────────────────────────────────────────────────
GSA Website Contact ← import site_audit_with_previews.csv
                     message template uses %business%, %preview_url%, %reasons%, etc.
                     → submits a personalized message through each site's form
```

**The CSV we feed GSA must:**
- Contain a clear **URL column** (the target business's site — what GSA submits to).
- Contain every personalization column the message references, with **matching
  header names** (`business`, `preview_url`, `missing_citation`, `review_count`,
  `reasons`, `competitor_1`…).
- Be written with **all values quoted** (`csv.QUOTE_ALL`).
- Keep the **preview URL** as a clean, short, per-business slug so it reads well
  as plain text.

> Note on column matching: our scraper currently emits a `website` column for the
> business's own site and a `preview_url` column for the site we built. In GSA,
> the business's own site (`website`) is the **target URL**; `%preview_url%` is the
> **custom column** you put in the message. Don't confuse the two.

---

## 8. First-Run Verification Checklist (do this once, ~10 min)

⚠️ VERIFY-ON-USE — settle the last small unknowns with one live test before a big run:

1. Make a 3-row test CSV: columns `Website,business_name,missing_citation`, all
   values quoted. Set each `Website` to a free **webhook.site** URL (so you can see
   exactly what gets submitted).
2. Message body: `Hey %business_name%, you are missing %missing_citation%`.
3. Import into GSA, confirm on **mouse-over** that each URL shows its CSV data.
4. Run it; check webhook.site received three **different** rendered messages with
   the right per-row values.
5. Confirm GSA used your intended column as the **target URL** (not a data column).

Once green, the syntax is locked and you can scale. Save the result back into this
doc's changelog if anything differed from the above.

---

## 9. Sources (verified June 2026)

- GSA Website Contact — Running Projects (CSV import + macros, exact format & syntax):
  https://docu.gsa-online.de/website_contact/running_projects
- GSA Website Contact — FAQ (plain-text limit, mouse-over data, no HTML/links/images):
  https://docu.gsa-online.de/website_contact/frequently_asked_questions
- GSA Macro Guide (full macro list, spinfile/columnspinfile, url macros):
  https://docu.gsa-online.de/search_engine_ranker/macro_guide
- GSA Website Contact — Product page (custom data, macros + spin marketing copy):
  https://www.gsa-online.de/product/web_contact/
- GSA Forum — Importing URLs from CSV (must-quote-values, columns hidden but on hover):
  https://forum.gsa-online.de/discussion/30328/importing-urls-from-csv

---

## Changelog
- 2026-06-13 — Created. Resolved the "one placeholder vs custom columns" dispute:
  custom CSV columns → `%ColumnName%` macros are **confirmed**. Original
  personalization plan is valid.
