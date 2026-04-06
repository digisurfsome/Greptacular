# Security Model

Defense-in-depth approach configured in `client.py`:
1. OS-level sandbox for bash commands
2. Filesystem restricted to project directory only
3. Bash commands validated using hierarchical allowlist

## Extra Read Paths

Agent can read outside project folder via `EXTRA_READ_PATHS` env var:
```bash
EXTRA_READ_PATHS=/Users/me/docs,/opt/shared-libs
```

Validation: absolute paths only, must exist, canonicalized (no `..` traversal), sensitive dirs blocked, read-only (Read/Glob/Grep only).

**Blocked directories:** `.ssh`, `.aws`, `.azure`, `.kube`, `.gnupg`, `.gpg`, `.password-store`, `.docker`, `.config/gcloud`, `.npmrc`, `.pypirc`, `.netrc`

## Per-Project Allowed Commands

**Hierarchy (highest to lowest priority):**
1. Hardcoded Blocklist (`security.py`) — NEVER allowed
2. Org Blocklist (`~/.autoforge/config.yaml`) — Cannot be overridden
3. Org Allowlist (`~/.autoforge/config.yaml`) — Available to all projects
4. Global Allowlist (`security.py`) — Default commands
5. Project Allowlist (`.autoforge/allowed_commands.yaml`) — Project-specific

**Project config** (`.autoforge/allowed_commands.yaml`):
```yaml
version: 1
commands:
  - name: swift
    description: Swift compiler
  - name: swift*
    description: All Swift tools (wildcard)
  - name: ./scripts/build.sh
    description: Project build script
```

**Org config** (`~/.autoforge/config.yaml`):
```yaml
version: 1
allowed_commands:
  - name: jq
    description: JSON processor
blocked_commands:
  - aws
  - kubectl
```

**Limits:** Max 100 commands per project. Blocklisted commands can NEVER be allowed.

**Files:** `security.py`, `test_security.py`, `test_security_integration.py`, `examples/project_allowed_commands.yaml`, `examples/org_config.yaml`
