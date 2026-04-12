# Building a Voice Agent — AI That Answers Calls and Books Meetings

## What You'll Build

An AI-powered phone agent that answers incoming calls, has natural conversations, qualifies leads using your criteria, checks your calendar for availability, books meetings, and transfers to a human when needed. It runs 24/7 and handles calls you'd otherwise miss.

## Prerequisites

- Vapi account (voice AI platform)
- Twilio account with a phone number
- Anthropic API key (Claude for reasoning)
- ElevenLabs account (text-to-speech)
- Google Calendar API credentials
- n8n account (for logging and CRM updates)
- A clear understanding of your qualifying criteria

## Estimated Time

2-3 hours for full setup including calendar integration and call transfer.

---

## Architecture

```
Incoming call
  → Twilio (receives the call)
    → Deepgram (speech-to-text, real-time transcription)
      → Claude (reasoning, decides what to say and do)
        → ElevenLabs (text-to-speech, natural voice)
          → Audio response back to caller
```

At each turn in the conversation, Claude:
1. Reads the transcript so far
2. Decides what to say next
3. Decides if a tool call is needed (check calendar, book meeting, transfer)
4. Generates a short, natural response

The caller hears a human-sounding voice with sub-second response times.

---

## Full Build Instructions

### Step 1: Vapi Account Setup

Vapi handles the voice pipeline — it connects Twilio, Deepgram, Claude, and ElevenLabs so you don't have to build the real-time audio streaming yourself.

