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

# cloud_dog_config.compat — Compatibility exports
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Compatibility helpers for staged migration from legacy config
#   managers.
# Related requirements: FR1.21
# Related architecture: CC1.13
#
# Recent changes:
# - 2026-02-18: Added LegacyConfigAdapter export.

"""Compatibility helpers for cloud_dog_config."""

from __future__ import annotations

from cloud_dog_config.compat.legacy_adapter import LegacyConfigAdapter

__all__ = ["LegacyConfigAdapter"]
