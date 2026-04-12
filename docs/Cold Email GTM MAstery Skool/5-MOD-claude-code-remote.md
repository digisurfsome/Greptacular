# Remote Claude Code Agents — Run Builds From Your Phone

## What You'll Build

A remote Claude Code execution environment that runs on a server. You'll trigger builds, pipelines, and AI agents from your phone via Telegram — without opening your laptop. Claude Code works in the background and notifies you when it's done.

## Prerequisites

- A VPS or cloud server (DigitalOcean, Hetzner, or Railway)
- Anthropic API key
- Telegram account + bot token (via @BotFather)
- Supabase account (for logging)
- Basic understanding of Docker
- SSH access to your server

## Estimated Time

1-2 hours for full setup including Telegram integration.

---

## Why Run Claude Code Remotely

Your laptop is closed. You're on your phone. You need Claude Code to:

- Run your daily lead pipeline at 7am automatically
- Generate a client pitch on demand while you're in a meeting
- Build and deploy a landing page while you eat lunch
- Process data and send you the results

Remote Claude Code means the agent runs on a server. You send commands. It does the work. It pings you when done.

---

## Full Build Instructions

### Step 1: Choose Your Server

**Option A — DigitalOcean Droplet ($6/mo)**
- Create a droplet: Ubuntu 22.04, 1GB RAM, 1 vCPU
- SSH in: `ssh root@your-droplet-ip`

**Option B — Hetzner Cloud ($4/mo)**
- Create a server: Ubuntu 22.04, CX11 (2GB RAM)
- SSH in: `ssh root@your-server-ip`

**Option C — Railway ($5 credit/mo free tier)**
- Create a new project from a GitHub repo
- No SSH needed — deploy via git push

### Step 2: Docker Setup

Create a `Dockerfile` on your server:

```dockerfile
FROM node:18-slim

# Install Claude Code globally
RUN npm install -g @anthropic-ai/claude-code

# Install git (needed for many Claude Code operations)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy project files
COPY . .

# Install project dependencies
RUN npm install

# Environment variables are passed at runtime
ENV ANTHROPIC_API_KEY=""
ENV TELEGRAM_BOT_TOKEN=""
ENV TELEGRAM_CHAT_ID=""

EXPOSE 3000

CMD ["node", "server.js"]
```

Build and run:

```bash
docker build -t claude-remote .
docker run -d \
  --name claude-agent \
  -p 3000:3000 \
  -e ANTHROPIC_API_KEY="sk-ant-..." \
  -e TELEGRAM_BOT_TOKEN="your-bot-token" \
  -e TELEGRAM_CHAT_ID="your-chat-id" \
  -e SUPABASE_URL="your-supabase-url" \
  -e SUPABASE_KEY="your-supabase-key" \
  claude-remote
```

### Step 3: Webhook Trigger Server

Create `server.js` — an Express server that receives POST requests and spawns Claude Code sessions:

```javascript
import express from 'express';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
const app = express();
app.use(express.json());

const WEBHOOK_SECRET = process.env.WEBHOOK_SECRET || 'your-secret';

// Webhook endpoint to trigger Claude Code tasks
app.post('/run', async (req, res) => {
  const { secret, task, project } = req.body;

  if (secret !== WEBHOOK_SECRET) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  // Respond immediately — task runs in background
  res.json({ status: 'started', task });

  try {
    const projectDir = `/app/projects/${project || 'default'}`;
    const { stdout, stderr } = await execAsync(
      `cd ${projectDir} && claude --print "${task}"`,
      { timeout: 300000 } // 5 minute timeout
    );

    await notifyTelegram(`Task completed: ${task}\n\nResult: ${stdout.slice(0, 500)}`);
    await logToSupabase({ task, status: 'completed', output: stdout });
  } catch (error) {
    await notifyTelegram(`Task failed: ${task}\n\nError: ${error.message}`);
    await logToSupabase({ task, status: 'failed', error: error.message });
  }
});

app.get('/status', (req, res) => {
  res.json({ status: 'running', uptime: process.uptime() });
});

app.listen(3000, () => console.log('Claude Remote Agent listening on port 3000'));
```

### Step 4: Telegram Command Interface

Create `telegram-bot.js` — a bot that listens for commands and triggers Claude Code:

```javascript
import TelegramBot from 'node-telegram-bot-api';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, { polling: true });
const ALLOWED_CHAT_ID = process.env.TELEGRAM_CHAT_ID;

// Security: only respond to your chat ID
function isAuthorized(msg) {
  return msg.chat.id.toString() === ALLOWED_CHAT_ID;
}

// /run <task description>
bot.onText(/\/run (.+)/, async (msg, match) => {
  if (!isAuthorized(msg)) return;

  const task = match[1];
  bot.sendMessage(msg.chat.id, `Starting task: ${task}`);

  try {
    const { stdout } = await execAsync(
      `claude --print "${task.replace(/"/g, '\\"')}"`,
      { timeout: 300000, cwd: '/app/projects/default' }
    );

    const result = stdout.length > 4000 ? stdout.slice(0, 4000) + '...' : stdout;
    bot.sendMessage(msg.chat.id, `Done:\n\n${result}`);
  } catch (error) {
    bot.sendMessage(msg.chat.id, `Failed: ${error.message.slice(0, 1000)}`);
  }
});

// /status — check if agent is alive
bot.onText(/\/status/, (msg) => {
  if (!isAuthorized(msg)) return;
  const uptime = Math.floor(process.uptime() / 60);
  bot.sendMessage(msg.chat.id, `Agent running. Uptime: ${uptime} minutes.`);
});

