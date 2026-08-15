.PHONY: install dev test lint sim doctor manifest clean

install:
	python -m pip install -e .

dev:
	python -m pip install -e .[dev]

test:
	pytest -q

lint:
	ruff check src tests scripts

sim:
	hybrid-scanner run --simulation --api

doctor:
	hybrid-scanner doctor

manifest:
	python scripts/generate_release_manifest.py

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache build dist
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
