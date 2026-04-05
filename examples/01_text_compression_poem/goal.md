# Goal: Optimize Text Compression

Improve the `compress()` and `decompress()` functions in `artifact.py` to achieve
a better compression ratio on the poem stored in `poem.txt`.

## Requirements

1. `compress(text: str) -> bytes` must accept a string and return compressed bytes.
2. `decompress(data: bytes) -> str` must accept compressed bytes and return the original string.
3. Round-trip correctness: `decompress(compress(text)) == text` must always hold.
4. The score is based on the compression ratio — smaller compressed output scores higher.

## Constraints

- The artifact must be a single Python file.
- Only standard library imports are allowed.
- The functions must handle arbitrary UTF-8 text, not just the specific poem.

## What makes a good solution

- Better compression algorithms (e.g., dictionary-based, Huffman-like, or zlib wrappers)
- Smarter encoding of common patterns in natural language text
- The baseline uses naive RLE, which is very inefficient for natural text
