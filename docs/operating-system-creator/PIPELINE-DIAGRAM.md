# OS Automation Pipeline — Full Diagram

> **How the original wizard (6 parts) evolved into the 10-stage pipeline, and where every gap landed.**

---

## The Evolution

```
ORIGINAL WIZARD (4 sections, 6-step pattern)
    │
    │  + 18 gaps discovered through testing
    │
    ▼
NEW 10-STAGE PIPELINE (everything covered)
```

---

## Where the Original 6 Went

The original wizard had 4 sections (A, B, C, D) and the 6-step pattern (INPUT → PROCESS → OUTPUT → STATE → NOTIFY → SCHEDULE). Here's exactly where each piece landed:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORIGINAL WIZARD                              │
│                                                                 │
│  Section A: Big Picture (10 questions)                          │
│    A1. Process name                                             │
│    A2. What does a human do today?          ──────► STAGE 0     │
│    A3. How often?                                  Process      │
│    A4. How long per run?                           Capture      │
│    A5. Items per run?                                           │
│    A6. Where does data come from?                               │
│    A7. Where does end result go?                                │
│    A8. Tools already in use?                                    │
│    A9. What breaks most often?                                  │
│    A10. Legal/compliance?                                       │
│                                                                 │
│  6-Step Pattern:                                                │
│    INPUT ─────────────────────────────────► STAGE 1             │
│    PROCESS                                  6-Step              │
│    OUTPUT                                   Mapping             │
│    STATE                                                        │
│    NOTIFY                                                       │
│    SCHEDULE                                                     │
│                                                                 │
│  Section B: Step Breakdown (9 questions × N steps)              │
│    B1. What does the human do?                                  │
│    B2. What data needed?                                        │
│    B3. What decisions?                     ──────► STAGE 2      │
│    B4. Could Claude decide?                        Step         │
│    B5. What's the output?                          Decomposition│
│    B6. Where does output go?                                    │
│    B7. API tool available?                 ──────► STAGE 3      │
│    B8. Error case?                                 Automation   │
│    B9. Human time per step?                        Classification│
│                                                                 │
│  Section C: Operations Layer (9 questions)                      │
│    C1. Statuses (lifecycle)               ──────► STAGE 1      │
│    C2. Audit trail?                                (STATE)      │
│    C3. Dedup needed?                                            │
│    C4. Who needs to know?                 ──────► STAGE 6      │
│    C5. What do they need to know?                  Dashboard    │
│    C6. How notified?                               Design      │
│    C7. When should it run?                ──────► STAGE 1      │
│    C8. Failure recovery?                           (SCHEDULE)   │
│    C9. Infrastructure?                    ──────► STAGE 4      │
│                                                    Environment  │
│  Section D: Success Criteria (4 questions)                      │
│    D1. Metrics                            ──────► STAGE 8      │
│    D2. Human cost                                  Test Cases   │
│    D3. Budget                             ──────► STAGE 4      │
│    D4. MVP step                                    Environment  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Where the 18 Gaps Landed

