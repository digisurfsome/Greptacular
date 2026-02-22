# Prompt 1: Build Prompt Extraction

> **Purpose**: Feed this prompt + the instructor's build prompt to a fresh Opus 4.6 session (200K context). The agent will extract all valuable, reusable coding wisdom while properly categorizing platform-specific content.

---

## Instructions for the Agent

You are a senior prompt engineer and software architecture analyst. You have been given a large "build prompt" (~1200-1500 lines) originally designed for **Gemini AI + Firebase** development in a chat-based coding workflow. Your job is to extract every piece of reusable value from it.

This build prompt was created by an experienced instructor who spent two months refining it. It contains significant accumulated wisdom about how to instruct AI coding agents effectively. Much of that wisdom is universal, but it's currently entangled with Gemini-specific and Firebase-specific instructions.

### Your Task

Analyze the entire build prompt and produce a structured extraction organized into **four categories**:

---

### Category 1: Fully Agnostic Gold

Rules, patterns, workflows, and principles that apply to **any** AI coding agent on **any** platform with **any** database. These need zero modification to be reused.

**What to look for:**
- Code quality standards and verification steps
- Error handling patterns and defensive coding practices
- File organization and project structure principles
- Agent workflow instructions (how to approach tasks, when to pause, how to verify)
- Context management strategies (how agents should manage their own context window)
- Communication patterns (how the agent should report progress, ask questions)
- Testing philosophy and verification checklists
- Git and version control practices
- Security principles
- TypeScript/JavaScript best practices
- State management patterns

**UI, Design Systems & Styling — extract with extra depth here:**
- How to maintain visual consistency across an application
- Rules about using design tokens, CSS variables, or theme values vs hardcoding
- Component styling approaches (utility classes, CSS modules, styled-components, etc.)
- Instructions for how the AI should handle screenshots or visual references
- How to build a style guide or design system from a reference image
- Rules about color systems, spacing scales, typography hierarchies
- Shadow, border-radius, and visual depth patterns
- Button styling, form input styling, card patterns — any component-level design rules
- Responsive design and breakpoint patterns
- Animation and transition standards
- Accessibility requirements (contrast, focus states, screen reader support)
- How to make components look "native" to a design system (consistency enforcement)
- Dark mode / theme switching patterns
- Rules about when to create reusable components vs one-off styles
- Layout systems (grid, flexbox patterns, spacing rhythm)
- Any workflow for going from a design reference to actual styled code
- How the AI should approach visual polish and attention to detail
- Image handling, icon systems, asset management patterns
- Performance optimization rules
- Debugging and troubleshooting workflows
- Prompt engineering patterns embedded in the instructions (meta-level: what makes these instructions effective)

---

### Category 2: Genericized Platform Wisdom

Instructions that are written specifically for **Gemini** but contain underlying principles that apply to **any AI coding model** (Claude, GPT, etc.).

**For each item, provide:**
- The original Gemini-specific instruction (quoted)
- The universal principle it encodes
- A rewritten, platform-agnostic version

