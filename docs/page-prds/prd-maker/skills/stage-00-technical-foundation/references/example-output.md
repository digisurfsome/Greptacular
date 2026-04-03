# Example Output Reference

> Two complete input→output scenarios for Stage 0.

---

## Scenario 1: Full-Input User

### Input

User answers all 5 platform questions:

> 1. Greenfield app — starting from scratch.
> 2. Web app only.
> 3. I want Next.js with Supabase for the database and auth.
> 4. New repo, using the Supabase starter.
> 5. Deploy to Vercel.

### Output: `context_packet.stage_0`

```json
{
  "platform_profile": {
    "boilerplate_id": "supabase_web",
    "boilerplate_name": "Supabase Web Starter",
    "description": "Next.js + Supabase + Vercel stack with auth, database, and hosting pre-configured"
  },
  "tech_stack": {
    "framework": "Next.js 14",
    "database": "Supabase/Postgres",
    "auth_provider": "Supabase Auth",
    "hosting": "Vercel",
    "additional": {}
  },
  "checklist_rule_ids": ["stack-1", "stack-2", "file-1", "file-2", "comp-1", "...all applicable rule IDs"],
  "command_allowlist": ["npm", "npx", "git", "node", "curl", "next", "supabase"],
  "resolved_rules": [
    { "rule_id": "stack-1", "resolution": "HANDLED", "priority": "critical", "enforcement": "hard", "evidence": "boilerplate: package.json defines Next.js 14 + Supabase" },
    { "rule_id": "auth-1", "resolution": "HANDLED", "priority": "critical", "enforcement": "hard", "evidence": "boilerplate: src/lib/supabase.ts provides auth client" },
    { "rule_id": "comp-1", "resolution": "MATCH", "priority": "important", "enforcement": "hard", "evidence": null },
    { "rule_id": "ban-1", "resolution": "MATCH", "priority": "critical", "enforcement": "hard", "evidence": null }
  ],
  "structural_coverage": {
    "categories": [
      { "name": "Stack Definition", "status": "covered_by_preamble" },
      { "name": "File Structure", "status": "covered_by_preamble" },
      { "name": "Component Architecture", "status": "covered_by_preamble" },
      { "name": "State Management", "status": "covered_by_preamble" },
      { "name": "Routing", "status": "covered_by_preamble" },
      { "name": "Styling", "status": "covered_by_preamble" },
      { "name": "Data Fetching", "status": "covered_by_preamble" },
      { "name": "Auth & Security", "status": "covered_by_preamble" },
      { "name": "Forms & Validation", "status": "missing" },
      { "name": "Error Handling", "status": "missing" },
      { "name": "Testing", "status": "missing" },
      { "name": "Build & Bundle", "status": "covered_by_preamble" },
      { "name": "Type Safety", "status": "covered_by_preamble" },
      { "name": "Code Quality", "status": "missing" },
      { "name": "Git & Version Control", "status": "missing" },
      { "name": "Environment Config", "status": "covered_by_preamble" },
      { "name": "Performance", "status": "missing" },
      { "name": "SEO", "status": "missing" },
      { "name": "Analytics & Monitoring", "status": "missing" },
      { "name": "Deployment", "status": "covered_by_preamble" },
      { "name": "Documentation", "status": "missing" },
      { "name": "Banned Patterns", "status": "covered_by_preamble" },
      { "name": "Internationalization", "status": "missing" },
      { "name": "Config Externalization", "status": "covered_by_preamble" },
      { "name": "Environment Parity", "status": "missing" },
      { "name": "Logging Strategy", "status": "missing" },
      { "name": "Dependency Management", "status": "missing" },
      { "name": "Legal/Compliance", "status": "missing" },
      { "name": "Deep Accessibility", "status": "missing" },
      { "name": "API Versioning", "status": "missing" }
    ]
  },
  "mechanism_target": {
    "categories": [
      { "id": "A", "name": "Data Input", "status": "needs_user_input" },
      { "id": "B", "name": "Data Storage", "status": "covered_by_boilerplate" },
      { "id": "C", "name": "Data Processing", "status": "needs_user_input" },
      { "id": "D", "name": "Data Output", "status": "needs_user_input" },
      { "id": "E", "name": "Authentication", "status": "covered_by_boilerplate" },
      { "id": "F", "name": "Authorization", "status": "covered_by_boilerplate" },
      { "id": "G", "name": "Communication", "status": "needs_user_input" },
      { "id": "H", "name": "Integration", "status": "needs_user_input" },
      { "id": "I", "name": "Workflow", "status": "needs_user_input" },
      { "id": "J", "name": "Search & Discovery", "status": "needs_user_input" },
      { "id": "K", "name": "Collaboration", "status": "needs_user_input" },
      { "id": "L", "name": "Monetization", "status": "needs_user_input" },
      { "id": "M", "name": "Admin/Ops", "status": "needs_user_input" },
      { "id": "N", "name": "Infrastructure", "status": "covered_by_boilerplate" }
    ]
  },
  "assumptions": [
    { "field": "tech_stack.additional.css", "value": "Tailwind CSS", "confidence": "inferred", "reversal_cost": "low", "source": "Included in supabase_web boilerplate" }
  ],
  "question_budget": {
    "mode": "full_detail",
    "max_rounds": 2,
    "blocking_questions_only": true
  },
  "stage_contract": {
    "stop_go": "go",
    "unresolved_blockers": []
  },
  "nfr_budgets": { "latency": null, "reliability": null, "cost": null, "scale": null, "security": null, "maintainability": null },
  "data_governance": { "pii_handling": null, "retention": null, "auditability": null, "regional_constraints": null },
  "observability_requirements": { "logs": null, "metrics": null, "traces": null, "alert_thresholds": null },
  "out_of_scope": []
}
```

