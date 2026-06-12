#!/usr/bin/env python3
"""
Groq Review Analyzer — AI Receptionist Lead Qualifier
=======================================================
Reads the _reviews_raw.json files output by hvac_dallas_leads.py,
sends every review to Groq (free, fast Llama 3.3 70B), and:

  1. Flags reviews mentioning ANY phone/response/communication problem
  2. Extracts the EXACT phrase that signals the problem
  3. Builds a master keyword list from real data (not guesses)
  4. Outputs a scored lead sheet with AI-verified quotes ready for email

HOW TO RUN:
  1. Get a free Groq API key at: https://console.groq.com
     (sign up → API Keys → Create → copy it)
  2. Add to .env file (same folder as this script):
         GROQ_API_KEY=gsk_yourkey
  3. Run:
         python analyze_reviews_groq.py hvac_dallas_standard_reviews_raw.json
     Or analyze both at once:
         python analyze_reviews_groq.py hvac_dallas_standard_reviews_raw.json hvac_dallas_emergency_reviews_raw.json

COST: $0.00 — Groq free tier
MODEL: llama-3.3-70b-versatile (Groq hosted, extremely fast)
"""

import csv
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

# ── Load .env ─────────────────────────────────────────────────────────────────
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.1-8b-instant"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"

# ── Groq call ─────────────────────────────────────────────────────────────────
def ask_groq(prompt: str, retries: int = 3) -> str:
    import requests as req_lib
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY.strip()}",
        "Content-Type":  "application/json",
    }
    body = {
        "model":       GROQ_MODEL,
        "temperature": 0,
        "max_tokens":  300,
        "messages": [
            {
                "role":    "system",
                "content": (
                    "You are a signal detector. Your job is to identify if a customer review "
                    "mentions any problem related to: not answering the phone, going to voicemail, "
                    "long hold times, no callback, being ignored, no response, after-hours unavailability, "
                    "having to call multiple times, or any other communication/availability failure. "
                    "Be liberal — if there's ANY hint of a phone or response problem, flag it."
                )
            },
            {"role": "user", "content": prompt}
        ]
    }

    for attempt in range(retries):
        try:
            resp = req_lib.post(GROQ_URL, headers=headers, json=body, timeout=30)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            elif resp.status_code == 429:
                wait = 10 * (attempt + 1)
                print(f"    ⏳ Rate limited — waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    ⚠️  Groq {resp.status_code}: {resp.text[:200]}")
                if attempt == 0:
                    print(f"    🔑 Key used: {GROQ_API_KEY[:8]}...{GROQ_API_KEY[-4:]} ({len(GROQ_API_KEY)} chars)")
                time.sleep(3)
        except Exception as e:
            print(f"    ⚠️  Request error attempt {attempt+1}: {e}")
            time.sleep(3)
    return "ERROR"


ANALYSIS_PROMPT = """\
Review (★{stars}): {text}

Answer in this EXACT format (no other text, no extra lines):
SIGNAL: YES or NO
CATEGORY: [one of: no_answer | voicemail | no_callback | on_hold | ignored | after_hours | repeat_calls | other_comm_problem | none]
PHRASE: [copy the exact 5-15 word phrase from the review that shows the problem, or "none"]
SUMMARY: [one sentence: what went wrong with communication, or "no communication issue"]
BIZ_SIZE: [solo_operator | small_team | established | unknown — based on clues like "the owner", "their office", "dispatch", etc.]
ROOT_CAUSE: [one of: owner_too_busy | no_system | bad_culture | overwhelmed | unknown]
PITCH: [one of: ai_receptionist | callback_automation | review_management | all_three | not_applicable — which service fits this problem best]
"""


def analyze_review(review: dict) -> dict:
    prompt = ANALYSIS_PROMPT.format(
        stars=review["stars"],
        text=review["text"][:600]  # cap at 600 chars — enough context, keeps cost zero
    )
    raw = ask_groq(prompt)

    result = {
        "signal":     False,
        "category":   "none",
        "phrase":     "none",
        "summary":    "no communication issue",
        "biz_size":   "unknown",
        "root_cause": "unknown",
        "pitch":      "not_applicable",
    }

    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("SIGNAL:"):
            result["signal"] = "yes" in line.lower()
        elif line.startswith("CATEGORY:"):
            result["category"] = line.split(":", 1)[1].strip().lower()
        elif line.startswith("PHRASE:"):
            result["phrase"] = line.split(":", 1)[1].strip()
        elif line.startswith("SUMMARY:"):
            result["summary"] = line.split(":", 1)[1].strip()
        elif line.startswith("BIZ_SIZE:"):
            result["biz_size"] = line.split(":", 1)[1].strip().lower()
        elif line.startswith("ROOT_CAUSE:"):
            result["root_cause"] = line.split(":", 1)[1].strip().lower()
        elif line.startswith("PITCH:"):
            result["pitch"] = line.split(":", 1)[1].strip().lower()

    return result


