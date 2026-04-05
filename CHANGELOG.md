# Changelog

## 0.1.0 (2026-04-05)

### Added
- Initial release of autoevolve
- Evolutionary optimization framework with LLM-guided mutation
- Two artifact types: `python_code` and `prompt_text`
- Three strategies: `beam`, `beam_archive`, `swarm`
- Four mutation modes: `rewrite`, `patch`, `nl_feedback`, `crossover`
- Five LLM providers: `mock`, `anthropic`, `openai`, `ollama`, `external_command`
- Subprocess-based evaluator sandboxing
- Archive with top-k, recent-k, and diverse-k selection
- OPRO-style natural language feedback
- Swarm mode with specialized mutation agents
- Run resume support
- Three bundled examples
- Comprehensive test suite
- CLI with run, resume, inspect, validate-task, and list-examples commands
