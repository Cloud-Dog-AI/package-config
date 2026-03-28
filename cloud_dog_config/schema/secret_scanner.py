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

# cloud_dog_config — defaults.yaml secret scanner
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Scans defaults.yaml data for likely secrets and fails fast.
# Related requirements: FR1.18, CS1.1
# Related architecture: CC1.8
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Secret scanner for defaults.yaml content."""

from __future__ import annotations

import re
from typing import Any


_VALUE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bsk-[A-Za-z0-9]{10,}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{10,}\b"),
    re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----"),
)

_KEY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"api[_-]?key", re.IGNORECASE),
    re.compile(r"credential", re.IGNORECASE),
)


def scan_for_secrets(data: Any) -> list[str]:
    """Return a list of secret findings for the provided data."""
    findings: list[str] = []
    _scan_value(data, path="$", findings=findings)
    return findings


def _scan_value(value: Any, *, path: str, findings: list[str]) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            if _key_looks_secret(str(k)) and _value_looks_real_secret(v):
                findings.append(f"{path}.{k}")
            _scan_value(v, path=f"{path}.{k}", findings=findings)
        return
    if isinstance(value, list):
        for i, v in enumerate(value):
            _scan_value(v, path=f"{path}[{i}]", findings=findings)
        return
    if _value_looks_real_secret(value):
        # Flag obvious secrets even without a suspicious key.
        findings.append(path)


def _key_looks_secret(key: str) -> bool:
    return any(p.search(key) for p in _KEY_PATTERNS)


def _value_looks_real_secret(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    v = value.strip()
    if not v:
        return False
    # Allow placeholders and blank defaults.
    if "${" in v:
        return False
    if v in ("", "changeme", "change-me", "example", "test"):
        return False
    return any(p.search(v) for p in _VALUE_PATTERNS)
