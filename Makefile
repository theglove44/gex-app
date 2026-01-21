.PHONY: lint test check format clean install deps

install:
	pip install -e ".[dev]"

deps:
	pip install ruff pytest black coverage

lint:
	ruff check .

format:
	ruff check --fix .
	black .

check:
	ruff check .
	black --check .

test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ --cov=gex_tool --cov-report=term-missing --cov-report=html

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov .venv

ci: check test
