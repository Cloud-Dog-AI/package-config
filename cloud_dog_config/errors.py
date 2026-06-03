# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# cloud_dog_config — Error types
#
# Licence: Proprietary — Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Package-specific exceptions raised by the loader/compiler.
# Related requirements: FR1.8, FR1.9
# Related architecture: SA1
#
# Recent changes:
# - 2026-02-15: Initial implementation.

"""Exception types for cloud_dog_config."""

from __future__ import annotations


class ConfigError(Exception):
    """Base exception for configuration failures."""


class EnvFileError(ConfigError):
    """Raised when an env file is missing or malformed."""


class YAMLLoadError(ConfigError):
    """Raised when YAML cannot be loaded or parsed."""


class CompileError(ConfigError):
    """Raised when placeholder compilation fails."""


class UnresolvedPlaceholderError(CompileError):
    """Raised when unresolved placeholders remain under strict policy."""


class CircularReferenceError(CompileError):
    """Raised when a circular reference is detected."""


class SchemaValidationError(ConfigError):
    """Raised when schema validation fails."""


class VaultError(CompileError):
    """Raised when Vault resolution fails under strict policy."""


class ConfigTransformError(ConfigError):
    """Raised when a post-compile transform fails."""


class ConfigImmutableError(ConfigError):
    """Raised when mutation of immutable config is attempted."""


class ConfigBindError(ConfigError):
    """Raised when binding config to a typed model fails."""


class ConfigReloadTimeoutError(ConfigError):
    """Raised when reload exceeds the configured timeout."""
