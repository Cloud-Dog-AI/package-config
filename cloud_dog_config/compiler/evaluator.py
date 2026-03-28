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

# cloud_dog_config — Safe expression evaluator
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Evaluates a restricted expression language for `${...}` compile
#   phase: `||`, `? :`, `==`, `!=`, `!`, literals and identifiers.
# Related requirements: FR1.5, FR1.8
# Related architecture: CC1.5
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Restricted expression evaluator for configuration compilation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Iterator


@dataclass(frozen=True, slots=True)
class Unresolved:
    """Represents an unresolved placeholder under non-strict policy."""

    expression: str

    def __bool__(self) -> bool:  # pragma: no cover (truthiness is by design)
        return False


class SafeExpressionError(ValueError):
    """Raised when an expression is unsafe or invalid."""


_FORBIDDEN_SUBSTRINGS = (
    "import",
    "eval",
    "exec",
    "$(",
    "`",
    ";",
)

_FORBIDDEN_CHARS = set("()\\")


def evaluate(expression: str, resolve_identifier: Callable[[str], Any]) -> Any:
    """Evaluate an expression with an identifier resolver.

    Identifiers are resolved via `resolve_identifier(name)` and may return
    `Unresolved` to represent missing values.
    """
    expr = expression.strip()
    _guard(expr)
    tokens = list(_lex(expr))
    parser = _Parser(tokens=tokens, resolve_identifier=resolve_identifier)
    value = parser.parse_expression()
    parser.expect_end()
    return value


def _guard(expr: str) -> None:
    lower = expr.lower()
    if any(s in lower for s in _FORBIDDEN_SUBSTRINGS):
        raise SafeExpressionError("Unsafe expression content")
    if any(ch in _FORBIDDEN_CHARS for ch in expr):
        # Disallow parentheses/brace syntax to avoid function calls and code injection.
        # JSON object/array literals are allowed only as complete literals parsed by json.loads,
        # and are expected to be provided as quoted strings in expressions if needed.
        raise SafeExpressionError("Unsupported expression syntax")
    # Arithmetic and assignment are not part of the lexer. If present outside
    # string/JSON literals, the lexer will fail with a SafeExpressionError.


@dataclass(frozen=True, slots=True)
class _Tok:
    t: str
    v: str


_TOKEN_RE = re.compile(
    r"""
    (?P<ws>\s+)
  | (?P<or>\|\|)
  | (?P<eq>==)
  | (?P<ne>!=)
  | (?P<q>\?)
  | (?P<colon>:)
  | (?P<not>!)
  | (?P<number>-?\d+(?:\.\d+)?)
  | (?P<str>"([^"\\]|\\.)*"|'([^'\\]|\\.)*')
  | (?P<ident>[A-Za-z_][A-Za-z0-9_\\.*]*)
    """,
    re.VERBOSE,
)


def _lex(expr: str) -> Iterator[_Tok]:
    i = 0
    while i < len(expr):
        if expr[i] in ("{", "["):
            lit, end = _read_json_literal(expr, i)
            yield _Tok(t="json", v=lit)
            i = end
            continue
        m = _TOKEN_RE.match(expr, i)
        if not m:
            raise SafeExpressionError(f"Invalid token near: {expr[i : i + 20]!r}")
        kind = m.lastgroup
        text = m.group(0)
        i = m.end()
        if kind == "ws":
            continue
        if kind in ("or", "eq", "ne", "q", "colon", "not"):
            yield _Tok(t=kind, v=text)
        elif kind == "number":
            yield _Tok(t="number", v=text)
        elif kind == "str":
            yield _Tok(t="str", v=text)
        elif kind == "ident":
            yield _Tok(t="ident", v=text)
        else:
            raise SafeExpressionError("Lexer error")


