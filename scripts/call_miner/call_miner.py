#!/usr/bin/env python3
"""
call_miner.py — Live Call Exchange Miner
=========================================
Extracts verbatim exchange pairs from real sales/cold call recordings.
Designed specifically for training a sales bot on:
  - What prospects actually say (objections, questions, hesitations)
  - How the salesperson responds
  - How the same topic comes up across many calls in different words

NOT a channel playbook builder — that's truth_builder_v2.py.
This captures the LIVE CONVERSATION DATA.

4-sweep pipeline (same pattern as channel_brain):
  Sweep 0: Interaction taxonomy discovery (auto-discovers what topics come up in calls)
  Sweep 1: Exchange pair extraction (prospect line + salesperson response, per video)
  Sweep 2: Cluster (same objection asked 10 ways = 1 cluster, all 10 variants kept)
  Sweep 3: Render (per-category .md files + master exchange doc)

Usage:
  python call_miner.py --config scripts/call_miner/connor-calls.json
  python call_miner.py --config scripts/call_miner/connor-calls.json --limit 5
  python call_miner.py --config scripts/call_miner/connor-calls.json --dry-run
  python call_miner.py --config scripts/call_miner/connor-calls.json --sweep 1
  python call_miner.py --config scripts/call_miner/connor-calls.json --reset

Config fields:
  project_name        : label for output headers
  videos_dir          : folder containing {video}/transcript.txt subfolders
  output_dir          : where to write all output
  call_filter_keywords: optional list of strings — only process videos whose
                        folder name matches one (e.g. ["cold-call","live","demo"])
                        Omit or set [] to process ALL videos in the folder
  taxonomy_gate       : true = pause for review after Sweep 0 (default true)
  taxonomy_sample_n   : how many transcripts to sample for taxonomy (default 8)
  cluster_mode        : "llm" | "embedding" | "dual" (default "llm")
  llm_batch_size      : extractions per cluster batch (default 25)
  embedding_threshold : cosine similarity cutoff (default 0.82)

IMPORTANT: subscription auth. Run `claude login` before first use.
"""

import argparse
import asyncio
import json
import os
import random
import re
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

# Tiktoken for transcript chunking (avoids exit 15 on long call transcripts)
try:
    import tiktoken
    _ENC = tiktoken.get_encoding("cl100k_base")
    def _token_count(s: str) -> int: return len(_ENC.encode(s))
    def _chunk_text(text: str, max_tokens: int = 4000, overlap: int = 400) -> list[str]:
        tokens = _ENC.encode(text)
        chunks, i = [], 0
        while i < len(tokens):
            chunk_tokens = tokens[i:i + max_tokens]
            chunks.append(_ENC.decode(chunk_tokens))
            i += max_tokens - overlap
        return chunks
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    def _chunk_text(text: str, max_tokens: int = 4000, overlap: int = 400) -> list[str]:
        # Char-based fallback (~4 chars per token)
        size, step = max_tokens * 4, (max_tokens - overlap) * 4
        return [text[i:i + size] for i in range(0, len(text), step)] or [text]

# Pop at import — prevents CLAUDECODE=1 poisoning nested claude processes
os.environ.pop("CLAUDECODE", None)

# Shared utilities from channel_brain
sys.path.insert(0, str(Path(__file__).parent.parent / "channel_brain"))
from _claude import (
    preflight, call_claude_stdin, parse_json,
    load_config, load_progress, save_progress, cleanup_scratch,
)

# Optional embeddings
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False


# =============================================================================
# SEED INTERACTION CATEGORIES (fallback / merge with auto-discovered)
# =============================================================================

SEED_INTERACTION_TYPES = [
    {"name": "voice-quality",       "label": "Voice Quality Concerns",        "description": "Prospect questions/concerns about how natural or clear the AI voice sounds"},
    {"name": "memory-retention",    "label": "Memory & Info Retention",        "description": "Can it remember company info, past conversations, product details"},
    {"name": "human-likeness",      "label": "Human Likeness / Convincingness","description": "Will callers know it's AI? Can it pass as human? Does it handle pauses?"},
    {"name": "pricing-pushback",    "label": "Pricing & Cost Objections",      "description": "Too expensive, want to negotiate, compare to hiring a person"},
    {"name": "trust-credibility",   "label": "Trust & Credibility",            "description": "Skepticism, 'prove it works', ask for case studies / references"},
    {"name": "setup-complexity",    "label": "Setup & Integration Concerns",   "description": "How hard to set up, how long, what do they need to provide"},
    {"name": "edge-cases",          "label": "Edge Case Handling",             "description": "What if customer asks something weird, gets angry, speaks another language"},
    {"name": "opener-hook",         "label": "Opening & Hook",                 "description": "How salesperson opens the call, gets past gatekeeper, earns first 30s"},
    {"name": "close-advance",       "label": "Close & Advance",                "description": "How salesperson asks for next step, books demo, gets commitment"},
    {"name": "competitor-compare",  "label": "Competitor Comparisons",         "description": "Prospect mentions other AI tools or solutions they've seen/tried"},
    {"name": "misc-objection",      "label": "Other Objections",               "description": "Objections that don't fit above categories"},
]


