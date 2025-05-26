.PHONY: help install test format lint clean run-mock run-quick run-standard run-comprehensive

help:
	@echo "SchizoBench Development Commands"
	@echo "==============================="
	@echo "install      - Install dependencies with Poetry"
	@echo "test         - Run test suite"
	@echo "format       - Format code with black and isort"
	@echo "lint         - Run linting checks"
	@echo "clean        - Remove generated files"
	@echo "run-mock     - Quick test with mock provider"
	@echo "run-quick    - Quick benchmark run"
	@echo "run-standard - Standard benchmark run"
	@echo "verify       - Verify setup and API keys"

install:
	poetry install

test:
	poetry run pytest tests/

format:
	poetry run black schizobench/ tests/
	poetry run isort schizobench/ tests/

lint:
	poetry run flake8 schizobench/ tests/
	poetry run mypy schizobench/

clean:
	rm -rf results/ results_v2/ visualizations/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage

run-mock:
	poetry run schizobench-v2 --provider mock --mode quick

run-quick:
	poetry run schizobench-v2 --provider anthropic --mode quick

run-standard:
	poetry run schizobench-v2 --provider anthropic --mode standard

run-comprehensive:
	poetry run schizobench-v2 --provider anthropic --mode comprehensive

verify:
	poetry run verify-setup

# Development shortcuts
dev-install:
	poetry install --with dev
	poetry run pre-commit install

shell:
	poetry shell

update:
	poetry update

# Docker support (future)
docker-build:
	docker build -t schizobench:latest .

docker-run:
	docker run -it --rm -v $$(pwd)/results:/app/results schizobench:latest