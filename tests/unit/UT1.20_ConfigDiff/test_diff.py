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

"""UT1.20: Structured config diff tests."""

from __future__ import annotations

from cloud_dog_config.config import GlobalConfig, freeze_tree, utc_now
from cloud_dog_config.diff import config_diff
from cloud_dog_config.redaction import REDACTED_VALUE


class TestConfigDiff:
    def test_detects_added_removed_modified_and_ignores_unchanged(self) -> None:
        old = {
            "service": {"host": "a", "port": 8080},
            "removed_key": "x",
            "db": {"password": "old-secret"},
        }
        new = {
            "service": {"host": "a", "port": 9090},
            "added_key": True,
            "db": {"password": "new-secret"},
        }

        changes = config_diff(old, new, redact=True)
        by_path = {change.path: change for change in changes}

        assert by_path["service.port"].change_type == "modified"
        assert by_path["removed_key"].change_type == "removed"
        assert by_path["added_key"].change_type == "added"
        assert by_path["db.password"].old_value == REDACTED_VALUE
        assert by_path["db.password"].new_value == REDACTED_VALUE
        assert "service.host" not in by_path

    def test_accepts_global_config_inputs(self) -> None:
        old_cfg = GlobalConfig(
            data=freeze_tree({"feature": {"enabled": False}}),
            version="1",
            loaded_at=utc_now(),
            sources=(),
        )
        new_cfg = GlobalConfig(
            data=freeze_tree({"feature": {"enabled": True}}),
            version="2",
            loaded_at=utc_now(),
            sources=(),
        )

        changes = config_diff(old_cfg, new_cfg, redact=False)
        assert len(changes) == 1
        assert changes[0].path == "feature.enabled"
        assert changes[0].old_value is False
        assert changes[0].new_value is True
