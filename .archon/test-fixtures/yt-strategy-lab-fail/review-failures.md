# Failures Review — YT Strategy Lab v2

Reviewer: build-review-failures
Scope: Silent failures, unhandled errors, error propagation gaps

## Findings

- **[CRITICAL]** Silent failure in file upload handler — returns HTTP 200 on disk-full error, data loss (server/routers/uploads.ts:67)
- **[CRITICAL]** Unhandled promise rejection in WebSocket message handler crashes the worker process (server/services/ws-handler.ts:45)
- **[CRITICAL]** Background job silently drops items on queue overflow — no dead-letter queue, no alert (server/services/job-runner.ts:198)
- **[HIGH]** Missing error boundary around `YouTubeEmbed` component — third-party widget crash takes down the whole page (ui/src/components/yt-lab/YouTubeEmbed.tsx:12)
- **[HIGH]** No retry logic on transient network failures in `fetchChannelData` — single 503 fails the entire request (server/services/youtube.ts:78)
- **[HIGH]** Cache invalidation failure not surfaced to caller — stale data served silently (server/services/cache.ts:134)
- **[HIGH]** No fallback when YouTube API quota is exhausted — UI shows blank screen with no explanation (server/services/youtube.ts:201)
- **[HIGH]** Uncaught exception in stream processor closes SSE connection silently — client left hanging (server/services/stream.ts:89)
- **[HIGH]** Failed writes to `analysis_results` table not retried — data silently lost (server/services/analysis.ts:67)
- **[HIGH]** No `/health` endpoint — load balancer cannot detect unhealthy instance (server/main.ts:end)
- **[HIGH]** Error in scheduled transcript-fetch job not reported to any monitoring channel (server/jobs/transcript-fetch.ts:34)
- **[HIGH]** Webhook handler for payment events has no idempotency check — duplicate events double-process (server/routers/webhooks.ts:23)
- **[HIGH]** No circuit breaker on OpenAI API calls — cascading failure when OpenAI is down (server/services/openai.ts:12)