# =============================================================================
# SWEEP 0 — INTERACTION TAXONOMY DISCOVERY
# =============================================================================

TAXONOMY_PROMPT = """You are analyzing transcripts of real sales calls (cold calls, live demos, sales calls) to discover the INTERACTION TYPES that come up.

You will receive:
1. Titles + info for every video in this folder.
2. Full transcript samples from {sample_n} random calls.

Your job: identify 10-20 specific INTERACTION CATEGORIES that appear in these calls.
An "interaction category" = a type of question, objection, hesitation, or exchange that repeats across calls.

Examples of good categories:
- "voice-quality-concerns" — prospect asks if the voice sounds robotic
- "pricing-pushback" — prospect says it's too expensive
- "human-likeness" — will my customers know it's AI?

Rules:
- Base categories on what ACTUALLY appears in these calls, not generic sales theory
- Name each with a lowercase-hyphenated slug
- Include a human-readable label
- 1-sentence description of what exchanges belong here
- 3 example verbatim phrases that would land in this category

Return ONLY raw JSON, no markdown fences:
{{
  "interaction_types": [
    {{
      "name": "slug-name",
      "label": "Human Label",
      "description": "what exchanges belong here",
      "examples": ["example phrase 1", "example phrase 2", "example phrase 3"]
    }}
  ]
}}"""


async def sweep0_taxonomy(cfg: dict, dry_run: bool = False) -> dict:
    output_dir    = Path(cfg["output_dir"])
    videos_dir    = Path(cfg["videos_dir"])
    taxonomy_path = output_dir / "taxonomy.json"
    sample_n      = int(cfg.get("taxonomy_sample_n", 8))

    output_dir.mkdir(parents=True, exist_ok=True)

    if taxonomy_path.exists():
        data = json.loads(taxonomy_path.read_text(encoding="utf-8"))
        types = data.get("interaction_types", [])
        print(f"  Sweep 0: taxonomy.json exists ({len(types)} types) — skipping. Delete to re-run.")
        return data

    folders = _get_video_folders(videos_dir, cfg.get("call_filter_keywords", []))
    print(f"  Sweep 0: {len(folders)} call videos found", flush=True)

    info_blocks = []
    for folder in folders:
        info_path = folder / "info.md"
        info = info_path.read_text(encoding="utf-8", errors="replace")[:300] if info_path.exists() else ""
        info_blocks.append(f"[{folder.name}]\n{info.strip()}")

    transcript_folders = [f for f in folders if (f / "transcript.txt").exists()]
    sampled = random.sample(transcript_folders, min(sample_n, len(transcript_folders)))
    samples = []
    for folder in sampled:
        t = (folder / "transcript.txt").read_text(encoding="utf-8", errors="replace")
        samples.append(f"=== {folder.name} ===\n{t[:5000].strip()}")

    print(f"  Sampled {len(samples)} call transcripts for taxonomy analysis", flush=True)

    if dry_run:
        result = {
            "interaction_types": SEED_INTERACTION_TYPES,
            "dry_run": True,
            "video_count": len(folders),
            "note": "seed types only — dry-run skipped LLM"
        }
        taxonomy_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

    await preflight()

    prompt = (
        TAXONOMY_PROMPT.format(sample_n=len(samples))
        + "\n\n--- ALL VIDEO INFO ---\n\n"
        + "\n\n".join(info_blocks)
        + "\n\n--- SAMPLE TRANSCRIPTS ---\n\n"
        + "\n\n".join(samples)
    )

    print("  Calling Claude for interaction taxonomy ...", flush=True)
    raw = await call_claude_stdin(prompt, label="s0-taxonomy")

    if raw:
        parsed = parse_json(raw)
        if parsed and isinstance(parsed, dict) and "interaction_types" in parsed:
            channel_types = parsed["interaction_types"]
            channel_names = {t["name"] for t in channel_types}
            merged = channel_types + [s for s in SEED_INTERACTION_TYPES if s["name"] not in channel_names]
            result = {
                "interaction_types": merged,
                "video_count": len(folders),
                "sample_count": len(samples),
                "discovered_count": len(channel_types),
                "seed_added": len(merged) - len(channel_types),
            }
            print(f"  Discovered {len(channel_types)} call-specific types + {len(merged)-len(channel_types)} seed fallbacks")
        else:
            print("  WARNING: parse failed — using seed types")
            result = {"interaction_types": SEED_INTERACTION_TYPES, "parse_error": True}
    else:
        print("  WARNING: LLM call failed — using seed types")
        result = {"interaction_types": SEED_INTERACTION_TYPES, "fallback": True}

    taxonomy_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"  Saved → {taxonomy_path}")
    return result


