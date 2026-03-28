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

"""UT1.19: Typed model bind tests."""

from __future__ import annotations

import builtins

import pytest

from cloud_dog_config.bind import bind_model
from cloud_dog_config.config import GlobalConfig, freeze_tree, utc_now
from cloud_dog_config.errors import ConfigBindError


class TestTypedModelBind:
    def test_bind_valid_subtree(self) -> None:
        pydantic = pytest.importorskip("pydantic")

        class ServiceModel(pydantic.BaseModel):
            host: str
            port: int

        cfg = GlobalConfig(
            data=freeze_tree({"service": {"host": "127.0.0.1", "port": 8080}}),
            version="1",
            loaded_at=utc_now(),
            sources=(),
        )
        model = bind_model(cfg, "service", ServiceModel)
        assert model.host == "127.0.0.1"
        assert model.port == 8080

    def test_bind_validation_failure_raises_field_detail(self) -> None:
        pydantic = pytest.importorskip("pydantic")

        class ServiceModel(pydantic.BaseModel):
            host: str
            port: int

        cfg = GlobalConfig(
            data=freeze_tree({"service": {"host": "127.0.0.1", "port": "bad"}}),
            version="1",
            loaded_at=utc_now(),
            sources=(),
        )
        with pytest.raises(ConfigBindError, match="port"):
            bind_model(cfg, "service", ServiceModel)

    def test_missing_path_raises(self) -> None:
        pydantic = pytest.importorskip("pydantic")

        class ServiceModel(pydantic.BaseModel):
            host: str

        cfg = GlobalConfig(data=freeze_tree({"service": {}}), version="1", loaded_at=utc_now(), sources=())
        with pytest.raises(ConfigBindError, match="not found"):
            bind_model(cfg, "service.http", ServiceModel)

    def test_import_guard_when_pydantic_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cfg = GlobalConfig(data=freeze_tree({"service": {"host": "x"}}), version="1", loaded_at=utc_now(), sources=())

        original_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
            if name == "pydantic":
                raise ImportError("pydantic missing")
            return original_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        with pytest.raises(ImportError, match="requires optional dependency 'pydantic'"):
            bind_model(cfg, "service", dict)  # type: ignore[arg-type]
