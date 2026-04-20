# FormBlast V2 — Hook Builder + Bring Your Own API
## Expansion Beyond SEO — Open Platform

---

## What Changes in V2

V1 is an SEO agency tool with managed backend APIs.
V2 opens the platform to any agency type by letting users:

1. Connect their own API key (any data API)
2. Define what data to pull
3. Map response fields to output columns
4. Set their own tier thresholds
5. Write their own email angles
6. Generate spinner variants via Claude
7. Use that hook in campaigns just like the native hooks

No code required. No support ticket to the dev. Fully self-serve.

---

## Who This Unlocks

Anyone running an agency with a data angle:

- PR agencies (media mention tracking)
- Franchise consultants (franchise location gap data)
- Insurance agencies (coverage comparison APIs)
- Healthcare marketing (patient review volume)
- Contractor licensing verification agencies
- Any niche we never thought of

If there's an API with competitive gap data, someone can build a hook for it.

---

## New Page: Hook Builder

Added to sidebar between Hooks and Settings.

### Step 1 — Name + Describe

```
Hook name:        [ Restaurant Health Scores              ]
What gap does     [ Health inspection scores vs nearby    ]
this expose?      [ competitors — shows owners their risk ]
Best for:         [ Restaurant consultants, health-focused ]
                  [ food service agencies                  ]
```

### Step 2 — API Connection

```
API endpoint:   [ https://api.example.com/v1/search     ]
Auth type:      (●) Bearer token  ( ) API key header  ( ) Query param  ( ) Basic auth
Key name:       [ Authorization                          ]
API key:        [ ••••••••••••••••••••••••••  ] [ Test Connection ]

                ✓ Connected — API responding

What inputs     Which CSV columns does this API need?
does it need?   [✓] business_name   [✓] city   [ ] website_url   [ ] niche
```

### Step 3 — Request Builder

```
Build the API call using available input variables:

GET https://api.example.com/v1/search
  ?name=    {business_name}       ← drag from input list
  &location={city}                ← drag from input list
  &limit=   5

[ + Add parameter ]     [ Run test call ]

Response preview:
{
  "businesses": [
    { "name": "Joe's Pizza",
      "rating": 3.5,          ← drag these to Step 4
      "review_count": 47,
      "price": "$$"
    },
    { "name": "Tony's",
      "rating": 4.8,
      "review_count": 312
    }
  ]
}
```

### Step 4 — Field Mapper

```
Drag response fields → name your output columns

businesses[0].rating        →  [ my_rating       ]  (number)
businesses[0].review_count  →  [ my_reviews      ]  (number)
businesses[0].name          →  [ my_biz_name     ]  (text)
businesses[1].rating        →  [ comp1_rating    ]  (number)
businesses[1].review_count  →  [ comp1_reviews   ]  (number)
businesses[1].name          →  [ top_competitor  ]  (text)

[ + Add field mapping ]

Available in emails: {my_rating} {my_reviews} {comp1_rating}
{comp1_reviews} {top_competitor} + all standard fields
({business_name} {city} {niche} {domain})
```

### Step 5 — Tier Logic

```
Tier by which field?   [ my_reviews   ▾]
Compare against:       [ comp1_reviews ▾]
Method:                (●) ratio   ( ) raw difference   ( ) absolute value

Tier A  ratio ≥  [ 0.80 ]   Label: [ Competitive — fine-tune ]
Tier B  ratio ≥  [ 0.40 ]   Label: [ Notable gap             ]
Tier C  ratio ≥  [ 0.10 ]   Label: [ Significant gap         ]
Tier D  ratio <  [ 0.10 ]   Label: [ Almost invisible        ]

Preview:  my_reviews=47, comp1_reviews=312 → ratio=0.15 → Tier C ✓
```

### Step 6 — Email Angles

