# Spec 010 — n8n Flow Translator (Agent-Powered)

## What This Is
An agent workflow that translates n8n workflow JSON into Activepieces flow JSON. There is no code bridge, no deterministic converter, no mapping script. Claude IS the bridge. The agent has two MCP servers — one that understands n8n (1,200 nodes) and one that understands Activepieces (280+ nodes). It reads the n8n flow through one MCP, understands what every step does, then builds the equivalent in Activepieces through the other MCP.

Think of it like translating French to English. The agent reads French (n8n JSON), understands the meaning (what the workflow does), and writes it in English (Activepieces JSON). There's no word-for-word dictionary — it's comprehension-based translation.

## Why It Matters
There are 30-40 proven, working n8n workflow JSONs available from school groups, community templates, and existing builds. Rebuilding those from scratch in Activepieces would take weeks. Translating them takes minutes per workflow. This is also an onboarding feature: "Bring your existing n8n workflows, we'll convert them."

The n8n ecosystem exploded. There are thousands of community-built workflows. Every one of them is a potential import into your platform. That's a massive head start on building a template library.

---

## The Tools the Agent Has

| Tool | What It Does | Node Count |
|------|-------------|-----------|
| n8n MCP server | Reads and understands n8n workflow JSON — every node type, every setting, every connection | ~1,200 nodes |
| Activepieces MCP server | Reads AP piece schemas, creates flows, manages nodes | 280+ nodes |
| Context7 (activepieces/activepieces) | Live accurate docs for every AP piece — field names, types, valid values | 768 snippets |
| Context7 (n8n) | n8n node documentation when needed for ambiguous nodes | Available |
| Existing node mapping reference | Previous agent pass that matched n8n nodes to AP equivalents | Reference doc |

---

## The Translation Flow

```
User provides n8n workflow JSON
  (paste, file upload, or URL)
        |
        v
STEP 1: COMPREHENSION
  Agent reads the n8n JSON using n8n MCP
  For each node, agent understands:
  - What the node does (function)
  - What settings are configured (parameters)
  - What connects to what (wiring / execution order)
  - What data flows between nodes (input/output shapes)
        |
        v
STEP 2: MAPPING
  Agent maps each n8n node to its Activepieces equivalent:
  - HTTP Request -> @activepieces/piece-http
  - Gmail -> @activepieces/piece-gmail
  - Schedule Trigger -> @activepieces/piece-schedule
  - IF -> ROUTER action type
  - Set -> Code action (JS assignment)
  - etc.
  
  Agent consults the node mapping reference doc first.
  For any node NOT in the reference: flag it.
        |
        v
STEP 3: FLAG UNMAPPED NODES
  Some n8n nodes won't have AP equivalents:
  - Custom n8n Function nodes -> Flag as "needs Code Module"
  - n8n-specific nodes with no AP match -> Flag for manual review
  - Rare integrations -> Check if AP has it, flag if not
  
  Agent produces a compatibility report:
  {
    "total_nodes": 12,
    "direct_match": 10,
    "needs_code_module": 1,
    "no_equivalent": 1,
    "compatibility_score": "83%"
  }
        |
        v
STEP 4: GENERATE AP FLOW JSON
  Using Context7 for exact AP piece schemas:
  - Pull schema for each mapped piece (pieceName, actionName, input fields)
  - Generate FlowVersion JSON (schemaVersion "21")
  - Wire nodes in correct order (linked list via nextAction)
  - Map n8n variable references to AP format ({{step_N.output.field}})
  - Include errorHandlingOptions on every PieceAction
        |
        v
STEP 5: VERIFICATION AGENT
  A second agent reviews the translation:
  - Reads original n8n JSON
  - Reads generated AP JSON
  - Checks: does every n8n node have a corresponding AP node?
  - Checks: are the connections wired the same way?
  - Checks: are settings mapped correctly (not just node types)?
  - Flags any discrepancies
  
  If discrepancies found: first agent revises.
  If clean: proceed to injection.
        |
        v
STEP 6: INJECT VIA IMPORT_FLOW
  Two-call pattern:
  POST /v1/flows (create empty flow)
  POST /v1/flows/{id} (IMPORT_FLOW with complete definition)
  
  Flow appears in AP builder, fully built.
        |
        v
STEP 7: HUMAN REVIEW
  User opens AP builder, reviews the translated flow.
  For flagged nodes (needs Code Module): user fills the 7-step form
  to build custom logic for those specific steps.
```

