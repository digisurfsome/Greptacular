# Phase 1B: Industry Standards Supplement Checklist

> **Type:** Self-contained handoff prompt for a fresh Claude Code agent
> **Estimated effort:** Single session, research + judgment
> **Output:** `docs/page-prds/prd-maker/industry-standards-checklist.md`

---

## Your Mission

Martin's checklist (192 rules) is excellent for structural code quality but has significant gaps. It was written by one developer for one stack and focuses heavily on React component patterns, Firebase configuration, and UI anti-patterns. It says nothing about internationalization, environment parity, logging strategy, legal compliance, deep accessibility, API versioning, or error recovery patterns.

Your job is to create a SUPPLEMENTARY checklist that covers the gaps the industry frameworks identify. This is NOT a replacement for Martin's checklist -- it covers what Martin DOESN'T cover. Together, Martin's agnostic checklist + your industry standards checklist = complete structural coverage.

---

## Files to Read (In This Order)

1. **`docs/page-prds/prd-maker/research-reference.md`** — Read the "30-Category Master Checklist" section (categories 1-30 synthesized from IEEE 830, FURPS+, Volere, arc42, C4 Model, 12-Factor App). This tells you what a "complete" spec covers. Compare it against Martin's 18 categories to find the gaps.

2. **`docs/page-prds/prd-maker/extracted-skills/arc42/arc42-template-EN-full.md`** — The full arc42 architecture documentation template. Read for: architecture constraints, cross-cutting concepts, quality requirements, risks and technical debt, deployment view. These are all areas Martin's checklist does not touch.

3. **`docs/page-prds/prd-maker/extracted-skills/frameworks/12-factor-app.md`** — The 12-Factor App methodology. Read for: config externalization, dependency management, dev/prod parity, logging as event streams, disposability, port binding, concurrency. Martin covers almost none of this.

4. **`docs/page-prds/prd-maker/trial-idea-1-structural-checklist.md`** — Skim Martin's 18 categories to confirm what IS already covered. Your checklist must NOT duplicate Martin's rules. If Martin already covers a topic (e.g., "no inline styles"), do NOT add a rule about it.

5. **`docs/page-prds/prd-maker/build-game-plan.md`** — Read section "1C. Create Industry Standards Supplement" for the specific gaps identified.

---

## The 10 Gap Areas to Cover

Your checklist must address these specific gaps. For each area, write concrete, implementable rules (not vague guidance).

### 1. Internationalization (i18n)

Rules covering:
- String externalization (no hardcoded user-facing strings in code)
- Locale-aware formatting (dates, numbers, currency)
- RTL layout support readiness
- Translation file structure and key naming
- Pluralization handling
- Language detection and fallback chain

### 2. Config Externalization

Rules covering:
- All environment-specific values in environment variables (no hardcoded URLs, API keys, feature flags)
- Configuration hierarchy (defaults < env vars < runtime overrides)
- Secrets management (never in source control, never in client bundles)
- Feature flags as config, not code branches
- Build-time vs runtime configuration separation

### 3. Environment Parity (Dev/Staging/Prod)

Rules covering:
- Development environment mirrors production as closely as possible
- Same database technology in dev and prod (no SQLite-in-dev, Postgres-in-prod)
- Same authentication flow in dev and prod
- Environment-specific configuration via env vars only, not code branches
- Seed data strategy for development
- Production data never copied to development

### 4. Logging Strategy

Rules covering:
- Structured logging (JSON format, not string concatenation)
- Log levels (ERROR, WARN, INFO, DEBUG) with clear usage guidelines
- No `console.log` in production (Martin mentions this but does not provide an alternative)
- Request ID / correlation ID for tracing across services
- Sensitive data NEVER logged (passwords, tokens, PII)
- Log aggregation readiness (stdout/stderr, not file-based)
- Client-side error reporting (uncaught exceptions, API failures)

### 5. Dependency Management

Rules covering:
- Lockfile committed to source control (package-lock.json, yarn.lock, pnpm-lock.yaml)
- Dependencies explicitly declared (no reliance on globally installed packages)
- No floating version ranges in production dependencies
- Regular dependency audit (security vulnerabilities)
- Peer dependency conflicts resolved before merge
- Maximum dependency age policy (flag deps not updated in 12+ months)

### 6. Legal/Compliance

Rules covering:
- Privacy policy page (required for any app collecting user data)
- Terms of service page
- Cookie consent (if applicable)
- GDPR considerations: data export, data deletion, consent tracking
- CCPA considerations for US users
- Third-party data sharing disclosure
- Open-source license compliance for dependencies
- Age verification requirements (COPPA if applicable)

### 7. Deep Accessibility (WCAG AA)

Rules covering:
- Color contrast ratios: 4.5:1 for normal text, 3:1 for large text (WCAG AA)
- Semantic HTML (proper heading hierarchy, landmarks, lists)
- Skip navigation link
- `prefers-reduced-motion` media query support (disable animations when set)
- `prefers-color-scheme` media query support
- Focus management for modals, drawers, and dynamic content
- Screen reader announcements for dynamic updates (ARIA live regions)
- Keyboard-only navigation for ALL interactive elements
- Touch target minimum size (44x44px)
- Alt text for all non-decorative images; decorative images marked with `alt=""`
- Form labels associated with inputs (not just placeholder text)
- Error messages associated with form fields via `aria-describedby`

