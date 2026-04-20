# Correctness Review — YT Strategy Lab v2

Reviewer: build-review-correctness
Scope: Logic errors, type safety, security issues

## Findings

- **[CRITICAL]** Missing null check in `getUserById` — if user not found returns undefined, callers destructure without guard (server/routers/users.ts:47)
- **[CRITICAL]** Race condition in async queue processor — two concurrent requests can both read `queue.length === 0` and both attempt to process the same item (server/services/queue.ts:112)
- **[HIGH]** Error handler in `createSession` swallows exceptions without logging — silent failures impossible to diagnose (server/routers/auth.ts:89)
- **[HIGH]** Type assertion `as User` without runtime validation at line 234 — malformed API response causes downstream crash (server/services/user-service.ts:234)
- **[HIGH]** Missing boundary check in pagination logic — negative `offset` values cause DB query error (server/routers/videos.ts:78)
- **[HIGH]** API response not validated before destructuring in `fetchChannelData` — external API shape changes crash the server (server/services/youtube.ts:156)
- **[HIGH]** Missing CSRF protection on all state-modifying endpoints — POST/PUT/DELETE exposed (server/main.ts:23)
- **[HIGH]** Database query not parameterized in search handler — SQL injection vector (server/routers/search.ts:34)
- **[HIGH]** Missing rate limiting on auth endpoints — brute-force risk (server/routers/auth.ts:12)
- **[HIGH]** Session token not invalidated on logout — token reuse after logout (server/services/session.ts:67)
- **[HIGH]** Missing input sanitization in `saveTranscript` handler — XSS risk if content is rendered (server/routers/transcripts.ts:91)
- **[HIGH]** Error messages in auth responses leak internal file paths (server/routers/auth.ts:103)
- **[HIGH]** No timeout configured on external YouTube API calls — hangs indefinitely if API is slow (server/services/youtube.ts:23)
