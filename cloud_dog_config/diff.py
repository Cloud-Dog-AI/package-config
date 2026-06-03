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

# cloud_dog_config — Structured config diff
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Computes structured, optionally redacted diffs between config
#   snapshots for audit and diagnostics.
# Related requirements: FR1.24
# Related architecture: CC1.16
#
# Recent changes:
# - 2026-02-18: Added ConfigChange dataclass and config_diff utility.

"""Structured config diff utilities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from cloud_dog_config.config import GlobalConfig
from cloud_dog_config.errors import ConfigError
from cloud_dog_config.redaction import DEFAULT_SECRET_KEY_PATTERNS, REDACTED_VALUE, redact, redact_string


@dataclass(frozen=True, slots=True)
class ConfigChange:
    """Represents one config tree change."""

    path: str
    change_type: str
    old_value: Any
    new_value: Any


def config_diff(
    old: GlobalConfig | dict[str, Any], new: GlobalConfig | dict[str, Any], redact: bool = True
) -> list[ConfigChange]:
    """Compute a structured diff between config snapshots."""
    old_tree = _normalise_input(old)
    new_tree = _normalise_input(new)

    changes: list[ConfigChange] = []
    _diff(old_tree, new_tree, path="", changes=changes, redact_values=redact)
    return changes


def _normalise_input(value: GlobalConfig | dict[str, Any]) -> dict[str, Any]:
    if isinstance(value, GlobalConfig):
        tree = _to_plain(value.data)
    elif isinstance(value, dict):
        tree = _to_plain(value)
    else:
        raise ConfigError(f"Unsupported diff input type: {type(value).__name__}")

    if not isinstance(tree, dict):
        raise ConfigError("Config diff input must be a mapping")
    return tree


def _diff(old: Any, new: Any, *, path: str, changes: list[ConfigChange], redact_values: bool) -> None:
    if isinstance(old, dict) and isinstance(new, dict):
        old_keys = set(old.keys())
        new_keys = set(new.keys())
        for key in sorted(old_keys - new_keys):
            key_path = _append_path(path, key)
            changes.append(
                ConfigChange(
                    path=key_path,
                    change_type="removed",
                    old_value=_serialise_value(key_path, old[key], redact_values),
                    new_value=None,
                )
            )
        for key in sorted(new_keys - old_keys):
            key_path = _append_path(path, key)
            changes.append(
                ConfigChange(
                    path=key_path,
                    change_type="added",
                    old_value=None,
                    new_value=_serialise_value(key_path, new[key], redact_values),
                )
            )
        for key in sorted(old_keys & new_keys):
            _diff(old[key], new[key], path=_append_path(path, key), changes=changes, redact_values=redact_values)
        return

    if isinstance(old, list) and isinstance(new, list):
        max_len = max(len(old), len(new))
        for idx in range(max_len):
            idx_path = f"{path}[{idx}]" if path else f"[{idx}]"
            if idx >= len(old):
                changes.append(
                    ConfigChange(
                        path=idx_path,
                        change_type="added",
                        old_value=None,
                        new_value=_serialise_value(idx_path, new[idx], redact_values),
                    )
                )
            elif idx >= len(new):
                changes.append(
                    ConfigChange(
                        path=idx_path,
                        change_type="removed",
                        old_value=_serialise_value(idx_path, old[idx], redact_values),
                        new_value=None,
                    )
                )
            else:
                _diff(old[idx], new[idx], path=idx_path, changes=changes, redact_values=redact_values)
        return

    if old != new:
        key_path = path or "$"
        changes.append(
            ConfigChange(
                path=key_path,
                change_type="modified",
                old_value=_serialise_value(key_path, old, redact_values),
                new_value=_serialise_value(key_path, new, redact_values),
            )
        )


def _append_path(base: str, key: str) -> str:
    return f"{base}.{key}" if base else key


def _serialise_value(path: str, value: Any, redact_values: bool) -> Any:
    plain = _to_plain(value)
    if not redact_values:
        return plain

    if _path_is_sensitive(path):
        return REDACTED_VALUE

    if isinstance(plain, dict) or isinstance(plain, list):
        return redact(plain)
    if isinstance(plain, str):
        return redact_string(plain)
    return plain


def _path_is_sensitive(path: str) -> bool:
    cleaned = path.replace("[", ".").replace("]", "")
    parts = [p.lower() for p in cleaned.split(".") if p and p != "$"]
    for part in parts:
        for pattern in DEFAULT_SECRET_KEY_PATTERNS:
            if pattern.lower() in part:
                return True
    return False


def _to_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_to_plain(v) for v in value]
    return value
