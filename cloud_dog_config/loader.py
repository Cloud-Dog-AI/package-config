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

# cloud_dog_config — Loader orchestrator
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Orchestrates PS-80 CM2 lifecycle steps 1-7: load defaults.yaml,
#   load config.yaml, parse env files, read os.environ, compile placeholders,
#   apply post-compile transforms, validate schema, freeze GlobalConfig, and
#   manage reload lifecycle.
# Related requirements: FR1.1, FR1.2, FR1.3, FR1.4, FR1.11, FR1.12, FR1.13,
#   FR1.19, FR1.26
# Related architecture: CC1.1
#
# Recent changes:
# - 2026-02-18: Added transform hooks and timeout-safe reload.
# - 2026-02-15: Initial implementation.

"""Configuration loader orchestrator."""

from __future__ import annotations

import os
import re
import threading
from collections.abc import Callable
from typing import Any

from cloud_dog_config.cli import normalise_env_files
from cloud_dog_config.coercion import coerce
from cloud_dog_config.compiler import compile_config, preprocess_directives
from cloud_dog_config.config import GlobalConfig, freeze_tree, utc_now
from cloud_dog_config.env_parser import parse_env_file
from cloud_dog_config.errors import ConfigError, ConfigReloadTimeoutError, SchemaValidationError
from cloud_dog_config.merger import deep_merge
from cloud_dog_config.naming import env_to_path
from cloud_dog_config.reload import emit_reload_audit
from cloud_dog_config.schema.secret_scanner import scan_for_secrets
from cloud_dog_config.schema.validator import validate_schema
from cloud_dog_config.transform import apply_transforms
from cloud_dog_config.compiler.tokenizer import tokenize
from cloud_dog_config.vault.client import VaultClient, VaultConnectionConfig
from cloud_dog_config.vault.mock_client import MockVaultClient


_CONFIG_LOCK = threading.Lock()
_CURRENT: GlobalConfig | None = None
_VERSION_COUNTER = 0
#: The kwargs of the most recent successful ``load_config`` call. Remembered so a
#: live reload (PS-80 hot reload / PS-93 Vault rotation self-heal) can re-run the
#: SAME load context — re-resolving ``vault.*`` identifiers LIVE in-process — without
#: the caller having to re-pass env files. A bare ``reload_config()`` previously
#: reloaded with defaults, dropping the service's env files; ``trigger_live_reload``
#: closes that gap.
_LAST_LOAD_KWARGS: dict[str, Any] = {}
_ENV_IDENT_RE = re.compile(r"\b[A-Z_][A-Z0-9_]*\b")
_EXPR_IDENT_IGNORE = frozenset({"TRUE", "FALSE", "NULL"})


def load_config(
    env_files: list[str] | None = None,
    config_yaml: str = "config.yaml",
    defaults_yaml: str = "defaults.yaml",
    schema: type | dict | None = None,
    unresolved_policy: str = "strict",
    vault_enabled: bool = True,
    transforms: list[Callable[[dict[str, Any]], dict[str, Any]]] | None = None,
) -> GlobalConfig:
    """Load, merge, compile, transform, validate, and freeze configuration."""
    load_kwargs: dict[str, Any] = {
        "env_files": env_files,
        "config_yaml": config_yaml,
        "defaults_yaml": defaults_yaml,
        "schema": schema,
        "unresolved_policy": unresolved_policy,
        "vault_enabled": vault_enabled,
        "transforms": transforms,
    }
    compiled, sources = _build_compiled_tree(**load_kwargs)
    result = _commit_config(compiled=compiled, sources=sources)
    # Remember the load context so a live reload re-resolves the SAME sources
    # (incl. Vault) without the caller re-passing env files (PS-80 / PS-93).
    global _LAST_LOAD_KWARGS
    _LAST_LOAD_KWARGS = dict(load_kwargs)
    return result


