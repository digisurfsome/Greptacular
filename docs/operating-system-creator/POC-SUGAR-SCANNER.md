# POC #8: Sugar Scanner — Pipeline Test

> **Domain:** Health/food tech, mobile-first, real-time in-store use
> **Why this tests the framework:** First mobile app with camera input, real-time processing, offline needs, and physical-world context (user is standing in a grocery aisle). All previous POCs were backend automations.

---

## Stage 0: Process Capture

**Raw process:** User is in a grocery store. They pick up a product, open the app on their phone, point the camera at the nutrition label. The app captures the image, extracts all text via OCR, parses out ingredients, nutritional values, and additives. It looks up each ingredient against a database of known problematic additives (artificial sweeteners, HFCS, excessive sodium, artificial colors, preservatives). It generates a health score (0-100) with color coding and specific warnings. The result is saved to the user's scan history. If a previously scanned product later gets recalled or reformulated, the user gets a push notification.

**Process identity:**
- **Name:** Sugar Scanner
- **Trigger:** User points phone camera at a nutrition label (manual, on-demand)
- **Frequency:** 5-20 scans per shopping trip, 1-3 trips per week
- **Duration per run:** Must complete in under 3 seconds (user is standing in aisle)
- **Items per run:** 1 product per scan

**Data endpoints:**
- **Input:** Phone camera image of nutrition label
- **Output:** Health score + ingredient warnings displayed on phone screen
- **Storage:** User's scan history (per-account)

**What breaks:**
- Bad lighting / blurry photos → OCR fails
- Unusual label formats (foreign products, handwritten deli labels)
- Ingredients not in the database
- No cell signal in store → can't reach server
- User scans non-food items by accident

**Tools in use:** None currently — this is a new system

---

## Stage 1: 6-Step Mapping

| Pattern | Sugar Scanner |
|---------|--------------|
| **INPUT** | Camera image of nutrition label (JPEG/PNG, variable quality) |
| **PROCESS** | OCR → Parse → Lookup → Score → Warn |
| **OUTPUT** | Health score (0-100), color badge, ingredient warnings list |
| **STATE** | scan_history table: product, score, ingredients, timestamp, user_id |
| **NOTIFY** | Push notification on product recall/reformulation |
| **SCHEDULE** | On-demand (user-triggered), recall check runs daily batch |