---

## Common Node Mappings (Reference)

| n8n Node | Activepieces Equivalent | Notes |
|----------|------------------------|-------|
| Schedule Trigger | @activepieces/piece-schedule | Direct match |
| Webhook | @activepieces/piece-webhook | Direct match |
| HTTP Request | @activepieces/piece-http | Direct match, map method/headers/body |
| Gmail (send) | @activepieces/piece-gmail / send_email | Map to/subject/body fields |
| Gmail (trigger) | @activepieces/piece-gmail / new_email | Direct match |
| Slack (send) | @activepieces/piece-slack / send_message | Map channel/text |
| Google Sheets (append) | @activepieces/piece-google-sheets / append_row | Map spreadsheet ID + row data |
| IF | ROUTER action type | Map conditions to branch definitions |
| Switch | ROUTER with EXECUTE_FIRST_MATCH | Multiple branches |
| Set | Code action (JS) | Simple variable assignment |
| Function | Code Module node | Custom JS -> needs 7-step form |
| Function Item | Code Module node (per-item) | Inside a loop |
| Loop Over Items | LOOP_ON_ITEMS action type | Map items reference |
| Merge | Code action | Combine data streams |
| Wait | @activepieces/piece-delay | Map duration |
| OpenAI / Claude | @activepieces/piece-openai or piece-anthropic | Map model/prompt/params |
| Notion | @activepieces/piece-notion | Map database/page operations |
| Airtable | @activepieces/piece-airtable | Map base/table/record operations |
| Discord | @activepieces/piece-discord | Map channel/message |
| RSS Feed | @activepieces/piece-rss | Map feed URL |

This mapping covers roughly 80% of nodes in typical n8n workflows. The rest are either rare integrations or custom functions.

---

## The Agent Prompts

### Translation Agent Prompt
```
You are translating an n8n workflow into an Activepieces flow.

You have access to:
- n8n MCP: understands every n8n node type and its settings
- Activepieces MCP: knows every AP piece, action, and required field
- Context7 (activepieces/activepieces): live accurate schemas for AP pieces
- Node mapping reference (below)

PROCESS:
1. Read the n8n JSON completely. Understand every node and connection.
2. For each n8n node, find the AP equivalent using the mapping reference.
3. If no mapping exists, check if AP has the integration. If not, flag as "needs Code Module."
4. Pull the exact AP piece schema from Context7 BEFORE generating any node config.
5. Generate complete FlowVersion JSON (schemaVersion "21").
6. Wire nodes in the same execution order as the original n8n flow.
7. Map variable references: n8n uses {{$node["name"].json["field"]}} -> AP uses {{step_N.output.field}}

NODE MAPPING REFERENCE:
{node_mapping_table}

INPUT: The complete n8n workflow JSON.
OUTPUT: 
1. Compatibility report (total nodes, direct matches, needs code module, no equivalent)
2. Complete AP FlowVersion JSON
3. List of flagged nodes with explanation of what's needed

Never guess at AP piece field names. Always pull from Context7 first.
```

### Verification Agent Prompt
```
You are reviewing a translation from n8n workflow to Activepieces flow.

ORIGINAL n8n JSON:
{n8n_json}

TRANSLATED AP JSON:
{ap_json}

COMPATIBILITY REPORT:
{compatibility_report}

CHECK EACH OF THESE:
1. Does every n8n node have a corresponding AP node? (count should match minus flagged)
2. Are connections wired the same way? (execution order preserved)
3. For each matched node pair: are the key settings mapped correctly?
   - URLs, API endpoints
   - Email addresses, channel IDs
   - Prompt text, model names
   - Filter conditions, branch logic
4. Are variable references translated correctly?
   n8n: {{$node["Step1"].json["email"]}} -> AP: {{step_1.output.email}}
5. Are there any nodes in the AP flow that don't correspond to anything in n8n? (shouldn't be)

OUTPUT:
{
  "verified": true/false,
  "issues": [{"node": "step_N", "problem": "description", "severity": "low/medium/high"}],
  "confidence_score": "0-100%"
}

Be strict. A confident translation should score 90%+.
```

