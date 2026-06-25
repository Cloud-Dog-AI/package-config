# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
# Licensed under the Apache License, Version 2.0
#
# Description: Comprehensive tests for the expression evaluator covering
#   all operators (||, ?:, ==, !=, !, +), string concatenation, null
#   coalescing, and real-world URL composition patterns.
# Related requirements: FR1.5, FR1.8
# Related tests: UT1.5

"""Comprehensive expression operator tests — W28A-505."""

from __future__ import annotations

import pytest

from cloud_dog_config.compiler.evaluator import Unresolved, evaluate
from cloud_dog_config.compiler.tokenizer import tokenize
from cloud_dog_config.compiler import compile_config


def _resolver(env: dict):
    """Build a resolver from a dict (missing keys → Unresolved)."""
    def resolve(name):
        if name in env:
            return env[name]
        # Dotted path
        parts = name.split(".")
        node = env
        for p in parts:
            if isinstance(node, dict) and p in node:
                node = node[p]
            else:
                return Unresolved(name)
        return node
    return resolve


# ── Tier 2: Operators ───────────────────────────────────────


class TestOrOperator:
    def test_returns_first_truthy(self):
        assert evaluate("A || B", _resolver({"A": "hello", "B": "world"})) == "hello"

    def test_returns_second_when_first_falsy(self):
        assert evaluate("A || B", _resolver({"A": "", "B": "fallback"})) == "fallback"

    def test_returns_second_when_first_unresolved(self):
        assert evaluate("A || 'default'", _resolver({})) == "default"

    def test_chained_three(self):
        assert evaluate("A || B || 'last'", _resolver({})) == "last"

    def test_chained_picks_middle(self):
        assert evaluate("A || B || C", _resolver({"B": "mid"})) == "mid"


class TestTernaryOperator:
    def test_true_branch(self):
        assert evaluate("FLAG ? 'yes' : 'no'", _resolver({"FLAG": True})) == "yes"

    def test_false_branch(self):
        assert evaluate("FLAG ? 'yes' : 'no'", _resolver({"FLAG": False})) == "no"

    def test_unresolved_is_falsy(self):
        assert evaluate("MISSING ? 'yes' : 'no'", _resolver({})) == "no"

    def test_truthy_string(self):
        assert evaluate("ENV ? 'a' : 'b'", _resolver({"ENV": "prod"})) == "a"

    def test_empty_string_is_falsy(self):
        assert evaluate("X ? 'a' : 'b'", _resolver({"X": ""})) == "b"


class TestEqualityOperator:
    def test_match(self):
        assert evaluate("A == 2", _resolver({"A": 2})) is True

    def test_mismatch(self):
        assert evaluate("A == 3", _resolver({"A": 2})) is False

    def test_string_match(self):
        assert evaluate("ENV == 'production'", _resolver({"ENV": "production"})) is True

    def test_inequality(self):
        assert evaluate("A != 2", _resolver({"A": 3})) is True

    def test_inequality_false(self):
        assert evaluate("A != 2", _resolver({"A": 2})) is False


class TestNotOperator:
    def test_negate_true(self):
        assert evaluate("!FLAG", _resolver({"FLAG": True})) is False

    def test_negate_false(self):
        assert evaluate("!FLAG", _resolver({"FLAG": False})) is True

    def test_negate_unresolved(self):
        assert evaluate("!MISSING", _resolver({})) is True


# ── Tier 3: String Concatenation (+) ────────────────────────


class TestConcatOperator:
    def test_two_strings(self):
        assert evaluate("A + B", _resolver({"A": "hello", "B": "world"})) == "helloworld"

    def test_string_plus_literal(self):
        assert evaluate("A + '://' + B", _resolver({"A": "https", "B": "host"})) == "https://host"

    def test_number_to_string(self):
        assert evaluate("HOST + ':' + PORT", _resolver({"HOST": "db", "PORT": 5432})) == "db:5432"

    def test_unresolved_becomes_empty(self):
        assert evaluate("'prefix-' + MISSING", _resolver({})) == "prefix-"

    def test_concat_inside_ternary(self):
        result = evaluate("SSL ? 'https://' + HOST : 'http://' + HOST", _resolver({"SSL": True, "HOST": "example.com"}))
        assert result == "https://example.com"


# ── Tier 3: Adjacent Token Concatenation ─────────────────────


class TestAdjacentTokenConcat:
    def test_url_from_parts(self):
        config = {"url": "${SCHEME}://${HOST}:${PORT}"}
        env = {"SCHEME": "https", "HOST": "db.example.com", "PORT": "5432"}
        result = compile_config(config, env=env, vault=None, unresolved_policy="strict", vault_enabled=False)
        assert result["url"] == "https://db.example.com:5432"

    def test_mixed_literal_and_ref(self):
        config = {"url": "http://${HOST}:${PORT}/api/v1"}
        env = {"HOST": "localhost", "PORT": "8080"}
        result = compile_config(config, env=env, vault=None, unresolved_policy="strict", vault_enabled=False)
        assert result["url"] == "http://localhost:8080/api/v1"

    def test_or_default_in_url(self):
        config = {"url": "${SCHEME || 'http'}://${HOST}:${PORT}"}
        env = {"HOST": "myhost", "PORT": "9090"}
        result = compile_config(config, env=env, vault=None, unresolved_policy="strict", vault_enabled=False)
        assert result["url"] == "http://myhost:9090"

    def test_ternary_in_url(self):
        config = {"url": "${USE_SSL ? 'https' : 'http'}://${HOST}"}
        env = {"USE_SSL": "true", "HOST": "secure.example.com"}
        result = compile_config(config, env=env, vault=None, unresolved_policy="strict", vault_enabled=False)
        assert result["url"] == "https://secure.example.com"


