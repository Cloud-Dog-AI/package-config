# platform-config — Architecture

**Package:** `cloud_dog_config`  
**Version:** 0.2.0  
**Standard:** PS-80 (Configuration Management)  
**Status:** Implemented

---

## OV1 — Overview

`cloud_dog_config` is a drop-in Python library that implements the PS-80 configuration management standard. It provides deterministic config loading, Vault secret resolution, safe expression evaluation, and an immutable `GlobalConfig` runtime object.

### Design Goals

- **Single implementation** of the canonical precedence chain — no per-project reimplementation.
- **Hexagonal / ports-and-adapters**: core config logic is independent of Vault client, YAML parser, or web framework.
- **Zero-surprise**: identical behaviour across all services; fully testable.
- **Minimal dependencies**: only `pyyaml` required; `hvac` and `pydantic` optional.

---

## SA1 — Module Layout

```
cloud_dog_config/
  __init__.py                    # Public API: load_config, get_config, GlobalConfig
  loader.py                      # Orchestrator: precedence chain, lifecycle steps 1-7
  env_parser.py                  # Env-file parser (KEY=value format)
  yaml_loader.py                 # YAML loader with deep-merge
  merger.py                      # Deep-merge engine (dict merge, array replace, scalar overwrite)
  compiler/
    __init__.py                  # Compile orchestrator (CM2 step 5)
    tokenizer.py                 # ${...} expression tokenizer
    evaluator.py                 # Safe expression evaluator (||, ?:, ==, !=, !)
    vault_resolver.py            # Vault lookup resolution
    reference_resolver.py        # Config/env reference resolution
    circular_detector.py         # Circular reference detection
  vault/
    __init__.py
    client.py                    # Thin Vault client (hvac wrapper)
    mock_client.py               # Mock client for testing / Vault-less dev
  schema/
    __init__.py
    validator.py                 # Schema validation (pydantic or JSON Schema)
    secret_scanner.py            # Scan for secrets in defaults.yaml
  config.py                      # GlobalConfig immutable snapshot class
  coercion.py                    # Type coercion engine (string → bool/int/float/JSON)
  redaction.py                   # Secret redaction utilities
  reload.py                      # Hot reload pipeline
  audit.py                       # Reload audit event emission
  naming.py                      # APPNAME__level1__level2 convention handler
  errors.py                      # Config-specific exceptions
  cli.py                         # --env CLI argument helpers
  pytest_plugin.py               # Pytest plugin: --env option, conftest helpers
  transform.py                   # Post-compile transform hook chain (FR1.19)
  metadata.py                    # Environment metadata accessor (FR1.20)
  compat/
    __init__.py
    legacy_adapter.py            # LegacyConfigAdapter for staged migration (FR1.21)
  profiles.py                    # Multi-profile resolver helper (FR1.22)
  bind.py                        # Typed model bind utility (FR1.23, optional pydantic)
  diff.py                        # Config diff utility (FR1.24)
  export.py                      # Config export with redaction (FR1.25)
```

---

## SA2 — Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      loader.py                               │
│  Orchestrates steps 1-8 of CM2 startup lifecycle             │
│                                                              │
│  1. yaml_loader ─→ defaults.yaml                             │
│  2. yaml_loader ─→ config.yaml                               │
│  3. env_parser  ─→ env-file(s)        ┌───────────┐         │
│  4. os.environ                        │  merger.py │         │
│  5. compiler/ ───────────────────────→│ deep-merge │         │
│  5a. transform.py ─→ post-compile hooks (NEW)                │
│  6. schema/validator                  └───────────┘         │
│  7. GlobalConfig freeze                                      │
│  8. metadata.py ─→ capture EnvMetadata (NEW)                 │
└────────────────────────┬─────────────────────────────────────┘
                         │ step 5
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    compiler/                                  │
│                                                              │
│  tokenizer.py ──→ Parse ${...} expressions                   │
│       │                                                      │
│       ├──→ reference_resolver.py (config/env refs)           │
│       ├──→ vault_resolver.py ──→ vault/client.py             │
│       │         │                    │                       │
│       │         │    ┌───────────────┘                       │
│       │         ▼    ▼                                       │
│       │    Vault server (hvac)                               │
│       │    OR mock_client.py                                 │
│       │                                                      │
│       └──→ evaluator.py (||, ?:, ==, !=, !)                 │
│                                                              │
│  circular_detector.py ──→ Reject cycles                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 Migration / Compatibility (NEW)               │
│                                                              │
│  compat/legacy_adapter.py ──→ LegacyConfigAdapter            │
│  profiles.py ──→ resolve_profile()                           │
│  bind.py ──→ bind_model() (optional pydantic)                │
│  diff.py ──→ config_diff()                                   │
│  export.py ──→ export_config()                               │
└─────────────────────────────────────────────────────────────┘
```

---

## CC1 — Core Components

### CC1.1 Loader (`loader.py`)

The central orchestrator. Public API:

```python
def load_config(
    env_files: list[str] | None = None,
    config_yaml: str = "config.yaml",
    defaults_yaml: str = "defaults.yaml",
    schema: type | dict | None = None,
    unresolved_policy: str = "strict",  # strict | warn | empty
    vault_enabled: bool = True,
    transforms: list[Callable[[dict], dict]] | None = None,
) -> GlobalConfig:
    """Load, merge, compile, transform, validate, freeze."""

