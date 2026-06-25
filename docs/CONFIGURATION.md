# cloud_dog_config Configuration

## External configuration
The package is driven by consumer-supplied environment variables, env files, and YAML configuration files.

## Supported layers
1. process environment
2. env files
3. `config.yaml`
4. `defaults.yaml`

## Common inputs
- `VAULT_ADDR`
- `VAULT_TOKEN`
- `VAULT_MOUNT_POINT`
- `VAULT_CONFIG_PATH`

## Guidance
- keep secrets in Vault, not source files
- use `${vault.*}` expressions for live credentials
- keep defaults non-secret and portable
