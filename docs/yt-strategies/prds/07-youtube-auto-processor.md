# PRD: YouTube Auto-Processor (Drop URL → Full Project)

## Overview
The user drops a YouTube URL into the system. The system automatically fetches the transcript, analyzes the video, identifies key moments for screenshots, extracts links from the description, and then uses an AI agent to build out a complete strategy project with all steps, prompts, and notes pre-filled. This is the "hands-off" pipeline.

## Current State (V1)
- YouTube ingestion backend exists (`POST /api/yt-lab/ingest`)
- Fetches transcript via `youtube-transcript-api` (no API key needed)
- Fetches metadata via `yt-dlp` (no API key needed)
- Identifies screenshot-worthy moments via transcript analysis
- Returns structured data to the frontend

## What's Missing (This PRD)
The AI processing layer that takes the raw transcript + metadata and BUILDS the full project automatically.

## User Flow

### Step 1: Paste URL
User pastes a YouTube URL into the input field on the project create form or the batch import view.

### Step 2: Fetch & Preview
System fetches transcript + metadata and shows preview:
- Video title, channel, duration, thumbnail
- Word count, link count, screenshot moment count
- User adds **context** (what they want extracted from this video)

### Step 3: Process (the new part)
User clicks "Process Video" button. The system:

1. **Sends to AI**: Full transcript + user context + video metadata
2. **AI analyzes**: Identifies the strategy, breaks it into steps, extracts key insights
3. **AI generates per step**:
   - Step title and description
   - Draft prompt (what to tell a computer-use agent to execute this step)
   - Expected output
   - Enhancement notes
   - Model recommendation (Opus/Sonnet/Haiku)
4. **Creates project**: Auto-populates a YT Strategy Lab project with all steps
5. **Links screenshots**: Associates screenshot moments with relevant steps

### Step 4: Review & Refine
User sees the complete project in the strategy builder. All fields pre-filled. They can edit, add steps, remove steps, adjust prompts, etc.

## AI Processing Pipeline

### System Prompt for Video Analysis
```
You are a strategy extraction specialist. You analyze video transcripts and extract
actionable, repeatable business workflows.

Given a video transcript and user context, you must:
1. Identify the core strategy or workflow being demonstrated
2. Break it into numbered, sequential steps
3. For each step, provide:
   - A clear title (action-oriented)
   - What to do (detailed description)
   - The prompt to give a computer-use AI agent to execute this step
   - What the expected output looks like
   - Enhancement notes (what would make this step even better)
   - Recommended AI model tier (opus/sonnet/haiku based on complexity)

Focus on making steps REPEATABLE for any niche, not just the specific one in the video.
Use {variables} for niche-specific details.

Output as structured JSON matching the project schema.
```

### Input to AI
```json
{
  "transcript": "Full transcript with timestamps...",
  "metadata": {
    "title": "Video title",
    "channel": "Channel name",
    "duration": 609,
    "description": "Full description with links..."
  },
  "user_context": "I want to extract the step-by-step process for building an AI ad agency...",
  "extracted_urls": ["url1", "url2"],
  "screenshot_suggestions": [
    { "timestamp": 103, "reason": "Shows prompt being typed" }
  ]
}
```

### Output from AI
```json
{
  "project": {
    "name": "AI Ad Agency Workflow",
    "niche": "Automotive / Car Dealerships",
    "description": "Complete workflow for building and operating an AI-powered ad agency...",
    "tags": ["ai-agency", "ads", "automation", "car-dealerships"]
  },
  "steps": [
    {
      "order": 1,
      "title": "Create Brand Style Guide",
      "description": "Have the AI create a complete brand identity...",
      "prompt": "Create a premium brand style guide for a {niche} advertising agency...",
      "expectedOutput": "A complete brand guideline document with color palette, typography...",
      "notes": "Consider adding logo concepts, social media templates...",
      "model": "claude-opus-4-6"
    }
  ]
}
```

## Backend Endpoint

```python
# POST /api/yt-lab/process
# Takes ingested video data + user context
# Sends to AI model for strategy extraction
# Returns structured project data

class ProcessRequest(BaseModel):
    video_id: str
    transcript: list[TranscriptSegment]
    metadata: VideoMetadata
    user_context: str
    extracted_urls: list[str]
    screenshot_suggestions: list[ScreenshotSuggestion]
    model: str = "claude-sonnet-4-6"  # Default to Sonnet for processing

class ProcessResponse(BaseModel):
    project: ProjectData
    steps: list[StepData]
    processing_time: float
```

## Model Selection for Processing
- **Sonnet 4.6** (default): Good balance of quality and speed for extraction
- **Opus 4.6** (premium): Better for complex videos with nuanced strategies
- **Haiku 4.5** (fast): Good enough for simple tutorial-style videos

Uses subscription-based access through AutoForge - no separate API key needed.

## Frontend Integration
- "Process Video" button appears after successful ingestion
- Shows processing progress (spinner + status text)
- On completion, redirects to strategy builder with all steps pre-filled
- User can review and edit everything before finalizing

## Success Criteria
- Dropping a URL and clicking Process creates a complete project in < 2 minutes
- Steps are meaningful and actionable (not just transcript dumps)
- Prompts are actually usable with a computer-use agent
- User context is respected in the output
- Works for any type of video (tutorials, interviews, demos)