Note: Martin's checklist has basic accessibility rules (keyboard navigation, focus management). Your rules should go DEEPER into WCAG AA compliance. Do not duplicate Martin's existing rules.

### 8. API Versioning

Rules covering:
- API version in URL path (`/api/v1/`) or header (`Accept: application/vnd.app.v1+json`)
- Deprecation policy (minimum notice period before removing endpoints)
- Backward compatibility requirements for minor versions
- Breaking change detection and documentation
- API changelog or migration guide for version transitions

### 9. Architecture Decision Records (ADRs)

Rules covering:
- ADR template: Status, Context, Decision, Consequences
- When to write an ADR (any decision that affects multiple files or introduces a new dependency)
- ADR numbering and storage location
- Superseded ADRs linked to replacement
- ADRs reviewed during onboarding

### 10. Error Recovery / Retry Strategy

Rules covering:
- Transient failure detection (network timeouts, 503s, rate limits)
- Exponential backoff with jitter for retries
- Maximum retry count (prevent infinite loops)
- Circuit breaker pattern for external service calls
- Graceful degradation (app still usable when non-critical services are down)
- Retry state visibility to the user (not silent retries that look like hangs)
- Idempotency requirements for retried operations

---

## Output File Format

Create: **`docs/page-prds/prd-maker/industry-standards-checklist.md`**

### Header

```markdown
# Industry Standards Supplement Checklist

> Covers structural rules that Martin's checklist does not address.
> This checklist + Martin's agnostic checklist = complete structural coverage for any app spec.
>
> Sources: IEEE 830, FURPS+, Volere, arc42, C4 Model, 12-Factor App, WCAG 2.1 AA
```

### Table Format Per Category

For each of the 10 gap areas, create a category section with this table format:

| # | Rule | Description | Technical Spec | Boilerplate Match | Severity |
|---|------|-------------|----------------|-------------------|----------|

- **#** — Sequential numbering starting from 200 (to avoid collision with Martin's 1-192)
- **Rule** — Short rule name (max 8 words)
- **Description** — 1-2 sentence explanation of what the rule requires
- **Technical Spec** — Precise, implementable specification. Must be specific enough that an agent can verify compliance. No vague language.
- **Boilerplate Match** — `_[to be filled]_` (filled later)
- **Severity** — CRITICAL / STANDARD / POLISH

### Category Structure

Each of the 10 categories should have:
- A `### Category Name` heading
- A 1-2 sentence description of what the category covers and why it matters
- A note about which industry framework(s) this category comes from (arc42, 12-Factor, WCAG, etc.)
- The rules table

---

## Rules for Writing Good Rules

1. **Be specific.** "Handle errors properly" is not a rule. "All API calls must have try/catch with user-visible error messages and automatic retry for transient failures (HTTP 503, network timeout)" is a rule.

2. **Be implementable.** An agent reading this rule must know EXACTLY what to build. If the rule requires judgment, specify the criteria for the judgment.

3. **Be verifiable.** It must be possible to check whether the rule is followed by reading the code. "Code should be clean" is not verifiable. "No function longer than 50 lines" is verifiable.

4. **Don't duplicate Martin.** If Martin already has a rule about something (even if his rule is less thorough), do NOT add your own version. His checklist is the authority for what it covers.

5. **Technology agnostic.** All rules must work for any stack. Reference capabilities, not products. "Use structured logging" not "Use Winston."

---

## Quality Checks Before You Finish

1. **No overlap with Martin:** For each rule you wrote, verify that Martin's 18 categories don't already have a similar rule. If they do, delete yours.
2. **Severity distribution:** CRITICAL rules should be things that cause security vulnerabilities, data loss, or legal liability. Not everything is critical. Aim for ~20% CRITICAL, ~50% STANDARD, ~30% POLISH.
3. **Specificity check:** Read every "Technical Spec" cell. If any cell uses words like "appropriate," "proper," "best practice," "as needed," or "consider" -- rewrite it with specific criteria.
4. **Count:** Aim for 60-80 total rules across all 10 categories. Not too few (gaps remain) or too many (overwhelming).
5. **Numbering:** Rules start at 200 and go up sequentially. No gaps, no duplicates.

---

## Success Criteria

- [ ] All 10 gap areas have rules
- [ ] 60-80 total rules
- [ ] Numbering starts at 200
- [ ] Every rule has a Severity tag
- [ ] No overlap with Martin's existing 192 rules
- [ ] All rules are technology-agnostic
- [ ] All Technical Spec cells are specific and implementable (no vague language)
- [ ] Header explains the relationship to Martin's checklist
- [ ] Category descriptions cite the source framework (arc42, 12-Factor, WCAG, etc.)
- [ ] File saved to `docs/page-prds/prd-maker/industry-standards-checklist.md`
