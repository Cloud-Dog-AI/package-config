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

"""AT1.2: Pytest Plugin Integration — verify plugin option and enforcement."""

from __future__ import annotations


class TestPytestPluginIntegration:
    def test_plugin_registers_env_option(self, pytester) -> None:  # type: ignore[no-untyped-def]
        pytester.makeconftest('pytest_plugins = ["cloud_dog_config.pytest_plugin"]\n')
        pytester.makepyfile(
            """
            def test_ok():
                assert True
            """
        )
        env_file = pytester.path / "env"
        env_file.write_text("X=1\n")
        result = pytester.runpytest("-q", "-p", "no:cloud_dog_config", "--env", str(env_file))
        result.assert_outcomes(passed=1)