def get_config(path: str | None = None) -> Any:
    """Access current GlobalConfig (or a dotted sub-path)."""

def reload_config(timeout_s: float = 30.0, **kwargs) -> GlobalConfig:
    """Hot-reload with timeout guard and atomic swap."""
```

### CC1.2 Env Parser (`env_parser.py`)

- Parses `KEY=value` lines.
- Strips comments (`#`), empty lines, leading/trailing whitespace.
- NO `export` prefix support (platform convention).
- Returns `dict[str, str]`.

### CC1.3 YAML Loader (`yaml_loader.py`)

- Loads YAML files using `yaml.safe_load`.
- Returns nested `dict`.
- File-not-found returns empty dict (for optional `config.yaml`).

### CC1.4 Merger (`merger.py`)

- `deep_merge(base: dict, overlay: dict) -> dict`
- Dicts: recursive merge by key.
- Lists: overlay replaces base entirely.
- Scalars: overlay wins.
- Deterministic and side-effect-free.

### CC1.5 Compiler (`compiler/`)

Orchestrates expression resolution on the merged config tree:

1. **Tokenize** — find all `${...}` expressions in string values.
2. **Resolve references** — substitute `${ENV_VAR}` and `${ENV_VAR:default}` from merged tree.
3. **Resolve Vault** — fetch `${vault.*}` scalars and objects from Vault.
4. **Evaluate expressions** — process `||`, `?:`, `==`, `!=`, `!`.
5. **Deep-merge Vault objects** — `${vault.*.* }` results merged at target node.
6. **Detect circular references** — fail if cycles detected.
7. **Apply unresolved policy** — strict/warn/empty for remaining placeholders.

### CC1.6 Vault Client (`vault/client.py`)

- Thin wrapper around `hvac` (optional dependency).
- `VaultClient.read(path: str) -> dict | str | None`
- Connection params from already-merged config (`vault_server`, `vault_key`).
- Timeout and retry configurable.
- `mock_client.py` returns configurable test data.

### CC1.7 GlobalConfig (`config.py`)

```python
class GlobalConfig:
    """Immutable configuration snapshot."""
    
    def get(self, path: str, default=None) -> Any:
        """Dot-notation access: config.get('llm.model')"""
    
    @property
    def version(self) -> str: ...
    
    @property
    def loaded_at(self) -> datetime: ...
    
    @property
    def sources(self) -> list[str]: ...  # Debug only, no secrets
```

- Frozen after creation (no mutation).
- Thread-safe: reload swaps reference atomically.

### CC1.8 Redaction (`redaction.py`)

- `redact(config_dict, secret_patterns) -> dict` — replaces secret values with `***REDACTED***`.
- Patterns: key names containing `secret`, `password`, `key`, `token`, `credential` (configurable).
- Used by audit events, config dumps, error messages.

### CC1.9 Type Coercion (`coercion.py`)

- `coerce(value: str, hint: type | None = None) -> Any`
- Schema hints preferred; safe heuristics as fallback.
- `"true"/"false"` → bool, integers, floats, JSON objects/arrays, else string.

### CC1.10 Naming Convention (`naming.py`)

- `env_to_path("CLOUD_DOG__LLM__MODEL") -> "llm.model"`
- `path_to_env("llm.model", prefix="CLOUD_DOG") -> "CLOUD_DOG__LLM__MODEL"`
- Double-underscore (`__`) as level separator.

### CC1.11 Post-Compile Transform (`transform.py`)

```python
def apply_transforms(
    config_tree: dict,
    transforms: list[Callable[[dict], dict]],
) -> dict:
    """Chain post-compile transforms. Each receives and returns the full tree."""
```

- Invoked by `loader.py` between compile (step 5) and schema validation (step 6).
- Failures raise `ConfigTransformError` with the failing transform name.
- Transforms are deterministic — same input always produces same output.

### CC1.12 Environment Metadata (`metadata.py`)

```python
@dataclass(frozen=True)
class EnvMetadata:
    hostname: str
    process_id: int
    python_version: str
    config_version: str
    loaded_at: datetime
    sources: list[str]        # Redacted source list
    vault_available: bool
    env_file_count: int

def get_env_metadata() -> EnvMetadata:
    """Return runtime metadata from current GlobalConfig without reading os.environ."""
```

### CC1.13 Legacy Config Adapter (`compat/legacy_adapter.py`)

```python
class LegacyConfigAdapter:
    def __init__(self, config: GlobalConfig, warn_on_access: bool = True): ...
    
    def get(self, path: str, default=None) -> Any:
        """Read-only access with deprecation warning."""
    
    def __setitem__(self, key, value):
        raise ConfigImmutableError("Config is immutable; use load_config() to reload.")
    
    def as_dict(self, path: str | None = None) -> dict:
        """Return config subtree as a plain dict (read-only snapshot)."""
```

