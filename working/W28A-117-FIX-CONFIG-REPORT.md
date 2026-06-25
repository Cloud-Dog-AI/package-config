# W28A-117 — Fix cloud_dog_config Issue 9 Report

## 1. Run summary

### Files changed
- `cloud_dog_config/loader.py`
  - Added placeholder-aware environment discovery via `_collect_placeholder_vars(tree)`.
  - Updated `_select_relevant_os_environ(base=...)` so `${PLACEHOLDER}`-referenced env vars are accepted from `os.environ`.
- `tests/unit/UT1.7_VaultResolver/test_loader_vault_env_mapping.py`
  - Added UT coverage for placeholder-referenced env acceptance and unreferenced env exclusion.
  - Added UT coverage for recursive placeholder variable extraction from nested dict/list structures.
- `tests/system/ST1.1_PrecedenceChain/test_precedence_chain.py`
  - Added ST coverage proving `os.environ` wins over env-file for placeholder-only keys (`FILE_MCP_SERVER_LOG`).
- `tests/system/ST1.4_EnvEnforcement/test_env_enforcement.py`
  - Fixed `pytester` subprocess setup to load `cloud_dog_config.pytest_plugin` explicitly in generated `conftest.py`.
- `tests/application/AT1.2_PytestPluginIntegration/test_pytest_plugin.py`
  - Fixed plugin integration test to load `cloud_dog_config.pytest_plugin` explicitly in generated `conftest.py`.
- `tests/integration/IT1.1_VaultScalarLookup/test_vault_scalar.py`
  - Reworked scalar discovery to read from the real Vault root config blob (read-only path) and dynamically discover a scalar identifier without list/write permissions.
  - Added fingerprint-based assertion to avoid leaking resolved values in failure output.
- `tests/integration/IT1.2_VaultObjectBundle/test_vault_object.py`
  - Reworked bundle discovery to read from the real Vault root config blob (read-only path) and dynamically discover a bundle identifier without list/write permissions.
  - Added fingerprint-based assertion to avoid leaking resolved values in failure output.
- `cloud_dog_config/compiler/vault_resolver.py`
  - Ruff formatting alignment (no behavioural change).
- `tests/unit/UT1.7_VaultResolver/test_vault_resolver.py`
  - Ruff formatting alignment (no behavioural change).

### Tests fixed/implemented and how
- **Issue 9 fix (critical):** restored `os.environ` precedence for placeholder-referenced non-`__` env keys.
- **UT additions:** validated placeholder extraction and env selection behaviour.
- **ST addition:** validated end-to-end precedence for placeholder-only key path.
- **ST/AT stability fixes:** ensured plugin `--env` enforcement tests reliably load plugin in subprocess runs.
- **IT resilience fixes:** removed dependency on KV list/write permissions by switching to read-only root-config discovery.

## 2. Test results (REAL counts from actual runs)

QT: 2p / 0f
UT: 99p / 0f
ST: 11p / 0f
IT: 5p / 0f
AT: 4p / 0f
Ruff: 0 issues

## 3. Verdict

**PASS**

All required tiers are green with real executions and evidence logs.

## 4. Evidence logs

- `working/w28a-117-qt.log`
- `working/w28a-117-ut.log`
- `working/w28a-117-st.log`
- `working/w28a-117-it.log`
- `working/w28a-117-at.log`
- `working/w28a-117-ruff.log`
- `working/w28a-117-targeted.log`

## 5. RULES.md COMPLIANCE WARRANTY

I warrant that:
1. I have read RULES.md IN FULL before starting work
2. ALL code I produced is 100% compliant with RULES.md
3. ALL test results reported are REAL — exact counts from actual runs
4. I have NOT weakened any test
5. I have NOT stored, copied, or exposed any credentials
6. ALL credentials come from Vault or git-ignored env files
7. I have NOT modified files outside this package