---

## Handling Partial Translations

Not every n8n workflow will translate 100%. The system handles partial translations gracefully:

```
Translation result:
  - 10/12 nodes translated directly
  - 1 node flagged as "needs Code Module" (custom JS function)
  - 1 node flagged as "no AP equivalent" (rare integration)

The 10 translated nodes get injected via IMPORT_FLOW.
The Code Module placeholder gets added with empty generated_code
  and a note in the purpose field: "Translated from n8n Function node.
  Original logic: [pasted from n8n]. Fill 7-step form to rebuild."
The no-equivalent node gets a comment node: "MANUAL: n8n had [node name]
  here. No AP equivalent found. Options: build custom piece or restructure."
```

The flow still works for the parts that translated. The gaps are clearly marked.

---

## Dependencies

| Spec | What This Spec Needs From It |
|------|------------------------------|
| Spec 001 — AP Foundation | Running AP instance, API access, IMPORT_FLOW two-call pattern |
| Spec 002 — AI Co-pilot | Flow JSON generation patterns, FlowVersion schema knowledge |
| Spec 004 — Code Module | Unmapped n8n Function nodes get flagged for Code Module |
| Spec 008 — MCP/Skills | n8n MCP server and AP MCP server must be connected and operational |

Specs 001 and 008 MUST be complete before starting this spec. Specs 002 and 004 are soft dependencies — the translator references their patterns but doesn't import their code.

---

## Mechanism Blueprint

| Step | Classification | What It Does | AI Involved? |
|------|---------------|-------------|--------------|
| Node Mapping Reference | WALL | Static JSON lookup table. n8n node type → AP piece name. Deterministic. | No |
| Compatibility Report | WALL | Count matched, unmatched, code-module-needed nodes. Arithmetic. | No |
| Translation Agent | DOOR | Claude reads n8n JSON via MCP, maps each node using reference + Context7, generates AP FlowVersion JSON. Must use Context7 for field names, must follow mapping reference first. | Yes — constrained |
| Verification Agent | DOOR | Second Claude call reviews translation. Checks node count, wiring, settings. Returns confidence score. Binary checks, strict comparison. | Yes — constrained |
| Flow Injection | WALL | Two AP API calls: POST create empty flow, POST IMPORT_FLOW with definition. Deterministic HTTP. | No |

**Key insight:** Two DOOR steps (Translation + Verification) use AI, but both are constrained by the node mapping reference and Context7 schemas. The agent can't hallucinate piece names because Context7 grounds it against real AP schemas.

---

## Build Order

| # | File | Depends On | Creates |
|---|------|-----------|---------|
| 1 | `translator/node_mapping.json` | Nothing | Static n8n→AP node mapping (15+ entries) |
| 2 | `translator/compatibility_report.py` | node_mapping.json | `generate_report()` function |
| 3 | `translator/translate_flow.py` | node_mapping.json, compatibility_report | `translate_n8n_to_ap()` function, translation agent prompt |
| 4 | `translator/verify_translation.py` | translate_flow output format | `verify_translation()` function, verification agent prompt |

---

## File Sandbox

| Category | Files |
|----------|-------|
| **Creates** | `translator/node_mapping.json`, `translator/compatibility_report.py`, `translator/translate_flow.py`, `translator/verify_translation.py` |
| **Reads** | n8n MCP (external), AP MCP (external), Context7 (external), AP API (`/api/v1/flows`), `.env` (AP_API_KEY, AP_BASE_URL) |
| **Must NOT touch** | `healing/`, `pieces/`, `skin/`, `copilot/`, `docker-compose.yml`, AP internal configuration, any file outside `translator/` |

---

## Success Criteria

- [ ] Agent reads an n8n workflow JSON and produces a compatibility report
- [ ] Direct-match nodes translate with correct pieceName and actionName
- [ ] Variable references translate from n8n format to AP format
- [ ] Verification agent catches at least one deliberately wrong mapping in a test
- [ ] IMPORT_FLOW injects the translated flow and it appears in the AP builder
- [ ] Unmapped nodes are flagged (not silently dropped)
- [ ] A 10-node n8n workflow translates in under 5 minutes
- [ ] The translated flow runs successfully on manual trigger (for the mapped nodes)

