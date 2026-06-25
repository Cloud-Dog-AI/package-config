# platform-config — TESTS.md

**Package:** `cloud_dog_config`  
**Version:** 0.2.0  
**Standard:** PS-80, PS-95  
**Status:** Implemented

---

## Test Strategy

### Overview

Tests are organised per PS-95 hierarchy:

- **UT** — Unit tests for individual components (parser, merger, compiler, coercion, redaction, vault client mock)
- **ST** — System tests for end-to-end config loading with real file I/O
- **IT** — Integration tests with real Vault server (env-gated)
- **AT** — Application tests simulating real service startup patterns

### Test Principles

- `--env` mandatory for all test runs (enforced by conftest).
- Zero hardcoded values — all from env files.
- UT tests use temp dirs and mock Vault client.
- ST/IT/AT use real file I/O; IT uses real Vault (env-gated).
- Stop on failure.

---

## Test Directory Structure

```
tests/
  conftest.py                           # --env enforcement, shared fixtures
  env-UT                                # Non-secret unit test config
  env-ST                                # Non-secret system test config
  env-IT                                # Non-secret integration test config (Vault connection)
  unit/
    UT1.1_EnvParser/
      test_env_parser.py
    UT1.2_YamlLoader/
      test_yaml_loader.py
    UT1.3_Merger/
      test_merger.py
    UT1.4_Tokenizer/
      test_tokenizer.py
    UT1.5_Evaluator/
      test_evaluator.py
    UT1.6_ReferenceResolver/
      test_reference_resolver.py
    UT1.7_VaultResolver/
      test_vault_resolver.py
    UT1.8_CircularDetector/
      test_circular_detector.py
    UT1.9_TypeCoercion/
      test_type_coercion.py
    UT1.10_Redaction/
      test_redaction.py
    UT1.11_NamingConvention/
      test_naming.py
    UT1.12_GlobalConfig/
      test_global_config.py
    UT1.13_SecretScanner/
      test_secret_scanner.py
    UT1.14_SafeExpressionBoundary/
      test_safe_expression_boundary.py
    UT1.15_PostCompileTransform/
      test_transform.py
    UT1.16_EnvMetadata/
      test_metadata.py
    UT1.17_LegacyConfigAdapter/
      test_legacy_adapter.py
    UT1.18_MultiProfileResolver/
      test_profiles.py
    UT1.19_TypedModelBind/
      test_bind.py
    UT1.20_ConfigDiff/
      test_diff.py
    UT1.21_ConfigExport/
      test_export.py
  system/
    ST1.1_PrecedenceChain/
      test_precedence_chain.py
    ST1.2_StartupLifecycle/
      test_startup_lifecycle.py
    ST1.3_HotReload/
      test_hot_reload.py
    ST1.4_EnvEnforcement/
      test_env_enforcement.py
    ST1.5_DefaultsYamlConvention/
      test_defaults_yaml.py
    ST1.6_VaultBundleAssignment/
      test_vault_bundle.py
    ST1.7_ReloadTimeout/
      test_reload_timeout.py
  integration/
    IT1.1_VaultScalarLookup/
      test_vault_scalar.py
    IT1.2_VaultObjectBundle/
      test_vault_object.py
    IT1.3_VaultFallback/
      test_vault_fallback.py
    IT1.4_VaultUnavailable/
      test_vault_unavailable.py
  application/
    AT1.1_ServiceStartupPattern/
      test_service_startup.py
    AT1.2_PytestPluginIntegration/
      test_pytest_plugin.py
    AT1.3_LegacyMigrationPattern/
      test_legacy_migration.py
    AT1.4_MultiProfileService/
      test_multi_profile_service.py
```

---

## Env File Mapping

| Suite | Non-secret env | Secrets env | Notes |
|-------|---------------|-------------|-------|
| UT* | tests/env-UT | — | No secrets needed; mock Vault |
| ST* | tests/env-ST | — | File-system tests; mock Vault |
| IT* | tests/env-IT | private/env-test-secrets | Real Vault connection |
| AT* | tests/env-AT | private/env-test-secrets | Full startup simulation |

---

## Coverage Map (Requirements → Tests)

