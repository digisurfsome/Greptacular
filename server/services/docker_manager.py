"""
Docker Manager
==============

Manages Docker container lifecycle for the Computer Use Execution Engine.
Each execution session gets its own container with Xvfb, Chromium, and noVNC.
Containers are ephemeral — created on session start, destroyed on stop.

Requires: pip install docker
"""

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Environment configuration
COMPUTER_USE_ENABLED = os.getenv("COMPUTER_USE_ENABLED", "true").lower() == "true"
COMPUTER_USE_DOCKER_IMAGE = os.getenv(
    "COMPUTER_USE_DOCKER_IMAGE", "autoforge-computer-use:latest"
)
COMPUTER_USE_DISPLAY_WIDTH = int(os.getenv("COMPUTER_USE_DISPLAY_WIDTH", "1920"))
COMPUTER_USE_DISPLAY_HEIGHT = int(os.getenv("COMPUTER_USE_DISPLAY_HEIGHT", "1080"))
COMPUTER_USE_NOVNC_PORT = int(os.getenv("COMPUTER_USE_NOVNC_PORT", "6080"))

# Maximum concurrent containers
MAX_CONTAINERS = 5

# Container startup timeout (seconds)
CONTAINER_START_TIMEOUT = 60


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class ContainerInfo(BaseModel):
    """Connection info for a running container."""

    session_id: str
    container_id: str
    novnc_port: int
    vnc_port: int
    novnc_url: str
    status: Literal["starting", "running", "stopped", "error"]


class ContainerStatus(BaseModel):
    """Current status of a container."""

    running: bool
    container_id: str | None = None
    ports: dict[str, int] = {}
    uptime_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Docker Manager
# ---------------------------------------------------------------------------


