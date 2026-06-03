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

# cloud_dog_config — YAML loader
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: YAML loading helper using yaml.safe_load. Missing config.yaml is
#   treated as empty; invalid YAML raises.
# Related requirements: FR1.3
# Related architecture: CC1.3
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""YAML loading helpers for cloud_dog_config."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from cloud_dog_config.errors import YAMLLoadError


def load_yaml(path: str, *, missing_ok: bool = False) -> dict[str, Any]:
    """Load a YAML file as a dictionary.

    Args:
        path: Path to YAML file.
        missing_ok: If True, missing file returns {}.

    Returns:
        Parsed YAML dict (or {}).
    """
    p = Path(path)
    if not p.exists():
        if missing_ok:
            return {}
        raise YAMLLoadError(f"YAML file not found: {path}")

    try:
        raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 (surface as YAMLLoadError)
        raise YAMLLoadError(f"Invalid YAML in {path}: {exc}") from exc

    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise YAMLLoadError(f"YAML root must be a mapping in {path}")
    return raw
