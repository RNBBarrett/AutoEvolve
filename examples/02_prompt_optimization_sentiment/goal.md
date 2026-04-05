# Goal: Optimize Sentiment Classification Prompt

Improve the prompt template in `prompt.txt` to better classify text as
positive or negative sentiment.

## Requirements

1. The prompt must contain `{text}` as a placeholder for the input text.
2. The prompt should clearly instruct the model to classify sentiment.
3. The response should be a single word: "positive" or "negative".

## What makes a good prompt

- Clearly states the task (sentiment classification)
- Mentions both target labels (positive, negative)
- Asks for a single-word structured response
- Includes few-shot examples for guidance
- Is concise but complete
- Uses a clear role or instruction framing