# =============================================================================
# SWEEP 1 — EXCHANGE PAIR EXTRACTION
# =============================================================================

EXTRACT_PROMPT = """Extract every verbatim EXCHANGE PAIR from this sales/cold call transcript.

IMPORTANT: This video has been pre-selected as a REAL CALL recording (cold call, live demo, or sales call).
Assume there ARE exchanges to extract. Look hard — a one-sided cold call still has the seller's lines,
a demo still has prospect reactions, a coaching replay still has the exchange being analyzed.

An exchange pair = [what prospect/gatekeeper says] + [what salesperson says back].
Also capture standalone opener lines and close/advance attempts.

RULES:
1. VERBATIM ONLY. Exact words spoken. No paraphrasing. No summarizing.
2. Capture BOTH sides when present: prospect_line AND salesperson_response.
3. If prospect asks a question → extract it + the response.
4. If prospect objects → extract the objection + the response.
5. If prospect shows interest/skepticism → extract the signal + what the seller does next.
6. Opener lines (first thing seller says to get attention) → type "opener-hook", prospect_line = "".
7. Close attempts (asking for next step / commitment) → type "close-advance".
8. Even if the call is one-sided (voicemail, monologue pitch) → extract the seller lines as openers.
9. interaction_type MUST be one of the provided slugs.
10. outcome: "advanced" (prospect engaged positively), "deflected" (concern addressed),
              "stalled" (no movement), "closed" (got commitment), "lost" (hung up/declined)
11. Return [] ONLY if the transcript is genuinely a tutorial/lecture with zero call interaction.

Return ONLY raw JSON, no markdown fences:
{{
  "exchanges": [
    {{
      "prospect_line": "verbatim prospect words (empty string if opener/close with no prospect input)",
      "salesperson_response": "verbatim salesperson words",
      "interaction_type": "slug-from-list",
      "outcome": "advanced|deflected|stalled|closed|lost",
      "context_note": "1 sentence: what stage of call, what led to this"
    }}
  ]
}}"""


CHUNK_TOKENS   = 4000   # tokens per Claude call (safe for subscription auth)
CHUNK_OVERLAP  = 400    # token overlap between chunks (preserves cross-boundary exchanges)
CHUNK_CHAR_CAP = 18000  # char threshold above which we chunk (short calls run as-is)


def _parse_exchanges(raw: str, valid_types: set, folder_name: str, source_title: str) -> list[dict]:
    parsed = parse_json(raw)
    if not parsed or not isinstance(parsed, dict) or "exchanges" not in parsed:
        return []
    results = []
    for ex in parsed["exchanges"]:
        sp = (ex.get("salesperson_response") or "").strip()
        if not sp:
            continue
        itype = ex.get("interaction_type", "misc-objection")
        if itype not in valid_types:
            itype = "misc-objection"
        results.append({
            "prospect_line":        (ex.get("prospect_line") or "").strip(),
            "salesperson_response": sp,
            "interaction_type":     itype,
            "outcome":              ex.get("outcome", "stalled"),
            "context_note":         (ex.get("context_note") or "").strip(),
            "source_folder":        folder_name,
            "source_video":         source_title,
        })
    return results


