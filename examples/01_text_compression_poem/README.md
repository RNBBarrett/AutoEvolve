# Example 01: Text Compression Poem

## What is being optimized

A Python compression module (`artifact.py`) that implements `compress()` and `decompress()` functions. The goal is to minimize the compressed byte size of a poem while maintaining perfect round-trip correctness.

## The baseline

The baseline uses naive run-length encoding (RLE). RLE stores each character as a `(count, char_code)` pair. This is efficient for data with many repeated characters but performs poorly on natural text, where consecutive character repetition is rare. For a typical poem, RLE actually *expands* the data (ratio > 1.0).

## How scoring works

The evaluator:
1. Loads the poem from `poem.txt`
2. Calls `compress(poem)` on the candidate
3. Calls `decompress(compressed)` and verifies exact equality
4. Computes `ratio = compressed_bytes / original_bytes`
5. Returns `score = 1.0 - ratio` (higher is better)

A score of 0.0 means the compressed output is the same size as the original. Scores above 0.0 indicate actual compression. The baseline typically scores below 0.0 because RLE expands the text.

## What improvements are plausible

With a real LLM provider, the optimizer might discover:
- Using Python's built-in `zlib` module for much better compression
- Dictionary-based encoding for common words
- Huffman-like frequency-based encoding
- Variable-length encoding schemes

## Running this example

```bash
# With mock provider (for testing)
autoevolve run --task examples/01_text_compression_poem/task.yaml

# With a real provider
autoevolve run --task examples/01_text_compression_poem/task.yaml --provider anthropic
```
