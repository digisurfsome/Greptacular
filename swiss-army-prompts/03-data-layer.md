# MODULE 03: DATA LAYER PROMPT

## Supabase Tables, RLS Policies, and Service Functions

**What this does:** Creates your app's database tables, secures them with Row Level Security, and builds a clean service layer so components never talk to Supabase directly. Also adds delete-account functionality.

**Prerequisite:** Modules 01 (Scaffold) and 02 (Auth) must be complete.

**This is the module where you define WHAT your app stores.** Fill in Section 1 below.

---

## --- START PROMPT ---

## TASK: Build the Supabase Data Layer

Create database tables, RLS policies, and a TypeScript service layer for this app. Follow every instruction exactly. Read the existing codebase first.

Read these files before starting: `src/config/supabase.ts`, `src/types/index.ts`, `src/types/supabase.ts`, `src/contexts/AuthContext.tsx`.

---

## SECTION 1: YOUR DATA ENTITIES [FILL THIS IN]

Define what your app stores. Be specific.

**Entity 1:** [NAME]
- Fields: [list each field with its type]
- Example: `title: string, description: string (optional), status: enum (draft/published/archived), priority: number`
- Belongs to: user (each user has their own)
- Sorting: by created_at descending (newest first)

**Entity 2:** [NAME] (if applicable)
- Fields: [list each field with its type]
- Belongs to: user
- Sorting: [how should these be ordered?]

**Entity 3:** [NAME] (if applicable)
- Fields: [list each field with its type]
- Belongs to: [user / entity 1 / entity 2]
- Sorting: [how should these be ordered?]

**Relationships:**
- [e.g., "Each Project has many Tasks" or "Each Recipe has many Ingredients"]

---

## SECTION 2: SQL GENERATION RULES

For each entity defined above, generate SQL following these exact patterns.

### Table Template

For EVERY table, use this structure:

```sql
-- ============================================
-- [TABLE_NAME] TABLE
-- [Brief description of what this stores]
-- ============================================

CREATE TABLE public.[table_name] (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,

  -- Entity-specific fields go here
  -- Use appropriate types:
  --   TEXT for strings
  --   INTEGER for numbers
  --   BOOLEAN for true/false
  --   TIMESTAMPTZ for dates/times
  --   JSONB for flexible structured data
  --   UUID for references to other tables

  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Enable RLS (MANDATORY for every table)
ALTER TABLE public.[table_name] ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own rows
CREATE POLICY "[table_name]_select_own"
  ON public.[table_name]
  FOR SELECT
  USING (auth.uid() = user_id);

-- Policy: Users can only insert their own rows
CREATE POLICY "[table_name]_insert_own"
  ON public.[table_name]
  FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Policy: Users can only update their own rows
CREATE POLICY "[table_name]_update_own"
  ON public.[table_name]
  FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Policy: Users can only delete their own rows
CREATE POLICY "[table_name]_delete_own"
  ON public.[table_name]
  FOR DELETE
  USING (auth.uid() = user_id);

-- Auto-update updated_at timestamp
CREATE TRIGGER [table_name]_updated_at
  BEFORE UPDATE ON public.[table_name]
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- Index for fast user queries (MANDATORY for every table with user_id)
CREATE INDEX idx_[table_name]_user_id ON public.[table_name](user_id);
```

### Enum Template

If an entity has a status/type field with fixed options:

```sql
CREATE TYPE public.[enum_name] AS ENUM ('option1', 'option2', 'option3');
```

Then reference it in the table: `status public.[enum_name] NOT NULL DEFAULT 'option1'`

### Foreign Key Template (for related tables)

If Entity B belongs to Entity A:

```sql
-- In Entity B's table definition:
[entity_a]_id UUID REFERENCES public.[entity_a](id) ON DELETE CASCADE NOT NULL,

-- Additional index for the foreign key
CREATE INDEX idx_[table_b]_[table_a]_id ON public.[table_b]([table_a]_id);

-- RLS policy should also check that the parent belongs to the user:
CREATE POLICY "[table_b]_select_own"
  ON public.[table_b]
  FOR SELECT
  USING (
    auth.uid() = user_id
    OR auth.uid() = (SELECT user_id FROM public.[table_a] WHERE id = [table_a]_id)
  );
```

### What Supabase Gives You That Firestore Doesn't