### Functional Requirements
- **FR1.1** → ST1.1 (precedence chain)
- **FR1.2** → UT1.1 (env parser)
- **FR1.3** → UT1.2 (YAML loader), UT1.3 (merger)
- **FR1.4** → UT1.4 (tokenizer), UT1.5 (evaluator), UT1.6 (reference resolver), ST1.2 (lifecycle)
- **FR1.5** → UT1.5 (evaluator), UT1.14 (boundary guard)
- **FR1.6** → UT1.7 (vault resolver mock), IT1.1 (real Vault scalar)
- **FR1.7** → ST1.6 (vault bundle), IT1.2 (real Vault object)
- **FR1.8** → UT1.5 (evaluator — unresolved policy paths)
- **FR1.9** → UT1.8 (circular detector)
- **FR1.10** → UT1.9 (type coercion)
- **FR1.11** → UT1.12 (GlobalConfig immutability, version, loaded_at)
- **FR1.12** → ST1.2 (schema validation in lifecycle)
- **FR1.13** → ST1.3 (hot reload)
- **FR1.14** → ST1.3 (reload audit event)
- **FR1.15** → UT1.10 (redaction)
- **FR1.16** → UT1.11 (naming convention)
- **FR1.17** → ST1.4 (--env enforcement), AT1.2 (pytest plugin)
- **FR1.18** → UT1.13 (secret scanner), ST1.5 (defaults.yaml)
- **FR1.19** → UT1.15 (post-compile transform)
- **FR1.20** → UT1.16 (env metadata)
- **FR1.21** → UT1.17 (legacy config adapter), AT1.3 (legacy migration pattern)
- **FR1.22** → UT1.18 (multi-profile resolver), AT1.4 (multi-profile service)
- **FR1.23** → UT1.19 (typed model bind)
- **FR1.24** → UT1.20 (config diff)
- **FR1.25** → UT1.21 (config export)
- **FR1.26** → ST1.7 (reload timeout)

### Non-Functional
- **NF1.1** → Dependency audit (no unexpected deps)
- **NF1.2** → ST1.2 (loading time benchmark)
- **NF1.3** → UT1.12 (thread-safety test)
- **NF1.4** → CI matrix (Python 3.10, 3.11, 3.12)

### Cyber Security
- **CS1.1** → UT1.10 (redaction), ST1.2 (no secrets in logs)
- **CS1.2** → UT1.10 (vault token redaction)
- **CS1.3** → UT1.14 (safe expression boundary — reject function calls, eval, imports)

---

## Unit Tests (UT)

### UT1.1: Env Parser
- **Type**: UT
- **Scope**: Parse KEY=value env files
- **What is being tested**: Comment stripping, whitespace handling, multi-file merge order, empty lines, quoted values
- **Inputs**: Temp env files
- **Outputs**: dict[str, str]
- **Env file**: tests/env-UT
- **Related Requirements**: FR1.2
- **Related Architecture**: CC1.2
- **Test File**: `tests/unit/UT1.1_EnvParser/test_env_parser.py`

### UT1.2: YAML Loader
- **Type**: UT
- **Scope**: Load and parse YAML files
- **What is being tested**: Nested structures, missing file handling, invalid YAML rejection
- **Related Requirements**: FR1.3
- **Related Architecture**: CC1.3

### UT1.3: Merger (Deep Merge)
- **Type**: UT
- **Scope**: Deep-merge semantics
- **What is being tested**: Dict merge, list replace, scalar overwrite, nested 3+ levels, empty dict/list edge cases
- **Related Requirements**: FR1.3
- **Related Architecture**: CC1.4

### UT1.4: Tokenizer
- **Type**: UT
- **Scope**: Extract ${...} expressions from strings
- **What is being tested**: Nested braces, escaped chars, multiple expressions per string, no-expression strings
- **Related Requirements**: FR1.4
- **Related Architecture**: CC1.5

### UT1.5: Safe Expression Evaluator
- **Type**: UT
- **Scope**: Evaluate restricted expressions
- **What is being tested**: `||` fallback, `? :` ternary, `==`/`!=` comparison, `!` negation, string/number/bool/null/JSON literals, unresolved placeholder policies (strict/warn/empty)
- **Related Requirements**: FR1.5, FR1.8
- **Related Architecture**: CC1.5

### UT1.6: Reference Resolver
- **Type**: UT
- **Scope**: Resolve ${ENV_VAR} and ${ENV_VAR:default} from config tree
- **What is being tested**: Existing key, missing key with default, missing key without default, nested reference chains
- **Related Requirements**: FR1.4
- **Related Architecture**: CC1.5

