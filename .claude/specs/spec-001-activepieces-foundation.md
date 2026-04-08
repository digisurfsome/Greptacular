# Spec 001 — Activepieces Foundation Setup

## What This Is
Setting up Activepieces self-hosted so the pipeline engine is running, the API is accessible, and the two-call IMPORT_FLOW pattern works. This is the foundation everything else builds on. Do not proceed to any other spec until this is confirmed working.

## Why It Matters
Every other feature — AI co-pilot, skin, code module node — is worthless without a running Activepieces instance with a working API. This is the ground floor.

---

## Step 1: Docker Setup

Create `docker-compose.yml` at project root:

```yaml
version: "3.8"

services:
  activepieces:
    image: activepieces/activepieces:latest
    ports:
      - "8080:80"
    environment:
      - AP_ENGINE_EXECUTABLE_PATH=/usr/src/app/dist/packages/engine/main.js
      - AP_ENCRYPTION_KEY=your_32_char_random_key_here
      - AP_JWT_SECRET=your_jwt_secret_here
      - AP_POSTGRES_DATABASE=activepieces
      - AP_POSTGRES_HOST=postgres
      - AP_POSTGRES_PORT=5432
      - AP_POSTGRES_USERNAME=activepieces
      - AP_POSTGRES_PASSWORD=activepieces_password
      - AP_REDIS_URL=redis://redis:6379
      - AP_FRONTEND_URL=http://localhost:8080
      - AP_SANDBOX_RUN_TIME_SECONDS=600
      - AP_TELEMETRY_ENABLED=false
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: activepieces
      POSTGRES_USER: activepieces
      POSTGRES_PASSWORD: activepieces_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

Run:
```bash
docker-compose up -d
```

Open `http://localhost:8080` — should show Activepieces setup screen.

---

## Step 2: First-Time Setup

1. Open `http://localhost:8080`
2. Create admin account (email + password)
3. Create a project — note the **Project ID** (visible in URL or API)
4. Go to Settings → API Keys → Generate a new API key
5. Save to `.env`:
```bash
AP_API_KEY=ap_your_key_here
AP_PROJECT_ID=your_project_id_here
AP_BASE_URL=http://localhost:8080
```

---

## Step 3: Confirm the API Works

Run this test script to confirm the API is alive:

```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("AP_BASE_URL")
API_KEY = os.getenv("AP_API_KEY")
PROJECT_ID = os.getenv("AP_PROJECT_ID")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# Test 1: List flows (should return empty list)
resp = requests.get(f"{BASE_URL}/api/v1/flows", headers=HEADERS, params={"projectId": PROJECT_ID})
assert resp.status_code == 200, f"API failed: {resp.text}"
print("✓ API connection works")
print(f"  Existing flows: {len(resp.json()['data'])}")
```

---

## Step 4: Test IMPORT_FLOW (The Critical One)

This is the exact pattern the AI co-pilot will use. Confirm it works with a real simple flow.

```python
import requests, os
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("AP_BASE_URL")
API_KEY = os.getenv("AP_API_KEY")
PROJECT_ID = os.getenv("AP_PROJECT_ID")
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# Step A: Create an empty flow
create_resp = requests.post(f"{BASE_URL}/api/v1/flows", headers=HEADERS, json={
    "displayName": "Test Import Flow",
    "projectId": PROJECT_ID
})
assert create_resp.status_code == 200, f"Create failed: {create_resp.text}"
flow_id = create_resp.json()["id"]
print(f"✓ Created empty flow: {flow_id}")

# Step B: Import a complete flow definition (Schedule trigger → HTTP request action)
flow_definition = {
    "displayName": "Test Import Flow",
    "schemaVersion": "21",
    "valid": True,
    "trigger": {
        "type": "PIECE",
        "name": "trigger",
        "displayName": "Schedule",
        "valid": True,
        "settings": {
            "pieceName": "@activepieces/piece-schedule",
            "triggerName": "cron_expression",
            "input": {
                "cronExpression": "0 9 * * *"
            },
            "pieceVersion": "~0.0.5",
            "propertySettings": {}
        },
        "nextAction": {
            "type": "PIECE",
            "name": "step_1",
            "displayName": "HTTP Request",
            "valid": True,
            "settings": {
                "pieceName": "@activepieces/piece-http",
                "actionName": "send_http_request",
                "pieceVersion": "~0.3.0",
                "input": {
                    "method": "GET",
                    "url": "https://httpbin.org/get",
                    "headers": {},
                    "body_type": "none",
                    "queryParams": {}
                },
                "propertySettings": {},
                "errorHandlingOptions": {
                    "continueOnFailure": False,
                    "retryOnFailure": False
                }
            }
        }
    }
}

import_resp = requests.post(f"{BASE_URL}/api/v1/flows/{flow_id}", headers=HEADERS, json={
    "type": "IMPORT_FLOW",
    "request": flow_definition
})
assert import_resp.status_code == 200, f"IMPORT_FLOW failed: {import_resp.text}"
print("✓ IMPORT_FLOW works — flow is in the builder")
print(f"  Open http://localhost:8080 and verify 'Test Import Flow' appears with 2 steps")
```

