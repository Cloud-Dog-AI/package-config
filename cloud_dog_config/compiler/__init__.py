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

# cloud_dog_config — Compile orchestrator
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Implements CM2 step 5 compile phase: resolve references, Vault
# lookups, and safe expressions inside `${...}` placeholders.
# Related requirements: FR1.4, FR1.5, FR1.7, FR1.8, FR1.9
# Related architecture: CC1.5
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Compile phase orchestrator for cloud_dog_config."""

from __future__ import annotations

import logging
from typing import Any

from cloud_dog_config.compiler.circular_detector import CircularDetector
from cloud_dog_config.compiler.evaluator import SafeExpressionError, Unresolved, evaluate
from cloud_dog_config.compiler.reference_resolver import resolve_reference_with_default
from cloud_dog_config.compiler.tokenizer import tokenize
from cloud_dog_config.compiler.vault_resolver import VaultBundle, VaultReader, resolve_vault_identifier
from cloud_dog_config.errors import CompileError, UnresolvedPlaceholderError, VaultError
from cloud_dog_config.merger import deep_merge

logger = logging.getLogger("cloud_dog_config.compiler")

_BUNDLE_SENTINEL_KEY = "__vault_bundle__"


def preprocess_directives(tree: dict[str, Any]) -> dict[str, Any]:
    """Transform directive-like placeholders into mergeable structures.

    Currently implemented:
    - `${vault.<project>.<path>.*}` at a node becomes:
      `{ "__vault_bundle__": "vault.<project>.<path>.*" }`

    This allows env/config overlays to merge nested keys into the node while
    preserving the directive for later compile-time bundle assignment.
    """
    return _preprocess_value(tree)


def compile_config(
    merged: dict[str, Any],
    *,
    env: dict[str, Any],
    vault: VaultReader | None,
    unresolved_policy: str,
    vault_enabled: bool,
) -> dict[str, Any]:
    """Compile a merged config tree by resolving `${...}` placeholders."""
    root = merged
    memo: dict[str, Any] = {}
    detector = CircularDetector()

    def get_raw(path: str) -> Any:
        """Return raw."""
        if not path:
            return root
        node: Any = root
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return Unresolved(path)
            node = node[part]
        return node

    def resolve_node(path: str) -> Any:
        """Resolve node."""
        if path in memo:
            return memo[path]
        detector.enter(path or "$")
        try:
            raw = get_raw(path)
            compiled = _compile_value(
                raw,
                path=path,
                root_raw=root,
                env=env,
                vault=vault,
                unresolved_policy=unresolved_policy,
                vault_enabled=vault_enabled,
                resolve_node=resolve_node,
                detector=detector,
            )
            memo[path] = compiled
            return compiled
        finally:
            detector.exit(path or "$")

    compiled_root = resolve_node("")
    if not isinstance(compiled_root, dict):
        raise CompileError("Compiled config root must be a mapping")
    return compiled_root


def _compile_value(
    value: Any,
    *,
    path: str,
    root_raw: dict[str, Any],
    env: dict[str, Any],
    vault: VaultReader | None,
    unresolved_policy: str,
    vault_enabled: bool,
    resolve_node: Any,
    detector: CircularDetector,
) -> Any:
    if isinstance(value, dict):
        # Vault bundle directive handling.
        if _BUNDLE_SENTINEL_KEY in value:
            directive = value.get(_BUNDLE_SENTINEL_KEY)
            if not isinstance(directive, str):
                raise CompileError("Invalid vault bundle directive")

            bundle = _resolve_identifier(
                directive,
                root_raw=root_raw,
                env=env,
                vault=vault,
                vault_enabled=vault_enabled,
                resolve_node=resolve_node,
            )

            overlay = {k: v for k, v in value.items() if k != _BUNDLE_SENTINEL_KEY}
            overlay_compiled = {
                k: _compile_value(
                    v,
                    path=f"{path}.{k}" if path else k,
                    root_raw=root_raw,
                    env=env,
                    vault=vault,
                    unresolved_policy=unresolved_policy,
                    vault_enabled=vault_enabled,
                    resolve_node=resolve_node,
                    detector=detector,
                )
                for k, v in overlay.items()
            }

            if isinstance(bundle, VaultBundle):
                base = bundle.data
            elif isinstance(bundle, Unresolved):
                if unresolved_policy == "strict":
                    raise VaultError(f"Vault bundle unresolved at {path}")
                base = {}
            else:
                # Not a dict-like bundle.
                if unresolved_policy == "strict":
                    raise VaultError(f"Vault bundle is not an object at {path}")
                base = {}

            merged = deep_merge(base, overlay_compiled)
            # Continue compiling in case vault payload includes placeholders.
            return _compile_value(
                merged,
                path=path,
                root_raw=root_raw,
                env=env,
                vault=vault,
                unresolved_policy=unresolved_policy,
                vault_enabled=vault_enabled,
                resolve_node=resolve_node,
                detector=detector,
            )

        return {
            k: _compile_value(
                v,
                path=f"{path}.{k}" if path else k,
                root_raw=root_raw,
                env=env,
                vault=vault,
                unresolved_policy=unresolved_policy,
                vault_enabled=vault_enabled,
                resolve_node=resolve_node,
                detector=detector,
            )
            for k, v in value.items()
        }

    if isinstance(value, list):
        return [
            _compile_value(
                v,
                path=f"{path}[{i}]",
                root_raw=root_raw,
                env=env,
                vault=vault,
                unresolved_policy=unresolved_policy,
                vault_enabled=vault_enabled,
                resolve_node=resolve_node,
                detector=detector,
            )
            for i, v in enumerate(value)
        ]

    if isinstance(value, str):
        if "${" not in value:
            return value

        tokens = tokenize(value)
        if len(tokens) == 1 and tokens[0].kind == "expr":
            v = _compile_expression(
                tokens[0].value,
                path=path,
                root_raw=root_raw,
                env=env,
                vault=vault,
                unresolved_policy=unresolved_policy,
                vault_enabled=vault_enabled,
                resolve_node=resolve_node,
            )
            if isinstance(v, Unresolved):
                return _apply_unresolved_policy(tokens[0].value, unresolved_policy)
            return v

        parts: list[str] = []
        for t in tokens:
            if t.kind == "literal":
                parts.append(t.value)
            else:
                v = _compile_expression(
                    t.value,
                    path=path,
                    root_raw=root_raw,
                    env=env,
                    vault=vault,
                    unresolved_policy=unresolved_policy,
                    vault_enabled=vault_enabled,
                    resolve_node=resolve_node,
                )
                if isinstance(v, Unresolved):
                    parts.append(_apply_unresolved_policy(t.value, unresolved_policy))
                else:
                    parts.append(str(v))
        return "".join(parts)

    return value


def _compile_expression(
    expression: str,
    *,
    path: str,
    root_raw: dict[str, Any],
    env: dict[str, Any],
    vault: VaultReader | None,
    unresolved_policy: str,
    vault_enabled: bool,
    resolve_node: Any,
) -> Any:
    expr = expression.strip()

    # Special-case NAME:default syntax (PS-80) when the expression is a simple reference.
    if _looks_like_ref_with_default(expr):
        v = resolve_reference_with_default(expr, config=root_raw, env=env)
        return _finalise_unresolved(v, expr, unresolved_policy)

    def resolver(ident: str) -> Any:
        """Handle resolver."""
        return _resolve_identifier(
            ident,
            root_raw=root_raw,
            env=env,
            vault=vault,
            vault_enabled=vault_enabled,
            resolve_node=resolve_node,
        )

    try:
        v = evaluate(expr, resolver)
    except SafeExpressionError as exc:
        raise CompileError(f"Unsafe expression at {path}: {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        raise CompileError(f"Expression evaluation failed at {path}: {exc}") from exc

    return _finalise_unresolved(v, expr, unresolved_policy)


def _resolve_identifier(
    ident: str,
    *,
    root_raw: dict[str, Any],
    env: dict[str, Any],
    vault: VaultReader | None,
    vault_enabled: bool,
    resolve_node: Any,
) -> Any:
    if ident.startswith("vault."):
        if not vault_enabled:
            return Unresolved(ident)
        if vault is None:
            return Unresolved(ident)
        try:
            return resolve_vault_identifier(ident, vault=vault)
        except Exception:
            return Unresolved(ident)

    # Prefer exact env key matches.
    if ident in env:
        return env[ident]

    # Resolve dotted config paths against compiled nodes.
    if "." in ident:
        v = resolve_node(ident)
        return v if not isinstance(v, Unresolved) else Unresolved(ident)

    # Fall back to merged config top-level keys without forcing root compilation re-entry.
    if ident in root_raw:
        return resolve_node(ident)

    return Unresolved(ident)


def _finalise_unresolved(value: Any, expr: str, policy: str) -> Any:
    if isinstance(value, Unresolved):
        if policy == "strict":
            raise UnresolvedPlaceholderError(f"Unresolved placeholder: {expr}")
        if policy == "warn":
            logger.warning("Unresolved placeholder kept: %s", expr)
            return Unresolved(expr)
        if policy == "empty":
            return ""
        raise CompileError(f"Unknown unresolved policy: {policy}")
    return value


def _apply_unresolved_policy(expr: str, policy: str) -> str:
    if policy == "strict":
        raise UnresolvedPlaceholderError(f"Unresolved placeholder: {expr}")
    if policy == "warn":
        logger.warning("Unresolved placeholder kept: %s", expr)
        return "${" + expr + "}"
    if policy == "empty":
        return ""
    raise CompileError(f"Unknown unresolved policy: {policy}")


def _looks_like_ref_with_default(expr: str) -> bool:
    if ":" not in expr:
        return False
    if any(op in expr for op in ("||", "==", "!=", "?", "!", "vault.")):
        return False
    # Ensure single colon and identifier-ish name.
    name, default = expr.split(":", 1)
    name = name.strip()
    default = default.strip()
    return bool(name) and bool(default) and " " not in name


def _preprocess_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _preprocess_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_preprocess_value(v) for v in value]
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("$${") or stripped.startswith("\\${"):
            stripped = "${" + stripped[3:]
        if stripped.startswith("${") and stripped.endswith("}"):
            inner = stripped[2:-1].strip()
            if inner.startswith("vault.") and inner.endswith(".*"):
                return {_BUNDLE_SENTINEL_KEY: inner}
        return value
    return value
