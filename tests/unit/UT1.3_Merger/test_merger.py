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

"""UT1.3: Merger — deep merge semantics tests."""

from __future__ import annotations

from cloud_dog_config.merger import deep_merge


class TestMerger:
    def test_dicts_merge_recursively(self) -> None:
        base = {"a": {"b": 1, "c": 2}}
        overlay = {"a": {"c": 3, "d": 4}}
        merged = deep_merge(base, overlay)
        assert merged == {"a": {"b": 1, "c": 3, "d": 4}}

    def test_lists_replaced(self) -> None:
        base = {"a": [1, 2, 3]}
        overlay = {"a": [9]}
        assert deep_merge(base, overlay) == {"a": [9]}

    def test_scalars_overwritten(self) -> None:
        base = {"a": 1}
        overlay = {"a": 2}
        assert deep_merge(base, overlay) == {"a": 2}

    def test_type_mismatch_overlay_wins(self) -> None:
        base = {"a": {"b": 1}}
        overlay = {"a": 5}
        assert deep_merge(base, overlay) == {"a": 5}
