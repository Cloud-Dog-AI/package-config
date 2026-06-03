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

# cloud_dog_config — Pytest plugin for --env enforcement
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Adds `--env` option and enforces it for all test runs. Loads env
#   files into os.environ without overwriting pre-set values.
# Related requirements: FR1.17
# Related architecture: SA1
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Pytest plugin enforcing `--env` for cloud_dog_config tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Handle pytest addoption."""
    parser.addoption(
        "--env",
        action="append",
        default=None,
        help="Path to env file(s) to load (repeatable).",
    )


@pytest.fixture(scope="session", autouse=True)
def _require_env(request: pytest.FixtureRequest) -> None:
    env_args = request.config.getoption("--env")
    if not env_args:
        pytest.fail("Missing required --env argument (e.g. --env tests/env-UT)")
    env_files: list[str] = []
    for arg in env_args:
        env_files.extend(_split_env_arg(arg))
    for path in env_files:
        _load_env_file(path)


def _split_env_arg(arg: str) -> list[str]:
    # Allow comma-separated convenience.
    return [p.strip() for p in arg.split(",") if p.strip()]


def _load_env_file(path: str) -> None:
    p = Path(path)
    if not p.exists():
        pytest.fail(f"Env file not found: {path}")
    for raw_line in p.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            pytest.fail(f"Invalid env file line (expected KEY=value): {raw_line!r}")
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if not key:
            pytest.fail(f"Invalid env file line (empty key): {raw_line!r}")
        os.environ.setdefault(key, value)
