# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a TTS (Text-to-Speech) reading application with Markdown report generation capabilities.

## Project Structure

```
tts_read/
├── src/                    # Python source code
│   └── markdown_converter.py  # Markdown conversion functionality
├── config/                 # Configuration files (YAML)
│   └── markdown_spec.yml   # Allowed Markdown syntax specification
├── tests/                  # Test files
└── .env                    # Environment variables (if needed)
```

## Key Development Guidelines

### Code Organization
- All Python source code must be in `src/` and its subdirectories
- Configuration data (settings, variables, prompts) must be stored in YAML files in `config/`
- Never hardcode values in source files - always load from config files or environment variables

### Git Workflow
- Commit after each successfully completed task
- Push after each commit to sync with remote repository
- Before committing, verify active branch is valid (no detached HEAD)
- If push fails due to access rights, inform user but continue working

### Testing
- Always create and run tests for new functionality
- Test files should be placed in the `tests/` directory
- **Run all tests after making significant changes to ensure nothing is broken**

### Markdown Report Generation
- When implementing Markdown conversion features in `src/markdown_converter.py`, always update `config/markdown_spec.yml` with new syntax
- Report sections use dictionary format with 'content' and 'is_markdown' fields to support mixed HTML/Markdown content
- Always consult `config/markdown_spec.yml` before converting report sections to Markdown

### Formatting Standards
- Numbers and units: always include space (e.g., "120 h", "90 %")
- Euro prices: start with € symbol followed by value (e.g., "€100")
- Academic titles: use full title on first mention (e.g., "Dr.-Ing."), then abbreviated form (e.g., "Dr.")
- German translations: "rate" (English) → "Quote" (German) for relative proportions; "Rate" is only for time-based measurements

## Common Development Tasks

Since this is a new project, common commands will be added as the project develops. Expected commands:

```bash
# Python virtual environment (once created)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies (once requirements.txt exists)
pip install -r requirements.txt

# Run tests (once test framework is set up)
pytest

# Linting (once configured)
flake8 src/
# or
pylint src/
```

## Architecture Notes

As this is a newly initialized project, the architecture will evolve. Based on the project name and guidelines:

1. **TTS Functionality**: Core text-to-speech reading capabilities will be implemented in `src/`
2. **Markdown Processing**: The `src/markdown_converter.py` module will handle conversion between HTML and Markdown formats
3. **Configuration-Driven**: All settings, prompts, and variables will be externalized to `config/` YAML files
4. **Report Generation**: Support for mixed HTML/Markdown content in report sections using dictionary structures

## Virtual Environment Guidelines
- Use virtual environment in folder `.venv`