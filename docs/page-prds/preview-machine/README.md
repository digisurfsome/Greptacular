# Preview Machine — AutoForge Integration PRD

> Cold-outreach machine: scrape local businesses → audit their websites → generate a
> personalized static preview site per business → deploy to Cloudflare Pages → blast
> the links via GSA. Full background: `HANDOFF.md` in this folder (read it first).

## Status (June 2026)

| Piece | Where | State |
|---|---|---|
| `biz_pull.py`, `site_age.py`, `sitegen.py`, `template.html`, `assets/` | **Tim's machine only — NOT in this repo yet** | Working, smoke-tested in the claude.ai session |
| Copywriter (subscription-billed copy JSONs) | `scripts/preview_machine/copywriter.py` | **Built. Selftest passes.** |
| sitegen `--copydir` mode | Patch spec below — apply when the 4 files land in the repo | Not applied (file not in repo) |
| Pitch column, multi-template, multi-niche | Roadmap (HANDOFF.md §6) | Not built — by design |

**⚠️ BLOCKER FOR FULL INTEGRATION:** the four pipeline files must be added to this repo
(suggested home: `scripts/preview_machine/`). Until then, run `copywriter.py` from this
repo and the four files from their current folder — the copy cache directory is the only
interface between them.

## The new orchestration (copy-cache pattern)

```
biz_pull.py  →  site_age.py  →  copywriter.py (SUBSCRIPTION)  →  sitegen.py --copydir copy/  →  wrangler deploy
```

Copywriting is decoupled from billing: subscription agent (copywriter.py), metered API
(sitegen's existing `claude_copy()`), or `--offline` templates all feed the same renderer.

### Running the copywriter

```
cd <repo-root>
python scripts/preview_machine/copywriter.py site_audit.csv --outdir copy
```

- Defaults: model `sonnet` (`claude-sonnet-4-6`), batch size 10, verdicts
  `STRONG TARGET,WORTH A LOOK`. Use `--model haiku`, `--verdicts all`, `--limit N` as needed.
- **Resumable:** existing `copy/<slug>.json` files are never regenerated. When a
  subscription rate limit kills a run, just re-run the same command later.
- **Liability lint built in:** any generated copy containing exclamation marks,
  licensing/insurance/certification/award/guarantee claims, invented "N years", or
  "look no further" is rejected and retried next run. (These are legal rules — see
  HANDOFF.md §5.)
- Writes `copy/manifest.json` (business name → slug) for slug-mismatch detection.
- `--selftest` is fully offline.

### ⚠️ Honest caveat for Tim (do not bury)

Subscription usage is included but **rate-limited, not infinite**. Thousands of sites in
one sitting WILL hit session/usage caps on the $100 plan. The workflow is built for this:
batch, hit the cap, re-run later — already-written JSONs are skipped. For genuinely huge
runs, sitegen's existing API path is the overflow valve (Haiku cuts cost ~4x vs Sonnet).

## sitegen.py `--copydir` patch spec (apply when sitegen.py is in the repo)

Add a mode; **remove nothing** (`--offline` and the API path stay as fallbacks):

1. New CLI arg `--copydir <dir>`.
2. Per row, resolve copy in this order:
   a. `<copydir>/<slug>.json` using **sitegen's own slug function** for `<slug>`;
   b. if missing, look the business name up in `<copydir>/manifest.json` to get the
      copywriter's slug, then load that file (covers slug-algorithm drift —
      copywriter.py's `slugify()` is lowercase + non-alphanumeric→hyphen);
   c. if still missing, fall back to `offline_copy()` (never the API in this mode).
3. The JSON keys map 1:1 onto the existing copy dict `claude_copy()` returns — same
   contract (HANDOFF.md §5). No template changes.
4. All hard constraints from HANDOFF.md §7 still hold: token set, `../assets/` paths,
   Excel phone unwrap, all existing CLI modes and selftests must still pass.

## Future AutoForge integration (phase 2 — not built)

When this becomes a real AutoForge workflow/page, follow `.claude/rules/new-page-standards.md`:
router `server/routers/preview_machine.py`, service `server/services/preview_machine_service.py`,
page `ui/src/pages/PreviewMachinePage.tsx`. The service should shell the four pipeline
stages and call the copywriter logic via the same SDK pattern
(`server/services/yt_processor.py::_call_via_sdk` — the 3-bug-fixed reference). A
"market" (niche × city) is the unit of work; dedupe on `domain` across city radii.

Roadmap items (HANDOFF.md §6): per-business `pitch` key in the same generation pass
(respect BLOCKED/PARKED verdict rules), multi-template rotation, custom domain per niche.
