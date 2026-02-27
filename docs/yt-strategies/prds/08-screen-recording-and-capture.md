# PRD: Screen Recording & Video Capture for Computer-Use Agent

## Overview
When the computer-use execution engine is running steps, capture not just screenshots but short video clips of key moments. This provides richer documentation, better debugging, and compelling demo content for marketing the SaaS.

## Capture Types

### 1. Screenshots (Primary - Already Planned)
- Taken at step transitions
- Taken on pause
- Taken when agent completes a notable action
- Stored as JPEG/PNG

### 2. Short Video Clips (3-10 seconds)
- Captured around key moments (agent clicking, typing, form filling)
- Shows the motion/flow of what the agent is doing
- More context than a static screenshot
- Stored as MP4 or WebM

### 3. Full Session Recording (Optional)
- Records the entire noVNC display for the full execution
- Useful for debugging, training, and demo creation
- Can be very large - only enable when explicitly requested
- Stored as MP4

## Technical Implementation

### For noVNC-Based Execution (Custom Computer Use Engine)

**Screenshot Capture:**
```python
# Already available via the computer_use tool - Claude takes screenshots natively
# Additionally, we can capture via noVNC:
import subprocess

def capture_screenshot(display_number: int, output_path: str):
    """Capture screenshot from virtual display."""
    subprocess.run([
        'xdotool', 'getactivewindow', '--',
        'import', '-window', 'root', output_path
    ], timeout=5)
```

**Video Clip Capture:**
```python
import subprocess
import threading

def capture_clip(display_number: int, output_path: str, duration: int = 5):
    """Capture a short video clip from virtual display."""
    subprocess.run([
        'ffmpeg',
        '-video_size', '1920x1080',
        '-framerate', '15',
        '-f', 'x11grab',
        '-i', f':{display_number}',
        '-t', str(duration),
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-crf', '28',
        output_path
    ], timeout=duration + 10)

def capture_clip_async(display_number: int, output_path: str, duration: int = 5):
    """Non-blocking clip capture."""
    thread = threading.Thread(
        target=capture_clip,
        args=(display_number, output_path, duration)
    )
    thread.start()
    return thread
```

**Full Session Recording:**
```python
class SessionRecorder:
    """Records the full execution session."""

    def __init__(self, display_number: int, output_path: str):
        self.process = None
        self.display = display_number
        self.output = output_path

    def start(self):
        self.process = subprocess.Popen([
            'ffmpeg',
            '-video_size', '1920x1080',
            '-framerate', '10',
            '-f', 'x11grab',
            '-i', f':{self.display}',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '30',
            self.output
        ])

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=10)
```

### When to Capture

**Auto-Capture Triggers:**
| Trigger | Capture Type | Duration |
|---------|-------------|----------|
| Step starts | Screenshot | - |
| Step completes | Screenshot + 3s clip (of the final result) | 3s |
| Agent clicks a button | 3s clip (centered on the click) | 3s |
| Agent fills a form | 5s clip (capture the typing) | 5s |
| Agent navigates to new page | Screenshot (after page load) | - |
| User pauses execution | Screenshot | - |
| Error occurs | Screenshot + 5s clip (capture the error state) | 5s |

**Manual Capture:**
- User clicks "Capture" button in the execution viewer
- Takes a screenshot + optional 5s clip
- Stored with the current step

### Storage Structure
```
.autoforge/yt-lab/{project_id}/captures/
├── step-01/
│   ├── start.jpg
│   ├── complete.jpg
│   ├── clip-form-fill.mp4
│   └── clip-result.mp4
├── step-02/
│   ├── start.jpg
│   ├── navigation-meta-ad-library.jpg
│   ├── clip-search.mp4
│   └── complete.jpg
└── session-recording.mp4 (optional full recording)
```

### Frontend Display

In the strategy builder, each step shows its captures:
```
┌─────────────────────────────────────────────────┐
│ Step 3: Competitive Research              Done ✓│
│ ...                                             │
│                                                 │
│ CAPTURES                                        │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐           │
│ │ 📷   │ │ 🎬   │ │ 📷   │ │ 🎬   │           │
│ │Start │ │Search│ │Result│ │Final │           │
│ │ .jpg │ │ .mp4 │ │ .jpg │ │ .mp4 │           │
│ └──────┘ └──────┘ └──────┘ └──────┘           │
│                                                 │
│ ▶ Full session recording available (12:34)      │
└─────────────────────────────────────────────────┘
```

Screenshots: click to enlarge in a modal
Video clips: click to play inline (HTML5 video element)
Full recording: opens in a new tab or modal video player

## Dependencies
- `ffmpeg` (for video capture from X11 display)
- `xdotool` (for screenshot capture, optional)
- Docker container with X11 display (already part of computer-use setup)

## SaaS Marketing Angle
These recordings are GOLD for marketing:
- Auto-generate demo videos showing the agent working
- Social media clips of the agent navigating websites
- Before/after comparisons (empty → filled project)
- Testimonial-style walkthroughs

## Success Criteria
- Screenshots captured automatically at every step transition
- Video clips capture meaningful moments (not just random frames)
- Storage is organized per project/step
- Clips are viewable inline in the strategy builder
- Full session recording available as opt-in
- Total storage per project stays reasonable (< 500MB for a typical 7-step workflow)
