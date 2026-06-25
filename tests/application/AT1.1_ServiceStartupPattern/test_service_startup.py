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

"""AT1.1: Service Startup Pattern — simulate real service startup configuration."""

from __future__ import annotations

from pathlib import Path

from cloud_dog_config import get_config, load_config


class TestServiceStartupPattern:
    def test_service_startup_end_to_end(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.yaml"
        config = tmp_path / "config.yaml"
        env_file = tmp_path / "env"

        defaults.write_text(
            "vault:\n"
            "  server: mock\n"
            "  key: ignored\n"
            "  mock_data:\n"
            "    secret/expert/llm/api_key:\n"
            "      api_key: sk-test\n"
            "app:\n"
            "  name: \"${CLOUD_DOG__APP__NAME || 'demo'}\"\n"
            "llm:\n"
            "  api_key: \"${vault.expert.llm.api_key || 'fallback'}\"\n",
            encoding="utf-8",
        )
        config.write_text("", encoding="utf-8")
        env_file.write_text("CLOUD_DOG__APP__NAME=my-app\n", encoding="utf-8")

        cfg = load_config(env_files=[str(env_file)], defaults_yaml=str(defaults), config_yaml=str(config))
        assert cfg.get("app.name") == "my-app"
        # Vault object scalar resolution should return the leaf value when present.
        assert cfg.get("llm.api_key") == "sk-test"
        assert get_config("app.name") == "my-app"
