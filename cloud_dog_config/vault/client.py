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

# cloud_dog_config — Vault client (hvac wrapper)
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Thin hvac-based Vault client for reading config secrets from
#   `secret/<project>/<path>`.
# Related requirements: FR1.6, CS1.2
# Related architecture: CC1.6
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Thin Vault client wrapper (optional dependency on hvac)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cloud_dog_config.errors import VaultError


@dataclass(frozen=True, slots=True)
class VaultConnectionConfig:
    """Vault connection configuration."""

    server: str
    token: str
    timeout_seconds: float = 5.0
    mount_point: str = ""


class VaultClient:
    """Thin Vault client wrapper around hvac (if installed)."""

    def __init__(self, config: VaultConnectionConfig) -> None:
        self._config = config
        self._client = _create_hvac_client(config)

    def read(self, path: str) -> dict[str, Any] | str | None:
        """Read a Vault secret path.

        Args:
            path: Path like `secret/<project>/<path>`.

        Returns:
            Secret dict/object, scalar string, or None if missing.
        """
        try:
            # hvac kv v2 uses .secrets.kv.v2.read_secret_version. We support both by probing.
            if hasattr(self._client.secrets, "kv") and hasattr(self._client.secrets.kv, "v2"):
                mount, secret_path = _split_mount(path, mount_override=self._config.mount_point)
                resp = self._client.secrets.kv.v2.read_secret_version(
                    path=secret_path,
                    mount_point=mount,
                    raise_on_deleted_version=True,
                )
                data = resp.get("data", {}).get("data", {})
                if isinstance(data, dict):
                    return data
                if data is None:
                    return None
                return str(data)

            resp = self._client.read(path)
            if not resp:
                return None
            data = resp.get("data")
            if isinstance(data, dict):
                # KV v1 returns {data:{...}}.
                return data
            if data is None:
                return None
            return str(data)
        except Exception as exc:  # noqa: BLE001 (wrapped)
            raise VaultError("Vault read failed") from exc


def _create_hvac_client(config: VaultConnectionConfig) -> Any:
    try:
        import hvac  # type: ignore
    except Exception as exc:  # noqa: BLE001 (dependency missing)
        raise VaultError("hvac is not installed (install cloud-dog-config[vault])") from exc

    client = hvac.Client(url=config.server, token=config.token, timeout=config.timeout_seconds)
    return client


def _split_mount(path: str, *, mount_override: str = "") -> tuple[str, str]:
    """Split path into KV mount and secret path for hvac v2 API.

    If mount_override is provided, it may include slashes. In that case:
    - the first segment is treated as the mount point
    - the remaining segments are treated as a prefix under the mount
    - the requested `path` has its first segment removed and appended to the prefix
    """
    cleaned = path.strip().strip("/")
    if mount_override:
        mount_parts = mount_override.strip().strip("/").split("/")
        mount = mount_parts[0]
        prefix = "/".join(mount_parts[1:])
        # Remove the first segment of requested path (e.g., "secret/...")
        req_parts = cleaned.split("/", 1)
        req_rest = req_parts[1] if len(req_parts) == 2 else ""
        joined = "/".join([p for p in (prefix, req_rest) if p])
        return mount, joined

    parts = cleaned.split("/", 1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]
