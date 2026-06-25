# Agent Instruction — Fix cloud_dog_config (v0.2.1)

**Package:** `cloud_dog_config`
**Target version:** 0.2.1
**Date:** 2026-02-19 (Issue 9 added — critical os.environ bug)
**Scope:** 8 delivered features (FR1.19–FR1.26) + **1 CRITICAL BUG FIX (Issue 9)**

---

## Status: ⚠️ OPEN — Issue 9 outstanding

Issues 1–8 from cross-project impact assessment have been delivered and verified. **Issue 9 is a CRITICAL BUG** discovered during file-mcp-server CONFIG migration — `_select_relevant_os_environ` silently drops env vars that are referenced as `${PLACEHOLDER}` in config YAML but do not match a top-level config key. This breaks `os.environ` precedence for ALL projects using per-project env var naming (e.g. `FILE_MCP_*`, `NOTIFICATION_*`, `SQL_AGENT_*`).

**Issue 9 MUST be fixed before any CONFIG migration can complete correctly.**

**Verified on 2026-02-18:**
- 103 tests passed, 0 failed, 3 skipped (IT env-gated)
- Lint and format clean (`ruff check` + `ruff format --check`)
- Build produces `cloud_dog_config-0.2.0.tar.gz` + `cloud_dog_config-0.2.0-py3-none-any.whl`
- All 34 SA1 modules present
- All 36 test directories present and matching TESTS.md (21 UT + 7 ST + 4 IT + 4 AT)

**Governing documents:**
1. `platform-config/REQUIREMENTS.md` (v0.2.0) — FR1.19–FR1.26
2. `platform-config/ARCHITECTURE.md` (v0.2.0) — CC1.11–CC1.17
3. `platform-config/TESTS.md` (v0.2.0) — UT1.15–UT1.21, ST1.7, AT1.3–AT1.4
4. `packages/backend/AGENT-INSTRUCTION.md` — Integrity Warranty and Config Delegation — ZERO TOLERANCE (MANDATORY)

---

## Delivery Summary

### Issue 1 — Post-Compile Transform Hook ✅ DELIVERED

**FR:** FR1.19 | **Architecture:** CC1.11 | **Tests:** UT1.15

- `cloud_dog_config/transform.py` — `apply_transforms()` chains callables in order; raises `ConfigTransformError` on failure with transform `__name__`
- `loader.py` — `load_config()` accepts `transforms: list[Callable] | None`; invoked at step 5a (after compile, before schema validation)
- `tests/unit/UT1.15_PostCompileTransform/test_transform.py` — passing

---

### Issue 2 — Environment Metadata Accessor ✅ DELIVERED

**FR:** FR1.20 | **Architecture:** CC1.12 | **Tests:** UT1.16

- `cloud_dog_config/metadata.py` — `EnvMetadata` frozen dataclass (8 fields); `get_env_metadata()` reads from GlobalConfig, NOT `os.environ`
- Exported from `__init__.py`
- `tests/unit/UT1.16_EnvMetadata/test_metadata.py` — passing

---

### Issue 3 — Legacy Config Adapter ✅ DELIVERED

**FR:** FR1.21 | **Architecture:** CC1.13 | **Tests:** UT1.17, AT1.3

- `cloud_dog_config/compat/legacy_adapter.py` — `LegacyConfigAdapter` with `get()`, `__getitem__`, `__setitem__` (raises `ConfigImmutableError`), `as_dict()`, deprecation warnings
- `tests/unit/UT1.17_LegacyConfigAdapter/test_legacy_adapter.py` — passing
- `tests/application/AT1.3_LegacyMigrationPattern/test_legacy_migration.py` — passing

---

### Issue 4 — Multi-Profile Resolver ✅ DELIVERED

**FR:** FR1.22 | **Architecture:** CC1.14 | **Tests:** UT1.18, AT1.4

- `cloud_dog_config/profiles.py` — `resolve_profile(config, profile_name, base_path, fallback)` with fallback logic, raises `ConfigError` when neither profile nor fallback exists
- Exported from `__init__.py`
- `tests/unit/UT1.18_MultiProfileResolver/test_profiles.py` — passing
- `tests/application/AT1.4_MultiProfileService/test_multi_profile_service.py` — passing

---

### Issue 5 — Typed Model Bind ✅ DELIVERED

**FR:** FR1.23 | **Architecture:** CC1.15 | **Tests:** UT1.19

