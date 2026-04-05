"""Baseline text compression artifact.

This is a deliberately simple run-length encoding implementation.
It works correctly but leaves significant room for improvement.
A good optimizer should be able to find better compression strategies.
"""


def compress(text: str) -> bytes:
    """Compress text using naive run-length encoding.

    Each character is stored as (count, char_code) pairs.
    This is inefficient for text with few repeated characters.
    """
    encoded = []
    i = 0
    while i < len(text):
        count = 1
        while i + count < len(text) and text[i + count] == text[i] and count < 255:
            count += 1
        encoded.append(count)
        encoded.append(ord(text[i]))
        i += count
    return bytes(encoded)


def decompress(data: bytes) -> str:
    """Decompress data produced by compress()."""
    result = []
    for i in range(0, len(data), 2):
        count = data[i]
        char = chr(data[i + 1])
        result.append(char * count)
    return "".join(result)
