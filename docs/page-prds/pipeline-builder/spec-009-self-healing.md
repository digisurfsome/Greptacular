# Spec 009 — Self-Healing System

## What This Is
An automated system that detects node failures during pipeline runs, classifies the error type, attempts an AI-powered fix scoped to only the broken node, verifies the fix by replaying the failed input, and either deploys the patch or escalates to a human. The fix agent cannot see or touch anything else in the pipeline — it only has access to the broken node's code, the error, and the input that caused the failure.

## Why It Matters
This is the product's actual moat. n8n has zero auto-healing. Make has zero auto-healing. Zapier has zero auto-healing. Every automation platform today requires a human to diagnose and fix broken flows manually. The self-healing system handles 60-70% of real-world breaks automatically. The remaining 30-40% (like "this entire API no longer exists") still need human judgment, but the agent surfaces full context so fix time goes from hours to minutes.

The dirty secret of the automation agency world: the people running 50+ client pipelines spend 30-40% of their time on maintenance. This system cuts that to under 10%.

---

## What Actually Breaks in Production (The Honest List)

| Break Type | Cause | Frequency | Auto-Fixable? |
|-----------|-------|-----------|---------------|
| API endpoint changed | Third party updated their API | Weekly across a portfolio | Yes — agent searches for new endpoint |
| Auth token expired | OAuth token wasn't refreshed | Monthly | No — requires human to reconnect credentials |
| DOM changed | Website redesigned (scrapers) | Constant | Partially — agent can update selectors |
| Rate limit hit | Client scaled up or API tightened limits | Unpredictable | Yes — add backoff, reduce batch size |
| Data format changed | API returns different JSON shape | Common | Yes — update parsing logic |
| Silent failure | No error handling, node just dies | Every time without the 7-step form | Yes — add error handling |
| Network timeout | Transient connectivity issue | Occasional | Yes — add retry logic |

---

## The Full Self-Healing Flow

```
Pipeline runs
        |
Node fails during execution
        |
        v
ERROR CAPTURE
  Saves: {
    error_message: string,
    error_type: string,
    node_name: string,
    node_code: string,
    input_that_caused_failure: object,
    previous_node_output: object,
    timestamp: ISO string,
    flow_id: string,
    run_id: string
  }
        |
        v
ERROR CLASSIFIER
  Pattern-matches the error into a category:
  - "rate_limit"        -> add backoff, reduce batch size
  - "auth_expired"      -> flag for human (can't auto-fix credentials)
  - "network_timeout"   -> add retry logic
  - "data_format"       -> update parsing logic
  - "api_endpoint"      -> search for new endpoint docs
  - "dom_changed"       -> update CSS selectors / XPath
  - "unknown"           -> send to Claude with full context
        |
        v
KNOWLEDGE BASE CHECK
  Has this exact error pattern been fixed before?
  - Yes -> apply the known fix directly (skip Claude call)
  - No  -> proceed to fix agent
        |
        v
FIX AGENT (scoped to ONE node only)
  Receives: broken code + exact error + input that caused it
  Cannot see: any other node, the flow structure, other pipelines
  Writes: patched version of just that node's code
        |
        v
VERIFICATION
  Replay the failed input against the patched code
        |
    +---+---+
    |       |
  PASS    FAIL
    |       |
    v       v
  Deploy  Retry (max 3 attempts)
  patch       |
    |     Still failing?
    |         |
    v         v
  Log to   ESCALATE to human
  knowledge  with full context:
  base       - original error
    |        - what was tried
    |        - why it failed
    v
  Notify owner
  "Node X broke, auto-fixed, verify when you can"
```

---

## Implementation

### The Error Capture Data Structure

```python
# healing/error_capture.py
from dataclasses import dataclass, asdict
from datetime import datetime
import json

@dataclass
class CapturedError:
    error_message: str
    error_type: str          # Python exception type name
    node_name: str           # e.g. "step_3"
    node_code: str           # the generated_code from the Code Module
    failed_input: dict       # the input that caused the failure
    previous_output: dict    # what the upstream node sent
    flow_id: str
    run_id: str
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
```

