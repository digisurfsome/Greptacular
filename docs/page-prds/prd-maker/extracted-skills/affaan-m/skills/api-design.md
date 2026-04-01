# API Design Patterns

**Name**: api-design
**Description**: REST API design patterns including resource naming, status codes, pagination, filtering, error responses, versioning, and rate limiting for production APIs.
**Origin**: ECC

## When to Activate

- Designing new API endpoints
- Reviewing existing API contracts
- Adding pagination, filtering, or sorting
- Implementing error handling for APIs
- Planning API versioning strategy
- Building public or partner-facing APIs

## Resource Design

### URL Structure Rules

Resources are nouns, plural, lowercase, kebab-case. Sub-resources indicate relationships. Actions that don't map to CRUD use verbs sparingly.

**Correct patterns:**
- `GET /api/v1/users`
- `GET /api/v1/users/:id`
- `POST /api/v1/users`
- `PUT /api/v1/users/:id`
- `PATCH /api/v1/users/:id`
- `DELETE /api/v1/users/:id`
- `GET /api/v1/users/:id/orders`
- `POST /api/v1/orders/:id/cancel`

### Naming Rules

**GOOD:**
- `/api/v1/team-members` (kebab-case for multi-word)
- `/api/v1/orders?status=active` (query params for filtering)
- `/api/v1/users/123/orders` (nested for ownership)

**BAD:**
- `/api/v1/getUsers` (verb in URL)
- `/api/v1/user` (singular instead of plural)
- `/api/v1/team_members` (snake_case in URLs)
- `/api/v1/users/123/getOrders` (verb in nested)

## HTTP Methods and Semantics

| Method | Idempotent | Safe | Purpose |
|--------|-----------|------|---------|
| GET | Yes | Yes | Retrieve resources |
| POST | No | No | Create resources, trigger actions |
| PUT | Yes | No | Full replacement of resource |
| PATCH | No* | No | Partial update of resource |
| DELETE | Yes | No | Remove a resource |

*PATCH can be made idempotent with proper implementation

## Status Codes Reference

### Success
- `200 OK` — GET, PUT, PATCH (with response body)
- `201 Created` — POST (include Location header)
- `204 No Content` — DELETE, PUT (no response body)

### Client Errors
- `400 Bad Request` — Validation failure, malformed JSON
- `401 Unauthorized` — Missing or invalid authentication
- `403 Forbidden` — Authenticated but not authorized
- `404 Not Found` — Resource doesn't exist
- `409 Conflict` — Duplicate entry, state conflict
- `422 Unprocessable Entity` — Semantically invalid (valid JSON, bad data)
- `429 Too Many Requests` — Rate limit exceeded

