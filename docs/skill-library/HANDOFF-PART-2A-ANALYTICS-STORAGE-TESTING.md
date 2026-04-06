# Skill Generation Handoff — Part 2A: Analytics, Email, Storage, Testing, Deployment (Skills 24-39)

> Run `npx ctx7 skills generate`, paste the prompt, save output to the listed path.
> See Part 1A for setup instructions.

---

## ANALYTICS

### 24. posthog
- **Save to:** `skills/analytics/posthog.md`
- **Library:** PostHog JS SDK | **Boilerplate:** web, dual

**Paste this prompt into ctx7:**
> PostHog analytics patterns including: posthog.capture() for custom events, feature flags with posthog.isFeatureEnabled() and useFeatureFlagEnabled() React hook, session recording configuration, user identification with posthog.identify(), group analytics for B2B with posthog.group(), Next.js integration with PostHogProvider and PostHogPageView component, server-side event capture, and A/B testing with feature flag payloads.

**When the wizard asks:**
- Framework? → "Next.js App Router"
- SDK? → "posthog-js client SDK, not the Node SDK"
- Features? → "Events, feature flags, session recording"

**Must include these patterns:**
- `posthog.capture('event_name', { property: value })`
- `posthog.identify(userId, { email, name })`
- `useFeatureFlagEnabled('flag-name')` React hook
- `PostHogProvider` wrapper in Next.js layout
- `PostHogPageView` component for automatic pageviews

---

### 25. plausible
- **Save to:** `skills/analytics/plausible.md`
- **Library:** Plausible Analytics | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Plausible Analytics patterns including: script tag installation with data-domain attribute, custom event tracking with plausible() function, goal conversions setup, custom properties for event metadata, Stats API for programmatic data access, proxy setup for ad-blocker bypass, self-hosting configuration, and Next.js Script component integration. Lightweight, privacy-first alternative to Google Analytics.

**When the wizard asks:**
- Hosting? → "Cloud (plausible.io) primary, self-hosted secondary"
- Framework? → "Next.js"
- Privacy? → "No cookies, GDPR compliant by default"

**Must include these patterns:**
- `<script data-domain="yoursite.com" src="https://plausible.io/js/script.js">`
- `plausible('Signup', { props: { plan: 'pro' } })` custom events
- Goal setup in dashboard for conversion tracking
- Stats API: `GET /api/v1/stats/aggregate` with filters
- Next.js: `<Script data-domain="..." src="..." strategy="afterInteractive" />`

---

## EMAIL

### 26. resend
- **Save to:** `skills/email/resend.md`
- **Library:** Resend | **Boilerplate:** web, dual

**Paste this prompt into ctx7:**
> Resend email patterns including: resend.emails.send() for transactional email, React Email JSX templates for type-safe email design, domain verification and DNS setup, webhook configuration for delivery events (delivered, bounced, complained), batch sending with resend.batch.send(), file attachments, CC/BCC/reply-to fields, and error handling with typed error responses.

**When the wizard asks:**
- Templates? → "React Email JSX components"
- Framework? → "Next.js API routes or server actions"
- Webhooks? → "Include delivery status webhooks"

**Must include these patterns:**
- `resend.emails.send({ from, to, subject, react: <Template /> })`
- React Email template with `<Html><Body><Text>` components
- Domain verification DNS records (SPF, DKIM, DMARC)
- Webhook handler for `email.delivered`, `email.bounced`
- `resend.batch.send([...emails])` for bulk sending

---

### 27. sendgrid
- **Save to:** `skills/email/sendgrid.md`
- **Library:** SendGrid | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> SendGrid email patterns including: @sendgrid/mail sgMail.send() for transactional email, dynamic templates with handlebars syntax and template data, template management via API, Event Webhook for delivery tracking (open, click, bounce, spam report), Inbound Parse for receiving email, sender identity verification, and email validation API for list cleaning.

**When the wizard asks:**
- API version? → "v3 Web API, not SMTP"
- Templates? → "Dynamic templates with handlebars"
- Events? → "Event Webhook for delivery tracking"

**Must include these patterns:**
- `sgMail.send({ to, from, templateId, dynamicTemplateData: {} })`
- Dynamic template handlebars: `{{firstName}}`, `{{#if}}`, `{{#each}}`
- Event Webhook handler for opens, clicks, bounces
- `sgMail.setApiKey(process.env.SENDGRID_API_KEY)` setup
- Inbound Parse webhook for receiving email

