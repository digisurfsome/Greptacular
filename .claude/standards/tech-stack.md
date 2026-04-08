# Tech Stack & Conventions — Modular AI Pipeline Builder

## Foundation

| Component | Technology | Notes |
|-----------|-----------|-------|
| Pipeline engine | Activepieces (self-hosted) | MIT license, Docker, do NOT fork core |
| Activepieces version | Latest stable | Pin version in docker-compose.yml |
| Database | PostgreSQL (Activepieces default) | Don't swap this out |
| Skin UI | React + TypeScript + Tailwind CSS | Same stack as Activepieces frontend |
| Skin API | FastAPI (Python) or Next.js API routes | Thin layer, 10-20 endpoints |
| Custom pieces | TypeScript (Activepieces pieces framework) | Built with `@activepieces/cli` |
| Mechanism library | TypeScript files with JSDoc metadata | Plain files, no framework needed |
| Test runner | Jest (for piece unit tests) | Built into Activepieces pieces framework |

## Activepieces Piece Development

### CLI Commands
```bash
npm install -g @activepieces/cli   # install once
ap init                             # init project with API key
ap create-piece --name my-piece --type custom   # scaffold new piece
ap update                           # push local changes to AP instance
ap publish                          # lock version, deploy to AP instance
```

### Piece File Structure
```
packages/pieces/custom/my-piece/
├── src/
│   ├── index.ts          # piece definition (createPiece)
│   ├── lib/
│   │   ├── actions/
│   │   │   └── my-action.ts      # createAction definition
│   │   └── triggers/
│   │       └── my-trigger.ts     # createTrigger definition (if needed)
├── package.json
└── tsconfig.json
```

### Property Types Available
```typescript
Property.ShortText({ displayName: '', required: true/false })
Property.LongText({ ... })
Property.Number({ ... })
Property.Checkbox({ ... })
Property.Dropdown({ options: [...] })
Property.MultiSelectDropdown({ options: [...] })
Property.Json({ ... })
Property.Array({ ... })
Property.DynamicProperties({ ... })   // computed at runtime
```

## Flow JSON Format

### Key Types (from Activepieces shared package)
```typescript
// The complete flow definition
type FlowVersion = {
  displayName: string
  trigger: FlowTrigger       // root trigger node
  schemaVersion: "21"        // ALWAYS "21" for current AP
  valid: boolean
}

// A piece action node
type PieceAction = {
  type: 'PIECE'
  name: string               // unique step name, e.g. "step_1"
  displayName: string
  settings: {
    pieceName: string        // e.g. "@activepieces/piece-gmail"
    actionName: string       // e.g. "send_email"
    pieceVersion: string     // e.g. "~0.6.0"
    input: Record<string, unknown>  // the settings for this action
    propertySettings: Record<string, PropertySettings>
    errorHandlingOptions?: {
      continueOnFailure: boolean
      retryOnFailure: boolean
    }
  }
  nextAction?: FlowAction    // linked list to next step
}

// Control flow: loop
type LoopOnItemsAction = {
  type: 'LOOP_ON_ITEMS'
  settings: {
    items: string  // usually a reference like "{{step_1.output}}"
  }
  firstLoopAction?: FlowAction  // first action inside the loop
  nextAction?: FlowAction       // action after the loop
}

// Control flow: branch / router
type RouterAction = {
  type: 'ROUTER'
  settings: {
    branches: Branch[]
    defaultBranch: string
    executionType: 'EXECUTE_FIRST_MATCH' | 'EXECUTE_ALL_MATCHES'
  }
  children: (FlowAction | null)[]   // one per branch
}
```

### Variable References in Flow JSON
When one step uses output from a previous step:
```json
"input": {
  "to": "{{step_1.output.email}}",
  "subject": "{{step_2.output.title}}"
}
```

## API Calls

### Create + Build a Complete Flow (Two-Call Pattern)
```python
import requests

BASE_URL = "http://localhost:8080/api/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# Step 1: Create empty flow
resp = requests.post(f"{BASE_URL}/flows", headers=HEADERS, json={
    "displayName": "My Pipeline",
    "projectId": PROJECT_ID
})
flow_id = resp.json()["id"]

# Step 2: Inject complete flow definition
flow_definition = { ... }  # complete FlowVersion JSON
requests.post(f"{BASE_URL}/flows/{flow_id}", headers=HEADERS, json={
    "type": "IMPORT_FLOW",
    "request": flow_definition
})
```

### Other Useful Operations
```python
# Run a flow manually
requests.post(f"{BASE_URL}/flow-runs", json={"flowId": flow_id, "projectId": PROJECT_ID})

# Get flow status
requests.get(f"{BASE_URL}/flows/{flow_id}")

# List all flows in project
requests.get(f"{BASE_URL}/flows", params={"projectId": PROJECT_ID})
```

## Directory Structure (Full Project)

```
project-root/
├── docker-compose.yml         # Activepieces + PostgreSQL
├── skin/                      # Branded UI shell
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api.ts             # calls Activepieces API
│   │   ├── auth/
│   │   └── pages/
│   ├── .env
│   │   ├── BUILDER_MODE=false
│   │   └── ACTIVEPIECES_URL=http://localhost:8080
│   └── Dockerfile
├── pieces/                    # Custom pieces (ap create-piece output)
│   └── code-module/
│       └── src/
│           ├── index.ts
│           └── lib/actions/
├── mechanisms/                # Reusable code patterns (mechanism library)
│   ├── data-transform/
│   ├── api-handling/
│   ├── llm-ops/
│   ├── control-flow/
│   └── output/
├── tests/                     # Piece test files (Jest)
│   └── code-module/
└── .env                       # AP_API_KEY, PROJECT_ID, etc.
```

## Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Piece name | kebab-case | `code-module`, `youtube-enricher` |
| Action name | snake_case | `build_with_ai`, `run_custom_code` |
| Step names in flows | step_N | `step_1`, `step_2` |
| Mechanism files | kebab-case.ts | `flatten-array.ts`, `retry-with-backoff.ts` |
| Mechanism tags | lowercase, comma-separated | `array, transform, data` |
| Skin components | PascalCase | `PipelineView.tsx`, `NodePanel.tsx` |
| API endpoints | snake_case paths | `/api/run_pipeline`, `/api/flow_status` |

## Environment Variables

```bash
# Activepieces
AP_API_KEY=your_api_key_here
AP_PROJECT_ID=your_project_id
AP_BASE_URL=http://localhost:8080

# Skin
BUILDER_MODE=false             # true = show builder (admin only)
VITE_AP_BASE_URL=http://localhost:8080

# AI Co-Pilot (uses Claude via subscription)
# No API key needed — uses Claude Code CLI subscription auth
```
