# GSA Website Contact — Scale Setup & Send Checklist (WORKING DOC)

> **Status: DRAFT / GROWING.** The personalization engine is PROVEN (see
> `gsa-website-contact-technical-reference.md`). This doc covers the **operational
> setup still required to send at scale** — proxies, captcha solving, threads, and
> the run checklist. Expect to add to it as we configure each piece.
>
> Companion docs:
> - Technical reference (macros, CSV, proven test): `docs/info/gsa-website-contact-technical-reference.md`
> - Plain-English playbook: `docs/info/gsa-website-contact-playbook-plain-english.md`

---

## 0. Where We Are vs Where We Need To Be

| Piece | Status | Notes |
|-------|--------|-------|
| CSV import + `%column%` personalization | ✅ **PROVEN** (v6.25, 2026-06-13) | One real send landed, fully merged |
| Knowing how to drive GSA (import / message / send) | ✅ Done | See checklist §5 |
| **Proxies (≈1000)** | ❌ **Not set up** | Must **purchase** + configure before scale |
| **Captcha Breaker (desktop, owned)** | ⚠️ Owned, **not wired in** | In owner's files; enable in Captchas tab |
| **Captcha — cloud backup** | ❌ **Not purchased** | Need to buy + add as fallback solver |
| **Thread / timing settings** | ❌ Not configured | Target ≈ **20 threads** w/ 1000 proxies |
| Pipeline CSV writes GSA-ready (quoted, matching headers) | ⏳ TODO | Make scraper output drop straight in |

**The test worked with ZERO settings** because the test target had no captcha and
needed no proxy. **Real targets will have captchas and will block repeat IPs**, so
the items marked ❌/⚠️ above are mandatory before a real batch.

---

## 1. Proxies (≈1000) — REQUIRED before scale

**Why:** Sending hundreds/thousands of form submissions from one IP gets that IP
blocked fast. Proxies spread the sends across many IPs so you stay under the radar
and don't burn your real IP.

