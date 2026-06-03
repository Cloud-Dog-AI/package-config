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

# cloud_dog_config.transforms — Built-in transform functions
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Built-in post-compile transform exports for reusable config
#   remapping behaviour across services.
# Related requirements: FR1.19
# Related architecture: CC1.11
#
# Recent changes:
# - 2026-03-16: Added resolve_file_keys transform export.

"""Built-in post-compile transform functions for cloud_dog_config."""

# Covers: FR1.19

from __future__ import annotations

from cloud_dog_config.transforms.file_resolver import resolve_file_keys

__all__ = ["resolve_file_keys"]
