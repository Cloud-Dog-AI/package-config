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

"""UT1.17: Legacy config adapter tests."""

from __future__ import annotations

import pytest

from cloud_dog_config.compat import LegacyConfigAdapter
from cloud_dog_config.config import GlobalConfig, freeze_tree, utc_now
from cloud_dog_config.errors import ConfigImmutableError


class TestLegacyConfigAdapter:
    def test_get_and_getitem_delegate_to_global_config(self) -> None:
        cfg = GlobalConfig(
            data=freeze_tree({"service": {"name": "demo"}}),
            version="1",
            loaded_at=utc_now(),
            sources=(),
        )
        adapter = LegacyConfigAdapter(cfg)
        with pytest.warns(DeprecationWarning):
            assert adapter.get("service.name") == "demo"
        with pytest.warns(DeprecationWarning):
            assert adapter["service.name"] == "demo"

    def test_mutation_is_rejected(self) -> None:
        cfg = GlobalConfig(data=freeze_tree({"a": 1}), version="1", loaded_at=utc_now(), sources=())
        adapter = LegacyConfigAdapter(cfg, warn_on_access=False)
        with pytest.raises(ConfigImmutableError):
            adapter["a"] = 2

    def test_as_dict_returns_plain_copy(self) -> None:
        cfg = GlobalConfig(
            data=freeze_tree({"service": {"name": "demo"}, "items": [1, 2]}),
            version="1",
            loaded_at=utc_now(),
            sources=(),
        )
        adapter = LegacyConfigAdapter(cfg, warn_on_access=False)
        snapshot = adapter.as_dict("service")
        assert snapshot == {"name": "demo"}
        snapshot["name"] = "changed"
        assert cfg.get("service.name") == "demo"
