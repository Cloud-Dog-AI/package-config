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

"""Vault discovery helpers for IT tests.

These tests run against a real Vault using credentials from `--env` files.
The integration environment may provide read-only tokens and may not include
pre-provisioned secrets under a fixed prefix. To keep tests deterministic and
standards-compliant (no hardcoded values), we discover an existing readable
secret via KV v2 list+read and then assert our resolver returns the same data.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class VaultEnv:
    """Vault environment settings loaded from env files."""

    addr: str
    token: str
    mount_point: str

    @property
    def mount(self) -> str:
        mount, _prefix = split_mount_point(self.mount_point)
        return mount

    @property
    def prefix(self) -> str:
        _mount, prefix = split_mount_point(self.mount_point)
        return prefix


def split_mount_point(mount_point: str) -> tuple[str, str]:
    """Split `VAULT_MOUNT_POINT` into mount and optional prefix."""
    cleaned = mount_point.strip().strip("/")
    parts = cleaned.split("/", 1) if cleaned else [""]
    mount = parts[0] if parts else ""
    prefix = parts[1] if len(parts) == 2 else ""
    return mount, prefix


def make_client(*, addr: str, token: str) -> Any:
    """Create an hvac client (hvac is an optional dependency of cloud_dog_config)."""
    import hvac

    return hvac.Client(url=addr, token=token)


def _list_kv_v2(client: Any, *, mount: str, path: str) -> list[str] | None:
    try:
        resp = client.secrets.kv.v2.list_secrets(mount_point=mount, path=path)
        keys = resp.get("data", {}).get("keys", [])
        return [str(k) for k in keys]
    except Exception:
        return None


def _read_kv_v2_dict(client: Any, *, mount: str, path: str) -> dict[str, Any] | None:
    try:
        resp = client.secrets.kv.v2.read_secret_version(
            mount_point=mount,
            path=path,
            raise_on_deleted_version=True,
        )
        data = (resp or {}).get("data", {}).get("data", None)
        if isinstance(data, dict) and data:
            return dict(data)
        return None
    except Exception:
        return None


def iter_kv_v2_leaf_paths(
    client: Any,
    *,
    mount: str,
    start_path: str = "",
    max_nodes: int = 500,
) -> Iterable[str]:
    """Iterate candidate KV v2 leaf secret paths by BFS using list_secrets."""
    start = start_path.strip().strip("/")
    queue: deque[str] = deque([start])
    visited = 0

    while queue and visited < max_nodes:
        cur = queue.popleft()
        visited += 1

        keys = _list_kv_v2(client, mount=mount, path=cur)
        if not keys:
            continue

        for key in keys:
            if key.endswith("/"):
                nxt = "/".join([p for p in (cur, key[:-1]) if p])
                queue.append(nxt)
                continue
            leaf = "/".join([p for p in (cur, key) if p])
            yield leaf


@dataclass(frozen=True, slots=True)
class DiscoveredSecret:
    """A discovered readable secret dict at a KV v2 path."""

    path: str
    data: dict[str, Any]

    @property
    def path_parts(self) -> list[str]:
        return [p for p in self.path.strip("/").split("/") if p]


def discover_bundle_secret(
    client: Any,
    *,
    mount: str,
    start_path: str = "",
    min_keys: int = 1,
) -> DiscoveredSecret | None:
    """Find the first readable secret with at least `min_keys` fields."""
    for leaf in iter_kv_v2_leaf_paths(client, mount=mount, start_path=start_path):
        data = _read_kv_v2_dict(client, mount=mount, path=leaf)
        if data is None:
            continue
        if len(data) >= min_keys:
            return DiscoveredSecret(path=leaf, data=data)
    return None


@dataclass(frozen=True, slots=True)
class DiscoveredScalar:
    """A discovered secret where the leaf path segment is also a key in the secret data."""

    path: str
    data: dict[str, Any]
    leaf_key: str

    @property
    def leaf_value(self) -> Any:
        return self.data[self.leaf_key]

    @property
    def path_parts(self) -> list[str]:
        return [p for p in self.path.strip("/").split("/") if p]


def discover_scalar_secret(
    client: Any,
    *,
    mount: str,
    start_path: str = "",
) -> DiscoveredScalar | None:
    """Find a readable secret where the secret contains a field matching its leaf path name."""
    for leaf in iter_kv_v2_leaf_paths(client, mount=mount, start_path=start_path):
        parts = [p for p in leaf.strip("/").split("/") if p]
        if not parts:
            continue
        leaf_key = parts[-1]
        data = _read_kv_v2_dict(client, mount=mount, path=leaf)
        if data is None:
            continue
        if leaf_key in data:
            return DiscoveredScalar(path=leaf, data=data, leaf_key=leaf_key)
    return None