**What to look for:**
- Instructions about how the AI should think or reason (Gemini-specific framing of universal cognitive patterns)
- Token/context management advice (may reference Gemini's specific limits but the strategy is universal)
- Output formatting instructions
- How to handle the AI making mistakes or hallucinating
- Instructions about the AI's strengths and weaknesses (some will be Gemini-specific, but the compensating strategies are often universal)
- Conversation flow management
- How to structure requests to the AI

---

### Category 3: Genericized Database Wisdom

Instructions written specifically for **Firebase/Firestore** but containing underlying principles that apply to **any database** (PostgreSQL, Supabase, SQLite, MongoDB, etc.).

**For each item, provide:**
- The original Firebase-specific instruction (quoted)
- The universal database principle it encodes
- A rewritten, database-agnostic version

**What to look for:**
- Data modeling patterns (Firebase's document model has equivalents in relational and other NoSQL systems)
- Query optimization strategies
- Security rules and access control patterns (Firebase Security Rules → RLS, middleware, etc.)
- Real-time data synchronization concepts
- Authentication and authorization flows
- Data validation patterns
- Migration and schema evolution strategies
- Indexing and performance guidance
- Error handling for database operations
- Offline/caching strategies
- Batch operations and transactions

---

### Category 4: Truly Platform-Locked Content

Content that is **genuinely only useful** for Gemini + Firebase and has no transferable value. Be conservative here - only put things in this category if you're confident there's no generalizable principle hiding inside.

**For each item, briefly note:**
- What it is
- Why it can't be generalized (the specific API, service, or behavior it depends on)

---

### Output Format

Structure your output as a clean markdown document with these sections:

```
# Build Prompt Extraction Results

## Executive Summary
- Total items extracted: [count]
- Category 1 (Fully Agnostic): [count] items
- Category 2 (Genericized Platform): [count] items
- Category 3 (Genericized Database): [count] items
- Category 4 (Platform-Locked): [count] items
- Estimated reusable value: [percentage of original content]

## Category 1: Fully Agnostic Gold
### 1.1 Agent Workflow & Methodology
### 1.2 Code Quality Standards
### 1.3 Verification & Testing
### 1.4 Error Handling & Defensive Coding
### 1.5 File Organization & Architecture
### 1.6 UI/UX & Design System Standards
#### 1.6.1 Visual Consistency & Design Tokens
#### 1.6.2 Component Styling Patterns
#### 1.6.3 Layout & Responsive Design
#### 1.6.4 Accessibility & Interaction States
#### 1.6.5 Working From Visual References (Screenshots/Images)
#### 1.6.6 Animation, Transitions & Polish
#### 1.6.7 Design System Workflow (How to Build/Maintain Consistency)
### 1.7 TypeScript & Language Standards
### 1.8 Context & Session Management
### 1.9 Git & Version Control
### 1.10 Security Principles
### 1.11 Communication & Reporting
### 1.12 Performance & Optimization
### 1.13 Debugging & Troubleshooting
### 1.14 Meta-Patterns (What Makes These Instructions Effective)
[Add/remove subsections as needed based on actual content]

## Category 2: Genericized Platform Wisdom
[For each item: Original → Principle → Rewritten]

## Category 3: Genericized Database Wisdom
[For each item: Original → Principle → Rewritten]

## Category 4: Platform-Locked (Non-Transferable)
[Brief list with justifications]

## Cross-Cutting Themes
[Patterns that span multiple categories - the instructor's overall philosophy]

## Recommended Priority Order
[If someone could only implement 10 of these rules, which 10? Which 20?]
```

---

### Critical Instructions

1. **Be exhaustive, not summarizing.** Don't compress 5 related rules into 1. If the build prompt has 5 distinct rules about error handling, extract all 5. The goal is to capture ALL the gold, not create a summary.

2. **Preserve the instructor's voice and specificity.** When a rule says something very specific and opinionated (like "never do X, always do Y"), keep that specificity. Don't water it down into generic advice. The value is in the specificity.

3. **Quote liberally.** When extracting from Categories 2 and 3, quote the original text so we can verify the extraction quality. For Category 1, you can paraphrase but keep the precision.

4. **Look for implicit rules.** Sometimes the most valuable patterns aren't stated as explicit rules but are embedded in examples, workflows, or the structure of the prompt itself. Extract these too.

5. **Note contradictions or tensions.** If any rules seem to contradict each other or create tension, note this. Different contexts may call for different approaches.

6. **Capture the meta-level.** This build prompt was refined over two months. Part of the value isn't just WHAT it says but HOW it says it - the prompt engineering techniques used to instruct the AI effectively. Note these patterns in Category 1.14.

7. **Don't discard anything prematurely.** When in doubt between Category 3 (genericizable) and Category 4 (platform-locked), lean toward Category 3. We can always discard later, but we can't recover what we miss now.

8. **Maintain context window awareness.** Your own output should be thorough but well-structured. Use clear headers and numbered items so the next agent can parse your output efficiently.

9. **Go extra deep on UI/design system content.** The build prompt likely contains significant wisdom about how to make AI-built interfaces look consistent and professional. This includes instructions about working from screenshots or visual references, how to enforce a visual style across components, how to structure CSS/styling for maintainability, and how to approach design tokens and theme values. The instructor specifically created a "style prompt" alongside this build prompt, so design system thinking is core to his methodology. Extract EVERYTHING related to visual consistency, component styling, design workflows, and UI architecture. If a rule seems like it's about coding but has UI implications (e.g., "always create a shared constants file for colors"), capture it in the UI section too.

10. **Distinguish between UI rules and UI opinions.** "Never use inline styles" is a rule. "I prefer rounded buttons" is an opinion. Extract the rules. For opinions, only include them if they serve a clear consistency or maintainability purpose (e.g., "always use consistent border-radius" is a rule even if it mentions a specific value).

---

### What NOT To Do

- Don't reorganize or "improve" the rules beyond categorization. Preserve the original intent.
- Don't add your own coding opinions. Extract what's there.
- Don't skip content because it seems obvious. If the instructor included it, there was a reason.
- Don't merge distinct rules. Two similar-but-different rules should stay as two items.

---

*Now analyze the build prompt provided below and produce the extraction.*

---

**[PASTE THE BUILD PROMPT BELOW THIS LINE]**
