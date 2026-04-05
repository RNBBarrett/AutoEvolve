# Expected Behavior

When running with the mock provider:

1. The baseline RLE compression achieves a compression ratio of approximately 2.0x
   (compressed size is about 2x the original), resulting in a negative score.
2. Mock provider mutations add comments and minor code changes that don't meaningfully
   change compression behavior, so scores will be similar across candidates.
3. With a real LLM provider, candidates might use zlib, dictionary compression, or
   other standard library tools to achieve much better ratios.
4. The run should complete without errors, producing a valid run directory with
   all expected output files.
