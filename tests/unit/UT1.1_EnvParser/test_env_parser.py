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

"""UT1.1: Env Parser — KEY=value parsing tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from cloud_dog_config.env_parser import EnvFileError, parse_env_file, parse_env_files


class TestEnvParser:
    def test_ignores_comments_and_empty_lines(self, tmp_path: Path) -> None:
        p = tmp_path / "env"
        p.write_text(
            "# comment\n\nKEY1=value1\nKEY2=value2 # trailing comment\n",
            encoding="utf-8",
        )
        d = parse_env_file(str(p))
        assert d["KEY1"] == "value1"
        assert d["KEY2"] == "value2"

    def test_preserves_hash_in_value(self, tmp_path: Path) -> None:
        p = tmp_path / "env"
        p.write_text("PASS=abc#123\n", encoding="utf-8")
        d = parse_env_file(str(p))
        assert d["PASS"] == "abc#123"

    def test_rejects_export_prefix(self, tmp_path: Path) -> None:
        p = tmp_path / "env"
        p.write_text("export KEY=value\n", encoding="utf-8")
        with pytest.raises(EnvFileError):
            parse_env_file(str(p))

    def test_handles_quoted_values(self, tmp_path: Path) -> None:
        p = tmp_path / "env"
        p.write_text("A=\"x y\"\nB='z'\n", encoding="utf-8")
        d = parse_env_file(str(p))
        assert d["A"] == "x y"
        assert d["B"] == "z"

    def test_multi_file_override_order(self, tmp_path: Path) -> None:
        p1 = tmp_path / "env1"
        p2 = tmp_path / "env2"
        p1.write_text("A=1\nB=first\n", encoding="utf-8")
        p2.write_text("B=second\nC=3\n", encoding="utf-8")
        d = parse_env_files([str(p1), str(p2)])
        assert d == {"A": "1", "B": "second", "C": "3"}
