# Preview Machine — AutoForge Integration PRD

> Cold-outreach machine: scrape local businesses → audit their websites → generate a
> personalized static preview site per business → deploy to Cloudflare Pages → blast
> the links via GSA. Full background: `HANDOFF.md` in this folder (read it first).

## Status (June 2026 — system integrated)

Everything lives in `scripts/preview_machine/`. Run order doc: `README_RUN_ORDER.md` there.

| Piece | Where | State |
|---|---|---|
| `gsa_filter.py`, `site_age.py`, `sitegen.py`, `template.html` | `scripts/preview_machine/` | **In repo. All selftests pass.** |
| Copywriter (subscription-billed copy JSONs) | `scripts/preview_machine/copywriter.py` | **Built. Selftest passes.** |
| sitegen `--copydir` mode | Applied to `scripts/preview_machine/sitegen.py` | **Done — functional test green** (cached copy used, fallback works, no unfilled tokens, phone unwrap intact) |
| `biz_pull.py` | **Still only on Tim's machine** | Not uploaded yet — drop it into `scripts/preview_machine/` |
| `assets/` images (ba1.jpg, ba2.jpg, hero.jpg) | **Tim's machine** | Images can't transfer through chat — copy the files into `scripts/preview_machine/assets/` |
| Pitch column, multi-template, multi-niche | Roadmap (HANDOFF.md §6) | Not built — by design |

`scripts/preview_machine/.gitignore` keeps run artifacts (previews/, copy/, *.csv,
assets images) out of git.

## The orchestration (copy-cache pattern)

```
biz_pull.py  →  gsa_filter.py  →  site_age.py (on _gsa_ready_)  →  copywriter.py (SUBSCRIPTION)  →  sitegen.py --copydir copy/  →  wrangler deploy
```

`gsa_filter.py` (new stage, between pull and audit) pre-screens which sites GSA can
actually deliver a contact-form message to — blocked ones are parked for cold email
instead of getting preview sites built for nothing.

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

## sitegen.py `--copydir` mode (APPLIED)

Implemented exactly as specced; **nothing removed** (`--offline` and the API path stay):

1. CLI arg `--copydir <dir>`.
2. Per row, copy resolves in this order:
   a. `<copydir>/<slug>.json` using sitegen's own slug function;
   b. if missing, business-name lookup in `<copydir>/manifest.json` (covers
      slug-algorithm drift between copywriter and sitegen);
   c. if still missing, `offline_copy()` fallback — never the API in this mode —
      and a summary NOTE tells you to re-run copywriter.py.
3. JSON keys map 1:1 onto the `claude_copy()` contract. No template changes.
4. Hard constraints (HANDOFF.md §7) verified: no unfilled tokens, `../assets/` paths
   untouched, Excel phone unwrap works, `--offline` and `--selftest` still pass.

## Future AutoForge integration (phase 2 — not built)

When this becomes a real AutoForge workflow/page, follow `.claude/rules/new-page-standards.md`:
router `server/routers/preview_machine.py`, service `server/services/preview_machine_service.py`,
page `ui/src/pages/PreviewMachinePage.tsx`. The service should shell the four pipeline
stages and call the copywriter logic via the same SDK pattern
(`server/services/yt_processor.py::_call_via_sdk` — the 3-bug-fixed reference). A
"market" (niche × city) is the unit of work; dedupe on `domain` across city radii.

Roadmap items (HANDOFF.md §6): per-business `pitch` key in the same generation pass
(respect BLOCKED/PARKED verdict rules), multi-template rotation, custom domain per niche.
