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

"""UT1.14: Safe Expression Boundary Guard — unsafe expression rejection tests."""

from __future__ import annotations

import pytest

from cloud_dog_config.compiler.evaluator import SafeExpressionError, evaluate


def _noop(_: str):
    return ""


class TestSafeExpressionBoundary:
    def test_rejects_function_calls(self) -> None:
        with pytest.raises(SafeExpressionError):
            evaluate("doit()", _noop)

    def test_rejects_arithmetic(self) -> None:
        with pytest.raises(SafeExpressionError):
            evaluate("1 + 2", _noop)

    def test_rejects_assignment(self) -> None:
        with pytest.raises(SafeExpressionError):
            evaluate("A=1", _noop)

    def test_rejects_import(self) -> None:
        with pytest.raises(SafeExpressionError):
            evaluate("import os", _noop)

    def test_rejects_shell_expansion(self) -> None:
        with pytest.raises(SafeExpressionError):
            evaluate("$(rm -rf /)", _noop)
