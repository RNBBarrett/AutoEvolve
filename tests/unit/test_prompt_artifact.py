"""Unit tests for autoevolve.artifacts.prompt_text — PromptTextArtifact."""

from __future__ import annotations

from pathlib import Path

import pytest

from autoevolve.artifacts.prompt_text import PromptTextArtifact
from autoevolve.errors import ArtifactError


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def artifact() -> PromptTextArtifact:
    """Return a fresh PromptTextArtifact instance."""
    return PromptTextArtifact()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPromptTextArtifactLoad:
    """Tests for PromptTextArtifact.load."""

    def test_load_reads_txt_file(self, artifact: PromptTextArtifact, tmp_path: Path) -> None:
        """load() should read a .txt file and return its content as a string."""
        text = "Classify the following review as positive or negative.\n"
        txt_file = tmp_path / "prompt.txt"
        txt_file.write_text(text, encoding="utf-8")

        result = artifact.load(txt_file)

        assert result == text

    def test_load_missing_file_raises(self, artifact: PromptTextArtifact, tmp_path: Path) -> None:
        """load() should raise ArtifactError if the file does not exist."""
        missing = tmp_path / "nonexistent.txt"

        with pytest.raises(ArtifactError):
            artifact.load(missing)


class TestPromptTextArtifactSave:
    """Tests for PromptTextArtifact.save."""

    def test_save_writes_content_to_txt_file(
        self, artifact: PromptTextArtifact, tmp_path: Path
    ) -> None:
        """save() should write the content string to the specified .txt file."""
        text = "Summarize the article in one sentence.\n"
        dest = tmp_path / "output.txt"

        returned_path = artifact.save(text, dest)

        assert returned_path == dest
        assert dest.read_text(encoding="utf-8") == text

    def test_save_to_directory_creates_default_file(
        self, artifact: PromptTextArtifact, tmp_path: Path
    ) -> None:
        """save() with a directory path should create artifact.txt inside it."""
        text = "Translate the following to French.\n"

        returned_path = artifact.save(text, tmp_path)

        expected = tmp_path / "artifact.txt"
        assert returned_path == expected
        assert expected.read_text(encoding="utf-8") == text

    def test_save_creates_parent_directories(
        self, artifact: PromptTextArtifact, tmp_path: Path
    ) -> None:
        """save() should create intermediate directories if they do not exist."""
        text = "Describe the image.\n"
        dest = tmp_path / "nested" / "deep" / "prompt.txt"

        artifact.save(text, dest)

        assert dest.is_file()
        assert dest.read_text(encoding="utf-8") == text


class TestPromptTextArtifactValidate:
    """Tests for PromptTextArtifact.validate."""

    def test_validate_passes_for_non_empty_text(self, artifact: PromptTextArtifact) -> None:
        """validate() should return True for non-empty text content."""
        assert artifact.validate("Classify this review.") is True

    def test_validate_passes_for_multiline_text(self, artifact: PromptTextArtifact) -> None:
        """validate() should return True for multiline non-empty text."""
        text = "You are a helpful assistant.\nAnswer concisely."
        assert artifact.validate(text) is True

    def test_validate_catches_empty_string(self, artifact: PromptTextArtifact) -> None:
        """validate() should return False for an empty string."""
        assert artifact.validate("") is False

    def test_validate_catches_whitespace_only(self, artifact: PromptTextArtifact) -> None:
        """validate() should return False for whitespace-only content."""
        assert artifact.validate("   \n\t  ") is False


class TestPromptTextArtifactFileExtension:
    """Tests for PromptTextArtifact.file_extension."""

    def test_file_extension_is_txt(self, artifact: PromptTextArtifact) -> None:
        """file_extension should be '.txt'."""
        assert artifact.file_extension == ".txt"
