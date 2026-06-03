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

"""UT1.2: YAML Loader — YAML parsing tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from cloud_dog_config.errors import YAMLLoadError
from cloud_dog_config.yaml_loader import load_yaml


class TestYamlLoader:
    def test_loads_nested_structures(self, tmp_path: Path) -> None:
        p = tmp_path / "defaults.yaml"
        p.write_text("a:\n  b: 1\n  c:\n    - 2\n", encoding="utf-8")
        d = load_yaml(str(p))
        assert d["a"]["b"] == 1
        assert d["a"]["c"] == [2]

    def test_missing_file_missing_ok(self, tmp_path: Path) -> None:
        p = tmp_path / "missing.yaml"
        d = load_yaml(str(p), missing_ok=True)
        assert d == {}

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "missing.yaml"
        with pytest.raises(YAMLLoadError):
            load_yaml(str(p), missing_ok=False)

    def test_invalid_yaml_raises(self, tmp_path: Path) -> None:
        p = tmp_path / "bad.yaml"
        p.write_text("a: [1,2\n", encoding="utf-8")
        with pytest.raises(YAMLLoadError):
            load_yaml(str(p), missing_ok=False)
