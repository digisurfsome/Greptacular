# Deploy: Package and Push to Target Repository

Package the built application for production deployment. This is the final pipeline node.

## Input

Read `$ARTIFACTS_DIR/context_packet.json` for tech stack info.
Read `$ARTIFACTS_DIR/build-report.md` for build status.
Read `$ARTIFACTS_DIR/implementation-report.md` for file list.

## Process

### Step 1: Production Readiness Checks

Before packaging, verify these exist and are correct:

1. **`.gitignore`** — must contain at minimum:
   ```
   node_modules/
   dist/
   .env
   *.db
   *.sqlite
   .DS_Store
   ```
   If missing, CREATE IT.

2. **Prisma binary targets** (if Prisma is used):
   Check `prisma/schema.prisma` for `binaryTargets`. Must include BOTH:
   ```prisma
   binaryTargets = ["native", "debian-openssl-3.0.x"]
   ```
   If only `"native"` is present, add `"debian-openssl-3.0.x"` for Linux deployment.

3. **Frontend serving** (if monorepo with separate client/server):
   Check if the Express/backend server serves the built frontend static files.
   If NOT, add to the server's main entry file:
   ```typescript
   import path from 'path'
   // After all API routes:
   const clientDist = path.join(__dirname, '../../client/dist')
   app.use(express.static(clientDist))
   app.get('*', (_req, res) => {
     res.sendFile(path.join(clientDist, 'index.html'))
   })
   ```

4. **CORS** — If CORS origin is hardcoded to `localhost`, change to:
   ```typescript
   origin: process.env.CORS_ORIGIN || true
   ```

5. **Root package.json scripts** (if monorepo):
   Ensure `build` script builds BOTH client and server:
   ```json
   "build": "cd client && npm install && npx vite build && cd ../server && npm install && npx prisma generate && npx tsc",
   "start": "cd server && npx prisma db push --skip-generate && node dist/index.js"
   ```

6. **Environment variables**:
   Create `$ARTIFACTS_DIR/.env.example` listing all required env vars:
   ```
   DATABASE_URL=file:./dev.db
   JWT_SECRET=change-me-to-a-random-string
   PORT=3001
   CORS_ORIGIN=http://localhost:5173
   ```

### Step 2: Clean Up

- Delete any committed `node_modules/` directories
- Delete any `.env` files with real secrets (replace with `.env.example`)
- Delete any `*.db` or `*.sqlite` files
- Delete any build artifacts (`dist/`, `.next/`, etc.)

### Step 3: Commit Everything

```bash
git add -A
git commit -m "Production-ready build from PRD Pipeline B"
```

### Step 4: Push to Remote

```bash
git push origin main
```

If push fails due to no remote, document the repo path and files for manual deployment.

## Output

Write deployment summary to `$ARTIFACTS_DIR/deploy-report.md`:
- Files committed
- Production checks passed/failed
- Environment variables required
- Deploy instructions for Railway/Vercel/Render:
  - Build command
  - Start command
  - Required env vars
- URL (if available)

Also output the summary as your response.
