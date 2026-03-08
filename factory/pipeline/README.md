# The Pipeline - How Ideas Become Apps

## The Car Wash Analogy

Picture a car wash with 8 stations. Your idea enters at station 1 as a messy brain dump. At each station, something specific happens to it. By station 8, it's a polished, tested, documented application ready to ship.

## The 8 Stations

### Station 1: Idea Intake
Raw capture. This is where voice transcripts, text rants, bullet points, and half-formed thoughts get turned into something structured. The goal: extract the core concept from the noise.

### Station 2: PRD Generation
Product Requirements Document. Take the extracted idea and turn it into a real spec -- what does this app do, who is it for, what are the features, what does success look like?

### Station 3: Architecture
System design time. What tech stack? What's the file structure? How do the pieces connect? Database schema? API design? This is the blueprint.

### Station 4: Code Generation
First pass of actual code. Scaffold the project, implement the core features, get something running. Bulk implementation happens here.

### Station 5: Security Review
Harden everything. Check for vulnerabilities, ensure secrets aren't hardcoded, validate inputs, review auth flows. Make it safe.

### Station 6: Testing & QA
Write tests. Run them. Lint the code. Type-check it. Make sure everything works and the code is clean.

### Station 7: Computer Use Testing
Final validation with real browser testing. Click through the UI, test the flows manually, use computer vision to verify the app looks right.

### Station 8: Polish & Delivery
Final touches. Generate user documentation, clean up the README, create a handoff package. Make it presentable.

## How Ideas Get Mounted

Each station has a `prompts/` folder. When the intake engine processes an idea, it creates prompt files in the appropriate station's folder. These prompts guide the AI agent at each station.

Each station also has a `manifest.json` (created by the mounter) that tracks:
- What ideas are mounted at this stage
- When they were mounted
- Why they were placed here
- Any overlaps or merges with existing ideas

## Flow

```
inbox/ → engine analyzes → mounted to stages → agents process each stage → app ships
```

It's a one-way flow. Ideas only move forward through the pipeline.