---

### 28. loops-so
- **Save to:** `skills/email/loops-so.md`
- **Library:** Loops.so | **Boilerplate:** web, dual

**Paste this prompt into ctx7:**
> Loops.so email platform patterns including: transactional email API for triggered messages, contact management with create/update/find operations, event-based triggers for automated sequences, audience segments for targeted campaigns, API key authentication, and webhook integration for contact events. Focus on the REST API for programmatic access.

**When the wizard asks:**
- Use case? → "Transactional and marketing email for SaaS"
- Integration? → "REST API from Next.js server"
- Contacts? → "Sync users from Supabase to Loops"

**Must include these patterns:**
- `POST /v1/transactional` to send transactional email
- `POST /v1/contacts/create` for adding contacts
- `PUT /v1/contacts/update` for updating contact properties
- Event sending: `POST /v1/events/send` with event name and email
- API key header: `Authorization: Bearer loops_...`

---

## STORAGE

### 29. supabase-storage
- **Save to:** `skills/storage/supabase-storage.md`
- **Library:** Supabase Storage | **Boilerplate:** web, dual

**Paste this prompt into ctx7:**
> Supabase Storage patterns including: file upload with supabase.storage.from(bucket).upload(), file download with download() and getPublicUrl(), signed URLs with createSignedUrl() for temporary access, image transformations with transform option (width, height, quality), bucket creation and configuration (public vs private), RLS policies on storage.objects table, file listing with list(), file deletion with remove(), and multipart upload for large files.

**When the wizard asks:**
- Security? → "RLS policies on storage.objects"
- Access? → "Both public and private buckets"
- Transforms? → "Image transformations for thumbnails"

**Must include these patterns:**
- `supabase.storage.from('avatars').upload(path, file)`
- `supabase.storage.from('avatars').getPublicUrl(path)`
- `supabase.storage.from('docs').createSignedUrl(path, 3600)`
- `supabase.storage.from('avatars').download(path)`
- RLS: `CREATE POLICY ... ON storage.objects USING (bucket_id = 'avatars' AND auth.uid()::text = (storage.foldername(name))[1])`

---

### 30. uploadthing
- **Save to:** `skills/storage/uploadthing.md`
- **Library:** UploadThing | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> UploadThing file upload patterns including: createUploadthing() for defining upload routes, FileRouter with file type and size validation, UploadButton and UploadDropzone React components, onUploadComplete callback for post-upload processing, middleware function for authentication, useUploadThing hook for programmatic uploads, and server-side file URL access after upload.

**When the wizard asks:**
- Framework? → "Next.js App Router"
- Components? → "Pre-built React components"
- Auth? → "Middleware for user verification"

**Must include these patterns:**
- `createUploadthing()` and `f({ image: { maxFileSize: '4MB' } })`
- FileRouter with `.middleware()` for auth and `.onUploadComplete()`
- `<UploadButton endpoint="imageUploader" />` component
- `<UploadDropzone endpoint="imageUploader" />` drag-and-drop
- `useUploadThing('imageUploader')` hook for custom UI

---

### 31. cloudflare-r2
- **Save to:** `skills/storage/cloudflare-r2.md`
- **Library:** Cloudflare R2 | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Cloudflare R2 object storage patterns including: S3-compatible API with @aws-sdk/client-s3, Workers binding for direct R2 access (env.MY_BUCKET.put/get/delete), presigned URLs for direct client uploads with PutObjectCommand, public bucket access via r2.dev custom domain, lifecycle rules for automatic deletion, multipart uploads for large files, and CORS configuration.

**When the wizard asks:**
- Access method? → "Both S3 API and Workers binding"
- Auth? → "Presigned URLs for client uploads"
- CDN? → "Public bucket with custom domain"

**Must include these patterns:**
- Workers: `env.MY_BUCKET.put(key, body)` and `env.MY_BUCKET.get(key)`
- S3 API: `new S3Client({ endpoint, credentials })` with R2 endpoint
- `getSignedUrl(client, new PutObjectCommand({ Bucket, Key }), { expiresIn })`
- Public access: `https://pub-xxx.r2.dev/path/to/file`
- CORS: `AllowedOrigins`, `AllowedMethods` configuration

