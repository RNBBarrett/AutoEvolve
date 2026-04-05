"""Baseline word frequency counter.

This implementation is deliberately inefficient (O(n^2)).
For each word, it scans the entire list to count occurrences.
A good optimizer should replace this with an O(n) approach.
"""


def count_words(text: str) -> dict[str, int]:
    """Count the frequency of each word in the text.

    Args:
        text: Input text string.

    Returns:
        Dictionary mapping lowercase words to their counts.
    """
    words = text.lower().split()
    result = {}
    for word in words:
        count = 0
        for w in words:
            if w == word:
                count += 1
        result[word] = count
    return result
