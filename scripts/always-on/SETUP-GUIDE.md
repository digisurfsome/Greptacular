# AutoForge Always-On Setup Guide (Windows 10)

Three things to set up. Total time: ~15 minutes.

---

## 1. Always-On Server (Never Restart Again)

### Quick Start (manual)

Double-click `autoforge-startup.vbs`. AutoForge starts hidden in the background.
Open `http://localhost:8888` in your browser. Done.

### Auto-Start on Boot (set and forget)

1. Press `Win+R`, type `shell:startup`, press Enter
2. Copy `autoforge-startup.vbs` into the folder that opens
3. That's it. AutoForge now starts every time you log into Windows.

### Controls

| Action | How |
|--------|-----|
| **Start** | Double-click `autoforge-startup.vbs` |
| **Stop** | Double-click `autoforge-stop.bat` |
| **Restart** | Double-click `autoforge-restart.bat` |
| **Check if running** | Open `http://localhost:8888` in your browser |

### What It Does

- Runs AutoForge server hidden (no terminal window cluttering your taskbar)
- Auto-restarts if the server crashes (5-second delay between restarts)
- Logs output to the background (not visible unless you run the .bat directly)

---

## 2. Install as a Desktop App (PWA)

Make AutoForge feel like a native Windows app with its own taskbar icon.

1. Open Chrome and go to `http://localhost:8888`
2. Click the three dots menu (top right)
3. Click **"Install AutoForge"** (or **"More tools" > "Create shortcut"**)
4. Check **"Open as window"** if prompted
5. Click **Install**

Now you have:
- AutoForge icon on your desktop and in your Start menu
- Opens in its own window (no browser URL bar, no tabs)
- Looks and feels like a native app
- Pin it to your taskbar for instant access

---

## 3. Access From Anywhere (Phone, Laptop on the Go)

### Option A: Cloudflare Tunnel (Free, Recommended)

Gives you a real URL like `forge.yourdomain.com` that works from anywhere.

**Prerequisites:** A Cloudflare account (free) and a domain managed by Cloudflare.

**Step 1: Install cloudflared**

```powershell
# Option 1: Download installer
# Go to: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
# Download the Windows 64-bit installer and run it.

# Option 2: Using winget (if you have it)
winget install Cloudflare.cloudflared
```

**Step 2: Authenticate**

```powershell
cloudflared tunnel login
```
This opens a browser. Pick the domain you want to use.

**Step 3: Create tunnel**

```powershell
cloudflared tunnel create autoforge
```

**Step 4: Configure the tunnel**

Create file `%USERPROFILE%\.cloudflared\config.yml`:

```yaml
tunnel: autoforge
credentials-file: C:\Users\YOUR_USERNAME\.cloudflared\TUNNEL_ID.json

ingress:
  - hostname: forge.yourdomain.com
    service: http://localhost:8888
  - service: http_status:404
```

Replace `YOUR_USERNAME` and `TUNNEL_ID` with your actual values.

**Step 5: Add DNS route**

```powershell
cloudflared tunnel route dns autoforge forge.yourdomain.com
```

**Step 6: Run the tunnel**

```powershell
cloudflared tunnel run autoforge
```

**Step 7: Install as Windows service (auto-start)**

```powershell
cloudflared service install
```

Now `forge.yourdomain.com` works from your phone, any laptop, anywhere.

### Option B: Tailscale (Easiest, No Domain Needed)

Private network between your devices. Simpler but only works on YOUR devices.

**Step 1: Install Tailscale**

Go to https://tailscale.com/download and install on:
- Your Windows PC
- Your phone (iOS/Android app)
- Any other laptop you use

**Step 2: Sign in on all devices**

Use the same account on every device.

**Step 3: Get your PC's Tailscale IP**

```powershell
tailscale ip
```
You'll get something like `100.64.x.x`.

**Step 4: Bind AutoForge to all interfaces**

Edit `autoforge-service.bat` and change the start line to:
```
python start_ui.py --host 0.0.0.0 --port 8888
```

**Step 5: Access from phone**

Open your phone browser and go to `http://100.64.x.x:8888`.

That's it. Works anywhere you have internet. Encrypted, private, only your devices.

### Option C: ngrok (Quickest for Testing)

Temporary public URL. Good for testing, not permanent.

```powershell
# Install
winget install ngrok.ngrok

# Authenticate (free account at ngrok.com)
ngrok config add-authtoken YOUR_TOKEN

# Start tunnel
ngrok http 8888
```

Gives you a URL like `https://abc123.ngrok-free.app` that forwards to your AutoForge.
URL changes every time you restart ngrok (unless you pay for a fixed subdomain).

---

## Troubleshooting

### AutoForge won't start
- Check if port 8888 is already in use: open `http://localhost:8888` first
- Run `autoforge-stop.bat` then try again
- Check if Python is in your PATH: open cmd, type `python --version`

### Browser says "can't connect"
- Server might not be running. Double-click `autoforge-startup.vbs`
- Wait 10-15 seconds for startup, then refresh

### Server keeps crashing
- Run `autoforge-service.bat` directly (not via VBS) to see error output
- Check if `venv` exists in the AutoForge directory
- Try: `cd AutoForge && venv\Scripts\activate && pip install -r requirements.txt`

### Cloudflare Tunnel not working
- Run `cloudflared tunnel run autoforge` manually to see errors
- Check `%USERPROFILE%\.cloudflared\config.yml` exists and is correct
- Make sure your domain's DNS is managed by Cloudflare

### Tailscale device not reachable
- Make sure Tailscale is running on BOTH devices
- Check Windows Firewall allows port 8888
- Try: `tailscale ping YOUR_PC_IP` from the other device
