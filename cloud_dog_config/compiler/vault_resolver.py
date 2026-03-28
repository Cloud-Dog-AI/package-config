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

# cloud_dog_config — Vault resolver
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Resolves `vault.<project>.<path>` identifiers during compile phase
#   using a VaultClient-like interface.
# Related requirements: FR1.6, FR1.7
# Related architecture: CC1.5, CC1.6
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Vault lookup resolver for the compile phase."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from cloud_dog_config.compiler.evaluator import Unresolved


class VaultReader(Protocol):
    """Protocol implemented by VaultClient and MockVaultClient."""

    def read(self, path: str) -> dict[str, Any] | str | None:
        """Read a value from the given Vault path."""
        ...


@dataclass(frozen=True, slots=True)
class VaultBundle:
    """Represents a Vault object/bundle result used for deep-merge assignment."""

    data: dict[str, Any]


@dataclass(frozen=True, slots=True)
class _AliasRule:
    target: tuple[str, ...]
    transform: Callable[[Any], Any] | None = None


def _strip_suffix(value: Any, suffix: str) -> Any:
    if isinstance(value, str) and value.endswith(suffix):
        return value[: -len(suffix)]
    return value


_LEGACY_ALIASES: dict[tuple[str, ...], _AliasRule] = {
    # Legacy service endpoint path -> canonical model base URL.
    ("dev", "services", "llm1", "url"): _AliasRule(target=("dev", "models", "ollama_qwen3_14b_llm1", "base_url")),
    # Legacy search MCP URL key -> canonical URI (normalised to service base URL).
    ("dev", "services", "searchmcp0", "mcp_url"): _AliasRule(
        target=("dev", "services", "searchmcp", "uri"),
        transform=lambda v: _strip_suffix(v, "/mcp"),
    ),
    # Legacy test-data keys -> canonical github URL location.
    ("dev", "test_data", "github_repo_url"): _AliasRule(target=("dev", "storage", "github", "url")),
    ("dev", "test_data", "example_url"): _AliasRule(target=("dev", "storage", "github", "url")),
    # Legacy flights MCP URL key -> canonical search MCP URI base (best-effort compatibility).
    ("dev", "services", "flights_mcp", "api_url"): _AliasRule(
        target=("dev", "services", "searchmcp", "uri"),
        transform=lambda v: _strip_suffix(v, "/mcp"),
    ),
}


def resolve_vault_identifier(identifier: str, *, vault: VaultReader) -> Any:
    """Resolve a `vault.*` identifier to a scalar or bundle.

    Supported forms:
    - vault.<project>.<path>          -> scalar (or dict)
    - vault.<project>.<path>.*        -> bundle (dict), wrapped in VaultBundle
    """
    if not identifier.startswith("vault."):
        return Unresolved(identifier)

    is_bundle = identifier.endswith(".*")
    core = identifier[:-2] if is_bundle else identifier
    parts = core.split(".")
    if len(parts) < 2:
        return Unresolved(identifier)
    if len(parts) < 3 and not is_bundle:
        return Unresolved(identifier)

    project = parts[1]
    secret_parts = parts[2:]
    if not project:
        return Unresolved(identifier)
    if not secret_parts and not is_bundle:
        return Unresolved(identifier)
    # For kv secret paths, map dot segments to path segments.
    secret_path = "/".join(secret_parts)

    # Read from secret/<project>/<path> (primary layout).
    vault_path = f"secret/{project}" if not secret_path else f"secret/{project}/{secret_path}"
    try:
        data = vault.read(vault_path)
    except Exception:
        data = None
    if data is None:
        # Fallback layout: root config blob at secret/<config-root>, then dotted traversal.
        data = _resolve_from_root_blob(
            project=project,
            secret_parts=secret_parts,
            is_bundle=is_bundle,
            vault=vault,
        )
        if isinstance(data, Unresolved):
            return data
        if is_bundle:
            if isinstance(data, dict):
                return VaultBundle(data=data)
            return Unresolved(identifier)
        return data

    # If caller requested a bundle, require object.
    if is_bundle:
        if isinstance(data, dict):
            return VaultBundle(data=data)
        return Unresolved(identifier)

    # Scalar lookup:
    if isinstance(data, dict):
        # If the secret is an object, attempt to return the last key's value if present,
        # otherwise return the object.
        leaf = secret_parts[-1]
        if leaf in data:
            return data[leaf]
        return data

    return data


def _resolve_from_root_blob(
    *,
    project: str,
    secret_parts: list[str],
    is_bundle: bool,
    vault: VaultReader,
) -> Any:
    """Resolve identifiers from root-blob Vault layouts.

    Expected root secret shape variants:
    - direct object payload (e.g. {"dev": {...}})
    - wrapped payload with `json` object
    - wrapped payload with `content` JSON string
    """
    try:
        root = vault.read("secret")
    except Exception:
        return Unresolved("vault.root")
    if root is None:
        return Unresolved("vault.root")

    tree = _extract_root_tree(root)
    if not isinstance(tree, dict):
        return Unresolved("vault.root")

    path = [project, *secret_parts]
    value, ok = _walk(tree, path)
    if not ok:
        value, ok = _resolve_legacy_alias(tree, path)
    if not ok:
        return Unresolved(".".join(path))

    if is_bundle and not isinstance(value, dict):
        return Unresolved(".".join(path))
    return value


def _resolve_legacy_alias(tree: dict[str, Any], path: list[str]) -> tuple[Any, bool]:
    rule = _LEGACY_ALIASES.get(tuple(path))
    if rule is None:
        return None, False
    value, ok = _walk(tree, list(rule.target))
    if not ok:
        return None, False
    if rule.transform is not None:
        try:
            value = rule.transform(value)
        except Exception:
            return None, False
    return value, True


def _extract_root_tree(root: Any) -> dict[str, Any] | None:
    if isinstance(root, dict):
        raw_json = root.get("json")
        if isinstance(raw_json, dict):
            return raw_json
        content = root.get("content")
        if isinstance(content, str):
            try:
                decoded = json.loads(content)
            except Exception:
                return None
            return decoded if isinstance(decoded, dict) else None
        return root
    return None


def _walk(node: Any, parts: list[str]) -> tuple[Any, bool]:
    current = node
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return None, False
        current = current[part]
    return current, True