### The Error Classifier

```python
# healing/classifier.py
import re

class ErrorClassifier:
    """
    Pattern-matches an error into a fixable category.
    Returns the category string + a recommended fix strategy.
    """

    PATTERNS = [
        # Rate limiting
        (r"(429|rate.?limit|too many requests|throttl)", "rate_limit",
         "Add exponential backoff. Reduce batch size. Add delay between calls."),

        # Auth / credentials
        (r"(401|403|unauthorized|forbidden|token.?expired|invalid.?credentials|oauth)",
         "auth_expired",
         "Cannot auto-fix. Credentials need manual refresh by human."),

        # Network / timeout
        (r"(timeout|timed?.?out|ECONNREFUSED|ENOTFOUND|network|socket.?hang)",
         "network_timeout",
         "Add retry with exponential backoff. Max 3 retries. Increase timeout."),

        # Data format changed
        (r"(undefined is not|cannot read prop|TypeError|KeyError|JSON.?parse|unexpected token)",
         "data_format",
         "The data shape changed. Update parsing logic to handle the new format."),

        # API endpoint moved / changed
        (r"(404|not.?found|endpoint.?not|moved.?permanently|301|302|deprecated)",
         "api_endpoint",
         "Search for new endpoint URL in API docs. Update the URL and parameters."),

        # DOM / scraping
        (r"(selector|element.?not.?found|no.?such.?element|xpath|queryselector)",
         "dom_changed",
         "Website layout changed. Update CSS selectors or XPath expressions."),
    ]

    @classmethod
    def classify(cls, error: 'CapturedError') -> tuple[str, str]:
        """Returns (category, fix_strategy)."""
        error_text = f"{error.error_message} {error.error_type}".lower()

        for pattern, category, strategy in cls.PATTERNS:
            if re.search(pattern, error_text, re.IGNORECASE):
                return category, strategy

        return "unknown", "Send full context to Claude agent for diagnosis."

    @classmethod
    def is_auto_fixable(cls, category: str) -> bool:
        """Auth issues require human intervention. Everything else is attempted."""
        return category != "auth_expired"
```

### The Knowledge Base

```python
# healing/knowledge_base.py
import json
from pathlib import Path
from datetime import datetime

KNOWLEDGE_BASE_PATH = Path("healing/known_fixes.json")

class HealingKnowledgeBase:
    """
    Stores error pattern -> fix pattern mappings.
    Gets smarter with every fix across every pipeline.
    """

    def __init__(self):
        self.fixes = self._load()

    def _load(self) -> list[dict]:
        if KNOWLEDGE_BASE_PATH.exists():
            return json.loads(KNOWLEDGE_BASE_PATH.read_text())
        return []

    def _save(self):
        KNOWLEDGE_BASE_PATH.write_text(json.dumps(self.fixes, indent=2))

    def find_known_fix(self, error: 'CapturedError') -> dict | None:
        """
        Search for a previously successful fix for this error pattern.
        Matches on: error_type + first line of error_message + category.
        """
        from healing.classifier import ErrorClassifier
        category, _ = ErrorClassifier.classify(error)
        error_sig = f"{error.error_type}:{error.error_message.split(chr(10))[0]}"

        for fix in self.fixes:
            if fix["error_signature"] == error_sig and fix["category"] == category:
                return fix

        return None

    def log_fix(self, error: 'CapturedError', category: str,
                fix_code: str, attempts: int, success: bool):
        """Log a fix attempt (successful or not) for future reference."""
        error_sig = f"{error.error_type}:{error.error_message.split(chr(10))[0]}"

        entry = {
            "error_signature": error_sig,
            "category": category,
            "original_error": error.error_message[:500],
            "node_name": error.node_name,
            "flow_id": error.flow_id,
            "fix_code": fix_code if success else None,
            "attempts": attempts,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.fixes.append(entry)
        self._save()
```