# ── Main ──────────────────────────────────────────────────────────────────────
def process_file(raw_json_path: str):
    path = Path(raw_json_path)
    if not path.exists():
        print(f"❌ File not found: {raw_json_path}")
        return

    reviews = json.loads(path.read_text(encoding="utf-8"))
    print(f"\n{'='*60}")
    print(f"Analyzing: {path.name}")
    print(f"Reviews:   {len(reviews)}")
    print(f"Model:     {GROQ_MODEL} (free)")
    print(f"{'='*60}\n")

    # Group by business
    by_biz = defaultdict(list)
    for rv in reviews:
        by_biz[rv["business"]].append(rv)

    all_results   = []   # flat list for CSV
    keyword_freq  = defaultdict(int)   # phrase → count across all reviews
    biz_scores    = defaultdict(lambda: {"signals": [], "score": 0, "name": ""})

    total = len(reviews)
    for idx, review in enumerate(reviews, 1):
        biz_name = review["business"]
        src   = review.get("source", "google")
        src_icon = "🔴" if src == "google" else "🟠"
        print(f"  [{idx:>3}/{total}] {src_icon}★{review['stars']} | {biz_name[:40]:<40}", end=" ")

        analysis = analyze_review(review)

        if analysis["signal"]:
            print(f"🚨 {analysis['category']} — \"{analysis['phrase'][:50]}\"")
            keyword_freq[analysis["phrase"]] += 1
            biz_scores[biz_name]["score"]   += 1
            biz_scores[biz_name]["name"]     = biz_name
            biz_scores[biz_name]["signals"].append({
                "stars":    review["stars"],
                "category": analysis["category"],
                "phrase":   analysis["phrase"],
                "summary":  analysis["summary"],
                "text":     review["text"][:300],
                "date":     review["date"],
            })
        else:
            print("✅ clean")

        all_results.append({
            "business":   biz_name,
            "source":     review.get("source", "google"),
            "stars":      review["stars"],
            "date":       review.get("date", ""),
            "time_ago":   review.get("time_ago", ""),
            "signal":     analysis["signal"],
            "category":   analysis["category"],
            "phrase":     analysis["phrase"],
            "summary":    analysis["summary"],
            "biz_size":   analysis["biz_size"],
            "root_cause": analysis["root_cause"],
            "pitch":      analysis["pitch"],
            "text":       review["text"][:300],
        })

        # Groq free tier = 30 req/min → need 2s+ between calls
        time.sleep(2.5)

    # ── Output 1: Full results CSV ─────────────────────────────────────────────
    out_csv = str(path).replace("_reviews_raw.json", "_ai_analysis.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        fields = ["business","source","stars","date","time_ago","signal","category","phrase","summary","biz_size","root_cause","pitch","text"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(all_results)
    print(f"\n✅ Full analysis saved → {Path(out_csv).name}")

    # ── Output 2: Business lead scores ────────────────────────────────────────
    scored_biznesses = sorted(biz_scores.values(), key=lambda x: -x["score"])
    lead_csv = str(path).replace("_reviews_raw.json", "_ai_leads.csv")
    with open(lead_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["RANK","BUSINESS","AI_SIGNAL_COUNT","TOP_QUOTE","TOP_CATEGORY"])
        for rank, biz in enumerate(scored_biznesses, 1):
            top = biz["signals"][0] if biz["signals"] else {}
            w.writerow([
                rank,
                biz["name"],
                biz["score"],
                top.get("text", "")[:200],
                top.get("category", ""),
            ])
    print(f"✅ Lead scores saved    → {Path(lead_csv).name}")

    # ── Output 3: Keyword frequency report ────────────────────────────────────
    kw_file = str(path).replace("_reviews_raw.json", "_keyword_patterns.txt")
    with open(kw_file, "w", encoding="utf-8") as f:
        f.write("DISCOVERED SIGNAL PHRASES — sorted by frequency\n")
        f.write("Use these to update MISSED_CALL_KEYWORDS in hvac_dallas_leads.py\n")
        f.write("="*60 + "\n\n")
        for phrase, count in sorted(keyword_freq.items(), key=lambda x: -x[1]):
            if phrase and phrase.lower() != "none":
                f.write(f"  ({count:>3}x)  {phrase}\n")
    print(f"✅ Keyword patterns     → {Path(kw_file).name}")

    # Print summary
    flagged_count = sum(1 for r in all_results if r["signal"])
    print(f"\n{'─'*55}")
    print("  SUMMARY")
    print(f"{'─'*55}")
    print(f"  Total reviews analyzed:  {total}")
    print(f"  Communication problems:  {flagged_count} ({flagged_count/total*100:.0f}%)")
    print(f"  Businesses with signals: {len(biz_scores)}")
    print("\n  TOP LEADS:")
    for biz in scored_biznesses[:5]:
        print(f"    🔴 [{biz['score']} signals] {biz['name']}")
        if biz["signals"]:
            print(f"       \"{biz['signals'][0]['text'][:120]}...\"")
    print("\n  TOP SIGNAL PHRASES (real language from real reviews):")
    for phrase, count in sorted(keyword_freq.items(), key=lambda x: -x[1])[:15]:
        if phrase and phrase.lower() != "none":
            print(f"    ({count}x) \"{phrase}\"")


def main():
    if not GROQ_API_KEY:
        print("❌ No GROQ_API_KEY found.")
        print(f"   Add it to: {_env_path}")
        print("   Format: GROQ_API_KEY=gsk_yourkey")
        print("   Get a free key at: https://console.groq.com")
        return

    files = sys.argv[1:] or []
    if not files:
        # Auto-detect raw JSON files in same folder
        files = list(Path(__file__).parent.glob("*_reviews_raw.json"))
        if not files:
            print("❌ No *_reviews_raw.json files found.")
            print("   Run hvac_dallas_leads.py first to generate them.")
            return
        print(f"Found {len(files)} raw review file(s) to analyze.")

    for f in files:
        process_file(str(f))


if __name__ == "__main__":
    main()
