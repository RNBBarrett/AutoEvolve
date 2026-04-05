"""Base artifact type abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class Artifact(ABC):
    """Base class for artifact types.

    An artifact represents the thing being optimized — a Python file,
    a prompt text file, or any other artifact type added in the future.
    """

    artifact_type: str
    file_extension: str

    @abstractmethod
    def load(self, path: Path) -> str:
        """Load artifact content from a file.

        Args:
            path: Path to the artifact file.

        Returns:
            The artifact content as a string.
        """

    @abstractmethod
    def save(self, content: str, path: Path) -> Path:
        """Save artifact content to a file.

        Args:
            content: The artifact content string.
            path: Path to write the file. If it's a directory, a default
                  filename with the correct extension is used.

        Returns:
            The path where the artifact was written.
        """

    @abstractmethod
    def validate(self, content: str) -> bool:
        """Check whether content is valid for this artifact type.

        Args:
            content: The artifact content to validate.

        Returns:
            True if valid, False otherwise.
        """


def get_artifact_handler(artifact_type: str) -> Artifact:
    """Get the appropriate Artifact handler for the given type.

    Args:
        artifact_type: One of 'python_code' or 'prompt_text'.

    Returns:
        An Artifact instance.

    Raises:
        ValueError: If the artifact type is not recognized.
    """
    from autoevolve.artifacts.python_code import PythonCodeArtifact
    from autoevolve.artifacts.prompt_text import PromptTextArtifact

    handlers: dict[str, type[Artifact]] = {
        "python_code": PythonCodeArtifact,
        "prompt_text": PromptTextArtifact,
    }

    if artifact_type not in handlers:
        raise ValueError(
            f"Unknown artifact type '{artifact_type}'. "
            f"Available: {', '.join(sorted(handlers))}"
        )
    return handlers[artifact_type]()