async def extract_video_exchanges(
    folder: Path,
    interaction_type_names: list[str],
    label: str,
) -> list[dict]:
    t_path = folder / "transcript.txt"
    if not t_path.exists():
        return []
    transcript = t_path.read_text(encoding="utf-8", errors="replace").strip()
    if len(transcript) < 200:
        return []

    info_path = folder / "info.md"
    info = info_path.read_text(encoding="utf-8", errors="replace")[:300] if info_path.exists() else ""
    source_title = info.split("\n")[0].strip() if info else folder.name
    valid_types  = set(interaction_type_names)
    types_str    = "\n".join(f"  - {t}" for t in interaction_type_names)
    header       = (
        EXTRACT_PROMPT
        + f"\n\nINTERACTION TYPE SLUGS (use exact):\n{types_str}"
        + f"\n\n--- VIDEO INFO ---\n{info.strip()}"
        + "\n\n--- TRANSCRIPT SEGMENT ---\n"
    )

    # Short transcripts: single call (fast, no chunking overhead)
    if len(transcript) <= CHUNK_CHAR_CAP:
        prompt = header + transcript
        raw = await call_claude_stdin(prompt, label=label)
        return _parse_exchanges(raw or "", valid_types, folder.name, source_title) if raw else []

    # Long transcripts (60-min cold calls etc): chunk to avoid exit 15
    chunks = _chunk_text(transcript, max_tokens=CHUNK_TOKENS, overlap=CHUNK_OVERLAP)
    print(f"(chunking {len(transcript):,} chars → {len(chunks)} segments)", end=" ", flush=True)

    all_results: list[dict] = []
    seen_pairs: set[tuple] = set()  # dedup exact duplicates across chunk boundaries

    for ci, chunk in enumerate(chunks):
        chunk_label = f"{label}-c{ci+1}"
        prompt = header + chunk
        raw = await call_claude_stdin(prompt, label=chunk_label)
        if not raw:
            continue
        chunk_results = _parse_exchanges(raw, valid_types, folder.name, source_title)
        for ex in chunk_results:
            key = (ex["prospect_line"][:80], ex["salesperson_response"][:80])
            if key not in seen_pairs:
                seen_pairs.add(key)
                all_results.append(ex)
        await asyncio.sleep(1)  # brief pause between chunks

    return all_results


async def sweep1_extract(
    cfg: dict,
    taxonomy: dict,
    limit: int | None = None,
    dry_run: bool = False,
) -> int:
    output_dir    = Path(cfg["output_dir"])
    videos_dir    = Path(cfg["videos_dir"])
    exchanges_dir = output_dir / "exchanges"
    exchanges_dir.mkdir(parents=True, exist_ok=True)

    type_names = [t["name"] for t in taxonomy.get("interaction_types", [])]
    if not type_names:
        print("  ERROR: taxonomy has no interaction types — run Sweep 0 first")
        return 0

    folders = _get_video_folders(videos_dir, cfg.get("call_filter_keywords", []))
    done_names = {f.stem for f in exchanges_dir.glob("*.jsonl")}
    todo = [f for f in folders if f.name not in done_names]

    print(
        f"  Sweep 1: {len(folders)} videos | {len(done_names)} done | {len(todo)} to extract",
        flush=True,
    )

    if limit:
        todo = todo[:limit]
        print(f"  Limited to first {limit}")

    if dry_run:
        print(f"  DRY RUN: would make {len(todo)} LLM calls")
        return 0

    if not todo:
        total = sum(
            sum(1 for line in f.read_text(encoding="utf-8").splitlines() if line.strip())
            for f in exchanges_dir.glob("*.jsonl")
        )
        print(f"  Nothing new. Total exchanges so far: {total}")
        return total

    progress = load_progress(output_dir)

    for i, folder in enumerate(todo, 1):
        print(f"  [{i}/{len(todo)}] {folder.name}", flush=True, end=" ")
        t0 = time.time()

        exchanges = await extract_video_exchanges(folder, type_names, label=f"s1-v{i}")
        elapsed = time.time() - t0

        jsonl_path = exchanges_dir / f"{folder.name}.jsonl"

        if not exchanges:
            print(f"→ 0 exchanges ({elapsed:.0f}s) [Claude found no exchange pairs — check transcript quality]")
            jsonl_path.write_text("", encoding="utf-8")
        else:
            lines = [json.dumps(e, ensure_ascii=False) for e in exchanges]
            jsonl_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"→ {len(exchanges)} exchanges ({elapsed:.0f}s)")

        progress.setdefault("sweep1_done", []).append(folder.name)
        save_progress(output_dir, progress)
        await asyncio.sleep(2)

    total = sum(
        sum(1 for line in f.read_text(encoding="utf-8").splitlines() if line.strip())
        for f in exchanges_dir.glob("*.jsonl")
    )
    print(f"  Sweep 1 done — {total} total exchanges")
    return total


# =============================================================================
# SWEEP 2 — CLUSTER EXCHANGE PAIRS
# =============================================================================

