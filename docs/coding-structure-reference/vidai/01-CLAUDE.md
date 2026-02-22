# VidAi - CLAUDE.md (Martin's Master Project Reference)

> **Source**: `/CLAUDE.md` in the VidAi repository (https://github.com/digisurfsome/VidAi)
> **Role**: Primary agent guidance document - comprehensive architecture and operational reference
> **Size**: ~23KB

---

## Complete Document

```markdown
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

- `npm run dev` - Start development server on port 8080
- `npm run build` - Build for production
- `npm run build:dev` - Build for development mode
- `npm run lint` - Run ESLint
- `npm run preview` - Preview production build

## Environment Setup

### Required Environment Variables

This application requires environment variables for secure credential management. Follow these steps:

1. **Copy the example file**: `cp .env.example .env.local`
2. **Configure your values** in `.env.local`:

# Supabase Configuration
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key-here

# Application Configuration
VITE_APP_URL=http://localhost:8080

# MCP Configuration (for .mcp.json)
SUPABASE_ACCESS_TOKEN=sbp_your-supabase-access-token

### MCP Configuration

The `.mcp.json` file requires manual token configuration since it doesn't support environment variable substitution:

1. Copy `.mcp.json.example` to `.mcp.json`
2. Replace `YOUR_SUPABASE_ACCESS_TOKEN` with your actual Supabase access token
3. Replace `YOUR_SUPABASE_PROJECT_REF` with your project reference

### Security Notes

- `.env.local` is gitignored - never commit environment files
- `VITE_` prefixed variables are client-side accessible
- Non-`VITE_` prefixed variables are server-side only
- All credentials are now externalized from source code
- `SUPABASE_SERVICE_ROLE_KEY` must be kept secure (server-side only)
- **Critical**: `SUPABASE_SERVICE_ROLE_KEY` is REQUIRED for admin functions to work properly

## Architecture Overview

This is a React + TypeScript + Vite application with Supabase authentication and a multi-layout architecture:

### Authentication System
- **Supabase Auth** configured with implicit flow for compatibility
- **Important**: Uses `flowType: 'implicit'` instead of PKCE to ensure password reset links work correctly
- Password reset links redirect directly to `/auth/update-password`
- Auth state changes handled via `onAuthStateChange` events
- **Admin Check**: AuthContext checks user role on login and provides `isAdmin` state
- **Admin Status Caching**: Admin status is cached in localStorage for instant display on page refresh
  - Cached value used immediately on page load to prevent UI flicker
  - Background verification happens without blocking navigation
  - Cache cleared automatically on logout
- **Hooks**: `useAdminPermissions` hook provides granular permission checks

### Layout System
Three distinct layouts managed by React Router:

**PublicLayout** (`/`):
- Header component with navigation
- Container-based content area
- Used for landing page only

**AuthLayout** (`/sign-in`, `/sign-up`, `/auth/*`):
- Vertically centered content without header navigation
- Displays app logo from database settings (if configured)
- Maximum width of 432px (max-w-md)
- Used for all authentication pages

**DashboardLayout** (`/dashboard`, `/dashboard/*`):
- Grid-based layout with sidebar (220px/280px responsive)
- Fixed header with UserButton
- Main content area with consistent padding
- Requires authentication

### Route Structure in App.tsx

/ (PublicLayout)
+-- / -> Index.tsx

/auth (AuthLayout)
|-- /sign-in -> SignInPage.tsx
|-- /sign-up -> SignUpPage.tsx
|-- /auth/callback -> AuthCallback.tsx
|-- /auth/reset-password -> ResetPasswordPage.tsx
+-- /auth/update-password -> UpdatePasswordPage.tsx

/dashboard (DashboardLayout - Auth Required)
|-- /dashboard -> DashboardPage.tsx
|-- /dashboard/generate -> GeneratePage.tsx
|-- /dashboard/settings -> SettingsPage.tsx
|-- /dashboard/profile -> ProfilePage.tsx
+-- /dashboard/admin/* -> Admin routes (InviteUser, etc.)

### shadcn/ui Integration
- Complete component library in `src/components/ui/`
- Configured with slate base color and CSS variables
- Path aliases: `@/components`, `@/lib/utils`, `@/hooks`
- **Do not modify** existing shadcn components - create new ones if customization needed

### Key Architectural Decisions
- All routes defined in `App.tsx` (per AI_RULES.md)
- Pages in `src/pages/`, components in `src/components/`
- Main page is `src/pages/Index.tsx`
- TanStack Query for data fetching
- Dual toast systems: shadcn Toaster + Sonner
- Dyad component tagger for development

### Authentication Configuration Notes
- **Password Reset Flow**: Uses implicit flow (`flowType: 'implicit'` in `src/lib/supabase.ts`)
- **Why Implicit Over PKCE**: PKCE flow fails for password reset links because the code verifier is stored in sessionStorage, which is domain-specific
- **Direct Redirects**: Password reset emails redirect directly to `/auth/update-password`
- **Auth Events**: The `AuthCallback` component listens for `PASSWORD_RECOVERY` events

## Email System Architecture

### Real Email Integration (CORS-Free)
Platform-agnostic email system that works locally and in production:

**Development Environment:**
- Vite plugin in `vite.config.ts` serves API functions locally at `/api/send-email`
- Custom middleware handles CORS headers and request parsing

**Production Environment:**
- Serverless function at `/api/send-email.ts` for Vercel/Netlify/Railway deployment

### Email Features
- Settings Management, Test Functionality, User Invitations, Database Integration
- Service Provider: Resend.com integration

### Key Files
- `/api/send-email.ts` - Serverless email API function (uses service role key)
- `src/lib/email.ts` - Client-side email functions
- `src/pages/SettingsPage.tsx` - Email configuration UI
- `src/lib/admin.ts` - Admin user management with email integration

## Database Schema

### Supabase Integration
- Connection: Configured in `src/lib/supabase.ts` using environment variables
- Authentication: Supabase Auth with user IDs as foreign keys
- CASCADE DELETE: All user-related tables have CASCADE DELETE foreign keys to auth.users

### Key Tables
- `user_api_keys`, `user_roles`, `user_metadata`, `admin_audit_log`, `app_settings`

## Admin System

### Admin Authentication
- Admin Detection via AuthContext checking user_roles table
- Admin Status Caching in localStorage for instant display
- Performance Optimization: async check without blocking navigation

### Admin Dashboard Architecture
Vertical tabbed interface: Overview, Users, Invitations, Settings, Audit Logs

### User Management Features
- User Invitations with real email via Resend
- Direct User Creation, Role Management, Audit Logging
- User Deletion System: Dual-Path (auth users via API, invitation-only via direct DB)
- CASCADE DELETE for all related data

### Invitation System
- Database: user_roles table with invitation_id (UUID), expires_at, created_by
- UUID Format via crypto.randomUUID()
- Email Templates in src/lib/email.ts
- Integration with Supabase Auth signup flow

## Stripe Admin Management System

- Product Management: Create, update, archive subscription plans and credit packages
- Automatic Stripe Integration with proper metadata tagging
- Two-Way Synchronization with conflict resolution
- Price Immutability handling
- Test Mode Support with visual indicators
- Metadata Filtering: Multi-tenant safety using `app: 'video-studio'` metadata
- Sync Monitoring dashboard
- Audit Logging in stripe_sync_log table
- Rate Limiting: 100 requests/minute, 10 syncs/hour
- Retry Logic: Exponential backoff from 1s to 30s

## App Settings System

- Dynamic Branding: app name, logo, favicon
- SEO Configuration, React Context for global state
- Admin-Only Access, RLS Policies
- API endpoint requires service role key to bypass RLS

## Database Migrations

Located in `supabase/migrations/`:
- 00000_initial_schema.sql - Complete database setup
- 00001_update_app_settings_rls.sql - RLS policy updates
- 00002_user_deletion_cascade.sql - CASCADE DELETE constraints
- 00003_add_created_by_to_user_roles.sql - Invitation creator tracking
- 00005_stripe_admin_management.sql - Stripe product/pricing management

## Troubleshooting

Common issues: Email settings (service role key), Invitation creation (RLS), UUID format, missing columns, email domain mismatch, service role table permissions.
```

## What This Document Controls

- **Complete Architecture Reference**: Every subsystem documented in detail
- **Authentication**: Supabase Auth with implicit flow, admin caching, password reset flow
- **Layout System**: 3 distinct layouts (Public/Auth/Dashboard) with specific styling
- **Route Structure**: Full route tree with component mappings
- **Email System**: Platform-agnostic with dev/production environments
- **Database Schema**: Tables, RLS policies, CASCADE DELETE, migrations
- **Admin System**: User management, invitations, audit logging, role-based access
- **Stripe Integration**: Two-way sync, rate limiting, metadata filtering, price history
- **App Settings**: Dynamic branding, SEO, React context management
- **Troubleshooting**: Common issues with specific solutions
