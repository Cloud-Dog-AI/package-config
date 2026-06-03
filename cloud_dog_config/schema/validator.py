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

# cloud_dog_config — Schema validator
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Optional schema validation for compiled configuration. Supports
#   Pydantic models (if installed) and a minimal dict-based schema.
# Related requirements: FR1.12
# Related architecture: CC1.6
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Schema validation for cloud_dog_config."""

from __future__ import annotations

from typing import Any

from cloud_dog_config.errors import SchemaValidationError


def validate_schema(config: dict[str, Any], schema: Any) -> None:
    """Validate config against schema.

    Args:
        config: Compiled config.
        schema: Either a Pydantic model class or a dict describing required keys.
    """
    if schema is None:
        return

    # Pydantic model class.
    if _is_pydantic_model_class(schema):
        try:
            schema.model_validate(config)  # type: ignore[attr-defined]
            return
        except Exception as exc:  # noqa: BLE001
            raise SchemaValidationError(str(exc)) from exc

    if isinstance(schema, dict):
        _validate_minimal_dict_schema(config, schema)
        return

    raise SchemaValidationError("Unsupported schema type")


def _validate_minimal_dict_schema(config: dict[str, Any], schema: dict[str, Any]) -> None:
    required = schema.get("required", [])
    if required:
        missing = [k for k in required if k not in config]
        if missing:
            raise SchemaValidationError(f"Missing required config keys: {missing}")


def _is_pydantic_model_class(schema: Any) -> bool:
    try:
        from pydantic import BaseModel  # type: ignore
    except Exception:
        return False
    try:
        return isinstance(schema, type) and issubclass(schema, BaseModel)
    except Exception:
        return False