CLUSTER_PROMPT = """Group these {n} call exchanges by semantic equivalence.

Two exchanges belong in the same cluster if the PROSPECT is raising the same concern/question
using different words. (e.g. "does it sound natural?" and "will people know it's a robot?" = same cluster)

Rules:
- Every index 0 to {n_minus_1} must appear in EXACTLY ONE group
- Keep ALL variants — never collapse to a single "canonical" version
- Cluster by PROSPECT LINE similarity (or salesperson opener similarity for opener-type)
- Singletons (truly unique) get their own group of size 1
- "label": 5-10 word description of the concern/question this cluster covers

Return ONLY raw JSON, no markdown fences:
{{
  "groups": [
    {{
      "label": "description of what prospect concern this is",
      "items": [0, 4, 7],
      "representative_idx": 0
    }}
  ]
}}

EXCHANGES:
{items_text}"""


async def sweep2_cluster(cfg: dict, dry_run: bool = False) -> dict:
    output_dir    = Path(cfg["output_dir"])
    exchanges_dir = output_dir / "exchanges"
    clusters_path = output_dir / "clusters.json"
    cluster_mode  = cfg.get("cluster_mode", "llm")
    batch_size    = int(cfg.get("llm_batch_size", 25))
    threshold     = float(cfg.get("embedding_threshold", 0.82))

    if clusters_path.exists():
        data = json.loads(clusters_path.read_text(encoding="utf-8"))
        print(f"  Sweep 2: clusters.json exists ({data.get('cluster_count','?')} clusters) — skipping.")
        return data

    # Load all exchanges
    all_items: list[dict] = []
    for jf in sorted(exchanges_dir.glob("*.jsonl")):
        for line in jf.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line:
                try:
                    all_items.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    n = len(all_items)
    print(f"  Sweep 2: {n} exchanges loaded from {len(list(exchanges_dir.glob('*.jsonl')))} files")

    if not all_items:
        print("  No exchanges found — run Sweep 1 first")
        return {"clusters": [], "singletons": [], "cluster_count": 0, "total_items": 0}

    if dry_run:
        batches = (n + batch_size - 1) // batch_size
        print(f"  DRY RUN: {n} exchanges, ~{batches} LLM batches needed")
        return {}

    # Embedding pre-grouping (optional)
    emb_groups: list[list[int]] = []
    if cluster_mode in ("dual", "embedding") and EMBEDDINGS_AVAILABLE:
        print("  Sweep 2a: embedding pass ...", flush=True)
        try:
            texts = [
                (item.get("prospect_line") or item.get("salesperson_response") or "")
                for item in all_items
            ]
            model = SentenceTransformer("all-MiniLM-L6-v2")
            embs  = model.encode(texts, show_progress_bar=False, batch_size=64)
            norms = np.linalg.norm(embs, axis=1, keepdims=True)
            embs  = embs / np.maximum(norms, 1e-9)
            parent = list(range(n))

            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]; x = parent[x]
                return x

            def union(x, y):
                px, py = find(x), find(y)
                if px != py: parent[px] = py

            CHUNK = 256
            for i in range(0, n, CHUNK):
                chunk = embs[i:i + CHUNK]
                sims  = np.dot(chunk, embs.T)
                for ci, row in enumerate(sims):
                    ai = i + ci
                    for j in np.where(row >= threshold)[0]:
                        if int(j) > ai: union(ai, int(j))

            bmap: dict = defaultdict(list)
            for idx in range(n): bmap[find(idx)].append(idx)
            emb_groups = list(bmap.values())
            multi = sum(1 for g in emb_groups if len(g) > 1)
            print(f"  Embedding: {n} → {len(emb_groups)} groups ({multi} multi-member)")
        except Exception as exc:
            print(f"  WARNING: embedding failed ({exc}) — LLM-only")
            emb_groups = []

    # Build LLM batches
    if emb_groups:
        batches: list[list[int]] = []
        cur: list[int] = []
        for grp in sorted(emb_groups, key=len, reverse=True):
            if len(cur) + len(grp) > batch_size and cur:
                batches.append(cur); cur = []
            cur.extend(grp)
            if len(cur) >= batch_size:
                batches.append(cur); cur = []
        if cur: batches.append(cur)
    else:
        batches = [list(range(i, min(i + batch_size, n))) for i in range(0, n, batch_size)]

    # LLM clustering
    llm_groups: list[dict] = []
    if cluster_mode in ("dual", "llm"):
        print(f"  Sweep 2b: {len(batches)} LLM batches ...", flush=True)
        for bi, batch in enumerate(batches, 1):
            blen = len(batch)
            items_text = "\n".join(
                f"{li}. [{all_items[gi].get('interaction_type','')}] "
                f"PROSPECT: {all_items[gi].get('prospect_line','(opener)')[:120]}  "
                f"| SELLER: {all_items[gi].get('salesperson_response','')[:80]}"
                for li, gi in enumerate(batch)
            )
            prompt = CLUSTER_PROMPT.format(n=blen, n_minus_1=blen-1, items_text=items_text)
            t0 = time.time()
            raw = await call_claude_stdin(prompt, label=f"c-b{bi}")
            elapsed = time.time() - t0

            parsed = parse_json(raw) if raw else None
            covered = set()
            if parsed and isinstance(parsed, dict) and "groups" in parsed:
                for grp in parsed["groups"]:
                    local_items = [int(li) for li in grp.get("items", []) if int(li) < blen]
                    if not local_items: continue
                    rep_local = grp.get("representative_idx", local_items[0])
                    rep_global = batch[rep_local if isinstance(rep_local, int) and rep_local < blen else local_items[0]]
                    global_items = [batch[li] for li in local_items]
                    covered.update(local_items)
                    llm_groups.append({
                        "label":          grp.get("label", ""),
                        "items":          global_items,
                        "representative": all_items[rep_global].get("prospect_line") or all_items[rep_global].get("salesperson_response", ""),
                    })
            # Singletons for missed indices
            for li, gi in enumerate(batch):
                if li not in covered:
                    llm_groups.append({"label": "singleton", "items": [gi], "representative": ""})

            print(f"    batch {bi}/{len(batches)}: {len(batch)} → groups ({elapsed:.0f}s)", flush=True)
            await asyncio.sleep(1)

    # If embedding-only
    if not llm_groups and emb_groups:
        for grp in emb_groups:
            llm_groups.append({"label": "embedding-cluster", "items": grp, "representative": ""})

    # Build final clusters
    assigned: set[int] = set()
    final_clusters: list[dict] = []
    for grp in llm_groups:
        idxs = grp.get("items", [])
        if not idxs: continue
        cluster_items = [all_items[i] for i in idxs]
        itype = cluster_items[0].get("interaction_type", "misc-objection")
        final_clusters.append({
            "id":            f"c{len(final_clusters)+1:04d}",
            "label":         grp.get("label", ""),
            "representative": grp.get("representative", ""),
            "interaction_type": itype,
            "size":          len(cluster_items),
            "items":         cluster_items,
        })
        assigned.update(idxs)

    singletons = [all_items[i] for i in range(n) if i not in assigned]

    result = {
        "total_items":    n,
        "cluster_count":  len(final_clusters),
        "singleton_count": len(singletons),
        "clusters":       final_clusters,
        "singletons":     singletons,
    }
    clusters_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Sweep 2 done → {len(final_clusters)} clusters, {len(singletons)} singletons")
    return result


