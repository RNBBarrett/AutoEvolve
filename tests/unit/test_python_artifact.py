"""Unit tests for autoevolve.artifacts.python_code — PythonCodeArtifact."""

from __future__ import annotations

from pathlib import Path

import pytest

from autoevolve.artifacts.python_code import PythonCodeArtifact
from autoevolve.errors import ArtifactError


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def artifact() -> PythonCodeArtifact:
    """Return a fresh PythonCodeArtifact instance."""
    return PythonCodeArtifact()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPythonCodeArtifactLoad:
    """Tests for PythonCodeArtifact.load."""

    def test_load_reads_py_file(self, artifact: PythonCodeArtifact, tmp_path: Path) -> None:
        """load() should read a .py file and return its content as a string."""
        code = "def greet(name):\n    return f'Hello, {name}!'\n"
        py_file = tmp_path / "sample.py"
        py_file.write_text(code, encoding="utf-8")

        result = artifact.load(py_file)

        assert result == code

    def test_load_missing_file_raises(self, artifact: PythonCodeArtifact, tmp_path: Path) -> None:
        """load() should raise ArtifactError if the file does not exist."""
        missing = tmp_path / "does_not_exist.py"

        with pytest.raises(ArtifactError):
            artifact.load(missing)


class TestPythonCodeArtifactSave:
    """Tests for PythonCodeArtifact.save."""

    def test_save_writes_content_to_py_file(
        self, artifact: PythonCodeArtifact, tmp_path: Path
    ) -> None:
        """save() should write the content string to the specified .py file."""
        code = "x = 42\n"
        dest = tmp_path / "output.py"

        returned_path = artifact.save(code, dest)

        assert returned_path == dest
        assert dest.read_text(encoding="utf-8") == code

    def test_save_to_directory_creates_default_file(
        self, artifact: PythonCodeArtifact, tmp_path: Path
    ) -> None:
        """save() with a directory path should create artifact.py inside it."""
        code = "y = 99\n"

        returned_path = artifact.save(code, tmp_path)

        expected = tmp_path / "artifact.py"
        assert returned_path == expected
        assert expected.read_text(encoding="utf-8") == code

    def test_save_creates_parent_directories(
        self, artifact: PythonCodeArtifact, tmp_path: Path
    ) -> None:
        """save() should create intermediate directories if they do not exist."""
        code = "z = 0\n"
        dest = tmp_path / "nested" / "deep" / "output.py"

        artifact.save(code, dest)

        assert dest.is_file()
        assert dest.read_text(encoding="utf-8") == code


class TestPythonCodeArtifactValidate:
    """Tests for PythonCodeArtifact.validate."""

    def test_validate_passes_for_valid_python(self, artifact: PythonCodeArtifact) -> None:
        """validate() should return True for syntactically valid Python code."""
        valid_code = "def add(a, b):\n    return a + b\n"

        assert artifact.validate(valid_code) is True

    def test_validate_passes_for_empty_script(self, artifact: PythonCodeArtifact) -> None:
        """validate() should return True for an empty string (valid Python)."""
        assert artifact.validate("") is True

    def test_validate_catches_syntax_error(self, artifact: PythonCodeArtifact) -> None:
        """validate() should return False for code with syntax errors."""
        broken_code = "def add(a, b\n    return a + b"

        assert artifact.validate(broken_code) is False

    def test_validate_catches_indentation_error(self, artifact: PythonCodeArtifact) -> None:
        """validate() should return False for code with indentation errors."""
        bad_indent = "def foo():\nreturn 1"

        assert artifact.validate(bad_indent) is False

    def test_validate_catches_incomplete_expression(self, artifact: PythonCodeArtifact) -> None:
        """validate() should return False for incomplete expressions."""
        incomplete = "x = (1 + 2"

        assert artifact.validate(incomplete) is False


class TestPythonCodeArtifactFileExtension:
    """Tests for PythonCodeArtifact.file_extension."""

    def test_file_extension_is_py(self, artifact: PythonCodeArtifact) -> None:
        """file_extension should be '.py'."""
        assert artifact.file_extension == ".py"