### UT1.7: Vault Resolver (Mock)
- **Type**: UT
- **Scope**: Resolve ${vault.*} expressions using mock Vault
- **What is being tested**: Scalar lookup, object/bundle lookup, missing path fallback, Vault unavailable fallback
- **Related Requirements**: FR1.6, FR1.7
- **Related Architecture**: CC1.5, CC1.6

### UT1.8: Circular Reference Detector
- **Type**: UT
- **Scope**: Detect and reject circular config references
- **What is being tested**: Direct cycle (A→B→A), indirect cycle (A→B→C→A), no-cycle (valid chain)
- **Related Requirements**: FR1.9
- **Related Architecture**: CC1.5

### UT1.9: Type Coercion
- **Type**: UT
- **Scope**: Coerce string values to typed values
- **What is being tested**: bool, int, float, JSON object, JSON array, plain string, schema hint override
- **Related Requirements**: FR1.10
- **Related Architecture**: CC1.9

### UT1.10: Redaction
- **Type**: UT
- **Scope**: Redact secrets from config output
- **What is being tested**: Key-pattern matching, nested redaction, vault token redaction, custom patterns
- **Related Requirements**: FR1.15, CS1.1, CS1.2
- **Related Architecture**: CC1.8

### UT1.11: Naming Convention
- **Type**: UT
- **Scope**: Env var ↔ dotted path conversion
- **What is being tested**: `CLOUD_DOG__LLM__MODEL` ↔ `llm.model`, prefix handling, edge cases
- **Related Requirements**: FR1.16
- **Related Architecture**: CC1.10

### UT1.12: GlobalConfig
- **Type**: UT
- **Scope**: Immutable config snapshot
- **What is being tested**: Immutability (mutation raises), dot-notation access, version/loaded_at/sources, thread-safety (concurrent reads)
- **Related Requirements**: FR1.11, NF1.3
- **Related Architecture**: CC1.7

### UT1.13: Secret Scanner
- **Type**: UT
- **Scope**: Scan defaults.yaml for secrets
- **What is being tested**: Detect API keys, passwords, tokens in defaults; pass clean defaults
- **Related Requirements**: FR1.18
- **Related Architecture**: CC1.8

### UT1.14: Safe Expression Boundary Guard
- **Type**: UT
- **Scope**: Reject unsafe expressions
- **What is being tested**: Function calls rejected, arithmetic rejected, assignment rejected, import/eval rejected, shell expansion rejected
- **Related Requirements**: FR1.5, CS1.3
- **Related Architecture**: CC1.5

### UT1.15: Post-Compile Transform Hook
- **Type**: UT
- **Scope**: Post-compile transform chain
- **What is being tested**: Single transform applied; chained transforms applied in order; transform failure raises ConfigTransformError and prevents freeze; identity transform (no-op) passes through; transform receives full compiled tree
- **Related Requirements**: FR1.19
- **Related Architecture**: CC1.11
- **Test File**: `tests/unit/UT1.15_PostCompileTransform/test_transform.py`

### UT1.16: Environment Metadata Accessor
- **Type**: UT
- **Scope**: Runtime metadata from GlobalConfig
- **What is being tested**: All fields populated; hostname and process_id from runtime; config_version and loaded_at from GlobalConfig; sources are redacted; vault_available reflects actual Vault state; env_file_count matches loaded files
- **Related Requirements**: FR1.20
- **Related Architecture**: CC1.12
- **Test File**: `tests/unit/UT1.16_EnvMetadata/test_metadata.py`

### UT1.17: Legacy Config Adapter
- **Type**: UT
- **Scope**: Backward-compatible config access
- **What is being tested**: `get(path, default)` reads from GlobalConfig; mutation via `__setitem__` raises ConfigImmutableError; deprecation warnings emitted on access; `as_dict(path)` returns plain dict snapshot; adapter wraps GlobalConfig without copying data
- **Related Requirements**: FR1.21
- **Related Architecture**: CC1.13
- **Test File**: `tests/unit/UT1.17_LegacyConfigAdapter/test_legacy_adapter.py`

### UT1.18: Multi-Profile Resolver
- **Type**: UT
- **Scope**: Profile-scoped config views
- **What is being tested**: Named profile returned; fallback to default when profile absent; base_path scoping; nested profile trees; missing profile and missing fallback raises error
- **Related Requirements**: FR1.22
- **Related Architecture**: CC1.14
- **Test File**: `tests/unit/UT1.18_MultiProfileResolver/test_profiles.py`