# =============================================================================
# SWEEP 3 — RENDER
# =============================================================================

def _slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\-]", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "misc"


def _format_exchange(ex: dict, show_outcome: bool = True) -> str:
    prospect  = ex.get("prospect_line", "").strip()
    response  = ex.get("salesperson_response", "").strip()
    context   = ex.get("context_note", "").strip()
    source    = ex.get("source_folder", "")
    outcome   = ex.get("outcome", "")
    lines = []
    if prospect:
        lines.append(f"**PROSPECT:** \"{prospect}\"")
    lines.append(f"**SELLER:** \"{response}\"")
    if show_outcome and outcome:
        lines.append(f"*outcome: {outcome}*")
    if context:
        lines.append(f"*({context})*")
    if source:
        lines.append(f"— `{source}`")
    return "\n".join(lines) + "\n"


def sweep3_render(cfg: dict) -> dict:
    output_dir    = Path(cfg["output_dir"])
    types_dir     = output_dir / "interaction-types"
    types_dir.mkdir(parents=True, exist_ok=True)

    clusters_path  = output_dir / "clusters.json"
    taxonomy_path  = output_dir / "taxonomy.json"
    master_path    = output_dir / "all_exchanges.md"
    index_path     = output_dir / "_call-index.md"

    if not clusters_path.exists():
        print(f"  ERROR: clusters.json not found. Run Sweep 2 first.")
        return {}

    clusters_data = json.loads(clusters_path.read_text(encoding="utf-8"))
    taxonomy_data = json.loads(taxonomy_path.read_text(encoding="utf-8")) if taxonomy_path.exists() else {}

    type_list  = taxonomy_data.get("interaction_types", [])
    type_order = [t["name"] for t in type_list]
    type_labels = {t["name"]: t["label"] for t in type_list}
    type_descs  = {t["name"]: t.get("description", "") for t in type_list}

    # Group by interaction_type
    by_type: dict[str, list[dict]] = defaultdict(list)
    for cluster in clusters_data.get("clusters", []):
        itype = cluster.get("interaction_type") or "misc-objection"
        by_type[itype].append(cluster)

    singleton_by_type: dict[str, list[dict]] = defaultdict(list)
    for item in clusters_data.get("singletons", []):
        itype = item.get("interaction_type") or "misc-objection"
        singleton_by_type[itype].append(item)

    all_types_data = set(by_type.keys()) | set(singleton_by_type.keys())
    ordered = [t for t in type_order if t in all_types_data]
    extras  = sorted(all_types_data - set(ordered))
    all_types = ordered + extras

    project_name   = cfg.get("project_name", "Call Miner")
    total_items    = clusters_data.get("total_items", "?")
    cluster_count  = clusters_data.get("cluster_count", "?")
    singleton_count = clusters_data.get("singleton_count", "?")

    master_parts = [
        f"# {project_name} — Call Exchange Library\n\n",
        f"> {total_items} total exchanges | {cluster_count} clusters | {singleton_count} singletons\n\n",
    ]

    written: list[tuple] = []

    for itype in all_types:
        label    = type_labels.get(itype, itype.replace("-", " ").title())
        desc     = type_descs.get(itype, "")
        clusters = sorted(by_type.get(itype, []), key=lambda c: c.get("size", 1), reverse=True)
        singletons = singleton_by_type.get(itype, [])
        if not clusters and not singletons:
            continue

        section_parts = [f"# {label}\n\n"]
        if desc:
            section_parts.append(f"*{desc}*\n\n")

        for cluster in clusters:
            clabel = (cluster.get("label") or "").strip()
            items  = cluster.get("items", [])
            size   = cluster.get("size", len(items))
            rep    = (cluster.get("representative") or "")[:80]

            if clabel and clabel not in ("singleton", "batch_failed", "parse_failed", "embedding-cluster"):
                section_parts.append(f"## {clabel}  *(×{size} variants)*\n\n")
            elif size > 1 and rep:
                section_parts.append(f"## \"{rep}\"...  *(×{size} variants)*\n\n")

            for ex in items:
                section_parts.append(_format_exchange(ex))
                section_parts.append("\n")
            section_parts.append("---\n\n")

        if singletons:
            section_parts.append("## Unique Exchanges\n\n")
            for ex in singletons:
                section_parts.append(_format_exchange(ex))
                section_parts.append("\n")

        section_text = "".join(section_parts)
        slug = _slugify(itype)
        (types_dir / f"{slug}.md").write_text(section_text, encoding="utf-8")
        written.append((itype, label, slug, len(clusters) + len(singletons)))

        master_parts.append(f"## {label}\n\n")
        body = section_text.split("\n", 1)[1].lstrip("\n") if "\n" in section_text else ""
        master_parts.append(body)
        master_parts.append("\n---\n\n")

    master_path.write_text("".join(master_parts), encoding="utf-8")

    idx_lines = [
        f"# {project_name} — Call Index\n\n",
        f"| Stat | Value |\n|------|-------|\n",
        f"| Total exchanges | {total_items} |\n",
        f"| Cluster groups  | {cluster_count} |\n",
        f"| Singletons      | {singleton_count} |\n",
        f"| Interaction types | {len(written)} |\n\n",
        "## Interaction Types\n\n",
    ]
    for itype, label, slug, count in written:
        idx_lines.append(f"- [{label}](interaction-types/{slug}.md) — {count} groups\n")
    idx_lines.append(f"\n[Full exchange library](all_exchanges.md)\n")
    index_path.write_text("".join(idx_lines), encoding="utf-8")

    print(f"  Sweep 3 done: {len(written)} interaction-type files")
    print(f"  Master: {master_path}")
    print(f"  Index:  {index_path}")
    return {"sections": len(written), "master": str(master_path)}


