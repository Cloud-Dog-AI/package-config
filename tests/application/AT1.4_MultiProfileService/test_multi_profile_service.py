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

"""AT1.4: Multi-profile service startup and routing tests."""

from __future__ import annotations

import pytest

from cloud_dog_config import load_config
from cloud_dog_config.bind import bind_model
from cloud_dog_config.profiles import resolve_profile


class TestMultiProfileService:
    def test_multi_profile_selection_with_fallback_and_typed_bind(self, tmp_path) -> None:  # type: ignore[no-untyped-def]
        pydantic = pytest.importorskip("pydantic")

        class StorageProfile(pydantic.BaseModel):
            backend: str
            bucket: str

        defaults = tmp_path / "defaults.yaml"
        config = tmp_path / "config.yaml"
        defaults.write_text(
            "storage:\n"
            "  profiles:\n"
            "    default:\n"
            "      backend: s3\n"
            "      bucket: default-bucket\n"
            "    archive:\n"
            "      backend: s3\n"
            "      bucket: archive-bucket\n",
            encoding="utf-8",
        )
        config.write_text("", encoding="utf-8")

        cfg = load_config(defaults_yaml=str(defaults), config_yaml=str(config), vault_enabled=False)

        archive = resolve_profile(cfg, "archive", base_path="storage.profiles")
        assert archive["bucket"] == "archive-bucket"
        archive_model = bind_model(cfg, "storage.profiles.archive", StorageProfile)
        assert archive_model.backend == "s3"

        missing = resolve_profile(cfg, "missing-profile", base_path="storage.profiles")
        assert missing["bucket"] == "default-bucket"
        default_model = bind_model(cfg, "storage.profiles.default", StorageProfile)
        assert default_model.bucket == "default-bucket"
