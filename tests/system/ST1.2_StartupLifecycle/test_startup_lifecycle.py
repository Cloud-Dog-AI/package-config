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

"""ST1.2: Startup Lifecycle — load→merge→compile→validate→freeze tests."""

from __future__ import annotations

import time
from pathlib import Path

from cloud_dog_config import load_config


class TestStartupLifecycle:
    def test_full_lifecycle_and_schema_validation(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.yaml"
        config = tmp_path / "config.yaml"
        env_file = tmp_path / "env"

        defaults.write_text(
            "api:\n"
            '  port: "${CLOUD_DOG__API__PORT:8080}"\n'
            '  enabled: "${CLOUD_DOG__API__ENABLED || true}"\n'
            "service:\n"
            "  name: \"${CLOUD_DOG__SERVICE__NAME || 'test-service'}\"\n",
            encoding="utf-8",
        )
        config.write_text("api:\n  port: 9000\n", encoding="utf-8")
        env_file.write_text("CLOUD_DOG__API__PORT=7000\n", encoding="utf-8")

        t0 = time.perf_counter()
        cfg = load_config(
            env_files=[str(env_file)],
            defaults_yaml=str(defaults),
            config_yaml=str(config),
            schema={"required": ["api", "service"]},
            vault_enabled=False,
        )
        dt_ms = (time.perf_counter() - t0) * 1000

        assert cfg.get("api.port") == 7000  # env wins, coerced to int
        assert cfg.get("api.enabled") is True
        assert cfg.get("service.name") == "test-service"
        assert dt_ms < 1000, "Sanity bound for local tests (benchmarked separately)"