1. Go to [vapi.ai](https://vapi.ai) and create an account
2. Navigate to the Dashboard
3. Copy your Vapi API key from Settings

### Step 2: Connect Twilio

1. In Vapi, go to Phone Numbers
2. Click "Import from Twilio"
3. Enter your Twilio Account SID and Auth Token (from twilio.com/console)
4. Select the phone number you want the AI to answer
5. Vapi will configure the webhook automatically — calls to this number now route through Vapi

If you don't have a Twilio number yet:
1. Go to twilio.com, create an account
2. Buy a phone number ($1/mo for a local US number)
3. Come back to Vapi and import it

### Step 3: Create the Assistant

In Vapi, go to Assistants and create a new one.

**Model Configuration:**
- Provider: Anthropic
- Model: Claude 3.5 Sonnet
- Temperature: 0.3 (low for consistency)
- Max tokens: 150 (keeps responses short)

**Voice Configuration:**
- Provider: ElevenLabs
- Voice: Pick one that matches your brand (Rachel for professional, Josh for casual)
- Stability: 0.5
- Similarity boost: 0.75

**Transcription:**
- Provider: Deepgram
- Model: Nova-2 (fastest, most accurate)
- Language: English

### Step 4: Write the System Prompt

This is the most critical part. The system prompt controls everything the agent says and does.

```
You are a phone assistant for [Your Company Name]. You answer incoming calls, qualify potential customers, and book meetings with the sales team.

VOICE RULES:
- Keep every response to 1-2 sentences maximum
- Speak naturally — use contractions ("I'll", "we're", "that's")
- Ask one question at a time — never stack multiple questions
- Pause after important information to let the caller respond
- If you don't understand something, ask them to repeat it
- Never spell out URLs or email addresses on a call — offer to text or email them instead

CONVERSATION FLOW:
1. Greet the caller: "Hey, thanks for calling [Company]. How can I help you?"
2. Listen to what they need
3. If they're interested in your product/service, start qualifying:
   - "What are you looking for specifically?"
   - "What's your timeline for getting this set up?"
   - "Do you have a budget range in mind?"
   - "Is there anyone else involved in the decision?"
4. If they qualify (interested + timeline within 3 months + decision maker):
   - Check calendar availability
   - Offer 2-3 time slots
   - Confirm the booking with their name and email
5. If they don't qualify:
   - Be helpful and friendly
   - Direct them to your website or email
   - Don't waste their time or yours

TRANSFER RULES:
- Transfer to a human if the caller:
  - Asks to speak to a person
  - Gets frustrated or confused
  - Has a billing or account issue (you don't have access to account data)
  - Has a question you can't answer from your knowledge
- When transferring: "Let me connect you with someone on the team who can help with that. One moment."

THINGS YOU KNOW:
- [Your Company Name] is a [what you do]
- Pricing: [your pricing tiers]
- Services: [your service list]
- Office hours: [your hours]

THINGS YOU DON'T DO:
- Don't make promises about pricing or timelines without checking
- Don't access or discuss specific account details
- Don't take credit card information over the phone
- Don't argue with upset callers — transfer them
```

### Step 5: Add Tools

Tools let the assistant take actions during the call. In Vapi, go to the Tools section of your assistant.

**Tool 1: check_calendar**

```json
{
  "type": "function",
  "function": {
    "name": "check_calendar",
    "description": "Check available meeting slots for the next 5 business days. Call this when a caller wants to book a meeting.",
    "parameters": {
      "type": "object",
      "properties": {
        "timezone": {
          "type": "string",
          "description": "The caller's timezone (e.g., 'America/New_York')"
        }
      }
    }
  }
}
```

This tool calls your n8n webhook, which checks Google Calendar and returns available slots.

**Tool 2: book_meeting**

```json
{
  "type": "function",
  "function": {
    "name": "book_meeting",
    "description": "Book a meeting on the calendar. Call this after the caller confirms a time slot.",
    "parameters": {
      "type": "object",
      "properties": {
        "datetime": {
          "type": "string",
          "description": "The meeting datetime in ISO format"
        },
        "caller_name": {
          "type": "string",
          "description": "The caller's full name"
        },
        "caller_email": {
          "type": "string",
          "description": "The caller's email address"
        },
        "notes": {
          "type": "string",
          "description": "Brief summary of what the caller is looking for"
        }
      },
      "required": ["datetime", "caller_name", "caller_email"]
    }
  }
}
```

**Tool 3: transfer_call**

```json
{
  "type": "function",
  "function": {
    "name": "transfer_call",
    "description": "Transfer the call to a human team member. Use when the caller asks for a person, is frustrated, or has a question you can't answer.",
    "parameters": {
      "type": "object",
      "properties": {
        "reason": {
          "type": "string",
          "description": "Brief reason for the transfer"
        },
        "conversation_summary": {
          "type": "string",
          "description": "Summary of the conversation so far so the human has context"
        }
      },
      "required": ["reason", "conversation_summary"]
    }
  }
}
```

### Step 6: Build the Calendar Integration (n8n)

Create an n8n workflow called "Voice Agent Calendar."

**Webhook Node (check_calendar):**
- Receives requests from Vapi when the AI calls the check_calendar tool
- Path: `/check-calendar`

**Google Calendar Node (Get Events):**
- Calendar: your booking calendar
- Time Min: now
- Time Max: 5 business days from now
- Returns all existing events

**Code Node (Find Available Slots):**
```javascript
const events = $input.all();
const busySlots = events.map(e => ({
  start: new Date(e.json.start.dateTime),
  end: new Date(e.json.end.dateTime)
}));

// Generate 30-min slots between 9am-5pm, skip busy ones
const available = [];
const now = new Date();

for (let day = 0; day < 5; day++) {
  const date = new Date(now);
  date.setDate(date.getDate() + day + 1);

  // Skip weekends
  if (date.getDay() === 0 || date.getDay() === 6) continue;

  for (let hour = 9; hour < 17; hour++) {
    const slotStart = new Date(date);
    slotStart.setHours(hour, 0, 0, 0);
    const slotEnd = new Date(slotStart);
    slotEnd.setMinutes(30);

    const isBusy = busySlots.some(busy =>
      slotStart < busy.end && slotEnd > busy.start
    );

    if (!isBusy) {
      available.push({
        datetime: slotStart.toISOString(),
        display: slotStart.toLocaleString('en-US', {
          weekday: 'long',
          month: 'long',
          day: 'numeric',
          hour: 'numeric',
          minute: '2-digit'
        })
      });
    }
  }
}

// Return next 6 available slots
return [{ json: { available_slots: available.slice(0, 6) } }];
```

**Respond to Webhook Node:**
- Returns the available slots to Vapi

**Second Webhook Node (book_meeting):**
- Path: `/book-meeting`

**Google Calendar Node (Create Event):**
- Calendar: your booking calendar
- Summary: `Call with {{ $json.caller_name }}`
- Start: `{{ $json.datetime }}`
- Duration: 30 minutes
- Description: `{{ $json.notes }}`
- Attendees: `{{ $json.caller_email }}`

**Supabase Node (Log Booking):**
- Insert into a `bookings` table for tracking

**Respond to Webhook Node:**
- Returns confirmation to Vapi

### Step 7: Connect Tools to n8n

In Vapi's tool configuration, set the server URL for each tool to your n8n webhook URLs:

- check_calendar → `https://your-n8n.app.n8n.cloud/webhook/check-calendar`
- book_meeting → `https://your-n8n.app.n8n.cloud/webhook/book-meeting`
- transfer_call → configure in Vapi's transfer settings with the destination phone number

### Step 8: Call Transfer Setup

In Vapi, configure the transfer destination:

1. Go to your assistant's settings
2. Under "Transfer," add your team's phone number
3. Set transfer mode to "warm" — the AI stays on the line briefly to hand off context
4. The conversation summary from the transfer_call tool is spoken to the human before the caller is connected

### Step 9: Logging and Monitoring (n8n)

Create a separate n8n workflow that Vapi webhooks into after each call:

1. **Webhook Node**: receives call data from Vapi's end-of-call webhook
2. **Supabase Node**: logs call details (duration, transcript, outcome, caller info)
3. **IF Node**: if meeting was booked, send notification
4. **Telegram Node**: notify you of booked meetings and important calls

---

## Qualifying Questions Framework

Adapt these to your business. The agent asks them naturally in conversation, not as a rigid script.

| Question | What It Reveals | Qualifier |
|---|---|---|
| "What are you looking for specifically?" | Intent and need | Must have a clear use case |
| "What's your timeline?" | Urgency | Within 3 months = qualified |
| "Do you have a budget range in mind?" | Budget | Within your pricing range |
| "Who else is involved in the decision?" | Authority | Decision maker or strong influencer |
| "What are you using right now?" | Current solution | Switching = higher intent |
| "What's not working about your current setup?" | Pain point | Clear pain = higher conversion |

The agent doesn't need all answers to qualify. Name + email + clear need + reasonable timeline is enough to book a meeting.

---

## Call Transfer Protocol

Transfer the call when:
- Caller explicitly asks for a human
- Caller is frustrated (raised voice, repeated complaints, "this isn't working")
- Caller is confused and repeating themselves
- The question requires account-specific information
- The caller has a billing dispute
- You don't have enough information to help

When transferring:
1. Tell the caller: "Let me connect you with someone who can help with that."
2. Send the conversation_summary to the human via the transfer tool
3. The human gets context before the caller is connected
4. Never just drop the call — always explain the transfer

---

## Pricing This Service

If you're offering voice agents to clients:

| Component | Price |
|---|---|
| Setup (build + configure + test) | $2,500 - $5,000 |
| Monthly management | $500 - $1,000/mo |
| Per-minute usage (Vapi + Twilio + AI) | ~$0.10-0.15/min (pass through or mark up) |

**Value proposition**: 24/7 coverage, no missed calls, consistent qualification, instant booking. A human receptionist costs $3,000-4,000/mo and works 8 hours.

**Upsell path**: if you're already running cold email campaigns for clients, the voice agent handles the inbound side. Cold email generates interest, voice agent converts it to meetings.

---

## Step-by-Step Plan

1. Create Vapi account and get API key
2. Set up Twilio phone number (or import existing)
3. Create Vapi assistant with Claude + ElevenLabs
4. Write and refine the system prompt
5. Add the three tools (check_calendar, book_meeting, transfer_call)
6. Build the n8n calendar check workflow
7. Build the n8n booking workflow
8. Connect Vapi tools to n8n webhook URLs
9. Configure call transfer with team phone number
10. Build the logging workflow (call data to Supabase)
11. Test with a real call — call the number yourself
12. Refine the system prompt based on test calls
13. Set up Telegram notifications for booked meetings
14. Go live

---

## Environment Variables

```
VAPI_API_KEY=vapi_...                    # Vapi platform access
TWILIO_ACCOUNT_SID=AC...                 # Twilio account
TWILIO_AUTH_TOKEN=...                     # Twilio auth
GOOGLE_CALENDAR_CREDENTIALS='{...}'      # Google Calendar API (JSON key)
ANTHROPIC_API_KEY=sk-ant-...             # Claude API for reasoning
ELEVENLABS_API_KEY=...                   # ElevenLabs text-to-speech
SUPABASE_URL=https://xxx.supabase.co     # Call logging database
SUPABASE_KEY=eyJ...                      # Supabase service role key
TELEGRAM_BOT_TOKEN=123456:ABC...         # Notifications
TELEGRAM_CHAT_ID=5915551069              # Your Telegram chat ID
```

---

## Testing Steps

1. Call the Twilio number from your phone — the AI should greet you
2. Ask about pricing — should respond from the system prompt knowledge
3. Ask to book a meeting — should check calendar and offer slots
4. Confirm a slot — should create a Google Calendar event
5. Check your calendar — event should appear with caller details
6. Check Supabase — call should be logged
7. Check Telegram — booking notification should arrive
8. Say "Can I talk to someone?" — should trigger transfer
9. Call with a difficult question outside the FAQ — should say it doesn't know
10. Test with poor audio (speaker phone, background noise) — should handle gracefully
11. Test rapid interruption (talk over the AI) — should handle turn-taking

---

## Success Criteria

- Phone number answers calls 24/7 with natural-sounding AI
- AI qualifies callers using your criteria
- Calendar check returns accurate available slots
- Meetings are booked and appear on Google Calendar with attendee details
- Call transfers work with conversation context passed to the human
- All calls are logged to Supabase with transcripts
- Telegram notifications arrive for booked meetings
- Response latency is under 1 second (caller doesn't feel a delay)
- AI correctly handles "I don't know" situations without making things up
- The agent sounds natural, not robotic — callers engage in real conversation
