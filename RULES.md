# cloud_dog_config — Package Rules

This package implements **PS-80 Configuration Management** and MUST comply with:

- `cloud-dog-ai-platform-standards/RULES.md`
- `cloud-dog-ai-platform-standards/docs/standards/80-config-mgmt.md`
- `packages/backend/platform-config/REQUIREMENTS.md`
- `packages/backend/platform-config/ARCHITECTURE.md`
- `packages/backend/platform-config/TESTS.md`

Package-specific rules:

- All public APIs MUST be imported from `cloud_dog_config/__init__.py`.
- Optional dependencies (`hvac`, `pydantic`) MUST degrade gracefully when not installed.
- Secret values MUST NEVER appear in logs, exceptions, or `GlobalConfig.sources`.
- All tests MUST be executed with `--env` and MUST fail if `--env` is omitted.