### UT1.19: Typed Model Bind
- **Type**: UT
- **Scope**: Config subtree to Pydantic model
- **What is being tested**: Valid subtree produces typed model; validation failure raises ConfigBindError with field detail; missing path raises error; pydantic import guard
- **Related Requirements**: FR1.23
- **Related Architecture**: CC1.15
- **Test File**: `tests/unit/UT1.19_TypedModelBind/test_bind.py`

### UT1.20: Config Diff
- **Type**: UT
- **Scope**: Structured diff between config snapshots
- **What is being tested**: Added paths detected; removed paths detected; modified paths detected; unchanged paths excluded; secret values redacted in diff output; nested diffs handled
- **Related Requirements**: FR1.24
- **Related Architecture**: CC1.16
- **Test File**: `tests/unit/UT1.20_ConfigDiff/test_diff.py`

### UT1.21: Config Export
- **Type**: UT
- **Scope**: Serialisable config export
- **What is being tested**: Full tree exported as dict; redact=True replaces secrets; redact=False exports raw values; custom secret patterns respected; nested structures preserved
- **Related Requirements**: FR1.25
- **Related Architecture**: CC1.17
- **Test File**: `tests/unit/UT1.21_ConfigExport/test_export.py`

---

## System Tests (ST)

### ST1.1: Precedence Chain
- **Type**: ST
- **Scope**: Full precedence chain with real files
- **What is being tested**: os.environ > env-file > config.yaml > defaults.yaml; multi-env-file order; key override at each level
- **Related Requirements**: FR1.1

### ST1.2: Startup Lifecycle
- **Type**: ST
- **Scope**: Full CM2 lifecycle steps 1-7
- **What is being tested**: Load → merge → compile → validate → freeze; schema rejection; timing < 100ms
- **Related Requirements**: FR1.4, FR1.11, FR1.12, NF1.2

### ST1.3: Hot Reload
- **Type**: ST
- **Scope**: Controlled reload pipeline
- **What is being tested**: Re-run lifecycle; atomic swap; audit event emission; schema validation before activation
- **Related Requirements**: FR1.13, FR1.14

### ST1.4: --env Enforcement
- **Type**: ST
- **Scope**: Mandatory --env parameter
- **What is being tested**: Startup without --env fails; startup with --env succeeds
- **Related Requirements**: FR1.17

### ST1.5: defaults.yaml Convention
- **Type**: ST
- **Scope**: defaults.yaml validation
- **What is being tested**: No secrets in defaults.yaml; all keys documented
- **Related Requirements**: FR1.18

### ST1.6: Vault Bundle Assignment
- **Type**: ST
- **Scope**: Object/bundle deep-merge (with mock Vault)
- **What is being tested**: Vault object merged at target node; os.environ overrides individual fields; fallback objects work
- **Related Requirements**: FR1.7

### ST1.7: Reload Timeout
- **Type**: ST
- **Scope**: Reload timeout enforcement
- **What is being tested**: Reload exceeding timeout fails cleanly without corrupting active config; active config remains unchanged after timeout; timeout configurable via `config.reload_timeout_s`; default timeout is 30s
- **Related Requirements**: FR1.26, FR1.13
- **Related Architecture**: CC1.1
- **Test File**: `tests/system/ST1.7_ReloadTimeout/test_reload_timeout.py`

---

## Integration Tests (IT) — Env-Gated

### IT1.1: Vault Scalar Lookup
- **Type**: IT
- **Scope**: Real Vault scalar secret resolution
- **Env file**: tests/env-IT + private/env-test-secrets (Vault connection)
- **Related Requirements**: FR1.6

### IT1.2: Vault Object Bundle
- **Type**: IT
- **Scope**: Real Vault object/bundle resolution
- **Related Requirements**: FR1.7

### IT1.3: Vault Fallback
- **Type**: IT
- **Scope**: Vault path missing → fallback expression used
- **Related Requirements**: FR1.6, FR1.8

### IT1.4: Vault Unavailable
- **Type**: IT
- **Scope**: Vault server unreachable → strict mode fails, warn mode logs
- **Related Requirements**: FR1.8

---

## Application Tests (AT)

### AT1.1: Service Startup Pattern
- **Type**: AT
- **Scope**: Simulate a real service startup using cloud_dog_config
- **What is being tested**: Full lifecycle with env-file, config.yaml, defaults.yaml, Vault (mock), schema validation, GlobalConfig access

### AT1.2: Pytest Plugin Integration
- **Type**: AT
- **Scope**: Verify pytest plugin adds --env and enforces it
- **What is being tested**: Plugin registers --env; missing --env fails; fixture provides config

