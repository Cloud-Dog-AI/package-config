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

"""UT1.16: Environment metadata accessor tests."""

from __future__ import annotations

import os
from pathlib import Path

from cloud_dog_config import load_config
from cloud_dog_config.config import GlobalConfig, freeze_tree, utc_now
from cloud_dog_config.metadata import get_env_metadata


class TestEnvMetadata:
    def test_get_env_metadata_from_loaded_config(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.yaml"
        config = tmp_path / "config.yaml"
        env_a = tmp_path / "env.a"
        env_b = tmp_path / "env.b"

        defaults.write_text(
            "vault:\n  server: mock\n  key: ignored\n  available: true\nservice:\n  name: app\n",
            encoding="utf-8",
        )
        config.write_text("", encoding="utf-8")
        env_a.write_text("CLOUD_DOG__SERVICE__NAME=svc-a\n", encoding="utf-8")
        env_b.write_text("CLOUD_DOG__SERVICE__NAME=svc-b\n", encoding="utf-8")

        cfg = load_config(
            defaults_yaml=str(defaults),
            config_yaml=str(config),
            env_files=[str(env_a), str(env_b)],
        )

        meta = get_env_metadata()
        assert meta.hostname
        assert meta.process_id == os.getpid()
        assert meta.python_version
        assert meta.config_version == cfg.version
        assert meta.loaded_at == cfg.loaded_at
        assert meta.vault_available is True
        assert meta.env_file_count == 2
        assert len(meta.sources) >= 2

    def test_sources_are_redacted(self) -> None:
        from cloud_dog_config import loader

        loader._CURRENT = GlobalConfig(  # type: ignore[attr-defined]
            data=freeze_tree({"service": {"name": "demo"}}),
            version="9",
            loaded_at=utc_now(),
            sources=("vault_token=sk-secret-value",),
        )

        meta = get_env_metadata()
        assert meta.sources[0].endswith("***REDACTED***")
