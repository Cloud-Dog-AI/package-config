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

# cloud_dog_config — Expression tokenizer
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Tokenises strings containing `${...}` expressions into literal and
#   expression segments. Supports multiple expressions per string, including
#   shell-safe escaped prefixes (`$${...}` and `\${...}`).
# Related requirements: FR1.4
# Related architecture: CC1.5
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Tokenizer for `${...}` placeholders (with escaped-prefix compatibility)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Token:
    """One token from a tokenised string."""

    kind: str  # "literal" | "expr"
    value: str


def tokenize(text: str) -> list[Token]:
    """Tokenise a string into literal and expression tokens."""
    tokens: list[Token] = []
    i = 0
    buf: list[str] = []

    def flush_literal() -> None:
        """Handle flush literal."""
        if buf:
            tokens.append(Token(kind="literal", value="".join(buf)))
            buf.clear()

    while i < len(text):
        if text.startswith("$${", i) or text.startswith("\\${", i):
            flush_literal()
            expr, end = _read_expression(text, i + 3)
            tokens.append(Token(kind="expr", value=expr))
            i = end
            continue
        if text.startswith("${", i):
            flush_literal()
            expr, end = _read_expression(text, i + 2)
            tokens.append(Token(kind="expr", value=expr))
            i = end
            continue
        buf.append(text[i])
        i += 1

    flush_literal()
    return tokens


def _read_expression(text: str, start: int) -> tuple[str, int]:
    """Read expression content starting at `start` (after `${`).

    Returns:
        (expression_text, new_index_after_closing_brace)
    """
    depth = 1
    i = start
    buf: list[str] = []
    in_single = False
    in_double = False
    escape = False

    while i < len(text):
        ch = text[i]
        if escape:
            buf.append(ch)
            escape = False
            i += 1
            continue

        if ch == "\\":
            escape = True
            buf.append(ch)
            i += 1
            continue

        if ch == "'" and not in_double:
            in_single = not in_single
            buf.append(ch)
            i += 1
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            buf.append(ch)
            i += 1
            continue

        if not in_single and not in_double:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return "".join(buf).strip(), i + 1

        buf.append(ch)
        i += 1

    raise ValueError("Unclosed ${...} expression")
