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

"""UT1.15: Post-compile transform hook tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from cloud_dog_config import get_config, load_config
from cloud_dog_config.errors import ConfigTransformError
from cloud_dog_config.transform import apply_transforms


class TestPostCompileTransform:
    def test_apply_transforms_in_order(self) -> None:
        def first(tree: dict[str, object]) -> dict[str, object]:
            updated = dict(tree)
            updated["service"] = {"name": "demo"}
            return updated

        def second(tree: dict[str, object]) -> dict[str, object]:
            updated = dict(tree)
            updated["service"] = {"name": f"{tree['service']['name']}-v2"}  # type: ignore[index]
            return updated

        out = apply_transforms({}, [first, second])
        assert out["service"]["name"] == "demo-v2"  # type: ignore[index]

    def test_transform_failure_raises_named_error(self) -> None:
        def bad_transform(tree: dict[str, object]) -> dict[str, object]:
            raise RuntimeError("boom")

        with pytest.raises(ConfigTransformError, match="bad_transform"):
            apply_transforms({}, [bad_transform])

    def test_load_config_applies_transform_before_schema(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.yaml"
        config = tmp_path / "config.yaml"
        defaults.write_text("service:\n  old_name: legacy\n", encoding="utf-8")
        config.write_text("", encoding="utf-8")

        def remap(tree: dict[str, object]) -> dict[str, object]:
            service = dict(tree.get("service", {}))  # type: ignore[arg-type]
            service["name"] = service.pop("old_name", "unknown")
            out = dict(tree)
            out["service"] = service
            return out

        cfg = load_config(
            defaults_yaml=str(defaults),
            config_yaml=str(config),
            schema={"required": ["service"]},
            transforms=[remap],
            vault_enabled=False,
        )
        assert cfg.get("service.name") == "legacy"
        assert get_config("service.name") == "legacy"