# ── Tier 4: Null Coalescing ──────────────────────────────────


class TestNullCoalescing:
    def test_or_with_unresolved(self):
        assert evaluate("OPTIONAL || 'fallback'", _resolver({})) == "fallback"

    def test_or_with_none(self):
        assert evaluate("VAL || 'fallback'", _resolver({"VAL": None})) == "fallback"

    def test_chained_all_missing(self):
        assert evaluate("A || B || C || 'last'", _resolver({})) == "last"

    def test_default_syntax(self):
        """${MISSING:default} tested via compile_config."""
        config = {"val": "${MISSING:mydefault}"}
        result = compile_config(config, env={}, vault=None, unresolved_policy="strict", vault_enabled=False)
        assert result["val"] == "mydefault"

    def test_default_not_used_when_present(self):
        config = {"val": "${PRESENT:ignored}"}
        result = compile_config(config, env={"PRESENT": "real"}, vault=None, unresolved_policy="strict", vault_enabled=False)
        assert result["val"] == "real"


# ── Tier 5: Real-World URL Composition ──────────────────────


class TestRealWorldPatterns:
    def test_mongodb_uri(self):
        config = {"uri": "mongodb://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT || '27017'}/${DB_NAME}"}
        env = {"DB_USER": "admin", "DB_PASS": "secret", "DB_HOST": "mongo1", "DB_NAME": "mydb"}
        result = compile_config(config, env=env, vault=None, unresolved_policy="strict", vault_enabled=False)
        assert result["uri"] == "mongodb://admin:secret@mongo1:27017/mydb"

    def test_postgresql_uri(self):
        config = {"uri": "postgresql://${PG_USER}:${PG_PASS}@${PG_HOST}:${PG_PORT || '5432'}/${PG_DB}"}
        env = {"PG_USER": "postgres", "PG_PASS": "pw", "PG_HOST": "pg1", "PG_DB": "app"}
        result = compile_config(config, env=env, vault=None, unresolved_policy="strict", vault_enabled=False)
        assert result["uri"] == "postgresql://postgres:pw@pg1:5432/app"

    def test_redis_url_all_defaults(self):
        config = {"url": "redis://${REDIS_HOST || 'localhost'}:${REDIS_PORT || '6379'}/${REDIS_DB || '0'}"}
        result = compile_config(config, env={}, vault=None, unresolved_policy="strict", vault_enabled=False)
        assert result["url"] == "redis://localhost:6379/0"

    def test_conditional_ssl(self):
        config = {"scheme": "${USE_SSL ? 'https' : 'http'}"}
        result = compile_config(config, env={"USE_SSL": "true"}, vault=None, unresolved_policy="strict", vault_enabled=False)
        assert result["scheme"] == "https"

    def test_conditional_ssl_false(self):
        config = {"scheme": "${USE_SSL ? 'https' : 'http'}"}
        result = compile_config(config, env={"USE_SSL": ""}, vault=None, unresolved_policy="strict", vault_enabled=False)
        assert result["scheme"] == "http"

    def test_env_override_chain(self):
        config = {"password": "${MY_DB_PASS || 'changeme'}"}
        result = compile_config(config, env={"MY_DB_PASS": "real_pass"}, vault=None, unresolved_policy="strict", vault_enabled=False)
        assert result["password"] == "real_pass"

    def test_env_override_fallback(self):
        config = {"password": "${MY_DB_PASS || 'changeme'}"}
        result = compile_config(config, env={}, vault=None, unresolved_policy="strict", vault_enabled=False)
        assert result["password"] == "changeme"

    def test_nested_path_with_default(self):
        config = {"timeout": "${server.timeout_seconds || '30'}",
                  "server": {"timeout_seconds": "60"}}
        result = compile_config(config, env={}, vault=None, unresolved_policy="strict", vault_enabled=False)
        assert result["timeout"] == "60"

    def test_bool_coercion_in_ternary(self):
        config = {"verify": "${ENV == 'production' ? true : false}"}
        result = compile_config(config, env={"ENV": "production"}, vault=None, unresolved_policy="strict", vault_enabled=False)
        assert result["verify"] is True

    def test_multi_segment_url(self):
        config = {"url": "${SCHEME || 'https'}://${HOST}.${DOMAIN || 'cloud-dog.net'}:${PORT}/api/v1"}
        env = {"HOST": "api", "PORT": "8080"}
        result = compile_config(config, env=env, vault=None, unresolved_policy="strict", vault_enabled=False)
        assert result["url"] == "https://api.cloud-dog.net:8080/api/v1"

    def test_plus_concat_in_ternary(self):
        """+ operator works inside ternary branches."""
        config = {"url": "${SSL ? 'https://' + HOST : 'http://' + HOST}"}
        env = {"SSL": "true", "HOST": "myhost"}
        result = compile_config(config, env=env, vault=None, unresolved_policy="strict", vault_enabled=False)
        assert result["url"] == "https://myhost"
