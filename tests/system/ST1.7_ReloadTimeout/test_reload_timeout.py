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

"""ST1.7: Reload timeout behaviour tests."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from cloud_dog_config import get_config, load_config, reload_config
from cloud_dog_config.errors import ConfigReloadTimeoutError


class TestReloadTimeout:
    def test_timeout_raises_and_active_config_is_unchanged(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        defaults = tmp_path / "defaults.yaml"
        config = tmp_path / "config.yaml"
        defaults.write_text("a: 1\n", encoding="utf-8")
        config.write_text("", encoding="utf-8")

        cfg1 = load_config(defaults_yaml=str(defaults), config_yaml=str(config), vault_enabled=False)

        from cloud_dog_config import loader as loader_mod

        def slow_build(**kwargs):  # type: ignore[no-untyped-def]
            time.sleep(0.2)
            return {"a": 2}, ("defaults_yaml=slow", "config_yaml=slow")

        monkeypatch.setattr(loader_mod, "_build_compiled_tree", slow_build)

        with pytest.raises(ConfigReloadTimeoutError):
            reload_config(timeout_s=0.05, defaults_yaml=str(defaults), config_yaml=str(config), vault_enabled=False)

        cfg_after = get_config()
        assert cfg_after.version == cfg1.version
        assert get_config("a") == 1

    def test_default_timeout_uses_config_reload_timeout_setting(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        defaults = tmp_path / "defaults.yaml"
        config = tmp_path / "config.yaml"
        defaults.write_text("a: 1\nconfig:\n  reload_timeout_s: 0.01\n", encoding="utf-8")
        config.write_text("", encoding="utf-8")

        load_config(defaults_yaml=str(defaults), config_yaml=str(config), vault_enabled=False)

        from cloud_dog_config import loader as loader_mod

        def slow_build(**kwargs):  # type: ignore[no-untyped-def]
            time.sleep(0.05)
            return {"a": 2}, ("defaults_yaml=slow", "config_yaml=slow")

        monkeypatch.setattr(loader_mod, "_build_compiled_tree", slow_build)

        with pytest.raises(ConfigReloadTimeoutError):
            reload_config(defaults_yaml=str(defaults), config_yaml=str(config), vault_enabled=False)
