# Backend Development Patterns

**Name**: backend-patterns
**Description**: Backend architecture patterns, API design, database optimization, and server-side best practices for Node.js, Express, and Next.js API routes.
**Origin**: ECC

## When to Activate

- Designing REST or GraphQL API endpoints
- Implementing repository, service, or controller layers
- Optimizing database queries (N+1, indexing, connection pooling)
- Adding caching (Redis, in-memory, HTTP cache headers)
- Setting up background jobs or async processing
- Structuring error handling and validation for APIs
- Building middleware (auth, logging, rate limiting)

## API Design Patterns

### RESTful API Structure

Resource-based URLs:
- `GET /api/markets` — List resources
- `GET /api/markets/:id` — Get single resource
- `POST /api/markets` — Create resource
- `PUT /api/markets/:id` — Replace resource
- `PATCH /api/markets/:id` — Update resource
- `DELETE /api/markets/:id` — Delete resource

Query parameters: `GET /api/markets?status=active&sort=volume&limit=20&offset=0`

### Repository Pattern

Abstract data access logic:

```typescript
interface MarketRepository {
  findAll(filters?: MarketFilters): Promise<Market[]>
  findById(id: string): Promise<Market | null>
  create(data: CreateMarketDto): Promise<Market>
  update(id: string, data: UpdateMarketDto): Promise<Market>
  delete(id: string): Promise<void>
}
```

Implementation features:
- Conditional query building
- Error handling
- Filter application (status, limit)

### Service Layer Pattern

Separate business logic from data access:
- Dependency injection of repository
- Vector search integration
- Result sorting by similarity
- Embedding generation

### Middleware Pattern

Request/response processing pipeline. Example `withAuth` middleware:
- Token extraction from Authorization header
- Token verification
- User attachment to request object
- Error responses for missing/invalid tokens

## Database Patterns

### Query Optimization

Good practice — select only needed columns:

```typescript
const { data } = await supabase
  .from('markets')
  .select('id, name, status, volume')
  .eq('status', 'active')
  .order('volume', { ascending: false })
  .limit(10)
```

Anti-pattern: Selecting all columns with wildcard.

### N+1 Query Prevention

**Problem**: Looping through results and querying individually.
**Solution**: Batch fetching with client-side mapping using Map data structure.

### Transaction Pattern

Using Supabase RPC for multi-step operations:
- SQL function wrapper (`create_market_with_position`)
- Automatic rollback on error
- EXCEPTION handling in PL/pgSQL

## Caching Strategies

### Redis Caching Layer

`CachedMarketRepository` implementing:
- Cache-checking before database queries
- TTL-based expiration (5 minutes / 300 seconds)
- Cache invalidation method

### Cache-Aside Pattern

Flow:
1. Check cache
2. Return if hit
3. Fetch from database on miss
4. Populate cache with TTL
5. Return data

## Error Handling Patterns

### Centralized Error Handler

Custom `ApiError` class with:
- Status code property
- Message property
- Operational flag

Handler function processing:
- ApiError instances
- Zod validation errors
- Unexpected errors with logging

### Retry with Exponential Backoff

`fetchWithRetry` function featuring:
- Configurable max retries (default: 3)
- Exponential delay calculation (1s, 2s, 4s)
- Error tracking and rethrow

## Authentication & Authorization

### JWT Token Validation

Process:
- Token extraction from Bearer Authorization header
- JWT verification using secret
- Payload typing with userId, email, role
- ApiError throwing for invalid tokens

### Role-Based Access Control

Permission system:
- Permission type union: `'read' | 'write' | 'delete' | 'admin'`
- Role-to-permission mapping:
  - admin: all permissions
  - moderator: read, write, delete
  - user: read, write
- `hasPermission` check function
- `requirePermission` higher-order function wrapper

## Rate Limiting

### Simple In-Memory Rate Limiter

`RateLimiter` class with:
- Map-based request tracking per identifier
- Time-window filtering
- Threshold comparison logic

Parameters: identifier (IP), maxRequests (e.g., 100), windowMs (e.g., 60000 for 1 minute)

Response: HTTP 429 on limit exceeded.

## Background Jobs & Queues

### Simple Queue Pattern

`JobQueue<T>` class implementing:
- Generic job typing
- Queue array management
- Processing state flag
- Serial job execution
- Error catching without halting queue

Example use case: Market indexing with `IndexJob` interface.

## Logging & Monitoring

### Structured Logging

Logger class methods:
- `log(level, message, context)` — core method
- `info()`, `warn()`, `error()` — convenience methods

Log entry structure:
- timestamp (ISO format)
- level (info/warn/error)
- message
- custom context properties
- error-specific fields (message, stack)

Usage: Request IDs, method, path tracking in API routes.

## Key Takeaway

"Backend patterns enable scalable, maintainable server-side applications. Choose patterns that fit your complexity level."