def reload_config(timeout_s: float = 30.0, **kwargs: Any) -> GlobalConfig:
    """Reload configuration with timeout protection and atomic swap."""
    old = _CURRENT
    effective_timeout = _resolve_reload_timeout(timeout_s, old)

    result: dict[str, Any] = {}
    error: dict[str, Exception] = {}
    done = threading.Event()

    def worker() -> None:
        """Handle worker."""
        try:
            compiled, sources = _build_compiled_tree(**kwargs)
            result["compiled"] = compiled
            result["sources"] = sources
        except Exception as exc:  # noqa: BLE001
            error["exception"] = exc
        finally:
            done.set()

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    if not done.wait(timeout=effective_timeout):
        raise ConfigReloadTimeoutError(f"Reload timed out after {effective_timeout:.3f}s")

    if "exception" in error:
        raise error["exception"]

    compiled = result["compiled"]
    sources = result["sources"]
    new = _commit_config(compiled=compiled, sources=sources)

    if old is not None:
        emit_reload_audit(
            actor="cloud_dog_config",
            outcome="success",
            old=old,
            new=new,
            vault_reads=0,
            new_version=new.version,
        )
    return new


def trigger_live_reload(timeout_s: float = 30.0) -> GlobalConfig:
    """Re-resolve config LIVE from the same sources, incl. Vault (PS-80/PS-93/PS-71).

    This is the canonical platform self-heal / hot-reload entry point. It re-runs the
    loader with the **remembered** load context (the env files + config/defaults yaml
    of the most recent ``load_config``), so ``vault.*`` identifiers are re-read LIVE
    from Vault in-process — NOT from any env-baked resolved value.

    Use it as the standard trigger after:
      * an API-key / profile / Settings CRUD via the platform's own core API (PS-71
        API-Keys CRUD operates on the live store), OR
      * an operator Vault rotation (PS-93).

    The new value takes effect on the running service within this single reload, with
    **NO container destroy + recreate**. This makes the stale-key problem self-healing:
    once live-resolution is deployed, restored Vault values take effect on the next
    live read. The container ``env``/TF MUST pass only ``VAULT_TOKEN`` + the config
    path (``VAULT_ADDR``/``VAULT_TOKEN``/``VAULT_CONFIG_PATH`` bridge to ``vault.*``),
    never resolved secret VALUES — baking values reintroduces the recreate-to-update
    CORE DEFECT.

    Returns:
        The newly-committed GlobalConfig (atomic swap; the prior snapshot is replaced).

    Raises:
        ConfigError: if no prior ``load_config`` established a load context.
    """
    if not _LAST_LOAD_KWARGS:
        raise ConfigError(
            "trigger_live_reload requires a prior load_config to establish the "
            "load context (env files + yaml sources)."
        )
    return reload_config(timeout_s=timeout_s, **_LAST_LOAD_KWARGS)


def get_config(path: str | None = None) -> Any:
    """Get the current GlobalConfig or a dotted sub-path."""
    if _CURRENT is None:
        raise ConfigError("Config not loaded")
    if path is None:
        return _CURRENT
    return _CURRENT.get(path)