| Feature | Firestore | Supabase |
|---------|-----------|----------|
| **Joins** | Impossible (denormalize everything) | `SELECT * FROM items JOIN categories ON ...` |
| **Aggregations** | Client-side counting | `SELECT COUNT(*), status FROM items GROUP BY status` |
| **Migrations** | None (schemaless) | SQL migrations, version controlled |
| **Type generation** | Manual TypeScript types | `npx supabase gen types typescript` auto-generates |
| **Cascading deletes** | Manual (delete each subcollection) | `ON DELETE CASCADE` — one line |
| **Full-text search** | Third-party (Algolia) | Built-in `to_tsvector` / `to_tsquery` |
| **Unique constraints** | Client-side validation only | `UNIQUE(user_id, slug)` — database enforced |

---

## SECTION 3: PRINT THE SQL

**IMPORTANT: Print ALL the SQL for me to copy and run in Supabase SQL Editor. Do NOT try to execute it yourself. You cannot connect to my Supabase instance.**

Generate the complete SQL based on the entities I defined in Section 1, following the templates in Section 2. Output it as one single SQL block I can paste.

---

## SECTION 4: UPDATE TYPESCRIPT TYPES

### Update src/types/supabase.ts

Add the new tables to the Database type. Follow the exact pattern that already exists for the `profiles` table:

```typescript
// For each new table, add:
[table_name]: {
  Row: {
    // all columns with their TypeScript types
    // UUID → string
    // TEXT → string
    // INTEGER → number
    // BOOLEAN → boolean
    // TIMESTAMPTZ → string
    // JSONB → Record<string, unknown> (or a specific interface)
    // ENUM → union type (e.g., 'draft' | 'published' | 'archived')
  }
  Insert: {
    // same as Row, but columns with defaults are optional (?)
    // id, created_at, updated_at are always optional
    // user_id is required
  }
  Update: {
    // all columns are optional (?)
  }
}
```

### Update src/types/index.ts

Add application-level interfaces for each entity:

```typescript
export interface [EntityName] {
  id: string
  user_id: string
  // ... all fields ...
  created_at: string
  updated_at: string
}
```

---

## SECTION 5: BUILD THE SERVICE LAYER

**src/services/database.ts:**

Build ALL database operations here. Components NEVER import from `@supabase/supabase-js` directly.

Follow this exact pattern for each entity:

```typescript
import { supabase } from '../config/supabase'
import type { [EntityName] } from '../types'

// ============================================
// [ENTITY_NAME] OPERATIONS
// ============================================

/** Get all [entities] for the current user, newest first */
export async function get[Entities](userId: string): Promise<[EntityName][]> {
  const { data, error } = await supabase
    .from('[table_name]')
    .select('*')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })

  if (error) throw new Error(`Failed to load [entities]: ${error.message}`)
  return data as [EntityName][]
}

/** Get a single [entity] by ID */
export async function get[Entity](id: string): Promise<[EntityName] | null> {
  const { data, error } = await supabase
    .from('[table_name]')
    .select('*')
    .eq('id', id)
    .single()

  if (error) {
    if (error.code === 'PGRST116') return null // Not found
    throw new Error(`Failed to load [entity]: ${error.message}`)
  }
  return data as [EntityName]
}

/** Create a new [entity] */
export async function create[Entity](
  userId: string,
  data: Omit<[EntityName], 'id' | 'user_id' | 'created_at' | 'updated_at'>
): Promise<[EntityName]> {
  const { data: created, error } = await supabase
    .from('[table_name]')
    .insert({ ...data, user_id: userId })
    .select()
    .single()

  if (error) throw new Error(`Failed to create [entity]: ${error.message}`)
  return created as [EntityName]
}

/** Update an existing [entity] */
export async function update[Entity](
  id: string,
  data: Partial<Omit<[EntityName], 'id' | 'user_id' | 'created_at' | 'updated_at'>>
): Promise<[EntityName]> {
  const { data: updated, error } = await supabase
    .from('[table_name]')
    .update(data)
    .eq('id', id)
    .select()
    .single()

  if (error) throw new Error(`Failed to update [entity]: ${error.message}`)
  return updated as [EntityName]
}

/** Delete an [entity] */
export async function delete[Entity](id: string): Promise<void> {
  const { error } = await supabase
    .from('[table_name]')
    .delete()
    .eq('id', id)

  if (error) throw new Error(`Failed to delete [entity]: ${error.message}`)
}

/** Search [entities] by title/name (client-side filter for simplicity) */
export async function search[Entities](
  userId: string,
  query: string
): Promise<[EntityName][]> {
  const { data, error } = await supabase
    .from('[table_name]')
    .select('*')
    .eq('user_id', userId)
    .ilike('title', `%${query}%`)
    .order('created_at', { ascending: false })

  if (error) throw new Error(`Failed to search [entities]: ${error.message}`)
  return data as [EntityName][]
}
```

