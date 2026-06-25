# platform-config — Requirements

**Package:** `cloud_dog_config`  
**Version:** 0.2.0  
**Standard:** PS-80 (Configuration Management)  
**Status:** Implemented

---

## Scope / Vision

### SV1.1
The package SHALL provide a single, reusable configuration loader for all Cloud-Dog Python services, implementing the canonical precedence chain defined in PS-80 CM1.

### SV1.2
The package SHALL eliminate per-project config loader reimplementation — services import `cloud_dog_config` and receive deterministic, validated, immutable configuration.

---

## Business Objectives

### BO1.1
Reduce configuration-related bugs by enforcing a single, tested config lifecycle across all services.

### BO1.2
Enable Vault-based secret management without requiring per-project Vault client code.

### BO1.3
Support consistent hot-reload and audit of config changes across all services.

---

## Functional Requirements

### FR1.1 — Canonical Precedence Loader
The package MUST load configuration in this order (highest wins):
1. `os.environ`
2. env-file(s) (1..N, ordered)
3. `config.yaml`
4. `defaults.yaml`

### FR1.2 — Env-File Parser
The package MUST parse env-files in the platform format:
- `KEY=value` lines (no `export` prefix; shell-style comments with `#`).
- Multiple env-files supported; later files override earlier.
- Env-file paths supplied via `--env` CLI arg, config entry, or API call.

### FR1.3 — YAML Loader
The package MUST load `defaults.yaml` and `config.yaml` with deep-merge semantics:
- Dictionaries: deep-merge by key.
- Arrays/lists: replaced as a whole.
- Scalars: last writer wins.

### FR1.4 — Config Compile Phase
The package MUST implement a compile phase (PS-80 CM2 step 5) that resolves:
- `${ENV_VAR}` — environment / config references.
- `${ENV_VAR:default}` — env reference with default.
- `${vault.<project>.<path>}` — Vault scalar lookups.
- `${vault.<project>.<path>.*}` — Vault object/bundle lookups (deep-merged).
- `${vault.<project>.<path> || <fallback>}` — Vault with fallback.
- `${<expr> ? <true_val> : <false_val>}` — ternary conditional.
- `${<a> || <b>}` — fallback (first truthy).

### FR1.5 — Safe Expression Evaluator
The compiler MUST support a restricted expression language:
- **Allowed**: `||`, `? :`, `==`, `!=`, `!`, string/number/boolean/null literals, JSON object/array literals.
- **NOT allowed**: function calls, arithmetic, assignment, loops, shell expansion, import/eval.

### FR1.6 — Vault Client
The package MUST provide a thin Vault client for config compile:
- Connect using `VAULT_ADDR` and `VAULT_TOKEN` from `os.environ` (populated by sourcing `env-vault`).
- Read config from KV v2 mount `cloud_dog_ai` at path `config` (API path: `cloud_dog_ai/data/config`).
- Support dot-path access to nested config: `get("dev.models.ollama_qwen3_14b_llm1.base_url")`.
- Support both scalar and object returns.
- Handle Vault unavailability gracefully (fallback expressions or unresolved policy).
- `VAULT_MOUNT_POINT` and `VAULT_CONFIG_PATH` env vars define the mount and path — MUST NOT be hardcoded.
- Cache the full config document in memory after first fetch; invalidate on reload.

### FR1.7 — Vault Object/Bundle Assignment
When a Vault path returns a dict/object, the package MUST deep-merge it into the config tree at the target node. `os.environ` overrides of individual fields within a bundle MUST still work.

### FR1.8 — Unresolved Placeholder Policy
The package MUST support configurable unresolved placeholder handling:
- `strict` — fail startup/reload (default in production).
- `warn` — log warning, keep placeholder literal.
- `empty` — replace with empty string / null.

### FR1.9 — Circular Reference Detection
The compiler MUST detect and reject circular references at compile time.

### FR1.10 — Type Coercion
Env values (strings) MUST be coerced using:
- Schema hints (preferred).
- Safe heuristics: `true`/`false`, integers, floats, JSON objects/arrays if clearly valid, else string.

### FR1.11 — GlobalConfig (Immutable Snapshot)
After compilation, the package MUST freeze config into an immutable `GlobalConfig` object:
- All access via `GlobalConfig` only.
- `config.version` (monotonic integer or UUID).
- `config.loaded_at` (UTC timestamp).
- `config.sources` (debug-only, no secrets).

### FR1.12 — Schema Validation
The package MUST validate the compiled config against a project-provided schema before freezing.

### FR1.13 — Hot Reload
The package SHOULD support controlled hot reload:
- Repeat steps 1–7 of the startup lifecycle.
- Atomic pointer swap for `GlobalConfig`.
- Schema validation before activation.
- In-flight requests continue with old config.

### FR1.14 — Reload Audit Events
Every reload SHALL emit an audit event including: actor, diff summary (paths changed, no secret values), validation result, vault reads count, new config version ID.

### FR1.15 — Secret Redaction
The package MUST provide redaction utilities for config display, debugging, and audit output. Secret values MUST NEVER appear in logs, dumps, or error messages.

