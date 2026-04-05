# Expected Behavior

When running with the mock provider:

1. The baseline prompt scores moderately (around 0.44) since it contains
   "Classify" and "{text}" but lacks examples and format instructions.
2. Mock mutations add specificity instructions, role prefixes, format directives,
   and examples, which progressively increase the heuristic score.
3. After a few generations, the mock-mutated prompts should score higher
   as they accumulate more of the heuristic checklist items.
4. With a real LLM provider, the prompt would be optimized for actual
   classification accuracy on the dataset.
