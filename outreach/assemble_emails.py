"""
assemble_emails.py — Assemble personalized outreach emails from enriched CSV.

Reads the enriched CSV (output of orchestrator.py), loads the pre-generated
spinner variant pools, and builds a unique email for each business.

Cost: $0/email (pure Python random selection — no API calls).
Prerequisite: run generate_variants.py once per hook first.

Usage:
  python assemble_emails.py --input enriched_seo_rankings_plumber_austin.csv
  python assemble_emails.py --input enriched.csv --hook pagespeed --reply-to you@yourdomain.com
  python assemble_emails.py --input enriched.csv --preview 5   # print first 5 emails

Output columns added:
  email_subject, email_body, reply_to, hook_used, tier
"""

import csv
import json
import random
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

VARIANTS_DIR = Path(__file__).parent / "spinner_variants"

# ─── Variant loader ────────────────────────────────────────────────────────────

_variant_cache: Dict[str, dict] = {}

def load_variants(hook_name: str, tier: str) -> Optional[dict]:
    """Load spinner variants for hook+tier. Cached after first load."""
    key = f"{hook_name}_tier_{tier.lower()}"
    if key in _variant_cache:
        return _variant_cache[key]

    path = VARIANTS_DIR / f"{key}.json"
    if not path.exists():
        return None

    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    _variant_cache[key] = data
    return data


# ─── Email assembler ───────────────────────────────────────────────────────────

def assemble_email(row: dict, hook_name: str, reply_to: str = "") -> Dict[str, str]:
    """
    Build one email for a business row.
    Returns dict with email_subject and email_body.
    Falls back gracefully if variants missing.
    """
    tier = row.get("tier", "D")

    if tier == "SKIP":
        return {"email_subject": "", "email_body": "", "assembly_status": "skipped"}

    variants = load_variants(hook_name, tier)

    if not variants:
        return {
            "email_subject": "",
            "email_body": "",
            "assembly_status": f"missing_variants_{hook_name}_tier_{tier.lower()}",
        }

    # Pick random variant from each block
    def pick(block_name: str) -> str:
        options = variants.get(block_name, [])
        if not options:
            return ""
        return random.choice(options)

    subject_raw   = pick("subject_lines")
    opener_raw    = pick("opener")
    hook_raw      = pick("hook")
    pain_raw      = pick("pain")
    pitch_raw     = pick("pitch")
    cta_raw       = pick("cta")

    # Substitute template variables from the row
    # Clean up None values so format doesn't crash
    safe_row = {k: (v if v is not None else "") for k, v in row.items()}

    def safe_format(template: str) -> str:
        try:
            return template.format(**safe_row)
        except KeyError as e:
            # Missing variable in row — leave placeholder visible so it's obvious
            return template  # Return unformatted so missing vars are visible

    subject = safe_format(subject_raw)
    opener  = safe_format(opener_raw)
    hook    = safe_format(hook_raw)
    pain    = safe_format(pain_raw)
    pitch   = safe_format(pitch_raw)
    cta     = safe_format(cta_raw)

    # Assemble body — 4 short paragraphs or sentences, no fluff
    body_parts = [p for p in [opener, hook, pain, pitch, cta] if p.strip()]
    body = "\n\n".join(body_parts)

    # Add reply-to line if provided
    if reply_to:
        body += f"\n\n— Reply directly to this email"

    return {
        "email_subject": subject,
        "email_body": body,
        "assembly_status": "ok",
    }


# ─── Batch assembler ───────────────────────────────────────────────────────────

def assemble_batch(rows: List[dict], hook_name: str, reply_to: str = "") -> List[dict]:
    """Assemble emails for all rows. Returns rows with email columns added."""
    results = []
    skipped = 0
    missing_variants = set()

    for row in rows:
        email = assemble_email(row, hook_name, reply_to)

        if email["assembly_status"] == "skipped":
            skipped += 1
        elif email["assembly_status"].startswith("missing_variants"):
            missing_variants.add(email["assembly_status"].replace("missing_variants_", ""))

        results.append({**row, **email, "hook_used": hook_name, "reply_to": reply_to})

    if skipped:
        print(f"  Skipped {skipped} rows (no data from hook)")
    if missing_variants:
        for mv in missing_variants:
            parts = mv.split("_tier_")
            h = parts[0]
            t = parts[1].upper() if len(parts) > 1 else "?"
            print(f"  WARNING: Missing variant file for hook='{h}' tier='{t}'")
            print(f"    Run: python generate_variants.py --hook {h}")

    return results


