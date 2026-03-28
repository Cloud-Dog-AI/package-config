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

# cloud_dog_config — GlobalConfig snapshot
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Immutable configuration snapshot class. After load/compile/validate,
#   services read config via this object only.
# Related requirements: FR1.11, NF1.3
# Related architecture: CC1.7
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Immutable GlobalConfig snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from types import MappingProxyType
from collections.abc import Mapping


@dataclass(frozen=True, slots=True)
class GlobalConfig:
    """Immutable configuration snapshot.

    Attributes:
        data: The compiled configuration tree (deep-frozen).
        version: Monotonic version identifier for reloads.
        loaded_at: UTC timestamp when loaded.
        sources: Debug-only source descriptors (MUST contain no secrets).
    """

    data: MappingProxyType
    version: str
    loaded_at: datetime
    sources: tuple[str, ...]

    def get(self, path: str, default: Any = None) -> Any:
        """Dot-notation access to nested config values."""
        node: Any = self.data
        if not path:
            return node
        for part in path.split("."):
            if isinstance(node, Mapping):
                if part not in node:  # type: ignore[operator]
                    return default
                node = node[part]  # type: ignore[index]
            else:
                return default
        return node


def freeze_tree(tree: dict[str, Any]) -> MappingProxyType:
    """Deep-freeze a config tree into read-only structures."""
    return _freeze_mapping(tree)


def _freeze_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_mapping(value)
    if isinstance(value, list):
        return tuple(_freeze_value(v) for v in value)
    return value


def _freeze_mapping(value: dict[str, Any]) -> MappingProxyType:
    return MappingProxyType({k: _freeze_value(v) for k, v in value.items()})


def utc_now() -> datetime:
    """UTC timestamp for load/reload."""
    return datetime.now(tz=timezone.utc)
