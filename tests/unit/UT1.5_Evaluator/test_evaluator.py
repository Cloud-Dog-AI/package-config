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

"""UT1.5: Safe Expression Evaluator — operator and literal tests."""

from __future__ import annotations

import pytest

from cloud_dog_config.compiler.evaluator import SafeExpressionError, Unresolved, evaluate


def _resolver(values: dict[str, object]):
    def r(name: str):
        return values.get(name, Unresolved(name))

    return r


class TestEvaluator:
    def test_or_fallback_returns_first_truthy(self) -> None:
        v = evaluate("A || B || C", _resolver({"A": "", "B": "x", "C": "y"}))
        assert v == "x"

    def test_or_fallback_uses_second_when_first_unresolved(self) -> None:
        v = evaluate("MISSING || 'fallback'", _resolver({}))
        assert v == "fallback"

    def test_ternary(self) -> None:
        v = evaluate("FLAG ? 'yes' : 'no'", _resolver({"FLAG": True}))
        assert v == "yes"

    def test_equality(self) -> None:
        v = evaluate("A == 2", _resolver({"A": 2}))
        assert v is True

    def test_inequality(self) -> None:
        v = evaluate("A != 2", _resolver({"A": 3}))
        assert v is True

    def test_negation(self) -> None:
        v = evaluate("!FLAG", _resolver({"FLAG": False}))
        assert v is True

    def test_json_literals(self) -> None:
        v = evaluate('{"a": 1, "b": [2]}', _resolver({}))
        assert v["a"] == 1
        assert v["b"] == [2]

    def test_rejects_import(self) -> None:
        with pytest.raises(SafeExpressionError):
            evaluate("import os", _resolver({}))

    def test_rejects_parentheses(self) -> None:
        with pytest.raises(SafeExpressionError):
            evaluate("f()", _resolver({"f": "x"}))
