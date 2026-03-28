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

# cloud_dog_config — Circular reference detection
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Detects circular config reference chains during compile.
# Related requirements: FR1.9
# Related architecture: CC1.5
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Circular reference detection utilities."""

from __future__ import annotations

from dataclasses import dataclass, field

from cloud_dog_config.errors import CircularReferenceError


@dataclass
class CircularDetector:
    """Tracks active resolution stack to detect circular references."""

    stack: list[str] = field(default_factory=list)
    active: set[str] = field(default_factory=set)

    def enter(self, path: str) -> None:
        """Handle enter."""
        if path in self.active:
            cycle = " -> ".join(self.stack + [path])
            raise CircularReferenceError(f"Circular reference detected: {cycle}")
        self.active.add(path)
        self.stack.append(path)

    def exit(self, path: str) -> None:
        """Handle exit."""
        if self.stack and self.stack[-1] == path:
            self.stack.pop()
        self.active.discard(path)
