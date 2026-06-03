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

# cloud_dog_config — Multi-profile resolver
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Resolves named profile config trees with fallback support.
# Related requirements: FR1.22
# Related architecture: CC1.14
#
# Recent changes:
# - 2026-02-18: Added resolve_profile helper.

"""Named profile resolution helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from cloud_dog_config.config import GlobalConfig
from cloud_dog_config.errors import ConfigError

_MISSING = object()


def resolve_profile(
    config: GlobalConfig,
    profile_name: str,
    base_path: str = "",
    fallback: str = "default",
) -> dict[str, Any]:
    """Resolve a profile config subtree, with fallback if absent."""
    requested_path = _join_path(base_path, profile_name)
    fallback_path = _join_path(base_path, fallback)

    candidate = config.get(requested_path, _MISSING)
    if candidate is _MISSING:
        candidate = config.get(fallback_path, _MISSING)
        if candidate is _MISSING:
            raise ConfigError(
                f"Profile '{profile_name}' not found at '{requested_path}' and fallback '{fallback}' is absent"
            )

    if not isinstance(candidate, Mapping):
        raise ConfigError(f"Resolved profile at '{requested_path}' is not a mapping")

    plain = _to_plain(candidate)
    if not isinstance(plain, dict):
        raise ConfigError(f"Resolved profile at '{requested_path}' is not serialisable as a dict")
    return plain


def _join_path(base_path: str, leaf: str) -> str:
    base = base_path.strip(".")
    leaf_clean = leaf.strip(".")
    if not base:
        return leaf_clean
    if not leaf_clean:
        return base
    return f"{base}.{leaf_clean}"


def _to_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_to_plain(v) for v in value]
    return value
