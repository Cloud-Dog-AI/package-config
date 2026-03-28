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

# cloud_dog_config — Post-compile transform hooks
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Chains deterministic transform hooks across the compiled config
#   tree before schema validation/freeze.
# Related requirements: FR1.19
# Related architecture: CC1.11
#
# Recent changes:
# - 2026-02-18: Added post-compile transform chain support.

"""Post-compile config transforms."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from cloud_dog_config.errors import ConfigTransformError


def apply_transforms(
    config_tree: dict[str, Any],
    transforms: list[Callable[[dict[str, Any]], dict[str, Any]]],
) -> dict[str, Any]:
    """Apply post-compile transform functions in order.

    Args:
        config_tree: Compiled config tree.
        transforms: Ordered list of transform callables.

    Returns:
        Transformed config tree.

    Raises:
        ConfigTransformError: If any transform fails or returns a non-dict tree.
    """
    current = config_tree
    for transform in transforms:
        transform_name = _transform_name(transform)
        try:
            transformed = transform(current)
        except Exception as exc:  # noqa: BLE001
            raise ConfigTransformError(f"Transform failed in {transform_name}: {exc}") from exc
        if not isinstance(transformed, dict):
            raise ConfigTransformError(
                f"Transform failed in {transform_name}: expected dict return, got {type(transformed).__name__}"
            )
        current = transformed
    return current


def _transform_name(transform: Callable[[dict[str, Any]], dict[str, Any]]) -> str:
    name = getattr(transform, "__name__", "")
    if isinstance(name, str) and name:
        return name
    return transform.__class__.__name__
