---
description: "Compound Engineering — Security Review: Focused security audit of codebase changes"
argument-hint: <optional: specific files or directories to focus on>
---

# Compound Engineering: Security Review

**Artifacts Directory**: $ARTIFACTS_DIR
**User Input**: $ARGUMENTS

## Context Loading

Read these files before reviewing:
- `$ARTIFACTS_DIR/context-packet/context-packet.json` — to understand what was built and the tech stack
- `$ARTIFACTS_DIR/ce-plan.md` — to understand what was implemented

---

## Purpose

Perform a focused security audit of the code produced during the work phase. You are a security specialist — you check ONLY for security issues. Do not comment on code style, performance, or architecture unless it directly creates a security vulnerability.

---

## Scope

Review ALL code that was created or modified during the work phase. To find what changed:

1. Check `git diff` if in a git repository (compare against the branch point or last known-good commit)
2. If no git history, read the files listed in the plan's task "Files" entries
3. If `$ARGUMENTS` specifies files, focus on those

---

## Security Checklist

Check EVERY item below. For each finding, rate it HIGH / MEDIUM / LOW.

### Authentication & Authorization

- [ ] **Auth bypass**: Can any endpoint be accessed without proper authentication?
- [ ] **Privilege escalation**: Can a regular user access admin-only functionality?
- [ ] **Token handling**: Are tokens stored securely? Are they validated on every request?
- [ ] **Session management**: Are sessions invalidated on logout? Do they expire?
- [ ] **Password handling**: Are passwords hashed with bcrypt/argon2 (not MD5/SHA1)? Is there a minimum length?

### Input Validation

- [ ] **SQL injection**: Are database queries parameterized? Any string concatenation in queries?
- [ ] **XSS (Cross-Site Scripting)**: Is user input sanitized before rendering in HTML? Are React's JSX escaping rules followed?
- [ ] **Command injection**: Is user input ever passed to shell commands? If so, is it properly escaped?
- [ ] **Path traversal**: Can user input manipulate file paths (e.g., `../../etc/passwd`)?
- [ ] **SSRF**: Can user input cause the server to make requests to arbitrary URLs?

### Secrets & Configuration

- [ ] **Hardcoded secrets**: Any API keys, passwords, tokens, or connection strings in source code?
- [ ] **Env file exposure**: Is `.env` in `.gitignore`? Are secrets loaded from environment, not code?
- [ ] **Debug mode**: Is debug mode disabled in production config? Are stack traces hidden?
- [ ] **CORS configuration**: Is CORS configured restrictively, not `*`?

### Data Handling

- [ ] **Sensitive data in logs**: Are passwords, tokens, or PII being logged?
- [ ] **Data validation**: Are all API inputs validated for type, length, and format?
- [ ] **Error messages**: Do error responses leak internal details (stack traces, SQL queries, file paths)?
- [ ] **File uploads**: If present, are file types and sizes validated? Are uploads stored safely?

### Dependencies

- [ ] **Known vulnerabilities**: Run `npm audit` or equivalent if available. Flag any HIGH/CRITICAL CVEs.
- [ ] **Outdated packages**: Are there critically outdated dependencies with known security patches?

---

## Output Format

Write findings to `$ARTIFACTS_DIR/review-security.md`:

```markdown
# Security Review

**Reviewed**: [ISO 8601 timestamp]
**Files reviewed**: [count]
**Findings**: [count by severity]

## HIGH Priority

### [Finding Title]
- **File**: [path:line]
- **Issue**: [specific description of the vulnerability]
- **Risk**: [what an attacker could do]
- **Fix**: [specific code change or approach to fix it]

## MEDIUM Priority

### [Finding Title]
- **File**: [path:line]
- **Issue**: [description]
- **Risk**: [potential impact]
- **Fix**: [recommended fix]

## LOW Priority

### [Finding Title]
- **File**: [path:line]
- **Issue**: [description]
- **Fix**: [recommended fix]

## Clean Areas
[List security areas that were checked and found to be properly handled.
This is important — it tells the synthesis stage what does NOT need attention.]
```

**Rules for findings**:
- Be specific. "Input not validated" is too vague. "POST /api/users accepts name field with no length limit — could cause DB overflow" is specific.
- Always include the exact file and line number.
- Always include a concrete fix recommendation, not just "fix this."
- If you find zero issues in a category, say so explicitly in "Clean Areas."
- Do NOT report code style issues, performance issues, or architectural concerns. Those are other reviewers' jobs.

---

## Signal Completion

After writing the review file, emit:
<promise>SECURITY_REVIEW_COMPLETE</promise>

If you could not access the codebase or find any changed files, write a review file noting this and still emit the promise.