### Realtime Subscriptions (optional — for live updates)

```typescript
/** Subscribe to changes on [entities] for a user */
export function subscribeTo[Entities](
  userId: string,
  callback: (payload: any) => void
) {
  return supabase
    .channel('[table_name]_changes')
    .on(
      'postgres_changes',
      {
        event: '*',
        schema: 'public',
        table: '[table_name]',
        filter: `user_id=eq.${userId}`,
      },
      callback
    )
    .subscribe()
}
```

### Error Handling Pattern

Every service function should throw human-readable errors. The calling component catches them and shows a toast:

```typescript
// In the component:
try {
  await createItem(user.id, formData)
  showToast({ type: 'success', message: 'Item created!' })
  navigate(`/items/${created.id}`)
} catch (err) {
  const message = err instanceof Error ? err.message : 'Something went wrong'
  showToast({ type: 'error', message })
}
```

---

## SECTION 6: DELETE ACCOUNT

Add the delete-account function to **src/services/database.ts**:

```typescript
// ============================================
// ACCOUNT DELETION
// ============================================

/**
 * Delete all user data and their profile.
 * Auth user deletion must be done via Supabase Dashboard or Edge Function.
 * CASCADE on the profiles table handles cleanup when auth.users row is deleted.
 *
 * For tables WITHOUT CASCADE from profiles, delete explicitly:
 */
export async function deleteAllUserData(userId: string): Promise<void> {
  // Delete from each table that has user_id
  // Order: children first, then parents
  const tables = [
    // '[child_table]',
    // '[parent_table]',
    // Add all your app's tables here
  ]

  for (const table of tables) {
    const { error } = await supabase
      .from(table)
      .delete()
      .eq('user_id', userId)

    if (error) {
      throw new Error(`Failed to delete data from ${table}: ${error.message}`)
    }
  }

  // Profile is deleted via CASCADE when auth user is deleted
  // The actual auth.users deletion requires a Supabase Edge Function or
  // manual deletion from the Dashboard.
  //
  // To enable self-service account deletion, deploy this Edge Function:
  // See: https://supabase.com/docs/guides/auth/managing-user-data#deleting-users
}
```

Then update **src/pages/Profile.tsx** to add the danger zone with a working delete flow. Use a ConfirmModal that requires typing "DELETE" (same pattern as the mentor's prompt — this is universally good UX).

---

## SECTION 7: VERIFY

1. Run the SQL in Supabase SQL Editor
2. Check Supabase Table Editor — your tables should appear
3. Check Authentication — the `profiles` trigger should still work
4. Run `npm run build` — zero TypeScript errors
5. Run `npm run dev` and:
   - Sign in
   - Check Supabase Table Editor — profile row should exist
   - Open browser DevTools Console — zero errors

---

## SECTION 8: COMMIT

```bash
git add -A
git commit -m "data: add [entity] tables, RLS policies, service layer, delete account"
```

---

## WHAT YOU NOW HAVE

| Layer | Status |
|-------|--------|
| Database tables with proper types | Done |
| Row Level Security on every table | Done |
| Auto-updating timestamps | Done |
| Cascading deletes | Done |
| Type-safe service layer | Done |
| CRUD operations for each entity | Done |
| Search by text field | Done |
| Realtime subscription pattern | Ready |
| Delete account flow | Done |
| Human-readable error messages | Done |

## KEY PATTERN: WHY SERVICES, NOT DIRECT CALLS

The mentor's prompt has this same rule for Firestore: **"NO Firestore calls in components."** Here's why this matters:

```
BAD (Firestore and Supabase both):
  Component → imports supabase → calls supabase.from('items').select(...)

GOOD:
  Component → imports getItems from services/database → calls getItems(userId)
```

Benefits:
1. **One place to change** if you rename a table or change a query
2. **Type safety** — the service function defines what goes in and comes out
3. **Error handling** — consistent error messages in one place
4. **Testability** — you can mock the service layer
5. **Readability** — `createItem(userId, data)` is clearer than raw Supabase calls

---

## WHAT'S NEXT

| Module | What It Adds |
|--------|-------------|
| **04 — UI Kit** | Modal, Toast, Button, Avatar, Skeleton, EmptyState components |
| **05 — CRUD Flow** | List → Detail → Create → Edit pages for your entities |

---

## --- END PROMPT ---
