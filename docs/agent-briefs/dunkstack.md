# DunkStack — Agent Brief

> Context-aware agent management system with token tracking, safety tiers, walkie-talkie comms, and session bridge saves.

## What It Does

DunkStack at `/#/dunkstack` is a real-time dashboard for managing long-running agent sessions. It tracks cumulative token usage with a 4-tier safety system (OK → WARNING → HANDOFF → HARD STOP), provides walkie-talkie-style communication with the agent via markdown files, and supports bridge saves for session continuity when context runs out.

## Files Involved

### Frontend — Page
| File | Purpose |
|------|---------|
| `ui/src/pages/DunkStackPage.tsx` (454 lines) | Main page — context gauge, comms chat, file viewer, project sidebar |

### Frontend — Components (`ui/src/components/dunkstack/`)
| File | Purpose |
|------|---------|
| `DunkStackCommsChat.tsx` | Walkie-talkie chat — reads/writes `.agent/comms/` files |
| `DunkStackContextGauge.tsx` (240 lines) | Visual context meter — color zones (green/yellow/orange/red) |
| `DunkStackSafetyPanel.tsx` (223 lines) | 3-tier safety display, session control buttons, bridge save |
| `DunkStackGuidePanel.tsx` (820 lines) | Floating draggable panel — manual docs + notes with CRUD |

### Frontend — Hook
| File | Purpose |
|------|---------|
| `ui/src/hooks/useDunkStack.ts` (341 lines) | State, WebSocket, comms parsing, token tracking, control modes |

### Backend — Router
| File | Purpose |
|------|---------|
| `server/routers/dunkstack.py` (570 lines) | All DunkStack endpoints + WebSocket |

## Data Flow

```
Agent runs in project dir → Writes to .agent/comms/to_human.md
UI polls / WebSocket → Reads to_human.md → Displays in chat
User types message → POST /comms/from-human → Appends to from_human.md
Agent reads from_human.md → Responds in to_human.md

Token tracking:
Agent makes API call → POST /tokens/record → In-memory accumulation
UI polls /tokens → Gets cumulative usage + safety tier
Safety tier changes → WebSocket broadcasts update
```

## File-Based Data (not SQLite)

DunkStack uses `.agent/` directory in the project folder:

```
.agent/
├── comms/
│   ├── to_human.md         Agent → human messages
│   ├── from_human.md       Human → agent messages
│   └── control.md          Session mode (idle/continue/autopilot)
├── knowledge/              Agent's accumulated knowledge
├── output/                 Agent's output artifacts
├── progress/
│   └── build_log.md        Build progress log
├── settings/
│   └── config.yml          Session configuration
├── working_memory.md       Agent's current working state
├── index.md                File index for the project
└── bridge.md               Session continuity bridge
```

## API Endpoints

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/api/dunkstack/comms/to-human` | Read agent messages |
| GET | `/api/dunkstack/comms/from-human` | Read human messages |
| POST | `/api/dunkstack/comms/from-human` | Send message to agent |
| GET/POST | `/api/dunkstack/control` | Read/update session mode |
| GET | `/api/dunkstack/working-memory` | Read agent working memory |
| GET | `/api/dunkstack/index` | Read file index |
| GET/POST | `/api/dunkstack/bridge` | Read/save bridge state |
| GET/PATCH | `/api/dunkstack/config` | Read/update YAML config |
| GET | `/api/dunkstack/tokens` | Token state + safety tier |
| POST | `/api/dunkstack/tokens/record` | Record token snapshot |
| POST | `/api/dunkstack/tokens/reset` | Reset token tracking |
| GET | `/api/dunkstack/tokens/log` | Full token log |
| GET | `/api/dunkstack/build-log` | Read build log |
| WS | `/api/dunkstack/ws` | Real-time updates |

## Safety Tiers

| Tier | Label | Threshold | Action |
|------|-------|-----------|--------|
| 0 | OK | 0% | Normal operation |
| 1 | WARNING | 45% | Alert user, suggest saving bridge |
| 2 | HANDOFF | 47.5% | Prepare bridge, stop new features |
| 3 | HARD STOP | 50% | Force bridge save, stop agent |

## Key Types (in types.ts)

- `DunkStackTokenState` — cumulative tokens, cost, API calls, usage %, safety tier
- `DunkStackSafetyStatus` — tier number, label, color, message
- `DunkStackCommsResponse` — content string + exists boolean
- `DunkStackConfigResponse` — config object + exists boolean

## Common Modifications

- **Change safety thresholds:** `server/routers/dunkstack.py` (tier calculation) + `DunkStackSafetyPanel.tsx`
- **Add new comms channel:** `dunkstack.py` (new endpoint) + `useDunkStack.ts` (new state) + `DunkStackCommsChat.tsx`
- **Add new file viewer tab:** `DunkStackPage.tsx` (tab list + content)
- **Change token tracking:** `dunkstack.py` (`/tokens/record` endpoint) + `DunkStackContextGauge.tsx`
