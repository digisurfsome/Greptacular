# Video Template Build Workflow

> Companion to `commercial-playbook.md`. Playbook = creative spec (what). This doc = build recipe (how).
> Use this as the step-by-step when cranking a new template.

---

## 0. Inputs Needed Before Build Starts

| Input | Source | Format |
|-------|--------|--------|
| Industry name | User choice | string (e.g. "plumbing") |
| Hook line | Written once per template | 3-5 sec voiceover + text card |
| 15 Slot A options (Wrong Tool) | Playbook + brainstorm | list of prop + action descriptions |
| 15 Slot B options (Rationale) | Playbook + brainstorm | list of quoted lines |
| 15 Slot C options (Escalation) | Playbook + brainstorm | list of visual cues |
| 15 Slot D options (Destruction) | Playbook + brainstorm | list of disaster effects |
| Hero CTA line | Brand-level fixed | 1 sentence + phone/URL |
| Brand color palette | Brand-level fixed | 3-5 hex codes |
| Hero PNG | Generated ONCE via Nano Banana / Gemini | transparent PNG |
| Villain PNG | Generated ONCE via Nano Banana / Gemini | transparent PNG |

Build template ONLY when all 8 rows filled. Missing any = half-built template.

---

## 1. Template Folder Layout

Every template = one folder. Self-contained.

```
video-templates/
  {industry}-{format-name}/
    template.yaml              ← master config (slots, timing, colors)
    hook/
      hook.html                ← hyperframes beat (fixed opener)
      voice.txt                ← hook line for TTS
    slot-a-wrong-tool/
      01-spare-tire.html
      02-swatch-bands.html
      ... (15 variations)
      voice-lines.json         ← 15 matching VO lines
    slot-b-rationale/
      01-rolling-updates.html
      ... (15)
      voice-lines.json
    slot-c-escalation/
      01-spinning.html
      ... (15)
      voice-lines.json
    slot-d-destruction/
      01-kinetic.html
      02-explosion.html
      ... (15)
      voice-lines.json
    hero-cta/
      cta.html                 ← fixed reveal + CTA
      voice.txt
    assets/
      hero.png
      villain.png
      logo-slot.png            ← replaced per business
      bg-patterns/
    render.py                  ← stitches one render given slot picks
    README.md                  ← template notes, samples
```

---

## 2. template.yaml Schema

```yaml
template_id: plumbing-hardware-hack
version: 1.0
industry: plumbing
format: roadrunner-chaos
duration_sec: 32
resolution: 1080x1920    # vertical for socials
fps: 30

beats:
  - id: hook
    seconds: 0-4
    type: fixed
    source: hook/hook.html
    voice: hook/voice.txt

  - id: slot-a
    seconds: 4-10
    type: random
    source_dir: slot-a-wrong-tool/
    variations: 15

  - id: slot-b
    seconds: 10-16
    type: random
    source_dir: slot-b-rationale/
    variations: 15

  - id: slot-c
    seconds: 16-22
    type: random
    source_dir: slot-c-escalation/
    variations: 15

  - id: slot-d
    seconds: 22-28
    type: random
    source_dir: slot-d-destruction/
    variations: 15

  - id: hero-cta
    seconds: 28-32
    type: fixed
    source: hero-cta/cta.html
    voice: hero-cta/voice.txt
    business_data_injected: true    # biz name, phone, logo

colors:
  primary: "#1E88E5"
  accent: "#FFD600"
  danger: "#E53935"
  bg: "#0A0A0A"

voice:
  tts_engine: edge-tts
  voice_id: en-US-GuyNeural
  speed: 1.0

business_data_fields:
  - business_name
  - phone
  - city
  - logo_url
  - website
  - seo_rank       # optional if Data Shock family
  - competitor_list # optional if Data Shock family
```

---

## 3. Build Order (Per Template)

Run in order. Each step independently verifiable.

| # | Step | Tool | Output | Time |
|---|------|------|--------|------|
| 1 | Fill template.yaml | editor | config file | 10 min manual |
| 2 | Generate hero + villain PNGs | Nano Banana / Gemini | 2 transparent PNGs | ~5 min |
| 3 | Build hook.html beat | hyperframes (+ Claude) | 1 HTML beat | ~5 min agent |
| 4 | Build hero-cta.html beat | hyperframes (+ Claude) | 1 HTML beat w/ data slots | ~5 min agent |
| 5 | Build 15 Slot A beats | hyperframes (+ Claude, batch) | 15 HTML | ~20 min agent |
| 6 | Build 15 Slot B beats | hyperframes (+ Claude, batch) | 15 HTML | ~20 min agent |
| 7 | Build 15 Slot C beats | hyperframes (+ Claude, batch) | 15 HTML | ~20 min agent |
| 8 | Build 15 Slot D beats | hyperframes (+ Claude, batch) | 15 HTML | ~20 min agent |
| 9 | Write voice-lines.json for all slots | Claude | JSON files | ~10 min |
| 10 | Build render.py | Claude | stitcher script | ~10 min |
| 11 | Smoke-test render w/ 1 slot pick | render.py | 1 MP4 | ~2 min |
| 12 | Render 10 random combos | render.py batch | 10 MP4 | ~10 min |
| 13 | Review quality, fix weak slots | manual + iterate | polished template | variable |

