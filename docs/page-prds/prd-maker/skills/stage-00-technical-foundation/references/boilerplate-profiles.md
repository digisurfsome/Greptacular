# Boilerplate Profiles Reference

> 5 supported profiles with their default stacks, capabilities, and mechanism coverage.

---

## Profile: `supabase_web`

**Name:** Supabase Web Starter
**Description:** Next.js + Supabase + Vercel stack with auth, database, and hosting pre-configured.
**When to select:** Greenfield + web-only or web-first + no strong stack preference. This is the DEFAULT profile.

| Field | Value |
|-------|-------|
| Framework | Next.js 14 (App Router) |
| Database | Supabase/Postgres |
| Auth Provider | Supabase Auth (email/password + OAuth) |
| Hosting | Vercel |
| CSS/Styling | Tailwind CSS |
| ORM/Query | Supabase client SDK |
| File Storage | Supabase Storage |

**Mechanism Coverage (what the boilerplate handles natively):**

| Category | Status | Notes |
|----------|--------|-------|
| A - Data Input | needs_user_input | Forms depend on app idea |
| B - Data Storage | covered_by_boilerplate | Supabase/Postgres + Storage |
| C - Data Processing | needs_user_input | App-specific logic |
| D - Data Output | needs_user_input | App-specific views |
| E - Authentication | covered_by_boilerplate | Supabase Auth |
| F - Authorization | covered_by_boilerplate | Row Level Security (RLS) |
| G - Communication | needs_user_input | Not included in base |
| H - Integration | needs_user_input | App-specific |
| I - Workflow | needs_user_input | App-specific |
| J - Search & Discovery | needs_user_input | Postgres full-text search available |
| K - Collaboration | needs_user_input | App-specific |
| L - Monetization | needs_user_input | Not included in base |
| M - Admin/Ops | needs_user_input | Not included in base |
| N - Infrastructure | covered_by_boilerplate | Vercel + Supabase managed hosting |

**Command Allowlist:** `npm`, `npx`, `git`, `node`, `curl`, `next`, `supabase`

---

## Profile: `flutter_mobile`

**Name:** Flutter Mobile + Supabase
**Description:** Flutter for mobile UI + Supabase backend for auth, database, and storage.
**When to select:** Mobile-only or mobile-first projects.

| Field | Value |
|-------|-------|
| Framework | Flutter (latest stable) |
| Database | Supabase/Postgres |
| Auth Provider | Supabase Auth |
| Hosting | App stores (iOS/Android) + Supabase backend |
| CSS/Styling | Flutter Material/Cupertino widgets |
| ORM/Query | Supabase Dart SDK |
| File Storage | Supabase Storage |

**Mechanism Coverage:**

| Category | Status | Notes |
|----------|--------|-------|
| A - Data Input | needs_user_input | Mobile-specific input patterns |
| B - Data Storage | covered_by_boilerplate | Supabase/Postgres |
| C - Data Processing | needs_user_input | App-specific |
| D - Data Output | needs_user_input | App-specific |
| E - Authentication | covered_by_boilerplate | Supabase Auth (mobile SDK) |
| F - Authorization | covered_by_boilerplate | RLS |
| G - Communication | needs_user_input | Push notifications need setup |
| H - Integration | needs_user_input | App-specific |
| I - Workflow | needs_user_input | App-specific |
| J - Search & Discovery | needs_user_input | App-specific |
| K - Collaboration | needs_user_input | App-specific |
| L - Monetization | needs_user_input | In-app purchases need setup |
| M - Admin/Ops | needs_user_input | Not included in base |
| N - Infrastructure | covered_by_boilerplate | Supabase managed backend |

**Command Allowlist:** `flutter`, `dart`, `git`, `curl`, `supabase`, `pod` (iOS)

---

## Profile: `dual`

**Name:** Dual Web + Mobile + Supabase
**Description:** Next.js web app + Flutter mobile app sharing a Supabase backend.
**When to select:** User explicitly wants both web and mobile clients.

| Field | Value |
|-------|-------|
| Framework | Next.js 14 (web) + Flutter (mobile) |
| Database | Supabase/Postgres |
| Auth Provider | Supabase Auth |
| Hosting | Vercel (web) + App stores (mobile) + Supabase (backend) |
| CSS/Styling | Tailwind CSS (web) + Flutter widgets (mobile) |
| ORM/Query | Supabase client SDK (JS + Dart) |
| File Storage | Supabase Storage |

**Mechanism Coverage:** Same as `supabase_web` (B, E, F, N covered). Mobile-specific concerns (push notifications, app store requirements) are flagged as additional needs in assumptions.

**Command Allowlist:** `npm`, `npx`, `git`, `node`, `curl`, `next`, `supabase`, `flutter`, `dart`, `pod`

---

## Profile: `no_boilerplate`

**Name:** No Boilerplate (Custom Stack)
**Description:** User has a specific stack not covered by supported boilerplates. Checklist rules still apply but no boilerplate file pointers exist.
**When to select:** User requests a non-standard stack (e.g., Django + PostgreSQL, Rails + MySQL, SvelteKit + Firebase).

| Field | Value |
|-------|-------|
| Framework | User-specified |
| Database | User-specified |
| Auth Provider | User-specified |
| Hosting | User-specified |
| CSS/Styling | User-specified |
| ORM/Query | User-specified |
| File Storage | User-specified |

**Mechanism Coverage:** All categories are `needs_user_input`. No boilerplate assumptions.

**Command Allowlist:** `git`, `curl` + user-specified tools

---

## Profile: `raw_checklist`

**Name:** Raw Checklist Only
**Description:** Existing app or bring-your-own architecture. The structural checklist applies but is resolved in CHECK mode against the existing codebase rather than a boilerplate.
**When to select:** `app_type: "existing"` or user is adding features to an existing project.

| Field | Value |
|-------|-------|
| Framework | Determined by existing codebase |
| Database | Determined by existing codebase |
| Auth Provider | Determined by existing codebase |
| Hosting | Determined by existing codebase |

**Mechanism Coverage:** All categories are `needs_user_input` until codebase analysis is supported (future feature).

**Command Allowlist:** Determined by existing project configuration

**Note:** Existing app analysis (codebase scanning, dependency detection) is a future feature. For now, the user must manually specify their stack, and it is recorded as assumptions.
