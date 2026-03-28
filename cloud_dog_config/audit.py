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

# cloud_dog_config — Reload audit event emission
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Emits reload audit events (diff summary, validation result, Vault
# reads). Integrates with cloud_dog_logging if available, otherwise logs to
# stdlib logging.
# Related requirements: FR1.14
# Related architecture: SA1
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Reload audit event emission."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("cloud_dog_config.audit")


@dataclass(frozen=True, slots=True)
class ReloadAuditEvent:
    """Audit event for config reload."""

    actor: str
    outcome: str
    changed_paths: list[str]
    vault_reads: int
    new_version: str
    changes: list[dict[str, object]] | None = None


_last_event: ReloadAuditEvent | None = None


def emit_reload_event(event: ReloadAuditEvent) -> None:
    """Emit a reload audit event."""
    global _last_event
    _last_event = event

    # Attempt to integrate with cloud_dog_logging audit logger if present.
    try:
        from cloud_dog_logging import get_audit_logger  # type: ignore
        from cloud_dog_logging.audit_schema import Actor  # type: ignore

        audit = get_audit_logger()
        actor = Actor(type="system", id=event.actor)
        audit.log_config_change(
            actor=actor,
            diff_summary={"changed_paths": event.changed_paths, "changes": event.changes or []},
            outcome=event.outcome,
            vault_reads=event.vault_reads,
            new_version=event.new_version,
        )
        return
    except Exception:
        pass

    logger.info(
        "Config reload audit",
        extra={
            "actor": event.actor,
            "outcome": event.outcome,
            "changed_paths": event.changed_paths,
            "changes": event.changes or [],
            "vault_reads": event.vault_reads,
            "new_version": event.new_version,
        },
    )


def get_last_event() -> ReloadAuditEvent | None:
    """Return the last emitted reload audit event (test support)."""
    return _last_event
