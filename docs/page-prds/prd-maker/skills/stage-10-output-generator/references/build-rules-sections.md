# BUILD_RULES.md — Section Templates

> Detailed reference playbook. Lives alongside CLAUDE.md in repo root.
> CLAUDE.md points to specific sections here for deeper protocols.
> Derived from Martin's 13 modules, adapted to the user's tech stack.

---

## Section Map

| Section | Source Module | Purpose |
|---------|-------------|---------|
| Debugging Protocol | Martin Module 08 (Bug Fix) | Step-by-step bug fixing methodology |
| Trace-First Debugging | Martin Module 10 (Debug) | Deep debugging with tracing |
| Feature Addition Protocol | Martin Module 09 (Feature Add) | How to add features safely |
| Testing & Verification | Martin Module 13 (Testing) | Testing standards and checklist |
| Data Access Patterns | Martin Module 03 (Data Layer) | Database and data layer conventions |
| Entity CRUD Pattern | Martin Module 05 (CRUD Flow) | Standard CRUD implementation pattern |

---

## Section Templates

### Debugging Protocol

```markdown
## Debugging Protocol

When you encounter a bug, follow this sequence. Do NOT skip steps.

### 1. Reproduce
- Identify the exact steps that trigger the bug
- Note the expected vs actual behavior
- Check if the bug is consistent or intermittent

### 2. Read the Error
- Read the FULL error message and stack trace
- Identify the file and line number
- Note any relevant variable values

### 3. Trace the Path
- Start at the error location
- Trace backwards through the call stack
- Identify where the data becomes incorrect
- Map the flow: {source} → {transform} → {destination} → {error}

### 4. Isolate
- Determine the smallest change that causes the bug
- Check: is this a data problem, logic problem, or timing problem?
- Check recent changes: `git log --oneline -10`

### 5. Fix
- Fix the ROOT CAUSE, not the symptom
- Make the minimal change needed
- Don't refactor while fixing — that's a separate task

### 6. Verify
```bash
# Run build
{build_command}

# Run tests
{test_command}

# Verify the specific bug is fixed
{manual_verification_step}

# Verify nothing else broke
{lint_command}
```

### 7. Document
- If the bug was non-obvious, add a comment explaining WHY the fix works
- If it could happen again, consider adding a test
```

---

### Trace-First Debugging

```markdown
## Trace-First Debugging

For complex bugs where the Debugging Protocol didn't find the root cause.

### Approach
1. Add logging at EVERY step of the suspected code path
2. Log inputs, outputs, and intermediate values
3. Run the reproduction steps
4. Read the trace from start to finish
5. The bug is where the trace diverges from expectations

### Trace Template
```{language}
// At function entry
console.log('[{function_name}] INPUT:', JSON.stringify({params}));

// At decision points
console.log('[{function_name}] BRANCH:', {condition} ? 'true-path' : 'false-path');

// At function exit
console.log('[{function_name}] OUTPUT:', JSON.stringify({result}));
```

### When to Use
- The bug only appears with specific data
- The error message doesn't point to the real cause
- Multiple components interact and you're unsure which one is wrong
- The bug is timing-related (race condition, async ordering)

### Clean Up
After finding the bug, REMOVE all trace logging before committing.
```

---

### Feature Addition Protocol

```markdown
## Feature Addition Protocol

When adding a new feature, follow this sequence to avoid breaking existing code.

### 1. Understand Context
- Read ALL files that will be affected by the feature
- Identify existing patterns for similar features
- Check if a similar feature already exists (extend it, don't duplicate)

### 2. Plan the Changes
- List every file that needs modification
- List every new file to create
- Identify which existing tests need updating
- Check: does this feature touch any shared/critical files?

### 3. Implement
- Create new files FIRST (types, interfaces, utilities)
- Modify existing files SECOND (add imports, wire up)
- Follow existing patterns — if the codebase uses {pattern}, you use {pattern}
- Keep changes minimal — don't refactor while adding

### 4. Wire Up
- Update route definitions if adding a page
- Update navigation if adding a user-facing feature
- Update exports/imports in index files
- Update types if adding new data shapes

### 5. Verify
```bash
{build_command}
{lint_command}
{test_command}
```

### 6. Self-Check
- [ ] Does the feature match the requirement exactly (no more, no less)?
- [ ] Did I modify only the files that needed changing?
- [ ] Did I follow existing patterns?
- [ ] Did I update all imports and exports?
- [ ] Is error handling present at boundaries?
```