# =============================================================================
# HELPERS
# =============================================================================

def _get_video_folders(videos_dir: Path, filter_keywords: list[str]) -> list[Path]:
    if not videos_dir.exists():
        print(f"FATAL: videos_dir not found: {videos_dir}")
        sys.exit(1)
    folders = [p for p in videos_dir.iterdir() if p.is_dir() and (p / "transcript.txt").exists()]
    if filter_keywords:
        kw = [k.lower() for k in filter_keywords]
        folders = [f for f in folders if any(k in f.name.lower() for k in kw)]
        print(f"  Filter '{filter_keywords}' → {len(folders)} matching folders", flush=True)
    folders.sort(key=lambda p: p.stat().st_mtime)
    return folders


# =============================================================================
# BANNER
# =============================================================================

def print_banner(cfg: dict) -> None:
    w = 68
    kw = cfg.get("call_filter_keywords", [])
    filter_str = f"filter={kw}" if kw else "no filter (all videos)"
    print("─" * w)
    print(f"  Call Miner  —  {cfg.get('project_name', 'unnamed')}")
    print(f"  Videos:  {cfg.get('videos_dir', '?')}")
    print(f"  Output:  {cfg.get('output_dir', '?')}")
    print(f"  {filter_str}")
    print("─" * w)


# =============================================================================
# ORCHESTRATOR
# =============================================================================

