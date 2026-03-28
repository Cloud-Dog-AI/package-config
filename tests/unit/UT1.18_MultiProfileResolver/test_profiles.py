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

"""UT1.18: Multi-profile resolver tests."""

from __future__ import annotations

import pytest

from cloud_dog_config.config import GlobalConfig, freeze_tree, utc_now
from cloud_dog_config.errors import ConfigError
from cloud_dog_config.profiles import resolve_profile


class TestMultiProfileResolver:
    def test_resolve_named_profile(self) -> None:
        cfg = GlobalConfig(
            data=freeze_tree(
                {
                    "storage": {
                        "profiles": {
                            "default": {"bucket": "main"},
                            "archive": {"bucket": "archive"},
                        }
                    }
                }
            ),
            version="1",
            loaded_at=utc_now(),
            sources=(),
        )
        profile = resolve_profile(cfg, "archive", base_path="storage.profiles")
        assert profile["bucket"] == "archive"

    def test_missing_profile_falls_back(self) -> None:
        cfg = GlobalConfig(
            data=freeze_tree({"profiles": {"default": {"url": "http://localhost"}}}),
            version="1",
            loaded_at=utc_now(),
            sources=(),
        )
        profile = resolve_profile(cfg, "missing", base_path="profiles")
        assert profile["url"] == "http://localhost"

    def test_missing_profile_and_fallback_raises(self) -> None:
        cfg = GlobalConfig(data=freeze_tree({"profiles": {}}), version="1", loaded_at=utc_now(), sources=())
        with pytest.raises(ConfigError, match="fallback"):
            resolve_profile(cfg, "missing", base_path="profiles", fallback="also_missing")
