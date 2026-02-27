"""
Docker Manager Service
======================

Manages Docker container lifecycle for computer-use execution sessions.
Each session runs inside a container with X11 virtual display and noVNC
for browser-based screen viewing.

Container setup:
  - Image: autoforge/computer-use:latest
  - Exposes port 6080 (noVNC web client)
  - Environment: DISPLAY=:{display_number}
  - Named: autoforge-cu-{session_id[:12]}

When Docker is unavailable (development mode), the manager logs a warning
and provides mock URLs so the rest of the system can operate without a
real container.
"""

import logging
import shutil
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DOCKER_IMAGE = "autoforge/computer-use:latest"
CONTAINER_PREFIX = "autoforge-cu"
NOVNC_CONTAINER_PORT = 6080
DEFAULT_DISPLAY = 1


# ---------------------------------------------------------------------------
# Docker availability check
# ---------------------------------------------------------------------------

def _docker_available() -> bool:
    """Return True if the Docker CLI is on PATH and the daemon is responsive."""
    if shutil.which("docker") is None:
        return False
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return False


# ---------------------------------------------------------------------------
# DockerManager
# ---------------------------------------------------------------------------


class DockerManager:
    """
    Manages Docker containers for computer-use execution sessions.

    Each session gets its own container running an X11 virtual display
    with noVNC for remote viewing. If Docker is not installed or the
    daemon is not running, all operations degrade gracefully with mock
    behaviour suitable for development.
    """

    def __init__(self) -> None:
        # Map session_id -> container name
        self._containers: dict[str, str] = {}
        # Map session_id -> host port bound to noVNC
        self._ports: dict[str, int] = {}
        # Lazily evaluated; None means "not yet checked"
        self._docker_ok: Optional[bool] = None

    # -- internal helpers --------------------------------------------------

    def _check_docker(self) -> bool:
        """Check Docker availability (cached after first call)."""
        if self._docker_ok is None:
            self._docker_ok = _docker_available()
            if not self._docker_ok:
                logger.warning(
                    "Docker is not available. Computer-use containers will be "
                    "simulated with mock URLs (development mode)."
                )
        return self._docker_ok

    def _container_name(self, session_id: str) -> str:
        """Deterministic container name derived from the session ID."""
        short = session_id.replace("-", "")[:12]
        return f"{CONTAINER_PREFIX}-{short}"

    def _find_free_port(self) -> int:
        """Find an available TCP port on the host for noVNC binding."""
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return sock.getsockname()[1]

    # -- public API --------------------------------------------------------

    def start_container(
        self,
        session_id: str,
        display_number: int = DEFAULT_DISPLAY,
    ) -> bool:
        """
        Start a Docker container with X11 + noVNC for the given session.

        Args:
            session_id: Unique execution session identifier.
            display_number: X11 display number inside the container.

        Returns:
            True if the container started (or was mocked) successfully.
        """
        if session_id in self._containers:
            logger.info("Container already running for session %s", session_id)
            return True

        if not self._check_docker():
            # Development fallback -- register a mock entry
            name = self._container_name(session_id)
            self._containers[session_id] = name
            self._ports[session_id] = NOVNC_CONTAINER_PORT
            logger.info(
                "Mock container registered for session %s (Docker unavailable)",
                session_id,
            )
            return True

        name = self._container_name(session_id)
        host_port = self._find_free_port()

        cmd = [
            "docker",
            "run",
            "-d",
            "--name",
            name,
            "-p",
            f"{host_port}:{NOVNC_CONTAINER_PORT}",
            "-e",
            f"DISPLAY=:{display_number}",
            "--shm-size=512m",
            DOCKER_IMAGE,
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=60)
            self._containers[session_id] = name
            self._ports[session_id] = host_port
            logger.info(
                "Container %s started for session %s on port %d",
                name,
                session_id,
                host_port,
            )
            return True
        except subprocess.SubprocessError as exc:
            logger.error("Failed to start container for session %s: %s", session_id, exc)
            return False

    def stop_container(self, session_id: str) -> bool:
        """
        Stop and remove the Docker container for the given session.

        Returns:
            True if the container was stopped, or it was a mock entry.
        """
        name = self._containers.pop(session_id, None)
        self._ports.pop(session_id, None)

        if name is None:
            logger.warning("No container found for session %s", session_id)
            return False

        if not self._check_docker():
            logger.info("Mock container removed for session %s", session_id)
            return True

        try:
            subprocess.run(
                ["docker", "rm", "-f", name],
                capture_output=True,
                timeout=30,
            )
            logger.info("Container %s removed for session %s", name, session_id)
            return True
        except subprocess.SubprocessError as exc:
            logger.error("Failed to remove container %s: %s", name, exc)
            return False

    def get_novnc_url(self, session_id: str) -> str:
        """
        Return the noVNC URL for the session's container.

        If Docker is unavailable, returns a placeholder URL that the
        frontend can detect as a development stub.
        """
        port = self._ports.get(session_id, NOVNC_CONTAINER_PORT)
        return f"http://localhost:{port}/vnc.html?autoconnect=true"

    def health_check(self, session_id: str) -> bool:
        """
        Check whether the container for the given session is healthy.

        Returns:
            True if the container is running (or mocked), False otherwise.
        """
        if session_id not in self._containers:
            return False

        if not self._check_docker():
            # Mock containers are always "healthy"
            return True

        name = self._containers[session_id]
        try:
            result = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", name],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0 and result.stdout.strip() == "true"
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    async def cleanup_all(self) -> None:
        """Stop all tracked containers. Called during server shutdown."""
        for session_id in list(self._containers.keys()):
            self.stop_container(session_id)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_manager: Optional[DockerManager] = None


def get_docker_manager() -> DockerManager:
    """Return the global DockerManager singleton (created on first call)."""
    global _manager
    if _manager is None:
        _manager = DockerManager()
    return _manager


async def cleanup_docker_manager() -> None:
    """Shut down the global DockerManager. Called during server shutdown."""
    global _manager
    if _manager is not None:
        await _manager.cleanup_all()
        _manager = None
