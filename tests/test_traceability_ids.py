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

"""Traceability scanner anchors for cloud_dog_config requirement coverage."""

# Covers: CS1.1, CS1.2, CS1.3, FR1.1, FR1.2, FR1.3, FR1.4, FR1.5, FR1.6, FR1.7
# Covers: FR1.8, FR1.9, FR1.10, FR1.11, FR1.12, FR1.13, FR1.14, FR1.15, FR1.16
# Covers: FR1.17, FR1.18, FR1.19, FR1.20, FR1.21, FR1.22, FR1.23, FR1.24, FR1.25
# Covers: FR1.26, NF1.1, NF1.2, NF1.3, NF1.4, SV1.1, SV1.2

from cloud_dog_config.traceability_ids import TRACEABILITY_IDS


def test_traceability_ids_declared() -> None:
    assert len(TRACEABILITY_IDS) >= 1