def _build_compiled_tree(
    env_files: list[str] | None = None,
    config_yaml: str = "config.yaml",
    defaults_yaml: str = "defaults.yaml",
    schema: type | dict | None = None,
    unresolved_policy: str = "strict",
    vault_enabled: bool = True,
    transforms: list[Callable[[dict[str, Any]], dict[str, Any]]] | None = None,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    """Build a compiled/validated config tree without mutating global state."""
    env_files_norm = normalise_env_files(env_files)

    # Step 1: defaults.yaml
    from cloud_dog_config.yaml_loader import load_yaml

    defaults_raw = load_yaml(defaults_yaml, missing_ok=False)
    defaults_raw = preprocess_directives(defaults_raw)
    findings = scan_for_secrets(defaults_raw)
    if findings:
        raise ConfigError(f"defaults.yaml contains likely secrets at: {findings}")

    # Step 2: config.yaml (optional)
    config_raw = load_yaml(config_yaml, missing_ok=True)
    config_raw = preprocess_directives(config_raw)

    # Step 3: env files (optional)
    merged: dict[str, Any] = deep_merge(defaults_raw, config_raw)

    env_kv: dict[str, Any] = {}
    for env_path in env_files_norm:
        parsed = parse_env_file(env_path)
        for k, v in parsed.items():
            env_kv[k] = coerce(v)
        merged = deep_merge(merged, _env_kv_to_tree(parsed, base=merged))

    # Step 4: os.environ (restricted)
    os_kv = _select_relevant_os_environ(base=merged)
    for k, v in os_kv.items():
        env_kv[k] = coerce(v)
    merged = deep_merge(merged, _env_kv_to_tree(os_kv, base=merged))

    # Step 5: compile placeholders
    vault_client = _create_vault_client(merged) if vault_enabled else None
    compiled = compile_config(
        merged,
        env=env_kv,
        vault=vault_client,
        unresolved_policy=unresolved_policy,
        vault_enabled=vault_enabled,
    )

    # Step 5a: post-compile transform hook
    if transforms:
        compiled = apply_transforms(compiled, transforms)

    # Step 6: schema validation
    try:
        validate_schema(compiled, schema)
    except SchemaValidationError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise SchemaValidationError(str(exc)) from exc

    sources = _build_sources(
        defaults_yaml=defaults_yaml,
        config_yaml=config_yaml,
        env_files=env_files_norm,
    )
    return compiled, sources


def _commit_config(*, compiled: dict[str, Any], sources: tuple[str, ...]) -> GlobalConfig:
    global _VERSION_COUNTER, _CURRENT
    with _CONFIG_LOCK:
        _VERSION_COUNTER += 1
        version = str(_VERSION_COUNTER)
        loaded_at = utc_now()
        frozen = GlobalConfig(
            data=freeze_tree(compiled),
            version=version,
            loaded_at=loaded_at,
            sources=sources,
        )
        _CURRENT = frozen
        return frozen


def _resolve_reload_timeout(timeout_s: float, current: GlobalConfig | None) -> float:
    configured_timeout: float | None = None
    if current is not None:
        candidate = current.get("config.reload_timeout_s", None)
        if isinstance(candidate, (int, float)):
            configured_timeout = float(candidate)

    effective = timeout_s
    if configured_timeout is not None and timeout_s == 30.0:
        effective = configured_timeout
    if effective <= 0:
        raise ConfigReloadTimeoutError("Reload timeout must be > 0 seconds")
    return effective


def _env_kv_to_tree(kv: dict[str, str], *, base: dict[str, Any]) -> dict[str, Any]:
    tree: dict[str, Any] = {}
    for k, v in kv.items():
        vault_path = _canonical_vault_env_path(k)
        if vault_path is not None:
            _set_path(tree, vault_path, coerce(v))
            continue
        p = env_to_path(k, prefix="CLOUD_DOG") or env_to_path(k)
        if p is not None:
            _set_path(tree, p, coerce(v))
        elif k in base:
            tree[k] = coerce(v)
    return tree


def _set_path(tree: dict[str, Any], dotted: str, value: Any) -> None:
    node = tree
    parts = [p for p in dotted.split(".") if p]
    for part in parts[:-1]:
        if part not in node or not isinstance(node[part], dict):
            node[part] = {}
        node = node[part]
    node[parts[-1]] = value


def _canonical_vault_env_path(env_key: str) -> str | None:
    key = env_key.strip().upper()
    direct = {
        "VAULT_ADDR": "vault.server",
        "VAULT_SERVER": "vault.server",
        "VAULT_TOKEN": "vault.key",
        "VAULT_KEY": "vault.key",
        "VAULT_MOUNT_POINT": "vault.mount_point",
        "VAULT_CONFIG_PATH": "vault.config_path",
    }
    if key in direct:
        return direct[key]

    if "__" not in key:
        return None

    parts = key.split("__")
    if not parts or parts[0] != "CLOUD_DOG":
        return None

    try:
        idx = parts.index("VAULT")
    except ValueError:
        return None

    if idx + 1 >= len(parts):
        return None

    field = "_".join(parts[idx + 1 :])
    scoped = {
        "ADDR": "vault.server",
        "SERVER": "vault.server",
        "TOKEN": "vault.key",
        "KEY": "vault.key",
        "MOUNT_POINT": "vault.mount_point",
        "MOUNT": "vault.mount_point",
        "CONFIG_PATH": "vault.config_path",
        "PATH": "vault.config_path",
    }
    return scoped.get(field)


def _select_relevant_os_environ(*, base: dict[str, Any]) -> dict[str, str]:
    # Avoid pulling in the entire process environment. Only accept:
    # - keys using the APPNAME__level convention
    # - keys that already exist at the base config top level
    # - keys referenced by ${PLACEHOLDER} expressions in merged config values
    # - raw VAULT_* bridge vars only when vault.* is not already explicitly set
    out: dict[str, str] = {}
    placeholder_vars = _collect_placeholder_vars(base)

    vault_cfg = base.get("vault") if isinstance(base.get("vault"), dict) else {}
    vault_cfg = vault_cfg if isinstance(vault_cfg, dict) else {}
    vault_existing = {
        "VAULT_ADDR": bool(str(vault_cfg.get("server", "")).strip()),
        "VAULT_TOKEN": bool(str(vault_cfg.get("key", "")).strip()),
        "VAULT_MOUNT_POINT": bool(str(vault_cfg.get("mount_point", "")).strip()),
        "VAULT_CONFIG_PATH": bool(str(vault_cfg.get("config_path", "")).strip()),
    }

    for k, v in os.environ.items():
        if k in ("VAULT_ADDR", "VAULT_TOKEN", "VAULT_MOUNT_POINT", "VAULT_CONFIG_PATH"):
            if vault_existing[k]:
                continue
            out[k] = v
            continue
        if "__" in k:
            out[k] = v
        elif k in base:
            out[k] = v
        elif k in placeholder_vars:
            out[k] = v
    return out


def _collect_placeholder_vars(tree: Any) -> set[str]:
    out: set[str] = set()
    if isinstance(tree, dict):
        for value in tree.values():
            out.update(_collect_placeholder_vars(value))
        return out
    if isinstance(tree, (list, tuple)):
        for item in tree:
            out.update(_collect_placeholder_vars(item))
        return out
    if not isinstance(tree, str) or "${" not in tree:
        return out
    try:
        tokens = tokenize(tree)
    except ValueError:
        return out
    for token in tokens:
        if token.kind != "expr":
            continue
        for candidate in _ENV_IDENT_RE.findall(token.value):
            if candidate in _EXPR_IDENT_IGNORE:
                continue
            out.add(candidate)
    return out


def _create_vault_client(compiled: dict[str, Any]) -> Any | None:
    # Vault config is expected under `vault.server` and `vault.key` (see defaults.yaml).
    vault_cfg = compiled.get("vault", {})
    if not isinstance(vault_cfg, dict):
        return None
    server = str(vault_cfg.get("server", "") or "")
    token = str(vault_cfg.get("key", "") or "")
    timeout_seconds = float(vault_cfg.get("timeout_seconds", 5) or 5)
    mount_point = str(vault_cfg.get("mount_point", "") or "")
    config_path = str(vault_cfg.get("config_path", "") or "")
    if config_path:
        mount_point = "/".join([p for p in (mount_point.strip("/"), config_path.strip("/")) if p])
    if server == "mock":
        mock_data = vault_cfg.get("mock_data", {})
        available = bool(vault_cfg.get("available", True))
        return MockVaultClient(data=mock_data if isinstance(mock_data, dict) else {}, available=available)
    if not server or not token:
        return None
    try:
        return VaultClient(
            VaultConnectionConfig(server=server, token=token, timeout_seconds=timeout_seconds, mount_point=mount_point)
        )
    except Exception:
        # Graceful degradation: behave as Vault-disabled if client cannot be created.
        return None


def _build_sources(*, defaults_yaml: str, config_yaml: str, env_files: list[str]) -> tuple[str, ...]:
    # Sources are debug-only and must not include secret values.
    parts = [
        f"defaults_yaml={defaults_yaml}",
        f"config_yaml={config_yaml}",
    ]
    if env_files:
        parts.append(f"env_files={','.join(env_files)}")
    return tuple(parts)
