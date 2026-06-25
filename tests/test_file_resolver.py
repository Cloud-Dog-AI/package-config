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

"""UT-FR1.19 tests for built-in resolve_file_keys transform."""

# Covers: FR1.19

from __future__ import annotations

from pathlib import Path

from cloud_dog_config import load_config
from cloud_dog_config.transforms import resolve_file_keys


def test_ut_fr1_19_01_replaces_value_when_file_exists(tmp_path: Path) -> None:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("resolved prompt", encoding="utf-8")
    tree = {"agent": {"system_prompt": "inline", "system_prompt_filename": str(prompt_file)}}

    transformed = resolve_file_keys(tree)

    assert transformed["agent"]["system_prompt"] == "resolved prompt"


def test_ut_fr1_19_02_leaves_value_when_filename_empty() -> None:
    tree = {"agent": {"system_prompt": "inline", "system_prompt_filename": "   "}}

    transformed = resolve_file_keys(tree)

    assert transformed["agent"]["system_prompt"] == "inline"


def test_ut_fr1_19_03_leaves_value_when_file_missing(tmp_path: Path) -> None:
    missing = tmp_path / "missing.txt"
    tree = {"agent": {"system_prompt": "inline", "system_prompt_filename": str(missing)}}

    transformed = resolve_file_keys(tree)

    assert transformed["agent"]["system_prompt"] == "inline"


def test_ut_fr1_19_04_removes_filename_keys_after_processing(tmp_path: Path) -> None:
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("resolved prompt", encoding="utf-8")
    tree = {"agent": {"system_prompt": "inline", "system_prompt_filename": str(prompt_file)}}

    transformed = resolve_file_keys(tree)

    assert "system_prompt_filename" not in transformed["agent"]


def test_ut_fr1_19_05_recurses_into_nested_dicts(tmp_path: Path) -> None:
    prompt_file = tmp_path / "nested.txt"
    prompt_file.write_text("nested resolved", encoding="utf-8")
    tree = {
        "agent": {
            "profiles": {
                "default": {
                    "prompt": "inline",
                    "prompt_filename": str(prompt_file),
                }
            }
        }
    }

    transformed = resolve_file_keys(tree)

    assert transformed["agent"]["profiles"]["default"]["prompt"] == "nested resolved"
    assert "prompt_filename" not in transformed["agent"]["profiles"]["default"]


def test_ut_fr1_19_06_handles_multiple_filename_keys_same_section(tmp_path: Path) -> None:
    a_file = tmp_path / "a.txt"
    b_file = tmp_path / "b.txt"
    a_file.write_text("A", encoding="utf-8")
    b_file.write_text("B", encoding="utf-8")
    tree = {
        "agent": {
            "system_prompt": "inline-a",
            "system_prompt_filename": str(a_file),
            "summary_prompt": "inline-b",
            "summary_prompt_filename": str(b_file),
        }
    }

    transformed = resolve_file_keys(tree)

    assert transformed["agent"]["system_prompt"] == "A"
    assert transformed["agent"]["summary_prompt"] == "B"
    assert "system_prompt_filename" not in transformed["agent"]
    assert "summary_prompt_filename" not in transformed["agent"]


def test_ut_fr1_19_07_load_config_transform_integration(tmp_path: Path) -> None:
    prompt_file = tmp_path / "system-prompt.txt"
    prompt_file.write_text("integration resolved prompt", encoding="utf-8")
    defaults_yaml = tmp_path / "defaults.yaml"
    config_yaml = tmp_path / "config.yaml"
    defaults_yaml.write_text(
        f"agent:\n  system_prompt: inline default\n  system_prompt_filename: {prompt_file}\n",
        encoding="utf-8",
    )
    config_yaml.write_text("", encoding="utf-8")

    cfg = load_config(
        defaults_yaml=str(defaults_yaml),
        config_yaml=str(config_yaml),
        transforms=[resolve_file_keys],
        vault_enabled=False,
    )

    assert cfg.get("agent.system_prompt") == "integration resolved prompt"
    assert cfg.get("agent.system_prompt_filename") is None


def test_ut_fr1_19_08_ignores_filename_without_matching_base_key(tmp_path: Path) -> None:
    prompt_file = tmp_path / "orphan.txt"
    prompt_file.write_text("orphan", encoding="utf-8")
    tree = {"agent": {"system_prompt_filename": str(prompt_file)}}

    transformed = resolve_file_keys(tree)

    assert transformed["agent"]["system_prompt_filename"] == str(prompt_file)


def test_ut_fr1_19_09_unreadable_file_warning_no_crash(
    tmp_path: Path,
    monkeypatch,
    caplog,
) -> None:
    prompt_file = tmp_path / "unreadable.txt"
    prompt_file.write_text("hidden", encoding="utf-8")
    tree = {"agent": {"system_prompt": "inline", "system_prompt_filename": str(prompt_file)}}

    original_read_text = Path.read_text

    def _raise_for_target(self: Path, *args, **kwargs) -> str:
        if self == prompt_file:
            raise OSError("permission denied")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", _raise_for_target)

    with caplog.at_level("WARNING"):
        transformed = resolve_file_keys(tree)

    assert transformed["agent"]["system_prompt"] == "inline"
    assert "system_prompt_filename" not in transformed["agent"]
    assert "Failed to read file for system_prompt" in caplog.text
