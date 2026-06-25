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

"""ST1.1: Precedence Chain — os.environ > env-file > config.yaml > defaults.yaml."""

from __future__ import annotations

from pathlib import Path

import pytest

from cloud_dog_config import load_config


class TestPrecedenceChain:
    def test_precedence_chain_order(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        defaults = tmp_path / "defaults.yaml"
        config = tmp_path / "config.yaml"
        env_file = tmp_path / "env"

        defaults.write_text("llm:\n  model: defaults\n", encoding="utf-8")
        config.write_text("llm:\n  model: config\n", encoding="utf-8")
        env_file.write_text("CLOUD_DOG__LLM__MODEL=env\n", encoding="utf-8")

        monkeypatch.setenv("CLOUD_DOG__LLM__MODEL", "os")

        cfg = load_config(
            env_files=[str(env_file)],
            defaults_yaml=str(defaults),
            config_yaml=str(config),
            vault_enabled=False,
        )
        assert cfg.get("llm.model") == "os"

    def test_multi_env_file_order(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.yaml"
        config = tmp_path / "config.yaml"
        env1 = tmp_path / "env1"
        env2 = tmp_path / "env2"

        defaults.write_text("A: 1\n", encoding="utf-8")
        config.write_text("A: 2\n", encoding="utf-8")
        env1.write_text("A=3\n", encoding="utf-8")
        env2.write_text("A=4\n", encoding="utf-8")

        cfg = load_config(
            env_files=[str(env1), str(env2)],
            defaults_yaml=str(defaults),
            config_yaml=str(config),
            vault_enabled=False,
        )
        assert cfg.get("A") == 4

    def test_os_environ_wins_for_placeholder_only_key(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        defaults = tmp_path / "defaults.yaml"
        config = tmp_path / "config.yaml"
        env_file = tmp_path / "env"

        defaults.write_text(
            'profiles:\n  default:\n    server_log: "${FILE_MCP_SERVER_LOG}"\n',
            encoding="utf-8",
        )
        config.write_text("", encoding="utf-8")
        env_file.write_text("FILE_MCP_SERVER_LOG=/tmp/from-env-file.log\n", encoding="utf-8")
        monkeypatch.setenv("FILE_MCP_SERVER_LOG", "/tmp/from-os.log")

        cfg = load_config(
            env_files=[str(env_file)],
            defaults_yaml=str(defaults),
            config_yaml=str(config),
            vault_enabled=False,
        )
        assert cfg.get("profiles.default.server_log") == "/tmp/from-os.log"