### The Fix Agent — Scoped Prompt

```python
# healing/fix_agent.py
import json

SCOPED_FIX_PROMPT = """
You are fixing a single broken node in an Activepieces pipeline.

SCOPE: You can ONLY see and modify THIS node's code. You cannot see or touch any other
node in the pipeline. You cannot modify the flow structure. You fix this one function.

THE ERROR:
{error_message}

ERROR CATEGORY: {category}
RECOMMENDED STRATEGY: {fix_strategy}

THE BROKEN CODE:
```javascript
{node_code}
```

THE INPUT THAT CAUSED THE FAILURE:
```json
{failed_input}
```

THE PREVIOUS NODE'S OUTPUT (what was sent to this node):
```json
{previous_output}
```

{knowledge_base_context}

RULES:
- Return ONLY the fixed JavaScript code (no import statements, no wrappers)
- The code must work as: const fn = new Function('input', 'context', code)
- Fix the specific error. Do not rewrite unrelated parts.
- If the data format changed, handle BOTH the old and new format
- Add error handling for this specific failure case
- The return value shape must not change (downstream nodes depend on it)

Return the fixed function body only. No explanation. No markdown.
"""


class FixAgent:
    def __init__(self, claude_client):
        self.client = claude_client

    def attempt_fix(self, error, category: str, fix_strategy: str) -> str | None:
        """
        Call Claude with scoped context to fix the broken node.
        Returns the patched code string, or None if Claude can't fix it.
        """
        from healing.knowledge_base import HealingKnowledgeBase
        kb = HealingKnowledgeBase()

        known = kb.find_known_fix(error)
        kb_context = ""
        if known and known.get("fix_code"):
            kb_context = (
                "KNOWN FIX FROM PREVIOUS OCCURRENCE:\n"
                "This exact error was fixed before. Here's what worked:\n"
                f"```javascript\n{known['fix_code']}\n```\n"
                "Use this as your starting point."
            )

        prompt = SCOPED_FIX_PROMPT.format(
            error_message=error.error_message,
            category=category,
            fix_strategy=fix_strategy,
            node_code=error.node_code,
            failed_input=json.dumps(error.failed_input, indent=2),
            previous_output=json.dumps(error.previous_output, indent=2),
            knowledge_base_context=kb_context
        )

        resp = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        return resp.content[0].text
```

### The Verification Replay

```python
# healing/verifier.py

class PatchVerifier:
    """Replays the failed input against the patched code to verify the fix."""

    @staticmethod
    def verify(patched_code: str, failed_input: dict,
               expected_output_shape: dict | None = None) -> dict:
        """
        Run the patched code with the input that originally caused the failure.
        Returns { passed: bool, output: any, error: str | None }
        """
        try:
            exec_globals = {}
            indented = "\n".join(("    " + line) for line in patched_code.split("\n"))
            exec(f"async def _test_fn(input_data, context):\n{indented}", exec_globals)

            import asyncio
            mock_context = {"externalCall": lambda p, a: {"mock": True}}
            output = asyncio.run(exec_globals['_test_fn'](failed_input, mock_context))

            if expected_output_shape and output:
                for key in expected_output_shape:
                    if key not in output:
                        return {
                            "passed": False,
                            "output": output,
                            "error": f"Output missing expected key: {key}"
                        }

            return {"passed": True, "output": output, "error": None}

        except Exception as e:
            return {"passed": False, "output": None, "error": str(e)}
```

### The Orchestrator

