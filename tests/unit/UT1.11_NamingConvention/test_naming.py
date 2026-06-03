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

"""UT1.11: Naming Convention — env var path conversion tests."""

from __future__ import annotations

import pytest

from cloud_dog_config.naming import env_to_path, path_to_env


class TestNamingConvention:
    def test_env_to_path_with_prefix(self) -> None:
        assert env_to_path("CLOUD_DOG__LLM__MODEL", prefix="CLOUD_DOG") == "llm.model"

    def test_env_to_path_without_prefix(self) -> None:
        assert env_to_path("APP__A__B") == "app.a.b"

    def test_env_to_path_requires_separator(self) -> None:
        assert env_to_path("PLAIN") is None

    def test_path_to_env(self) -> None:
        assert path_to_env("llm.model", prefix="CLOUD_DOG") == "CLOUD_DOG__LLM__MODEL"

    def test_path_to_env_empty_rejected(self) -> None:
        with pytest.raises(ValueError):
            path_to_env("", prefix="CLOUD_DOG")
