# Quality Gate Command

> Source: https://github.com/affaan-m/everything-claude-code/blob/main/commands/quality-gate.md

## Overview

An on-demand quality pipeline that mirrors hook behavior but is operator-invoked. Provides file or project scope assessment.

## Usage

```
/quality-gate [path|.] [--fix] [--strict]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `[path\|.]` | Optional target path (defaults to current directory) |
| `--fix` | Allow auto-format/fix where configured |
| `--strict` | Fail on warnings where supported |

## Pipeline Phases

1. **Detect** - Detect language/tooling for target
2. **Format** - Run formatter checks
3. **Lint/Type** - Run lint/type checks when available
4. **Remediate** - Produce a concise remediation list

## Notes

This command mirrors hook behavior but is operator-invoked, providing on-demand execution of the quality pipeline for file or project scope assessment.