```python
# healing/orchestrator.py
import requests
import json
from healing.error_capture import CapturedError
from healing.classifier import ErrorClassifier
from healing.knowledge_base import HealingKnowledgeBase
from healing.fix_agent import FixAgent
from healing.verifier import PatchVerifier

class SelfHealingOrchestrator:
    """
    Main entry point. Called when any node fails during a pipeline run.
    Orchestrates: capture -> classify -> check KB -> fix -> verify -> deploy/escalate.
    """

    MAX_ATTEMPTS = 3

    def __init__(self, ap_base_url: str, ap_api_key: str, claude_client):
        self.ap_base = ap_base_url
        self.headers = {
            "Authorization": f"Bearer {ap_api_key}",
            "Content-Type": "application/json"
        }
        self.classifier = ErrorClassifier()
        self.fix_agent = FixAgent(claude_client)
        self.verifier = PatchVerifier()
        self.kb = HealingKnowledgeBase()

    def handle_failure(self, error: CapturedError) -> dict:
        """
        Main entry point. Returns:
        { resolved: bool, method: str, attempts: int, details: str }
        """
        # Step 1: Classify
        category, fix_strategy = self.classifier.classify(error)

        # Step 2: Check if auto-fixable
        if not self.classifier.is_auto_fixable(category):
            self._notify_human(error, category,
                "Cannot auto-fix. Requires manual credential refresh.")
            return {
                "resolved": False,
                "method": "escalated_immediately",
                "attempts": 0,
                "details": f"Category '{category}' requires human intervention."
            }

        # Step 3: Check knowledge base for known fix
        known_fix = self.kb.find_known_fix(error)
        if known_fix and known_fix.get("fix_code"):
            result = self.verifier.verify(known_fix["fix_code"], error.failed_input)
            if result["passed"]:
                self._deploy_patch(error, known_fix["fix_code"])
                self._notify_owner(error, "auto-fixed (known pattern)", 1)
                return {
                    "resolved": True,
                    "method": "knowledge_base",
                    "attempts": 1,
                    "details": "Applied known fix from previous occurrence."
                }

        # Step 4: Attempt fix with Claude (up to MAX_ATTEMPTS)
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            patched_code = self.fix_agent.attempt_fix(error, category, fix_strategy)
            if not patched_code:
                continue

            result = self.verifier.verify(patched_code, error.failed_input)
            if result["passed"]:
                self._deploy_patch(error, patched_code)
                self.kb.log_fix(error, category, patched_code, attempt, success=True)
                self._notify_owner(error, f"auto-fixed (attempt {attempt})", attempt)
                return {
                    "resolved": True,
                    "method": "ai_fix",
                    "attempts": attempt,
                    "details": f"Fixed by Claude on attempt {attempt}."
                }

        # Step 5: All attempts failed — escalate
        self.kb.log_fix(error, category, "", self.MAX_ATTEMPTS, success=False)
        self._escalate_to_human(error, category, self.MAX_ATTEMPTS)
        return {
            "resolved": False,
            "method": "escalated_after_attempts",
            "attempts": self.MAX_ATTEMPTS,
            "details": f"Failed after {self.MAX_ATTEMPTS} attempts. Escalated."
        }

    def _deploy_patch(self, error: CapturedError, patched_code: str):
        """Update the node's generated_code in the AP flow."""
        requests.post(
            f"{self.ap_base}/api/v1/flows/{error.flow_id}",
            headers=self.headers,
            json={
                "type": "UPDATE_ACTION",
                "request": {
                    "name": error.node_name,
                    "settings": {"generated_code": patched_code}
                }
            }
        )

    def _notify_owner(self, error: CapturedError, method: str, attempts: int):
        print(f"[SELF-HEALING] {error.flow_id}/{error.node_name}: {method} ({attempts} attempts)")

    def _notify_human(self, error: CapturedError, category: str, reason: str):
        print(f"[ESCALATION] {error.flow_id}/{error.node_name}: {reason}")

    def _escalate_to_human(self, error: CapturedError, category: str, attempts: int):
        print(f"[ESCALATION] {error.flow_id}/{error.node_name}: "
              f"Failed after {attempts} attempts. Category: {category}")
```

### Run Monitor