def _read_json_literal(expr: str, start: int) -> tuple[str, int]:
    """Read a JSON object/array literal starting at start."""
    open_ch = expr[start]
    close_ch = "}" if open_ch == "{" else "]"
    i = start
    depth = 0
    in_single = False
    in_double = False
    escape = False
    while i < len(expr):
        ch = expr[i]
        if escape:
            escape = False
            i += 1
            continue
        if ch == "\\":
            escape = True
            i += 1
            continue
        if ch == "'" and not in_double:
            # JSON uses double quotes, but accept single quotes only inside strings we do not parse here.
            in_single = not in_single
            i += 1
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            i += 1
            continue
        if not in_single and not in_double:
            if ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0:
                    return expr[start : i + 1], i + 1
        i += 1
    raise SafeExpressionError("Unclosed JSON literal")


class _Parser:
    def __init__(self, *, tokens: list[_Tok], resolve_identifier: Callable[[str], Any]) -> None:
        self._tokens = tokens
        self._i = 0
        self._resolve_identifier = resolve_identifier

    def expect_end(self) -> None:
        """Handle expect end."""
        if self._i != len(self._tokens):
            raise SafeExpressionError("Unexpected trailing tokens")

    def parse_expression(self) -> Any:
        """Parse expression."""
        return self._parse_ternary()

    def _parse_ternary(self) -> Any:
        cond = self._parse_or()
        if self._peek("q"):
            self._consume("q")
            true_val = self._parse_ternary()
            self._consume("colon")
            false_val = self._parse_ternary()
            return true_val if _truthy(cond) else false_val
        return cond

    def _parse_or(self) -> Any:
        left = self._parse_equality()
        while self._peek("or"):
            self._consume("or")
            right = self._parse_equality()
            left = left if _truthy(left) else right
        return left

    def _parse_equality(self) -> Any:
        left = self._parse_unary()
        while True:
            if self._peek("eq"):
                self._consume("eq")
                right = self._parse_unary()
                left = left == right
            elif self._peek("ne"):
                self._consume("ne")
                right = self._parse_unary()
                left = left != right
            else:
                break
        return left

    def _parse_unary(self) -> Any:
        if self._peek("not"):
            self._consume("not")
            v = self._parse_unary()
            return not _truthy(v)
        return self._parse_primary()

    def _parse_primary(self) -> Any:
        tok = self._peek_any()
        if tok is None:
            raise SafeExpressionError("Unexpected end of expression")
        if tok.t == "json":
            self._i += 1
            try:
                return json.loads(tok.v)
            except Exception as exc:  # noqa: BLE001
                raise SafeExpressionError("Invalid JSON literal") from exc
        if tok.t == "number":
            self._i += 1
            if "." in tok.v:
                return float(tok.v)
            return int(tok.v)
        if tok.t == "str":
            self._i += 1
            return _parse_string(tok.v)
        if tok.t == "ident":
            self._i += 1
            ident = tok.v
            if ident in ("true", "false", "null"):
                return {"true": True, "false": False, "null": None}[ident]
            return self._resolve_identifier(ident)
        raise SafeExpressionError("Unexpected token")

    def _peek(self, t: str) -> bool:
        tok = self._peek_any()
        return tok is not None and tok.t == t

    def _peek_any(self) -> _Tok | None:
        if self._i >= len(self._tokens):
            return None
        return self._tokens[self._i]

    def _consume(self, t: str) -> _Tok:
        tok = self._peek_any()
        if tok is None or tok.t != t:
            raise SafeExpressionError(f"Expected {t}")
        self._i += 1
        return tok


def _parse_string(token_text: str) -> Any:
    # Use json.loads for correct escape handling.
    if token_text.startswith("'"):
        # Convert single-quoted to JSON double-quoted.
        inner = token_text[1:-1]
        inner = inner.replace("\\'", "'")
        return inner
    return json.loads(token_text)


def _truthy(value: Any) -> bool:
    if isinstance(value, Unresolved):
        return False
    return bool(value)
