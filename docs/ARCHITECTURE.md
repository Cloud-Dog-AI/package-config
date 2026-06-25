# cloud_dog_config Architecture

## Purpose
`cloud_dog_config` provides the shared configuration loading and compilation pipeline for Cloud-Dog Python services.

## Main responsibilities
- load layered configuration from environment, env files, config files, and defaults
- compile expressions such as `${vault.*}` and environment references
- bind compiled configuration into typed runtime models
- expose reload, diff, and redaction helpers

## Main components
- loaders: read env files and structured config inputs
- compiler: resolve expressions and merge values deterministically
- vault integration: resolve Vault-backed identifiers through a single adapter layer
- runtime binding: expose immutable config snapshots and model binding helpers
- pytest integration: enforce `--env` usage in package tests

## Integration pattern
Consumer applications load config once at startup, then pass the compiled snapshot into their own runtime factories.
