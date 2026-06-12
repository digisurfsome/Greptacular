#!/usr/bin/env python3
"""Preview Machine copywriter — subscription-billed copy JSON generator.

Reads ``site_audit.csv`` (the site_age.py output contract) and writes one
``<slug>.json`` per business into a copy-cache directory.  ``sitegen.py
--copydir <dir>`` then renders previews from these JSONs with ZERO API spend.

Billing: Claude **subscription** via the Agent SDK (``~/.claude/.credentials.json``).
NO ``ANTHROPIC_API_KEY`` is used — the env is force-cleared.  Do NOT add an
API-key fallback here; the metered API path already exists inside sitegen.py
as the overflow valve for huge runs.

Resumable by design: existing ``<slug>.json`` files are never regenerated, so
you can re-run after hitting subscription rate limits and it picks up where it
left off.

Usage (from repo root):
    cd <repo-root>
    python scripts/preview_machine/copywriter.py site_audit.csv --outdir copy
    python scripts/preview_machine/copywriter.py site_audit.csv --model haiku
    python scripts/preview_machine/copywriter.py --selftest

SDK pattern source: server/services/yt_processor.py::_call_via_sdk (the
3-bug-fixed reference — acceptEdits mode, settings file, rate_limit_event
exception recovery).  See docs/references/sdk-client-pattern.md.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Models (subscription usage — sonnet for quality, haiku if rate limits bite)
# ---------------------------------------------------------------------------
MODELS = {
    "sonnet": "claude-sonnet-4-6",
    "haiku": "claude-haiku-4-5",
}
DEFAULT_VERDICTS = ("STRONG TARGET", "WORTH A LOOK")
SDK_TIMEOUT_SECONDS = 600

# ---------------------------------------------------------------------------
# The copy contract — keys are template-bound ({{TOKEN}} vocabulary).
# Do NOT rename keys; sitegen.py maps them 1:1 onto template.html tokens.
# ---------------------------------------------------------------------------
REQUIRED_KEYS = [
    "badge_text", "hero_headline_pre", "hero_accent", "hero_sub",
    "tagline_short", "services_headline", "services_sub", "services",
    "step_1", "step_2", "step_3",
    "about_headline", "about_text_1", "about_text_2", "checks",
    "panel_card_title", "panel_card_sub",
    "reviews_headline", "reviews_sub",
    "cta_headline", "cta_sub", "footer_blurb",
]

# Liability lint — these are legal-claim rules, not style preferences.
# A copy block containing any of these is REJECTED (not written, so it
# regenerates on the next run).
BANNED_PATTERNS = [
    (re.compile(r"!"), "exclamation mark"),
    (re.compile(r"\blicensed\b", re.I), "licensing claim"),
    (re.compile(r"\binsured\b", re.I), "insurance claim"),
    (re.compile(r"\bcertif", re.I), "certification claim"),
    (re.compile(r"\baward", re.I), "award claim"),
    (re.compile(r"\bguarantee", re.I), "guarantee claim"),
    (re.compile(r"\b\d+\+?\s*years\b", re.I), "invented years-in-business"),
    (re.compile(r"look no further", re.I), "banned cliche"),
]

SYSTEM_PROMPT = """You are a copywriter producing website copy for local service businesses.
You will receive a batch of businesses. For EACH business, write one JSON copy object.

OUTPUT FORMAT — respond with ONE JSON object and nothing else (no prose, no markdown fences):
{"<slug>": {<copy object>}, "<slug>": {<copy object>}, ...}

Each copy object must have EXACTLY these keys:
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

