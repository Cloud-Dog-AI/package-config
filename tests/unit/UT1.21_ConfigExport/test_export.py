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

"""UT1.21: Config export tests."""

from __future__ import annotations

from cloud_dog_config.config import GlobalConfig, freeze_tree, utc_now
from cloud_dog_config.export import export_config
from cloud_dog_config.redaction import REDACTED_VALUE


class TestConfigExport:
    def test_export_redacted(self) -> None:
        cfg = GlobalConfig(
            data=freeze_tree({"db": {"password": "secret"}, "items": [1, 2]}),
            version="1",
            loaded_at=utc_now(),
            sources=(),
        )

        out = export_config(cfg, redact=True)
        assert out["db"]["password"] == REDACTED_VALUE
        assert out["items"] == [1, 2]
        assert isinstance(out["items"], list)

    def test_export_raw(self) -> None:
        cfg = GlobalConfig(
            data=freeze_tree({"token": "abc123", "nested": {"api_key": "key"}}),
            version="1",
            loaded_at=utc_now(),
            sources=(),
        )
        out = export_config(cfg, redact=False)
        assert out["token"] == "abc123"
        assert out["nested"]["api_key"] == "key"

    def test_export_custom_secret_patterns(self) -> None:
        cfg = GlobalConfig(
            data=freeze_tree({"private_blob": "sensitive", "safe": "ok"}),
            version="1",
            loaded_at=utc_now(),
            sources=(),
        )
        out = export_config(cfg, redact=True, secret_patterns=["private_blob"])
        assert out["private_blob"] == REDACTED_VALUE
        assert out["safe"] == "ok"
