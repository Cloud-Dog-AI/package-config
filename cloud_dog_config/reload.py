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

# cloud_dog_config — Hot reload pipeline
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Implements controlled hot reload with atomic GlobalConfig swap.
# Related requirements: FR1.13, FR1.14
# Related architecture: SA1
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Hot reload helpers for cloud_dog_config."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from cloud_dog_config.audit import ReloadAuditEvent, emit_reload_event


def diff_paths(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    """Compute changed dotted paths between two config trees."""
    try:
        from cloud_dog_config.diff import config_diff

        return [change.path for change in config_diff(old, new, redact=False)]
    except Exception:
        out: list[str] = []
        _diff(old, new, prefix="", out=out)
        return out


def _diff(old: Any, new: Any, *, prefix: str, out: list[str]) -> None:
    if type(old) != type(new):  # noqa: E721
        out.append(prefix or "$")
        return
    if isinstance(old, dict):
        keys = set(old.keys()) | set(new.keys())
        for k in sorted(keys):
            p = f"{prefix}.{k}" if prefix else k
            if k not in old or k not in new:
                out.append(p)
            else:
                _diff(old[k], new[k], prefix=p, out=out)
        return
    if isinstance(old, (list, tuple)):
        if len(old) != len(new):
            out.append(prefix or "$")
            return
        for i, (a, b) in enumerate(zip(old, new, strict=True)):
            _diff(a, b, prefix=f"{prefix}[{i}]", out=out)
        return
    if old != new:
        out.append(prefix or "$")


def emit_reload_audit(
    *,
    actor: str,
    outcome: str,
    old: dict[str, Any] | Any,
    new: dict[str, Any] | Any,
    vault_reads: int,
    new_version: str,
) -> None:
    """Emit reload audit."""
    changes: list[dict[str, Any]] = []
    changed_paths: list[str]
    try:
        from cloud_dog_config.diff import config_diff

        diff_result = config_diff(old, new, redact=True)
        changed_paths = [item.path for item in diff_result]
        changes = [_change_as_dict(item) for item in diff_result]
    except Exception:
        changed_paths = diff_paths(old, new)

    event = ReloadAuditEvent(
        actor=actor,
        outcome=outcome,
        changed_paths=changed_paths,
        vault_reads=vault_reads,
        new_version=new_version,
        changes=changes,
    )
    emit_reload_event(event)


def _change_as_dict(change: Any) -> dict[str, Any]:
    try:
        return asdict(change)
    except Exception:
        return {
            "path": getattr(change, "path", ""),
            "change_type": getattr(change, "change_type", ""),
            "old_value": getattr(change, "old_value", None),
            "new_value": getattr(change, "new_value", None),
        }