### Server Errors
- `500 Internal Server Error` — Unexpected failure (don't expose details)
- `502 Bad Gateway` — Upstream service failed
- `503 Service Unavailable` — Temporary overload, include Retry-After

### Common Mistakes

**Incorrect:** `{ "status": 200, "success": false, "error": "Not found" }`
**Correct:** HTTP 404 with `{ "error": { "code": "not_found", "message": "User not found" } }`

**Incorrect:** 500 for validation errors
**Correct:** 400 or 422 with field-level details

**Incorrect:** 200 for created resources
**Correct:** 201 with Location header

## Response Format

### Success Response

```json
{
  "data": {
    "id": "abc-123",
    "email": "alice@example.com",
    "name": "Alice",
    "created_at": "2025-01-15T10:30:00Z"
  }
}
```

### Collection Response with Pagination

```json
{
  "data": [
    { "id": "abc-123", "name": "Alice" },
    { "id": "def-456", "name": "Bob" }
  ],
  "meta": {
    "total": 142,
    "page": 1,
    "per_page": 20,
    "total_pages": 8
  },
  "links": {
    "self": "/api/v1/users?page=1&per_page=20",
    "next": "/api/v1/users?page=2&per_page=20",
    "last": "/api/v1/users?page=8&per_page=20"
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": [
      {
        "field": "email",
        "message": "Must be a valid email address",
        "code": "invalid_format"
      },
      {
        "field": "age",
        "message": "Must be between 0 and 150",
        "code": "out_of_range"
      }
    ]
  }
}
```

### Response Envelope Options

**Option A: Envelope with data wrapper (recommended for public APIs)**

```typescript
interface ApiResponse<T> {
  data: T;
  meta?: PaginationMeta;
  links?: PaginationLinks;
}

interface ApiError {
  error: {
    code: string;
    message: string;
    details?: FieldError[];
  };
}
```

**Option B: Flat response (simpler, for internal APIs)**
- Return resource directly on success
- Return error object on failure
- Distinguish by HTTP status code

## Pagination Strategies

### Offset-Based Pagination

```
GET /api/v1/users?page=2&per_page=20

SELECT * FROM users
ORDER BY created_at DESC
LIMIT 20 OFFSET 20;
```

**Advantages:** Easy to implement, supports jumping to page N
**Disadvantages:** Slow on large offsets, inconsistent with concurrent inserts

### Cursor-Based Pagination

```
GET /api/v1/users?cursor=eyJpZCI6MTIzfQ&limit=20

SELECT * FROM users
WHERE id > :cursor_id
ORDER BY id ASC
LIMIT 21;  -- fetch one extra to determine has_next
```

Response:
```json
{
  "data": [],
  "meta": {
    "has_next": true,
    "next_cursor": "eyJpZCI6MTQzfQ"
  }
}
```

**Advantages:** Consistent performance, stable with concurrent inserts
**Disadvantages:** Cannot jump to arbitrary page, cursor is opaque

### Pagination Type Selection

| Use Case | Type |
|----------|------|
| Admin dashboards, small datasets (<10K) | Offset |
| Infinite scroll, feeds, large datasets | Cursor |
| Public APIs | Cursor (default) with offset (optional) |
| Search results | Offset (users expect page numbers) |

## Filtering, Sorting, and Search

### Filtering

- Simple equality: `GET /api/v1/orders?status=active&customer_id=abc-123`
- Comparison operators: `GET /api/v1/products?price[gte]=10&price[lte]=100`
- Multiple values: `GET /api/v1/products?category=electronics,clothing`
- Nested fields: `GET /api/v1/orders?customer.country=US`

### Sorting

- Single field: `GET /api/v1/products?sort=-created_at`
- Multiple fields: `GET /api/v1/products?sort=-featured,price,-created_at`

### Full-Text Search

- Search query: `GET /api/v1/products?q=wireless+headphones`
- Field-specific: `GET /api/v1/users?email=alice`

### Sparse Fieldsets

```
GET /api/v1/users?fields=id,name,email
GET /api/v1/orders?fields=id,total,status&include=customer.name
```

## Authentication and Authorization

### Token-Based Authentication

Bearer token: `Authorization: Bearer eyJhbGciOiJIUzI1NiIs...`
API key (server-to-server): `X-API-Key: sk_live_abc123`

### Authorization Patterns

**Resource-level:** Check ownership before returning data (403 if not owner).
**Role-based:** `requireRole("admin")` middleware wrapper.

## Rate Limiting

### Headers

```
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

When exceeded:
```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

### Rate Limit Tiers

| Tier | Limit | Window | Use Case |
|------|-------|--------|----------|
| Anonymous | 30/min | Per IP | Public endpoints |
| Authenticated | 100/min | Per user | Standard API access |
| Premium | 1000/min | Per API key | Paid API plans |
| Internal | 10000/min | Per service | Service-to-service |

## Versioning Strategies

### URL Path Versioning (Recommended)

```
/api/v1/users
/api/v2/users
```

### Header Versioning

```
GET /api/users
Accept: application/vnd.myapp.v2+json
```

### Versioning Rules

1. Start with `/api/v1/` — don't version until necessary
2. Maintain at most 2 active versions (current + previous)

**Deprecation timeline:**
- Announce deprecation (6 months notice for public APIs)
- Add Sunset header: `Sunset: Sat, 01 Jan 2026 00:00:00 GMT`
- Return `410 Gone` after sunset date

**Non-breaking changes (no new version):** Adding fields, optional params, new endpoints.
**Breaking changes (require new version):** Removing/renaming fields, changing types, changing URLs, changing auth.

## Implementation Examples

### TypeScript (Next.js API Route)

```typescript
import { z } from "zod";
import { NextRequest, NextResponse } from "next/server";

const createUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
});

export async function POST(req: NextRequest) {
  const body = await req.json();
  const parsed = createUserSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json({
      error: {
        code: "validation_error",
        message: "Request validation failed",
        details: parsed.error.issues.map(i => ({
          field: i.path.join("."),
          message: i.message,
          code: i.code,
        })),
      },
    }, { status: 422 });
  }

  const user = await createUser(parsed.data);

  return NextResponse.json(
    { data: user },
    {
      status: 201,
      headers: { Location: `/api/v1/users/${user.id}` },
    },
  );
}
```

### Python (Django REST Framework)

```python
from rest_framework import serializers, viewsets, status
from rest_framework.response import Response

class CreateUserSerializer(serializers.Serializer):
    email = serializers.EmailField()
    name = serializers.CharField(max_length=100)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "name", "created_at"]

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateUserSerializer
        return UserSerializer

    def create(self, request):
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.create(**serializer.validated_data)
        return Response(
            {"data": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
            headers={"Location": f"/api/v1/users/{user.id}"},
        )
```

### Go (net/http)

```go
func (h *UserHandler) CreateUser(w http.ResponseWriter, r *http.Request) {
    var req CreateUserRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        writeError(w, http.StatusBadRequest, "invalid_json", "Invalid request body")
        return
    }

    if err := req.Validate(); err != nil {
        writeError(w, http.StatusUnprocessableEntity, "validation_error", err.Error())
        return
    }

    user, err := h.service.Create(r.Context(), req)
    if err != nil {
        switch {
        case errors.Is(err, domain.ErrEmailTaken):
            writeError(w, http.StatusConflict, "email_taken", "Email already registered")
        default:
            writeError(w, http.StatusInternalServerError, "internal_error", "Internal error")
        }
        return
    }

    w.Header().Set("Location", fmt.Sprintf("/api/v1/users/%s", user.ID))
    writeJSON(w, http.StatusCreated, map[string]any{"data": user})
}
```

## API Design Checklist

Before shipping a new endpoint:

- [ ] Resource URL follows naming conventions (plural, kebab-case, no verbs)
- [ ] Correct HTTP method used (GET for reads, POST for creates, etc.)
- [ ] Appropriate status codes returned (not 200 for everything)
- [ ] Input validated with schema (Zod, Pydantic, Bean Validation)
- [ ] Error responses follow standard format with codes and messages
- [ ] Pagination implemented for list endpoints (cursor or offset)
- [ ] Authentication required (or explicitly marked as public)
- [ ] Authorization checked (users access only their own resources)
- [ ] Rate limiting configured
- [ ] Response does not leak internal details (stack traces, SQL errors)
- [ ] Consistent naming with existing endpoints (camelCase vs snake_case)
- [ ] Documented (OpenAPI/Swagger spec updated)
