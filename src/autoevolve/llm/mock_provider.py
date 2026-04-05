"""Mock LLM provider for deterministic testing.

This is the backbone of the entire test suite. It produces deterministic,
varied, syntactically valid candidates for both code and prompt artifacts
without making any real LLM calls.
"""

from __future__ import annotations

import re
from typing import Any

from autoevolve.llm.base import Provider
from autoevolve.prompt_builder import ARTIFACT_START, ARTIFACT_END


class MockProvider(Provider):
    """Deterministic mock provider for testing.

    Supports three modes via the model parameter:
    - 'mock-deterministic': Returns a slightly improved variant of the input
    - 'mock-malformed': Returns garbage output to test error handling
    - 'mock-noop': Returns the input unchanged
    """

    def __init__(self, model: str = "mock-deterministic") -> None:
        self.model = model
        self._counter = 0

    def generate(self, prompt: str, *, metadata: dict[str, Any] | None = None) -> str:
        """Generate a response based on the mock mode."""
        self._counter += 1

        if self.model == "mock-malformed":
            return self._malformed_response()
        elif self.model == "mock-noop":
            return self._noop_response(prompt)
        else:
            return self._deterministic_response(prompt)

    def _extract_artifact(self, prompt: str) -> str:
        """Extract artifact content from between the standard delimiters."""
        pattern = re.escape(ARTIFACT_START) + r"\n(.*?)\n" + re.escape(ARTIFACT_END)
        match = re.search(pattern, prompt, re.DOTALL)
        if match:
            return match.group(1)
        # Fallback: try to find code-like content
        return prompt.split("\n")[-1] if prompt else ""

    def _is_code_prompt(self, prompt: str) -> bool:
        """Detect whether this prompt is for a Python code artifact."""
        return "Python code" in prompt or "python_code" in prompt or "def " in prompt

    def _deterministic_response(self, prompt: str) -> str:
        """Return a slightly modified version of the artifact."""
        artifact = self._extract_artifact(prompt)
        iteration = self._counter

        if self._is_code_prompt(prompt):
            return self._transform_code(artifact, iteration)
        else:
            return self._transform_prompt(artifact, iteration)

    def _transform_code(self, code: str, iteration: int) -> str:
        """Apply a deterministic transformation to Python code."""
        transforms = [
            self._code_add_comment,
            self._code_add_docstring_note,
            self._code_optimize_pattern,
            self._code_add_type_hint,
        ]
        transform = transforms[iteration % len(transforms)]
        result = transform(code, iteration)
        return f"HYPOTHESIS: Improvement iteration {iteration} - applying optimization.\n{result}"

    def _transform_prompt(self, prompt_text: str, iteration: int) -> str:
        """Apply a deterministic transformation to prompt text."""
        transforms = [
            self._prompt_add_specificity,
            self._prompt_add_role,
            self._prompt_add_format_instruction,
            self._prompt_add_example,
        ]
        transform = transforms[iteration % len(transforms)]
        result = transform(prompt_text, iteration)
        return f"HYPOTHESIS: Prompt improvement iteration {iteration}.\n{result}"

    # --- Code transforms ---

    def _code_add_comment(self, code: str, iteration: int) -> str:
        """Add an optimization comment."""
        return f"# optimization: iteration {iteration}\n{code}"

    def _code_add_docstring_note(self, code: str, iteration: int) -> str:
        """Add a note to the first docstring, or add one."""
        if '"""' in code:
            return code.replace('"""', f'"""  # improved v{iteration}', 1)
        lines = code.split("\n")
        if lines:
            lines.insert(1, f'    """Optimized version {iteration}."""')
        return "\n".join(lines)

    def _code_optimize_pattern(self, code: str, iteration: int) -> str:
        """Apply a simple code pattern transformation."""
        # Try to replace a common pattern to make code slightly different
        if "result = []" in code:
            code = code.replace("result = []", f"result = list()  # v{iteration}", 1)
        elif "result = list()" in code:
            code = code.replace("result = list()", f"result = []  # v{iteration}", 1)
        elif "return" in code:
            # Add a comment before the first return
            code = code.replace("return", f"# iteration {iteration}\n    return", 1)
        else:
            code = f"# optimized iteration {iteration}\n{code}"
        return code

    def _code_add_type_hint(self, code: str, iteration: int) -> str:
        """Add type annotations if missing."""
        if "-> " not in code and "def " in code:
            code = code.replace("def ", f"# typed v{iteration}\ndef ", 1)
        else:
            code = f"# type-checked v{iteration}\n{code}"
        return code

    # --- Prompt transforms ---

    def _prompt_add_specificity(self, text: str, iteration: int) -> str:
        """Append a specificity instruction."""
        return f"{text}\nBe specific and concise in your response."

    def _prompt_add_role(self, text: str, iteration: int) -> str:
        """Prepend a role instruction."""
        return f"You are an expert classifier.\n{text}"

    def _prompt_add_format_instruction(self, text: str, iteration: int) -> str:
        """Add output format instruction."""
        return f"{text}\nRespond with exactly one word: positive or negative."

    def _prompt_add_example(self, text: str, iteration: int) -> str:
        """Add a few-shot example."""
        return f"{text}\n\nExample: 'I love this product' -> positive\nExample: 'This is awful' -> negative"

    # --- Malformed / noop ---

    def _malformed_response(self) -> str:
        """Return malformed output for testing error handling."""
        responses = [
            "```python\nbroken code here\n```",
            "Here is my analysis:\n\nThe code needs several improvements...",
            "I'll help you with that! First, let me explain...",
            "",
        ]
        return responses[self._counter % len(responses)]

    def _noop_response(self, prompt: str) -> str:
        """Return the artifact unchanged."""
        return self._extract_artifact(prompt)
