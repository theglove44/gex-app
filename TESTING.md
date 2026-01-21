# GEX Tool Test Suite

This document describes the testing infrastructure and conventions for the GEX Tool project.

## Quick Start

```bash
# Install dependencies
make deps

# Run tests
make test

# Run with coverage
make test-cov

# Check formatting
make check

# Auto-format code
make format
```

## Testing Stack

- **pytest**: Test runner
- **ruff**: Linting (replaces flake8, isort, pyupgrade)
- **black**: Code formatting
- **coverage**: Code coverage measurement

## Test Structure

```
tests/
├── __init__.py           # Package initialization
├── conftest.py           # Pytest fixtures and configuration
├── test_gex_core.py      # Core GEX calculation tests
├── test_components.py    # UI component tests
├── test_charts.py        # Chart rendering tests
├── test_layouts.py       # Layout management tests
└── test_streamlit_app.py # App integration tests
```

## Writing Tests

### Naming Conventions
- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Fixtures
Common fixtures are defined in `conftest.py`:
- `sample_gex_data`: Sample GEX calculation data
- `mock_market_data`: Mock market data for testing
- `temp_dir`: Temporary directory for file operations

### Skipping Tests
Use `pytest.skip` for tests requiring missing dependencies:

```python
try:
    import streamlit
except ImportError:
    pytest.skip("streamlit not installed", allow_module_level=True)
```

## CI Pipeline

GitHub Actions runs on every push/PR:
1. **Lint**: ruff + black check
2. **Test**: pytest with coverage
3. **Coverage**: Reports uploaded to Codecov

## Coverage Requirements

- Minimum coverage: 80%
- Focus on core business logic (GEX calculations)
- UI components may have lower priority

## Troubleshooting

### Import Errors
Ensure dependencies are installed: `pip install -e ".[dev]"`

### Ruff Errors
Run `ruff check --fix .` to auto-fix most issues.

### Coverage Missing
Check that source paths in `pyproject.toml` match your package structure.
