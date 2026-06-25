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

"""AT1.3: Legacy migration pattern tests."""

from __future__ import annotations

import pytest

from cloud_dog_config import load_config
from cloud_dog_config.compat import LegacyConfigAdapter
from cloud_dog_config.errors import ConfigImmutableError


class TestLegacyMigrationPattern:
    def test_legacy_adapter_supports_staged_migration(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        defaults = tmp_path / "defaults.yaml"
        config = tmp_path / "config.yaml"
        env_file = tmp_path / "env"

        defaults.write_text("service:\n  name: default\n  timeout_s: 5\n", encoding="utf-8")
        config.write_text("", encoding="utf-8")
        env_file.write_text("CLOUD_DOG__SERVICE__NAME=legacy-service\n", encoding="utf-8")

        cfg = load_config(
            defaults_yaml=str(defaults),
            config_yaml=str(config),
            env_files=[str(env_file)],
            vault_enabled=False,
        )
        adapter = LegacyConfigAdapter(cfg, warn_on_access=True)

        with pytest.warns(DeprecationWarning):
            service_name = adapter.get("service.name")
        assert service_name == "legacy-service"

        with pytest.warns(DeprecationWarning):
            snapshot = adapter.as_dict("service")
        assert snapshot["timeout_s"] == 5

        with pytest.raises(ConfigImmutableError):
            adapter["service.timeout_s"] = 10