**Plan (owner's stated intent):**
- **≈1000 proxies**, paired with **≈20 send threads** (plenty of IP headroom — each
  thread rotates through many IPs).

**TODO — purchase:**
- [ ] Buy ≈1000 proxies. Provider TBD. Prefer **private/semi-dedicated HTTP(S)
      proxies** (rotating residential also works but costs more). Confirm format
      (`ip:port` or `ip:port:user:pass`).

**Where they go in GSA (two separate spots):**
- **Sending:** *Submission Content* tab → **"Use proxies for sending"** checkbox →
  **Configure** → paste/import the proxy list. (This is the one that matters for
  delivery.)
- **Search scraping (optional):** *Scraping* tab → **"Use proxies for search
  engines"**. Only needed if you let GSA scrape its own targets. Our pipeline feeds
  GSA pre-built URLs, so this is **off** for our workflow.
- Global proxy management/testing usually also lives under the **Options** toolbar
  button. (Confirm exact path when we wire it up.)

**To verify when set up:**
- [ ] Import proxies, run GSA's proxy **test**, confirm a healthy count pass.
- [ ] Confirm sending uses them (not your home IP).

---

## 2. Captcha Solving — REQUIRED before scale

Many real contact forms have a CAPTCHA. No solver = those sends fail. We use a
**two-layer** setup:

**Layer 1 — GSA Captcha Breaker (PRIMARY, already owned):**
- Desktop app, runs locally, solves most common image/text captchas for ~free per solve.
- Lives in the **owner's files** (installed locally). 
- Wire-in: *Captchas* tab in GSA Website Contact → enable **GSA Captcha Breaker**
  (GSA auto-detects it when CB is running). Start CB before a batch.
- [ ] TODO: locate CB install, launch it, enable it in the Captchas tab, test a solve.

**Layer 2 — Cloud captcha service (BACKUP, to purchase):**
- For captchas CB can't crack (reCAPTCHA v2/v3, hCaptcha, Turnstile), a cloud
  service solves them via human/AI farm at a small per-solve cost.
- **TODO — purchase:** [ ] Buy a cloud captcha plan. Product TBD — confirm which one
  (common options: 2Captcha, CapMonster Cloud, Death By Captcha, XEvil-on-server).
  *(Owner said "the other one's a cloud version I need to purchase" — confirm exact name.)*
- Wire-in: *Captchas* tab → add the cloud service as a **second/fallback** solver
  (GSA tries CB first, falls back to cloud). Enter the API key.
- [ ] TODO: add cloud service + key, set order (CB first → cloud fallback), test.

> **Note:** Even with both solvers, some forms stay unsolvable (hard WAF, embed-only
> forms). Our `gsa_filter.py` already pre-screens those out, so they never reach GSA.

---

## 3. Threads & Timing — configure before scale

**Owner's target:** **≈20 threads** with the 1000-proxy pool.

- **Threads** (how many forms GSA works at once): set in **Options** (global toolbar)
  → submission/HTML threads. Start at **20**. More threads = faster, but needs more
  proxies + more captcha throughput, and raises footprint. 20 is a sane, safe start.
- **Seconds between download and submission** (*Submission Content* tab, bottom):
  was `0` for the test. For real sends, a small delay/random spread looks more human.
  - [ ] TODO: decide a value (e.g. a few seconds + random) when we tune.
- **Filter Out Comment Forms** (on by default) — keep on; we want real contact forms.
- **Detect Hidden Elements** (on) — keep on; avoids tripping honeypot fields.
- **"What to do if a required field can't be filled"** — was *Fill with Random Data*.
  Fine for now; revisit if specific forms misbehave.

---

## 4. The "Buy + Build" To-Do List (blocking scale)

- [ ] **Purchase ≈1000 proxies** (format + provider confirmed).
- [ ] **Purchase cloud captcha plan** (product + API key).
- [ ] **Launch + enable GSA Captcha Breaker** (already owned, in files).
- [ ] **Configure proxies** in GSA (Submission Content → Use proxies for sending).
- [ ] **Configure captcha** (CB primary + cloud fallback) in Captchas tab.
- [ ] **Set threads ≈20** (Options) + timing spread.
- [ ] **Make the pipeline CSV GSA-ready** (quoted values via `QUOTE_ALL`, headers
      that match the message macros) so the scrape output imports with zero editing.
- [ ] **Then** run a small REAL batch (e.g. 10–25 live targets) before going big.

---

## 5. Preliminary Send Checklist (DRAFT — will grow)

> Use this once the setup in §1–§3 is done. For the bare personalization test we
> already ran, only steps marked ⭐ are strictly needed.

**One-time / per-machine setup**
1. [ ] Launch **GSA Captcha Breaker** (and confirm cloud fallback key is in).
2. [ ] Confirm proxies imported + tested (Submission Content → Use proxies for sending).
3. [ ] Confirm threads ≈20 (Options).

**Per campaign**
4. ⭐ Prepare the CSV: URL column + your personalization columns, **every value
   quoted** (`QUOTE_ALL`). Headers must match the `%macros%` in the message.
5. ⭐ New project → *Scraping* tab → **uncheck the keyword** under "Keywords to find
   Targets" (so GSA doesn't scrape) → **"Add your own URLs"** → import the CSV.
   - Verify: hover a URL → the CSV data shows in the mouse-over hint.
6. ⭐ *Submission Content* tab → select the **`message`** row → **Edit** → paste the
   message body (with `%column%` macros + `{spin|syntax}`). Set `subject`/`name`/
   `email` rows as desired (random is fine).
7. [ ] *Captchas* tab → confirm CB + cloud fallback enabled.
8. [ ] *Filter* / *Checking* tabs → review (defaults OK to start).
9. ⭐ **OK** to close Settings → **Start ▶ → "Send Message (+Check)"**.
10. [ ] Watch **Sent / Failed** columns. Check a sample of successes.

**After**
11. [ ] **Save/Export** results CSV (keeps status per URL).
12. [ ] Feed failures/blocked into the cold-email bucket.

> ⚠️ This checklist is preliminary. Add: proxy provider specifics, exact thread/
> timing numbers, captcha order, and any per-niche filter tweaks as we lock them in.

---

## 6. Open Question — Do We Need 3 Separate Test Sites?

**Short answer: No, not required.** Personalization is already proven — GSA rendered
Joe's Plumbing's exact row data and submitted it for real. Seeing 3 land instead of 1
would only re-demonstrate behavior we already understand (the single-domain dedupe).

**If you want extra certainty that *different rows produce different messages* inside
GSA** (not just our local sim), the cheap way is:
- Re-run the **same 3-row CSV** with **duplicate-domain skipping turned OFF** in GSA,
  so all 3 sub-paths on webhook.site send. (No new sites to build.)
- *Or* I can spin up **3 different recorder domains** (webhook.site + 2 other free
  request-catchers) so all 3 are distinct domains and naturally send. ~5 min of setup.

**Recommendation:** skip it for now. It's optional polish, not a blocker. The real
campaign uses distinct business domains, so multi-send happens automatically.

---

## Changelog
- 2026-06-13 — Created. Captured post-proof state: personalization done; proxies,
  captcha (CB desktop + cloud), and thread/timing settings still to set up. Added
  buy/build to-do, preliminary send checklist, and the "3 test sites?" decision.