```
Variables available to use:
{my_rating} {my_reviews} {my_biz_name}
{comp1_rating} {comp1_reviews} {top_competitor}
{business_name} {city} {niche}

Tier A angle — they're close but behind on something:
[ You have {my_reviews} reviews at {my_rating} stars. Strong. ]
[ But {top_competitor} is at {comp1_rating} with {comp1_reviews}. ]
[ That gap matters at the decision moment.                       ]

Tier B angle — meaningful gap:
[ _________________________________________________ ]

Tier C angle — serious gap:
[ _________________________________________________ ]

Tier D angle — almost no presence:
[ _________________________________________________ ]

Subject line template:
[ "{top_competitor} has {comp1_reviews} reviews, {business_name} has {my_reviews}" ]
```

### Step 7 — Generate Variants

```
Claude generates 10 variations of each email block
for all 4 tiers using your angles as the brief.

Cost: ~$0.05 one time     Est. time: 45 seconds

[ Generate Variants ]

✓ Tier A — 40 variants generated
✓ Tier B — 40 variants generated
✓ Tier C — 40 variants generated
✓ Tier D — 40 variants generated

[ Preview in Email Studio ]
```

### Step 8 — Test + Publish

```
Test business:   [ Joe's Pizza              ]
City:            [ Austin TX                ]

                 [ Run Test ]

Result:
  my_reviews: 47    comp1_reviews: 312    ratio: 0.15
  Tier: C

Assembled email:
  Subject: "Tony's has 312 reviews, Joe's Pizza has 47 — that gap costs calls"
  Body: Joe's Pizza is sitting at 47 reviews while Tony's across
  town has built 312. First thing someone checks before calling...

[ ← Adjust ] [ Publish Hook ] [ Save as Draft ]
```

---

## Hook Visibility Options

When publishing a custom hook, user chooses:

```
( ●) Private — only I can use this hook
(  ) Share with FormBlast community (earn credits when others use it)
```

Community hooks go through a basic review before appearing in the Hook library.
Popular community hooks (50+ active users) get evaluated for native integration.

---

## API Key Management (V2 Settings)

New section added to Settings:

```
MY API CONNECTIONS

[ + Add API Connection ]

┌─────────────────────┬────────────────┬──────────────┬──────────┐
│ Name                │ Used in        │ Last tested  │ Actions  │
├─────────────────────┼────────────────┼──────────────┼──────────┤
│ Yelp Fusion         │ Restaurant hook│ 2 days ago ✓ │ [Edit]   │
│ SerpAPI             │ Review hook    │ Today ✓      │ [Edit]   │
│ BrightLocal         │ Citations hook │ Never        │ [Test]   │
└─────────────────────┴────────────────┴──────────────┴──────────┘
```

Keys stored encrypted. Never displayed after entry.
User pays their own API costs for custom hooks.
Native hooks (SEO Rankings, PageSpeed, etc.) are backend-managed — no key needed.

---

## Pricing Adjustment for V2

| Plan | Price | Hooks | Custom Hooks | Community |
|------|-------|-------|-------------|-----------|
| Starter | $49/mo | Native only | — | View only |
| Pro | $97/mo | All native | 3 custom | View + use |
| Agency | $197/mo | All native | Unlimited | Build + share |

Custom hook API costs are always paid by the user directly.
Native hook API costs are absorbed into plan pricing.

---

## What Gets Built in V2

1. Hook Builder UI (8-step wizard above)
2. API Connection manager (encrypted key storage)
3. Dynamic field mapper (JSON path parser + UI)
4. Tier logic builder (formula engine)
5. Community hook library (browse + install)
6. Hook usage analytics (which hooks perform best by niche)
7. Credit system for community hook creators

---

## What Doesn't Change from V1

All pipeline scripts stay the same.
The hook interface (`HookModule` base class) is already designed for this.
V2 custom hooks generate the same JSON variant files as native hooks.
Campaign creation, Email Studio, Analytics, Pipeline Planner — unchanged.
The only new thing is how hooks get created and where API keys live.

---

## V1 → V2 Migration

No breaking changes. V1 users upgrade seamlessly.
Their existing campaigns, hooks, and analytics carry forward.
New "Custom Hooks" tab appears in the Hooks page.
API Connections section appears in Settings.
Everything else identical.
