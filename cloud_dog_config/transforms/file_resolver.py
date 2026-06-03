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

# cloud_dog_config.transforms.file_resolver — Resolve *_filename keys
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Built-in post-compile transform that resolves sibling
#   *_filename metadata keys to UTF-8 file content and removes metadata keys.
# Related requirements: FR1.19
# Related architecture: CC1.11
#
# Recent changes:
# - 2026-03-16: Added built-in resolve_file_keys transform.

"""Built-in transform: resolve ``*_filename`` keys to file content."""

# Covers: FR1.19

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def resolve_file_keys(config_tree: dict[str, Any]) -> dict[str, Any]:
    """Resolve sibling ``*_filename`` keys recursively and remove metadata keys.

    For each key ``K`` where ``K_filename`` exists in the same mapping:
    - if ``K_filename`` is a non-empty string and points to a readable file,
      replace ``K`` with the file content.
    - otherwise, keep ``K`` unchanged.
    - remove ``K_filename`` from the mapping.
    """
    return _resolve_node(config_tree)


def _resolve_node(node: dict[str, Any]) -> dict[str, Any]:
    filename_keys: list[tuple[str, str]] = []
    for key in list(node.keys()):
        if key.endswith("_filename"):
            base_key = key[: -len("_filename")]
            if base_key and base_key in node:
                filename_keys.append((base_key, key))

    for base_key, filename_key in filename_keys:
        filename_value = node.get(filename_key)
        if isinstance(filename_value, str) and filename_value.strip():
            file_path = Path(filename_value.strip())
            if file_path.is_file():
                try:
                    node[base_key] = file_path.read_text(encoding="utf-8")
                    logger.debug(
                        "Resolved %s from file: %s (%d chars)",
                        base_key,
                        filename_value,
                        len(str(node[base_key])),
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Failed to read file for %s (%s): %s",
                        base_key,
                        filename_value,
                        exc,
                    )
            else:
                logger.debug(
                    "File for %s not found: %s; using inline value",
                    base_key,
                    filename_value,
                )
        del node[filename_key]

    for key, value in list(node.items()):
        node[key] = _resolve_value(value)

    return node


def _resolve_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _resolve_node(value)
    if isinstance(value, list):
        return [_resolve_value(item) for item in value]
    return value