- `cloud_dog_config/bind.py` — `bind_model(config, path, model_cls)` with pydantic `ValidationError` → `ConfigBindError` mapping, field-level detail, `ImportError` guard with guidance
- Exported from `__init__.py`
- `tests/unit/UT1.19_TypedModelBind/test_bind.py` — passing

---

### Issue 6 — Config Diff Utility ✅ DELIVERED

**FR:** FR1.24 | **Architecture:** CC1.16 | **Tests:** UT1.20

- `cloud_dog_config/diff.py` — `ConfigChange` dataclass (path, change_type, old_value, new_value); `config_diff(old, new, redact=True)` with recursive walk, secret redaction, accepts `GlobalConfig` or `dict`
- `reload.py` — already uses `config_diff()` in `emit_reload_audit()` for structured diff in audit events
- Exported from `__init__.py`
- `tests/unit/UT1.20_ConfigDiff/test_diff.py` — passing

---

### Issue 7 — Config Export ✅ DELIVERED

**FR:** FR1.25 | **Architecture:** CC1.17 | **Tests:** UT1.21

- `cloud_dog_config/export.py` — `export_config(config, redact=True, secret_patterns=None)` returns serialisable dict with optional redaction
- Exported from `__init__.py`
- `tests/unit/UT1.21_ConfigExport/test_export.py` — passing

---

### Issue 8 — Reload Timeout ✅ DELIVERED

**FR:** FR1.26 | **Tests:** ST1.7

- `loader.py` — `reload_config(timeout_s=30.0)` uses `threading.Thread` + `threading.Event.wait(timeout=)` for timeout enforcement; reads `config.reload_timeout_s` from active config as override; raises `ConfigReloadTimeoutError`; active config remains unchanged on timeout
- `errors.py` — `ConfigReloadTimeoutError` class present
- `tests/system/ST1.7_ReloadTimeout/test_reload_timeout.py` — passing

---

## Error Classes Delivered (4)

All in `cloud_dog_config/errors.py`:
- `ConfigTransformError` (Issue 1)
- `ConfigImmutableError` (Issue 3)
- `ConfigBindError` (Issue 5)
- `ConfigReloadTimeoutError` (Issue 8)

---

## Public API Exports

All new APIs exported from `cloud_dog_config/__init__.py`:
- `bind_model`, `LegacyConfigAdapter`, `ConfigChange`, `config_diff`, `export_config`, `get_env_metadata`, `EnvMetadata`, `resolve_profile`

---

## Verification — Full Suite

```bash
set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
pytest tests --env tests/env-IT -q
ruff check cloud_dog_config tests
ruff format --check cloud_dog_config tests
python -m build
find cloud_dog_config -name '*.py' -not -path '*__pycache__*' | sort
```

---

### Issue 9 — `_select_relevant_os_environ` drops placeholder-referenced env vars ❌ CRITICAL BUG

**Discovered:** 2026-02-19, during file-mcp-server CONFIG migration audit
**Severity:** CRITICAL — blocks all 5 CONFIG migrations
**File:** `cloud_dog_config/loader.py`, function `_select_relevant_os_environ` (line ~214)

#### The Bug

`_select_relevant_os_environ` filters `os.environ` and only keeps vars that:
1. Are `VAULT_*` bridge vars
2. Contain `__` (double-underscore convention)
3. Match a **top-level key** in the merged config tree (`k in base`)

Criterion 3 fails for ALL project-specific env vars like `FILE_MCP_SERVER_LOG`, `FILE_MCP_S3_ACCESS_KEY`, etc. These vars are referenced as `${FILE_MCP_SERVER_LOG}` inside YAML values — they are placeholder variable names, NOT top-level config keys. The merged config tree has `profiles` and `http` as top-level keys, so `k in base` never matches `FILE_MCP_*`.

**Result:** `os.environ` values for project-specific vars are silently dropped. The platform precedence chain `os.environ → env-file(s) → config.yaml → defaults.yaml` is BROKEN — `os.environ` has no effect for these vars.

#### The Fix

Scan the merged config tree for all `${VARIABLE}` placeholder references. Add those variable names to the acceptance set in `_select_relevant_os_environ`. This ensures any env var referenced as a placeholder in config YAML is picked up from `os.environ`.

**Implementation approach:**