class DockerManager:
    """
    Manages Docker containers for computer-use execution.

    Each session gets its own container with Xvfb, Chromium, and noVNC.
    Containers are ephemeral — created on session start, destroyed on stop.
    """

    def __init__(self) -> None:
        self._containers: dict[str, ContainerInfo] = {}
        self._start_times: dict[str, datetime] = {}
        self._docker_available: bool | None = None

    def _get_client(self):
        """Lazily initialize Docker client."""
        try:
            import docker

            return docker.from_env()
        except ImportError:
            logger.error("docker package not installed. Install with: pip install docker")
            raise RuntimeError("docker package not installed")
        except Exception as e:
            logger.error(f"Failed to connect to Docker daemon: {e}")
            raise RuntimeError(f"Docker daemon not available: {e}")

    async def is_available(self) -> bool:
        """Check if Docker is available and responsive."""
        if self._docker_available is not None:
            return self._docker_available
        try:
            client = await asyncio.to_thread(self._get_client)
            await asyncio.to_thread(client.ping)
            self._docker_available = True
            return True
        except Exception:
            self._docker_available = False
            return False

    async def start_container(self, session_id: str) -> ContainerInfo:
        """Start a new container for an execution session. Returns connection info."""
        if len(self._containers) >= MAX_CONTAINERS:
            raise RuntimeError(
                f"Maximum container limit ({MAX_CONTAINERS}) reached. "
                "Stop an existing session first."
            )

        if session_id in self._containers:
            raise RuntimeError(f"Container already exists for session {session_id}")

        client = await asyncio.to_thread(self._get_client)

        logger.info(
            f"Starting container for session {session_id} "
            f"(image: {COMPUTER_USE_DOCKER_IMAGE})"
        )

        try:
            container = await asyncio.to_thread(
                client.containers.run,
                COMPUTER_USE_DOCKER_IMAGE,
                detach=True,
                remove=True,
                name=f"autoforge-cu-{session_id}",
                labels={
                    "autoforge.session_id": session_id,
                    "autoforge.service": "computer-use",
                },
                environment={
                    "DISPLAY_WIDTH": str(COMPUTER_USE_DISPLAY_WIDTH),
                    "DISPLAY_HEIGHT": str(COMPUTER_USE_DISPLAY_HEIGHT),
                    "DISPLAY_DEPTH": "24",
                },
                ports={
                    "5900/tcp": None,  # Dynamic host port
                    "6080/tcp": None,  # Dynamic host port
                },
                shm_size="2g",  # Shared memory for Chromium
            )

            # Wait for container to start and ports to be assigned
            await self._wait_for_ports(client, container.id, session_id)

            # Refresh container info to get port mappings
            container.reload()
            ports = container.ports

            vnc_port = int(ports.get("5900/tcp", [{}])[0].get("HostPort", 0))
            novnc_port = int(ports.get("6080/tcp", [{}])[0].get("HostPort", 0))

            if not vnc_port or not novnc_port:
                raise RuntimeError("Failed to allocate ports for container")

            novnc_url = (
                f"http://localhost:{novnc_port}/vnc.html"
                f"?autoconnect=true&resize=scale"
            )

            info = ContainerInfo(
                session_id=session_id,
                container_id=container.id,
                novnc_port=novnc_port,
                vnc_port=vnc_port,
                novnc_url=novnc_url,
                status="running",
            )

            self._containers[session_id] = info
            self._start_times[session_id] = datetime.now(timezone.utc)

            logger.info(
                f"Container started for session {session_id}: "
                f"VNC={vnc_port}, noVNC={novnc_port}"
            )

            # Wait for noVNC health check
            healthy = await self._wait_for_health(novnc_port, session_id)
            if not healthy:
                logger.warning(
                    f"Container {session_id} started but health check timed out. "
                    "Proceeding anyway — services may still be initializing."
                )

            return info

        except Exception as e:
            logger.error(f"Failed to start container for session {session_id}: {e}")
            # Clean up on failure
            await self._cleanup_container(client, session_id)
            raise

    async def stop_container(self, session_id: str) -> None:
        """Stop and remove the container for a session."""
        if session_id not in self._containers:
            logger.warning(f"No container found for session {session_id}")
            return

        try:
            client = await asyncio.to_thread(self._get_client)
            await self._cleanup_container(client, session_id)
        except Exception as e:
            logger.error(f"Error stopping container for session {session_id}: {e}")
        finally:
            self._containers.pop(session_id, None)
            self._start_times.pop(session_id, None)

    async def get_container_status(self, session_id: str) -> ContainerStatus:
        """Check if a container is running and get its ports."""
        info = self._containers.get(session_id)
        if not info:
            return ContainerStatus(running=False)

        try:
            client = await asyncio.to_thread(self._get_client)
            container = await asyncio.to_thread(client.containers.get, info.container_id)
            running = container.status == "running"

            uptime = 0.0
            start_time = self._start_times.get(session_id)
            if start_time:
                uptime = (datetime.now(timezone.utc) - start_time).total_seconds()

            return ContainerStatus(
                running=running,
                container_id=info.container_id,
                ports={"vnc": info.vnc_port, "novnc": info.novnc_port},
                uptime_seconds=uptime,
            )
        except Exception:
            return ContainerStatus(running=False, container_id=info.container_id)

    async def health_check(self, session_id: str) -> bool:
        """Verify the container's noVNC endpoint is responding."""
        info = self._containers.get(session_id)
        if not info:
            return False
        return await self._check_novnc_health(info.novnc_port)

    def get_container_info(self, session_id: str) -> ContainerInfo | None:
        """Get stored container info for a session."""
        return self._containers.get(session_id)

    async def cleanup_all(self) -> None:
        """Stop all containers. Called during server shutdown."""
        if not self._containers:
            return

        logger.info(f"Cleaning up {len(self._containers)} computer-use containers")
        session_ids = list(self._containers.keys())
        for session_id in session_ids:
            try:
                await self.stop_container(session_id)
            except Exception as e:
                logger.error(f"Error cleaning up container {session_id}: {e}")

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    async def _wait_for_ports(
        self, client, container_id: str, session_id: str
    ) -> None:
        """Wait for Docker to assign ports to the container."""
        for _ in range(CONTAINER_START_TIMEOUT):
            try:
                container = await asyncio.to_thread(client.containers.get, container_id)
                if container.status == "running" and container.ports:
                    vnc_ports = container.ports.get("5900/tcp")
                    novnc_ports = container.ports.get("6080/tcp")
                    if vnc_ports and novnc_ports:
                        return
            except Exception:
                pass
            await asyncio.sleep(1)
        raise RuntimeError(
            f"Container {session_id} did not assign ports within {CONTAINER_START_TIMEOUT}s"
        )

    async def _wait_for_health(
        self, novnc_port: int, session_id: str, timeout: int = 30
    ) -> bool:
        """Wait for noVNC to become responsive."""
        for _ in range(timeout):
            if await self._check_novnc_health(novnc_port):
                logger.info(f"Container {session_id} health check passed")
                return True
            await asyncio.sleep(1)
        return False

    async def _check_novnc_health(self, port: int) -> bool:
        """Check if noVNC is responding on the given port."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection("localhost", port), timeout=2.0
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False

    async def _cleanup_container(self, client, session_id: str) -> None:
        """Force-stop and remove a container by session_id."""
        try:
            container_name = f"autoforge-cu-{session_id}"
            container = await asyncio.to_thread(client.containers.get, container_name)
            logger.info(f"Stopping container {container_name}")
            await asyncio.to_thread(container.stop, timeout=10)
        except Exception as e:
            # Container may already be stopped/removed (auto-remove=True)
            logger.debug(f"Container cleanup for {session_id}: {e}")
