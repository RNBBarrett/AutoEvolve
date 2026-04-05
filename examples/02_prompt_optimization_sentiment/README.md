# Example 02: Prompt Optimization for Sentiment

## What is being optimized

A prompt template (`prompt.txt`) for classifying text as positive or negative sentiment. This demonstrates that autoevolve handles prompt text as a first-class artifact type, not just Python code.

## The baseline

The baseline prompt is minimal:
```
Classify the following text as positive or negative sentiment.
Text: {text}
Sentiment:
```

It works but lacks structure, examples, and clear output formatting instructions.

## How scoring works

The evaluator uses deterministic heuristics (no LLM calls required):
- Does the prompt contain classification keywords? (+1)
- Does it include a `{text}` placeholder? (+2)
- Does it mention "positive" and "negative"? (+1 each)
- Is the length reasonable? (+1)
- Does it ask for a single-word response? (+1)
- Does it include few-shot examples? (+1-2)

Score = checks_passed / 9

## What improvements are plausible

The optimizer should discover that adding:
- A clear role instruction ("You are an expert classifier")
- Both label names in the prompt
- Few-shot examples
- Output format instructions ("Respond with exactly one word")

...all increase the heuristic score.

## Running this example

```bash
autoevolve run --task examples/02_prompt_optimization_sentiment/task.yaml
```
