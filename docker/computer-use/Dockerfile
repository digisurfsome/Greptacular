# Computer Use Execution Engine Container
# ========================================
#
# Provides a virtual desktop environment for the Computer Use Agent:
# - Xvfb virtual display (1920x1080 default, configurable)
# - Chromium browser
# - noVNC + websockify for WebSocket-based VNC streaming
# - ffmpeg for future screen recording (Phase 8)
# - supervisord to manage all services
#
# Build:
#   docker build -t autoforge-computer-use docker/computer-use/
#
# Run:
#   docker run -d -p 6080:6080 -p 5900:5900 autoforge-computer-use
#
# Access noVNC: http://localhost:6080/vnc.html?autoconnect=true&resize=scale

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:0
ENV DISPLAY_WIDTH=1920
ENV DISPLAY_HEIGHT=1080
ENV DISPLAY_DEPTH=24

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Virtual display
    xvfb \
    x11vnc \
    # Browser
    chromium-browser \
    # noVNC and websockify
    novnc \
    websockify \
    # Screen recording (Phase 8)
    ffmpeg \
    # Utilities
    xdotool \
    xdg-utils \
    supervisor \
    curl \
    ca-certificates \
    fonts-liberation \
    fonts-dejavu-core \
    dbus-x11 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -s /bin/bash agent && \
    mkdir -p /home/agent/.config/chromium && \
    chown -R agent:agent /home/agent

# Copy supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create log directory
RUN mkdir -p /var/log/supervisor && \
    chown -R agent:agent /var/log/supervisor

# Health check script
RUN echo '#!/bin/bash\ncurl -sf http://localhost:6080/ > /dev/null && echo "healthy" || exit 1' > /usr/local/bin/healthcheck.sh && \
    chmod +x /usr/local/bin/healthcheck.sh

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD /usr/local/bin/healthcheck.sh

# Expose ports
EXPOSE 5900
EXPOSE 6080

# Run as non-root
USER agent
WORKDIR /home/agent

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
