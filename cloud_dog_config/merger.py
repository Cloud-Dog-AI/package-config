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

# cloud_dog_config — Deep-merge engine
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Deterministic, side-effect-free deep merge for configuration
#   trees: dicts merge recursively, lists replace, scalars overwrite.
# Related requirements: FR1.3
# Related architecture: CC1.4
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Deep-merge semantics for configuration trees."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def deep_merge(base: Any, overlay: Any) -> Any:
    """Deep-merge overlay onto base using PS-80 semantics.

    Rules:
    - dict + dict: merge recursively by key
    - list: overlay replaces base entirely
    - scalar: overlay wins
    - type mismatch: overlay wins

    This function is side-effect-free: it does not mutate inputs.
    """
    if isinstance(base, Mapping) and isinstance(overlay, Mapping):
        merged: dict[str, Any] = {}
        for k in base.keys() | overlay.keys():
            if k in base and k in overlay:
                merged[k] = deep_merge(base[k], overlay[k])
            elif k in overlay:
                merged[k] = _clone(overlay[k])
            else:
                merged[k] = _clone(base[k])
        return merged

    if isinstance(overlay, list):
        return [_clone(v) for v in overlay]

    # Any non-mapping value (including list/scalar) is overwritten by overlay.
    return _clone(overlay)


def _clone(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _clone(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clone(v) for v in value]
    return value
