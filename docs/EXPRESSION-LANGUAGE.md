# cloud_dog_config Expression Language Reference

## Overview

The `${...}` expression syntax in config files (YAML, env files) supports variable substitution, Vault secret lookup, fallback defaults, conditional logic, string concatenation, and URL composition — all without writing custom resolvers.

Expressions are evaluated during the **compile phase** (step 6 of the config loading pipeline) after all sources (defaults, config, env files, os.environ) have been merged.

---

## Basic Substitution

| Syntax | Example | Description |
|--------|---------|-------------|
| `${VAR}` | `${DB_HOST}` | Resolve from env or config tree |
| `${path.to.key}` | `${database.host}` | Dotted path into nested config |
| `${VAR:default}` | `${DB_HOST:localhost}` | Use `default` if VAR is unresolved |
| `${vault.project.key}` | `${vault.dev.db.password}` | Vault secret lookup |
| `${vault.project.key.*}` | `${vault.dev.db.*}` | Vault bundle (deep-merge object) |

---

## Operators

| Operator | Syntax | Example | Description | Precedence |
|----------|--------|---------|-------------|------------|
| NOT | `!` | `${!DEBUG}` | Logical negation | 1 (highest) |
| Concat | `+` | `${A + '://' + B}` | String concatenation | 2 |
| Equality | `==` | `${ENV == 'prod'}` | Value comparison (true/false) | 3 |
| Inequality | `!=` | `${ENV != 'dev'}` | Value comparison (true/false) | 3 |
| OR | `\|\|` | `${A \|\| B \|\| 'default'}` | First truthy value (fallback chain) | 4 |
| Ternary | `? :` | `${SSL ? 'https' : 'http'}` | Conditional: `cond ? true_val : false_val` | 5 (lowest) |

**Operator precedence** (highest to lowest): `!` > `+` > `== !=` > `||` > `? :`

---

## String Concatenation

### Adjacent Token Concatenation (recommended for URLs)

When a config value contains multiple `${...}` expressions separated by literal text, they are concatenated automatically:

```yaml
# Adjacent tokens — each ${} is evaluated, then joined with the literal text between them
api_url: http://${HOST}:${PORT}/api/v1
# Result: http://myhost:8080/api/v1
```

### Explicit `+` Operator (for use inside expressions)

The `+` operator concatenates values as strings inside a single `${...}` expression. This is useful inside ternary branches or when all parts must be in one expression:

```yaml
# + operator inside a ternary
url: ${USE_SSL ? 'https://' + HOST : 'http://' + HOST}
# Result: https://myhost  (when USE_SSL is truthy)

# + with port
endpoint: ${HOST + ':' + PORT}
# Result: myhost:8080
```

Numbers are automatically converted to strings when concatenated. Unresolved values become empty strings.

---

## URL Composition Patterns

These are the most common real-world patterns:

### 1. URL from parts with defaults
```yaml
api_url: ${SCHEME || 'https'}://${API_HOST}:${API_PORT || '8080'}/api/v1
# With API_HOST=myhost → https://myhost:8080/api/v1
```

### 2. MongoDB connection string
```yaml
mongo_uri: mongodb://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT || '27017'}/${DB_NAME}
# Result: mongodb://admin:secret@mongo1:27017/mydb
```

### 3. PostgreSQL connection string
```yaml
pg_uri: postgresql://${PG_USER}:${PG_PASS}@${PG_HOST}:${PG_PORT || '5432'}/${PG_DB}
# Result: postgresql://postgres:pw@pg1:5432/app
```

### 4. Redis URL with all defaults
```yaml
redis_url: redis://${REDIS_HOST || 'localhost'}:${REDIS_PORT || '6379'}/${REDIS_DB || '0'}
# With no env set → redis://localhost:6379/0
```

### 5. Conditional SSL scheme
```yaml
scheme: ${USE_SSL ? 'https' : 'http'}
# USE_SSL=true → https
# USE_SSL="" → http
```

### 6. Vault secret with env override
```yaml
api_key: ${MY_API_KEY || vault.dev.services.myservice.api_key || 'dev-fallback'}
# Checks MY_API_KEY env, then Vault, then fallback
```

### 7. Multi-segment domain URL
```yaml
base_url: ${SCHEME || 'https'}://${HOST}.${DOMAIN || 'cloud-dog.net'}:${PORT}/api/v1
# HOST=api, PORT=8080 → https://api.cloud-dog.net:8080/api/v1
```

### 8. Boolean from environment comparison
```yaml
verify_ssl: ${ENV == 'production' ? true : false}
# ENV=production → true (boolean, not string)
```

### 9. Nested config path with default
```yaml
timeout: ${server.timeout_seconds || '30'}
server:
  timeout_seconds: 60
# Result: 60 (from config), or 30 (fallback)
```

### 10. Ternary with concatenation
```yaml
url: ${SSL ? 'https://' + HOST : 'http://' + HOST}
# SSL=true, HOST=example.com → https://example.com
```

---

## Vault Integration

### Scalar lookup
```yaml
password: ${vault.dev.database.password}
# Reads a single value from Vault
```

### Bundle (object) merge
```yaml
database:
  ${vault.dev.database.*}
# Deep-merges the entire Vault object into the database config node
```

### Vault path resolution order
1. Primary: `secret/<project>/<path>` (specific secret)
2. Fallback: root blob at `secret/` with `json` or `content` key
3. Legacy aliases (hardcoded migration rules)

---

## Literals

| Type | Example | Notes |
|------|---------|-------|
| String | `'hello'` or `"hello"` | Single or double quotes |
| Number | `42`, `3.14`, `-1` | Integer or float |
| Boolean | `true`, `false` | Keywords (not strings) |
| Null | `null` | Keyword |
| JSON object | `{"key": "value"}` | Parsed via json.loads |
| JSON array | `[1, 2, 3]` | Parsed via json.loads |

---

## Escaping

| Escape | Syntax | Result | Use Case |
|--------|--------|--------|----------|
| Docker | `$${VAR}` | `${VAR}` (literal) | Docker Compose files |
| Shell | `\${VAR}` | `${VAR}` (literal) | Shell scripts |

---

## Truthiness Rules

| Value | Truthy? | Notes |
|-------|---------|-------|
| Non-empty string | Yes | `"hello"` is truthy |
| Empty string `""` | No | Falsy |
| Number != 0 | Yes | `1`, `3.14` are truthy |
| `0` | No | Falsy |
| `true` | Yes | |
| `false` | No | |
| `null` | No | |
| Unresolved | No | Missing variables are falsy |
| Non-empty dict/list | Yes | |
| Empty dict/list | No | |

---

## Error Handling

| Condition | Behaviour |
|-----------|-----------|
| Missing variable (no default) | Depends on `unresolved_policy` |
| Circular reference | Error with cycle trace |
| Unsafe content (`import`, `eval`, `exec`) | Rejected immediately |
| Parentheses `()` | Rejected (prevents function calls) |
| Unclosed `${...}` | Error |

### Unresolved Policies

| Policy | Behaviour |
|--------|-----------|
| `strict` (default) | Raises `UnresolvedPlaceholderError` |
| `warn` | Logs warning, keeps `${...}` as literal |
| `empty` | Replaces with empty string |

---

## Safety

The expression evaluator is **intentionally restricted** to prevent code execution:

- **No parentheses** — prevents function calls
- **No `import`, `eval`, `exec`** — rejected by guard
- **No backticks or semicolons** — rejected
- **No variable assignment** — expressions are read-only
- **JSON literals** parsed via `json.loads()` (safe)
- **Identifiers** match only `[A-Za-z_][A-Za-z0-9_.*]*`