LIABILITY RULES — absolute, no exceptions:
- Use ONLY known facts: business name, city, state, and the real Google rating/review count when provided.
- NEVER invent: stats, years in business, awards, certifications, licenses, customer quotes, guarantees.
- "checks" must be free of unverifiable claims. Good: "Locally owned", "Free quotes", "Fast response", "Satisfaction focused". NEVER "Licensed & insured".
- Mention the city naturally. Confident, premium, plain-spoken.
- No exclamation marks anywhere. No "look no further" cliches."""


# ---------------------------------------------------------------------------
# Slug — MUST match sitegen.py's slug for the same business, because sitegen
# looks up <copydir>/<slug>.json by its own slug.  manifest.json (business
# name -> slug) is written alongside so mismatches are detectable: the
# sitegen --copydir patch falls back to a manifest lookup by business name.
# ---------------------------------------------------------------------------
def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "business"


def load_rows(csv_path: Path, verdicts: tuple[str, ...]) -> list[dict]:
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return []
    if "business" not in rows[0]:
        sys.exit(
            f"FATAL: {csv_path} has no 'business' column. Expected the post-fix "
            "site_audit.csv contract (verdict, score, business, phone, city, ...)."
        )
    if verdicts == ("ALL",):
        return rows
    return [r for r in rows if (r.get("verdict") or "").strip().upper() in verdicts]


def lint_copy(copy: dict) -> list[str]:
    """Validate one copy object against the contract + liability rules."""
    problems: list[str] = []
    for key in REQUIRED_KEYS:
        if key not in copy:
            problems.append(f"missing key: {key}")
    if problems:
        return problems
    if not (isinstance(copy["services"], list) and len(copy["services"]) == 6):
        problems.append("services must be a list of exactly 6 items")
    if not (isinstance(copy["checks"], list) and len(copy["checks"]) == 4):
        problems.append("checks must be a list of exactly 4 items")
    for step in ("step_1", "step_2", "step_3"):
        if not (isinstance(copy[step], dict) and "name" in copy[step] and "desc" in copy[step]):
            problems.append(f"{step} must be {{name, desc}}")
    blob = json.dumps(copy)
    for pattern, label in BANNED_PATTERNS:
        if pattern.search(blob):
            problems.append(f"liability lint: {label}")
    return problems


def build_batch_message(rows: list[dict]) -> str:
    lines = ["Write copy for these businesses. Known facts only:\n"]
    for r in rows:
        slug = slugify(r["business"])
        facts = [f"slug: {slug}", f"business: {r['business']}"]
        for col in ("city", "state", "rating", "reviews"):
            val = (r.get(col) or "").strip()
            if val:
                facts.append(f"{col}: {val}")
        lines.append(" | ".join(facts))
    lines.append(
        "\nReturn ONE JSON object keyed by slug, one copy object per business, "
        "exactly the keys in the contract. No markdown fences."
    )
    return "\n".join(lines)


def extract_json(text: str) -> dict:
    """Pull the JSON object out of a model response (fences, prose, etc.)."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError(f"no JSON object in response (first 200 chars: {text[:200]!r})")
    return json.loads(text[start : end + 1])


# ---------------------------------------------------------------------------
# Subscription SDK call — pattern copied from yt_processor._call_via_sdk()
# (all 3 known bugs fixed). DO NOT swap in anthropic.Anthropic(api_key=...).
# ---------------------------------------------------------------------------
async def call_claude_subscription(system_prompt: str, user_message: str, model: str, scratch: str) -> str:
    from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

    # CLAUDECODE blocks nested CLI sessions; API vars must be EMPTY STRINGS
    # (empty overrides os.environ in the SDK's env merge) so the CLI falls
    # back to subscription OAuth in ~/.claude/.credentials.json.
    os.environ.pop("CLAUDECODE", None)
    sdk_env = {"ANTHROPIC_API_KEY": "", "ANTHROPIC_AUTH_TOKEN": ""}

    system_cli = shutil.which("claude")
    if not system_cli:
        raise RuntimeError("Claude CLI not found on PATH — install Claude Code and run 'claude login' first")
    creds = Path.home() / ".claude" / ".credentials.json"
    if not creds.exists():
        print(f"  WARNING: no {creds} — run 'claude login' or this will fail")

    settings_file = Path(scratch) / ".claude-copywriter-settings.json"
    settings_file.write_text(json.dumps({"permissions": {"defaultMode": "acceptEdits", "allow": []}}))

    client = ClaudeSDKClient(
        options=ClaudeAgentOptions(
            model=model,
            cli_path=system_cli,
            system_prompt=system_prompt,
            env=sdk_env,
            max_turns=2,
            permission_mode="acceptEdits",  # NOT bypassPermissions — Bun crash (exit 3) on Windows
            allowed_tools=[],
            cwd=scratch,
            settings=str(settings_file.resolve()),
            setting_sources=["user"],
        )
    )

    async def _run() -> str:
        await client.__aenter__()
        try:
            await client.query(user_message)
            full_text = ""
            try:
                async for msg in client.receive_response():
                    msg_type = type(msg).__name__
                    if msg_type in ("RateLimitEvent", "rate_limit_event"):
                        print("  rate_limit event — SDK retries automatically...")
                        continue
                    if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                        for block in msg.content:
                            if type(block).__name__ == "TextBlock" and hasattr(block, "text"):
                                full_text += block.text
            except Exception as exc:
                # SDK throws "Unknown message type: rate_limit_event" AFTER the
                # full response is already collected. Keep what we have.
                if full_text.strip():
                    print(f"  recovered from SDK exception with {len(full_text)} chars: {exc}")
                else:
                    raise
            return full_text
        finally:
            try:
                await client.__aexit__(None, None, None)
            except Exception:
                pass

    return await asyncio.wait_for(_run(), timeout=SDK_TIMEOUT_SECONDS)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