# ─── Output ────────────────────────────────────────────────────────────────────

BASE_OUTPUT_COLS = [
    "business_name", "website_url", "domain", "niche", "city", "state",
    "kw1", "kw1_rank", "kw1_traffic",
    "kw2", "kw2_rank", "kw2_traffic",
    "kw3", "kw3_rank", "kw3_traffic",
    "top_competitor", "top_traffic",
    "tier", "hook_used",
    "email_subject", "email_body", "reply_to", "assembly_status",
]

def write_output(rows: List[dict], output_path: str):
    # Collect all column names (base + any extras from hooks)
    all_keys = set()
    for row in rows:
        all_keys.update(row.keys())

    # Start with base cols, append any extras
    cols = [c for c in BASE_OUTPUT_COLS if c in all_keys]
    extras = [k for k in sorted(all_keys) if k not in cols]
    cols += extras

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {len(rows)} rows to {output_path}")


def print_preview(rows: List[dict], n: int = 3):
    """Print N sample emails to console for review."""
    sample = [r for r in rows if r.get("assembly_status") == "ok"][:n]

    for i, row in enumerate(sample, 1):
        print(f"\n{'='*60}")
        print(f"[{i}] {row.get('business_name', '?')} — Tier {row.get('tier', '?')}")
        print(f"SUBJECT: {row.get('email_subject', '')}")
        print(f"\n{row.get('email_body', '')}")

    if not sample:
        print("No successfully assembled emails to preview.")


def print_summary(rows: List[dict]):
    from collections import Counter
    tiers = Counter(r.get("tier", "?") for r in rows)
    statuses = Counter(r.get("assembly_status", "?") for r in rows)

    print("\n--- Assembly Summary ---")
    for tier in ["A", "B", "C", "D"]:
        print(f"  Tier {tier}: {tiers.get(tier, 0)}")
    print(f"  Skipped: {tiers.get('SKIP', 0)}")
    print(f"  Status: {dict(statuses)}")
    print(f"  Total ready to send: {statuses.get('ok', 0)}")


# ─── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assemble personalized emails from enriched CSV")
    parser.add_argument("--input", required=True, help="Enriched CSV (output of orchestrator.py)")
    parser.add_argument("--output", help="Output CSV path (auto-named if omitted)")
    parser.add_argument("--hook", default="seo_rankings",
                        help="Hook name to use for variant loading (default: seo_rankings)")
    parser.add_argument("--reply-to", default="",
                        help="Reply-to email address to include in outreach")
    parser.add_argument("--preview", type=int, default=0,
                        help="Print N sample emails to console before writing")
    parser.add_argument("--seed", type=int, default=None,
                        help="Random seed for reproducible assembly (optional)")

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # Load input
    with open(args.input, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Loaded {len(rows)} businesses from {args.input}")

    # Check variant files exist
    tiers_needed = set(r.get("tier", "D") for r in rows if r.get("tier") != "SKIP")
    missing = []
    for tier in tiers_needed:
        path = VARIANTS_DIR / f"{args.hook}_tier_{tier.lower()}.json"
        if not path.exists():
            missing.append(tier)

    if missing:
        print(f"\nMissing variant files for tiers: {missing}")
        print(f"Run first: python generate_variants.py --hook {args.hook}")
        sys.exit(1)

    # Assemble
    print(f"Assembling emails (hook={args.hook})...")
    results = assemble_batch(rows, args.hook, args.reply_to)

    # Preview
    if args.preview > 0:
        print_preview(results, args.preview)

    # Write output
    if args.output:
        output_path = args.output
    else:
        base = Path(args.input).stem
        output_path = f"emails_{base}.csv"

    write_output(results, output_path)
    print_summary(results)

    print(f"\nNext step: python filter.py --input {output_path}")
