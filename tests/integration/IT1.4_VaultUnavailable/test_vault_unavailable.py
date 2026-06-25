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

"""IT1.4: Vault Unavailable — strict fails, warn keeps placeholder (env-gated)."""

from __future__ import annotations

from pathlib import Path

import pytest

from cloud_dog_config import load_config
from cloud_dog_config.errors import UnresolvedPlaceholderError


class TestVaultUnavailable:
    def test_strict_fails_when_vault_unreachable(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("VAULT_ADDR", "http://127.0.0.1:9")
        monkeypatch.setenv("VAULT_TOKEN", "test-token")
        monkeypatch.setenv("VAULT_MOUNT_POINT", "secret")

        defaults = tmp_path / "defaults.yaml"
        defaults.write_text('value: "${vault.cloud_dog_config_it.unreachable.value}"\n', encoding="utf-8")
        with pytest.raises(UnresolvedPlaceholderError):
            load_config(defaults_yaml=str(defaults), config_yaml=str(tmp_path / "config.yaml"), vault_enabled=True)

    def test_warn_keeps_placeholder_when_vault_unreachable(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("VAULT_ADDR", "http://127.0.0.1:9")
        monkeypatch.setenv("VAULT_TOKEN", "test-token")
        monkeypatch.setenv("VAULT_MOUNT_POINT", "secret")

        defaults = tmp_path / "defaults.yaml"
        defaults.write_text('value: "${vault.cloud_dog_config_it.unreachable.value}"\n', encoding="utf-8")
        cfg = load_config(
            defaults_yaml=str(defaults),
            config_yaml=str(tmp_path / "config.yaml"),
            vault_enabled=True,
            unresolved_policy="warn",
        )
        assert "vault." in cfg.get("value")
