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

# cloud_dog_config — Env naming convention
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Helpers to map APPNAME__level1__level2 env vars to dotted config
#   paths and back.
# Related requirements: FR1.16
# Related architecture: CC1.10
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Env var naming convention helpers."""

from __future__ import annotations


def env_to_path(env_key: str, *, prefix: str | None = None) -> str | None:
    """Convert an env var name to a dotted config path.

    Example: CLOUD_DOG__LLM__MODEL -> llm.model
    """
    key = env_key.strip()
    if not key or "__" not in key:
        return None

    parts = key.split("__")
    if prefix:
        if parts[0] != prefix:
            return None
        parts = parts[1:]

    if not parts:
        return None
    return ".".join(p.lower() for p in parts if p)


def path_to_env(path: str, *, prefix: str) -> str:
    """Convert a dotted config path to an env var name with prefix."""
    cleaned = path.strip().strip(".")
    if not cleaned:
        raise ValueError("Path must be non-empty")
    parts = [p.upper() for p in cleaned.split(".") if p]
    return "__".join([prefix] + parts)
