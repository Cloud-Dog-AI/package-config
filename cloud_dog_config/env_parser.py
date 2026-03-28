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

# cloud_dog_config — Env-file parser
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Parses platform KEY=value env files with # comments.
# Related requirements: FR1.2
# Related architecture: CC1.2
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Env-file parser for cloud_dog_config."""

from __future__ import annotations

from pathlib import Path

from cloud_dog_config.errors import EnvFileError


def parse_env_file(path: str) -> dict[str, str]:
    """Parse an env file (KEY=value) into a dict of strings."""
    p = Path(path)
    if not p.exists():
        raise EnvFileError(f"Env file not found: {path}")

    result: dict[str, str] = {}
    for raw_line in p.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            raise EnvFileError("Env files MUST NOT use 'export' prefix")

        # Strip trailing comment, but only if preceded by whitespace.
        # This preserves values containing '#', e.g. passwords.
        hash_index = _comment_hash_index(line)
        if hash_index is not None:
            line = line[:hash_index].rstrip()
        if not line:
            continue

        if "=" not in line:
            raise EnvFileError(f"Invalid env line (expected KEY=value): {raw_line!r}")

        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if not key:
            raise EnvFileError(f"Invalid env line (empty key): {raw_line!r}")

        # Remove simple surrounding quotes.
        if len(value) >= 2 and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
            value = value[1:-1]

        result[key] = value

    return result


def parse_env_files(paths: list[str]) -> dict[str, str]:
    """Parse multiple env files, later files overriding earlier ones."""
    merged: dict[str, str] = {}
    for p in paths:
        merged.update(parse_env_file(p))
    return merged


def _comment_hash_index(line: str) -> int | None:
    # Platform convention: comments start with '#' when preceded by whitespace.
    for i, ch in enumerate(line):
        if ch == "#":
            if i == 0:
                return 0
            if line[i - 1].isspace():
                return i
    return None
