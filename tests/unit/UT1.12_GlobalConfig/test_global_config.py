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

"""UT1.12: GlobalConfig — immutability and access tests."""

from __future__ import annotations

import threading

import pytest

from cloud_dog_config.config import GlobalConfig, freeze_tree, utc_now


class TestGlobalConfig:
    def test_dot_access(self) -> None:
        cfg = GlobalConfig(data=freeze_tree({"a": {"b": 1}}), version="1", loaded_at=utc_now(), sources=())
        assert cfg.get("a.b") == 1
        assert cfg.get("a.missing", default=9) == 9

    def test_immutability(self) -> None:
        cfg = GlobalConfig(data=freeze_tree({"a": 1}), version="1", loaded_at=utc_now(), sources=())
        with pytest.raises(Exception):
            # dataclass frozen
            cfg.version = "2"  # type: ignore[misc]

    def test_thread_safe_reads(self) -> None:
        cfg = GlobalConfig(data=freeze_tree({"a": {"b": 1}}), version="1", loaded_at=utc_now(), sources=())
        errors: list[Exception] = []

        def worker() -> None:
            try:
                for _ in range(1000):
                    assert cfg.get("a.b") == 1
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors
