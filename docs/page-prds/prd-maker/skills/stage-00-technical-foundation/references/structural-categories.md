# Structural Categories Reference (30 Total)

> 22 Martin checklist categories + 10 industry standards gap areas − 2 overlaps = 30 unique categories.
> Each category must appear in the `structural_coverage.categories` array.

---

## Martin Checklist Categories (22)

| # | Category | Description |
|---|----------|-------------|
| 1 | Stack Definition | Framework, runtime, language, package manager choices |
| 2 | File Structure | Directory layout, naming conventions, file organization |
| 3 | Component Architecture | Component patterns, composition, prop contracts |
| 4 | State Management | Global state, local state, derived state patterns |
| 5 | Routing | Page routing, navigation, URL structure |
| 6 | Styling | CSS methodology, design tokens, responsive approach |
| 7 | Data Fetching | API calls, caching, loading/error states |
| 8 | Auth & Security | Authentication flow, session management, CSRF, XSS |
| 9 | Forms & Validation | Form handling, input validation, error display |
| 10 | Error Handling | Try/catch patterns, error boundaries, user-facing errors |
| 11 | Testing | Unit, integration, E2E test strategy and tooling |
| 12 | Build & Bundle | Build pipeline, bundling, code splitting |
| 13 | Type Safety | TypeScript/typing strategy, strict mode |
| 14 | Code Quality | Linting, formatting, code review standards |
| 15 | Git & Version Control | Branch strategy, commit conventions, PR process |
| 16 | Environment Config | Dev/staging/prod configuration |
| 17 | Performance | Core Web Vitals, lazy loading, optimization |
| 18 | SEO | Meta tags, sitemap, structured data (web only) |
| 19 | Analytics & Monitoring | Usage tracking, error monitoring |
| 20 | Deployment | CI/CD pipeline, deploy process |
| 21 | Documentation | README, inline docs, API docs |
| 22 | Banned Patterns | 43 anti-patterns that must never appear |

---

## Industry Standards Gap Areas (10)

These cover structural areas Martin's checklist does not address. Rule numbers start at 200.

| # | Category | Rules | Description |
|---|----------|-------|-------------|
| 23 | Internationalization (i18n) | 200-207 | String externalization, locale formatting, RTL readiness |
| 24 | Config Externalization | 208-214 | Secrets management, env vars, feature flags |
| 25 | Environment Parity | 215-220 | Dev/staging/prod consistency, seed data |
| 26 | Logging Strategy | 221-228 | Structured logs, log levels, correlation IDs |
| 27 | Dependency Management | 229-235 | Lockfiles, version pinning, security audits |
| 28 | Legal/Compliance | 236-243 | Privacy policy, terms, cookie consent, GDPR |
| 29 | Deep Accessibility (WCAG AA) | 244-253 | Contrast, semantic HTML, ARIA, reduced motion |
| 30 | API Versioning | 254-258 | Version identifiers, deprecation, backward compat |

---

## Overlap Resolution

Two categories from the industry standards overlap with Martin's checklist:

| Industry Category | Martin Overlap | Resolution |
|-------------------|---------------|------------|
| Architecture Decision Records (ADRs) | #21 Documentation | Merged into #21. ADR rules (259-263) are sub-rules of Documentation. |
| Error Recovery / Retry Strategy | #10 Error Handling | Merged into #10. Retry rules (264-270) are sub-rules of Error Handling. |

This produces 22 + 10 − 2 = **30 unique categories**.

---

## Default Coverage by Profile

### `supabase_web` Defaults

| Category | Default Status |
|----------|---------------|
| 1. Stack Definition | covered_by_preamble |
| 2. File Structure | covered_by_preamble |
| 3. Component Architecture | covered_by_preamble |
| 4-7 | covered_by_preamble |
| 8. Auth & Security | covered_by_preamble |
| 9-22 | missing (app-specific) |
| 23-30 (industry) | missing (not in boilerplate) |

Note: "covered_by_preamble" means the boilerplate + resolved rules address the category. "missing" means it must be resolved by the user's app idea in downstream stages. Categories can move to "provided_by_user" if the user explicitly addresses them in intake.
