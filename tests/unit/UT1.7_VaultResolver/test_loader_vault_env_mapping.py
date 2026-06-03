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

"""UT1.7: Vault env mapping and mount config composition tests."""

from __future__ import annotations

from pathlib import Path

from cloud_dog_config import load_config
from cloud_dog_config import loader as loader_mod


class _DummyVaultClient:
    def __init__(self, config: object) -> None:
        self.config = config


class TestLoaderVaultEnvMapping:
    def test_raw_vault_env_keys_map_to_vault_tree(self) -> None:
        tree = loader_mod._env_kv_to_tree(
            {
                "VAULT_ADDR": "https://vault.example.test",
                "VAULT_TOKEN": "token-1",
                "VAULT_MOUNT_POINT": "cloud_dog_ai",
                "VAULT_CONFIG_PATH": "config",
            },
            base={},
        )
        assert tree["vault"]["server"] == "https://vault.example.test"
        assert tree["vault"]["key"] == "token-1"
        assert tree["vault"]["mount_point"] == "cloud_dog_ai"
        assert tree["vault"]["config_path"] == "config"

    def test_app_scoped_vault_keys_map_to_canonical_vault_tree(self) -> None:
        tree = loader_mod._env_kv_to_tree(
            {
                "CLOUD_DOG__MYAPP__VAULT__ADDR": "https://vault.example.test",
                "CLOUD_DOG__MYAPP__VAULT__TOKEN": "token-2",
                "CLOUD_DOG__MYAPP__VAULT__MOUNT_POINT": "cloud_dog_ai",
                "CLOUD_DOG__MYAPP__VAULT__CONFIG_PATH": "config",
            },
            base={},
        )
        assert tree["vault"]["server"] == "https://vault.example.test"
        assert tree["vault"]["key"] == "token-2"
        assert tree["vault"]["mount_point"] == "cloud_dog_ai"
        assert tree["vault"]["config_path"] == "config"

    def test_mount_point_is_composed_with_config_path(self, monkeypatch) -> None:
        monkeypatch.setattr(loader_mod, "VaultClient", _DummyVaultClient)
        client = loader_mod._create_vault_client(
            {
                "vault": {
                    "server": "https://vault.example.test",
                    "key": "token-3",
                    "mount_point": "cloud_dog_ai",
                    "config_path": "config",
                    "timeout_seconds": 5,
                }
            }
        )
        assert isinstance(client, _DummyVaultClient)
        assert client.config.mount_point == "cloud_dog_ai/config"

    def test_app_scoped_vault_env_supports_substitution_with_mock_vault(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.yaml"
        env_file = tmp_path / "env"
        defaults.write_text(
            "vault:\n"
            "  server: ''\n"
            "  key: ''\n"
            "  mock_data:\n"
            "    secret/expert/llm/model:\n"
            "      model: granite4\n"
            "llm:\n"
            '  model: "${vault.expert.llm.model}"\n',
            encoding="utf-8",
        )
        env_file.write_text(
            "CLOUD_DOG__MYAPP__VAULT__SERVER=mock\nCLOUD_DOG__MYAPP__VAULT__TOKEN=unused\n",
            encoding="utf-8",
        )

        cfg = load_config(
            env_files=[str(env_file)],
            defaults_yaml=str(defaults),
            config_yaml=str(tmp_path / "config.yaml"),
            vault_enabled=True,
        )
        assert cfg.get("llm.model") == "granite4"

    def test_docker_escaped_vault_expression_in_env_file(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.yaml"
        env_file = tmp_path / "env"
        defaults.write_text(
            "vault:\n"
            "  server: ''\n"
            "  key: ''\n"
            "  mock_data:\n"
            "    secret/expert/llm/model:\n"
            "      model: granite4\n"
            "llm:\n"
            "  model: baseline\n",
            encoding="utf-8",
        )
        env_file.write_text(
            "CLOUD_DOG__MYAPP__VAULT__SERVER=mock\n"
            "CLOUD_DOG__MYAPP__VAULT__TOKEN=unused\n"
            "CLOUD_DOG__LLM__MODEL=$${vault.expert.llm.model}\n",
            encoding="utf-8",
        )

        cfg = load_config(
            env_files=[str(env_file)],
            defaults_yaml=str(defaults),
            config_yaml=str(tmp_path / "config.yaml"),
            vault_enabled=True,
        )
        assert cfg.get("llm.model") == "granite4"

    def test_docker_escaped_vault_bundle_expression(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.yaml"
        env_file = tmp_path / "env"
        defaults.write_text(
            "vault:\n"
            "  server: ''\n"
            "  key: ''\n"
            "  mock_data:\n"
            "    secret/expert/db/creds:\n"
            "      username: vault_user\n"
            "      password: vault_pass\n"
            "db:\n"
            '  creds: "$${vault.expert.db.creds.*}"\n',
            encoding="utf-8",
        )
        env_file.write_text(
            "CLOUD_DOG__MYAPP__VAULT__SERVER=mock\nCLOUD_DOG__MYAPP__VAULT__TOKEN=unused\n",
            encoding="utf-8",
        )

        cfg = load_config(
            env_files=[str(env_file)],
            defaults_yaml=str(defaults),
            config_yaml=str(tmp_path / "config.yaml"),
            vault_enabled=True,
        )
        assert cfg.get("db.creds.username") == "vault_user"
        assert cfg.get("db.creds.password") == "vault_pass"

    def test_shell_escaped_vault_expression_in_os_environ(self, tmp_path: Path, monkeypatch) -> None:
        defaults = tmp_path / "defaults.yaml"
        defaults.write_text(
            "vault:\n"
            "  server: ''\n"
            "  key: ''\n"
            "  mock_data:\n"
            "    secret/expert/llm/model:\n"
            "      model: granite4\n"
            "llm:\n"
            "  model: baseline\n",
            encoding="utf-8",
        )
        monkeypatch.setenv("CLOUD_DOG__MYAPP__VAULT__SERVER", "mock")
        monkeypatch.setenv("CLOUD_DOG__MYAPP__VAULT__TOKEN", "unused")
        monkeypatch.setenv("CLOUD_DOG__LLM__MODEL", r"\${vault.expert.llm.model}")

        cfg = load_config(
            env_files=[],
            defaults_yaml=str(defaults),
            config_yaml=str(tmp_path / "config.yaml"),
            vault_enabled=True,
        )
        assert cfg.get("llm.model") == "granite4"

    def test_select_relevant_os_environ_includes_placeholder_references(self, monkeypatch) -> None:
        monkeypatch.setenv("FILE_MCP_SERVER_LOG", "/tmp/from-os.log")
        monkeypatch.setenv("NOT_REFERENCED_KEY", "drop-me")

        selected = loader_mod._select_relevant_os_environ(
            base={
                "profiles": {
                    "default": {
                        "server_log": "${FILE_MCP_SERVER_LOG || '/tmp/default.log'}",
                    }
                }
            }
        )

        assert selected["FILE_MCP_SERVER_LOG"] == "/tmp/from-os.log"
        assert "NOT_REFERENCED_KEY" not in selected

    def test_collect_placeholder_vars_walks_nested_trees(self) -> None:
        placeholder_vars = loader_mod._collect_placeholder_vars(
            {
                "profiles": {
                    "default": {
                        "log_path": "${FILE_MCP_SERVER_LOG}",
                        "s3": ["${FILE_MCP_S3_ACCESS_KEY}", "${FILE_MCP_S3_SECRET_KEY || ''}"],
                    }
                }
            }
        )

        assert "FILE_MCP_SERVER_LOG" in placeholder_vars
        assert "FILE_MCP_S3_ACCESS_KEY" in placeholder_vars
        assert "FILE_MCP_S3_SECRET_KEY" in placeholder_vars
