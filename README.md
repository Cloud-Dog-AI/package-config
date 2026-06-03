# platform-config

**Package:** `cloud_dog_config`  
**Standard:** PS-80 (Configuration Management)  
**Version:** `0.2.0`  
**Status:** Implemented

## Purpose

Drop-in Python library implementing the PS-80 configuration management standard. Provides deterministic config loading, Vault secret resolution, safe expression evaluation, and an immutable `GlobalConfig` runtime object.

## Key Features

- Canonical precedence chain: `os.environ → env-file(s) → config.yaml → defaults.yaml`
- Config compile phase: `${vault.*}` lookups, `${ENV_VAR}` references, `||` fallbacks, `?:` ternaries, `+` string concatenation, `==`/`!=` equality, `!` negation
- Escaped-placeholder compatibility for env/shell/docker: `$${...}` and `\${...}` are treated as `${...}`
- Vault object/bundle assignment (deep-merge entire secret groups)
- Immutable `GlobalConfig` snapshot with version tracking
- Safe expression evaluator (no arbitrary code execution)
- Secret redaction utilities
- Hot reload pipeline with audit events
- Post-compile transform hook chain (`transforms=[...]`)
- Environment metadata accessor (`get_env_metadata()`)
- Legacy migration adapter (`LegacyConfigAdapter`)
- Multi-profile resolver (`resolve_profile`)
- Typed model binding (`bind_model`)
- Structured config diff + redacted export utilities
- Reload timeout protection (`reload_config(timeout_s=...)`)
- Pytest plugin with `--env` enforcement
- Zero framework dependency (works with FastAPI, Flask, CLI, etc.)

## Dependencies

- **Required:** `pyyaml`
- **Optional:** `hvac` (Vault client), `pydantic` (schema validation)

## Expression Language

Config values support `${...}` expressions with operators for URL composition and conditional logic:

```yaml
# URL from parts with fallback defaults
api_url: ${SCHEME || 'https'}://${API_HOST}:${API_PORT || '8080'}/api/v1

# Conditional SSL
verify_ssl: ${ENV == 'production' ? true : false}

# Vault secret with env override
db_password: ${MY_DB_PASS || vault.dev.db.password || 'changeme'}

# String concatenation inside ternary
url: ${SSL ? 'https://' + HOST : 'http://' + HOST}
```

See [Expression Language Reference](docs/EXPRESSION-LANGUAGE.md) for full documentation.

## Documents

- [EXPRESSION-LANGUAGE.md](docs/EXPRESSION-LANGUAGE.md) — Expression syntax, operators, URL patterns
- [REQUIREMENTS.md](REQUIREMENTS.md) — Functional and non-functional requirements
- [ARCHITECTURE.md](ARCHITECTURE.md) — Module layout, component design, integration pattern
- [TESTS.md](TESTS.md) — Test plan, directory structure, coverage map

## Quick Start

```python
from cloud_dog_config import load_config, get_config

config = load_config(env_files=["private/env-test"])
model = get_config("llm.model")
```

## Installation

```bash
pip install cloud-dog-config
```

## API Overview

- `load_config(...)` loads and compiles layered configuration input.
- `get_config(...)` reads values from the active config snapshot.
- `bind_model(...)` validates config into typed consumer models.

## Examples

- Load layered config from `tests/env-UT`, `config.yaml`, and `defaults.yaml`.
- Resolve Vault-backed values through `${vault.*}` expressions at runtime.
- Bind compiled config into a typed model for service startup.

## Validation Status (2026-02-18)

- Package implemented and built: `cloud_dog_config-0.2.0`
- Quality gates run in this uplift:
  - `pytest tests --env tests/env-IT -q` -> `103 passed, 3 skipped`
  - `pytest tests --env tests/env-UT -q` -> `103 passed, 3 skipped`
  - `ruff check cloud_dog_config tests` -> pass
  - `ruff format --check cloud_dog_config tests` -> pass
  - `python -m build --no-isolation` -> pass (sdist + wheel)

---

## Licence

Apache-2.0 — Copyright (c) 2026 Cloud-Dog, Viewdeck Engineering Limited
