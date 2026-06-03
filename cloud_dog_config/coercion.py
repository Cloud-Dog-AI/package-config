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

# cloud_dog_config — Type coercion
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Coerce env string values to typed values using safe heuristics
#   (bool/int/float/JSON) and optional schema hints.
# Related requirements: FR1.10
# Related architecture: CC1.9
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Type coercion for env values."""

from __future__ import annotations

import json
from typing import Any


def coerce(value: str, hint: type | None = None) -> Any:
    """Coerce a string value into a typed value."""
    if hint is not None:
        return _coerce_with_hint(value, hint)
    return _coerce_heuristic(value)


def _coerce_with_hint(value: str, hint: type) -> Any:
    v = value.strip()
    if hint is bool:
        return _parse_bool(v)
    if hint is int:
        return int(v)
    if hint is float:
        return float(v)
    if hint is str:
        return value
    # Fallback to heuristic for unknown hints.
    return _coerce_heuristic(value)


def _coerce_heuristic(value: str) -> Any:
    v = value.strip()
    lower = v.lower()
    if lower in ("true", "false"):
        return lower == "true"
    # Int then float.
    if _looks_int(v):
        try:
            return int(v)
        except Exception:
            pass
    if _looks_float(v):
        try:
            return float(v)
        except Exception:
            pass

    # JSON object/array literals.
    if (v.startswith("{") and v.endswith("}")) or (v.startswith("[") and v.endswith("]")):
        try:
            return json.loads(v)
        except Exception:
            pass

    if lower == "null":
        return None

    return value


def _parse_bool(v: str) -> bool:
    lower = v.strip().lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    raise ValueError(f"Invalid bool value: {v!r}")


def _looks_int(v: str) -> bool:
    s = v.strip()
    if not s:
        return False
    if s[0] in "+-":
        s = s[1:]
    return s.isdigit()


def _looks_float(v: str) -> bool:
    s = v.strip()
    if not s:
        return False
    if s.count(".") != 1:
        return False
    left, right = s.split(".", 1)
    if left and left[0] in "+-":
        left = left[1:]
    if left and not left.isdigit():
        return False
    return right.isdigit()