1. Add a helper function `_collect_placeholder_vars(tree: dict) -> set[str]` that recursively walks the merged config tree and extracts all variable names from `${VAR}` and `${VAR || FALLBACK}` expressions using the existing tokenizer.
2. In `_select_relevant_os_environ`, call this helper on `base` and add a fourth acceptance criterion: `k in placeholder_vars`.
3. This is ~15 lines of new code plus ~2 lines changed in the existing function.

**Pseudocode:**

```python
import re

_PLACEHOLDER_RE = re.compile(r"\$\{\s*([A-Za-z_][A-Za-z0-9_]*)")

def _collect_placeholder_vars(tree: Any) -> set[str]:
    """Recursively collect env var names referenced as ${VAR} in config values."""
    out: set[str] = set()
    if isinstance(tree, str):
        out.update(_PLACEHOLDER_RE.findall(tree))
    elif isinstance(tree, dict):
        for v in tree.values():
            out.update(_collect_placeholder_vars(v))
    elif isinstance(tree, (list, tuple)):
        for item in tree:
            out.update(_collect_placeholder_vars(item))
    return out
```

Then in `_select_relevant_os_environ`:

```python
def _select_relevant_os_environ(*, base: dict[str, Any]) -> dict[str, str]:
    placeholder_vars = _collect_placeholder_vars(base)  # NEW
    out: dict[str, str] = {}
    ...
    for k, v in os.environ.items():
        ...
        if "__" in k:
            out[k] = v
        elif k in base:
            out[k] = v
        elif k in placeholder_vars:  # NEW — accept placeholder-referenced vars
            out[k] = v
    return out
```

#### Tests Required

- **UT:** Load a config with `${MY_APP_FOO}` placeholder, set `MY_APP_FOO` in `os.environ`, verify it resolves.
- **UT:** Verify vars NOT referenced as placeholders are still excluded from os.environ pickup.
- **ST:** End-to-end: defaults.yaml with `${FILE_MCP_SERVER_LOG}`, env file sets one value, `os.environ` sets a different value — `os.environ` wins.

#### Verification

After fix, run from file-mcp-server with a CLEAN 30-line adapter (no `os.environ` reads, no temp files):

```bash
cd /opt/iac/Development/cloud-dog-ai/file-mcp-server
PYTHONPATH=src:. python3 -m pytest tests/test_config_loader.py -v --timeout=30 --env run/env.base
```

All 6 tests must pass. If they do, the bug is fixed.

#### DO NOT

- **DO NOT** work around this bug in project adapters — the fix goes HERE, in the package.
- **DO NOT** read `os.environ` in any adapter — that is config delegation violation (PS-80).
- **DO NOT** write temp env files to inject os.environ values — that is a workaround, not a fix.

---

## pyproject.toml version

```toml
version = "0.2.1"
```

---

## MANDATORY COMPLETION REPORT

When finished, write your report to:
**`/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/packages/backend/platform-config/working/W28A-117-FIX-CONFIG-REPORT.md`**

Your report MUST include ALL of the following:

### 1. Run summary
- List every file changed and what was changed
- List every test fixed and how

### 2. Test results (REAL counts from actual runs)
```
QT: Xp / Yf
UT: Xp / Yf
ST: Xp / Yf
IT: Xp / Yf
AT: Xp / Yf
Ruff: X issues
```

### 3. Verdict
State one of: **PASS** (100% green) / **PARTIAL** (some fixed, some remain) / **FAIL** (no improvement) / **BLOCKED** (cannot proceed)

If not PASS, list every remaining failure with classification: `CODE_BUG`, `ENV_CONFIG`, `INFRA_MISSING`, `EXT_SERVICE`

### 4. Evidence logs
All logs MUST be saved to `working/` directory:
```
working/w28a-117-qt.log
working/w28a-117-ut.log
working/w28a-117-st.log
working/w28a-117-it.log
working/w28a-117-at.log
working/w28a-117-ruff.log
```

### 5. RULES.md COMPLIANCE WARRANTY

Copy this EXACTLY into your report:
```
I warrant that:
1. I have read RULES.md IN FULL before starting work
2. ALL code I produced is 100% compliant with RULES.md
3. ALL test results reported are REAL — exact counts from actual runs
4. I have NOT weakened any test
5. I have NOT stored, copied, or exposed any credentials
6. ALL credentials come from Vault or git-ignored env files
7. I have NOT modified files outside this package
```
