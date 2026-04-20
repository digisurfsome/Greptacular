# Test Coverage Review — YT Strategy Lab v2

Reviewer: build-review-tests
Scope: Missing tests for WALL steps, untested critical paths

## Findings

- **[HIGH]** No tests for the authentication flow (login, logout, token refresh) — zero test files for auth (server/routers/auth.ts)
- **[HIGH]** No tests for the YouTube channel fetch service — external API integration untested (server/services/youtube.ts)
- **[HIGH]** No tests for transcript processing logic — most complex WALL step has no coverage (server/services/transcript.ts)
- **[HIGH]** Missing integration tests for all API endpoints — no test file for any router (server/routers/)
- **[HIGH]** No tests for error boundary behavior in UI components (ui/src/components/yt-lab/)
- **[HIGH]** Missing tests for WebSocket reconnection logic (server/services/ws-handler.ts)
- **[HIGH]** No tests for the queue overflow handling (server/services/job-runner.ts)
- **[HIGH]** No tests for the concurrent request scenario in queue processor (server/services/queue.ts)
- **[HIGH]** Missing snapshot tests for `StrategyDashboard`, `TranscriptViewer`, `AnalysisCard` (ui/src/components/yt-lab/)
- **[HIGH]** No tests for the scheduled job logic (server/jobs/)
- **[HIGH]** Missing contract tests for external API integrations — shape changes will silently break (server/services/)
- **[HIGH]** No tests for session expiry and token invalidation flows (server/services/session.ts)
