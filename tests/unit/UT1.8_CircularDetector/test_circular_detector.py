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

"""UT1.8: Circular Detector — circular reference detection tests."""

from __future__ import annotations

import pytest

from cloud_dog_config.compiler.circular_detector import CircularDetector
from cloud_dog_config.errors import CircularReferenceError


class TestCircularDetector:
    def test_direct_cycle_detected(self) -> None:
        d = CircularDetector()
        d.enter("a")
        with pytest.raises(CircularReferenceError):
            d.enter("a")

    def test_indirect_cycle_detected(self) -> None:
        d = CircularDetector()
        d.enter("a")
        d.enter("b")
        with pytest.raises(CircularReferenceError):
            d.enter("a")
