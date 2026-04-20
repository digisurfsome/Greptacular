# Simplify Review — YT Strategy Lab v2

Reviewer: build-review-simplify
Scope: Duplication, unnecessary complexity, refactoring opportunities

## Findings

- **[HIGH]** `getUserById` and `getUserByEmail` share 90% logic — extract a common `queryUser(where)` builder (server/services/user-service.ts:12,67)
- **[HIGH]** Error handling pattern copy-pasted into 8 separate route handlers — extract to `asyncHandler` middleware (server/routers/)
- **[HIGH]** Date formatting logic duplicated across 6 different files — extract to `ui/src/lib/format.ts` (ui/src/components/)
- **[HIGH]** Three separate auth-check implementations in different middleware layers — consolidate to one `requireAuth` function (server/middleware/)
- **[HIGH]** Pagination logic duplicated in `getVideos`, `getChannels`, `getAnalyses`, `getTranscripts`, `getJobs` — extract `paginatedQuery` helper (server/services/)
- **[HIGH]** Four different retry implementations across youtube.ts, openai.ts, cache.ts, webhooks.ts — standardize to one `withRetry` utility (server/lib/)
- **[HIGH]** Config access (`process.env.X`) scattered across 14 files — centralize to `server/config.ts` (server/)
- **[HIGH]** Input validation logic duplicated between `server/routers/` and `ui/src/lib/` — extract shared Zod schemas (shared/)
- **[HIGH]** Logger setup repeated in 7 separate modules — export a single configured logger instance (server/lib/logger.ts)
- **[HIGH]** Environment variable access in `server/`, `server/jobs/`, `server/services/` all separately loading dotenv (server/)
- **[HIGH]** Two separate in-memory cache implementations for user data and channel data — unify (server/services/)
- **[HIGH]** Permission check logic duplicated across 9 controller functions — extract `requireRole(role)` middleware (server/middleware/)
- **[HIGH]** Three different approaches to async error handling in streaming vs. REST vs. WebSocket handlers (server/services/)
