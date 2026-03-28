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

"""UT1.6: Reference Resolver — ${ENV_VAR} resolution tests."""

from __future__ import annotations

from cloud_dog_config.compiler.evaluator import Unresolved
from cloud_dog_config.compiler.reference_resolver import resolve_reference, resolve_reference_with_default


class TestReferenceResolver:
    def test_env_exact_match(self) -> None:
        v = resolve_reference("X", config={"X": "cfg"}, env={"X": "env"})
        assert v == "env"

    def test_dotted_path_lookup(self) -> None:
        v = resolve_reference("a.b", config={"a": {"b": 1}}, env={})
        assert v == 1

    def test_missing_returns_unresolved(self) -> None:
        v = resolve_reference("MISSING", config={}, env={})
        assert isinstance(v, Unresolved)

    def test_default_used_when_missing(self) -> None:
        v = resolve_reference_with_default("MISSING:hello", config={}, env={})
        assert v == "hello"

    def test_default_not_used_when_present(self) -> None:
        v = resolve_reference_with_default("X:hello", config={"X": "cfg"}, env={})
        assert v == "cfg"
