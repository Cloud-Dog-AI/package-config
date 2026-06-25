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

"""IT1.2: Vault Object Bundle — real Vault bundle resolution (env-gated)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from collections.abc import Mapping

import pytest

from cloud_dog_config import load_config
from tests.integration.vault_discovery import make_client, split_mount_point


def _vault_env_ready() -> bool:
    return (
        bool(os.environ.get("VAULT_ADDR"))
        and bool(os.environ.get("VAULT_TOKEN"))
        and bool(os.environ.get("VAULT_MOUNT_POINT"))
    )


def _effective_prefix(base_prefix: str) -> str:
    cfg_path = os.environ.get("VAULT_CONFIG_PATH", "").strip().strip("/")
    return "/".join([p for p in (base_prefix.strip().strip("/"), cfg_path) if p])


def _to_plain(value: object) -> object:
    if isinstance(value, Mapping):
        return {k: _to_plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_plain(v) for v in value]
    if isinstance(value, tuple):
        return [_to_plain(v) for v in value]
    return value


def _extract_root_tree(payload: object) -> dict[str, object] | None:
    if not isinstance(payload, Mapping):
        return None
    json_payload = payload.get("json")
    if isinstance(json_payload, Mapping):
        return dict(json_payload)
    content = payload.get("content")
    if isinstance(content, str):
        try:
            decoded = json.loads(content)
        except Exception:  # noqa: BLE001
            return None
        if isinstance(decoded, Mapping):
            return dict(decoded)
    return dict(payload)


def _read_root_tree(*, client: object, mount: str, prefix: str) -> dict[str, object] | None:
    if not prefix:
        return None
    try:
        response = client.secrets.kv.v2.read_secret_version(  # type: ignore[attr-defined]
            mount_point=mount,
            path=prefix,
            raise_on_deleted_version=True,
        )
    except Exception:  # noqa: BLE001
        return None
    payload = (response or {}).get("data", {}).get("data", None)
    return _extract_root_tree(payload)


def _discover_bundle_path(tree: object, path: tuple[str, ...] = ()) -> tuple[tuple[str, ...], dict[str, object]] | None:
    if not isinstance(tree, Mapping):
        return None
    if len(path) >= 2 and tree:
        return path, dict(tree)
    for key in sorted(tree):
        if not isinstance(key, str):
            continue
        result = _discover_bundle_path(tree[key], path + (key,))
        if result is not None:
            return result
    return None


def _fingerprint(value: object) -> str:
    payload = json.dumps(_to_plain(value), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class TestVaultObjectBundle:
    def test_real_vault_object_bundle(self, tmp_path: Path) -> None:
        # IT tests must fail (not skip) when required real env/settings are unavailable.
        if not _vault_env_ready():
            pytest.fail(
                "Vault env not configured; run with --env tests/env-IT --env /opt/iac/Development/cloud-dog-ai/env-vault"
            )

        mount, base_prefix = split_mount_point(os.environ["VAULT_MOUNT_POINT"])
        prefix = _effective_prefix(base_prefix)

        client = make_client(addr=os.environ["VAULT_ADDR"], token=os.environ["VAULT_TOKEN"])
        root_tree = _read_root_tree(client=client, mount=mount, prefix=prefix)
        if root_tree is None:
            pytest.fail("Unable to read Vault root config tree for bundle lookup integration test.")

        discovered = _discover_bundle_path(root_tree)
        if discovered is None:
            pytest.fail("No object bundle discovered in Vault root config tree for bundle integration test.")

        path_parts, expected_bundle = discovered
        identifier = "vault." + ".".join(path_parts) + ".*"

        defaults = tmp_path / "defaults.yaml"
        defaults.write_text(
            f'db:\n  creds: "${{{identifier}}}"\n',
            encoding="utf-8",
        )

        cfg = load_config(defaults_yaml=str(defaults), config_yaml=str(tmp_path / "config.yaml"), vault_enabled=True)
        got = cfg.get("db.creds")
        assert _fingerprint(got) == _fingerprint(expected_bundle), "Resolved bundle mismatch for discovered Vault path."
