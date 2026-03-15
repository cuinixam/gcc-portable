"""Pypeline steps for GCC packaging and testing."""

from pathlib import Path
from typing import Any

from pypeline.domain.execution_context import ExecutionContext
from pypeline.domain.pipeline import PipelineStep

DEFAULT_GCC_VERSION = "14"
DEFAULT_BUILD_NUMBER = "0"
DEFAULT_OUTPUT_DIR = "build/dist"


class PackageStep(PipelineStep[ExecutionContext]):
    """Pypeline step that packages GCC into a portable macOS archive."""

    def __init__(self, execution_context: ExecutionContext, group_name: str, config: dict[str, Any] | None = None) -> None:
        super().__init__(execution_context, group_name, config)
        self.target_dir = self._get_config_value("output_dir", DEFAULT_OUTPUT_DIR)

    def run(self) -> int:
        gcc_version = self.execution_context.get_input("gcc_version") or DEFAULT_GCC_VERSION
        build_number = self.execution_context.get_input("build_number") or DEFAULT_BUILD_NUMBER
        self.execution_context.create_process_executor(
            ["jarvis", "package", str(gcc_version), "--output", self.target_dir, "--build-number", str(build_number)],
            cwd=self.project_root_dir,
        ).execute()
        return 0

    def get_name(self) -> str:
        return self.__class__.__name__

    def get_inputs(self) -> list[Path]:
        return []

    def get_outputs(self) -> list[Path]:
        return []

    def update_execution_context(self) -> None:
        pass

    def get_needs_dependency_management(self) -> bool:
        return False

    def _get_config_value(self, key: str, default: str) -> str:
        if self.config and key in self.config:
            return str(self.config[key])
        return default


class TestStep(PipelineStep[ExecutionContext]):
    """Pypeline step that tests the portable GCC archive."""

    def __init__(self, execution_context: ExecutionContext, group_name: str, config: dict[str, Any] | None = None) -> None:
        super().__init__(execution_context, group_name, config)
        self.target_dir = self._get_config_value("output_dir", DEFAULT_OUTPUT_DIR)

    def run(self) -> int:
        self.execution_context.create_process_executor(
            ["jarvis", "test", self.target_dir, "--output", self.target_dir],
            cwd=self.project_root_dir,
        ).execute()
        return 0

    def get_name(self) -> str:
        return self.__class__.__name__

    def get_inputs(self) -> list[Path]:
        return []

    def get_outputs(self) -> list[Path]:
        return []

    def update_execution_context(self) -> None:
        pass

    def get_needs_dependency_management(self) -> bool:
        return False

    def _get_config_value(self, key: str, default: str) -> str:
        if self.config and key in self.config:
            return str(self.config[key])
        return default
