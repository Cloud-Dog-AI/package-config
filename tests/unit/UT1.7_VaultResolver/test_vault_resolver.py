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

"""UT1.7: Vault Resolver — mock Vault lookups tests."""

from __future__ import annotations

import json

from cloud_dog_config.compiler.evaluator import Unresolved
from cloud_dog_config.compiler.vault_resolver import VaultBundle, resolve_vault_identifier
from cloud_dog_config.vault.mock_client import MockVaultClient


class TestVaultResolver:
    def test_scalar_lookup_from_object(self) -> None:
        vault = MockVaultClient(
            data={"secret/expert/llm/model": {"model": "qwen3"}},
        )
        v = resolve_vault_identifier("vault.expert.llm.model", vault=vault)
        assert v == "qwen3"

    def test_bundle_lookup(self) -> None:
        vault = MockVaultClient(
            data={"secret/expert/db/creds": {"username": "u", "password": "p"}},
        )
        v = resolve_vault_identifier("vault.expert.db.creds.*", vault=vault)
        assert isinstance(v, VaultBundle)
        assert v.data["username"] == "u"

    def test_project_root_bundle_lookup(self) -> None:
        vault = MockVaultClient(
            data={"secret/expert": {"username": "u", "password": "p"}},
        )
        v = resolve_vault_identifier("vault.expert.*", vault=vault)
        assert isinstance(v, VaultBundle)
        assert v.data["username"] == "u"

    def test_missing_returns_unresolved(self) -> None:
        vault = MockVaultClient(data={})
        v = resolve_vault_identifier("vault.expert.missing.value", vault=vault)
        assert isinstance(v, Unresolved)

    def test_scalar_lookup_from_root_blob_json(self) -> None:
        vault = MockVaultClient(
            data={
                "secret": {
                    "json": {
                        "dev": {
                            "services": {
                                "sqlagent0": {
                                    "api_url": "https://sqlagent0.example.test",
                                    "mcp_url": "https://sqlagent0.example.test:8443",
                                }
                            }
                        }
                    }
                }
            }
        )
        v = resolve_vault_identifier("vault.dev.services.sqlagent0.api_url", vault=vault)
        assert v == "https://sqlagent0.example.test"

    def test_bundle_lookup_from_root_blob_json(self) -> None:
        vault = MockVaultClient(
            data={
                "secret": {
                    "json": {
                        "dev": {
                            "services": {
                                "sqlagent0": {
                                    "api_url": "https://sqlagent0.example.test",
                                    "mcp_url": "https://sqlagent0.example.test:8443",
                                }
                            }
                        }
                    }
                }
            }
        )
        v = resolve_vault_identifier("vault.dev.services.sqlagent0.*", vault=vault)
        assert isinstance(v, VaultBundle)
        assert v.data["api_url"] == "https://sqlagent0.example.test"
        assert v.data["mcp_url"] == "https://sqlagent0.example.test:8443"

    def test_scalar_lookup_from_root_blob_content(self) -> None:
        payload = {
            "dev": {
                "services": {
                    "sqlagent0": {
                        "api_url": "https://sqlagent0.example.test",
                    }
                }
            }
        }
        vault = MockVaultClient(data={"secret": {"content": json.dumps(payload)}})
        v = resolve_vault_identifier("vault.dev.services.sqlagent0.api_url", vault=vault)
        assert v == "https://sqlagent0.example.test"

    def test_git_mcp_service_fields_from_root_blob_json_string(self) -> None:
        payload = {
            "dev": {
                "services": {
                    "gitmcpserver0": {
                        "api_key": "non-secret-test-key",
                        "api_url": "https://gitmcpserver0.example.test/api/v1",
                        "mcp_url": "https://gitmcpserver0.example.test/mcp",
                        "a2a_url": "https://gitmcpserver0.example.test/a2a",
                        "web_url": "https://gitmcpserver0.example.test/",
                    }
                }
            }
        }
        vault = MockVaultClient(data={"secret": {"json": json.dumps(payload)}})

        assert resolve_vault_identifier("vault.dev.services.gitmcpserver0.api_key", vault=vault) == "non-secret-test-key"
        assert (
            resolve_vault_identifier("vault.dev.services.gitmcpserver0.api_url", vault=vault)
            == "https://gitmcpserver0.example.test/api/v1"
        )
        assert (
            resolve_vault_identifier("vault.dev.services.gitmcpserver0.mcp_url", vault=vault)
            == "https://gitmcpserver0.example.test/mcp"
        )
        assert (
            resolve_vault_identifier("vault.dev.services.gitmcpserver0.a2a_url", vault=vault)
            == "https://gitmcpserver0.example.test/a2a"
        )
        assert (
            resolve_vault_identifier("vault.dev.services.gitmcpserver0.web_url", vault=vault)
            == "https://gitmcpserver0.example.test/"
        )

    def test_legacy_aliases_from_root_blob(self) -> None:
        vault = MockVaultClient(
            data={
                "secret": {
                    "json": {
                        "dev": {
                            "models": {"ollama_qwen3_14b_llm1": {"base_url": "https://llm1.example.test"}},
                            "services": {"searchmcp": {"uri": "https://searchmcp0.example.test/mcp"}},
                            "storage": {"github": {"url": "https://github.com"}},
                        }
                    }
                }
            }
        )

        assert resolve_vault_identifier("vault.dev.services.llm1.url", vault=vault) == "https://llm1.example.test"
        assert (
            resolve_vault_identifier("vault.dev.services.searchmcp0.mcp_url", vault=vault)
            == "https://searchmcp0.example.test"
        )
        assert resolve_vault_identifier("vault.dev.test_data.github_repo_url", vault=vault) == "https://github.com"
        assert resolve_vault_identifier("vault.dev.test_data.example_url", vault=vault) == "https://github.com"
