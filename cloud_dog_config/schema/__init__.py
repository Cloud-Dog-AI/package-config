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

# cloud_dog_config — Schema validation and secret scanning
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Optional schema validation and defaults.yaml secret scanning.
# Related requirements: FR1.12, FR1.18
# Related architecture: SA1
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Schema and secret scanning helpers for cloud_dog_config."""

from __future__ import annotations

from cloud_dog_config.schema.secret_scanner import scan_for_secrets
from cloud_dog_config.schema.validator import validate_schema

__all__ = ["scan_for_secrets", "validate_schema"]
