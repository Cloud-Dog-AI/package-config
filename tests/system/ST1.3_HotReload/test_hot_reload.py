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

"""ST1.3: Hot Reload — reload pipeline and audit event tests."""

from __future__ import annotations

from pathlib import Path

from cloud_dog_config import load_config, reload_config
from cloud_dog_config.audit import get_last_event


class TestHotReload:
    def test_reload_swaps_config_and_emits_audit(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.yaml"
        config = tmp_path / "config.yaml"
        env_file = tmp_path / "env"

        defaults.write_text("a: 1\n", encoding="utf-8")
        config.write_text("a: 2\n", encoding="utf-8")
        env_file.write_text("a=3\n", encoding="utf-8")

        cfg1 = load_config(env_files=[str(env_file)], defaults_yaml=str(defaults), config_yaml=str(config))
        # Env keys without APP__ nesting only override keys that exist in base config.
        assert cfg1.get("a") == 3

        env_file.write_text("a=4\n", encoding="utf-8")
        cfg2 = reload_config(env_files=[str(env_file)], defaults_yaml=str(defaults), config_yaml=str(config))
        assert cfg2.get("a") == 4
        assert cfg2.version != cfg1.version

        event = get_last_event()
        assert event is not None
        assert event.outcome == "success"
        assert event.new_version == cfg2.version