// /build <project> <description>
bot.onText(/\/build (\S+) (.+)/, async (msg, match) => {
  if (!isAuthorized(msg)) return;

  const project = match[1];
  const description = match[2];
  bot.sendMessage(msg.chat.id, `Building ${project}: ${description}`);

  try {
    const { stdout } = await execAsync(
      `cd /app/projects/${project} && claude --print "${description.replace(/"/g, '\\"')}"`,
      { timeout: 600000 }
    );

    bot.sendMessage(msg.chat.id, `Build complete for ${project}.`);
  } catch (error) {
    bot.sendMessage(msg.chat.id, `Build failed: ${error.message.slice(0, 1000)}`);
  }
});

console.log('Telegram bot listening for commands...');
```

Install the dependency:

```bash
npm install node-telegram-bot-api
```

### Step 5: Notification Helper

Create `notify.js` — reusable notification functions:

```javascript
import fetch from 'node-fetch';

const TELEGRAM_API = `https://api.telegram.org/bot${process.env.TELEGRAM_BOT_TOKEN}`;
const CHAT_ID = process.env.TELEGRAM_CHAT_ID;

export async function notifyTelegram(message) {
  try {
    await fetch(`${TELEGRAM_API}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: CHAT_ID,
        text: message,
        parse_mode: 'Markdown'
      })
    });
  } catch (error) {
    console.error('Telegram notification failed:', error.message);
  }
}

export async function logToSupabase({ task, status, output, error }) {
  try {
    await fetch(`${process.env.SUPABASE_URL}/rest/v1/agent_logs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'apikey': process.env.SUPABASE_KEY,
        'Authorization': `Bearer ${process.env.SUPABASE_KEY}`
      },
      body: JSON.stringify({
        task,
        status,
        output: output || null,
        error: error || null,
        created_at: new Date().toISOString()
      })
    });
  } catch (err) {
    console.error('Supabase logging failed:', err.message);
  }
}
```

### Step 6: Background Execution & Scheduling

For scheduled tasks, add a cron-style runner using `node-cron`:

```javascript
import cron from 'node-cron';
import { exec } from 'child_process';
import { promisify } from 'util';
import { notifyTelegram, logToSupabase } from './notify.js';

const execAsync = promisify(exec);

// Daily lead pipeline at 7am EST
cron.schedule('0 7 * * *', async () => {
  try {
    const { stdout } = await execAsync(
      'cd /app/projects/lead-pipeline && claude --print "Run the daily lead pipeline"',
      { timeout: 600000 }
    );
    await notifyTelegram('Daily lead pipeline complete.');
    await logToSupabase({ task: 'daily-pipeline', status: 'completed', output: stdout });
  } catch (error) {
    await notifyTelegram(`Pipeline failed: ${error.message}`);
  }
}, { timezone: 'America/New_York' });
```

### Step 7: Security Configuration

- **API keys in env vars only** — never hardcode in source files
- **Network isolation** — only expose port 3000, keep everything else internal
- **Rate limiting** — add express-rate-limit to prevent abuse:

```javascript
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 20 // max 20 requests per window
});

app.use('/run', limiter);
```

- **Webhook secret** — always validate the secret on incoming requests
- **Chat ID validation** — the Telegram bot only responds to your chat ID

---

## Step-by-Step Plan

1. Provision a VPS (DigitalOcean or Hetzner)
2. SSH in, install Docker
3. Create the project directory with Dockerfile, server.js, telegram-bot.js, notify.js
4. Set up Supabase table `agent_logs` with columns: id, task, status, output, error, created_at
5. Create a Telegram bot via @BotFather, save the token
6. Build and run the Docker container with all env vars
7. Test with `/status` in Telegram
8. Test with `/run Write a haiku about code` in Telegram
9. Set up scheduled tasks with node-cron
10. Monitor logs with `docker logs claude-agent`

---

## Environment Variables

```
ANTHROPIC_API_KEY=sk-ant-...          # Claude API access
TELEGRAM_BOT_TOKEN=123456:ABC...      # From @BotFather
TELEGRAM_CHAT_ID=5915551069           # Your Telegram chat ID
SUPABASE_URL=https://xxx.supabase.co  # Supabase project URL
SUPABASE_KEY=eyJ...                   # Supabase service role key
WEBHOOK_SECRET=your-random-secret     # Webhook authentication
```

---

## Testing Steps

1. `docker ps` — container should be running
2. `curl http://localhost:3000/status` — should return `{"status": "running"}`
3. Send `/status` in Telegram — bot should respond with uptime
4. Send `/run Say hello` in Telegram — should get a response back
5. POST to `/run` endpoint with a task — should complete and notify via Telegram
6. Check Supabase `agent_logs` table — should see logged entries
7. Wait for a scheduled task to fire (or set one 1 minute from now to test)

---

## Success Criteria

- Docker container running on VPS with Claude Code installed
- Webhook endpoint accepts tasks and executes them
- Telegram bot responds to /run, /status, and /build commands
- Completion notifications arrive via Telegram
- All task executions logged to Supabase
- Scheduled tasks fire on time
- Only your Telegram chat ID can issue commands

---

## Use Cases

- **Daily lead pipeline**: Scheduled at 7am, scrapes prospects, researches companies, scores leads, sends results to Telegram
- **On-demand site generation**: `/build landing-page Create a landing page for [product]` — builds and deploys while you're away
- **Report generation**: Triggered by Slack webhook or scheduled, generates analysis reports and sends them
- **Pitch generation**: `/run Generate pitch for acme.com` — creates a client pitch and notifies when ready
