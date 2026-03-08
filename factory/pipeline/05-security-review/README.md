# Stage 05: Security Review

## What Happens Here

Harden the app. Find vulnerabilities, fix them, make sure secrets aren't exposed.

**Input:** Working codebase from Stage 04.

**Output:** Security-hardened codebase with no known vulnerabilities.

## What Gets Mounted Here

- Security checklists for the chosen tech stack
- Common vulnerability patterns to check for
- Auth/authz implementation guides
- Secret management best practices
- Input validation patterns

## The Prompts

Prompts in this stage guide the AI to:
1. Check for hardcoded secrets or API keys
2. Validate all user inputs
3. Review authentication and authorization flows
4. Check for XSS, CSRF, and injection vulnerabilities
5. Ensure proper error handling (no stack traces leaked)
6. Review dependency security (known CVEs)

## When Is This Stage Done?

When a security checklist has been run and all identified issues are fixed. No hardcoded secrets, all inputs validated, auth flows solid.