### FR1.16 — Env Naming Convention
The package MUST support the `APPNAME__level1__level2` naming convention for env vars mapping to nested config paths.

### FR1.17 — --env CLI Integration
The package MUST provide a pytest plugin or conftest helper that adds `--env` to pytest and hard-fails if not provided.

### FR1.18 — defaults.yaml Convention
The package MUST validate that `defaults.yaml` contains no secrets (configurable scan).

### FR1.19 — Post-Compile Transform Hook
The package MUST support an optional `post_compile_transform` callback invoked between compile (step 5) and freeze (step 7):
- Signature: `Callable[[dict], dict]` — receives the compiled config tree, returns transformed tree.
- Use case: deterministic project-specific remaps (e.g. legacy env/profile renames, vector profile aliasing).
- Transform failures MUST raise `ConfigTransformError` and prevent freeze.
- Multiple transforms may be chained (list of callables, executed in order).
- **Sources**: expert-agent (env/profile remap), sql-agent (prompt file indirection), file-mcp (placeholder-path overrides).

### FR1.20 — Environment Metadata Accessor
The package MUST provide a `get_env_metadata()` API returning runtime metadata without reading `os.environ` directly:
- Fields: `hostname`, `process_id`, `python_version`, `config_version`, `loaded_at`, `sources` (redacted), `vault_available` (bool), `env_file_count`.
- Use case: health/status endpoints that need env context without direct env access.
- **Source**: expert-agent (health endpoint env metadata).

### FR1.21 — Legacy Config Adapter
The package MUST provide a `LegacyConfigAdapter` helper for staged migration:
- Wraps `GlobalConfig` with mutable-looking `get(path, default)` ergonomics.
- Read-only — mutation attempts raise `ConfigImmutableError`.
- Emits deprecation warnings on each access to guide migration.
- Optional: `adapter.as_dict(path)` for code expecting raw dicts.
- **Sources**: sql-agent (mutable config callers), notification-agent (config mutation APIs), chat-client (mutable legacy configs).

### FR1.22 — Multi-Profile Resolver
The package MUST provide a `resolve_profile(config, profile_name, fallback="default")` helper:
- Returns a scoped config view for the named profile.
- Falls back to the named fallback profile if the requested profile is absent.
- Profiles are config subtrees (e.g. `storage.profiles.{name}`).
- Use case: per-request routing in multi-backend services.
- **Source**: file-mcp (multi-profile request selection).

### FR1.23 — Typed Model Bind
The package SHOULD provide a `bind_model(path, model_cls)` utility:
- Extracts the config subtree at `path` and validates/coerces it into `model_cls` (Pydantic BaseModel).
- Returns a typed, validated instance.
- Raises `ConfigBindError` on validation failure with field-level detail.
- Optional dependency on `pydantic`; raises `ImportError` with guidance if absent.
- **Source**: file-mcp (typed bind for project Pydantic models).

### FR1.24 — Config Diff Utility
The package MUST provide a `config_diff(old, new)` utility:
- Returns a structured diff of changed paths (added, removed, modified).
- Secret values MUST be redacted in diff output.
- Used by reload audit events (FR1.14) to provide diff summaries.
- **Source**: foresight (audit and diagnostics).

### FR1.25 — Config Export (Redacted)
The package MUST provide a `export_config(config, redact=True)` utility:
- Returns a serialisable dict representation of the config tree.
- When `redact=True`, all secret values are replaced with `***REDACTED***`.
- Use case: diagnostics endpoints, admin config viewers.
- **Source**: foresight (operator diagnostics).

### FR1.26 — Reload Timeout
Reload operations (FR1.13) MUST support a configurable timeout (`config.reload_timeout_s`, default 30s):
- If Vault or file I/O exceeds the timeout, reload fails cleanly without corrupting the active config.
- Timeout is separate from Vault client connect/read timeouts.
- **Source**: foresight (operational reliability).

---

## Non-Functional Requirements

### NF1.1
The package MUST have zero non-stdlib runtime dependencies beyond: `pyyaml`, `hvac` (optional, for Vault), `pydantic` (optional, for schema validation).

### NF1.2
Config loading (excluding Vault network calls) MUST complete in < 100ms for a typical project.

### NF1.3
The package MUST be thread-safe: `GlobalConfig` is immutable; reload swaps the reference atomically.

### NF1.4
The package MUST work with Python 3.10+.

### NF1.5
The package MUST be installable via pip from a local path or private PyPI.

---

## Cyber Security

### CS1.1
Secrets MUST NEVER be logged, dumped, or included in error messages.

### CS1.2
Vault tokens MUST be treated as secrets — redacted in all output.

### CS1.3
The safe expression evaluator MUST NOT allow arbitrary code execution.

---

## Acceptance Criteria

A project is compliant when:
- It uses `cloud_dog_config` for all configuration loading.
- The precedence chain is enforced and tested.
- `--env` is mandatory and tested.
- Vault substitution resolves correctly (or falls back).
- `GlobalConfig` is the single source of truth after init.
- No direct `os.environ`, env-file, YAML, or Vault reads outside the config subsystem.
