# Failures Review — Team Task Manager

Reviewer: build-review-failures
Scope: Silent failures, unhandled errors, error propagation gaps

## Findings

- **[CRITICAL]** Unhandled promise rejection in task creation route — crashes worker on DB constraint violation (server/routers/tasks.ts:56)
- **[CRITICAL]** Background reminder job silently fails when email service is down — no fallback, no alert (server/jobs/reminders.ts:23)
- **[HIGH]** Missing error boundary on `TaskList` component — bad task data crashes the whole page (ui/src/components/tasks/TaskList.tsx:8)
- **[HIGH]** No retry on email send failure — transient SMTP error drops the email permanently (server/services/email.ts:45)
- **[HIGH]** Failed task status update not reported back to client — UI shows optimistic update but DB write failed (server/services/task-service.ts:112)
- **[HIGH]** No `/health` endpoint for load balancer checks (server/main.ts)
