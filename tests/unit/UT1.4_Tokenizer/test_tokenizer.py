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

"""UT1.4: Tokenizer — ${...} extraction tests."""

from __future__ import annotations

import pytest

from cloud_dog_config.compiler.tokenizer import tokenize


class TestTokenizer:
    def test_no_expression(self) -> None:
        tokens = tokenize("hello")
        assert len(tokens) == 1
        assert tokens[0].kind == "literal"
        assert tokens[0].value == "hello"

    def test_single_expression(self) -> None:
        tokens = tokenize("${A}")
        assert [(t.kind, t.value) for t in tokens] == [("expr", "A")]

    def test_multiple_expressions(self) -> None:
        tokens = tokenize("x=${A}, y=${B}")
        assert [t.kind for t in tokens] == ["literal", "expr", "literal", "expr"]

    def test_nested_braces_inside_quotes(self) -> None:
        tokens = tokenize('${{"a": 1} ? "x" : "y"}')
        assert len(tokens) == 1
        assert tokens[0].kind == "expr"

    def test_unclosed_expression_raises(self) -> None:
        with pytest.raises(ValueError):
            tokenize("x=${A")

    def test_docker_escaped_expression(self) -> None:
        tokens = tokenize("$${vault.dev.email.smtp.host}")
        assert [(t.kind, t.value) for t in tokens] == [("expr", "vault.dev.email.smtp.host")]

    def test_shell_escaped_expression(self) -> None:
        tokens = tokenize(r"\${ENV_VALUE}")
        assert [(t.kind, t.value) for t in tokens] == [("expr", "ENV_VALUE")]
