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

"""UT1.10: Redaction — secret redaction tests."""

from __future__ import annotations

from cloud_dog_config.redaction import REDACTED_VALUE, redact, redact_string


class TestRedaction:
    def test_key_pattern_redaction(self) -> None:
        data = {"api_key": "sk-1234567890abcdef", "ok": "value"}
        red = redact(data)
        assert red["api_key"] == REDACTED_VALUE
        assert red["ok"] == "value"

    def test_nested_redaction(self) -> None:
        data = {"a": {"password": "p", "b": 1}}
        red = redact(data)
        assert red["a"]["password"] == REDACTED_VALUE

    def test_string_redaction_heuristic(self) -> None:
        assert redact_string("sk-abcdef123456") == REDACTED_VALUE