**Multi-level check (Gap #1):** YES — two levels:
1. **Real-time scan pipeline** (user-triggered, must be fast)
2. **Background recall monitor** (daily batch, checks all previously scanned products against recall databases)

These are independent — the scan works without the recall monitor, and the recall monitor works on historical data.

---

## Stage 2: Step Decomposition

### Step 1: Image Capture
- **Input:** Phone camera pointed at nutrition label
- **Output:** JPEG image (1-5MB)
- **Decisions:** Is the image sharp enough? Is there a label in frame?
- **Error:** Blurry image, no label detected, wrong orientation
- **Repeats (Gap #2):** No — one image per scan (but user may retry if blurry)
- **Time:** <1 second

### Step 2: OCR Extraction
- **Input:** JPEG image
- **Output:** Raw text string of everything on the label
- **Decisions:** Confidence threshold — is the OCR reliable enough to proceed?
- **Error:** Low confidence OCR, partial text extraction, foreign language
- **Time:** 0.5-1.5 seconds

### Step 3: Label Parsing
- **Input:** Raw OCR text
- **Output:** Structured data: { ingredients: [], nutrition_facts: { calories, fat, sodium, sugar, ... }, serving_size, allergens }
- **Decisions:** Which section is ingredients vs nutrition facts? Handle variations in label format
- **Error:** Can't identify sections, unusual format, missing data
- **Extensible options (Gap #3):** YES — label formats vary by country (US FDA vs EU vs other)
- **Time:** 0.3-0.5 seconds

### Step 4: Ingredient Lookup
- **Input:** Parsed ingredient list
- **Output:** Each ingredient tagged: { name, category, risk_level, warnings }
- **Decisions:** Fuzzy matching (ingredient names vary — "high fructose corn syrup" vs "HFCS" vs "glucose-fructose syrup")
- **Error:** Unknown ingredient, ambiguous match
- **Presets (Gap #4):** YES — common ingredient aliases should be pre-mapped
- **Time:** 0.2-0.5 seconds

### Step 5: Health Scoring
- **Input:** Tagged ingredients + nutrition facts
- **Output:** Score 0-100, color badge (green/yellow/red), warning list
- **Decisions:** Scoring algorithm (weighted by: sugar content, additive count, sodium, artificial ingredients)
- **Error:** Incomplete data → partial score with confidence indicator
- **Batch merge (Gap #5):** Could compare multiple scanned products side-by-side
- **Time:** <0.1 seconds

### Step 6: Result Display & Storage
- **Input:** Score + warnings
- **Output:** Rendered card on phone screen, saved to scan_history
- **Decisions:** None — pure rendering and storage
- **Error:** Storage failure (offline mode needed)
- **Time:** <0.5 seconds

### Step 7: Recall Monitor (Background)
- **Input:** All products in scan_history
- **Output:** Push notifications for recalls/reformulations
- **Decisions:** Match product to recall database entry
- **Error:** False positive match, notification delivery failure
- **Time:** Runs daily, batch

**MVP Step:** Steps 1-5 (scan → score). Storage and recall monitor come later.

---

## Early Gap Analysis (after Stage 2)

Quick scan for showstoppers:
- **OCR API needed** — which one? Google Vision, Apple's on-device OCR, Tesseract?
- **Ingredient database** — does a public API exist or do we build our own?
- **Offline mode** — if OCR requires a server, no signal = no scan. SHOWSTOPPER for in-store use.
- **Legal** — are we making health claims? FDA implications?

---

## Stage 3: Automation Classification

| Step | Type | Detail |
|------|------|--------|
| Image Capture | **Human + Device** | User points camera, device captures |
| OCR Extraction | **External API** | Google Cloud Vision API or Apple Vision framework |
| Label Parsing | **AI-driven** | Claude parses raw OCR text into structured format |
| Ingredient Lookup | **Deterministic** | Database lookup with fuzzy matching |
| Health Scoring | **Deterministic** | Weighted algorithm, no AI needed |
| Result Display | **Code** | Frontend rendering |
| Recall Monitor | **Deterministic + External API** | FDA recall API + matching logic |

**Prompt skeleton for Label Parsing (Gap #10):**
```
Task: Parse this nutrition label OCR text into structured data.
Input: Raw OCR text from a food product label.
Output: JSON with: ingredients (array), nutrition_facts (object with calories, fat, sodium, sugar, protein, fiber, serving_size), allergens (array).
Rules: Handle OCR errors gracefully. If a value is unclear, include it with confidence: "low".
Model: Claude Haiku (fast, cheap)
Cost: ~$0.001 per parse
```

---

## Stage 4: Environment Setup

**API Keys:**

| Service | Key Type | Cost | How to Get |
|---------|----------|------|-----------|
| Google Cloud Vision | API key | $1.50/1000 images | Google Cloud Console → Vision API → Enable → Create credentials |
| Claude API (Haiku) | API key | ~$0.001/parse | Anthropic Console → API Keys |
| FDA Recall API | None needed | Free | Open API, no auth |
| Push notification service | API key | Free tier usually enough | Firebase Cloud Messaging |

**Dependencies:**
- Runtime: Node.js 20+ (server), React Native or Flutter (mobile)
- OCR: Google Cloud Vision SDK or @google-cloud/vision
- Database: PostgreSQL (users, scan_history, ingredients)
- Push: Firebase Admin SDK

**Cost per run:** ~$0.0025 per scan ($1.50/1000 OCR + $0.001 AI parse)
**Monthly estimate:** 1000 scans/month = ~$2.50

**Rate limits:**
| API | Limit | Buffer Strategy |
|-----|-------|----------------|
| Google Vision | 1800 req/min | No issue for single-user app |
| Claude Haiku | 1000 req/min | No issue |
| FDA Recall | Unknown — test | Cache results daily |

---

## Stage 5: Error Handling

**Error matrix:**

| Step | Error | Action | Severity |
|------|-------|--------|----------|
| Image Capture | Blurry image | Prompt user to retake, show focus guide | Low |
| Image Capture | No label detected | "Point camera at nutrition label" message | Low |
| OCR | Low confidence (<70%) | Show "Could not read label — try again with better lighting" | Medium |
| OCR | Partial extraction | Proceed with partial data, flag score as "incomplete" | Medium |
| Label Parsing | Can't identify sections | Fall back to showing raw OCR text, let user confirm | Medium |
| Ingredient Lookup | Unknown ingredient | Show as "unrecognized" with neutral score impact | Low |
| Scoring | Incomplete data | Show partial score with "based on X of Y fields" disclaimer | Low |
| Storage | Offline | Queue locally, sync when connection returns | Low |
| Recall Monitor | API down | Retry next day, no user impact | Low |

**Quality gates:**
- OCR confidence must be >70% to proceed automatically
- If <70%, show user the extracted text and ask "Does this look right?"

**Rollback (Gap #17):** User can delete a scan from history. No other rollback needed — scans are read-only observations.

**Data retention (Gap #12):** Scan history kept indefinitely (user's data). Ingredient database updated monthly.

---

## Stage 6: Dashboard Design

Not a terminal dashboard — this is a **mobile app UI**. But the framework asks for it, so adapting:

**User-facing screens:**
1. **Scan screen** — camera viewfinder with overlay guide
2. **Result card** — score badge, ingredient list with warnings, "save" button
3. **History screen** — list of past scans, sortable by date/score
4. **Alerts screen** — recall notifications

**Key metrics (operator view, if this becomes a service):**
- Scans/day across all users
- OCR success rate
- Average score by product category
- Recall matches found

**CLI commands (for operator):**
```
sugar-scanner health          # API status, DB connection, OCR quota remaining
sugar-scanner stats           # Scan volume, success rate, top products
sugar-scanner ingredients update  # Refresh ingredient database
sugar-scanner recalls check   # Manual recall check trigger
```

---

## Stage 7: Build Order

**Phase 1: Core scan pipeline (MVP)**
- Ingredient database (seed with top 500 additives)
- OCR integration (Google Vision)
- Label parser (Claude Haiku)
- Scoring algorithm
- Test: Scan 10 real products, verify scores make sense

**Phase 2: Mobile app**
- Camera capture UI
- Result display card
- API server connecting phone to processing pipeline
- Test: End-to-end scan from phone camera to score display

**Phase 3: User accounts + history**
- Auth (email/Google sign-in)
- Scan history storage
- History browsing UI
- Test: Scan 5 products, verify all appear in history

**Phase 4: Recall monitoring**
- FDA recall API integration
- Daily batch job
- Push notification setup
- Test: Insert a known recalled product into history, verify notification fires

**File structure:**
```
sugar-scanner/
├── server/
│   ├── index.js              # Express API server
│   ├── ocr.js                # Google Vision integration
│   ├── parser.js             # Claude label parser
│   ├── scorer.js             # Health scoring algorithm
│   ├── ingredients-db.js     # Ingredient lookup
│   ├── recalls.js            # FDA recall checker
│   └── db.js                 # PostgreSQL connection
├── mobile/
│   ├── App.tsx               # React Native entry
│   ├── screens/
│   │   ├── ScanScreen.tsx
│   │   ├── ResultScreen.tsx
│   │   ├── HistoryScreen.tsx
│   │   └── AlertsScreen.tsx
│   └── services/
│       ├── api.ts            # Server API client
│       └── camera.ts         # Camera integration
├── data/
│   └── ingredients.json      # Seed ingredient database
└── scripts/
    ├── seed-ingredients.js   # Load ingredient DB
    └── check-recalls.js      # Manual recall check
```

---

## Stage 8: Test Cases

**Sample test case (real data):**
- Product: Coca-Cola Classic 12oz can
- Ingredients: Carbonated water, high fructose corn syrup, caramel color, phosphoric acid, natural flavors, caffeine
- Nutrition: 140 cal, 39g sugar, 45mg sodium, 0g fat
- Expected score: ~25/100 (high sugar, HFCS, artificial color)
- Expected warnings: "High fructose corn syrup", "39g sugar (156% daily recommended added sugar)", "Caramel color (potential carcinogen concern)"

**Testing checklist:**
1. [ ] Scan clear label in good lighting → score in <3 seconds
2. [ ] Scan blurry label → "retake" prompt
3. [ ] Scan non-food item → "no nutrition label detected"
4. [ ] Scan foreign language label → graceful failure or partial parse
5. [ ] Scan with no internet → queued locally, syncs later
6. [ ] Score a "healthy" product (plain oatmeal) → score >80
7. [ ] Score a "unhealthy" product (Coca-Cola) → score <30
8. [ ] Compare two products in history → correct relative ranking
9. [ ] Recall notification fires for known recalled product
10. [ ] User can delete a scan from history

**Health checks:**
```
curl localhost:3000/health          # Server status
curl localhost:3000/ocr/test        # OCR API reachable
curl localhost:3000/ingredients/count  # Ingredient DB loaded
```

---

## Stage 9: Gap Analysis (Final Pass)

| # | Gap | Covered? | Where? |
|---|-----|----------|--------|
| 1 | Multi-level phasing | YES | Stage 1 — real-time scan + background recall monitor |
| 2 | Repeating steps | YES | Stage 2 — user may retry blurry scans |
| 3 | Extensible options | YES | Stage 2 — label formats vary by country |
| 4 | Presets | YES | Stage 2 — ingredient alias mapping |
| 5 | Cross-item merge | YES | Stage 2 — side-by-side product comparison |
| 6 | API keys | YES | Stage 4 — Google Vision, Claude, Firebase |
| 7 | Dependencies | YES | Stage 4 — full stack listed |
| 8 | Cost per run | YES | Stage 4 — $0.0025/scan |
| 9 | Rate limits | YES | Stage 4 — all APIs documented |
| 10 | Prompt templates | YES | Stage 3 — label parser prompt |
| 11 | User interaction | PARTIAL | Stage 6 — adapted for mobile but framework assumed terminal |
| 12 | Data retention | YES | Stage 5 — indefinite scan history |
| 13 | Output quality | YES | Stage 5 — OCR confidence gate |
| 14 | Versioning | YES | Scoring algorithm can be updated, old scans re-scored |
| 15 | Prerequisites | YES | Stage 4 — setup order documented |
| 16 | Sample test case | YES | Stage 8 — Coca-Cola can |
| 17 | Rollback | YES | Stage 5 — delete scan from history |
| 18 | Access control | YES | Per-user accounts, users only see own scans |

**Coverage: 17.5/18** — NEAR COMPLETE

**Gap #11 is partial** — the framework's Stage 6 is designed for terminal dashboards and CLI commands. This is a mobile app. The stage still produced useful output but had to be adapted.

---

## NEW Gaps Discovered

### Gap #19: Real-time Latency Requirements
The framework never asks "how fast must this respond?" All previous POCs were batch or async. Sugar Scanner MUST return results in <3 seconds or it's useless. **Stage 0 should ask about latency requirements.**

### Gap #20: Offline / Connectivity Requirements
The framework assumes always-online server-side processing. Sugar Scanner needs to work in a grocery store with bad cell signal. **Stage 4 should ask "does this need to work offline? What degrades gracefully?"**

### Gap #21: Hardware/Sensor Input
The framework assumes data comes from APIs, files, or databases. Sugar Scanner's input is a camera. Other automations might use microphones, GPS, accelerometers, barcode scanners. **Stage 0 should ask "does this involve physical-world input devices?"**

### Gap #22: Client-Side vs Server-Side Processing Split
The framework assumes everything runs on one server. Sugar Scanner has processing split between phone (camera capture, UI) and server (OCR, AI, scoring). **Stage 4 should ask "where does each step physically execute?"**

### Gap #23: App Store / Distribution
The framework ends with a CLAUDE.md build file. But a mobile app also needs app store submission, signing, review process. **Stage 7 should ask "how does the end user get this?"**

### Gap #24: User Onboarding / First-Time Experience
The framework never asks how a new user starts using the system. For backend automations this doesn't matter. For user-facing apps, onboarding is critical. **Stage 6 should include "what does the first-time user experience look like?"**

---

## Framework Assessment

**What worked:**
- Stages 0-5 mapped cleanly. The 6-step pattern (INPUT/PROCESS/OUTPUT/STATE/NOTIFY/SCHEDULE) captured the core flow perfectly even for a mobile app.
- The gap checklist caught most things — 17.5/18 is solid.
- Stage 3 (automation classification) correctly separated deterministic scoring from AI-driven parsing.
- Stage 8 test cases produced a concrete, testable example.

**What didn't work:**
- **Stage 6 (Dashboard Design) is too narrow.** It assumes terminal UI + CLI. For user-facing apps, the "interface" stage needs to cover mobile screens, web UIs, or chatbot interfaces — not just terminal dashboards.
- **Stage 4 (Environment Setup) assumes one execution environment.** Doesn't capture client/server split.
- **No latency/performance stage.** For real-time apps, response time is a core requirement, not an afterthought.

**What needs changing:**
1. Stage 0: Add question — "Does this need to respond in real-time? What's the max acceptable latency?"
2. Stage 0: Add question — "Does this involve physical devices or sensors?"
3. Stage 4: Add question — "Does this work offline? What degrades?"
4. Stage 4: Add question — "Where does each step execute? (server, client device, edge)"
5. Stage 6: Rename from "Dashboard Design" to "Interface Design" and support mobile/web/terminal/bot patterns
6. Stage 7: Add question — "How does the end user get/install this?"