async def main() -> None:
    ap = argparse.ArgumentParser(description="Call Miner — exchange pair extractor for sales bot training")
    ap.add_argument("--config",  required=True)
    ap.add_argument("--sweep",   type=int, default=None, choices=[0, 1, 2, 3])
    ap.add_argument("--limit",   type=int, default=None, help="Limit Sweep 1 to first N videos")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--reset",   action="store_true", help="Wipe output and start over")
    args = ap.parse_args()

    cfg        = load_config(args.config)
    output_dir = Path(cfg["output_dir"])

    if args.reset:
        if output_dir.exists():
            shutil.rmtree(output_dir)
            print(f"Reset: wiped {output_dir}")
        output_dir.mkdir(parents=True, exist_ok=True)

    print_banner(cfg)
    full_run = args.sweep is None

    try:
        taxonomy: dict = {}

        # ── Sweep 0 ────────────────────────────────────────────────────────────
        if full_run or args.sweep == 0:
            print("\n[SWEEP 0]  Interaction Taxonomy Discovery")
            taxonomy = await sweep0_taxonomy(cfg, dry_run=args.dry_run)
            types = taxonomy.get("interaction_types", [])
            print(f"  → {len(types)} interaction types:")
            for t in types:
                print(f"      {t['name']}")

            gate_flag = output_dir / "_sweep0_gate_passed"
            if (
                full_run and not args.dry_run
                and cfg.get("taxonomy_gate", True)
                and not gate_flag.exists()
            ):
                taxonomy_path = output_dir / "taxonomy.json"
                print()
                print("  ┌─ TAXONOMY GATE ───────────────────────────────────────────────────────────┐")
                print("  │  Sweep 0 complete. Open taxonomy.json, review the interaction types above. │")
                print("  │  You can ADD, REMOVE, or RENAME types before extraction starts.           │")
                print("  │  Each type becomes a section in your final exchange library.              │")
                print(f"  │  File: {str(taxonomy_path)}  │")
                print("  │  Press Enter when ready to begin extraction (Sweep 1).                   │")
                print("  └───────────────────────────────────────────────────────────────────────────┘")
                input("  > ")
                gate_flag.write_text("passed", encoding="utf-8")
                if taxonomy_path.exists():
                    taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
        else:
            taxonomy_path = output_dir / "taxonomy.json"
            if taxonomy_path.exists():
                taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
            else:
                print("ERROR: taxonomy.json not found. Run --sweep 0 first.")
                sys.exit(1)

        # ── Sweep 1 ────────────────────────────────────────────────────────────
        if full_run or args.sweep == 1:
            print("\n[SWEEP 1]  Exchange Extraction")
            count = await sweep1_extract(cfg, taxonomy, limit=args.limit, dry_run=args.dry_run)
            if not args.dry_run:
                print(f"  → {count} total exchanges")

        # ── Sweep 2 ────────────────────────────────────────────────────────────
        if full_run or args.sweep == 2:
            print("\n[SWEEP 2]  Clustering")
            clusters = await sweep2_cluster(cfg, dry_run=args.dry_run)
            if not args.dry_run and clusters:
                print(f"  → {clusters.get('cluster_count',0)} clusters, {clusters.get('singleton_count',0)} singletons")

        # ── Sweep 3 ────────────────────────────────────────────────────────────
        if full_run or args.sweep == 3:
            print("\n[SWEEP 3]  Render")
            result = sweep3_render(cfg)
            if result:
                print(f"  → {result.get('sections',0)} interaction-type files")

        print()
        print("─" * 68)
        if args.dry_run:
            print("  DRY RUN complete")
        else:
            print(f"  DONE  —  output: {output_dir}")
            master = output_dir / "all_exchanges.md"
            if master.exists():
                print(f"  Exchange library: {master}  ({master.stat().st_size // 1024} KB)")
        print("─" * 68)

    finally:
        cleanup_scratch()


if __name__ == "__main__":
    import shutil
    asyncio.run(main())
