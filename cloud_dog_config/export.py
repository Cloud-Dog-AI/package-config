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

# cloud_dog_config — Config export utility
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Exports immutable GlobalConfig into a serialisable dictionary,
#   with optional secret redaction for diagnostics.
# Related requirements: FR1.25
# Related architecture: CC1.17
#
# Recent changes:
# - 2026-02-18: Added export_config utility.

"""Config export helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from cloud_dog_config.config import GlobalConfig
from cloud_dog_config.redaction import redact as redact_tree


def export_config(
    config: GlobalConfig,
    redact: bool = True,
    secret_patterns: list[str] | None = None,
) -> dict[str, Any]:
    """Export config to a serialisable dictionary."""
    tree = _to_plain(config.data)
    if not isinstance(tree, dict):
        raise TypeError("GlobalConfig tree must be a mapping")
    if not redact:
        return tree
    return redact_tree(tree, extra_key_patterns=secret_patterns)


def _to_plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_to_plain(v) for v in value]
    return value