---

## TESTING

### 32. playwright
- **Save to:** `skills/testing/playwright.md`
- **Library:** Playwright | **Boilerplate:** web, dual

**Paste this prompt into ctx7:**
> Playwright testing patterns including: test() function with descriptive names, page.goto/click/fill for interactions, expect assertions (toBeVisible, toHaveText, toHaveURL, toContainText), test.describe for grouping, fixtures for shared setup, Page Object Model pattern for maintainable tests, visual regression with toHaveScreenshot(), API testing with request context, trace viewer for debugging failures, and test configuration in playwright.config.ts.

**When the wizard asks:**
- Framework? → "Next.js"
- Browsers? → "Chromium primary, cross-browser optional"
- Patterns? → "Page Object Model for large test suites"

**Must include these patterns:**
- `test('user can sign up', async ({ page }) => { ... })`
- `await page.goto('/'); await page.click('button'); await page.fill('input', 'text')`
- `await expect(page.locator('h1')).toHaveText('Welcome')`
- Page Object: `class LoginPage { constructor(page) { ... } async login() { ... } }`
- `await expect(page).toHaveScreenshot()` visual regression

---

### 33. vitest
- **Save to:** `skills/testing/vitest.md`
- **Library:** Vitest | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Vitest testing patterns including: describe/it/expect for test structure, vi.mock() for module mocking, vi.spyOn() for function spying, coverage configuration with @vitest/coverage-v8, snapshot testing with toMatchSnapshot and toMatchInlineSnapshot, workspace configuration for monorepos, browser mode with @vitest/browser, TypeScript support without configuration, and setup files for global test configuration.

**When the wizard asks:**
- Framework? → "Framework-agnostic, works with any"
- Coverage? → "@vitest/coverage-v8"
- Mocking? → "vi.mock and vi.spyOn built-in"

**Must include these patterns:**
- `describe('Module', () => { it('should work', () => { expect(result).toBe(expected) }) })`
- `vi.mock('./module', () => ({ fn: vi.fn() }))`
- `vi.spyOn(object, 'method').mockReturnValue(value)`
- `expect(result).toMatchInlineSnapshot()` inline snapshots
- `vitest.config.ts` with coverage and setup files

---

### 34. cypress
- **Save to:** `skills/testing/cypress.md`
- **Library:** Cypress | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Cypress testing patterns including: cy.visit/get/click/type for interactions, cy.intercept() for API mocking and network stubbing, fixtures for test data in cypress/fixtures/, custom commands in cypress/support/commands.ts, component testing with cy.mount(), cy.wait('@alias') for network request assertions, should() assertions with chaining, and cypress.config.ts configuration for E2E and component testing.

**When the wizard asks:**
- Testing type? → "E2E primary, component testing secondary"
- Framework? → "React with Next.js"
- API mocking? → "cy.intercept for network stubbing"

**Must include these patterns:**
- `cy.visit('/login'); cy.get('[data-testid="email"]').type('user@test.com')`
- `cy.intercept('POST', '/api/login', { statusCode: 200, body: { token: '...' } }).as('login')`
- `cy.wait('@login').its('response.statusCode').should('eq', 200)`
- Custom command: `Cypress.Commands.add('login', (email, password) => { ... })`
- `cy.mount(<Component />)` for component testing

---

## DEPLOYMENT

### 35. vercel
- **Save to:** `skills/deployment/vercel.md`
- **Library:** Vercel | **Boilerplate:** web, dual

**Paste this prompt into ctx7:**
> Vercel deployment patterns including: vercel.json configuration for rewrites, redirects, and headers, environment variables via dashboard and CLI, serverless functions in app/api/ with export const runtime='edge' option, OG image generation with @vercel/og and ImageResponse, build command and output directory configuration, custom domain setup and DNS, preview deployments for PRs, and Vercel CLI for local development with vercel dev.

**When the wizard asks:**
- Framework? → "Next.js (auto-detected)"
- Functions? → "Both serverless and edge runtime"
- Features? → "OG image generation, preview deploys"

**Must include these patterns:**
- `vercel.json` with `rewrites`, `redirects`, `headers` config
- Environment variables: `vercel env add VARIABLE_NAME`
- `export const runtime = 'edge'` in route handlers
- `new ImageResponse(<div>...</div>)` with `@vercel/og`
- `vercel --prod` for production deploy via CLI