```
┌─────────────────────────────────────────────────────────────────┐
│                    18 GAPS DISCOVERED                            │
│                                                                 │
│  STRUCTURAL (found during Video Intelligence test)              │
│                                                                 │
│   Gap 1:  Multi-level phasing         ──────► STAGE 1 (new Q)  │
│   Gap 2:  Repeating steps             ──────► STAGE 2 (new Q)  │
│   Gap 3:  Extensible option lists     ──────► STAGE 2 (new Q)  │
│   Gap 4:  Presets / saved combos      ──────► STAGE 2 (new Q)  │
│   Gap 5:  Cross-item batch merge      ──────► STAGE 2 (new Q)  │
│                                                                 │
│  PRACTICAL (found during real-time building)                    │
│                                                                 │
│   Gap 6:  API keys/credentials        ──────► STAGE 4 (new)    │
│   Gap 7:  Dependencies/runtime        ──────► STAGE 4 (new)    │
│   Gap 8:  Cost-per-run math           ──────► STAGE 4 (new)    │
│   Gap 9:  Rate limits                 ──────► STAGE 4 (new)    │
│   Gap 10: Prompt template capture     ──────► STAGE 3 (new)    │
│   Gap 11: User interaction model      ──────► STAGE 6 (new)    │
│   Gap 12: Data retention lifecycle    ──────► STAGE 5 (new)    │
│   Gap 13: Output quality validation   ──────► STAGE 5 (new)    │
│   Gap 14: Versioning/reprocessing     ──────► STAGE 5 (new)    │
│   Gap 15: Prerequisite dependencies   ──────► STAGE 4 (new)    │
│   Gap 16: Sample test case            ──────► STAGE 8 (new)    │
│   Gap 17: Rollback/undo              ──────► STAGE 5 (new)    │
│   Gap 18: Access control              ──────► STAGE 9 (check)  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Complete 10-Stage Pipeline

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   STAGE 0: PROCESS CAPTURE                                       ║
║   ┌──────────────────────────────────────┐                       ║
║   │ Original: Section A (all 10 Qs)      │                       ║
║   │ New: Nothing — Section A was solid   │                       ║
║   │                                      │                       ║
║   │ Ask: What's the process? How often?  │                       ║
║   │      What tools? What breaks?        │                       ║
║   └──────────────┬───────────────────────┘                       ║
║                  │                                                ║
║                  ▼                                                ║
║   STAGE 1: 6-STEP MAPPING                                        ║
║   ┌──────────────────────────────────────┐                       ║
║   │ Original: The 6-step pattern         │                       ║
║   │         + Section C1-C3 (state)      │                       ║
║   │         + Section C7-C8 (schedule)   │                       ║
║   │ New: Gap 1 — "Is this multi-phase?"  │                       ║
║   │                                      │                       ║
║   │ Map: INPUT → PROCESS → OUTPUT        │                       ║
║   │      STATE → NOTIFY → SCHEDULE       │                       ║
║   │      Check for multiple levels       │                       ║
║   └──────────────┬───────────────────────┘                       ║
║                  │                                                ║
║                  ▼                                                ║
║   STAGE 2: STEP DECOMPOSITION                                    ║
║   ┌──────────────────────────────────────┐                       ║
║   │ Original: Section B (9 Qs per step)  │                       ║
║   │ New: Gap 2 — "Does this repeat?"     │                       ║
║   │      Gap 3 — "Options grow?"         │                       ║
║   │      Gap 4 — "Save as presets?"      │                       ║
║   │      Gap 5 — "Batch merge?"          │                       ║
║   │                                      │                       ║
║   │ For each step: inputs, outputs,      │                       ║
║   │ decisions, errors, timing, repeats   │                       ║
║   └──────────────┬───────────────────────┘                       ║
║                  │                                                ║
║            ┌─────┴─────┐                                         ║
║            ▼           │                                         ║
║   GAP ANALYSIS         │  ◄── EARLY PASS (2 min quick scan)     ║
║   (Stage 9 lite)       │      Catch showstoppers before          ║
║            │           │      investing in detailed design        ║
║            └─────┬─────┘                                         ║
║                  │                                                ║
║                  ▼                                                ║
║   STAGE 3: AUTOMATION CLASSIFICATION                             ║
║   ┌──────────────────────────────────────┐                       ║
║   │ Original: B4 "Could Claude decide?"  │                       ║
║   │         + B7 "API tool available?"   │                       ║
║   │ New: Gap 10 — Prompt skeletons       │                       ║
║   │                                      │                       ║
║   │ Each step → Code / AI / Human /      │                       ║
║   │              External API / Hybrid   │                       ║
║   │ AI steps get prompt templates        │                       ║
║   │ Deterministic steps get logic rules  │                       ║
║   └──────────────┬───────────────────────┘                       ║
║                  │                                                ║
║                  ▼                                                ║
║   STAGE 4: ENVIRONMENT SETUP                                     ║
║   ┌──────────────────────────────────────┐                       ║
║   │ Original: A8 (tools), C9 (infra),   │                       ║
║   │           D3 (budget)                │                       ║
║   │ New: Gap 6 — API keys checklist      │                       ║
║   │      Gap 7 — Dependencies/runtime    │                       ║
║   │      Gap 8 — Cost-per-run math       │                       ║
║   │      Gap 9 — Rate limits             │                       ║
║   │      Gap 15 — Prerequisites          │                       ║
║   │                                      │                       ║
║   │ Every key: how to get it, cost, env  │                       ║
║   │ Every API: rate limit + buffer       │                       ║
║   │ Total cost per run calculated        │                       ║
║   └──────────────┬───────────────────────┘                       ║
║                  │                                                ║
║                  ▼                                                ║
║   STAGE 5: ERROR HANDLING & VALIDATION                           ║
║   ┌──────────────────────────────────────┐                       ║
║   │ Original: B8 (error case)            │                       ║
║   │ New: Gap 12 — Data retention         │                       ║
║   │      Gap 13 — Quality validation     │                       ║
║   │      Gap 14 — Versioning/reprocess   │                       ║
║   │      Gap 17 — Rollback/undo          │                       ║
║   │                                      │                       ║
║   │ Error matrix per step                │                       ║
║   │ Quality gates                        │                       ║
║   │ Cascade failure rules                │                       ║
║   │ Data retention lifecycle             │                       ║
║   └──────────────┬───────────────────────┘                       ║
║                  │                                                ║
║                  ▼                                                ║
║   STAGE 6: DASHBOARD DESIGN                                      ║
║   ┌──────────────────────────────────────┐                       ║
║   │ Original: C4-C6 (notifications)      │                       ║
║   │ New: Gap 11 — User interaction       │                       ║
║   │                                      │                       ║
║   │ Terminal dashboard layout            │                       ║
║   │ CLI commands                         │                       ║
║   │ Key metrics (3-5)                    │                       ║
║   │ Notification thresholds              │                       ║
║   └──────────────┬───────────────────────┘                       ║
║                  │                                                ║
║                  ▼                                                ║
║   STAGE 7: BUILD ORDER                                           ║
║   ┌──────────────────────────────────────┐                       ║
║   │ Original: D4 (MVP step)             │                       ║
║   │ New: Entire stage is new            │                       ║
║   │                                      │                       ║
║   │ Dependency graph                     │                       ║
║   │ Build phases (test each one)         │                       ║
║   │ File structure                       │                       ║
║   │ Module specs                         │                       ║
║   │ MVP path                             │                       ║
║   └──────────────┬───────────────────────┘                       ║
║                  │                                                ║
║                  ▼                                                ║
║   STAGE 8: TEST CASES & HEALTH CHECKS                           ║
║   ┌──────────────────────────────────────┐                       ║
║   │ Original: D1-D2 (metrics, cost)     │                       ║
║   │ New: Gap 16 — Sample test case       │                       ║
║   │                                      │                       ║
║   │ Real test data (not hypothetical)    │                       ║
║   │ Numbered testing checklist           │                       ║
║   │ Health check commands                │                       ║
║   │ Ongoing monitoring plan              │                       ║
║   └──────────────┬───────────────────────┘                       ║
║                  │                                                ║
║                  ▼                                                ║
║   STAGE 9: GAP ANALYSIS (FINAL PASS)                             ║
║   ┌──────────────────────────────────────┐                       ║
║   │ Original: Nothing — didn't exist     │                       ║
║   │ New: All 18 gaps as checklist        │                       ║
║   │      + Gap 18 (access control)       │                       ║
║   │      + discover new gaps             │                       ║
║   │                                      │                       ║
║   │ Full 18-point sweep                  │                       ║
║   │ Score: COMPLETE / GAPS / INCOMPLETE  │                       ║
║   │ New gaps → feed back into stages     │                       ║
║   └──────────────┬───────────────────────┘                       ║
║                  │                                                ║
║                  ▼                                                ║
║   STAGE 10: CLAUDE.md GENERATOR                                  ║
║   ┌──────────────────────────────────────┐                       ║
║   │ Original: Nothing — was manual       │                       ║
║   │ New: Entire stage is new             │                       ║
║   │                                      │                       ║
║   │ Render everything into one file      │                       ║
║   │ Self-contained build instructions    │                       ║
║   │ Drop in folder → run claude → done   │                       ║
║   └──────────────────────────────────────┘                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## Summary Count

```
Original wizard questions:           32 (A:10 + B:9 + C:9 + D:4)
Original 6-step pattern:              6 (INPUT/PROCESS/OUTPUT/STATE/NOTIFY/SCHEDULE)
Gaps discovered through testing:     18
New stages added:                     4 (Stages 4, 7, 9, 10 are entirely new)
Stages that absorbed gaps:            6 (Stages 1-3, 5-6, 8 got new questions)
                                    ────
Total coverage points:              ~60 (vs original ~38)
```

**What stayed the same:** The core 6-step pattern (Stage 1) and the step breakdown questions (Stage 2) were already solid. They just got extended.

**What's entirely new:** Environment Setup (Stage 4), Build Order (Stage 7), Gap Analysis (Stage 9), and CLAUDE.md Generator (Stage 10) didn't exist at all in the original wizard.

**Biggest upgrade:** The original wizard asked WHAT the process does. The new pipeline also asks HOW to build it, HOW to test it, and HOW to verify nothing was missed.
