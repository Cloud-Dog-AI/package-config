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

# cloud_dog_config — Secret redaction utilities
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Redacts secret values from config output and audit records.
# Related requirements: FR1.15, CS1.1, CS1.2
# Related architecture: CC1.8
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Secret redaction utilities."""

from __future__ import annotations

import re
from typing import Any

REDACTED_VALUE = "***REDACTED***"

DEFAULT_SECRET_KEY_PATTERNS = (
    "secret",
    "password",
    "token",
    "api_key",
    "apikey",
    "key",
    "credential",
)


def redact(data: Any, *, extra_key_patterns: list[str] | None = None) -> Any:
    """Redact secrets in a nested dict/list structure.

    Redaction is key-driven (matches key patterns). Values are replaced with
    `***REDACTED***` regardless of type.
    """
    patterns = list(DEFAULT_SECRET_KEY_PATTERNS)
    if extra_key_patterns:
        patterns.extend(extra_key_patterns)
    compiled = [re.compile(re.escape(p), re.IGNORECASE) for p in patterns]
    return _redact_value(data, compiled)


def redact_string(value: str) -> str:
    """Redact a string if it appears to contain a token/secret."""
    # Keep heuristic minimal: treat Vault tokens, API keys, and obvious secrets as sensitive.
    if not value:
        return value
    lowered = value.lower()
    if "vault" in lowered and "token" in lowered:
        return REDACTED_VALUE
    if value.startswith("sk-") or value.startswith("vk-") or value.startswith("ghp_"):
        return REDACTED_VALUE
    if "-----begin" in lowered:
        return REDACTED_VALUE
    return value


def _redact_value(value: Any, key_patterns: list[re.Pattern[str]]) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            if _key_is_sensitive(k, key_patterns):
                out[k] = REDACTED_VALUE
            else:
                out[k] = _redact_value(v, key_patterns)
        return out
    if isinstance(value, list):
        return [_redact_value(v, key_patterns) for v in value]
    if isinstance(value, str):
        return redact_string(value)
    return value


def _key_is_sensitive(key: str, key_patterns: list[re.Pattern[str]]) -> bool:
    for pat in key_patterns:
        if pat.search(key):
            return True
    return False