async def run(args: argparse.Namespace) -> int:
    csv_path = Path(args.csv)
    if not csv_path.exists():
        sys.exit(f"FATAL: {csv_path} not found")
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    verdicts = ("ALL",) if args.verdicts.strip().upper() == "ALL" else tuple(
        v.strip().upper() for v in args.verdicts.split(",")
    )
    rows = load_rows(csv_path, verdicts)
    if args.limit:
        rows = rows[: args.limit]

    manifest_path = outdir / "manifest.json"
    manifest: dict[str, str] = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    pending = []
    for r in rows:
        slug = slugify(r["business"])
        manifest[r["business"]] = slug
        if not (outdir / f"{slug}.json").exists():
            pending.append(r)

    print(f"{len(rows)} businesses match verdicts {verdicts}; "
          f"{len(rows) - len(pending)} already cached; {len(pending)} to generate.")
    if not pending:
        manifest_path.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        print("Nothing to do — copy cache is complete.")
        return 0

    model = MODELS[args.model]
    scratch = tempfile.mkdtemp(prefix="preview_copywriter_")
    written = failed = 0

    for i in range(0, len(pending), args.batch_size):
        batch = pending[i : i + args.batch_size]
        names = ", ".join(b["business"] for b in batch[:3])
        print(f"\nBatch {i // args.batch_size + 1}: {len(batch)} businesses ({names}...) via {model}")
        t0 = time.time()
        try:
            raw = await call_claude_subscription(SYSTEM_PROMPT, build_batch_message(batch), model, scratch)
            payload = extract_json(raw)
        except Exception as exc:
            print(f"  BATCH FAILED ({exc}) — rows stay pending, re-run to resume.")
            failed += len(batch)
            continue

        for row in batch:
            slug = slugify(row["business"])
            copy = payload.get(slug)
            if not isinstance(copy, dict):
                print(f"  MISSING in response: {slug} — will retry next run")
                failed += 1
                continue
            problems = lint_copy(copy)
            if problems:
                print(f"  REJECTED {slug}: {'; '.join(problems[:3])} — will retry next run")
                failed += 1
                continue
            (outdir / f"{slug}.json").write_text(
                json.dumps(copy, indent=1, ensure_ascii=False), encoding="utf-8"
            )
            written += 1
        manifest_path.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        print(f"  batch done in {time.time() - t0:.0f}s — {written} written, {failed} failed so far")

    print(f"\nDONE: {written} copy JSONs written to {outdir.resolve()}, {failed} pending retry.")
    print(f"Next: python sitegen.py {csv_path} --copydir {outdir}")
    return 0 if failed == 0 else 1


# ---------------------------------------------------------------------------
# Selftest — fully offline, no SDK, no network
# ---------------------------------------------------------------------------
def selftest() -> int:
    ok = True

    def check(label: str, cond: bool) -> None:
        nonlocal ok
        print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
        ok = ok and cond

    print("copywriter selftest:")
    check("slugify basic", slugify("Joe's Pressure Washing, LLC") == "joe-s-pressure-washing-llc")
    check("slugify empty", slugify("***") == "business")

    good = {k: "Words here" for k in REQUIRED_KEYS}
    good["services"] = [{"name": "Wash", "desc": "A sentence."}] * 6
    good["checks"] = ["Locally owned", "Free quotes", "Fast response", "Satisfaction focused"]
    for s in ("step_1", "step_2", "step_3"):
        good[s] = {"name": "Step", "desc": "A sentence."}
    check("lint accepts clean copy", lint_copy(good) == [])

    bad = dict(good)
    bad["hero_sub"] = "Licensed & insured with 20 years of experience!"
    problems = lint_copy(bad)
    check("lint catches licensing claim", any("licensing" in p for p in problems))
    check("lint catches years claim", any("years" in p for p in problems))
    check("lint catches exclamation", any("exclamation" in p for p in problems))

    missing = {k: v for k, v in good.items() if k != "cta_headline"}
    check("lint catches missing key", any("cta_headline" in p for p in lint_copy(missing)))

    fenced = '```json\n{"a-slug": {"x": 1}}\n```'
    check("extract_json strips fences", extract_json(fenced) == {"a-slug": {"x": 1}})

    msg = build_batch_message([
        {"business": "Big Tex Wash", "city": "Waco", "state": "TX", "rating": "4.8", "reviews": "31"},
        {"business": "No Facts Co", "city": "", "state": "", "rating": "", "reviews": ""},
    ])
    check("batch msg includes slug", "slug: big-tex-wash" in msg)
    check("batch msg omits empty facts", "rating:" not in msg.split("no-facts-co")[1].split("\n")[0])

    print("SELFTEST", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


def main() -> int:
    p = argparse.ArgumentParser(description="Generate copy-cache JSONs from site_audit.csv via Claude subscription")
    p.add_argument("csv", nargs="?", default="site_audit.csv", help="site_audit.csv from site_age.py")
    p.add_argument("--outdir", default="copy", help="copy-cache dir for sitegen --copydir (default: copy)")
    p.add_argument("--model", choices=list(MODELS), default="sonnet")
    p.add_argument("--batch-size", type=int, default=10, help="businesses per generation pass (default 10)")
    p.add_argument("--verdicts", default=",".join(DEFAULT_VERDICTS),
                   help='comma-separated verdict filter, or "all" (default: "STRONG TARGET,WORTH A LOOK")')
    p.add_argument("--limit", type=int, default=0, help="cap rows processed this run (0 = no cap)")
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()

    if args.selftest:
        return selftest()
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
