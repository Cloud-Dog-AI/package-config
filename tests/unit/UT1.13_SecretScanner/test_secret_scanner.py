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

"""UT1.13: Secret Scanner — defaults.yaml secret detection tests."""

from __future__ import annotations

from cloud_dog_config.schema.secret_scanner import scan_for_secrets


class TestSecretScanner:
    def test_detects_obvious_secrets(self) -> None:
        findings = scan_for_secrets({"api_key": "sk-abcdef1234567890"})
        assert findings

    def test_allows_placeholders(self) -> None:
        findings = scan_for_secrets({"api_key": "${vault.expert.llm.api_key}"})
        assert findings == []

    def test_passes_clean_defaults(self) -> None:
        findings = scan_for_secrets({"a": {"b": "value"}})
        assert findings == []
