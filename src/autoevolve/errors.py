"""Custom exception hierarchy for autoevolve."""


class AutoEvolveError(Exception):
    """Base exception for all autoevolve errors."""


class TaskValidationError(AutoEvolveError):
    """Raised when a task configuration is invalid or incomplete."""


class EvaluatorError(AutoEvolveError):
    """Raised when an evaluator fails unexpectedly."""


class ProviderError(AutoEvolveError):
    """Raised when an LLM provider call fails."""


class ResumeError(AutoEvolveError):
    """Raised when a run cannot be resumed."""


class SandboxTimeoutError(AutoEvolveError):
    """Raised when an evaluation exceeds the allowed timeout."""


class ArtifactError(AutoEvolveError):
    """Raised when an artifact cannot be loaded or is invalid."""
