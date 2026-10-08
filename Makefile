.PHONY: install install-dev run test lint format clean

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

lint:
	ruff check app/ tests/

format:
	ruff format app/ tests/

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache
	find . -name "*.pyc" -delete
