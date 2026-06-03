# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# cloud_dog_config — Environment metadata accessor
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Provides runtime environment metadata derived from the current
#   GlobalConfig without direct os.environ reads.
# Related requirements: FR1.20
# Related architecture: CC1.12
#
# Recent changes:
# - 2026-02-18: Added EnvMetadata and get_env_metadata API.

"""Runtime metadata access from GlobalConfig."""

from __future__ import annotations

import os
import socket
import sys
from dataclasses import dataclass
from datetime import datetime

from cloud_dog_config.config import GlobalConfig
from cloud_dog_config.redaction import redact, redact_string


@dataclass(frozen=True, slots=True)
class EnvMetadata:
    """Runtime metadata snapshot derived from GlobalConfig."""

    hostname: str
    process_id: int
    python_version: str
    config_version: str
    loaded_at: datetime
    sources: list[str]
    vault_available: bool
    env_file_count: int


def get_env_metadata() -> EnvMetadata:
    """Return runtime metadata from the current GlobalConfig."""
    from cloud_dog_config.loader import get_config

    cfg = get_config()
    if not isinstance(cfg, GlobalConfig):
        raise TypeError("Current config is not a GlobalConfig instance")

    return EnvMetadata(
        hostname=socket.gethostname(),
        process_id=os.getpid(),
        python_version=_python_version(),
        config_version=cfg.version,
        loaded_at=cfg.loaded_at,
        sources=_redact_sources(cfg.sources),
        vault_available=_vault_available(cfg),
        env_file_count=_count_env_files(cfg.sources),
    )


def _python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def _redact_sources(sources: tuple[str, ...]) -> list[str]:
    redacted: list[str] = []
    for source in sources:
        key, sep, value = source.partition("=")
        if not sep:
            redacted.append(redact_string(source))
            continue
        source_map = redact({key: value})
        safe_value = source_map.get(key, value)
        redacted.append(f"{key}={safe_value}")
    return redacted


def _count_env_files(sources: tuple[str, ...]) -> int:
    for source in sources:
        if not source.startswith("env_files="):
            continue
        _, _, value = source.partition("=")
        return len([p for p in value.split(",") if p.strip()])
    return 0


def _vault_available(config: GlobalConfig) -> bool:
    server = str(config.get("vault.server", "") or "").strip()
    key = str(config.get("vault.key", "") or "").strip()
    if not server:
        return False
    if server.lower() == "mock":
        return bool(config.get("vault.available", True))
    return bool(key)