### Metadata Updates

```json
{
  "current_stage": 0,
  "updated_at": "2026-04-03T12:05:00Z",
  "confidence_scores": {
    "0": {
      "score": 96,
      "dimensions": {
        "completeness": 20,
        "accuracy": 19,
        "consistency": 20,
        "specificity": 18,
        "handoff_readiness": 19
      },
      "gate_result": "pass"
    }
  },
  "stage_timestamps": {
    "0": "2026-04-03T12:05:00Z"
  }
}
```

---

## Scenario 2: Zero-Input User

### Input

User says: "Just help me build something. I don't know anything about tech stacks."

No platform questions answered.

### Output: `context_packet.stage_0`

```json
{
  "platform_profile": {
    "boilerplate_id": "supabase_web",
    "boilerplate_name": "Supabase Web Starter",
    "description": "Next.js + Supabase + Vercel stack with auth, database, and hosting pre-configured"
  },
  "tech_stack": {
    "framework": "Next.js 14",
    "database": "Supabase/Postgres",
    "auth_provider": "Supabase Auth",
    "hosting": "Vercel",
    "additional": { "css": "Tailwind CSS" }
  },
  "checklist_rule_ids": ["stack-1", "stack-2", "file-1", "...all applicable rule IDs"],
  "command_allowlist": ["npm", "npx", "git", "node", "curl", "next", "supabase"],
  "resolved_rules": [
    { "rule_id": "stack-1", "resolution": "HANDLED", "priority": "critical", "enforcement": "hard", "evidence": "boilerplate: package.json defines stack" },
    { "rule_id": "comp-1", "resolution": "MATCH", "priority": "important", "enforcement": "hard", "evidence": null }
  ],
  "structural_coverage": {
    "categories": [
      { "name": "Stack Definition", "status": "covered_by_preamble" },
      { "name": "File Structure", "status": "covered_by_preamble" },
      { "name": "Auth & Security", "status": "covered_by_preamble" },
      { "name": "Forms & Validation", "status": "missing" },
      { "name": "Testing", "status": "missing" }
    ]
  },
  "mechanism_target": {
    "categories": [
      { "id": "A", "name": "Data Input", "status": "needs_user_input" },
      { "id": "B", "name": "Data Storage", "status": "covered_by_boilerplate" },
      { "id": "C", "name": "Data Processing", "status": "needs_user_input" },
      { "id": "D", "name": "Data Output", "status": "needs_user_input" },
      { "id": "E", "name": "Authentication", "status": "covered_by_boilerplate" },
      { "id": "F", "name": "Authorization", "status": "covered_by_boilerplate" },
      { "id": "G", "name": "Communication", "status": "needs_user_input" },
      { "id": "H", "name": "Integration", "status": "needs_user_input" },
      { "id": "I", "name": "Workflow", "status": "needs_user_input" },
      { "id": "J", "name": "Search & Discovery", "status": "needs_user_input" },
      { "id": "K", "name": "Collaboration", "status": "needs_user_input" },
      { "id": "L", "name": "Monetization", "status": "needs_user_input" },
      { "id": "M", "name": "Admin/Ops", "status": "needs_user_input" },
      { "id": "N", "name": "Infrastructure", "status": "covered_by_boilerplate" }
    ]
  },
  "assumptions": [
    { "field": "metadata.app_type", "value": "greenfield", "confidence": "assumed", "reversal_cost": "high", "source": "No existing codebase indicated" },
    { "field": "platform_profile.boilerplate_id", "value": "supabase_web", "confidence": "assumed", "reversal_cost": "medium", "source": "Lowest-risk default for web apps" },
    { "field": "tech_stack.framework", "value": "Next.js 14", "confidence": "assumed", "reversal_cost": "medium", "source": "Default web framework for supabase_web profile" },
    { "field": "tech_stack.database", "value": "Supabase/Postgres", "confidence": "assumed", "reversal_cost": "high", "source": "Core data layer for supabase_web profile" },
    { "field": "tech_stack.auth_provider", "value": "Supabase Auth", "confidence": "assumed", "reversal_cost": "medium", "source": "Native auth for supabase_web profile" },
    { "field": "tech_stack.hosting", "value": "Vercel", "confidence": "assumed", "reversal_cost": "low", "source": "Default hosting for Next.js apps" },
    { "field": "platform_target", "value": "web", "confidence": "assumed", "reversal_cost": "medium", "source": "Web is most common starting platform" },
    { "field": "repo_source", "value": "new_repo", "confidence": "assumed", "reversal_cost": "low", "source": "Greenfield implies new repo" },
    { "field": "tech_stack.additional.css", "value": "Tailwind CSS", "confidence": "assumed", "reversal_cost": "low", "source": "Included in supabase_web boilerplate" },
    { "field": "payment_processor", "value": "Stripe (deferred)", "confidence": "assumed", "reversal_cost": "low", "source": "Only activated if monetization signal in later stages" },
    { "field": "tooling", "value": "Claude Code", "confidence": "assumed", "reversal_cost": "low", "source": "Running within this pipeline" },
    { "field": "question_budget.mode", "value": "zero_input", "confidence": "assumed", "reversal_cost": "low", "source": "No user input provided" }
  ],
  "question_budget": {
    "mode": "zero_input",
    "max_rounds": 0,
    "blocking_questions_only": true
  },
  "stage_contract": {
    "stop_go": "go",
    "unresolved_blockers": []
  },
  "nfr_budgets": { "latency": null, "reliability": null, "cost": null, "scale": null, "security": null, "maintainability": null },
  "data_governance": { "pii_handling": null, "retention": null, "auditability": null, "regional_constraints": null },
  "observability_requirements": { "logs": null, "metrics": null, "traces": null, "alert_thresholds": null },
  "out_of_scope": []
}
```

### Metadata Updates

```json
{
  "current_stage": 0,
  "updated_at": "2026-04-03T12:02:00Z",
  "confidence_scores": {
    "0": {
      "score": 92,
      "dimensions": {
        "completeness": 19,
        "accuracy": 18,
        "consistency": 20,
        "specificity": 17,
        "handoff_readiness": 18
      },
      "gate_result": "pass"
    }
  },
  "stage_timestamps": {
    "0": "2026-04-03T12:02:00Z"
  }
}
```

### Why Score is 92 (not higher)

- **Specificity: 17** — All tech is specified but since everything is assumed, capability notes are minimal.
- **Accuracy: 18** — Defaults are valid and compatible, but without user confirmation, there's inherent uncertainty.
- **Completeness: 19** — All fields populated, but structural_coverage has many "missing" categories (expected at Stage 0).
- The score is still ≥ 90 because the defaults form a coherent, valid stack and the assumption log is complete.
