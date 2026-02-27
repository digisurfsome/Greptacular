# PRD: Video Screenshot Intelligence

## Overview
Enhance the YouTube ingestion system to capture and analyze screenshots from videos at key moments. This provides visual context that makes the strategy extraction dramatically more accurate - the agent can literally SEE what's on screen (prompts, dashboards, websites, results).

## Why Screenshots Matter

Videos often contain critical information that's ONLY visible on screen:
- **Prompts being typed** - The exact wording they use
- **Tool interfaces** - What software they're using, how it's configured
- **Results** - Ad creatives, website designs, spreadsheets
- **Workflows** - Step-by-step process visible in browser/IDE
- **Data** - Metrics, analytics, pricing info shown on screen

The transcript alone misses all of this. Screenshots + transcript = complete picture.

## Screenshot Capture Strategy

### Automatic Detection (from transcript analysis)
The system already identifies visual cue moments. Enhance with:

1. **Verbal cues** (existing): "look at this", "as you can see", "here's the prompt"
2. **Screen transition cues** (new): "I opened up", "I went to", "I navigated to"
3. **Result cues** (new): "and here's what it created", "the output was", "it generated"
4. **Instruction cues** (new): "all I typed was", "I just prompted it to", "I asked it to"
5. **Duration-based** (new): Take a screenshot every 30-60 seconds regardless, as a baseline

### Intelligent Timestamp Refinement
- Verbal cues often come AFTER the visual appears (1-3 seconds delay)
- Capture 3 frames: cue_time - 2s, cue_time, cue_time + 2s
- Use AI vision to pick the most informative frame
- Discard duplicates (frames that are >95% similar)

### Screenshot Analysis Pipeline
For each captured screenshot:
1. **OCR extraction** - Pull any visible text (prompts, URLs, data)
2. **UI identification** - What app/website is shown (Facebook, Instagram, Google, IDE, etc.)
3. **Content classification** - Is this a prompt, a result, a dashboard, a form, etc.
4. **Relevance scoring** - How useful is this for understanding the strategy (1-10)
5. **Context linking** - Map to the nearest transcript segment

## Technical Implementation

### Backend Enhancement (server/routers/yt_ingestion.py)

```python
class ScreenshotCapture(BaseModel):
    timestamp: float
    reason: str          # Why this moment was flagged
    image_path: str      # Local file path to screenshot
    ocr_text: str        # Extracted text from image
    ui_detected: str     # What interface/app is shown
    classification: str  # prompt | result | dashboard | form | navigation | other
    relevance_score: int # 1-10
    transcript_segment: str  # Nearest transcript text

class EnhancedIngestResponse(IngestResponse):
    screenshots: list[ScreenshotCapture]
    screenshot_summary: str  # AI-generated summary of what screenshots reveal
```

### Capture Methods

**Method 1: yt-dlp + ffmpeg (current, enhanced)**
```bash
# Capture frame at specific timestamp
yt-dlp --no-download --write-thumbnail {url}
ffmpeg -ss {timestamp} -i $(yt-dlp -g {url}) -frames:v 1 -q:v 2 screenshot_{ts}.jpg
```

**Method 2: Periodic capture (new)**
```bash
# Capture frame every 30 seconds
ffmpeg -i $(yt-dlp -g {url}) -vf "fps=1/30" screenshots/frame_%04d.jpg
```

**Method 3: Scene change detection (new)**
```bash
# Capture frames where the scene changes significantly
ffmpeg -i $(yt-dlp -g {url}) -vf "select='gt(scene,0.3)'" -vsync vfn screenshots/scene_%04d.jpg
```

### Vision Analysis
For each captured screenshot, send to Claude vision:
```python
response = client.messages.create(
    model="claude-haiku-4-5",  # Fast + cheap for vision analysis
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", "data": img_b64}},
            {"type": "text", "text": """Analyze this screenshot from a tutorial video.
            1. What text is visible? (OCR)
            2. What app/website is shown?
            3. Is this showing: a prompt, a result, a dashboard, a form, or navigation?
            4. Rate relevance 1-10 for understanding the tutorial strategy.
            5. Summarize what's happening in one sentence."""}
        ]
    }]
)
```

### Frontend Display

In the strategy builder, each step can show associated screenshots:
```
┌─────────────────────────────────────────────┐
│ Step 3: Competitive Research                │
│ ...                                         │
│                                             │
│ SCREENSHOTS FROM VIDEO                      │
│ ┌──────┐ ┌──────┐ ┌──────┐                │
│ │ 📷   │ │ 📷   │ │ 📷   │                │
│ │1:47  │ │1:55  │ │2:05  │                │
│ │Meta  │ │Search│ │Result│                │
│ │Ad Lib│ │Query │ │List  │                │
│ └──────┘ └──────┘ └──────┘                │
│                                             │
│ Click to enlarge. OCR text shown below.     │
└─────────────────────────────────────────────┘
```

## Video Capture (Future)
The user asked about capturing video clips, not just screenshots. Current limitation: ffmpeg CAN extract short clips but storage/bandwidth is heavier. Plan:

- **Short clips (3-5 seconds)** around key moments - feasible with ffmpeg
- **GIF generation** of key moments - lightweight alternative
- Store as mp4 clips in project folder
- Display inline in the step view with play button

```bash
# Extract 5-second clip around timestamp
ffmpeg -ss {timestamp-2} -i $(yt-dlp -g {url}) -t 5 -c:v libx264 -c:a aac clip_{ts}.mp4
```

This is a future enhancement - screenshots first, clips later.

## Success Criteria
- Screenshots captured at 80%+ of visually important moments
- OCR accurately extracts visible text (prompts, URLs, data)
- Screenshots are linked to the correct steps in the strategy builder
- Agent uses screenshots as context when building out strategy details
- User can view screenshots inline while editing steps
- No more than 20-30 screenshots per 10-minute video (quality over quantity)
