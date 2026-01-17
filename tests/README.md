# CommitPilot Testing

## Quick Start

```bash
pip install pytest pytest-mock python-dotenv openai
pytest tests/ -v
```

## Test Structure

- `test_auto_commit.py` - Tests for main module
- `__init__.py` - Test package initialization

## Running Tests

```bash
# All tests
pytest tests/

# With verbose output
pytest tests/ -v

# Specific test
pytest tests/test_auto_commit.py::test_get_git_diff

# With coverage
pytest --cov=. --cov-report=term tests/
```

## Test Coverage

```bash
pip install pytest-cov
pytest --cov=. --cov-report=html tests/
# Open htmlcov/index.html in browser
```

## Guidelines

- Use mocks for external dependencies (API calls, git commands)
- Test both success and error scenarios
- Document test functions with docstrings
- Keep tests simple and focused on one thing
- Use fixtures for common setup

## Current Test Coverage

- Configuration setup and caching
- Git operations (diff, status, add, commit, push)
- Message generation (with fallbacks)
- Environment variable handling
- Error handling
