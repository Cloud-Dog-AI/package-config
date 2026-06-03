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

# cloud_dog_config — Mock Vault client
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: In-memory mock Vault client used for unit/system tests.
# Related requirements: FR1.6
# Related architecture: CC1.6
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Mock Vault client for tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MockVaultClient:
    """Simple in-memory Vault client."""

    data: dict[str, Any]
    available: bool = True

    def read(self, path: str) -> dict[str, Any] | str | None:
        """Handle read."""
        if not self.available:
            raise ConnectionError("Vault unavailable")
        if path not in self.data:
            return None
        return self.data[path]
