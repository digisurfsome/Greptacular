# Computer Use Execution Container
# =================================
#
# Provides an isolated X11 + noVNC environment for the computer-use agent.
# The agent runs inside this container, interacting with a virtual display
# that is streamed to the browser via noVNC.
#
# Services:
#   - Xvfb:  Virtual X11 framebuffer (:1, 1920x1080x24)
#   - x11vnc: VNC server connected to the virtual display
#   - noVNC:  WebSocket-to-VNC bridge (port 6080)
#   - Chromium: Browser for the agent to control
#   - ffmpeg: Screen capture / recording support

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1
ENV RESOLUTION=1920x1080x24

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Virtual display
    xvfb \
    # VNC server
    x11vnc \
    # noVNC (WebSocket bridge)
    novnc websockify \
    # Browser
    chromium-browser \
    # Screen capture
    ffmpeg \
    # Window manager (lightweight)
    fluxbox \
    # Utilities
    supervisor \
    curl \
    ca-certificates \
    fonts-liberation \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for the agent
RUN useradd -m -s /bin/bash agent
ENV HOME=/home/agent

# noVNC configuration
ENV NOVNC_PORT=6080
ENV VNC_PORT=5901

# Copy supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose noVNC port
EXPOSE 6080

# Health check: verify noVNC is responding
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:6080/ || exit 1

USER agent
WORKDIR /home/agent

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