---

## Protocol Checkpoints (Stage 08 Injection)

### Pulse Checks — After Each File (matches Build Order)
| File | Assertions |
|------|-----------|
| `translator/node_mapping.json` | File exists; valid JSON; contains at least 15 n8n→AP node mappings; every entry has `n8n_type` and `ap_piece` keys |
| `translator/compatibility_report.py` | File exists; `generate_report()` function present; output dict contains `total_nodes`, `direct_match`, `needs_code_module`, `no_equivalent` fields |
| `translator/translate_flow.py` | File exists; `translate_n8n_to_ap()` function present; translation agent prompt defined; contains "n8n" and "Activepieces" and "FlowVersion" |
| `translator/verify_translation.py` | File exists; `verify_translation()` function present; verification prompt defined; checks node count, wiring, and settings; returns `confidence_score` |

### Seam Checks — Connection Points
**Seam 1: n8n JSON -> Translation Agent**
- Agent receives valid n8n workflow JSON
- Agent identifies all nodes and their types
- Agent produces a node-by-node mapping list

**Seam 2: Translation Agent -> AP FlowVersion JSON**
- Generated JSON has `schemaVersion: "21"`
- Generated JSON has valid `trigger` with `nextAction` chain
- Every `pieceName` in the JSON matches a real AP piece (no hallucinated names)

**Seam 3: Translation -> Verification Agent**
- Verification agent receives both JSONs (original n8n + translated AP)
- Verification checks node count matches (minus flagged nodes)
- Verification returns confidence score

**Seam 4: Verified JSON -> IMPORT_FLOW**
- Only inject after verification confidence >= 80%
- IMPORT_FLOW returns HTTP 200
- Flow appears in AP builder with correct node count

### Full Checkpoint (Phase 10 Gate)
**Pattern checks (git diff):**
```
Expected new directory: translator/ (or skill files in .claude/skills/)
Expected files: translate_flow.py, verify_translation.py, node_mapping.json
No modification to healing/, pieces/, skin/, or copilot/.
```

**Functional checks:**
```bash
# Test with a simple 3-node n8n workflow (Schedule -> HTTP -> Gmail)
python -c "
from translator.translate_flow import translate_n8n_to_ap

test_n8n = {
    'nodes': [
        {'type': 'n8n-nodes-base.scheduleTrigger', 'name': 'Schedule'},
        {'type': 'n8n-nodes-base.httpRequest', 'name': 'Fetch Data', 
         'parameters': {'url': 'https://httpbin.org/get', 'method': 'GET'}},
        {'type': 'n8n-nodes-base.gmail', 'name': 'Send Email',
         'parameters': {'to': 'test@test.com', 'subject': 'Report'}}
    ],
    'connections': {
        'Schedule': {'main': [[{'node': 'Fetch Data'}]]},
        'Fetch Data': {'main': [[{'node': 'Send Email'}]]}
    }
}

result = translate_n8n_to_ap(test_n8n)
assert result['compatibility']['direct_match'] >= 2, 'Should match at least 2 nodes'
assert 'schemaVersion' in str(result['ap_flow']), 'Should generate AP flow JSON'
print('Translation test passed')
print(f'Compatibility: {result[\"compatibility\"]}')"
```

**Gate condition:** Simple n8n workflow translates with 2+ direct matches. AP JSON contains valid `schemaVersion`. Verification agent returns 80%+ confidence. IMPORT_FLOW succeeds. PASS or FAIL.

### Violation Rules
| Level | Trigger | Action |
|-------|---------|--------|
| LOW | Translation works but display names don't match original | Log, cosmetic issue |
| MEDIUM | One node's settings are partially mapped (some fields missing) | Fix mapping, add Context7 lookup for that piece |
| HIGH | Verification agent returns <60% confidence | Stop translation, review node mapping reference |
| CRITICAL | Agent hallucinates AP piece names not in the real registry | Stop — Context7 integration broken; fix schema grounding |

### Two-Strike Rule
Max 2 translation attempts per workflow. If the same workflow fails verification twice, stop for human review — likely a structural incompatibility that needs manual architecture decisions.
