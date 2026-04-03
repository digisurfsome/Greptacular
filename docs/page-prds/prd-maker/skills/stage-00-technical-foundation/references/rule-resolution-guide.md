# Rule Resolution Guide

> How to resolve each Martin checklist category and industry standards rule against each boilerplate profile.

---

## Resolution Decision Tree

For each rule in the agnostic checklist and industry standards supplement:

```
1. Does the boilerplate already implement this rule?
   → YES: resolution = "HANDLED", evidence = file/config path
   → NO: continue

2. Does the rule's principle apply to this stack?
   → NO: resolution = "N/A" (e.g., mobile-specific rule for web-only app)
   → YES: continue

3. Does the rule's IMPLEMENTATION need to change for this stack?
   → NO: resolution = "MATCH" (carry as-is)
   → YES: continue

4. Can the boilerplate's native tooling enhance the rule?
   → YES: resolution = "ENHANCE" (keep rule + add boilerplate pointers)
   → NO: resolution = "REPLACE" (swap implementation, keep principle)
```

---

## Priority Assignment

| Priority | Criteria |
|----------|----------|
| `critical` | Security, auth, data integrity, build hygiene. Failure = broken app or security vulnerability. |
| `important` | Structure, naming, testing, accessibility, config. Failure = technical debt or poor quality. |
| `nice` | Polish, documentation, optimization. Failure = suboptimal but functional. |

---

## Enforcement Assignment

| Enforcement | Criteria |
|-------------|----------|
| `hard` | Build hygiene, structure, naming discipline, anti-pattern bans, security, auth boundaries, state/data handling consistency, deterministic component and testing standards. Non-negotiable. |
| `soft` | Feature count limits ("only 5 features" → recommendation), provider-specific assumptions, optimization suggestions. Advisory. |

---

## Per-Profile Resolution Patterns

### `supabase_web` Profile

| Martin Category | Typical Resolution | Rationale |
|----------------|-------------------|-----------|
| 1. Stack Definition | HANDLED | Supabase Web Starter defines the full stack |
| 2. File Structure | ENHANCE | Base structure exists; add Supabase-specific directories |
| 3. Component Architecture | MATCH | Component rules are framework-agnostic |
| 4. State Management | MATCH | State rules apply to any React app |
| 5. Routing | ENHANCE | Next.js App Router has specific patterns |
| 6. Styling | ENHANCE | Tailwind CSS is pre-configured |
| 7. Data Fetching | REPLACE | Supabase SDK replaces generic fetch patterns |
| 8. Auth & Security | HANDLED | Supabase Auth + RLS pre-configured |
| 9. Forms & Validation | MATCH | Form rules are stack-agnostic |
| 10. Error Handling | MATCH | Error patterns are universal |
| 11-22. (remaining) | MATCH or ENHANCE | Most structural rules apply as-is or with minor enhancements |
| Banned Patterns (43) | MATCH | All banned patterns are universal anti-patterns |

| Industry Standards | Typical Resolution | Rationale |
|-------------------|-------------------|-----------|
| 1. i18n | MATCH | Rules are stack-agnostic |
| 2. Config Externalization | ENHANCE | Vercel env vars + Next.js conventions |
| 3. Environment Parity | ENHANCE | Supabase local dev + Vercel preview |
| 4. Logging | MATCH | Rules are stack-agnostic |
| 5. Dependency Management | ENHANCE | npm-specific tooling |
| 6. Legal/Compliance | MATCH | Rules are stack-agnostic |
| 7. Accessibility (WCAG) | MATCH | Rules are stack-agnostic |
| 8. API Versioning | MATCH | Rules are stack-agnostic |
| 9. ADRs | MATCH | Rules are stack-agnostic |
| 10. Error Recovery/Retry | MATCH | Rules are stack-agnostic |

### `flutter_mobile` Profile

| Martin Category | Typical Resolution | Rationale |
|----------------|-------------------|-----------|
| 1. Stack Definition | HANDLED | Flutter + Supabase defines the stack |
| 2. File Structure | REPLACE | Flutter has different directory conventions |
| 3. Component Architecture | REPLACE | Flutter uses widgets, not JSX components |
| 4. State Management | REPLACE | Flutter state (Provider/Riverpod/Bloc) differs from React |
| 5. Routing | REPLACE | Flutter Navigator/GoRouter differs from web routing |
| 6. Styling | REPLACE | Flutter themes, not CSS |
| 7. Data Fetching | REPLACE | Supabase Dart SDK |
| 8. Auth & Security | HANDLED | Supabase Auth mobile SDK |
| 9-22. (remaining) | MATCH, REPLACE, or N/A | Many web-specific rules need mobile adaptation |
| Web-specific rules | N/A | CSS, HTML semantic, browser-specific rules don't apply |

### `no_boilerplate` and `raw_checklist` Profiles

All rules default to `MATCH` (carry as-is) since no boilerplate handles anything. The user's stated stack is used to determine which rules are `N/A` (e.g., mobile rules for a web-only project). No rules are `HANDLED` or `ENHANCE` because there are no boilerplate file pointers to reference.

---

## Evidence Examples

| Resolution | Evidence Format |
|-----------|----------------|
| HANDLED | `"boilerplate: src/lib/supabase.ts provides auth client"` |
| ENHANCE | `"extends: boilerplate uses Tailwind; add theme token file at src/styles/tokens.ts"` |
| REPLACE | `"replaces: Firebase Firestore patterns with Supabase Postgres + RLS"` |
| MATCH | `null` (no evidence needed — rule carries unchanged) |
| N/A | `null` (rule does not apply) |