```python
# healing/monitor.py
import requests
from healing.error_capture import CapturedError

def monitor_failed_runs(ap_base: str, headers: dict, project_id: str, orchestrator):
    """
    Poll for failed runs and trigger self-healing.
    In production: webhook listener or scheduled task.
    """
    resp = requests.get(
        f"{ap_base}/api/v1/flow-runs",
        headers=headers,
        params={"projectId": project_id, "status": "FAILED", "limit": 10}
    )

    for run in resp.json()["data"]:
        failed_step = _find_failed_step(run)
        if not failed_step:
            continue

        error = CapturedError(
            error_message=failed_step.get("errorMessage", "Unknown error"),
            error_type=failed_step.get("errorType", "Unknown"),
            node_name=failed_step["stepName"],
            node_code=_get_node_code(ap_base, headers, run["flowId"],
                                     failed_step["stepName"]),
            failed_input=failed_step.get("input", {}),
            previous_output=_get_previous_output(run, failed_step["stepName"]),
            flow_id=run["flowId"],
            run_id=run["id"]
        )

        result = orchestrator.handle_failure(error)
        print(f"  [{error.node_name}] -> {result['method']} "
              f"(resolved={result['resolved']})")


def _find_failed_step(run: dict) -> dict | None:
    """Find the first failed step in a flow run."""
    for step_name, step_data in run.get("steps", {}).items():
        if step_data.get("status") == "FAILED":
            return {"stepName": step_name, **step_data}
    return None


def _get_node_code(ap_base, headers, flow_id, step_name) -> str:
    """Retrieve the generated_code for a specific node."""
    resp = requests.get(f"{ap_base}/api/v1/flows/{flow_id}", headers=headers)
    flow = resp.json()
    # Walk the action chain to find the step
    action = flow.get("version", {}).get("trigger", {}).get("nextAction")
    while action:
        if action.get("name") == step_name:
            return action.get("settings", {}).get("input", {}).get("generated_code", "")
        action = action.get("nextAction")
    return ""


def _get_previous_output(run: dict, failed_step_name: str) -> dict:
    """Get the output of the step before the failed one."""
    steps = run.get("steps", {})
    prev_output = {}
    for step_name, step_data in steps.items():
        if step_name == failed_step_name:
            return prev_output
        prev_output = step_data.get("output", {})
    return prev_output
```

---

## Directory Structure

```
healing/
    __init__.py
    error_capture.py        # CapturedError dataclass
    classifier.py           # ErrorClassifier with pattern matching
    knowledge_base.py       # Known fixes storage + lookup
    fix_agent.py            # Claude-powered fix agent (scoped prompt)
    verifier.py             # Replay verification
    orchestrator.py         # Main orchestrator (ties everything together)
    monitor.py              # AP run monitoring / failure detection
    known_fixes.json        # Knowledge base data file (auto-generated)
```

---

## Dependencies

| Spec | What This Spec Needs From It |
|------|------------------------------|
| Spec 001 — AP Foundation | Running AP instance, API access, bearer token auth |
| Spec 004 — Code Module | The `generated_code` field in Code Module nodes is what the fix agent patches |
| Spec 006 — Testing Layer | Verification replay pattern mirrors the testing layer's validation approach |

Specs 001 and 004 MUST be complete before starting this spec. Spec 006 is a soft dependency — the patterns are similar but not a hard blocker.

---

## Mechanism Blueprint

| Step | Classification | What It Does | AI Involved? |
|------|---------------|-------------|--------------|
| Error Capture | WALL | Captures error data into structured dataclass. Pure data extraction. | No |
| Error Classifier | WALL | Regex pattern matching against known error categories. Deterministic. | No |
| Knowledge Base Lookup | WALL | JSON file read/write. Exact signature matching. Deterministic. | No |
| Fix Agent | DOOR | Claude generates a patch for ONE node. Scoped prompt — can only see broken node's code, error, and input. Cannot see flow structure or other nodes. | Yes — constrained |
| Patch Verification | WALL | Replay failed input against patched code. Binary pass/fail. | No |
| Orchestration | WALL | Decision tree: classify → check KB → fix → verify → deploy/escalate. Deterministic flow control. | No |
| Run Monitor | WALL | Poll AP API for failed runs. Extract error data. Deterministic. | No |

