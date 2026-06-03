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

# cloud_dog_config — CLI helpers
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Helpers for working with `--env` style arguments in services and
#   tests.
# Related requirements: FR1.2, FR1.17
# Related architecture: SA1
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""CLI helpers for cloud_dog_config."""

from __future__ import annotations

import os
from collections.abc import Sequence


def normalise_env_files(env_files: list[str] | None) -> list[str]:
    """Normalise env file arguments into a concrete list."""
    if not env_files:
        return []
    out: list[str] = []
    for item in env_files:
        if not item:
            continue
        out.extend([p.strip() for p in item.split(",") if p.strip()])
    return out


def resolve_runtime_env_files(
    explicit: str | Sequence[str] | None = None,
    *,
    env_var: str = "CLOUD_DOG_ENV_FILES",
) -> list[str]:
    """Resolve runtime env-file inputs from explicit args or the standard env pointer."""
    if explicit is None:
        raw = os.environ.get(env_var, "").strip()
        return normalise_env_files([raw] if raw else None)
    if isinstance(explicit, str):
        return normalise_env_files([explicit])
    return normalise_env_files([str(item) for item in explicit if str(item).strip()])
