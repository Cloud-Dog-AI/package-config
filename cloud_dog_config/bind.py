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

# cloud_dog_config — Typed model bind utility
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Binds a config subtree at a dotted path into a typed Pydantic
#   model instance.
# Related requirements: FR1.23
# Related architecture: CC1.15
#
# Recent changes:
# - 2026-02-18: Added bind_model helper and validation error mapping.

"""Typed model bind helpers for config subtrees."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from cloud_dog_config.config import GlobalConfig
from cloud_dog_config.errors import ConfigBindError

_MISSING = object()


def bind_model(config: GlobalConfig, path: str, model_cls: type) -> Any:
    """Bind a config subtree to a typed Pydantic model."""
    validation_error_cls = _get_pydantic_validation_error()

    subtree = config.get(path, _MISSING)
    if subtree is _MISSING:
        raise ConfigBindError(f"Config path not found: {path}")
    if not isinstance(subtree, Mapping):
        raise ConfigBindError(f"Config path does not contain an object: {path}")

    payload = _to_plain(subtree)
    try:
        return model_cls(**payload)
    except validation_error_cls as exc:  # type: ignore[misc]
        raise ConfigBindError(_format_validation_error(path, exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise ConfigBindError(f"Model bind failed at '{path}': {exc}") from exc


def _get_pydantic_validation_error() -> type[Exception]:
    try:
        from pydantic import ValidationError  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "bind_model requires optional dependency 'pydantic'. Install with: pip install 'cloud-dog-config[schema]'"
        ) from exc
    return ValidationError


def _format_validation_error(path: str, exc: Exception) -> str:
    details: list[str] = []
    errors_func = getattr(exc, "errors", None)
    if callable(errors_func):
        try:
            for item in errors_func():
                if not isinstance(item, dict):
                    continue
                loc_raw = item.get("loc", ())
                if isinstance(loc_raw, tuple):
                    loc = ".".join(str(p) for p in loc_raw)
                elif isinstance(loc_raw, list):
                    loc = ".".join(str(p) for p in loc_raw)
                else:
                    loc = str(loc_raw)
                msg = str(item.get("msg", "validation error"))
                details.append(f"{loc}: {msg}" if loc else msg)
        except Exception:
            details = []

    if not details:
        details.append(str(exc))

    joined = "; ".join(details)
    return f"Model bind validation failed at '{path}': {joined}"


def _to_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_to_plain(v) for v in value]
    return value