---

### 36. netlify
- **Save to:** `skills/deployment/netlify.md`
- **Library:** Netlify | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Netlify deployment patterns including: netlify.toml configuration for build settings and redirects, serverless functions in netlify/functions/ directory with handler export, edge functions in netlify/edge-functions/ with Deno runtime, _redirects file for URL routing, environment variables via dashboard and CLI, build plugins for extending the build process, and Netlify CLI (netlify dev) for local development.

**When the wizard asks:**
- Framework? → "Next.js with @netlify/plugin-nextjs"
- Functions? → "Serverless functions in netlify/functions/"
- Redirects? → "Both netlify.toml and _redirects file"

**Must include these patterns:**
- `netlify.toml` with `[build]` command and publish directory
- `export const handler = async (event, context) => { return { statusCode: 200, body: '...' } }`
- Edge function: `export default async (request, context) => { ... }`
- `[[redirects]]` in netlify.toml or `_redirects` file
- `netlify dev` for local development with functions

---

### 37. railway
- **Save to:** `skills/deployment/railway.md`
- **Library:** Railway | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Railway deployment patterns including: automatic deployment from GitHub repos, railway.json service configuration, PostgreSQL and Redis database provisioning with one click, environment variables with reference syntax (${{Postgres.DATABASE_URL}}), persistent volumes for file storage, private networking between services, Railway CLI for local development (railway run), health check configuration, and custom domains.

**When the wizard asks:**
- Services? → "Web service + database"
- Database? → "PostgreSQL provisioned on Railway"
- Networking? → "Private networking between services"

**Must include these patterns:**
- `railway.json` with `build` and `deploy` configuration
- `${{Postgres.DATABASE_URL}}` reference variable syntax
- `railway link` to connect local project to Railway
- `railway run npm run dev` for local dev with Railway env vars
- Volume mount for persistent file storage

---

### 38. cloudflare-workers
- **Save to:** `skills/deployment/cloudflare-workers.md`
- **Library:** Cloudflare Workers | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Cloudflare Workers patterns including: export default { fetch } handler for HTTP requests, KV namespace for key-value storage, Durable Objects for stateful coordination, D1 SQLite database for relational data, Queues for async message processing, scheduled() handler for cron triggers, wrangler.toml configuration for bindings, wrangler dev for local development, and environment variables with secrets.

**When the wizard asks:**
- Runtime? → "Workers runtime (not Node.js)"
- Storage? → "KV for simple, D1 for relational, Durable Objects for stateful"
- CLI? → "Wrangler CLI"

**Must include these patterns:**
- `export default { async fetch(request, env, ctx) { ... } }`
- KV: `await env.MY_KV.put(key, value)` and `await env.MY_KV.get(key)`
- D1: `await env.DB.prepare('SELECT * FROM users').all()`
- `wrangler.toml` with `[[kv_namespaces]]`, `[[d1_databases]]` bindings
- `scheduled(event, env, ctx)` for cron jobs

---

### 39. docker
- **Save to:** `skills/deployment/docker.md`
- **Library:** Docker | **Boilerplate:** universal

**Paste this prompt into ctx7:**
> Docker patterns including: Dockerfile with FROM, RUN, COPY, WORKDIR, CMD instructions, multi-stage builds for smaller production images, docker-compose.yml for multi-service orchestration with services, volumes, and networks, health checks with HEALTHCHECK instruction, .dockerignore for excluding files, production optimization (non-root user, layer caching, alpine base images, dependency caching with --mount=type=cache), and environment variable handling with ARG and ENV.

**When the wizard asks:**
- Use case? → "Production deployment of Next.js and Python apps"
- Base images? → "Alpine for small size, node:slim as alternative"
- Orchestration? → "Docker Compose for local development"

**Must include these patterns:**
- Multi-stage: `FROM node:20-alpine AS builder` → `FROM node:20-alpine AS runner`
- `COPY --from=builder /app/.next ./.next` for build artifacts only
- `docker-compose.yml` with `services:`, `volumes:`, `networks:`
- `HEALTHCHECK CMD curl -f http://localhost:3000/ || exit 1`
- `RUN addgroup -S app && adduser -S app -G app` non-root user
