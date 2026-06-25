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

"""ST1.13 — PS-82 Scope D / PS-80 / PS-93 live key resolution self-heal.

Proves the BINDING standard: a running service resolves keys/config LIVE from the
Vault store in-process, so an operator Vault rotation (or an API-driven key edit)
takes effect on the running process within a single ``trigger_live_reload()`` — with
NO container destroy + recreate, and WITHOUT the caller re-passing env files.

This is the regression guard for the recreate-to-update CORE DEFECT: if a service
baked the RESOLVED secret VALUE into the container env at TF-apply, a rotation would
require ``terraform apply``-recreate. With live in-process resolution, the restored
Vault value is picked up on the next live read — self-healing.
"""

from __future__ import annotations

from pathlib import Path

from cloud_dog_config import get_config, load_config, trigger_live_reload


def _write_vault_store(defaults: Path, api_key_value: str) -> None:
    """Write a defaults.yaml whose api_server.api_key resolves LIVE from Vault.

    ``vault.server: mock`` + ``mock_data`` is the committed, deterministic stand-in
    for the live Vault store; mutating ``mock_data`` simulates an operator rotation
    of the same Vault path. The service config references the secret ONLY by
    ``vault.*`` identifier — it never bakes the resolved VALUE.
    """
    defaults.write_text(
        "vault:\n"
        "  server: mock\n"
        "  key: ignored\n"
        "  mock_data:\n"
        "    secret/svc/api/api_key:\n"
        f"      api_key: {api_key_value}\n"
        "api_server:\n"
        '  api_key: "${vault.svc.api.api_key}"\n',
        encoding="utf-8",
    )


class TestLiveKeyResolutionSelfHeal:
    def test_vault_rotation_takes_effect_within_one_reload_no_recreate(
        self, tmp_path: Path
    ) -> None:
        defaults = tmp_path / "defaults.yaml"
        config = tmp_path / "config.yaml"
        config.write_text("", encoding="utf-8")

        # --- initial deploy: the service resolves the key LIVE from Vault ----------
        _write_vault_store(defaults, "key-v46")
        cfg1 = load_config(
            defaults_yaml=str(defaults),
            config_yaml=str(config),
            vault_enabled=True,
        )
        assert cfg1.get("api_server.api_key") == "key-v46"

        # --- operator rotates the SAME Vault path (no code/env change, no TF) ------
        _write_vault_store(defaults, "key-v47")

        # --- self-heal: a single live reload re-reads Vault in-process ------------
        # NOTE: no env files re-passed, no container recreate — the remembered load
        # context is replayed and the vault.* identifier is re-resolved LIVE.
        cfg2 = trigger_live_reload()

        # The running config now sees the rotated value within one reload.
        assert cfg2.get("api_server.api_key") == "key-v47"
        assert cfg2.version != cfg1.version
        # The process-global snapshot is swapped atomically (same proof for get_config).
        assert get_config("api_server.api_key") == "key-v47"

    def test_trigger_live_reload_requires_prior_load(self, tmp_path: Path) -> None:
        # A fresh load establishes the context; afterwards trigger_live_reload is a
        # no-arg self-heal that re-resolves the SAME sources.
        defaults = tmp_path / "defaults.yaml"
        config = tmp_path / "config.yaml"
        config.write_text("", encoding="utf-8")
        _write_vault_store(defaults, "key-a")
        load_config(
            defaults_yaml=str(defaults),
            config_yaml=str(config),
            vault_enabled=True,
        )
        # No re-passed kwargs needed — the load context is remembered.
        reloaded = trigger_live_reload()
        assert reloaded.get("api_server.api_key") == "key-a"