**Success criteria:** Open the Activepieces builder at `http://localhost:8080`, find "Test Import Flow", open it, and see a Schedule trigger connected to an HTTP Request action — all settings filled in.

---

## Step 5: Connect Context7

Context7 gives the AI co-pilot accurate Activepieces schemas. This is what prevents the "wrong settings" problem.

In any Claude session working on flow generation, start with:
```
use context7 library: /activepieces/activepieces
```

This loads 768 snippets of Activepieces documentation so Claude knows:
- Every piece's `pieceName` (exact string)
- Every action's `actionName` (exact string)
- Every action's required and optional input fields
- Valid values for dropdown fields

**You do not need to build anything for this step.** It's a prompt instruction, not code.

---

## Step 6: Install the Activepieces CLI

For building custom pieces (needed in Spec 004):

```bash
npm install -g @activepieces/cli
ap --version   # confirm it installed
```

---

## Success Criteria for Spec 001

- [ ] `docker-compose up -d` starts Activepieces cleanly
- [ ] `http://localhost:8080` shows the Activepieces UI
- [ ] API test script returns 200 and lists flows
- [ ] IMPORT_FLOW test script creates a flow that appears in the builder with correct steps and settings
- [ ] Context7 command returns Activepieces docs snippets
- [ ] `ap --version` shows CLI is installed

Do not start Spec 002 until all six are checked off.

---

## Protocol Checkpoints (Stage 08 Injection)

### Pulse Checks — After Each File
| File | Assertions |
|------|-----------|
| `docker-compose.yml` | File exists; contains `activepieces`, `postgres`, `redis` services; port 8080 mapped |
| `.env` | File exists; `AP_API_KEY`, `AP_PROJECT_ID`, `AP_BASE_URL` all present and non-empty |
| `test_api.py` | File exists; no syntax errors (`python -c "import ast; ast.parse(open('test_api.py').read())`); imports `requests` and `os` |
| `test_import_flow.py` | File exists; no syntax errors; contains `IMPORT_FLOW` string |

### Seam Checks — Connection Points
**Seam 1: Docker → API** (check after `.env` is configured)
- `docker-compose up -d` exits code 0
- `curl http://localhost:8080/api/v1/flows -H "Authorization: Bearer $AP_API_KEY"` returns HTTP 200
- Response body contains `"data":[]` or `"data":[...]` (valid JSON)

**Seam 2: API → IMPORT_FLOW** (check after `test_import_flow.py` runs)
- Script exits code 0
- Flow ID returned is a non-empty string
- `GET /api/v1/flows/{flow_id}` returns the flow with `trigger.type == "PIECE"`

### Full Checkpoint (Phase 1 Gate)
**Pattern checks (git diff):**
```
Expected new files: docker-compose.yml, .env, test_api.py, test_import_flow.py
No other files should be modified.
```

**Functional checks:**
```bash
docker-compose up -d
python test_api.py          # must print "✓ API connection works"
python test_import_flow.py  # must print "✓ IMPORT_FLOW works"
# Then: open http://localhost:8080 and confirm "Test Import Flow" appears with 2 steps
```

**Gate condition:** Both test scripts print success AND the flow is visible in the AP builder UI. Binary: PASS or FAIL. Do not start Phase 2 on FAIL.

### Violation Rules
| Level | Trigger | Action |
|-------|---------|--------|
| LOW | Test script runs but output format differs slightly | Log and proceed |
| MEDIUM | API returns 200 but flow JSON is malformed | Review and fix before continuing |
| HIGH | Docker fails to start; API returns 4xx/5xx | Revert, fix docker-compose.yml, retry |
| CRITICAL | AP instance corrupted or DB migration failure | Full stop — rebuild from scratch |

### Two-Strike Rule
Max 2 retries on any failing check. If both fail: stop and ask human. Do not attempt a third retry — if 2 fresh attempts fail, the problem is in the spec or the environment, not the execution.
