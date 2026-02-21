# VidAi - AI_RULES.md (Martin's AI Coding Rules)

> **Source**: `/AI_RULES.md` in the VidAi repository (https://github.com/digisurfsome/VidAi)
> **Role**: Core coding standards document that defines tech stack rules and AI behavior constraints
> **Lines**: ~25

---

## Complete Document

```markdown
# Tech Stack

- You are building a React application.
- Use TypeScript.
- Use React Router. KEEP the routes in src/App.tsx
- Always put source code in the src folder.
- Put pages into src/pages/
- Put components into src/components/
- The main page (default page) is src/pages/Index.tsx
- UPDATE the main page to include the new components. OTHERWISE, the user can NOT see any components!
- ALWAYS try to use the shadcn/ui library.
- Tailwind CSS: always use Tailwind CSS for styling components. Utilize Tailwind classes extensively for layout, spacing, colors, and other design aspects.
- Do not undertake fake or temporary "for local development" workarounds. Build correctly, production ready with appropriate decisions.
- Do not add any mention of Claude code when you are doing a GIT commit

Available packages and libraries:

- The lucide-react package is installed for icons.
- You ALREADY have ALL the shadcn/ui components and their dependencies installed. So you don't need to install them again.
- You have ALL the necessary Radix UI components installed.
- Use prebuilt components from the shadcn/ui library after importing them. Note that these files shouldn't be edited, so make new components if you need to change them.
```

## What This Document Controls

- **Tech Stack Mandate**: React + TypeScript + React Router
- **File Organization**: All source in `src/`, pages in `src/pages/`, components in `src/components/`
- **Routing**: Routes must stay in `src/App.tsx`
- **Main Page**: Must be updated to show new components (visibility requirement)
- **UI Library**: shadcn/ui as the primary component library
- **Styling**: Tailwind CSS only, used extensively
- **Quality**: Production-ready code only, no temporary workarounds
- **Git Hygiene**: No Claude/AI mentions in commit messages
- **Icons**: Lucide React package
- **Component Rules**: Don't edit shadcn/ui files, create new components instead
- **Pre-installed Packages**: All shadcn/ui, Radix UI components already available

## Key Characteristics

This is a **concise, directive** document. Unlike AutoForge's multi-layered approach, Martin keeps his AI rules tight and focused:

1. **No persona definition** - Just direct instructions
2. **No workflow phases** - Trusts the agent to figure out the process
3. **No verification checklist** - Relies on the agent's judgment
4. **No context budget** - Not managing autonomous multi-session agents
5. **Strong on file organization** - Very clear about where things go
6. **Practical constraints** - "OTHERWISE, the user can NOT see any components!" shows real-world experience with AI mistakes
7. **Anti-pattern prevention** - Explicitly forbids temporary workarounds and shadcn file editing
