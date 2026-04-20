# Simplify Review — Team Task Manager

Reviewer: build-review-simplify
Scope: Duplication, unnecessary complexity

## Findings

- **[HIGH]** Task validation logic duplicated in router and service layer — extract to shared Zod schema (server/routers/tasks.ts, server/services/task-service.ts)
