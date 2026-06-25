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

"""ST1.6: Vault Bundle Assignment — bundle deep-merge with env overrides (mock Vault)."""

from __future__ import annotations

from pathlib import Path

from cloud_dog_config import load_config


class TestVaultBundleAssignment:
    def test_bundle_merged_and_env_overrides_win(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.yaml"
        config = tmp_path / "config.yaml"
        env_file = tmp_path / "env"

        defaults.write_text(
            "vault:\n"
            "  server: mock\n"
            "  key: ignored\n"
            "  mock_data:\n"
            "    secret/expert/db/creds:\n"
            "      username: vault_user\n"
            "      password: vault_pass\n"
            "db:\n"
            '  creds: "${vault.expert.db.creds.*}"\n',
            encoding="utf-8",
        )
        config.write_text("", encoding="utf-8")
        env_file.write_text("CLOUD_DOG__DB__CREDS__USERNAME=env_user\n", encoding="utf-8")

        cfg = load_config(
            env_files=[str(env_file)],
            defaults_yaml=str(defaults),
            config_yaml=str(config),
            vault_enabled=True,
        )

        assert cfg.get("db.creds.username") == "env_user"
        assert cfg.get("db.creds.password") == "vault_pass"
