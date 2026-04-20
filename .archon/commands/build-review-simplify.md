# Review: Code Simplifier

One of 4 parallel review agents. Your job: find opportunities to simplify while preserving exact functionality.

## Input
Read `$ARTIFACTS_DIR/implementation-report.md` for what was built.
Use Glob to find all source files. Read the actual code.

## Focus Areas
1. **Dead code**: Unused imports, unreachable branches, commented-out code
2. **Duplication**: Copy-pasted logic that should be extracted
3. **Over-engineering**: Abstractions with only one implementation, unnecessary indirection
4. **Simplification**: Complex conditionals that could be simplified, nested callbacks that could be flattened
5. **Naming**: Unclear variable/function names that hurt readability
6. **File organization**: Files that are too large, responsibilities that should be split

## Rules
- ONLY suggest changes that preserve EXACT functionality
- Never suggest changing WALLs — they're deterministic for a reason
- DOORs can be simplified within their constraints
- ROOMs have the most simplification opportunity

## Evidence Standard
Every finding MUST have file:line, the current code, and the simplified version.

## Output
Write findings to `$ARTIFACTS_DIR/review-simplify.md`:
- Simplification opportunities (with before/after code)
- Dead code to remove
- Duplication to extract
