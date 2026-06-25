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

"""Shared test configuration for cloud_dog_config."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

import pytest

pytest_plugins = ["pytester"]

_TIER_TOKENS = {"UT", "ST", "IT", "AT", "QT", "PT", "CT"}


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the shared --env option used across platform packages."""
    try:
        parser.addoption(
            "--env",
            action="append",
            default=[],
            help="Env tier token(s) or env file path(s); repeatable and comma-separated.",
        )
    except ValueError:
        # Another plugin may already have registered --env in this process.
        return


def _normalise_env_files(raw: list[str] | str | None) -> list[Path]:
    """Expand tier tokens (UT/ST/IT/AT/QT/PT/CT) into tests/env-* files."""
    values: list[str]
    if raw is None:
        values = []
    elif isinstance(raw, str):
        values = [raw]
    else:
        values = list(raw)

    tests_dir = Path(__file__).resolve().parent
    out: list[Path] = []
    for value in values:
        for part in value.split(","):
            token = part.strip()
            if not token:
                continue
            upper = token.upper()
            if upper in _TIER_TOKENS:
                tier_file = tests_dir / f"env-{upper}"
                if tier_file.is_file():
                    out.append(tier_file)
            else:
                out.append(Path(token))
    return out


def _load_env_file(path: Path, *, locked: set[str]) -> dict[str, str]:
    """Parse env file with KEY=value lines, keeping os.environ precedence."""
    if not path.is_file():
        raise pytest.UsageError(f"Env file not found: {path}")

    loaded: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise pytest.UsageError(f"Invalid env line in {path}: {raw_line}")
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            raise pytest.UsageError(f"Invalid env line in {path}: {raw_line}")
        if key in locked:
            continue
        loaded[key] = value.strip()
    return loaded


@pytest.fixture(scope="session", autouse=True)
def _require_and_load_env(request: pytest.FixtureRequest) -> None:
    """Require --env and load env file values before tests execute."""
    env_files = _normalise_env_files(request.config.getoption("env"))
    if not env_files:
        raise pytest.UsageError("Missing required --env argument (for example: --env UT).")

    locked = set(os.environ.keys())
    merged: dict[str, str] = {}
    for env_file in env_files:
        merged.update(_load_env_file(env_file, locked=locked))
    os.environ.update(merged)


@pytest.fixture(autouse=True)
def _reset_global_config_state() -> Generator[None, None, None]:
    """Reset module-level GlobalConfig state between tests."""
    from cloud_dog_config import loader

    loader._CURRENT = None  # type: ignore[attr-defined]
    loader._VERSION_COUNTER = 0  # type: ignore[attr-defined]
    yield
    loader._CURRENT = None  # type: ignore[attr-defined]
    loader._VERSION_COUNTER = 0  # type: ignore[attr-defined]