**Key insight:** Only ONE step (Fix Agent) uses AI, and it's tightly DOOR-constrained. The rest is deterministic WALL logic. This is intentional — the self-healing system itself should not need healing.

---

## Build Order

Files must be created in this sequence. Each file's dependencies are listed.

| # | File | Depends On | Creates |
|---|------|-----------|---------|
| 1 | `healing/__init__.py` | Nothing | Package marker |
| 2 | `healing/error_capture.py` | Nothing | `CapturedError` dataclass |
| 3 | `healing/classifier.py` | error_capture | `ErrorClassifier` class |
| 4 | `healing/knowledge_base.py` | error_capture, classifier | `HealingKnowledgeBase` class |
| 5 | `healing/fix_agent.py` | knowledge_base, error_capture | `FixAgent` class, `SCOPED_FIX_PROMPT` |
| 6 | `healing/verifier.py` | Nothing (standalone) | `PatchVerifier` class |
| 7 | `healing/orchestrator.py` | All above | `SelfHealingOrchestrator` class |
| 8 | `healing/monitor.py` | error_capture, orchestrator | `monitor_failed_runs()` function |

---

## File Sandbox

| Category | Files |
|----------|-------|
| **Creates** | `healing/__init__.py`, `healing/error_capture.py`, `healing/classifier.py`, `healing/knowledge_base.py`, `healing/fix_agent.py`, `healing/verifier.py`, `healing/orchestrator.py`, `healing/monitor.py`, `healing/known_fixes.json` (auto-generated at runtime) |
| **Reads** | AP API (`/api/v1/flows`, `/api/v1/flow-runs`), `.env` (AP_API_KEY, AP_BASE_URL) |
| **Must NOT touch** | `pieces/`, `skin/`, `copilot/`, `translator/`, `docker-compose.yml`, AP internal configuration, any file outside `healing/` |

---

## Success Criteria

- [ ] Error classifier correctly categorizes at least 5 different error types
- [ ] Auth errors are immediately escalated (never auto-fixed)
- [ ] Fix agent prompt is scoped to one node only (prompt does NOT contain flow structure)
- [ ] Verification replays the exact failed input against the patched code
- [ ] A successful fix is deployed to the AP flow via UPDATE_ACTION
- [ ] A successful fix is logged to the knowledge base
- [ ] A second occurrence of the same error uses the known fix (no Claude call needed)
- [ ] After 3 failed attempts, the system escalates to human with full context
- [ ] Owner receives notification for every auto-fix
- [ ] Owner receives escalation for every failed auto-fix (with what was tried)

---

## Protocol Checkpoints (Stage 08 Injection)

### Pulse Checks — After Each File
| File | Assertions |
|------|-----------|
| `healing/__init__.py` | File exists; package is importable (`python -c "import healing"` succeeds) |
| `healing/error_capture.py` | File exists; `CapturedError` dataclass defined; fields: `error_message`, `node_code`, `failed_input`, `flow_id`; `to_dict()` and `to_json()` present |
| `healing/classifier.py` | File exists; `ErrorClassifier` class; `classify()` returns (category, strategy) tuple; `PATTERNS` has 6+ entries; `is_auto_fixable()` returns False for `auth_expired` |
| `healing/knowledge_base.py` | File exists; `HealingKnowledgeBase` class; `find_known_fix()` and `log_fix()` present; reads/writes `known_fixes.json` |
| `healing/fix_agent.py` | File exists; `SCOPED_FIX_PROMPT` constant contains "ONLY see and modify THIS node"; `FixAgent.attempt_fix()` present |
| `healing/verifier.py` | File exists; `PatchVerifier.verify()` returns dict with `passed`, `output`, `error` keys |
| `healing/orchestrator.py` | File exists; `SelfHealingOrchestrator` class; `handle_failure()` present; `MAX_ATTEMPTS = 3` |
| `healing/monitor.py` | File exists; `monitor_failed_runs()` function present; imports `CapturedError` from `healing.error_capture`; imports orchestrator |

