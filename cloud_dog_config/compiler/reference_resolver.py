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

# cloud_dog_config — Reference resolver
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Resolves `${ENV_VAR}` and `${ENV_VAR:default}` from os.environ,
#   env files, and the merged config tree.
# Related requirements: FR1.4
# Related architecture: CC1.5
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Reference resolution for the compile phase."""

from __future__ import annotations

from typing import Any

from cloud_dog_config.compiler.evaluator import Unresolved


def resolve_reference(name: str, *, config: dict[str, Any], env: dict[str, Any]) -> Any:
    """Resolve a reference name from env or config.

    Order:
    1. env mapping by exact key
    2. config dotted path
    3. config top-level key
    """
    key = name.strip()
    if not key:
        return Unresolved(name)

    if key in env:
        return env[key]

    # Dotted path access.
    if "." in key:
        v = _get_path(config, key)
        if v is not _MISSING:
            return v

    if key in config:
        return config[key]

    return Unresolved(name)


def resolve_reference_with_default(spec: str, *, config: dict[str, Any], env: dict[str, Any]) -> Any:
    """Resolve NAME:default reference."""
    if ":" not in spec:
        return resolve_reference(spec, config=config, env=env)

    name, default = spec.split(":", 1)
    resolved = resolve_reference(name, config=config, env=env)
    if isinstance(resolved, Unresolved):
        return _parse_default_literal(default.strip())
    return resolved


def _parse_default_literal(text: str) -> Any:
    # Use evaluator literal conventions in a minimal form.
    lower = text.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if lower == "null":
        return None
    # Numbers.
    try:
        if "." in text:
            return float(text)
        return int(text)
    except Exception:
        pass
    # Default to string.
    return text


_MISSING = object()


def _get_path(config: dict[str, Any], path: str) -> Any:
    node: Any = config
    for part in path.split("."):
        if not isinstance(node, dict):
            return _MISSING
        if part not in node:
            return _MISSING
        node = node[part]
    return node
