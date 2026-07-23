from __future__ import annotations

import docker
from docker.errors import DockerException

from app.config import settings

try:
    _client = docker.DockerClient(base_url=settings.docker_host)
    _client.ping()
except DockerException:
    _client = None


def get_docker():
    if _client is None:
        raise RuntimeError("Docker daemon is not reachable.")
    return _client
