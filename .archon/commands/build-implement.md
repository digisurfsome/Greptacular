# Implement: Execute Plan Step by Step

Based on Cole's Implement cookbook. Execute the enriched plan with validation gates after each task.

## Input

Read enriched phase files from `$ARTIFACTS_DIR/phases/phase-*-enriched.md` (or `phase-*.md` if enriched not available).
Read `$ARTIFACTS_DIR/CLAUDE.md` and `$ARTIFACTS_DIR/BUILD_RULES.md`.
Read `$ARTIFACTS_DIR/context_packet.json` for mechanism blueprints and Wall/Door/Room classifications.

## Process

### Step 0: Production Defaults (BEFORE writing any code)

Create these files FIRST before building anything:

1. **`.gitignore`** at project root:
   ```
   node_modules/
   dist/
   .env
   *.db
   *.sqlite
   .DS_Store
   ```

2. **Prisma schema** (if using Prisma): always include Linux binary target:
   ```prisma
   generator client {
     provider      = "prisma-client-js"
     binaryTargets = ["native", "debian-openssl-3.0.x"]
   }
   ```

3. **Monorepo serving** (if separate client/server): Express must serve the built React frontend:
   ```typescript
   // After ALL API routes in the server entry file:
   import path from 'path'
   const clientDist = path.join(__dirname, '../../client/dist')
   app.use(express.static(clientDist))
   app.get('*', (_req, res) => {
     res.sendFile(path.join(clientDist, 'index.html'))
   })
   ```

4. **CORS**: never hardcode localhost. Use:
   ```typescript
   origin: process.env.CORS_ORIGIN || true
   ```

5. **Root package.json** (if monorepo): include scripts that build BOTH client and server:
   ```json
   "build": "cd client && npm install && npx vite build && cd ../server && npm install && npx prisma generate && npx tsc",
   "start": "cd server && npx prisma db push --skip-generate && node dist/index.js"
   ```

### Step 1: Preflight
- Read all mandatory reading files listed in the plan
- Verify "Patterns to Mirror" code snippets still match the codebase
- Check git state is clean

### Step 2: Execute Each Phase
For each phase file, in order:

**Per file in the build order:**
1. Read the target file (if UPDATE) or parent directory (if CREATE)
2. Read the MIRROR reference from the plan
3. Make the changes following Wall/Door/Room classifications:
   - WALL steps: Implement EXACTLY as specified. One way only.
   - DOOR steps: Choose within the defined constraints.
   - ROOM steps: Use best judgment within topic boundaries.
4. Run PULSE check after each file (from protocol injection):
   - File exists at expected path
   - Exports expected functions/components
   - No syntax errors
5. If pulse check fails: fix immediately before moving on
6. If stuck after 2 fix attempts: STOP and document the issue

**At mechanism connection points:**
- Run SEAM checks: imports resolve, interfaces match

**At end of each phase:**
- Run FULL checkpoint: compile, test, git diff against files_allowed
- Gate: ALL must pass before next phase

### Step 3: Track Deviations
If you must deviate from the plan, document:
- WHAT changed
- WHY it changed
- Impact on downstream phases

### Step 4: Two-Strike Rule
Maximum 2 retries per phase. On second failure: STOP for human review.
"If 2 fresh attempts fail the same phase, the problem is the phase spec, not the agent."

## Output

Write implementation report to `$ARTIFACTS_DIR/implementation-report.md`:
- Tasks completed vs total
- Validation results per phase
- Deviations from plan
- Predicted vs actual complexity
- Files created/modified with line counts