### Seam Checks — Connection Points
**Seam 1: Error Capture -> Classifier**
- `CapturedError` fields all populated (no None for required fields)
- `ErrorClassifier.classify()` accepts `CapturedError`, returns valid category
- Rate limit error (containing "429") classifies as `"rate_limit"`
- Auth error (containing "401") classifies as `"auth_expired"`

**Seam 2: Classifier -> Fix Agent**
- When `is_auto_fixable()` returns False, `handle_failure()` does NOT call `fix_agent`
- When True, fix agent receives correct category and strategy strings

**Seam 3: Fix Agent -> Verifier**
- Fix agent returns a code string
- Verifier receives that string + original `failed_input`
- Verifier executes patched code without crashing on valid input

**Seam 4: Verifier -> Deploy**
- `passed: True` triggers `_deploy_patch()` via POST to `/api/v1/flows/{flow_id}`
- Patched code appears in AP flow's node settings after the call

**Seam 5: Knowledge Base -> Fix Agent**
- Successful fix stored via `log_fix()` with error signature
- Next occurrence of same error: `find_known_fix()` returns stored fix
- Known fix applied directly if verification passes (saves Claude call)

### Full Checkpoint (Phase 9 Gate)
**Pattern checks (git diff):**
```
Expected new directory: healing/
Expected files: __init__.py, error_capture.py, classifier.py, knowledge_base.py,
                fix_agent.py, verifier.py, orchestrator.py, monitor.py
No modification to pieces/, skin/, copilot/, or AP configuration.
```

**Functional checks:**
```bash
python -c "
from healing.error_capture import CapturedError
from healing.classifier import ErrorClassifier

e1 = CapturedError(error_message='HTTP 429 Too Many Requests', error_type='HTTPError',
    node_name='step_1', node_code='', failed_input={}, previous_output={},
    flow_id='test', run_id='test')
cat, _ = ErrorClassifier.classify(e1)
assert cat == 'rate_limit', f'Expected rate_limit, got {cat}'

e2 = CapturedError(error_message='401 Unauthorized', error_type='HTTPError',
    node_name='step_1', node_code='', failed_input={}, previous_output={},
    flow_id='test', run_id='test')
cat2, _ = ErrorClassifier.classify(e2)
assert cat2 == 'auth_expired'
assert not ErrorClassifier.is_auto_fixable(cat2)
print('All classifier tests passed')
"

python -c "
from healing.verifier import PatchVerifier
result = PatchVerifier.verify('THIS IS NOT VALID CODE', {'x': 1})
assert not result['passed'], 'Bad code should fail'
print('Verifier test passed')
"
```

**Gate condition:** Classifier categorizes 5+ error types correctly. Auth errors never auto-fixed. Verifier catches bad code. Knowledge base stores and retrieves. PASS or FAIL.

### Violation Rules
| Level | Trigger | Action |
|-------|---------|--------|
| LOW | Classifier puts an error in "unknown" that could match a pattern | Add pattern to PATTERNS list |
| MEDIUM | Fix agent returns code that changes the output shape | Add output shape validation to verifier |
| HIGH | Knowledge base returns stale fix that no longer works | Add fix expiration / re-verify before applying |
| CRITICAL | Fix agent prompt leaks flow structure or other nodes' code | Stop — prompt scoping broken; fix immediately |

### Two-Strike Rule
Max 2 full orchestration test runs per scenario. If system escalates incorrectly or fails to escalate auth errors, stop for human review — classifier patterns or orchestrator logic needs redesign.