### CC1.14 Multi-Profile Resolver (`profiles.py`)

```python
def resolve_profile(
    config: GlobalConfig,
    profile_name: str,
    base_path: str = "",
    fallback: str = "default",
) -> dict:
    """Return scoped config view for the named profile.
    Falls back to fallback profile if profile_name is absent."""
```

### CC1.15 Typed Model Bind (`bind.py`)

```python
def bind_model(config: GlobalConfig, path: str, model_cls: type) -> Any:
    """Extract config subtree at path and validate into model_cls (Pydantic BaseModel).
    Raises ConfigBindError on validation failure."""
```

- Optional `pydantic` dependency; raises `ImportError` with guidance if absent.

### CC1.16 Config Diff (`diff.py`)

```python
@dataclass
class ConfigChange:
    path: str
    change_type: str  # "added" | "removed" | "modified"
    old_value: str | None  # Redacted
    new_value: str | None  # Redacted

def config_diff(
    old: GlobalConfig | dict,
    new: GlobalConfig | dict,
    redact: bool = True,
) -> list[ConfigChange]:
    """Structured diff between two config snapshots."""
```

### CC1.17 Config Export (`export.py`)

```python
def export_config(
    config: GlobalConfig,
    redact: bool = True,
    secret_patterns: list[str] | None = None,
) -> dict:
    """Serialisable dict of config tree. Secrets redacted when redact=True."""
```

---

## DM1 — Data Model

No persistent storage. Configuration is ephemeral (loaded at startup, held in memory).

### Config Tree

```yaml
# Merged config tree (before compilation)
llm:
  provider: "${vault.expert.llm.provider || ollama}"
  model: "${vault.expert.llm.model || granite4}"
  api_key: "${vault.expert.llm.api_key}"

# After compilation
llm:
  provider: "openrouter"
  model: "qwen3:14b"
  api_key: "sk-prod-key-12345"
```

---

## DP1 — Dependency Policy

| Dependency | Status | Notes |
|-----------|--------|-------|
| `pyyaml` | Required | YAML parsing |
| `hvac` | Optional | Vault client; graceful degradation if absent |
| `pydantic` | Optional | Schema validation; JSON Schema alternative available |

No web framework dependency. No database dependency.

---

## SE1 — Security Architecture

- Vault tokens treated as secrets — never logged.
- Safe expression evaluator prevents arbitrary code execution.
- `GlobalConfig` is immutable — no mutation after freeze.
- Redaction applied to all config output paths.
- `defaults.yaml` scanner rejects committed secrets.

---

## Integration Pattern

Services consume the package as follows:

```python
from cloud_dog_config import load_config, get_config

# At startup
config = load_config(
    env_files=["private/env-test"],
    defaults_yaml="defaults.yaml",
    config_yaml="config.yaml",
)

# In application code
model = get_config("llm.model")
api_port = get_config("api_server.port")
```

For pytest:
```python
# conftest.py — uses built-in plugin
pytest_plugins = ["cloud_dog_config[dot]pytest_plugin"]
```

## Auto-Declared Source Modules (Traceability Scanner)
<!-- TRACEABILITY-MODULE-LIST:START -->
The list below is generated from the current source tree and kept in sync for architecture-traceability audits.
- `cloud_dog_config/__init__.py`
- `cloud_dog_config/audit.py`
- `cloud_dog_config/bind.py`
- `cloud_dog_config/cli.py`
- `cloud_dog_config/coercion.py`
- `cloud_dog_config/compat/__init__.py`
- `cloud_dog_config/compat/legacy_adapter.py`
- `cloud_dog_config/compiler/__init__.py`
- `cloud_dog_config/compiler/circular_detector.py`
- `cloud_dog_config/compiler/evaluator.py`
- `cloud_dog_config/compiler/reference_resolver.py`
- `cloud_dog_config/compiler/tokenizer.py`
- `cloud_dog_config/compiler/vault_resolver.py`
- `cloud_dog_config/config.py`
- `cloud_dog_config/diff.py`
- `cloud_dog_config/env_parser.py`
- `cloud_dog_config/errors.py`
- `cloud_dog_config/export.py`
- `cloud_dog_config/loader.py`
- `cloud_dog_config/merger.py`
- `cloud_dog_config/metadata.py`
- `cloud_dog_config/naming.py`
- `cloud_dog_config/profiles.py`
- `cloud_dog_config/pytest_plugin.py`
- `cloud_dog_config/redaction.py`
- `cloud_dog_config/reload.py`
- `cloud_dog_config/schema/__init__.py`
- `cloud_dog_config/schema/secret_scanner.py`
- `cloud_dog_config/schema/validator.py`
- `cloud_dog_config/traceability_ids.py`
- `cloud_dog_config/transform.py`
- `cloud_dog_config/vault/__init__.py`
- `cloud_dog_config/vault/client.py`
- `cloud_dog_config/vault/mock_client.py`
- `cloud_dog_config/yaml_loader.py`
<!-- TRACEABILITY-MODULE-LIST:END -->
