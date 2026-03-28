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

"""UT1.9: Type Coercion — string coercion tests."""

from __future__ import annotations

import pytest

from cloud_dog_config.coercion import coerce


class TestTypeCoercion:
    def test_bool(self) -> None:
        assert coerce("true") is True
        assert coerce("false") is False

    def test_int(self) -> None:
        assert coerce("42") == 42

    def test_float(self) -> None:
        assert coerce("3.14") == pytest.approx(3.14)

    def test_json_object(self) -> None:
        assert coerce('{"a": 1}') == {"a": 1}

    def test_json_array(self) -> None:
        assert coerce("[1,2]") == [1, 2]

    def test_string_fallback(self) -> None:
        assert coerce("hello") == "hello"

    def test_hint_override(self) -> None:
        assert coerce("true", hint=bool) is True