---

### Testing & Verification

```markdown
## Testing & Verification

### After Every Change
```bash
# Compile check — does it build?
{build_command}

# Lint check — does it meet code standards?
{lint_command}

# Test check — do existing tests pass?
{test_command}
```

### When to Write Tests
- New utility functions: ALWAYS
- New API endpoints: ALWAYS
- Complex business logic: ALWAYS
- Simple UI components: ONLY if they have conditional rendering logic
- Configuration changes: NEVER (just verify the build)

### Test Structure
```{language}
describe('{ComponentOrFunction}', () => {
  it('should {expected_behavior} when {condition}', () => {
    // Arrange: set up test data
    // Act: call the function / render the component
    // Assert: verify the expected outcome
  });

  it('should handle {edge_case}', () => {
    // Test the boundary condition
  });

  it('should throw/return error when {invalid_input}', () => {
    // Test error handling
  });
});
```

### Regression Checklist
After any change, manually verify:
- [ ] The changed feature works as expected
- [ ] Adjacent features still work (anything sharing state, routes, or data)
- [ ] No console errors in browser (for UI changes)
- [ ] No new lint warnings
```

---

### Data Access Patterns

```markdown
## Data Access Patterns

### Single Source of Truth
All database access goes through a dedicated data layer.
- {Database access file path from stage_0/stage_7}
- Components NEVER query the database directly
- All queries are typed and return typed results

### Query Pattern
```{language}
// GOOD: centralized, typed, reusable
export async function get{Entity}ById(id: string): Promise<{Entity}> {
  const { data, error } = await {db_client}.from('{table}').select('*').eq('id', id).single();
  if (error) throw new {EntityError}(error.message);
  return data;
}

// BAD: inline query in component
const { data } = await supabase.from('items').select('*');  // NEVER do this
```

### Mutation Pattern
```{language}
export async function create{Entity}(input: Create{Entity}Input): Promise<{Entity}> {
  // Validate input
  // Execute mutation
  // Return typed result
  // Handle errors at this layer
}
```

### Rules
- Every query function returns a typed result
- Error handling happens in the data layer, not the UI
- Queries include only the fields needed (no `select('*')` in production)
- Mutations validate input before executing
```

---

### Entity CRUD Pattern

```markdown
## Entity CRUD Pattern

When building CRUD for any entity, follow this standard pattern.

### File Structure
```
{entity_directory}/
├── {entity}.types.ts     # Types and interfaces
├── {entity}.queries.ts   # Data access (read operations)
├── {entity}.mutations.ts # Data access (write operations)
├── {entity}.list.tsx     # List/table view component
├── {entity}.detail.tsx   # Detail/single view component
├── {entity}.form.tsx     # Create/edit form component
└── {entity}.test.ts      # Tests
```

### Implementation Order
1. Types first — define the entity shape
2. Queries — read operations (list, getById, search)
3. Mutations — write operations (create, update, delete)
4. List view — display all entities
5. Detail view — display single entity
6. Form — create and edit
7. Wire up routes and navigation

### Standard Operations
| Operation | Function | Route |
|-----------|----------|-------|
| List | `get{Entity}List()` | `/{entities}` |
| Detail | `get{Entity}ById(id)` | `/{entities}/:id` |
| Create | `create{Entity}(input)` | `/{entities}/new` |
| Update | `update{Entity}(id, input)` | `/{entities}/:id/edit` |
| Delete | `delete{Entity}(id)` | N/A (action on detail page) |

### Rules
- Always include loading states
- Always include error states
- Always include empty states (no data)
- Delete requires confirmation
- Forms validate before submission
- Optimistic updates where appropriate (list operations)
```

---

## Rendering Rules

1. Replace ALL `{placeholders}` with actual values from `stage_0.tech_stack`
2. Replace `{language}` with the stack's primary language (typescript, python, etc.)
3. Replace `{build_command}`, `{lint_command}`, `{test_command}` with actual commands
4. Replace `{db_client}` with the actual database client name
5. If a section is not applicable to the tech stack (e.g., "Entity CRUD Pattern" for a CLI tool), omit it entirely
6. Martin's name NEVER appears. Rules are presented as project conventions.
7. Keep each section focused — no cross-references between BUILD_RULES.md sections
8. CLAUDE.md references these sections by exact name — section headings must be stable