### AT1.3: Legacy Migration Pattern
- **Type**: AT
- **Scope**: Simulate staged migration using LegacyConfigAdapter
- **What is being tested**: Service startup with LegacyConfigAdapter wrapping GlobalConfig; existing code paths work via adapter; deprecation warnings logged; mutation attempts caught and reported; adapter removed after migration complete
- **Related Requirements**: FR1.21
- **Related Architecture**: CC1.13
- **Test File**: `tests/application/AT1.3_LegacyMigrationPattern/test_legacy_migration.py`

### AT1.4: Multi-Profile Service
- **Type**: AT
- **Scope**: Simulate multi-profile service startup (e.g. file-mcp storage profiles)
- **What is being tested**: Multiple profiles resolved at startup; per-request profile selection; fallback profile used when requested profile absent; profile config bound to typed models
- **Related Requirements**: FR1.22, FR1.23
- **Related Architecture**: CC1.14, CC1.15
- **Test File**: `tests/application/AT1.4_MultiProfileService/test_multi_profile_service.py`

---

## Test Run History

| Date (UTC) | Scope | Command | Status | Notes |
|------------|-------|---------|--------|-------|
| 2026-02-18 | Full package matrix (IT env file) | `pytest tests --env tests/env-IT -q` | PASS | 103 passed, 0 failed, 3 skipped |
| 2026-02-18 | ST1.7 timeout validation | `pytest tests/system/ST1.7_ReloadTimeout --env tests/env-ST -q` | PASS | 2 passed, 0 failed, 0 skipped |
| 2026-02-18 | Uplift targeted scope | `pytest tests/unit/UT1.15_PostCompileTransform tests/unit/UT1.16_EnvMetadata tests/unit/UT1.17_LegacyConfigAdapter tests/unit/UT1.18_MultiProfileResolver tests/unit/UT1.19_TypedModelBind tests/unit/UT1.20_ConfigDiff tests/unit/UT1.21_ConfigExport tests/system/ST1.7_ReloadTimeout tests/application/AT1.3_LegacyMigrationPattern tests/application/AT1.4_MultiProfileService --env tests/env-UT -q` | PASS | 24 passed, 0 failed, 0 skipped |
| 2026-02-18 | Full package matrix (UT env) | `pytest tests --env tests/env-UT -q` | PASS | 103 passed, 0 failed, 3 skipped |
| 2026-02-18 | Lint | `ruff check cloud_dog_config tests` | PASS | All checks passed |
| 2026-02-18 | Format check | `ruff format --check cloud_dog_config tests` | PASS | 75 files already formatted |
| 2026-02-18 | Build artefacts | `python -m build --no-isolation` | PASS | `cloud_dog_config-0.2.0.tar.gz` + `cloud_dog_config-0.2.0-py3-none-any.whl` |
| 2026-02-17 | Full package matrix | `set -a; source /opt/iac/Development/cloud-dog-ai/env-vault-admin; set +a; pytest tests --env tests/env-IT -q` | PASS | 82 passed, 0 failed, 0 skipped |
| 2026-02-17 | Full package matrix | `set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a; pytest tests --env tests/env-IT -q -rs` | PASS | 80 passed, 0 failed, 2 skipped (Vault discovery permissions/content) |
| 2026-02-17 | Unit/System/Application matrix | `pytest tests --env tests/env-UT -q` | PASS | 79 passed, 0 failed, 3 skipped |
| 2026-02-17 | Lint | `ruff check cloud_dog_config tests` | PASS | All checks passed |
| 2026-02-17 | Format check | `ruff format --check cloud_dog_config tests` | PASS | 57 files already formatted |
| 2026-02-17 | Build artefacts | `python -m build` | PASS | sdist + wheel produced in `dist/` |
| 2026-02-17 | Wheel install + import | `python3 -m venv /tmp/cloud_dog_ai_cfg_wheel_<id> && pip install dist/cloud_dog_config-0.1.0-py3-none-any.whl && python -c "import cloud_dog_config"` | PASS | Wheel installs and package imports successfully in isolated venv |

---

## Latest Verified Run

| Date (UTC) | Scope | Command | Status | Notes |
|------------|-------|---------|--------|-------|
| 2026-02-18 | Full package matrix (IT env file) | `pytest tests --env tests/env-IT -q` | PASS | 103 passed, 0 failed, 3 skipped |
