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

"""IT1.3: Vault Fallback — missing Vault path uses fallback expression (env-gated)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from cloud_dog_config import load_config


def _vault_env_ready() -> bool:
    return (
        bool(os.environ.get("VAULT_ADDR"))
        and bool(os.environ.get("VAULT_TOKEN"))
        and bool(os.environ.get("VAULT_MOUNT_POINT"))
    )


class TestVaultFallback:
    def test_missing_path_uses_fallback(self, tmp_path: Path) -> None:
        # IT tests must fail (not skip) when required real env/settings are unavailable.
        if not _vault_env_ready():
            pytest.fail(
                "Vault env not configured; run with --env tests/env-IT --env /opt/iac/Development/cloud-dog-ai/env-vault"
            )

        defaults = tmp_path / "defaults.yaml"
        defaults.write_text(
            "value: \"${vault.cloud_dog_config_it.missing.path || 'fallback'}\"\n",
            encoding="utf-8",
        )
        cfg = load_config(defaults_yaml=str(defaults), config_yaml=str(tmp_path / "config.yaml"), vault_enabled=True)
        assert cfg.get("value") == "fallback"
