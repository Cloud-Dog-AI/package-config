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

# cloud_dog_config.compat — Legacy config adapter
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Read-only adapter exposing legacy mutable-looking access patterns
#   over immutable GlobalConfig.
# Related requirements: FR1.21
# Related architecture: CC1.13
#
# Recent changes:
# - 2026-02-18: Added LegacyConfigAdapter for staged migration.

"""Legacy compatibility adapter for GlobalConfig."""

from __future__ import annotations

import warnings
from collections.abc import Mapping
from typing import Any

from cloud_dog_config.config import GlobalConfig
from cloud_dog_config.errors import ConfigError, ConfigImmutableError

_MISSING = object()


class LegacyConfigAdapter:
    """Read-only adapter with legacy `get` and item-access ergonomics."""

    def __init__(self, config: GlobalConfig, warn_on_access: bool = True) -> None:
        self._config = config
        self._warn_on_access = warn_on_access

    def get(self, path: str, default: Any = None) -> Any:
        """Read value from GlobalConfig using dotted path access."""
        self._warn(path)
        return self._config.get(path, default)

    def __getitem__(self, key: str) -> Any:
        """Read value via item access, mirroring `get` behaviour."""
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Reject mutation to preserve GlobalConfig immutability."""
        raise ConfigImmutableError("Config is immutable; use load_config() to reload.")

    def as_dict(self, path: str | None = None) -> dict[str, Any]:
        """Return a plain dictionary snapshot of a config subtree."""
        self._warn(path)
        if path is None:
            value: Any = self._config.data
        else:
            value = self._config.get(path, _MISSING)
            if value is _MISSING:
                return {}

        plain = _to_plain(value)
        if not isinstance(plain, dict):
            raise ConfigError(f"Config path is not a mapping: {path}")
        return plain

    def _warn(self, path: str | None) -> None:
        if not self._warn_on_access:
            return
        suffix = f" for path '{path}'" if path else ""
        warnings.warn(
            "LegacyConfigAdapter is deprecated; migrate to GlobalConfig access APIs" + suffix,
            DeprecationWarning,
            stacklevel=3,
        )


def _to_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_to_plain(v) for v in value]
    return value
