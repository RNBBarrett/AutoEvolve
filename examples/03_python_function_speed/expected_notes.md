# Expected Behavior

When running with the mock provider:

1. The baseline O(n^2) implementation scores reasonably on correctness
   but poorly on speed for large inputs.
2. Mock mutations add comments and minor structural changes that don't
   change the algorithm, so speed scores will be similar.
3. With a real LLM provider, the optimizer would likely discover
   using `collections.Counter` or a simple dict accumulator for O(n).
4. All correctness tests should pass for all candidates since mock
   mutations don't break the core logic.