**Total first template: ~2-3 hrs real time, ~200-300k tokens.**
**Second template onward (swap slots, reuse infra): ~30-45 min.**

---

## 4. render.py Contract

Single responsibility: given template + biz data + slot picks, output final MP4.

```python
# CLI:
python render.py \
  --template plumbing-hardware-hack \
  --business business_data.json \
  --slots '{"a": 3, "b": 7, "c": 12, "d": 1}' \
  --output renders/acme-plumbing-001.mp4

# OR random:
python render.py \
  --template plumbing-hardware-hack \
  --business business_data.json \
  --random-slots \
  --seed 42 \
  --output renders/acme-plumbing-001.mp4
```

Pipeline inside render.py:
1. Parse template.yaml
2. Load biz data JSON
3. Pick slot HTML files (random or explicit)
4. Inject biz data into hero-cta.html (name, phone, logo)
5. Generate TTS for all voice lines (Edge-TTS free)
6. Render each HTML beat to MP4 via hyperframes
7. ffmpeg concat all 6 beats
8. ffmpeg overlay audio track
9. ffmpeg burn subtitles (optional)
10. Write final MP4 to output

---

## 5. Slot Variation Rules (Anti-Broken Combos)

Not all 15×15×15×15 = 50,625 combos will look right. Some rules to prevent garbage:

| Rule | Why |
|------|-----|
| Slot A + Slot B must match **mixing format** (Logic Leap, Medical, Safety, Vintage, Military) | Otherwise rationale doesn't fit tool |
| Slot C escalation must reference Slot A tool visually | Otherwise no continuity |
| Slot D destruction must acknowledge Slot A prop | Payoff must tie to setup |

Tag each slot entry w/ `mixing_format` field. Render.py enforces match. Reduces usable combos from 50,625 → ~15,000 still massively scalable.

---

## 6. Business Data Injection

Only hero-cta beat uses biz data. Template slots (A/B/C/D) = purely creative, no biz data.

Injection happens via hyperframes variable substitution:

```html
<!-- hero-cta.html excerpt -->
<div class="cta-card">
  <img src="{{logo_url}}" class="biz-logo">
  <h1>{{business_name}}</h1>
  <p class="cta-line">Don't DIY. Call {{phone}}</p>
  <p class="location">Serving {{city}}</p>
</div>
```

```json
// business_data.json
{
  "business_name": "Joe's Plumbing",
  "phone": "555-0199",
  "city": "Denver",
  "logo_url": "file://./assets/joes-logo.png",
  "website": "joesplumbing.com"
}
```

---

## 7. Data Shock Family (Different Workflow)

For Family C (SEO pitch videos), workflow changes:

| Beat | Data-driven? |
|------|------|
| Hook | fixed |
| Biz intro | YES — name + logo |
| Problem data | YES — SEO rank, keyword |
| Competitor data | YES — competitor name + revenue |
| Gap visualization | YES — derived chart |
| Hero CTA | YES — your phone |

No destruction/chaos. Serious tone. Bar charts. Pie charts. Map overlays.

Same folder structure but different beat list in template.yaml. Same render.py, different template config. This unlocks the "automated SEO review video" idea without needing the loom/browser-record system.

---

## 8. Template Production Metrics (Track These)

| Metric | Target |
|--------|--------|
| First template build time | < 3 hrs |
| Second template build time | < 1 hr |
| Render time per video | < 60 sec |
| Storage per template | < 500 MB |
| Tokens per template build | < 400k |
| Smoke test pass rate | 100% (1 render works) |
| Random 10 combo pass rate | > 90% (9 of 10 look right) |

If ANY metric blown, stop and fix infra before cranking more templates.

---

## 9. Checklist — Template Ready to Ship

- [ ] template.yaml validated
- [ ] All 6 beat types render individually
- [ ] 10 random renders viewed, 9+ pass visual QA
- [ ] TTS voice sounds consistent across beats
- [ ] biz data injection tested w/ 3 different businesses
- [ ] File sizes reasonable (final MP4 < 20 MB)
- [ ] Captions/subtitles legible
- [ ] Hero PNG + villain PNG look consistent across slots
- [ ] Brand colors applied uniformly
- [ ] README.md written (notes, samples, known issues)
- [ ] Committed to repo

---

## 10. Next Templates (Post-First Plumbing Template)

After plumbing Hardware Hack works:

1. **HVAC Hardware Hack** — 80% asset reuse (swap prop library + villain)
2. **Roofing Hardware Hack** — 80% asset reuse
3. **Auto Repair Hardware Hack** — 70% asset reuse
4. **Plumbing Data Shock** (SEO pitch) — new format, plumbing industry
5. **Plumbing Testimonial Carousel** — Family B

Sequencing = highest asset-reuse first. Gets catalog deep fast.
