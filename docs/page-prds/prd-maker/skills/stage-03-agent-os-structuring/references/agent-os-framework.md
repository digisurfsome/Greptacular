# Agent OS Framework — Five Lenses

> Origin: 15-year software veteran's framework that cut build time from 1.5 days to 0.5 days with fewer bugs.
> Function: Guardrailing system that adds walls and doors to keep agents centered on concept and context.

## The Five Lenses

Every raw idea is processed through five questions. Together they produce the four output sections.

### Lens 1: What Is the Product?

- **Name it.** Use whatever the user called it, or derive from the core concept.
- **Define it in one sentence.** A stranger reads this sentence and knows what it does.
- **Describe its identity.** 1-2 paragraphs covering what it is, how it presents itself, what makes it distinctive.

→ Maps to: `concept_and_context.product_name`, `one_line_description`, `product_identity`

### Lens 2: What Is It Solving?

- **Identify the pain.** What frustration, inefficiency, or gap does the user experience?
- **State it from the user's perspective.** Not "the system will..." but "users currently struggle with..."
- **Be specific.** Not "it helps people" but "freelance designers waste 3 hours per week manually tracking invoices."

→ Maps to: `problem_statement`

### Lens 3: Market Feasibility

- **Is this viable?** Does the market exist? Are people paying for solutions in this space?
- **What exists already?** Name competitors. Be specific.
- **What are the risks?** Technical, market, adoption risks with severity levels.
- **How does this product differ?** What's the actual differentiator — not aspirational, but real.

→ Maps to: `feasibility_assessment`, `target_user_and_market.competitive_landscape`

### Lens 4: Who Is It For?

- **Define specific personas.** Not "users" — specific types of people.
- **What are their pain points?** Real frustrations they experience.
- **What are their goals?** What they want to achieve (related to the product domain).
- **What is the market context?** Landscape, timing, trends.

→ Maps to: `target_user_and_market.personas`, `market_context`

### Lens 5: What Exists Already?

- **Name competitors.** Real products, not categories.
- **State differentiators.** For each competitor, how does THIS product differ?
- **Identify the gap.** What's the underserved niche?

→ Maps to: `target_user_and_market.competitive_landscape`

## Lens-to-Section Mapping

| Lens | Output Section |
|------|---------------|
| 1 (What is it?) | `concept_and_context` |
| 2 (What's it solving?) | `problem_statement` |
| 3 (Feasibility) | `feasibility_assessment` + `competitive_landscape` |
| 4 (Who's it for?) | `target_user_and_market` |
| 5 (What exists?) | `competitive_landscape` (overlaps with Lens 3) |

## Critical Boundaries

- **No "how":** The five lenses produce "what" and "why" only. Architecture, databases, APIs, implementation details are deferred.
- **No mechanism extraction:** Features may be mentioned in context but not decomposed into discrete units.
- **No invention:** The lenses organize what the user said. They do not add features, assumptions, or embellishments.
- **Persistent output:** The structured document serves as a drift anchor — agents reference it throughout the entire build.
