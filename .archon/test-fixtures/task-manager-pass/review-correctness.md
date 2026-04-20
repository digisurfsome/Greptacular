# Correctness Review — Team Task Manager

Reviewer: build-review-correctness
Scope: Logic errors, type safety, security issues

## Findings

- **[CRITICAL]** Missing null check in `getTaskById` before returning to caller (server/routers/tasks.ts:34)
- **[CRITICAL]** JWT secret falls back to empty string if env var unset — tokens always valid (server/auth.ts:12)
- **[HIGH]** Pagination offset can be negative — causes SQLite error (server/routers/tasks.ts:89)
- **[HIGH]** Task assignment allows assigning to user from different workspace — missing scope check (server/services/task-service.ts:67)
- **[HIGH]** Missing CSRF token validation on task mutation endpoints (server/main.ts:45)
